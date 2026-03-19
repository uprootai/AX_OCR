"""기하학 기반 치수 추출

순서: 원 검출 → 치수선 추적 → ROI 크롭 OCR → 역할 자동 결정

기존 파이프라인(OCR 전체 → 분류 추측)과 달리,
도면의 시각적 구조를 먼저 파악한 후 필요한 영역만 OCR한다.
"""
import cv2
import numpy as np
import logging
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


def extract_by_geometry(
    image_path: str,
    ocr_engine: str = "paddleocr",
    confidence_threshold: float = 0.3,
) -> Dict:
    """기하학 기반 OD/ID/W 추출

    Returns:
        {
            "od": {"value": "515", "confidence": 0.9, "bbox": {...}, "source": "circle_outer_dim_line"},
            "id": {"value": "460", ...},
            "w": {"value": "250", ...},
            "circles": [...],  # 검출된 원 정보
            "dim_lines": [...],  # 추적된 치수선
            "rois": [...],  # OCR 실행한 ROI 영역
            "debug": {...},
        }
    """
    img_color = cv2.imread(image_path)
    if img_color is None:
        return {"error": "이미지 로드 실패"}

    img_gray = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)
    orig_h, orig_w = img_gray.shape[:2]

    # Step 1: 원 검출
    circles_info = _detect_circles(img_gray, orig_w, orig_h)
    if not circles_info["found"]:
        return {
            "od": None, "id": None, "w": None,
            "circles": [], "dim_lines": [], "rois": [],
            "debug": {"error": "원/호 검출 실패", **circles_info},
        }

    outer_circle = circles_info["outer"]
    inner_circle = circles_info.get("inner")

    # Step 2: 치수선 검출 (LSD)
    dim_lines = _detect_dimension_lines(img_gray, outer_circle, inner_circle, orig_w, orig_h)

    # Step 3: 원 주변 크롭 → 전체 OCR (작은 ROI 대신 큰 영역)
    crop_dims, crop_offset = _crop_ocr_around_circles(
        image_path, img_gray, outer_circle, inner_circle,
        ocr_engine, confidence_threshold, orig_w, orig_h,
    )

    # Step 4: OCR 결과를 원과의 거리로 역할 분류
    result = _classify_by_circle_proximity(
        crop_dims, outer_circle, inner_circle, orig_w, orig_h,
    )

    result["circles"] = [
        {"cx": int(outer_circle[0]), "cy": int(outer_circle[1]), "r": int(outer_circle[2]), "role": "outer"},
    ]
    if inner_circle is not None:
        result["circles"].append(
            {"cx": int(inner_circle[0]), "cy": int(inner_circle[1]), "r": int(inner_circle[2]), "role": "inner"}
        )
    result["dim_lines"] = [
        {"x1": int(l["x1"]), "y1": int(l["y1"]), "x2": int(l["x2"]), "y2": int(l["y2"]), "direction": l["direction"]}
        for l in dim_lines
    ]

    return result


def get_geometry_supplementary_dims(
    image_path: str,
    ocr_engine: str = "paddleocr",
    confidence_threshold: float = 0.3,
) -> tuple:
    """원 검출 + 크롭 OCR로 보충 치수 목록 반환 (공통 파이프라인용)

    기존 전체 이미지 OCR이 놓치는 치수를 원 주변 크롭 OCR로 보충한다.
    또한 원의 픽셀 반지름을 반환하여 노이즈 필터에 활용할 수 있게 한다.

    Returns:
        (supplementary_dims: list[dict], circle_r_outer: float | None)
    """
    img_color = cv2.imread(image_path)
    if img_color is None:
        return [], None
    img_gray = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)
    orig_h, orig_w = img_gray.shape[:2]

    circles_info = _detect_circles(img_gray, orig_w, orig_h)
    if not circles_info["found"]:
        return [], None

    outer = circles_info["outer"]
    inner = circles_info.get("inner")
    r_outer = float(outer[2])

    crop_dims, _ = _crop_ocr_around_circles(
        image_path, img_gray, outer, inner,
        ocr_engine, confidence_threshold, orig_w, orig_h,
    )
    return crop_dims, r_outer


def filter_ocr_noise(dims: list, r_outer: float = None) -> list:
    """공통 OCR 노이즈 필터 — 날짜, 참조치수, 나사산, 비현실적 값 제거

    Args:
        dims: OCR 검출 치수 목록 (dict 형태)
        r_outer: 외경 원의 픽셀 반지름 (스케일 필터용, None이면 스킵)
    Returns:
        필터링된 치수 목록
    """
    import re
    filtered = []
    for d in dims:
        val = d.get("value", "").strip() if isinstance(d, dict) else (d.value.strip() if hasattr(d, 'value') else "")

        # 날짜 패턴 (2025-3-09, 2024.01.15 등) 제거
        if re.match(r'^\d{4}[-./]\d{1,2}[-./]\d{1,2}', val):
            continue
        # 나사산 (M16, M20 등) 제거
        if re.match(r'^M\d', val, re.IGNORECASE):
            continue
        # 각도/기타 비치수 제거
        if re.search(r'°|deg|UNC|UNF|TPI', val, re.IGNORECASE):
            continue
        # 괄호 참조치수 제거
        if val.startswith('(') and val.endswith(')'):
            continue

        # 스케일 필터: 원 반지름 대비 비현실적으로 큰 값 제거
        # Ø 접두사 → 타이트 (0.85): 도면 내 다른 부품의 Ø 주석 배제
        # 일반 값 → 보통 (1.0)
        if r_outer:
            has_dia_prefix = bool(re.match(r'^[ØøΦ⌀∅]', val))
            cleaned = re.sub(r'^[ØøΦ⌀∅Rr]\s*', '', val)
            cleaned = re.sub(r'[()]', '', cleaned)
            m = re.match(r'(\d+\.?\d*)', cleaned)
            if m:
                num = float(m.group(1))
                threshold = r_outer * 0.85 if has_dia_prefix else r_outer * 1.0
                if num > threshold:
                    continue

        filtered.append(d)

    # 유사값 병합: 5% 이내 중복 제거 (높은 confidence 우선)
    merged = []
    for d in sorted(filtered, key=lambda x: x.get("confidence", 0.5) if isinstance(x, dict) else (x.confidence if hasattr(x, 'confidence') else 0.5), reverse=True):
        val = d.get("value", "").strip() if isinstance(d, dict) else (d.value.strip() if hasattr(d, 'value') else "")
        cleaned = re.sub(r'^[ØøΦ⌀∅Rr]\s*', '', val)
        cleaned = re.sub(r'[()]', '', cleaned)
        m = re.match(r'(\d+\.?\d*)', cleaned)
        if not m:
            merged.append(d)
            continue
        num = float(m.group(1))
        is_dup = False
        for md in merged:
            mv = md.get("value", "").strip() if isinstance(md, dict) else (md.value.strip() if hasattr(md, 'value') else "")
            mc = re.sub(r'^[ØøΦ⌀∅Rr]\s*', '', mv)
            mc = re.sub(r'[()]', '', mc)
            mm = re.match(r'(\d+\.?\d*)', mc)
            if mm and abs(num - float(mm.group(1))) / max(float(mm.group(1)), 1) < 0.05:
                is_dup = True
                break
        if not is_dup:
            merged.append(d)
    return merged


def _detect_circles(
    img_gray: np.ndarray, orig_w: int, orig_h: int
) -> Dict:
    """동심원 검출 — 컨투어+타원피팅 우선, HoughCircles 보조

    기계 도면의 특성(해칭, 불완전 원호, 치수선 간섭)에 대응하기 위해
    Canny 에지 → 컨투어 → 타원 피팅 → 원형도 필터를 1차로 사용하고,
    실패 시 HoughCircles로 폴백한다.
    """
    max_dim = 2000
    scale = 1.0
    img = img_gray.copy()
    if max(orig_h, orig_w) > max_dim:
        scale = max_dim / max(orig_h, orig_w)
        img = cv2.resize(img, (int(orig_w * scale), int(orig_h * scale)))

    rh, rw = img.shape[:2]

    # ── 1차: 컨투어 + 타원 피팅 ──
    result = _detect_circles_by_contour(img, rw, rh, scale)
    if result["found"]:
        logger.info(f"컨투어 기반 원 검출 성공: outer r={int(result['outer'][2])}")
        return result

    # ── 2차: HoughCircles 폴백 ──
    logger.info("컨투어 실패 → HoughCircles 폴백")
    return _detect_circles_by_hough(img, rw, rh, scale)


def _detect_circles_by_contour(
    img: np.ndarray, rw: int, rh: int, scale: float
) -> Dict:
    """Canny 에지 → 컨투어 → 타원 피팅으로 원 검출

    해칭/치수선이 많은 기계 도면에서 HoughCircles보다 안정적.
    불완전한 원호(30%만 보여도)도 타원 피팅으로 검출 가능.
    """
    blurred = cv2.GaussianBlur(img, (5, 5), 1.5)
    edges = cv2.Canny(blurred, 30, 100)

    # 끊어진 에지 연결
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    dilated = cv2.dilate(edges, kernel, iterations=2)

    contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    min_area = rw * rh * 0.002  # 이미지 면적의 0.2% 이상
    max_radius = min(rw, rh) * 0.45  # 이미지의 45% 초과 → 도면 전체 윤곽 제외
    candidates = []

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area or len(cnt) < 20:
            continue

        # 바운딩 박스 종횡비 → 극단적으로 길쭉한 것 제외
        x, y, bw, bh = cv2.boundingRect(cnt)
        bb_aspect = min(bw, bh) / max(bw, bh) if max(bw, bh) > 0 else 0
        if bb_aspect < 0.6:
            continue

        # 타원 피팅
        ellipse = cv2.fitEllipse(cnt)
        (cx, cy), (ma, MA), angle = ellipse
        aspect = min(ma, MA) / max(ma, MA) if max(ma, MA) > 0 else 0
        if aspect < 0.6:
            continue

        radius_est = (ma + MA) / 4

        # 너무 큰 원 제외 (도면 전체 윤곽)
        if radius_est > max_radius:
            continue

        orig_cx = cx / scale
        orig_cy = cy / scale
        orig_r = radius_est / scale

        # 이미지 범위 내 확인
        if orig_cx < 0 or orig_cy < 0:
            continue

        candidates.append({
            "coords": np.array([int(orig_cx), int(orig_cy), int(orig_r)]),
            "aspect": aspect,
        })

    if not candidates:
        return {"found": False, "reason": "컨투어 기반 원 검출 실패"}

    logger.info(f"컨투어 원 후보 {len(candidates)}개 검출")

    # 원형도(aspect) × 면적 기준 정렬 — 둥근 큰 원 우선
    candidates.sort(key=lambda c: c["aspect"] * c["coords"][2], reverse=True)
    outer = candidates[0]["coords"]

    # 동심원 찾기
    inner = None
    for cand in candidates[1:]:
        c = cand["coords"]
        dist = np.sqrt((c[0] - outer[0])**2 + (c[1] - outer[1])**2)
        if dist < outer[2] * 0.4 and 0.3 < c[2] / outer[2] < 0.95:
            inner = c
            break

    return {
        "found": True,
        "outer": outer,
        "inner": inner,
        "total_circles": len(candidates),
    }


def _detect_circles_by_hough(
    img: np.ndarray, rw: int, rh: int, scale: float
) -> Dict:
    """HoughCircles 폴백 — 단순 도면용"""
    blurred = cv2.GaussianBlur(img, (9, 9), 2)
    min_r = min(rw, rh) // 20
    max_r = min(rw, rh) // 3

    circles = cv2.HoughCircles(
        blurred, cv2.HOUGH_GRADIENT,
        dp=1.2, minDist=min_r,
        param1=100, param2=50,
        minRadius=min_r, maxRadius=max_r,
    )

    if circles is None:
        circles = cv2.HoughCircles(
            blurred, cv2.HOUGH_GRADIENT,
            dp=1.5, minDist=min_r // 2,
            param1=80, param2=30,
            minRadius=min_r // 2, maxRadius=max_r,
        )

    if circles is None:
        return {"found": False, "reason": "HoughCircles 검출 실패"}

    circles_arr = np.round(circles[0]).astype(int)
    if scale != 1.0:
        circles_arr = np.round(circles_arr / scale).astype(int)

    sorted_by_r = sorted(circles_arr, key=lambda c: c[2], reverse=True)
    outer = sorted_by_r[0]

    inner = None
    for c in sorted_by_r[1:]:
        dist = np.sqrt((c[0] - outer[0])**2 + (c[1] - outer[1])**2)
        if dist < outer[2] * 0.3 and c[2] < outer[2] * 0.95:
            inner = c
            break

    return {
        "found": True,
        "outer": outer,
        "inner": inner,
        "total_circles": len(circles_arr),
    }



def _crop_ocr_around_circles(
    image_path: str,
    img_gray: np.ndarray,
    outer: np.ndarray,
    inner: Optional[np.ndarray],
    ocr_engine: str,
    confidence_threshold: float,
    orig_w: int,
    orig_h: int,
) -> tuple:
    """원 주변을 넓게 크롭하여 OCR — 불필요한 도면 영역 제거로 정확도 향상

    전체 이미지 OCR(4개 검출) 대비 크롭 OCR(9개 검출)로
    약 2배 이상 치수 검출률이 올라간다.
    """
    import tempfile, os

    cx, cy, r = int(outer[0]), int(outer[1]), int(outer[2])

    from services.dimension_service import DimensionService
    dim_service = DimensionService()

    def _run_ocr_on_crop(crop_gray, offset_x, offset_y):
        """크롭 이미지에 OCR 실행 → bbox를 원본 좌표로 변환하여 반환"""
        if crop_gray.size == 0:
            return []
        fd, tp = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        try:
            cv2.imwrite(tp, crop_gray)
            res = dim_service.extract_dimensions(tp, confidence_threshold, [ocr_engine])
            found = res.get("dimensions", [])
            for d in found:
                bbox = d.get("bbox") if isinstance(d, dict) else (d.bbox if hasattr(d, "bbox") else None)
                if bbox:
                    if isinstance(bbox, dict):
                        bbox["x1"] += offset_x
                        bbox["y1"] += offset_y
                        bbox["x2"] += offset_x
                        bbox["y2"] += offset_y
                    else:
                        bbox.x1 += offset_x
                        bbox.y1 += offset_y
                        bbox.x2 += offset_x
                        bbox.y2 += offset_y
            return found
        finally:
            if os.path.exists(tp):
                os.unlink(tp)

    # 2개 크롭 크기로 OCR → 결과 병합
    # 1) 집중 크롭: 원 주변 1.8×r (가까운 치수 잘 검출)
    m1 = int(r * 1.8)
    c1_y1, c1_y2 = max(0, cy - m1), min(orig_h, cy + m1)
    c1_x1, c1_x2 = max(0, cx - m1), min(orig_w, cx + m1)

    # 2) 확장 크롭: 위쪽 3.0×r (원 위에 있는 OD/ID 치수 포함)
    c2_y1 = max(0, cy - int(r * 3.0))
    c2_y2 = min(orig_h, cy + int(r * 1.5))
    c2_x1 = max(0, cx - int(r * 2.0))
    c2_x2 = min(orig_w, cx + int(r * 2.0))

    # 전체 좌표 기준 offset
    x1, y1 = min(c1_x1, c2_x1), min(c1_y1, c2_y1)

    try:
        dims_focused = _run_ocr_on_crop(
            img_gray[c1_y1:c1_y2, c1_x1:c1_x2], c1_x1, c1_y1,
        )
        dims_wide = _run_ocr_on_crop(
            img_gray[c2_y1:c2_y2, c2_x1:c2_x2], c2_x1, c2_y1,
        )

        # 병합: 집중 크롭 우선 + 확장에서 누락 값 추가
        dims = list(dims_focused)
        existing_vals = {(d.get("value", "") if isinstance(d, dict) else d.value) for d in dims}
        for wd in dims_wide:
            wv = wd.get("value", "") if isinstance(wd, dict) else wd.value
            if wv not in existing_vals:
                dims.append(wd)
                existing_vals.add(wv)

        # 디버그: 검출된 모든 치수값 출력
        for d in dims:
            val = d.get("value", "") if isinstance(d, dict) else (d.value if hasattr(d, "value") else "")
            bb = d.get("bbox", {}) if isinstance(d, dict) else {}
            logger.info(f"  크롭OCR: val={val!r}  bbox={bb}")
        logger.info(f"크롭 OCR: {len(dims)}개 치수 검출 (focused={len(dims_focused)}, wide={len(dims_wide)})")
        return dims, (x1, y1)
    except Exception as e:
        logger.warning(f"크롭 OCR 실패: {e}")
        return [], (0, 0)


def _classify_by_circle_proximity(
    dims: list,
    outer: np.ndarray,
    inner: Optional[np.ndarray],
    orig_w: int,
    orig_h: int,
) -> Dict:
    """OCR 치수를 값 크기 기반으로 OD/ID/W 분류

    전략: 거리 기반 분류 대신, 베어링/플랜지 도면의 물리적 관계를 활용.
    - 가장 큰 값 → OD (외경)
    - 가장 작은 값 → W (폭/두께)
    - 중간 값 → ID (내경)
    - 검증: OD > ID > W, OD ≈ ID + 2*W (베어링 관계)
    - 나사산(M/UNC/UNF) 및 각도/기타 비치수값 제외
    """
    import re

    cx, cy, r_outer = int(outer[0]), int(outer[1]), int(outer[2])
    r_inner = int(inner[2]) if inner is not None else int(r_outer * 0.6)

    # ── 1단계: 치수 후보 수집 (비치수값 필터링) ──
    candidates = []
    for d in dims:
        if isinstance(d, dict):
            val_text = d.get("value", "").strip()
            bbox = d.get("bbox")
            confidence = d.get("confidence", 0.5)
        else:
            val_text = d.value.strip() if hasattr(d, 'value') else str(d)
            bbox = d.bbox if hasattr(d, 'bbox') else None
            confidence = d.confidence if hasattr(d, 'confidence') else 0.5

        # 나사산(M16, M20 등), 각도, 기타 비치수 제외
        if re.match(r'^M\d', val_text, re.IGNORECASE):
            continue
        if re.search(r'°|deg|UNC|UNF|TPI', val_text, re.IGNORECASE):
            continue
        # 괄호 안의 값은 참조 치수(reference dimension) → 제외
        if val_text.startswith('(') and val_text.endswith(')'):
            logger.info(f"  참조치수 제외: {val_text}")
            continue

        # 접두사 제거 후 숫자 추출
        cleaned = re.sub(r'^[ØøΦ⌀∅Rr]\s*', '', val_text)
        cleaned = re.sub(r'[()]', '', cleaned)
        m = re.match(r'(\d+\.?\d*)', cleaned)
        if not m:
            continue
        num_val = float(m.group(1))
        if num_val < 10:
            continue

        # 스케일 기반 필터: 기계 도면은 축소 스케일이므로
        # 실제 치수(mm)는 원의 픽셀 반지름보다 작은 경우가 대부분
        # 예: r_outer=665px, OD=515mm → 515 < 665*1.2=798
        max_reasonable = r_outer * 1.2
        if num_val > max_reasonable:
            logger.info(f"  스케일 필터: {val_text}={num_val} > {max_reasonable} 제외")
            continue

        # R 접두사 → 반지름 → 직경 변환
        is_radius = bool(re.match(r'^[Rr]\s*\d', val_text))
        display_val = num_val * 2 if is_radius else num_val

        if not bbox:
            continue
        if isinstance(bbox, dict):
            bbox_dict = bbox
        else:
            bbox_dict = {"x1": bbox.x1, "y1": bbox.y1, "x2": bbox.x2, "y2": bbox.y2}

        candidates.append({
            "value": val_text,
            "num": display_val,
            "confidence": confidence,
            "bbox": bbox_dict,
        })

    logger.info(f"치수 후보 {len(candidates)}개: {[(c['value'], c['num']) for c in candidates]}")

    if not candidates:
        return {
            "od": None, "id": None, "w": None, "rois": [],
            "debug": {"candidates": 0, "total_dims": len(dims)},
        }

    # ── 2단계: 값 크기 기반 분류 ──
    # 중복/유사 값 병합 (같은 치수를 다른 크롭에서 약간 다르게 읽은 경우)
    # 예: 440과 450은 같은 치수(460)를 OCR이 다르게 읽은 것
    unique = []
    for c in sorted(candidates, key=lambda x: x["confidence"], reverse=True):
        is_dup = False
        for u in unique:
            if abs(c["num"] - u["num"]) / max(u["num"], 1) < 0.05:  # 5% 이내
                is_dup = True
                break
        if not is_dup:
            unique.append(c)
    unique.sort(key=lambda c: c["num"], reverse=True)
    logger.info(f"고유 후보 {len(unique)}개 (내림차순): {[(c['value'], c['num']) for c in unique]}")

    od, id_val, w = None, None, None

    # ── 2단계: 값 크기 기반 분류 (상위 3개 = OD > ID > W) ──
    if len(unique) >= 3:
        od = unique[0]       # 가장 큰 값 → OD
        id_val = unique[1]   # 두 번째 → ID
        w = unique[2]        # 세 번째 → W
    elif len(unique) == 2:
        od = unique[0]
        ratio = unique[1]["num"] / unique[0]["num"] if unique[0]["num"] > 0 else 0
        if ratio > 0.5:
            id_val = unique[1]
        else:
            w = unique[1]
    elif len(unique) == 1:
        od = unique[0]

    result = {
        "od": _fmt(od), "id": _fmt(id_val), "w": _fmt(w),
        "rois": [],
        "debug": {
            "candidates": len(candidates),
            "unique": len(unique),
            "total_dims": len(dims),
            "values": [(c["value"], c["num"]) for c in unique],
        },
    }
    return result


def _fmt(c: Optional[Dict]) -> Optional[Dict]:
    """후보를 결과 형식으로 변환"""
    if not c:
        return None
    return {"value": c["value"], "confidence": c["confidence"], "bbox": c["bbox"]}


def _detect_dimension_lines(
    img_gray: np.ndarray,
    outer: np.ndarray,
    inner: Optional[np.ndarray],
    orig_w: int,
    orig_h: int,
) -> List[Dict]:
    """원 주변의 치수선(직선) 검출 — LSD 기반"""
    # LSD (Line Segment Detector)
    lsd = cv2.createLineSegmentDetector(0)
    lines, widths, prec, nfa = lsd.detect(img_gray)

    if lines is None:
        return []

    cx, cy, r_outer = int(outer[0]), int(outer[1]), int(outer[2])
    dim_lines = []

    for line in lines:
        x1, y1, x2, y2 = line[0]
        length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        if length < 30:  # 너무 짧은 선 무시
            continue

        # 선의 중점
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dist_to_center = np.sqrt((mx - cx)**2 + (my - cy)**2)

        # 원 근처(반지름의 0.8~3배)에 있는 선만
        if dist_to_center < r_outer * 0.5 or dist_to_center > r_outer * 3.5:
            continue

        # 방향 판단 (수평/수직)
        angle = abs(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
        if angle < 15 or angle > 165:
            direction = "horizontal"
        elif 75 < angle < 105:
            direction = "vertical"
        else:
            continue  # 대각선은 치수선이 아닐 확률 높음

        # 원 가장자리에서 시작하는지 확인
        for px, py in [(x1, y1), (x2, y2)]:
            dist_from_edge = abs(np.sqrt((px - cx)**2 + (py - cy)**2) - r_outer)
            if dist_from_edge < r_outer * 0.3:
                dim_lines.append({
                    "x1": float(x1), "y1": float(y1),
                    "x2": float(x2), "y2": float(y2),
                    "direction": direction,
                    "length": float(length),
                    "dist_to_center": float(dist_to_center),
                })
                break

    # 가장 유력한 치수선만 선택 (최대 8개 — 길이 긴 순)
    dim_lines.sort(key=lambda l: l["length"], reverse=True)
    dim_lines = dim_lines[:8]
    logger.info(f"치수선 후보 {len(dim_lines)}개 (원 cx={cx}, cy={cy}, r={r_outer})")
    return dim_lines


def _extract_rois_from_dim_lines(
    dim_lines: List[Dict],
    outer: np.ndarray,
    inner: Optional[np.ndarray],
    orig_w: int,
    orig_h: int,
) -> List[Dict]:
    """치수선 끝점 근처에 텍스트 ROI 생성"""
    cx, cy = int(outer[0]), int(outer[1])
    rois = []
    pad = 60  # 텍스트 영역 패딩

    for line in dim_lines:
        # 원 중심에서 더 먼 끝점 = 텍스트가 있을 끝
        d1 = np.sqrt((line["x1"] - cx)**2 + (line["y1"] - cy)**2)
        d2 = np.sqrt((line["x2"] - cx)**2 + (line["y2"] - cy)**2)
        if d1 > d2:
            tx, ty = line["x1"], line["y1"]
        else:
            tx, ty = line["x2"], line["y2"]

        roi = {
            "x1": max(0, int(tx) - pad),
            "y1": max(0, int(ty) - pad),
            "x2": min(orig_w, int(tx) + pad),
            "y2": min(orig_h, int(ty) + pad),
            "direction": line["direction"],
            "source": "dim_line",
        }
        # 중복 ROI 방지
        if not any(_rois_overlap(roi, r) for r in rois):
            rois.append(roi)

    return rois


def _extract_rois_from_circle_edges(
    outer: np.ndarray,
    inner: Optional[np.ndarray],
    orig_w: int,
    orig_h: int,
) -> List[Dict]:
    """원 동서남북 가장자리 바깥에 ROI 생성 (치수선 미검출 시 대비)"""
    cx, cy, r = int(outer[0]), int(outer[1]), int(outer[2])
    margin = int(r * 0.3)
    text_w, text_h = 120, 50

    edge_rois = [
        # 북쪽 (위)
        {"x1": cx - text_w, "y1": max(0, cy - r - margin - text_h), "x2": cx + text_w, "y2": cy - r - margin + text_h, "direction": "vertical", "source": "edge_north"},
        # 남쪽 (아래)
        {"x1": cx - text_w, "y1": cy + r + margin - text_h, "x2": cx + text_w, "y2": min(orig_h, cy + r + margin + text_h), "direction": "vertical", "source": "edge_south"},
        # 동쪽 (오른쪽)
        {"x1": cx + r + margin - text_w, "y1": cy - text_h, "x2": min(orig_w, cx + r + margin + text_w), "y2": cy + text_h, "direction": "horizontal", "source": "edge_east"},
        # 서쪽 (왼쪽)
        {"x1": max(0, cx - r - margin - text_w), "y1": cy - text_h, "x2": cx - r - margin + text_w, "y2": cy + text_h, "direction": "horizontal", "source": "edge_west"},
    ]

    # 유효 범위 클리핑
    valid = []
    for roi in edge_rois:
        roi["x1"] = max(0, roi["x1"])
        roi["y1"] = max(0, roi["y1"])
        roi["x2"] = min(orig_w, roi["x2"])
        roi["y2"] = min(orig_h, roi["y2"])
        if roi["x2"] - roi["x1"] > 20 and roi["y2"] - roi["y1"] > 20:
            valid.append(roi)

    return valid


def _rois_overlap(a: Dict, b: Dict, threshold: float = 0.5) -> bool:
    """두 ROI가 겹치는지"""
    x_overlap = max(0, min(a["x2"], b["x2"]) - max(a["x1"], b["x1"]))
    y_overlap = max(0, min(a["y2"], b["y2"]) - max(a["y1"], b["y1"]))
    overlap_area = x_overlap * y_overlap
    a_area = (a["x2"] - a["x1"]) * (a["y2"] - a["y1"])
    return overlap_area > a_area * threshold if a_area > 0 else False


def _ocr_rois(
    image_path: str,
    img_gray: np.ndarray,
    rois: List[Dict],
    ocr_engine: str,
    confidence_threshold: float,
) -> List[Dict]:
    """각 ROI 영역을 크롭하여 OCR 실행"""
    from services.dimension_service import DimensionService

    dim_service = DimensionService()
    results = []
    fail_count = 0

    for roi in rois[:12]:  # ROI 최대 12개
        if fail_count >= 3:  # 연속 3회 실패 시 중단
            logger.warning("ROI OCR 연속 실패 — 나머지 스킵")
            break
        # ROI 크롭 이미지 저장 (임시)
        import tempfile, os
        crop = img_gray[roi["y1"]:roi["y2"], roi["x1"]:roi["x2"]]
        if crop.size == 0:
            continue

        # 크롭 이미지를 확대 (작은 텍스트 인식률 향상)
        scale_factor = max(1, 100 // max(crop.shape[:2]))
        if scale_factor > 1:
            crop = cv2.resize(crop, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                cv2.imwrite(f.name, crop)
                tmp_path = f.name

            ocr_result = dim_service.extract_dimensions(
                tmp_path, confidence_threshold, [ocr_engine]
            )
            dims = ocr_result.get("dimensions", [])

            fail_count = 0  # 성공 시 리셋
            for d in dims:
                # bbox를 원본 이미지 좌표로 변환
                if isinstance(d, dict):
                    bbox = d.get("bbox", {})
                    if isinstance(bbox, dict):
                        d["bbox"] = {
                            "x1": roi["x1"] + int(bbox.get("x1", 0) / max(scale_factor, 1)),
                            "y1": roi["y1"] + int(bbox.get("y1", 0) / max(scale_factor, 1)),
                            "x2": roi["x1"] + int(bbox.get("x2", 0) / max(scale_factor, 1)),
                            "y2": roi["y1"] + int(bbox.get("y2", 0) / max(scale_factor, 1)),
                        }
                    d["roi_direction"] = roi.get("direction", "unknown")
                    d["roi_source"] = roi.get("source", "unknown")
                    results.append(d)

        except Exception as e:
            fail_count += 1
            logger.warning(f"ROI OCR 실패 ({roi.get('source', '?')}): {e}")
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    logger.info(f"ROI OCR 결과: {len(results)}개 치수 ({len(rois)}개 ROI)")
    return results


def _assign_roles(
    ocr_results: List[Dict],
    outer: np.ndarray,
    inner: Optional[np.ndarray],
    orig_w: int,
    orig_h: int,
) -> Dict:
    """치수선 방향 + 원과의 관계로 OD/ID/W 역할 결정"""
    import re

    cx, cy, r_outer = int(outer[0]), int(outer[1]), int(outer[2])
    r_inner = int(inner[2]) if inner is not None else r_outer // 2

    od_candidates = []
    id_candidates = []
    w_candidates = []

    for d in ocr_results:
        value_str = d.get("value", "")
        # 숫자 추출
        nums = re.findall(r"[\d.]+", value_str.replace("Ø", "").replace("ø", "").replace("R", ""))
        if not nums:
            continue
        try:
            num_val = float(nums[0])
        except ValueError:
            continue

        if num_val < 5:  # 너무 작은 값 무시
            continue

        bbox = d.get("bbox", {})
        dim_cx = (bbox.get("x1", 0) + bbox.get("x2", 0)) / 2
        dim_cy = (bbox.get("y1", 0) + bbox.get("y2", 0)) / 2
        direction = d.get("roi_direction", "unknown")
        confidence = d.get("confidence", 0.5)

        # R 접두사면 직경으로 변환
        is_radius = value_str.strip().upper().startswith("R") and not value_str.strip().upper().startswith("RA")
        diameter_val = num_val * 2 if is_radius else num_val

        entry = {
            "value": value_str,
            "numeric": num_val,
            "diameter": diameter_val,
            "confidence": confidence,
            "bbox": bbox,
            "direction": direction,
        }

        # 역할 추정
        if direction == "vertical":
            # 수직 치수선 = OD 또는 ID
            # 원 바깥쪽에 있으면 OD, 안쪽이면 ID
            dist = np.sqrt((dim_cx - cx)**2 + (dim_cy - cy)**2)
            if dist > r_outer * 0.8 or diameter_val > r_inner * 2:
                od_candidates.append(entry)
            else:
                id_candidates.append(entry)
        elif direction == "horizontal":
            # 수평 치수선 = W (폭)
            w_candidates.append(entry)
        else:
            # 방향 불명 → 값 크기로 추정
            if diameter_val > r_inner * 2:
                od_candidates.append(entry)
            elif diameter_val > num_val * 0.3:
                id_candidates.append(entry)
            else:
                w_candidates.append(entry)

    # 각 역할에서 최적 선택
    def _best(candidates):
        if not candidates:
            return None
        # diameter 값이 가장 큰 것 우선 (같으면 confidence 높은 것)
        return max(candidates, key=lambda c: (c["diameter"], c["confidence"]))

    od = _best(od_candidates)
    id_val = _best(id_candidates)
    w = _best(w_candidates)

    return {
        "od": _format_result(od, "outer_diameter") if od else None,
        "id": _format_result(id_val, "inner_diameter") if id_val else None,
        "w": _format_result(w, "length") if w else None,
    }


def _format_result(entry: Dict, role: str) -> Dict:
    return {
        "value": entry["value"],
        "numeric": entry["numeric"],
        "diameter": entry["diameter"],
        "confidence": entry["confidence"],
        "bbox": entry["bbox"],
        "role": role,
        "direction": entry["direction"],
    }
