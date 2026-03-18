"""OpenCV 기반 OD/ID/폭 분류기

도면 이미지에서 시각적 특징을 분석하여 치수의 소재 역할을 분류한다.
기존 classify_material_role()의 앞단계로 작동하며,
확정된 분류만 설정하고 불확실한 치수는 None으로 남긴다.

접근법:
1. Ø 기호 필터링: OCR 결과에서 Ø 포함 치수 → 가장 큰 Ø=OD, 두번째=ID
2. 동심원 검출: Hough Circle Transform으로 동심원 쌍 → OD/ID 매핑
3. 수직 치수선 분석: 도면 좌측/상단의 수직 치수 → 폭(LENGTH) 추정
"""
import re
import logging
from typing import List, Optional, Tuple

import cv2
import numpy as np

from schemas.dimension import Dimension, DimensionType, MaterialRole

logger = logging.getLogger(__name__)


def _is_ocr_noise(text: str) -> bool:
    """OCR 노이즈 판별 — 도면번호, 파트코드, 주석 등 비치수 텍스트 차단

    조건:
    1. 도면번호: TD + 숫자 5자리 이상
    2. 파트번호: P001, L005, B001 패턴
    3. 코드성 텍스트: 연속 영문 2자 이상 (MM 단위, Ø 제외)
    4. 접두 코드: ++, Z+Z 등
    5. 복수 소수점: 202.501.24 — OCR이 여러 치수를 하나로 병합
    6. 잘린 공차: ⌀60.: — 콜론/세미콜론으로 끝남
    7. 괄호 내 영문 포함 = 주석/코드 ((a00), (ref) 등)
    8. 숫자 사이 영문: 190a900, 93B0, 94B.5 — OCR 오인식
    9. X 병합: 42X365, 82.1X2 — 치수 곱셈/병합
    10. 특수문자 오염: Ø632*, ⌀73) — 꼬리 특수문자
    """
    t = text.strip()
    if re.search(r'[Tt][Dd]\d{5,}', t):
        return True
    if re.search(r'[PpBbLl]\d{3,}', t):
        return True

    # Ø/MM 제거 후 영문 2자 이상 = 코드성 텍스트
    cleaned = re.sub(r'[Mm]{2}$', '', t)
    cleaned = re.sub(r'^[ØφΦ⌀(]', '', cleaned)
    if re.search(r'[a-zA-Z]{2,}', cleaned):
        return True
    if re.match(r'^[+\-Z]{2,}', t):
        return True

    # 복수 소수점 = OCR 병합 오류 (202.501.24, 201.705.15)
    digits_only = re.sub(r'^[ØφΦ⌀(]\s*', '', t)
    if len(re.findall(r'\.', digits_only)) >= 2:
        return True
    # 잘린 공차: 콜론/세미콜론으로 끝남 (⌀60.:)
    if re.search(r'[:;]\s*$', t):
        return True
    # 괄호 내 영문 포함 = 주석/코드 ((a00), (ref) 등)
    if re.search(r'\([a-zA-Z]', t):
        return True
    # 숫자 사이 영문 = OCR 오인식 (190a900, 93B0, ⌀94B.5)
    # t에서도 Ø 제거하여 검사 (⌀94B.5 → 94B.5 → 4B.)
    cleaned_full = re.sub(r'^[ØφΦ⌀(\[]+', '', t)
    if re.search(r'\d[a-zA-Z][\d.]', cleaned_full):
        return True
    # X로 병합된 치수 (42X365, 82.1X2) — 곱셈/병합 표기
    if re.search(r'\d[Xx]\d', t) and not re.match(r'^[Mm]\d+[Xx]', t):
        return True
    # 꼬리 특수문자 오염 (Ø632*, ⌀73))
    if re.search(r'[*)\]]\s*$', t) and not re.match(r'^\(.*\)$', t):
        return True
    # 꼬리 소수점 (4400.) = 잘린 OCR
    if re.search(r'\d\.\s*$', t):
        return True
    # 순수 공차값 (±15, +0.1, -0.05) — 치수가 아님
    if re.match(r'^[±]\s*\d', t) or re.match(r'^[+\-]\s*0?\.\d', t):
        return True
    # 따옴표 접두사 = OCR 오인식 ("0560, "0560)
    if re.match(r'^["\'\u201c\u201d\u2018\u2019]', t):
        return True
    # 숫자 + 단일영문 끝 (16B, 08C) = 재질/코드 참조
    if re.match(r'^\d+[a-zA-Z]$', t):
        return True
    # 선행 0 + 숫자 (03, 08) = 코드/참조 (치수는 00 시작 안 함)
    if re.match(r'^0\d+$', t):
        return True
    # 꼬리 직경기호 (9⌀) = OCR 순서 뒤집힘
    if re.search(r'\d[ØφΦ⌀]\s*$', t):
        return True
    # 단일 문자 + 숫자 (a8, R3 제외 but 직경 문맥에서 a8은 노이즈)
    if re.match(r'^[a-df-qstvwyz]\d+$', t, re.IGNORECASE):
        return True
    # 숫자+연산자+4자리이상 = OCR 병합 (8+209001, 15-40032)
    if re.search(r'\d[+\-]\d{4,}', t):
        return True
    return False


def _parse_numeric_value(text: str) -> Optional[float]:
    """치수 텍스트에서 Ø/⌀ 뒤의 숫자값 추출

    OCR 노이즈 대응: 'B0D⌀600' → ⌀ 뒤의 600을 추출.
    ⌀ 기호가 있으면 그 뒤의 숫자를, 없으면 첫 번째 숫자를 반환.
    소수점 뒤 3자리(.001, .003) = OCR이 공차를 소수점으로 인식 → 정수부만 사용.
    """
    text = text.strip()
    # 괄호 제거 (예: (⌀95), (310))
    text = re.sub(r'^[(\[]+|[)\]]+$', '', text).strip()
    # Ø/⌀ 기호가 있으면 그 뒤의 숫자 추출
    dia_match = re.search(r'[ØφΦ⌀]\s*(\d+\.?\d*)', text)
    if dia_match:
        try:
            v = float(dia_match.group(1))
            # .00x 패턴 = 공차 오인식 (202.004 → 202)
            if '.' in dia_match.group(1):
                parts = dia_match.group(1).split('.')
                if len(parts[1]) >= 3 and parts[1].startswith('00'):
                    v = float(parts[0])
            return v
        except ValueError:
            pass
    # Ø 없으면 일반 숫자 추출
    cleaned = re.sub(r'^[RrMmCc]', '', text)
    m = re.search(r'(\d+\.?\d*)', cleaned)
    if m:
        try:
            v = float(m.group(1))
            # .00x 패턴 보정
            if '.' in m.group(1):
                parts = m.group(1).split('.')
                if len(parts[1]) >= 3 and parts[1].startswith('00'):
                    v = float(parts[0])
            return v
        except ValueError:
            pass
    return None


def clean_dimension_value(text: str) -> Optional[str]:
    """OD/ID/W 요약 저장용 — raw OCR에서 깨끗한 숫자 문자열 추출

    '⌀700', '250±0.1' → '700', '250'
    '96"1', '520 443.3', ':a570:=' → None (가비지)
    """
    if not text:
        return None
    # Ø 뒤에 바로 마이너스 → 노이즈 (⌀-5)
    if re.search(r'[ØφΦ⌀]\s*-', text):
        return None
    v = _parse_numeric_value(text)
    if v is None or v <= 0:
        return None
    # 소수점 이하 4자리 이상 → OCR 합침 노이즈 (420.6429)
    if v != int(v):
        dec_part = str(v).split('.')[1]
        if len(dec_part) >= 4:
            v = float(int(v))
    # 정수면 정수로, 소수면 소수로
    if v == int(v):
        return str(int(v))
    return str(v)


def _has_diameter_prefix(text: str) -> bool:
    """Ø/⌀ 포함 여부 확인 (PCD 제외)

    OCR 노이즈로 'B0D⌀600', '0D⌀550' 같이 앞에 쓰레기가 붙는 경우도 처리.
    """
    text = text.strip().upper()
    if text.startswith("PCD"):
        return False
    return bool(re.search(r'[ØφΦ⌀]', text))


def classify_by_diameter_symbol(
    dimensions: List[Dimension],
) -> List[Dimension]:
    """Ø 기호 기반 OD/ID 분류 (MVP 접근법)

    규칙:
    - Ø 접두사가 있는 치수만 대상
    - 가장 큰 Ø 값 → OUTER_DIAMETER
    - 두 번째로 큰 Ø 값 → INNER_DIAMETER
    - 나머지 Ø 값 (30 이하) → OTHER (볼트홀 등)
    - Ø 없는 치수 → 분류하지 않음 (None 유지)
    """
    # Ø 치수 수집: (index, value) — OCR 쓰레기 필터링
    dia_entries: List[Tuple[int, float]] = []
    for i, d in enumerate(dimensions):
        if _has_diameter_prefix(d.value):
            if _is_ocr_noise(d.value):
                continue
            v = _parse_numeric_value(d.value)
            if v is None or v <= 0 or v >= 2000:
                continue
            # Ø 뒤에 바로 숫자가 오는 깨끗한 패턴만 허용
            if not re.search(r'[ØφΦ⌀]\s*\d', d.value):
                continue
            # 최소 5mm — Ø02, Ø3 등은 OCR 오인식
            if v < 5:
                continue
            dia_entries.append((i, v))

    if not dia_entries:
        return dimensions

    # 값 기준 내림차순 정렬
    dia_entries.sort(key=lambda x: x[1], reverse=True)

    result = list(dimensions)

    # 가장 큰 Ø → OD
    od_idx, od_val = dia_entries[0]
    # 소형 부품 판별: Ø가 30 이하여도, 전체 치수 중 최대값이면 OD
    # (볼트홀은 주요 치수보다 작음)
    all_vals = [_parse_numeric_value(d.value) for d in dimensions
                if not _is_ocr_noise(d.value)]
    all_vals = [v for v in all_vals if v and v > 0]
    max_overall = max(all_vals) if all_vals else 0

    # Ø값이 전체 최대의 50% 이상이면 볼트홀이 아닌 주요 직경
    is_main_diameter = (od_val > 30 or
                        od_val >= max_overall * 0.5 or
                        len(dia_entries) <= 2)
    if is_main_diameter:
        result[od_idx] = result[od_idx].model_copy(
            update={"material_role": MaterialRole.OUTER_DIAMETER}
        )
        logger.info(f"Ø 기반 OD 분류: '{dimensions[od_idx].value}' = {od_val}")

    # ID 후보 찾기: OD 대비 비율 기반
    # 볼트홀/소형 피처 = OD의 10% 이하, 주요 직경 = 10% 초과
    bolt_threshold = max(od_val * 0.1, 30)  # 최소 30mm

    if len(dia_entries) >= 2:
        if len(dia_entries) == 2:
            id_idx, id_val = dia_entries[1]
        else:
            # 주요 직경만 필터 (볼트홀/소형 피처 제외)
            major = [(i, v) for i, v in dia_entries[1:] if v > bolt_threshold]
            if major:
                # 가장 작은 주요 직경 = ID (베어링/케이싱의 내경)
                id_idx, id_val = major[-1]
            else:
                id_idx, id_val = None, 0

        if (id_idx is not None and id_val > bolt_threshold
                and id_val >= od_val * 0.2
                and abs(id_val - od_val) > od_val * 0.05):  # ID ≠ OD
            result[id_idx] = result[id_idx].model_copy(
                update={"material_role": MaterialRole.INNER_DIAMETER}
            )
            logger.info(f"Ø 기반 ID 분류: '{dimensions[id_idx].value}' = {id_val}")

    # 나머지 소형 Ø → OTHER (볼트홀 등)
    for idx, val in dia_entries[1:]:
        if result[idx].material_role is None and val <= bolt_threshold:
            result[idx] = result[idx].model_copy(
                update={"material_role": MaterialRole.OTHER}
            )

    return result


def classify_by_concentric_circles(
    dimensions: List[Dimension],
    image_path: str,
    image_width: int,
    image_height: int,
) -> List[Dimension]:
    """동심원 검출 기반 OD/ID 매핑

    Hough Circle Transform으로 동심원 쌍을 찾고,
    근처 Ø 치수를 OD/ID에 매핑한다.

    이미 material_role이 설정된 치수는 건드리지 않는다.
    """
    try:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return dimensions
    except Exception:
        return dimensions

    # 큰 이미지는 리사이즈 (Hough Circle 성능)
    max_dim = 2000
    h, w = img.shape[:2]
    scale = 1.0
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)))
        logger.info(f"동심원 검출용 리사이즈: {w}x{h} → {img.shape[1]}x{img.shape[0]}")

    # 이미지 전처리
    blurred = cv2.GaussianBlur(img, (9, 9), 2)

    # Hough Circle 검출 (리사이즈된 이미지 기준)
    resized_h, resized_w = img.shape[:2]
    min_radius = min(resized_w, resized_h) // 20
    max_radius = min(resized_w, resized_h) // 3
    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=min_radius,
        param1=100,
        param2=50,
        minRadius=min_radius,
        maxRadius=max_radius,
    )

    if circles is None:
        return dimensions

    circles = np.round(circles[0]).astype(int)
    if len(circles) < 2:
        return dimensions

    # 동심원 쌍 찾기: 중심이 가까운(거리 < 작은원 반지름의 50%) 원 쌍
    concentric_pairs: List[Tuple[int, int]] = []  # (outer_idx, inner_idx)
    for i in range(len(circles)):
        for j in range(i + 1, len(circles)):
            cx1, cy1, r1 = circles[i]
            cx2, cy2, r2 = circles[j]
            dist = np.sqrt((cx1 - cx2) ** 2 + (cy1 - cy2) ** 2)
            smaller_r = min(r1, r2)
            if dist < smaller_r * 0.5:
                if r1 > r2:
                    concentric_pairs.append((i, j))
                else:
                    concentric_pairs.append((j, i))

    if not concentric_pairs:
        return dimensions

    # 가장 큰 동심원 쌍 선택
    best_pair = max(concentric_pairs, key=lambda p: circles[p[0]][2])
    outer_circle = circles[best_pair[0]]
    inner_circle = circles[best_pair[1]]

    logger.info(
        f"동심원 검출: outer=({outer_circle[0]},{outer_circle[1]},r={outer_circle[2]}), "
        f"inner=({inner_circle[0]},{inner_circle[1]},r={inner_circle[2]})"
    )

    # Ø 치수 중 material_role 미분류인 것들을 원에 매핑
    result = list(dimensions)
    for i, d in enumerate(result):
        if d.material_role is not None:
            continue
        if not _has_diameter_prefix(d.value):
            continue

        v = _parse_numeric_value(d.value)
        if v is None:
            continue

        # 치수 bbox 중심 (원본 좌표 → 리사이즈 좌표로 변환)
        dim_cx = (d.bbox.x1 + d.bbox.x2) / 2 * scale
        dim_cy = (d.bbox.y1 + d.bbox.y2) / 2 * scale
        dist_to_center = np.sqrt(
            (dim_cx - outer_circle[0]) ** 2 + (dim_cy - outer_circle[1]) ** 2
        )

        # 동심원 근처(외경 반지름의 2배 이내)에 있는 Ø 치수만 매핑
        if dist_to_center < outer_circle[2] * 2:
            # 값이 큰 쪽 = OD, 작은 쪽 = ID
            outer_r_mm = outer_circle[2]
            inner_r_mm = inner_circle[2]
            ratio = v / max(outer_r_mm, 1)

            # 외경에 가까운 비율이면 OD, 내경에 가까우면 ID
            outer_ratio = abs(ratio - outer_r_mm / max(inner_r_mm, 1))
            inner_ratio = abs(ratio - 1)

            if outer_ratio < inner_ratio:
                result[i] = d.model_copy(
                    update={"material_role": MaterialRole.OUTER_DIAMETER}
                )
                logger.info(f"동심원 기반 OD: '{d.value}'")
            else:
                result[i] = d.model_copy(
                    update={"material_role": MaterialRole.INNER_DIAMETER}
                )
                logger.info(f"동심원 기반 ID: '{d.value}'")

    return result


def classify_width_by_position(
    dimensions: List[Dimension],
    image_width: int,
    image_height: int,
) -> List[Dimension]:
    """위치 기반 폭(WIDTH=LENGTH) 분류

    규칙:
    - Ø 접두사가 없는 치수만 대상
    - 이미 material_role이 설정된 치수는 건드리지 않음
    - 도면 좌측(x < 25%) 또는 상단(y < 30%)에 위치한 큰 수직 치수 → LENGTH
    - 수평 스팬이 넓은 치수(bbox_width > bbox_height * 1.5) → LENGTH 후보
    - OD/ID가 확정된 후, 남은 큰 값 중 최대값 → LENGTH (폭)
    """
    result = list(dimensions)

    # OD/ID 이미 분류된 값 수집
    classified_od = None
    classified_id = None
    for d in result:
        if d.material_role == MaterialRole.OUTER_DIAMETER:
            classified_od = _parse_numeric_value(d.value)
        elif d.material_role == MaterialRole.INNER_DIAMETER:
            classified_id = _parse_numeric_value(d.value)

    if classified_od is None:
        # OD가 없으면 폭 분류 의미 없음
        return result

    # 미분류 non-Ø 치수 중 LENGTH 후보 찾기
    length_candidates: List[Tuple[int, float, float]] = []  # (idx, value, score)

    for i, d in enumerate(result):
        if d.material_role is not None:
            continue
        if _has_diameter_prefix(d.value):
            continue
        if _is_ocr_noise(d.value):
            continue
        if d.dimension_type in (
            DimensionType.THREAD, DimensionType.SURFACE_FINISH,
            DimensionType.ANGLE, DimensionType.CHAMFER,
            DimensionType.TOLERANCE, DimensionType.RADIUS,
        ):
            continue

        v = _parse_numeric_value(d.value)
        if v is None or v < 10:
            continue

        score = 0.0
        cx = (d.bbox.x1 + d.bbox.x2) / 2
        cy = (d.bbox.y1 + d.bbox.y2) / 2

        if image_width and image_height:
            x_ratio = cx / image_width
            y_ratio = cy / image_height

            # 단면도 영역 보너스 (x 30~60%, y 15~40% = 상부 중앙)
            if 0.25 <= x_ratio <= 0.65 and 0.15 <= y_ratio <= 0.40:
                score += 2.5

            # 극좌측 페널티 (x < 10% = 상세도/테두리 영역)
            if x_ratio < 0.10:
                score -= 2.0
            elif x_ratio < 0.20:
                score += 0.5

            # 상단 영역 보너스
            if y_ratio < 0.35:
                score += 1.0

            # 우하단 타이틀 블록 페널티
            if x_ratio > 0.65 and y_ratio > 0.75:
                score -= 5.0

        # 공차 포함 = 핵심 치수 시그널
        if d.tolerance or re.search(r'[±+]\s*\d', d.value):
            score += 2.0

        # 수평 bbox = 수평 치수 (폭 방향)
        bbox_w = d.bbox.x2 - d.bbox.x1
        bbox_h = d.bbox.y2 - d.bbox.y1
        if bbox_w > bbox_h * 2:
            score += 0.5

        # 값 크기: OD의 15~60% 범위 (베어링 폭 전형)
        if classified_od and v < classified_od:
            if classified_od * 0.15 <= v <= classified_od * 0.6:
                score += 1.5
            elif v > classified_od * 0.1:
                score += 0.5

        if score > 0:
            length_candidates.append((i, v, score))

    if not length_candidates:
        return result

    # 최고 점수 후보를 LENGTH(폭)로 분류
    best = max(length_candidates, key=lambda x: (x[2], x[1]))
    best_idx, best_val, best_score = best

    if best_score >= 2.0:
        result[best_idx] = result[best_idx].model_copy(
            update={"material_role": MaterialRole.LENGTH}
        )
        logger.info(
            f"위치 기반 폭 분류: '{dimensions[best_idx].value}' = {best_val} "
            f"(score={best_score:.1f})"
        )

    return result


def classify_by_dimension_type(
    dimensions: List[Dimension],
) -> List[Dimension]:
    """dimension_type == 'diameter' 기반 OD/ID 분류 (Ø 기호 없는 도면용 fallback)

    OCR이 Ø 기호 없이도 직경 치수를 dimension_type='diameter'로 분류한 경우,
    또는 Ø는 있지만 전부 소형값(≤30)일 때 일반 치수에서 OD/ID를 추정한다.

    규칙:
    - dimension_type == 'diameter'인 치수 중 가장 큰 값 → OD
    - diameter 타입이 없으면, 전체 치수 중 가장 큰 값 → OD (비원형 부품 가능성)
    - OD의 20~80% 범위에서 가장 작은 diameter 타입 → ID
    """
    result = list(dimensions)

    # 이미 OD가 있으면 스킵
    if any(d.material_role == MaterialRole.OUTER_DIAMETER for d in result):
        return result

    # 1차: dimension_type == 'diameter' 치수 수집 (노이즈 제외)
    dia_entries: List[Tuple[int, float]] = []
    for i, d in enumerate(result):
        if d.material_role is not None:
            continue
        if _is_ocr_noise(d.value):
            continue
        if d.dimension_type == DimensionType.DIAMETER:
            v = _parse_numeric_value(d.value)
            if v and 5 < v < 2000:  # 소형 부품도 허용 (5mm 이상)
                dia_entries.append((i, v))

    # 2차: diameter 타입 없으면, length 타입 중 가장 큰 값 시도
    if not dia_entries:
        for i, d in enumerate(result):
            if d.material_role is not None:
                continue
            if _is_ocr_noise(d.value):
                continue
            if d.dimension_type in (
                DimensionType.THREAD, DimensionType.SURFACE_FINISH,
                DimensionType.ANGLE, DimensionType.CHAMFER,
                DimensionType.TOLERANCE, DimensionType.RADIUS,
            ):
                continue
            # unknown 타입: 값이 깨끗한 숫자면 허용 (=120MM → 120)
            if d.dimension_type == DimensionType.UNKNOWN:
                # 순수 숫자 패턴만 허용 (괄호 감싼 것도)
                cleaned = re.sub(r'^[=()\[\]]+|[=()\[\]]+$', '', d.value.strip())
                cleaned = re.sub(r'[Mm]{2}$', '', cleaned)
                if not re.match(r'^\d+\.?\d*$', cleaned):
                    continue
            v = _parse_numeric_value(d.value)
            if v and v > 30 and v < 2000:
                dia_entries.append((i, v))

    if not dia_entries:
        return result

    dia_entries.sort(key=lambda x: x[1], reverse=True)

    # OD = 가장 큰 값
    od_idx, od_val = dia_entries[0]
    result[od_idx] = result[od_idx].model_copy(
        update={"material_role": MaterialRole.OUTER_DIAMETER}
    )
    logger.info(f"타입 기반 OD 분류: '{dimensions[od_idx].value}' = {od_val}")

    # ID = OD의 20~80% 범위에서 가장 작은 주요 직경
    if len(dia_entries) >= 2:
        bolt_threshold = max(od_val * 0.1, 30)
        major = [(i, v) for i, v in dia_entries[1:] if v > bolt_threshold]
        if major:
            id_idx, id_val = major[-1]
            if id_val >= od_val * 0.2:
                result[id_idx] = result[id_idx].model_copy(
                    update={"material_role": MaterialRole.INNER_DIAMETER}
                )
                logger.info(f"타입 기반 ID 분류: '{dimensions[id_idx].value}' = {id_val}")

    return result


# ISO 355 / JIS B 1512 기반 표준 베어링 치수 (OD → 가능한 ID 집합)
BEARING_CATALOG: dict = {
    1200: [900, 850, 800], 1120: [850, 800, 750],
    1000: [750, 700, 670, 650], 950: [700, 670, 650],
    900: [650, 630, 600], 850: [630, 600, 560],
    800: [580, 560, 540, 520], 750: [560, 540, 520, 500],
    700: [520, 500, 480, 460, 440], 650: [480, 460, 440, 420],
    630: [460, 440, 420, 400, 380], 600: [440, 420, 400, 380, 360],
    560: [420, 400, 380, 360, 340], 500: [360, 340, 320, 300, 280],
    480: [340, 320, 300, 280, 260], 460: [320, 300, 280, 260, 250],
    440: [300, 280, 260, 250, 240], 420: [280, 260, 250, 240, 220],
    400: [280, 260, 250, 240, 220], 380: [260, 250, 240, 220, 200],
    360: [250, 240, 220, 200, 180], 340: [240, 220, 200, 180, 160],
    320: [220, 200, 180, 160, 140], 300: [200, 180, 160, 140, 120],
    280: [200, 180, 160, 140, 120], 260: [180, 160, 140, 120, 110],
    250: [170, 160, 140, 120, 110], 240: [160, 140, 120, 110, 100],
    220: [140, 120, 110, 100, 90], 200: [120, 110, 100, 90, 80],
    180: [110, 100, 90, 80, 70], 160: [100, 90, 80, 70, 60],
    140: [80, 70, 60, 50], 120: [70, 60, 50, 45],
    110: [60, 50, 45, 40], 100: [55, 50, 45, 40, 35],
    90: [50, 45, 40, 35, 30], 80: [42, 40, 35, 30, 25],
    75: [40, 35, 30, 25], 70: [35, 30, 25, 20],
    65: [35, 30, 25, 20], 60: [30, 25, 20, 17],
    55: [25, 20, 17], 50: [25, 20, 17, 15],
    47: [20, 17, 15], 42: [20, 17, 15, 12],
    40: [17, 15, 12], 37: [17, 15, 12],
    35: [15, 12, 10], 32: [12, 10, 8], 30: [10, 8],
}


def _catalog_match_score(od_val: float, candidate_val: float) -> float:
    """베어링 카탈로그 매칭 점수 (0 또는 5.0)"""
    tol = 0.05  # ±5%
    for cat_od, valid_ids in BEARING_CATALOG.items():
        if abs(od_val - cat_od) <= cat_od * tol:
            for valid_id in valid_ids:
                if abs(candidate_val - valid_id) <= valid_id * tol:
                    return 5.0
    return 0.0


def classify_by_catalog(dimensions: List[Dimension]) -> List[Dimension]:
    """베어링 카탈로그 매칭으로 ID 추정 — OD가 있지만 ID가 없을 때

    ISO 355 / JIS B 1512 표준 베어링 치수 테이블과 대조하여,
    OD에 대응하는 표준 ID 치수가 미분류 치수에 있으면 ID로 분류한다.
    """
    result = list(dimensions)

    od_dim = next((d for d in result
                   if d.material_role == MaterialRole.OUTER_DIAMETER), None)
    if not od_dim:
        return result
    if any(d.material_role == MaterialRole.INNER_DIAMETER for d in result):
        return result

    od_val = _parse_numeric_value(od_dim.value)
    if not od_val:
        return result

    best_idx = None
    best_score = 0.0

    for i, d in enumerate(result):
        if d.material_role is not None:
            continue
        if _is_ocr_noise(d.value):
            continue
        # M/R-prefix 제외
        val_text = d.value.strip()
        if re.match(r'^[Mm]\s*\d', val_text) or re.match(r'^[Rr]\s*\d', val_text):
            continue
        v = _parse_numeric_value(d.value)
        if not v or v <= 0 or v < 5 or v >= od_val:
            continue

        score = _catalog_match_score(od_val, v)
        if score <= 0:
            continue

        # 보너스: Ø, diameter 타입
        if _has_diameter_prefix(d.value):
            score += 3.0
        if d.dimension_type == DimensionType.DIAMETER:
            score += 1.0

        if score > best_score:
            best_score = score
            best_idx = i

    if best_idx is not None and best_score >= 3.0:
        result[best_idx] = result[best_idx].model_copy(
            update={"material_role": MaterialRole.INNER_DIAMETER}
        )
        v = _parse_numeric_value(result[best_idx].value)
        logger.info(
            f"카탈로그 매칭 ID: '{dimensions[best_idx].value}' = {v} "
            f"(score={best_score:.1f})"
        )

    return result


def infer_inner_diameter(
    dimensions: List[Dimension],
    image_width: int = 0,
    image_height: int = 0,
) -> List[Dimension]:
    """복합 시그널 기반 ID 추정 — OD 있지만 ID 없을 때 Ø 없는 치수에서 ID를 찾는다.

    아이디어: 베어링/케이싱 도면에서 내경은 여러 약한 시그널의 조합으로 식별 가능하다.

    시그널 (각각 단독으로는 불충분, 합산하면 강력):
    1. OD 대비 비율: 0.3~0.9 범위 = 전형적 ID/OD 비율 (평균 0.63)
    2. 값 반복 빈도: 같은 숫자가 여러 번 나타남 = 핵심 치수 (도면에서 참조됨)
    3. 공차 보유: 끼워맞춤 공차가 있으면 기능 치수 (= ID/OD)
    4. Ø 접두사: 약하지만 여전히 직경 시그널
    5. dimension_type == diameter: OCR이 직경으로 인식
    6. 도면 중앙 위치: 보어/내경은 주로 도면 중앙 단면도에 표시
    7. W(폭)와의 구별: 이미 W로 분류된 값과 같으면 제외
    """
    result = list(dimensions)

    # OD 확인
    od_dim = next((d for d in result if d.material_role == MaterialRole.OUTER_DIAMETER), None)
    if od_dim is None:
        return result

    # 이미 ID 있으면 스킵
    if any(d.material_role == MaterialRole.INNER_DIAMETER for d in result):
        return result

    od_val = _parse_numeric_value(od_dim.value)
    if not od_val or od_val <= 0:
        return result

    # W 값 수집 (중복 분류 방지)
    w_val = None
    for d in result:
        if d.material_role and d.material_role.value == "length":
            w_val = _parse_numeric_value(d.value)

    # 전체 치수의 값 빈도 계산
    value_counts: dict = {}
    for d in dimensions:
        v = _parse_numeric_value(d.value)
        if v and v > 0:
            # 소수점 1자리까지 반올림하여 빈도 집계
            key = round(v, 1)
            value_counts[key] = value_counts.get(key, 0) + 1

    # ID 후보 점수 계산
    candidates: List[Tuple[int, float, float]] = []  # (idx, value, score)

    for i, d in enumerate(result):
        if d.material_role is not None:
            continue
        if _is_ocr_noise(d.value):
            continue
        # 나사, 표면거칠기, 각도, 챔퍼, 반경 제외
        if d.dimension_type in (
            DimensionType.THREAD, DimensionType.SURFACE_FINISH,
            DimensionType.ANGLE, DimensionType.CHAMFER, DimensionType.RADIUS,
        ):
            continue
        # M-prefix = thread (M10, M20), R-prefix = radius (R30, R  40)
        val_text = d.value.strip()
        if re.match(r'^[Mm]\s*\d', val_text) or re.match(r'^[Rr]\s*\d', val_text):
            continue

        v = _parse_numeric_value(d.value)
        if v is None or v <= 0 or v < 5:
            continue

        # W와 같은 값이면 제외
        if w_val and abs(v - w_val) < 0.5:
            continue
        # OD와 같은 값이면 제외 (ID ≠ OD)
        if abs(v - od_val) < od_val * 0.05:
            continue

        ratio = v / od_val
        # OD의 15~95% 범위만 대상
        if ratio < 0.15 or ratio > 0.95:
            continue

        score = 0.0

        # 시그널 1: OD 대비 비율 (0.4~0.8 = 전형적 ID, 가우시안 보너스)
        if 0.3 <= ratio <= 0.9:
            # 0.63 중심 가우시안, 표준편차 0.2
            gaussian = 3.0 * np.exp(-((ratio - 0.63) ** 2) / (2 * 0.2 ** 2))
            score += gaussian

        # 값 크기 보너스: ID는 보통 "두 번째로 큰 치수" (OD > ID > W)
        # OD의 50% 이상이면 W보다는 ID일 확률이 높음
        if ratio >= 0.50:
            score += 0.5

        # 시그널 2: 값 반복 빈도 (≥2회 = 핵심 치수)
        key = round(v, 1)
        freq = value_counts.get(key, 0)
        if freq >= 3:
            score += 2.0
        elif freq >= 2:
            score += 1.0

        # 시그널 3: 공차 보유 = 기능 치수
        if d.tolerance or re.search(r'[±+]\s*\d', d.value):
            score += 2.5

        # 시그널 4: Ø 접두사
        if _has_diameter_prefix(d.value):
            score += 3.0

        # 시그널 5: dimension_type == diameter
        if d.dimension_type == DimensionType.DIAMETER:
            score += 2.0

        # 시그널 6: 도면 중앙 위치 (보어는 주로 중앙)
        if image_width and image_height:
            cx = (d.bbox.x1 + d.bbox.x2) / 2
            cy = (d.bbox.y1 + d.bbox.y2) / 2
            x_ratio = cx / image_width
            y_ratio = cy / image_height

            # 중앙 영역 (x 25~75%, y 20~60%)
            if 0.25 <= x_ratio <= 0.75 and 0.20 <= y_ratio <= 0.60:
                score += 1.0

            # 타이틀 블록 페널티
            if x_ratio > 0.65 and y_ratio > 0.75:
                score -= 5.0

        if score > 0:
            candidates.append((i, v, score))

    if not candidates:
        return result

    # 최고 점수 후보를 ID로 분류 (최소 3.0점 필요)
    best = max(candidates, key=lambda x: (x[2], x[1]))
    best_idx, best_val, best_score = best

    if best_score >= 3.0:
        result[best_idx] = result[best_idx].model_copy(
            update={"material_role": MaterialRole.INNER_DIAMETER}
        )
        logger.info(
            f"복합 시그널 ID 추정: '{dimensions[best_idx].value}' = {best_val} "
            f"(score={best_score:.1f}, ratio={best_val/od_val:.2f})"
        )

    return result


def classify_od_id_width(
    dimensions: List[Dimension],
    image_path: Optional[str] = None,
    image_width: int = 0,
    image_height: int = 0,
    session_name: Optional[str] = None,
) -> List[Dimension]:
    """OD/ID/폭 통합 분류기 — postprocess_dimensions()의 앞단계

    실행 순서:
    0. 세션명 파싱 — BOM에서 추출된 OD/ID/W로 검증 기준값 확보
    1. Ø 기호 기반 OD/ID 분류 (OCR 텍스트에 Ø 있을 때)
    2. dimension_type fallback (Ø 없거나 소형값만 있을 때)
    3. 복합 시그널 ID 추정 (OD 있지만 ID 없을 때)
    4. 위치 기반 폭(LENGTH) 분류 (OD 확정 후)
    5. 세션명 기준값으로 결과 검증/보정

    확정된 분류만 설정하고, 불확실한 치수는 material_role=None으로 남긴다.
    기존 classify_material_role()이 후속으로 None인 치수를 처리한다.
    """
    if not dimensions:
        return dimensions

    logger.info(f"OpenCV OD/ID/폭 분류기 시작: {len(dimensions)}개 치수")

    # Step 0: 세션명에서 기준값 확보
    from services.session_name_parser import parse_session_name_dimensions
    ref = parse_session_name_dimensions(session_name or "")
    if ref["pattern"]:
        logger.info(
            f"세션명 기준값: OD={ref['od']}, ID={ref['id']}, W={ref['w']} "
            f"(패턴={ref['pattern']})"
        )

    # Step 1: Ø 기호 기반 OD/ID
    result = classify_by_diameter_symbol(dimensions)

    # Step 2: Ø 기반으로 OD 못 찾으면 dimension_type fallback
    has_od = any(d.material_role == MaterialRole.OUTER_DIAMETER for d in result)
    if not has_od:
        result = classify_by_dimension_type(result)

    # Step 3: 베어링 카탈로그 매칭으로 ID 추정
    has_id = any(d.material_role == MaterialRole.INNER_DIAMETER for d in result)
    if not has_id:
        result = classify_by_catalog(result)

    # Step 4: 여전히 ID 없으면 복합 시그널로 추정
    has_id = any(d.material_role == MaterialRole.INNER_DIAMETER for d in result)
    if not has_id:
        result = infer_inner_diameter(result, image_width, image_height)

    # Step 5: 위치 기반 폭 분류
    if image_width and image_height:
        result = classify_width_by_position(result, image_width, image_height)

    # Step 6: 세션명 기준값으로 결과 검증/보정
    if ref["pattern"]:
        from services.session_name_parser import validate_with_session_ref
        result = validate_with_session_ref(
            result, ref, _parse_numeric_value, _is_ocr_noise,
        )

    # 분류 요약 로그
    roles = {}
    for d in result:
        if d.material_role is not None:
            role_name = d.material_role.value
            roles[role_name] = roles.get(role_name, 0) + 1

    if roles:
        logger.info(f"OpenCV 분류 결과: {roles}")

    return result


