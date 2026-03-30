"""OD/ID/W 다중 방법론 앙상블 모듈

K방법(geometry_guided), S01(arrowhead), S02(text-first), S06(YOLO+OCR)을
조합하여 투표 기반으로 최종 OD/ID/W를 결정한다.

사용: run_ensemble(image_path) → {od, id, w, method_results, consensus}
"""

import ast
import cv2
import numpy as np
import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def _extract_num(val_str: Optional[str]) -> Optional[float]:
    """'Ø1036' → 1036.0, '550+2' → 550.0, 'Ø838.2.00' → 838.2, None → None"""
    if val_str is None:
        return None
    cleaned = re.sub(r"[ØøΦ⌀∅()R]", "", str(val_str))
    # Extract first valid number (handles '550+2', '342-378NM', '838.2.00')
    m = re.search(r"(\d+\.?\d*)", cleaned)
    if m:
        try:
            return float(m.group(1))
        except (ValueError, TypeError):
            return None
    return None


def _apply_soft_filter(result: Dict, drawing_title: str = "") -> Dict:
    """비베어링/이상치 soft 필터 — confidence penalty 적용"""
    penalties = []
    confidence = 1.0
    od_num = _extract_num(result.get("od", {}).get("value"))
    id_num = _extract_num(result.get("id", {}).get("value"))
    w_num = _extract_num(result.get("w", {}).get("value"))

    # 1. BEARING 키워드 없으면 신뢰도 감소
    title_upper = drawing_title.upper()
    if not any(kw in title_upper for kw in ("BEARING", "BRG", "베어링")):
        confidence *= 0.85
        penalties.append("title_missing_bearing")

    # 2. OD 범위 체크 (50~2000mm)
    if od_num is not None and (od_num < 50 or od_num > 2000):
        confidence *= 0.80
        penalties.append("od_out_of_range")

    # 3. 물리적 순서 OD > ID > W
    if od_num and id_num and od_num <= id_num:
        confidence *= 0.75
        penalties.append("invalid_physical_order")
    if id_num and w_num and id_num <= w_num:
        confidence *= 0.85
        penalties.append("id_leq_w")

    result["soft_filter"] = {
        "confidence": round(confidence, 2),
        "applied_penalties": penalties,
        "drawing_title": drawing_title,
    }
    return result


def _vote_best(values: List[Optional[float]], tolerance: float = 5.0) -> Optional[float]:
    """가장 빈번한 값 선택 (±tolerance 이내 동일 취급)"""
    valid = [v for v in values if v is not None]
    if not valid:
        return None
    groups: List[List[float]] = []
    for v in sorted(valid):
        placed = False
        for g in groups:
            if abs(v - g[0]) <= tolerance:
                g.append(v)
                placed = True
                break
        if not placed:
            groups.append([v])
    best = max(groups, key=len)
    return round(sum(best) / len(best), 1)


def _parse_circle_str(raw) -> Optional[tuple]:
    """numpy str '[1008 1146  810]' → (1008, 1146, 810)"""
    if raw is None:
        return None
    if isinstance(raw, (tuple, list)) and len(raw) >= 3:
        return tuple(int(x) for x in raw[:3])
    if isinstance(raw, np.ndarray) and len(raw) >= 3:
        return tuple(int(x) for x in raw[:3])
    if isinstance(raw, str):
        arr = np.fromstring(raw.strip("[]"), sep=" ")
        if len(arr) >= 3:
            return tuple(int(x) for x in arr[:3])
    return None


def _run_s06_yolo_ocr(image_path: str, model_path: str) -> Dict:
    """S06: YOLO 텍스트 검출 → PaddleOCR 읽기 → 규칙 분류"""
    import requests
    from ultralytics import YOLO

    model = YOLO(model_path)
    results = model(image_path, verbose=False, conf=0.3)
    if not results or not results[0].boxes:
        return {"od": None, "id": None, "w": None}

    img = cv2.imread(image_path)
    h, w_img = img.shape[:2]

    # YOLO 검출 영역에서 텍스트 추출
    dim_values = []
    for box in results[0].boxes:
        cls_id = int(box.cls[0])
        if cls_id != 0:  # dimension_number만
            continue
        x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
        # 패딩 추가
        pad = 5
        x1, y1 = max(0, x1 - pad), max(0, y1 - pad)
        x2, y2 = min(w_img, x2 + pad), min(h, y2 + pad)
        crop = img[y1:y2, x1:x2]
        if crop.size == 0:
            continue

        # PaddleOCR로 크롭 영역 읽기
        _, buf = cv2.imencode('.png', crop)
        try:
            resp = requests.post(
                'http://localhost:5006/api/v1/ocr',
                files={'file': ('crop.png', buf.tobytes(), 'image/png')},
                timeout=10,
            )
            if resp.status_code == 200:
                for det in resp.json().get('detections', []):
                    text = det.get('text', '')
                    has_dia = any(c in text for c in 'ØøΦ⌀∅')
                    nums = re.findall(r'[\d.]+', text)
                    for n in nums:
                        try:
                            val = float(n)
                            # 도면 번호 필터 (5자리 이상 정수는 치수 아닐 가능성 높음)
                            if val >= 10 and val <= 9999:
                                cx = (x1 + x2) / 2
                                cy = (y1 + y2) / 2
                                dim_values.append({
                                    "val": val, "has_dia": has_dia,
                                    "cx": cx, "cy": cy,
                                    "is_horizontal": (x2 - x1) > (y2 - y1),
                                })
                        except ValueError:
                            pass
        except Exception:
            pass

    if not dim_values:
        return {"od": None, "id": None, "w": None}

    # 분류: Ø 값 → 직경 후보, 수평 → 폭 후보
    dia_cands = sorted(
        [d for d in dim_values if d["has_dia"]],
        key=lambda x: x["val"], reverse=True,
    )
    horiz_cands = sorted(
        [d for d in dim_values if d["is_horizontal"] and not d["has_dia"]],
        key=lambda x: x["val"],
    )
    all_sorted = sorted(dim_values, key=lambda x: x["val"], reverse=True)

    od = dia_cands[0]["val"] if dia_cands else (all_sorted[0]["val"] if all_sorted else None)
    id_val = None
    w_val = None

    if dia_cands and len(dia_cands) >= 2:
        id_val = dia_cands[1]["val"]
    elif all_sorted and len(all_sorted) >= 2:
        remaining = [d for d in all_sorted if d["val"] != od]
        if remaining:
            id_val = remaining[0]["val"]

    if horiz_cands:
        w_val = horiz_cands[0]["val"]
    elif all_sorted and len(all_sorted) >= 3:
        used = {od, id_val}
        for d in sorted(all_sorted, key=lambda x: x["val"]):
            if d["val"] not in used:
                w_val = d["val"]
                break

    return {
        "od": f"Ø{od:.0f}" if od else None,
        "id": f"{id_val:.0f}" if id_val else None,
        "w": f"{w_val:.0f}" if w_val else None,
    }


def run_ensemble(image_path: str, drawing_title: str = "") -> Dict:
    """다중 방법론 앙상블 실행

    0. 레이아웃 디텍션 (비베어링 필터 + 영역 제외)
    1. K방법 실행 (내부에서 dims 캡처)
    2. 캡처된 dims + circles를 S01/S02에 전달
    3. 투표로 최종 결과 결정
    """
    import services.geometry_guided_extractor as gg

    img = cv2.imread(image_path)
    if img is None:
        return {"od": None, "id": None, "w": None, "error": "Image load failed"}
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # --- Step 0: 레이아웃 디텍션 (선택적) ---
    layout_info = None
    try:
        from services.layout_detector import detect_layout
        layout_info = detect_layout(image_path)
        if layout_info and not layout_info["is_bearing"]:
            logger.info(f"Layout: 비베어링 판정 → 스킵 ({image_path})")
            return {
                "od": None, "id": None, "w": None,
                "method_results": {},
                "strategy": "layout_skip",
                "layout": {"is_bearing": False, "regions": layout_info["regions"]},
            }
    except ImportError:
        logger.debug("layout_detector not available, skipping layout step")
    except Exception as e:
        logger.debug(f"Layout detection skipped: {e}")

    method_results: Dict[str, Dict] = {}

    # --- K method + dims 캡처 ---
    captured_dims: List[dict] = []
    captured_circles: dict = {}
    original_classify = gg._classify_by_circle_proximity

    def capturing_classify(dims, circles, dim_lines, *a, **kw):
        captured_dims.extend(dims)
        captured_circles.update({"circles": circles, "dim_lines": dim_lines})
        return original_classify(dims, circles, dim_lines, *a, **kw)

    gg._classify_by_circle_proximity = capturing_classify
    try:
        k_result = gg.extract_by_geometry(image_path)
        method_results["K"] = {
            "od": k_result["od"]["value"] if k_result.get("od") else None,
            "id": k_result["id"]["value"] if k_result.get("id") else None,
            "w": k_result["w"]["value"] if k_result.get("w") else None,
        }
    except Exception as e:
        logger.warning(f"K method failed: {e}")
        method_results["K"] = {"od": None, "id": None, "w": None}
    finally:
        gg._classify_by_circle_proximity = original_classify

    # --- 세션명/파일명 힌트로 K 결과 보정 ---
    if drawing_title:
        from services.session_name_parser import parse_session_name_dimensions
        ref = parse_session_name_dimensions(drawing_title)
        ref_od = ref.get("od")
        ref_id = ref.get("id")
        ref_w = ref.get("w")
        k = method_results.get("K", {})

        if ref_od or ref_id:
            logger.info(f"세션명 힌트: OD={ref_od}, ID={ref_id}, W={ref_w} (pattern={ref.get('pattern')})")

            # K가 실패했거나 세션명 힌트와 30% 이상 차이나면 힌트 우선
            k_od = k.get("od")
            k_id = k.get("id")

            def _close(a, b, tol=0.3):
                if a is None or b is None:
                    return False
                try:
                    return abs(float(a) - float(b)) / max(float(b), 1) <= tol
                except (ValueError, TypeError):
                    return False

            if ref_od and (not k_od or not _close(k_od, ref_od)):
                # K 외경이 없거나 힌트와 30% 이상 차이 → OCR 값 중 힌트에 가장 가까운 값 선택
                best_od = None
                best_dist = float("inf")
                for d in captured_dims:
                    try:
                        import re as _re
                        val_str = str(d.get("value", ""))
                        val_str = _re.sub(r'^[ØøΦ⌀∅]\s*', '', val_str)
                        val_str = _re.sub(r'[()]', '', val_str)
                        m = _re.match(r'(\d+\.?\d*)', val_str)
                        if m:
                            v = float(m.group(1))
                            dist = abs(v - ref_od)
                            if dist < best_dist and dist / ref_od < 0.15:  # ±15% 이내
                                best_dist = dist
                                best_od = val_str.strip()
                    except (ValueError, TypeError):
                        pass
                if best_od:
                    method_results["K"]["od"] = best_od
                    logger.info(f"K 외경 보정: {k_od} → {best_od} (힌트 {ref_od})")
                elif ref_od:
                    method_results["K"]["od"] = str(int(ref_od))
                    logger.info(f"K 외경 힌트 직접 사용: {ref_od}")

            if ref_id and (not k_id or not _close(k_id, ref_id)):
                best_id = None
                best_dist = float("inf")
                for d in captured_dims:
                    try:
                        import re as _re
                        val_str = str(d.get("value", ""))
                        val_str = _re.sub(r'^[ØøΦ⌀∅]\s*', '', val_str)
                        val_str = _re.sub(r'[()]', '', val_str)
                        m = _re.match(r'(\d+\.?\d*)', val_str)
                        if m:
                            v = float(m.group(1))
                            dist = abs(v - ref_id)
                            if dist < best_dist and dist / ref_id < 0.15:
                                best_dist = dist
                                best_id = val_str.strip()
                    except (ValueError, TypeError):
                        pass
                if best_id:
                    method_results["K"]["id"] = best_id
                    logger.info(f"K 내경 보정: {k_id} → {best_id} (힌트 {ref_id})")
                elif ref_id:
                    method_results["K"]["id"] = str(int(ref_id))
                    logger.info(f"K 내경 힌트 직접 사용: {ref_id}")

            if ref_w and not k.get("w"):
                method_results["K"]["w"] = str(int(ref_w))
                logger.info(f"K 폭 힌트 직접 사용: {ref_w}")

    # --- dims → S01/S02 형식으로 변환 (레이아웃 영역 필터 적용) ---
    exclude_bboxes = layout_info["exclude_bboxes"] if layout_info else []
    dims_for_sub = []
    excluded_count = 0
    for d in captured_dims:
        bbox_raw = d.get("bbox", {})
        if isinstance(bbox_raw, str):
            try:
                bbox_raw = ast.literal_eval(bbox_raw)
            except Exception:
                continue
        if not isinstance(bbox_raw, dict):
            continue
        # 레이아웃 기반 영역 제외 (notes/table 안의 텍스트 스킵)
        if exclude_bboxes:
            try:
                from services.layout_detector import is_in_exclude_zone
                if is_in_exclude_zone(bbox_raw, exclude_bboxes):
                    excluded_count += 1
                    continue
            except ImportError:
                pass
        dims_for_sub.append({
            "value": d.get("value", ""),
            "confidence": float(d.get("confidence", 0.5)),
            "bbox": bbox_raw,
        })

    if excluded_count > 0:
        logger.info(f"Layout filter: {excluded_count} dims excluded from notes/table zones")

    # outer circle 추출
    outer_circle = None
    circles_list = captured_circles.get("circles", [])
    if isinstance(circles_list, list):
        for c in circles_list:
            if isinstance(c, dict) and c.get("role") == "outer":
                outer_circle = (c["cx"], c["cy"], c["r"])
                break

    # --- K 실패 시 독립 OCR로 dims 확보 ---
    if not dims_for_sub:
        try:
            from services.dimension_service import DimensionService
            svc = DimensionService()
            fallback_result = svc.extract_dimensions(
                image_path, ocr_engines=["edocr2"], confidence_threshold=0.3,
            )
            for d in fallback_result.get("dimensions", []):
                val = d.get("value", "")
                conf = d.get("confidence", 0.5)
                bbox = d.get("bbox")
                if not isinstance(bbox, dict):
                    continue
                dims_for_sub.append({
                    "value": str(val),
                    "confidence": float(conf),
                    "bbox": bbox,
                })
            if dims_for_sub:
                logger.info(f"Fallback OCR: {len(dims_for_sub)} dims for S01/S02")
        except Exception as e:
            logger.warning(f"Fallback OCR failed: {e}")

    # --- S01 Arrowhead ---
    if dims_for_sub:
        try:
            from services.arrowhead_detector import run_arrowhead_pipeline
            s01 = run_arrowhead_pipeline(gray, dims_for_sub, outer_circle=outer_circle)
            method_results["S01"] = {
                "od": s01["od"]["value"] if s01.get("od") else None,
                "id": s01["id"]["value"] if s01.get("id") else None,
                "w": s01["w"]["value"] if s01.get("w") else None,
            }
        except Exception as e:
            logger.warning(f"S01 failed: {e}")
            method_results["S01"] = {"od": None, "id": None, "w": None}

        # --- S02 Text-First ---
        try:
            from services.dimension_text_first import extract_text_first
            oc_arr = np.array(outer_circle) if outer_circle else None
            s02 = extract_text_first(dims_for_sub, gray, outer_circle=oc_arr)
            method_results["S02"] = {
                "od": s02["od"]["value"] if s02.get("od") else None,
                "id": s02["id"]["value"] if s02.get("id") else None,
                "w": s02["w"]["value"] if s02.get("w") else None,
            }
        except Exception as e:
            logger.warning(f"S02 failed: {e}")
            method_results["S02"] = {"od": None, "id": None, "w": None}

    # --- S06 YOLO+OCR (optional) ---
    s06_model_path = "/tmp/yolo_s06_ocr/dim_detect_v2/weights/best.pt"
    try:
        import os
        if os.path.exists(s06_model_path):
            s06_result = _run_s06_yolo_ocr(image_path, s06_model_path)
            if any(s06_result.get(k) for k in ("od", "id", "w")):
                method_results["S06"] = s06_result
    except Exception as e:
        logger.warning(f"S06 failed: {e}")

    # --- K-priority + fallback voting ---
    # K method is most accurate (83% GT vs 50% ensemble voting).
    # Use K result when available; vote only to fill K's gaps.
    k_result = method_results.get("K", {})
    k_od = _extract_num(k_result.get("od"))
    k_id = _extract_num(k_result.get("id"))
    k_w = _extract_num(k_result.get("w"))

    # Plausibility check: OD > ID > W
    k_plausible = (
        k_od is not None and k_id is not None and k_w is not None
        and k_od > k_id > k_w
    )

    od_votes = [_extract_num(m.get("od")) for m in method_results.values()]
    id_votes = [_extract_num(m.get("id")) for m in method_results.values()]
    w_votes = [_extract_num(m.get("w")) for m in method_results.values()]

    vote_od = _vote_best(od_votes)
    vote_id = _vote_best(id_votes)
    vote_w = _vote_best(w_votes)

    # Strategy: K-priority when plausible, vote-fallback for gaps
    if k_plausible:
        final_od, final_id, final_w = k_od, k_id, k_w
        strategy = "k_priority"
    elif k_od is not None and k_id is not None:
        # K has OD+ID but missing/bad W → use K's OD+ID, vote for W
        final_od, final_id = k_od, k_id
        final_w = k_w if k_w is not None else vote_w
        strategy = "k_partial"
    else:
        # K failed → pure vote fallback
        final_od, final_id, final_w = vote_od, vote_id, vote_w
        strategy = "vote_fallback"

    def _agreement(votes, consensus):
        if consensus is None:
            return 0.0
        valid = [v for v in votes if v is not None]
        return sum(1 for v in valid if abs(v - consensus) <= 5.0) / max(len(valid), 1)

    result = {
        "od": {"value": f"Ø{final_od:.0f}" if final_od else None},
        "id": {"value": f"{final_id:.0f}" if final_id else None},
        "w": {"value": f"{final_w:.0f}" if final_w else None},
        "method_results": method_results,
        "strategy": strategy,
        "consensus": {
            "od_agreement": round(_agreement(od_votes, final_od), 2),
            "id_agreement": round(_agreement(id_votes, final_id), 2),
            "w_agreement": round(_agreement(w_votes, final_w), 2),
        },
    }
    if layout_info:
        result["layout"] = {
            "is_bearing": layout_info["is_bearing"],
            "excluded_dims": excluded_count,
        }
    return _apply_soft_filter(result, drawing_title)
