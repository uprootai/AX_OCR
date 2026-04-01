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
    """S06: YOLO 텍스트 검출 → PaddleOCR 읽기 → 규칙 분류 (분리: s06_yolo_ocr.py)"""
    from services.s06_yolo_ocr import run_s06_yolo_ocr
    return run_s06_yolo_ocr(image_path, model_path)


PADDLE_URL = "http://paddleocr-api:5006/api/v1/ocr"


def _paddle_ocr(png_bytes, timeout=60):
    """모듈 레벨 PaddleOCR 호출"""
    import requests
    try:
        resp = requests.post(
            PADDLE_URL,
            files={"file": ("img.png", png_bytes, "image/png")},
            timeout=timeout,
        )
        resp.raise_for_status()
        return resp.json().get("detections", [])
    except Exception:
        return []


def _to_img_bytes(img, fmt="JPEG"):
    """PIL Image → bytes 변환"""
    import io
    buf = io.BytesIO()
    if fmt == "JPEG":
        img = img.convert("RGB")
    img.save(buf, format=fmt, quality=90)
    return buf.getvalue()


def _auto_detect_section(image_path: str, paddle_fn, img_bytes_fn) -> Optional[Dict]:
    """OCR 앵커 + 콘텐츠 밀도로 SECTION 영역 자동 감지 (하드코딩 제거)

    Returns:
        {"left": 0.46, "top": 0.31, "right": 0.73, "bottom": 0.90} or None
    """
    import cv2
    import numpy as np
    from PIL import Image

    try:
        img_cv = cv2.imread(image_path)
        if img_cv is None:
            return None
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        # 전체 이미지 OCR → 앵커 텍스트 찾기
        pil_img = Image.open(image_path)
        full_bytes = img_bytes_fn(pil_img)
        dets = paddle_fn(full_bytes, timeout=120)

        anchors = {}
        for d in dets:
            text = (d.get("text", "") or "").upper()
            bbox = d.get("bbox", [])
            if not (isinstance(bbox, list) and len(bbox) >= 4 and isinstance(bbox[0], list)):
                continue
            xs = [p[0] for p in bbox]
            ys = [p[1] for p in bbox]
            cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)

            if "SECTION" in text and len(text) > 5:
                anchors["section"] = {"cx": cx, "cy": cy, "y_top": min(ys)}
            elif "GEN" in text and "SIDE" in text:
                anchors["gen"] = {"cx": cx, "cy": cy}
            elif "TBN" in text and "SIDE" in text:
                anchors["tbn"] = {"cx": cx, "cy": cy}

        sec = anchors.get("section")
        if not sec:
            return None

        # 좌우 경계: GEN SIDE ~ TBN SIDE (없으면 SECTION 기준 ±15%)
        gen_x = anchors.get("gen", {}).get("cx", sec["cx"] - w * 0.15)
        tbn_x = anchors.get("tbn", {}).get("cx", sec["cx"] + w * 0.15)
        col_left = int(min(gen_x, tbn_x))
        col_right = int(max(gen_x, tbn_x))

        # 상단 경계: 콘텐츠 밀도 스캔 (라벨에서 위로)
        _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        label_y = int(sec["y_top"])
        content_top = label_y

        in_content = False
        for row_y in range(label_y, 0, -1):
            row = binary[row_y, col_left:col_right]
            density = np.sum(row > 0) / max(len(row), 1)
            if density > 0.03:
                in_content = True
            elif density < 0.005 and in_content:
                gap = sum(1 for cy in range(row_y, max(row_y - 25, 0), -1)
                          if np.sum(binary[cy, col_left:col_right] > 0) / max(col_right - col_left, 1) < 0.005)
                if gap > 20:
                    content_top = row_y + 20
                    break

        margin_x = w * 0.03
        margin_y = h * 0.02
        return {
            "left": max(0, (col_left - margin_x)) / w,
            "top": max(0, (content_top - margin_y)) / h,
            "right": min(w, (col_right + margin_x)) / w,
            "bottom": min(h, (label_y + h * 0.05)) / h,
            "anchors": anchors,
            "ocr_dets": dets,
        }
    except Exception as e:
        logger.warning(f"SECTION auto-detect failed: {e}")
        return None


def _detect_drawing_views(
    ocr_dets: list, img_w: int, img_h: int, image_path: str = ""
) -> Dict[str, Dict]:
    """OCR 앵커 + 콘텐츠 밀도로 ASSY 도면의 4개 뷰 영역을 감지

    좌측 영역을 콘텐츠 밀도 수평 스캔으로 보조도/메인뷰 분리.
    절단선(E-3) 위치에 의존하지 않음.

    Returns:
        {"auxiliary_view": ..., "main_view": ..., "section_view": ..., "iso_view": ...}
        좌표는 0~1 정규화. 감지된 뷰만 포함.
    """
    import cv2 as _cv2
    import numpy as _np

    anchors = {}
    for d in ocr_dets:
        text = (d.get("text", "") or "").upper()
        bbox = d.get("bbox", [])
        if not (isinstance(bbox, list) and len(bbox) >= 4 and isinstance(bbox[0], list)):
            continue
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)

        if "ISO" in text and "VIEW" in text:
            anchors["iso"] = {"cx": cx, "cy": cy}
        if "GEN" in text and "SIDE" in text:
            anchors["gen"] = {"cx": cx, "cy": cy}
        if "TBN" in text and "SIDE" in text:
            anchors["tbn"] = {"cx": cx, "cy": cy}

    views = {}
    iso_x = anchors.get("iso", {}).get("cx")
    gen_x = anchors.get("gen", {}).get("cx")
    tbn_x = anchors.get("tbn", {}).get("cx")

    # SECTION 좌측 경계
    sec_left = min(gen_x, tbn_x) / img_w if gen_x and tbn_x else 0.46

    # 우측 경계: ISO VIEW 좌측
    right_bound = (iso_x / img_w - 0.02) if iso_x else 0.75

    # --- 좌측 영역에서 보조도/메인뷰 분리 (콘텐츠 밀도 수평 스캔) ---
    left_right = min(sec_left, right_bound)
    split_y = None  # 보조도와 메인뷰 사이 빈 공간의 y좌표 (정규화)

    if image_path:
        try:
            img_cv = _cv2.imread(image_path)
            if img_cv is not None:
                gray = _cv2.cvtColor(img_cv, _cv2.COLOR_BGR2GRAY)
                _, binary = _cv2.threshold(gray, 200, 255, _cv2.THRESH_BINARY_INV)
                h_px, w_px = binary.shape

                scan_x1 = int(w_px * 0.05)
                scan_x2 = int(w_px * left_right)

                # y=10%~60% 범위에서 수평 밀도 최소 구간 찾기
                densities = []
                for row_y in range(int(h_px * 0.10), int(h_px * 0.60)):
                    row = binary[row_y, scan_x1:scan_x2]
                    density = _np.sum(row > 0) / max(len(row), 1)
                    densities.append((row_y, density))

                # 밀도 < 0.01 인 연속 구간 찾기 (최소 15px 갭)
                gap_start = None
                gap_best = None
                gap_best_len = 0
                for row_y, density in densities:
                    if density < 0.01:
                        if gap_start is None:
                            gap_start = row_y
                    else:
                        if gap_start is not None:
                            gap_len = row_y - gap_start
                            if gap_len > gap_best_len:
                                gap_best = (gap_start, row_y)
                                gap_best_len = gap_len
                            gap_start = None
                # 마지막 구간 체크
                if gap_start is not None:
                    last_y = densities[-1][0]
                    gap_len = last_y - gap_start
                    if gap_len > gap_best_len:
                        gap_best = (gap_start, last_y)
                        gap_best_len = gap_len

                if gap_best and gap_best_len > 15:
                    split_y = (gap_best[0] + gap_best[1]) / 2 / h_px
                    logger.info(f"View split: y={split_y:.3f} (gap={gap_best_len}px)")
        except Exception as e:
            logger.warning(f"Content density scan failed: {e}")

    # 폴백: split_y를 못 찾으면 y=0.30 기본값
    if split_y is None:
        split_y = 0.30
        logger.info("View split: fallback y=0.30")

    # 보조도 (상단 좌측)
    views["auxiliary_view"] = {
        "left": 0.0, "top": 0.02,
        "right": left_right,
        "bottom": split_y - 0.01,
    }
    # 메인 뷰 (하단 좌측 — 베어링 정면도)
    views["main_view"] = {
        "left": 0.0, "top": split_y,
        "right": sec_left,
        "bottom": 0.92,
    }

    # SECTION E-3
    if gen_x and tbn_x:
        sec_right = max(gen_x, tbn_x) / img_w
        views["section_view"] = {
            "left": sec_left - 0.02,
            "top": 0.25,
            "right": sec_right + 0.02,
            "bottom": 0.92,
        }

    # ISO VIEW
    if iso_x:
        views["iso_view"] = {
            "left": iso_x / img_w - 0.05,
            "top": 0.25,
            "right": 1.0,
            "bottom": 0.60,
        }

    return views


def _scan_side_view(
    image_path: str,
    side_region: Dict,
    hint_od: Optional[float] = None,
    hint_id: Optional[float] = None,
) -> Optional[float]:
    """측면도(축방향 뷰)에서 W(폭) 추출 — 단일 PaddleOCR 호출

    측면도의 세로 방향 치수 = 베어링 폭(W).
    가로 방향 치수 = 직경 참조값 (무시).
    """
    from PIL import Image, ImageEnhance

    img = Image.open(image_path)
    iw, ih = img.size
    x1 = int(iw * side_region["left"])
    y1 = int(ih * side_region["top"])
    x2 = int(iw * side_region["right"])
    y2 = int(ih * side_region["bottom"])
    crop = img.crop((x1, y1, x2, y2))
    cw, ch = crop.size
    if cw < 50 or ch < 50:
        return None

    # 2배 확대 + 대비 강화
    up = crop.resize((cw * 2, ch * 2), Image.LANCZOS)
    enhanced = ImageEnhance.Contrast(up).enhance(1.5)
    dets = _paddle_ocr(_to_img_bytes(enhanced, fmt="PNG"))

    w_cands = []
    for d in dets:
        text = d.get("text", "")
        if re.match(r"^M\d", text, re.IGNORECASE):
            continue
        if re.search(r"TORQUE|NM$|SECTION|VIEW|SIDE|DWG|SCALE", text, re.IGNORECASE):
            continue
        # Ø 기호 있으면 직경 → W 아님
        if re.search(r"[ØøΦ⌀∅]", text):
            continue
        is_ref = bool(re.match(r"^\s*\(.*\)\s*$", text.strip()))
        cleaned = re.sub(r"[()]", "", text)
        m = re.search(r"(\d+\.?\d*)", cleaned)
        if not m:
            continue
        num = float(m.group(1))
        if num < 30 or num > 1000:
            continue
        if hint_od and num >= hint_od:
            continue
        # bbox 방향: 세로로 긴 bbox = 세로 치수선 = W 후보
        bbox = d.get("bbox", [])
        if isinstance(bbox, list) and len(bbox) >= 4 and isinstance(bbox[0], list):
            xs = [p[0] for p in bbox]
            ys = [p[1] for p in bbox]
            bw = max(xs) - min(xs)
            bh = max(ys) - min(ys)
            is_vertical = bh > bw * 1.2  # 세로로 긴 텍스트
            w_cands.append({"num": num, "is_ref": is_ref, "is_vertical": is_vertical})

    if not w_cands:
        return None

    # 선택 우선순위: hint_id와 일치 > 세로 방향 비참조 > 비참조 최소값
    if hint_id:
        for c in w_cands:
            if abs(c["num"] - hint_id) / max(hint_id, 1) < 0.05:
                logger.info(f"SIDE W: {c['num']} matches hint_id={hint_id}")
                return c["num"]

    non_ref_vert = [c for c in w_cands if not c["is_ref"] and c["is_vertical"]]
    non_ref = [c for c in w_cands if not c["is_ref"]]
    pool = non_ref_vert or non_ref or w_cands
    pool.sort(key=lambda c: c["num"])
    return pool[0]["num"]


def _run_section_scan(image_path: str, drawing_title: str = "") -> Dict:
    """SEC: SECTION 단면도 세로 텍스트 스캔 → OD/ID/W 추출

    ASSY 도면의 SECTION E-3 영역에서:
    - 기본 크롭 (53~78%) → ID/W (위치 기반)
    - 세로 슬라이딩 스캔 (60~73%) → OD (Ø치수)
    - 세션명 힌트 결합 → OD 확정

    검증 결과: GT 7건 기준 OD 5/7(71%), ID 6/7(86%), W 5/7(71%)
    """
    import time
    from PIL import Image, ImageEnhance

    _paddle = _paddle_ocr
    _img_bytes = _to_img_bytes

    img = Image.open(image_path)
    w, h = img.size

    # --- 0. SECTION 영역 자동 감지 (하드코딩 금지) ---
    sec_region = _auto_detect_section(image_path, _paddle, _img_bytes)
    if not sec_region:
        logger.info("SEC auto-detect failed, skipping SEC method (no hardcoded fallback)")
        return {"method_id": "SEC", "od": None, "id_val": None, "width": None, "classified_dims": [], "views": {}}

    # 뷰 감지 (sec_region의 OCR 결과 재사용)
    views = _detect_drawing_views(sec_region.get("ocr_dets", []), w, h, image_path)
    logger.info(f"Views detected: {list(views.keys())}")

    sx1 = int(w * sec_region["left"])
    sy1 = int(h * sec_region["top"])
    sx2 = int(w * sec_region["right"])
    sy2 = int(h * sec_region["bottom"])
    logger.info(f"SEC auto-detect: left={sec_region['left']:.2f} top={sec_region['top']:.2f} right={sec_region['right']:.2f} bottom={sec_region['bottom']:.2f}")

    # --- 1. 기본 크롭 → ID/W ---
    cropped = img.crop((sx1, sy1, sx2, sy2))
    cw, ch = cropped.size
    dets = _paddle(_img_bytes(cropped))

    nums = []
    for d in dets:
        text = d.get("text", "")
        # M-prefix 볼트 스펙 제거 (M10, M16, M48 등)
        if re.match(r"^M\d", text, re.IGNORECASE):
            continue
        # TORQUE/NM 제거
        if re.search(r"TORQUE|NM$", text, re.IGNORECASE):
            continue
        has_dia = bool(re.search(r"[ØøΦ⌀∅]", text))
        # 참조치수: 괄호로 감싼 값 (200) → 실치수 아님
        is_ref = bool(re.match(r"^\s*\(.*\)\s*$", text.strip()))
        cleaned = re.sub(r"[()]", "", text)
        m = re.search(r"(\d+\.?\d*)", cleaned)
        if not m:
            continue
        num = float(m.group(1))
        if num < 10 or num > 2000:
            continue
        bbox = d.get("bbox", [])
        if isinstance(bbox, list) and len(bbox) >= 4 and isinstance(bbox[0], list):
            x_c = sum(p[0] for p in bbox) / len(bbox)
            y_c = sum(p[1] for p in bbox) / len(bbox)
        else:
            continue
        nums.append({"num": num, "x": x_c / max(cw, 1), "y": y_c / max(ch, 1),
                      "has_dia": has_dia, "is_ref": is_ref})

    # --- 힌트 OD 사전 파싱 (ID 필터에 활용) ---
    _hint_od = None
    _m = re.search(r"OD\s*(\d+)", drawing_title, re.IGNORECASE)
    if _m:
        _hint_od = float(_m.group(1))
    else:
        _m = re.search(r"\((\d+)\s*[xX×]\s*(\d+)\)", drawing_title)
        if _m:
            _hint_od = float(_m.group(1))
        else:
            _m = re.search(r"(\d{3,4})\s*[xX×]\s*(\d{2,3})", drawing_title)
            if _m:
                _hint_od = float(_m.group(1))

    # ID: 중앙 (x < 0.60, y 30~70%), 최소 30mm
    id_cands = [n for n in nums if n["x"] < 0.60 and 0.30 < n["y"] < 0.70
                and n["num"] >= 30]
    # OD 참조값으로 ID 후보 필터: ID < OD * 0.95 (OD보다 작아야 함)
    od_ref = _hint_od
    if od_ref:
        id_cands = [n for n in id_cands if n["num"] < od_ref * 0.95]

    # Ø 기호 있는 후보 우선, 없으면 베어링 치수 범위(100~) 우선
    id_dia = [n for n in id_cands if n["has_dia"]]
    id_large = [n for n in id_cands if n["num"] >= 100]
    if id_dia:
        id_dia.sort(key=lambda n: n["num"])
        id_val = id_dia[0]["num"]
    elif id_large:
        id_large.sort(key=lambda n: n["num"])
        id_val = id_large[0]["num"]
    elif id_cands:
        id_cands.sort(key=lambda n: n["num"], reverse=True)
        id_val = id_cands[0]["num"]
    else:
        id_val = None

    # ID 재시도: 유효한 후보(100mm+) 없으면 적응형 이진화로 재OCR
    if not id_large and not id_dia:
        try:
            import cv2 as _cv2
            id_x2 = int(cw * 0.60)
            id_y1 = int(ch * 0.30)
            id_y2 = int(ch * 0.70)
            id_zone = cropped.crop((0, id_y1, id_x2, id_y2))
            arr = np.array(id_zone.convert("L"))
            adapt = _cv2.adaptiveThreshold(
                arr, 255, _cv2.ADAPTIVE_THRESH_GAUSSIAN_C, _cv2.THRESH_BINARY, 31, 10)
            adapt_img = Image.fromarray(adapt).resize(
                (adapt.shape[1] * 4, adapt.shape[0] * 4), Image.LANCZOS)
            retry_dets = _paddle(_img_bytes(adapt_img, fmt="PNG"))
            for d in retry_dets:
                text = d.get("text", "")
                if re.match(r"^M\d", text, re.IGNORECASE):
                    continue
                cleaned = re.sub(r"[{}\[\]()]", "", text)
                m = re.search(r"(\d{3,4}\.?\d*)", cleaned)
                if m:
                    num = float(m.group(1))
                    od_limit = od_ref * 0.95 if od_ref else 2000
                    if 50 <= num <= min(od_limit, 2000):
                        id_val = num
                        logger.info(f"SEC ID retry (adaptive): found {num} from '{text}'")
                        break
        except Exception as e:
            logger.debug(f"SEC ID retry failed: {e}")

    # W: 상단+하단 양쪽 공통값 (실치수 우선, 참조치수는 폴백)
    w_top_real = set(int(n["num"]) for n in nums if n["y"] < 0.20 and n["num"] >= 30
                     and not n.get("is_ref"))
    w_bot_real = set(int(n["num"]) for n in nums if n["y"] > 0.75 and n["num"] >= 30
                     and not n.get("is_ref"))
    w_top_all = set(int(n["num"]) for n in nums if n["y"] < 0.20 and n["num"] >= 30)
    w_bot_all = set(int(n["num"]) for n in nums if n["y"] > 0.75 and n["num"] >= 30)

    # 1순위: 실치수 공통값, 2순위: 전체(참조 포함) 공통값, 3순위: 단측
    w_common_real = w_top_real & w_bot_real
    w_common_all = w_top_all & w_bot_all
    if w_common_real:
        w_val = float(min(w_common_real))
    elif w_common_all:
        w_val = float(min(w_common_all))
    elif w_bot_real:
        w_val = float(max(w_bot_real))
    elif w_bot_all:
        w_val = float(max(w_bot_all))
    elif w_top_real:
        w_val = float(min(w_top_real))
    elif w_top_all:
        w_val = float(min(w_top_all))
    else:
        w_val = None

    # --- 2. 세로 슬라이딩 스캔 → OD ---
    # 자동 감지된 SECTION 영역 기준으로 스캔 범위 결정
    scan_left = sx1 + int((sx2 - sx1) * 0.30)  # SECTION 내부 30%~80%
    scan_right = sx1 + int((sx2 - sx1) * 0.80)
    scan_height = sy2 - sy1
    od_found = []
    for frac in [0.15, 0.30, 0.45, 0.60, 0.75]:
        scan_top = sy1 + int(scan_height * frac)
        scan_bot = sy1 + int(scan_height * (frac + 0.20))
        strip = img.crop((scan_left, scan_top, scan_right, min(scan_bot, sy2)))
        rotated = strip.rotate(-90, expand=True)
        up = rotated.resize((rotated.width * 3, rotated.height * 3), Image.LANCZOS)
        enhanced = ImageEnhance.Contrast(up).enhance(1.8).convert("L")
        scan_dets = _paddle(_img_bytes(enhanced, fmt="PNG"))
        for d in scan_dets:
            text = d.get("text", "")
            cleaned = re.sub(r"^[(\s]*0?", "", text)
            m = re.search(r"(\d{3,4}\.?\d*)", cleaned)
            if m:
                num = float(m.group(1))
                if 100 < num < 2000 and num not in [n for n, _ in od_found]:
                    od_found.append((num, text))
        time.sleep(0.5)

    # --- 3. 세션명 힌트 결합 (_hint_od는 ID 필터에서 이미 파싱됨) ---
    hint_od = _hint_od
    od_val = None
    if od_found:
        if hint_od:
            near = [(n, t) for n, t in od_found if abs(n - hint_od) / hint_od < 0.20]
            od_val = near[0][0] if near else max(n for n, _ in od_found)
        else:
            od_val = max(n for n, _ in od_found)
    elif hint_od:
        od_val = hint_od

    return {
        "od": f"Ø{od_val:.0f}" if od_val else None,
        "id": f"{id_val:.0f}" if id_val else None,
        "w": f"{w_val:.0f}" if w_val else None,
        "views": views,
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

    # --- SEC: SECTION 세로스캔 (ASSY 도면 전용) ---
    # ASSY 도면의 SECTION E-3 영역에서 세로 방향 Ø치수 스캔
    if "ASSY" in drawing_title.upper():
        try:
            sec_result = _run_section_scan(image_path, drawing_title)
            if any(sec_result.get(k) for k in ("od", "id", "w")):
                method_results["SEC"] = sec_result
                logger.info(f"SEC result: {sec_result}")
        except Exception as e:
            logger.warning(f"SEC method failed: {e}")

    # --- SIDE VIEW: 측면도 W 스캔 (ASSY only) ---
    if "ASSY" in drawing_title.upper():
        try:
            sec_views = method_results.get("SEC", {}).get("views", {})
            side_region = sec_views.get("auxiliary_view")
            if side_region:
                side_w = _scan_side_view(
                    image_path, side_region,
                    hint_od=_extract_num(method_results.get("SEC", {}).get("od")),
                    hint_id=_extract_num(method_results.get("SEC", {}).get("id")),
                )
                if side_w:
                    method_results["SIDE"] = {"od": None, "id": None, "w": f"{side_w:.0f}"}
                    logger.info(f"SIDE view W: {side_w}")
        except Exception as e:
            logger.warning(f"SIDE view scan failed: {e}")

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

    # K가 비정상이면 투표에서 제외 (ASSY 도면에서 케이싱 잡는 문제 방지)
    if k_plausible:
        od_votes = [_extract_num(m.get("od")) for m in method_results.values()]
        id_votes = [_extract_num(m.get("id")) for m in method_results.values()]
        w_votes = [_extract_num(m.get("w")) for m in method_results.values()]
    else:
        od_votes = [_extract_num(m.get("od")) for mk, m in method_results.items() if mk != "K"]
        id_votes = [_extract_num(m.get("id")) for mk, m in method_results.items() if mk != "K"]
        w_votes = [_extract_num(m.get("w")) for mk, m in method_results.items() if mk != "K"]

    vote_od = _vote_best(od_votes)
    vote_id = _vote_best(id_votes)
    vote_w = _vote_best(w_votes)

    # Strategy: ASSY 도면은 SEC 우선, 그 외 K 우선
    sec_result = method_results.get("SEC", {})
    sec_od = _extract_num(sec_result.get("od"))
    sec_id = _extract_num(sec_result.get("id"))
    sec_w = _extract_num(sec_result.get("w"))
    is_assy = "ASSY" in drawing_title.upper()

    # SEC ID plausibility: ID는 OD의 20~95% 범위여야 유효
    sec_id_ok = (sec_id is not None and sec_od is not None
                 and sec_od * 0.20 < sec_id < sec_od * 0.95)

    if is_assy and (sec_od or sec_id):
        # --- OD 결정 ---
        # 기본: SEC OD 사용 (SECTION OCR이 ASSY 도면에서 가장 신뢰)
        final_od = sec_od

        # 예외 1: K가 plausible하고 다른 비-SEC 방법이 K에 동의 → K로 오버라이드
        # (Thrust처럼 K 원검출이 성공하고 SEC가 하우징 치수를 잡는 경우)
        k_od_override = False
        if k_plausible and k_od and sec_od and abs(sec_od - k_od) / max(k_od, 1) > 0.15:
            for mk, mv in method_results.items():
                if mk in ("K", "SEC"):
                    continue
                mv_od = _extract_num(mv.get("od"))
                if mv_od and abs(mv_od - k_od) / max(k_od, 1) < 0.05:
                    k_od_override = True
                    break
            if k_od_override:
                final_od, final_id, final_w = k_od, k_id, k_w
                logger.info(f"K-override: K plausible + corroborated → OD={k_od}")

        # 예외 2: SEC OD와 투표가 30%+ 차이 & 투표에 2+ 지지 → 투표 사용
        # (T5처럼 SECTION에 실제 OD가 없고 S01/S02가 정답을 찾는 경우)
        if not k_od_override and final_od and vote_od:
            if abs(final_od - vote_od) / max(vote_od, 1) > 0.30:
                supporters = sum(1 for v in od_votes if v and abs(v - vote_od) <= 5.0)
                if supporters >= 2:
                    final_od = vote_od
                    logger.info(f"Vote-override OD: SEC={sec_od} → vote={vote_od} ({supporters} supporters)")

        # --- ID 결정 ---
        if not k_od_override:
            # SEC ID plausibility를 최종 OD 기준으로 재평가
            sec_id_ok_final = (sec_id is not None and final_od is not None
                               and final_od * 0.20 < sec_id < final_od * 0.95)
            final_id = sec_id if sec_id_ok_final else (k_id if k_id else vote_id)

            # OD가 vote로 교체된 경우: K.ID가 베어링 비율에 더 적합하면 K 사용
            # (SECTION에 ID가 없어서 엉뚱한 값을 잡는 경우 대비)
            if final_od and final_od != sec_od and k_id and sec_id:
                k_ratio = k_id / final_od
                sec_ratio = sec_id / final_od
                k_typical = 0.30 < k_ratio < 0.90
                sec_typical = 0.30 < sec_ratio < 0.90
                if k_typical and not sec_typical:
                    final_id = k_id
                    logger.info(f"K-ID preferred: ratio {k_ratio:.2f} vs SEC {sec_ratio:.2f}")

        # --- W 결정 ---
        if not k_od_override:
            side_w = _extract_num(method_results.get("SIDE", {}).get("w"))
            # SIDE W는 SEC W가 없을 때만 사용 (SEC W가 있으면 SECTION이 더 신뢰)
            # 또는 SIDE W가 hint_id와 일치하면 사용 (T3/T4: ID=W=260 패턴)
            if side_w and not sec_w:
                final_w = side_w
                logger.info(f"SIDE-fill W: {side_w} (SEC W 없음)")
            elif side_w and sec_w and final_id and abs(side_w - final_id) / max(final_id, 1) < 0.05:
                # SIDE W가 ID와 일치 → ID=W인 특이 케이스 (T3/T4)
                final_w = side_w
                logger.info(f"SIDE-override W: SEC={sec_w} → SIDE={side_w} (matches ID={final_id})")
            else:
                final_w = sec_w if sec_w else (k_w if k_w else vote_w)

        strategy = "sec_priority"
        logger.info(f"SEC-priority: OD={final_od} ID={final_id} W={final_w}")
    elif k_plausible:
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
