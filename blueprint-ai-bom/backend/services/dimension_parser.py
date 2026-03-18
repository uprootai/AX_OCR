"""치수 파싱, 검증, 패턴 매칭 함수

dimension_service.py에서 분리된 순수 함수 모듈.
클래스 메서드 → 독립 함수로 변환 (self.* 제거)
"""
import re
import uuid
import logging
from typing import List, Optional, Tuple

from schemas.dimension import Dimension, DimensionType, MaterialRole
from schemas.detection import VerificationStatus, BoundingBox
from services.opencv_classifier import classify_od_id_width

logger = logging.getLogger(__name__)

# ISO 4287 Ra 표면 거칠기 표준값 (μm)
RA_STANDARD_VALUES = {0.025, 0.05, 0.1, 0.2, 0.4, 0.8, 1.6, 3.2, 6.3, 12.5, 25, 50}

SUB_DIM_PATTERNS = [
    re.compile(r'\(\d+\)\s*[ØφΦ⌀]\s*\d+\.?\d*'),
    re.compile(r'\(\d+\)\s*M\d+\.?\d*'),
    re.compile(r'\(\d+\)\s*\d+\.?\d*[°˚]'),
    re.compile(r'[ØφΦ⌀]\s*\d+\.?\d*'),
    re.compile(r'M\d+\.?\d*(?:\s*[x×]\s*\d+)?'),
    re.compile(r'R\s*\d+\.?\d*'),
    re.compile(r'PCD\s*[ØφΦ⌀]?\s*\d+\.?\d*'),
    re.compile(r'[±]\s*\d+\.?\d*'),
    re.compile(r'\b\d+\.?\d*\s*(?=Drill|drill|Tap|tap|thru|Hole|hole)'),
]


def fix_diameter_symbol(text: str) -> str:
    """PaddleOCR이 Ø를 0으로 읽는 문제 보정

    - "0392" → "Ø392" (독립 텍스트에서 0+3자리이상 숫자)
    - "PCD0430" → "PCDØ430"
    - "(2x0361)" → "(2xØ361)"
    - 단, "0.5" 같은 소수는 변환하지 않음
    """
    return re.sub(r'(?<![.\d])0(\d{2,})', r'Ø\1', text)


def is_dimension_pattern(text: str) -> bool:
    """PaddleOCR 텍스트가 치수 패턴인지 확인"""
    exclude_patterns = [
        r'Rev\.', r'\d{4}[.\-/]\d{2}[.\-/]\d{2}', r'^[A-Z]\d+-\d+',
        r'^[A-Z]{2}\d{5,}', r'(?i)Dwg|DATE|SCALE|PART|MATERIAL|FINISH|WEIGHT',
    ]
    for pat in exclude_patterns:
        if re.search(pat, text):
            return False

    dimension_patterns = [
        r'^\d+\.?\d*$', r'^[ØφΦ⌀]\s*\d+', r'^R\s*\d+', r'^M\s*\d+',
        r'^PCD[Ø]?\d+', r'^\d+\.?\d*\s*[±]', r'^\d+\.?\d*\s*[+\-]\s*\d',
        r'^\d+\.?\d*\s*[°˚]', r'^\(\d+[x×]', r'^\(\d+\.?\d*\)$',
        r'^\d+\.?\d*\s*\(\*?\)', r'^\d+\.?\d*\s*mm', r'^\d+\.?\d*\s*[A-Z]\d+$',
        r'^\(\d+\)\s*[ØφΦ⌀]\s*\d+', r'^\(\d+\)\s*\d+\.?\d*[°˚]',
        r'^\(\d+\)\s*\d+\.?\d*$', r'^[±]\s*\d+',
        r'^\(\d+\)\s*M\s*\d+', r'^\(\d+\)\s*R\s*\d+',
    ]
    for pat in dimension_patterns:
        if re.search(pat, text):
            return True

    return False


def is_valid_dimension(dim: Dimension) -> bool:
    """OCR 결과 품질 필터 - 깨진 텍스트, 오탐 제거"""
    text = dim.raw_text.strip()
    if len(text) <= 1:
        return False
    if not re.search(r'\d', text):
        return False
    garbage_ratio = sum(1 for c in text if c in ':;|{}[]\\') / max(len(text), 1)
    if garbage_ratio > 0.3:
        return False
    if '\n' in text or len(text) > 30:
        return False
    if sum(1 for c in text if c.isdigit()) / max(len(text), 1) < 0.3:
        return False
    if (dim.bbox.x2 - dim.bbox.x1) > 500:
        return False
    numeric_match = re.match(r'^[ØφΦ⌀]?\s*(\d+\.?\d*)', text)
    if numeric_match and float(numeric_match.group(1)) >= 5000:
        return False

    # 해칭 패턴 필터: 반복 0/1/4 + 극소 bbox → 단면 해칭선 오인식
    bbox_area = (dim.bbox.x2 - dim.bbox.x1) * (dim.bbox.y2 - dim.bbox.y1)
    if bbox_area < 200 and re.match(r'^[01]{2,}$|^[14]{2,}$|^[01]+$', dim.value.strip()):
        return False
    return True


def parse_dimension_text(text: str) -> Tuple[DimensionType, str, Optional[str]]:
    """치수 텍스트 파싱 → (DimensionType, parsed_value, tolerance)"""
    text = text.strip()
    tolerance = None
    dim_type = DimensionType.UNKNOWN
    parsed_value = text

    # 복합 패턴 (구체적인 패턴 먼저)
    match = re.match(r'^[ØφΦ⌀]\s*(\d+\.?\d*)\s*[±]\s*(\d+\.?\d*)', text)
    if match:
        return DimensionType.DIAMETER, parsed_value, f"±{match.group(2)}"
    match = re.match(r'^[ØφΦ⌀]\s*(\d+\.?\d*)\s*\+\s*(\d+\.?\d*)\s*/\s*-\s*(\d+\.?\d*)', text)
    if match:
        return DimensionType.DIAMETER, parsed_value, f"+{match.group(2)}/-{match.group(3)}"
    match = re.match(r'^[ØφΦ⌀]\s*(\d+\.?\d*)\s*-\s*(\d+\.?\d*)\s*\+\s*(\d+\.?\d*)', text)
    if match:
        return DimensionType.DIAMETER, parsed_value, f"+{match.group(3)}/-{match.group(2)}"
    match = re.match(r'^[ØφΦ⌀]\s*(\d+\.?\d*)\s*([A-Za-z]\d+)', text)
    if match:
        return DimensionType.DIAMETER, parsed_value, match.group(2)
    match = re.match(r'^M\s*(\d+\.?\d*)(?:\s*[×xX]\s*(\d+\.?\d*))?', text)
    if match:
        return DimensionType.THREAD, parsed_value, tolerance
    match = re.match(r'^C\s*(\d+\.?\d*)(?:\s*[×xX]\s*(\d+\.?\d*)\s*°)?', text, re.IGNORECASE)
    if match:
        return DimensionType.CHAMFER, parsed_value, tolerance

    # 단일 패턴
    if re.match(r'^[ØφΦ⌀]\s*\d+', text):
        dim_type = DimensionType.DIAMETER
    elif re.match(r'^R\s*\d+', text, re.IGNORECASE):
        dim_type = DimensionType.RADIUS
    elif re.search(r'\d+\s*[°˚]', text) or 'deg' in text.lower():
        dim_type = DimensionType.ANGLE
    elif re.match(r'^Ra\s*[\d.]+', text, re.IGNORECASE):
        dim_type = DimensionType.SURFACE_FINISH
    elif re.match(r'^\d+\.?\d*$', text):
        # 독립 숫자: ISO 4287 Ra 표준값이면 표면 거칠기로 분류
        try:
            dim_type = DimensionType.SURFACE_FINISH if float(text) in RA_STANDARD_VALUES else DimensionType.LENGTH
        except ValueError:
            dim_type = DimensionType.LENGTH
    elif re.match(r'^\d+\.?\d*', text):
        dim_type = DimensionType.LENGTH

    # 공차 추출 (특수 치수 타입은 IT 공차 제외)
    skip_it_tolerance = dim_type in (
        DimensionType.RADIUS, DimensionType.CHAMFER, DimensionType.THREAD,
        DimensionType.ANGLE, DimensionType.SURFACE_FINISH,
    )

    tolerance_patterns = [
        (r'(\d+\.?\d*)\s*-\s*(\d+\.?\d*)\s*\+\s*(\d+\.?\d*)',
         lambda m: f"+{m.group(3)}/-{m.group(2)}", False),
        (r'(\d+\.?\d*)\s*\+\s*(\d+\.?\d*)\s*/\s*0(?!\d)',
         lambda m: f"+{m.group(2)}/0", False),
        (r'(\d+\.?\d*)\s*0\s*/\s*-\s*(\d+\.?\d*)',
         lambda m: f"0/-{m.group(2)}", False),
        (r'\+\s*(\d+\.?\d*)\s*/\s*-\s*(\d+\.?\d*)',
         lambda m: f"+{m.group(1)}/-{m.group(2)}", False),
        (r'[±]\s*(\d+\.?\d*)', lambda m: f"±{m.group(1)}", False),
        (r'(?<![RrCcMm])([HhGgFfEeDdBbAaJjKkNnPpSsTtUuVvXxYyZz])(\d+)',
         lambda m: f"{m.group(1)}{m.group(2)}", True),
    ]

    if tolerance is None:
        for pattern, formatter, is_it_tolerance in tolerance_patterns:
            if is_it_tolerance and skip_it_tolerance:
                continue
            match = re.search(pattern, text)
            if match:
                tolerance = formatter(match)
                break

    return dim_type, parsed_value, tolerance


def extract_unit(text: str) -> Optional[str]:
    """단위 추출"""
    text_lower = text.lower()
    if 'mm' in text_lower:
        return 'mm'
    elif 'cm' in text_lower:
        return 'cm'
    elif 'in' in text_lower or '"' in text:
        return 'inch'
    elif '°' in text or 'deg' in text_lower:
        return 'degree'
    elif 'm' in text_lower and 'mm' not in text_lower:
        return 'm'
    return None


def parse_bbox_flexible(bbox_data) -> BoundingBox:
    """다양한 bbox 포맷을 BoundingBox로 변환

    지원: [x1,y1,x2,y2] | [[x1,y1],[x2,y2],...] | {x1,y1,x2,y2}
    """
    if isinstance(bbox_data, dict):
        return BoundingBox(
            x1=float(bbox_data.get("x1", 0)), y1=float(bbox_data.get("y1", 0)),
            x2=float(bbox_data.get("x2", 0)), y2=float(bbox_data.get("y2", 0)),
        )
    if isinstance(bbox_data, list) and len(bbox_data) == 4:
        if isinstance(bbox_data[0], (list, tuple)):
            xs = [pt[0] for pt in bbox_data]
            ys = [pt[1] for pt in bbox_data]
            return BoundingBox(
                x1=float(min(xs)), y1=float(min(ys)),
                x2=float(max(xs)), y2=float(max(ys)),
            )
        return BoundingBox(
            x1=float(bbox_data[0]), y1=float(bbox_data[1]),
            x2=float(bbox_data[2]), y2=float(bbox_data[3]),
        )
    return BoundingBox(x1=0, y1=0, x2=0, y2=0)


def apply_bbox_offset(det: dict, offset_x: float, offset_y: float) -> dict:
    """PaddleOCR detection의 bbox 좌표에 타일 오프셋 적용"""
    det = dict(det)
    bbox_points = det.get("bbox", det.get("position", []))
    if bbox_points and len(bbox_points) == 4:
        shifted = [[pt[0] + offset_x, pt[1] + offset_y] for pt in bbox_points]
        if "bbox" in det:
            det["bbox"] = shifted
        else:
            det["position"] = shifted
    return det


def parse_paddle_detection(det: dict, idx: int, text: str) -> Optional[Dimension]:
    """PaddleOCR 응답을 Dimension 객체로 변환"""
    try:
        dim_id = f"dim_{idx:03d}_{uuid.uuid4().hex[:8]}"
        confidence = float(det.get("confidence", 0.5))

        bbox_points = det.get("bbox", det.get("position", []))
        if bbox_points and len(bbox_points) == 4:
            xs = [pt[0] for pt in bbox_points]
            ys = [pt[1] for pt in bbox_points]
            bbox = BoundingBox(
                x1=float(min(xs)), y1=float(min(ys)),
                x2=float(max(xs)), y2=float(max(ys)),
            )
        else:
            bbox = BoundingBox(x1=0, y1=0, x2=0, y2=0)

        dim_type, parsed_value, tolerance = parse_dimension_text(text)
        unit = extract_unit(text)

        return Dimension(
            id=dim_id, bbox=bbox, value=parsed_value, raw_text=text,
            unit=unit, tolerance=tolerance, dimension_type=dim_type,
            confidence=confidence, model_id="paddleocr",
            verification_status=VerificationStatus.PENDING,
            modified_value=None, modified_bbox=None, linked_to=None,
        )
    except Exception as e:
        logger.error(f"PaddleOCR 치수 파싱 실패: {e}")
        return None


def parse_edocr2_detection(det: dict, idx: int) -> Optional[Dimension]:
    """eDOCr2 응답을 Dimension 객체로 변환"""
    try:
        dim_id = f"dim_{idx:03d}_{uuid.uuid4().hex[:8]}"
        raw_text = det.get("value", det.get("text", ""))
        confidence = det.get("confidence", 0.9)
        location = det.get("location", [])
        bbox_data = det.get("bbox", None)

        if location and len(location) == 4:
            xs = [pt[0] for pt in location]
            ys = [pt[1] for pt in location]
            bbox = BoundingBox(
                x1=float(min(xs)), y1=float(min(ys)),
                x2=float(max(xs)), y2=float(max(ys)),
            )
        elif isinstance(bbox_data, dict):
            bbox = BoundingBox(
                x1=float(bbox_data.get("x1", 0)), y1=float(bbox_data.get("y1", 0)),
                x2=float(bbox_data.get("x2", 0)), y2=float(bbox_data.get("y2", 0)),
            )
        elif isinstance(bbox_data, list) and len(bbox_data) >= 4:
            bbox = BoundingBox(
                x1=float(bbox_data[0]), y1=float(bbox_data[1]),
                x2=float(bbox_data[2]), y2=float(bbox_data[3]),
            )
        else:
            bbox = BoundingBox(x1=0, y1=0, x2=0, y2=0)

        dim_type, parsed_value, tolerance = parse_dimension_text(raw_text)

        edocr2_type = det.get("type", "")
        if edocr2_type and dim_type == DimensionType.UNKNOWN:
            type_mapping = {
                "dimension": DimensionType.LENGTH,
                "diameter": DimensionType.DIAMETER,
                "radius": DimensionType.RADIUS,
                "angle": DimensionType.ANGLE,
                "tolerance": DimensionType.TOLERANCE,
                "text_dimension": DimensionType.UNKNOWN,
            }
            dim_type = type_mapping.get(edocr2_type, DimensionType.UNKNOWN)

        unit = det.get("unit") or extract_unit(raw_text)

        return Dimension(
            id=dim_id, bbox=bbox, value=parsed_value, raw_text=raw_text,
            unit=unit, tolerance=tolerance, dimension_type=dim_type,
            confidence=confidence, model_id="edocr2",
            verification_status=VerificationStatus.PENDING,
            modified_value=None, modified_bbox=None, linked_to=None,
        )
    except Exception as e:
        logger.error(f"치수 파싱 실패: {e}")
        return None


def parse_paddleocr_detections(
    detections: list,
    confidence_threshold: float,
    offset_x: float = 0.0,
    offset_y: float = 0.0,
) -> List[Dimension]:
    """PaddleOCR 검출 결과 → Dimension 리스트 (패턴 필터 + 텍스트 블록 분해)"""
    dimensions: List[Dimension] = []
    for idx, det in enumerate(detections):
        text = det.get("text", "").strip()
        if not text:
            continue

        text = fix_diameter_symbol(text)

        if offset_x or offset_y:
            det = apply_bbox_offset(det, offset_x, offset_y)

        if is_dimension_pattern(text):
            dimension = parse_paddle_detection(det, idx, text)
            if dimension and dimension.confidence >= confidence_threshold and is_valid_dimension(dimension):
                dimensions.append(dimension)
                continue
        sub_dims = extract_dims_from_text_block(det, idx, text, confidence_threshold)
        dimensions.extend(sub_dims)

    return dimensions


def parse_generic_texts(
    texts: list, model_id: str, confidence_threshold: float
) -> List[Dimension]:
    """범용 OCR 텍스트 결과를 Dimension 리스트로 변환"""
    dimensions: List[Dimension] = []
    for idx, det in enumerate(texts):
        if isinstance(det, dict):
            text = det.get("text", "").strip()
            confidence = float(det.get("confidence", 0.5))
            bbox_raw = det.get("bbox")
        else:
            text = str(det).strip()
            confidence = 0.5
            bbox_raw = None

        if not text or confidence < confidence_threshold:
            continue
        text = fix_diameter_symbol(text)
        bbox = parse_bbox_flexible(bbox_raw) if bbox_raw else BoundingBox(x1=0, y1=0, x2=0, y2=0)

        if is_dimension_pattern(text):
            dim_type, parsed_value, tolerance = parse_dimension_text(text)
            dim = Dimension(
                id=f"dim_{idx:03d}_{uuid.uuid4().hex[:8]}",
                bbox=bbox, value=parsed_value, raw_text=text,
                unit=extract_unit(text), tolerance=tolerance,
                dimension_type=dim_type, confidence=confidence, model_id=model_id,
                verification_status=VerificationStatus.PENDING,
                modified_value=None, modified_bbox=None, linked_to=None,
            )
            if is_valid_dimension(dim):
                dimensions.append(dim)
        else:
            for pat in SUB_DIM_PATTERNS:
                for m in pat.finditer(text):
                    sub = fix_diameter_symbol(m.group().strip())
                    if not is_dimension_pattern(sub):
                        continue
                    dt, pv, tol = parse_dimension_text(sub)
                    sub_dim = Dimension(
                        id=f"dim_{idx:03d}_{uuid.uuid4().hex[:8]}",
                        bbox=bbox, value=pv, raw_text=sub,
                        unit=extract_unit(sub), tolerance=tol,
                        dimension_type=dt, confidence=confidence, model_id=model_id,
                        verification_status=VerificationStatus.PENDING,
                        modified_value=None, modified_bbox=None, linked_to=None,
                    )
                    if is_valid_dimension(sub_dim):
                        dimensions.append(sub_dim)
    return dimensions


def _parse_numeric(text: str) -> Optional[float]:
    """치수 텍스트에서 첫 번째 숫자값 추출 (내부 유틸)"""
    m = re.search(r'(\d+\.?\d*)', re.sub(r'^[ØφΦ⌀RrMmCc]', '', text.strip()))
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return None


def _format_corrected(v_fixed: float, original_str: str) -> str:
    """교정된 숫자를 과학적 표기법 없이 포맷 (내부 유틸)"""
    if v_fixed == int(v_fixed):
        return str(int(v_fixed))
    # 원본 소수점 자릿수 + 1 로 출력
    original_decimals = len(original_str.split('.')[1]) if '.' in original_str else 0
    target_decimals = max(original_decimals + 1, 2)
    return f"{v_fixed:.{target_decimals}f}".rstrip('0').rstrip('.')


def filter_non_dimension_text(dimensions: List[Dimension]) -> List[Dimension]:
    """비치수 텍스트 필터링 — 날짜, 도면번호, 섹션 라벨, 벌룬 번호 제거

    패턴:
    - 날짜: 2020.02.18, 202.004.28 → Ø 접두어와 함께 오인식됨
    - 도면번호: TD0060700, 9Z09000L 등
    - 섹션 라벨: E-3, B-2, F-6, D-5 등
    - 벌룬/아이템 번호: Ø01~Ø19 (conf < 0.55) — 조립도 원형 번호
    - 후행 소수점: 3., 6., 1. (값 불완전)
    - 단위 포함 텍스트: 1mm, 71mm
    """
    # 비치수 패턴 (제거 대상)
    non_dim_patterns = [
        # 날짜 패턴 (Ø 접두어 포함)
        re.compile(r'^[ØφΦ⌀]?\s*\d{2,4}[.\-/]\d{2}[.\-/]\d{2}'),
        # 도면번호 패턴
        re.compile(r'(?i)^T[D0][\d]{5,}'),
        re.compile(r'(?i)[a-z]*[Z9]0?[a-z]?900[0-9GLI]*', re.IGNORECASE),
        # 섹션/뷰 라벨 (E-3, B-2, F-6, D-5 등)
        re.compile(r'^[A-GS]-\d$'),
        # ISO 표준 참조
        re.compile(r'(?i)^[1I]?SO\s*276'),
        # 용지 크기
        re.compile(r'(?i)\d+[x×]\d+\s*mm$'),
        # 순수 가비지
        re.compile(r'^[a-z]{2,}\d*$', re.IGNORECASE),
    ]

    result: List[Dimension] = []
    for d in dimensions:
        text = d.value.strip()

        # 패턴 매칭으로 비치수 제거
        skip = False
        for pat in non_dim_patterns:
            if pat.search(text):
                logger.debug(f"비치수 텍스트 제거: '{text}' (패턴: {pat.pattern})")
                skip = True
                break
        if skip:
            continue

        # 벌룬/아이템 번호 필터: Ø + 1~2자리 정수, 낮은 신뢰도
        balloon_match = re.match(r'^[ØφΦ⌀]\s*0?(\d{1,2})$', text)
        if balloon_match:
            num = int(balloon_match.group(1))
            if 1 <= num <= 19 and d.confidence < 0.55:
                logger.debug(f"벌룬 번호 제거: '{text}' (conf={d.confidence:.2f})")
                continue

        # 후행 소수점만 있는 값 (3., 6., 1.) — 불완전한 OCR
        if re.match(r'^\d+\.$', text) and len(text) <= 3:
            logger.debug(f"불완전 후행소수점 제거: '{text}'")
            continue

        # 단위 접미사 정리 (1mm → 1, 71mm → 71)
        unit_cleaned = re.sub(r'\s*mm\s*$', '', text, flags=re.IGNORECASE)
        if unit_cleaned != text and re.match(r'^\d+\.?\d*$', unit_cleaned):
            d = d.model_copy(update={"value": unit_cleaned})

        result.append(d)

    removed = len(dimensions) - len(result)
    if removed > 0:
        logger.info(f"비치수 텍스트 필터: {removed}개 제거 (원본 {len(dimensions)}개)")
    return result


def fix_tolerance_absorption(dimensions: List[Dimension]) -> List[Dimension]:
    """공차 흡수 오류 교정 — 공차값이 치수에 병합된 패턴 분리

    패턴:
    - 486.001 → 486 ±0.01 (3자리 정수 + .00X 패턴)
    - 202.505.22 → 202.5 +0.05/-0.22 (소수 + .XX.XX 패턴)
    - 160.003 → 160 +0.003 (3자리 정수 + .00X 패턴)
    - 250.01 → 250 ±0.01 (3자리 정수 + .0X 패턴)
    """
    result: List[Dimension] = []
    for d in dimensions:
        text = d.value.strip()
        # Ø 접두어 제거 후 숫자 분석
        prefix = ''
        cleaned = text
        prefix_match = re.match(r'^([ØφΦ⌀]\s*)', text)
        if prefix_match:
            prefix = prefix_match.group(1)
            cleaned = text[len(prefix):]

        # 패턴 1: NNN.00X → NNN ±0.00X (3자리 정수 + 매우 작은 소수)
        m = re.match(r'^(\d{3,})\.0{1,2}(\d{1,3})$', cleaned)
        if m and d.tolerance is None:
            base = m.group(1)
            tol_digits = '0' * (len(cleaned.split('.')[1]) - len(m.group(2))) + m.group(2)
            tol_val = f"0.{tol_digits}"
            new_value = f"{prefix}{base}"
            new_tolerance = f"±{tol_val}"
            logger.info(f"공차 흡수 교정: '{text}' → value='{new_value}', tol='{new_tolerance}'")
            d = d.model_copy(update={
                "value": new_value,
                "tolerance": new_tolerance,
                "ocr_corrected": True,
                "confidence": round(d.confidence * 0.9, 4),
            })
            result.append(d)
            continue

        # 패턴 2: NNN.N + XX.XX (이중 소수점 — 공차 양쪽 값 병합)
        m = re.match(r'^(\d+\.\d+?)(\d{2})\.(\d{2})$', cleaned)
        if m and d.tolerance is None:
            base = m.group(1)
            upper = f"0.{m.group(2)}"
            lower = f"0.{m.group(3)}"
            new_value = f"{prefix}{base}"
            new_tolerance = f"+{upper}/-{lower}"
            logger.info(f"공차 흡수 교정 (이중): '{text}' → value='{new_value}', tol='{new_tolerance}'")
            d = d.model_copy(update={
                "value": new_value,
                "tolerance": new_tolerance,
                "ocr_corrected": True,
                "confidence": round(d.confidence * 0.9, 4),
            })

        result.append(d)
    return result


def fix_character_confusion(dimensions: List[Dimension]) -> List[Dimension]:
    """OCR 문자 혼동 교정

    패턴:
    - B ↔ 8: Ø2B7 → Ø287, 3B.1 → 38.1
    - Ø 뒤 숫자 전위: Ø01 → Ø10, Ø02 → Ø20 (conf > 0.7인 경우만)
    """
    result: List[Dimension] = []
    for d in dimensions:
        text = d.value.strip()
        modified = False

        # B → 8 교정 (숫자 컨텍스트 내의 B — 소수점 사이도 포함)
        if re.search(r'\d[Bb][\d.]', text) or re.search(r'[Bb]\d+\.\d', text):
            new_text = re.sub(r'(?<=\d)[Bb](?=[\d.])', '8', text)
            new_text = re.sub(r'^([ØφΦ⌀]\s*)(\d+)[Bb](\d)', r'\g<1>\g<2>8\3', new_text)
            if new_text != text:
                logger.info(f"문자 혼동 교정 B→8: '{text}' → '{new_text}'")
                d = d.model_copy(update={"value": new_text, "ocr_corrected": True})
                modified = True

        # Ø 뒤 숫자 전위 교정 (Ø01 → Ø10, Ø02 → Ø20 등)
        # 단, conf >= 0.7이고 Ø + 0 + 단일숫자인 경우
        if not modified and d.confidence >= 0.7:
            m = re.match(r'^([ØφΦ⌀])\s*0(\d)$', text)
            if m and m.group(2) != '0':
                new_text = f"{m.group(1)}{m.group(2)}0"
                logger.info(f"Ø 숫자 전위 교정: '{text}' → '{new_text}'")
                d = d.model_copy(update={
                    "value": new_text,
                    "ocr_corrected": True,
                    "confidence": round(d.confidence * 0.9, 4),
                })

        result.append(d)
    return result


def fix_decimal_by_confidence(dimensions: List[Dimension]) -> List[Dimension]:
    """신뢰도 기반 소수점 교정 — conf=0.85 구간에서 체계적 ÷10 오류 감지

    MAD 기반 교정의 보완: conf가 정확히 0.85(±0.01)인 값 중
    ×10 결과가 도면에서 더 합리적인 정수가 되는 경우 교정.

    예: 34.7 (conf=0.85) → 347, 6.81 (conf=0.85) → 68.1
    """
    result: List[Dimension] = []
    for d in dimensions:
        v = _parse_numeric(d.value)
        if v is None or d.ocr_corrected:
            result.append(d)
            continue

        # conf ≈ 0.85 (±0.015) — 체계적 ÷10 오류 지표
        is_suspect_conf = 0.835 <= d.confidence <= 0.865

        if is_suspect_conf and d.dimension_type in (
            DimensionType.LENGTH, DimensionType.DIAMETER, DimensionType.UNKNOWN
        ):
            v10 = v * 10
            # ×10이 깔끔한 정수 또는 소수점 1자리가 되는지 확인
            # IEEE 754 부동소수점 오차 허용 (116.82*10=1168.1999...98)
            is_cleaner = (
                abs(v10 - round(v10)) < 0.001  # 347.0 → 정수
                or abs(v10 * 10 - round(v10 * 10)) < 0.01  # 68.1 → 소수점 1자리
            )
            # 원본 텍스트의 소수점 자릿수 확인 (str(float)는 .0 추가하므로 부정확)
            num_match = re.search(r'(\d+\.?\d*)', re.sub(r'^[ØφΦ⌀RrMmCc]', '', d.value.strip()))
            num_str = num_match.group(1) if num_match else str(v)
            decimal_part = num_str.split('.')[1] if '.' in num_str else ''
            # 인치-미터 변환 표준값 제외 (25.4=1", 12.7=0.5", 50.8=2")
            inch_standards = {25.4, 12.7, 50.8, 76.2, 38.1, 19.05, 6.35}
            is_inch_standard = any(abs(v - s) < 0.01 for s in inch_standards)
            # 2자리 이상: 116.82→1168.2, 또는 1자리 + ×10=정수≥100: 34.7→347
            has_suspicious_decimal = not is_inch_standard and (
                len(decimal_part) >= 2
                or (len(decimal_part) == 1 and v >= 10
                    and abs(v10 - round(v10)) < 0.001 and v10 >= 100)
            )

            if is_cleaner and has_suspicious_decimal and 1 < v < 500:
                raw_str = re.search(r'(\d+\.?\d*)', re.sub(r'^[ØφΦ⌀RrMmCc]', '', d.value.strip()))
                if raw_str:
                    old = raw_str.group(1)
                    new = _format_corrected(v10, old)
                    new_value = d.value.replace(old, new, 1)
                    logger.info(
                        f"신뢰도 기반 ÷10 교정: '{d.value}' → '{new_value}' "
                        f"(conf={d.confidence:.3f})"
                    )
                    d = d.model_copy(update={
                        "value": new_value,
                        "confidence": round(d.confidence * 0.85, 4),
                        "ocr_corrected": True,
                    })

        result.append(d)
    return result


def correct_decimal_artifacts(dimensions: List[Dimension]) -> List[Dimension]:
    """OCR 소수점 오인식 교정 (클러스터 친화도 기반)

    패턴: PaddleOCR이 `490` → `4900`, `490.02` → `4900.2` 로 읽는 ×10 오류.
    전략: 값이 다른 치수들의 분포에서 고립되어 있고,
    ÷10 결과가 기존 치수 클러스터에 합류하면 교정한다.

    기존 MAD 방식은 이분포(bimodal) 데이터에서 큰 정상 값을 오교정.
    → 개선: 최대값 구간(상위 10%)만 후보로 삼고, ÷10 후 기존 값과의
    최근접 거리가 줄어드는 경우만 교정한다.

    - 교정 시 confidence *= 0.85 (불확실성 반영)
    """
    # 이전 단계에서 교정된 치수 제외하고 숫자 수집
    numeric_vals: List[float] = []
    for d in dimensions:
        if d.ocr_corrected:
            continue
        v = _parse_numeric(d.value)
        if v is not None and 0 < v < 50000:
            numeric_vals.append(v)

    if len(numeric_vals) < 5:
        return dimensions

    numeric_vals.sort()
    max_val = numeric_vals[-1]

    # 상위 10% 이상이면서 ×10 격차가 있는 값만 후보
    # (정상 분포에서는 ×10 격차가 없음)
    p90 = numeric_vals[int(len(numeric_vals) * 0.9)]

    corrected: List[Dimension] = []
    for d in dimensions:
        if d.ocr_corrected:
            corrected.append(d)
            continue

        raw_num_str = re.search(r'(\d+\.?\d*)', re.sub(r'^[ØφΦ⌀RrMmCc]', '', d.value.strip()))
        if not raw_num_str:
            corrected.append(d)
            continue
        try:
            v = float(raw_num_str.group(1))
        except ValueError:
            corrected.append(d)
            continue

        # 후보 조건: 값이 상위 10% 이상이고 max 대비 같은 자릿수
        if v >= p90 and v >= max_val * 0.5:
            v_fixed = v / 10
            # ÷10 결과가 기존 치수 클러스터에 가까운지 확인
            # "가까움" = 기존 치수 중 ±20% 범위에 다른 값이 존재
            has_neighbor = any(
                abs(nv - v_fixed) / max(v_fixed, 0.1) < 0.2
                for nv in numeric_vals if nv != v
            )
            # 원본은 고립 (±20% 범위에 이웃 없음)
            is_isolated = not any(
                abs(nv - v) / max(v, 0.1) < 0.2
                for nv in numeric_vals if nv != v
            )

            if has_neighbor and is_isolated and v_fixed <= 5000:
                old_str = raw_num_str.group(1)
                new_str = _format_corrected(v_fixed, old_str)
                new_value = d.value.replace(old_str, new_str, 1)
                logger.info(
                    f"OCR 소수점 교정: '{d.value}' → '{new_value}' "
                    f"(÷10 후 클러스터 합류, p90={p90:.1f})"
                )
                d = d.model_copy(update={
                    "value": new_value,
                    "confidence": round(d.confidence * 0.85, 4),
                    "ocr_corrected": True,
                })

        corrected.append(d)

    return corrected


def classify_material_role(
    dim: Dimension,
    image_width: int = 0,
    image_height: int = 0,
    sorted_values: Optional[List[float]] = None,
) -> MaterialRole:
    """치수의 소재 견적 역할 분류

    분류 우선순위:
    1. 치수 타입 기반 (THREAD/SURFACE_FINISH → OTHER 확정)
    2. 접두사/키워드 분석 (PCD, Ø 크기, R)
    3. 공간 위치 기반 (도면 내 위치로 전체 치수 vs 상세 치수 구분)
    4. 값 크기 기반 (대형 값 → 외경/길이 추정)
    """
    raw = dim.value.upper()

    # 1. 확정 OTHER
    if dim.dimension_type in (DimensionType.THREAD, DimensionType.SURFACE_FINISH,
                               DimensionType.ANGLE, DimensionType.CHAMFER,
                               DimensionType.TOLERANCE):
        return MaterialRole.OTHER

    # PCD (볼트 피치원) → 가공 치수
    if raw.startswith("PCD"):
        return MaterialRole.OTHER

    # 반경 단독 (R접두사) → 형상 특징이지 소재 사이즈 아님
    if dim.dimension_type == DimensionType.RADIUS:
        return MaterialRole.OTHER

    # 2. 직경 분류 (Ø 접두사 or diameter type)
    has_dia_prefix = bool(re.match(r'^[ØφΦ⌀Ø]', raw))
    if has_dia_prefix or dim.dimension_type == DimensionType.DIAMETER:
        v = _parse_numeric(dim.value)
        if v is not None:
            if v <= 30:
                return MaterialRole.OTHER        # 볼트 구멍 (M3~M30 범위)
            elif v <= 80:
                return MaterialRole.INNER_DIAMETER  # 중간: 내경 추정
            else:
                return MaterialRole.OUTER_DIAMETER  # 대형: 외경 추정
        return MaterialRole.OUTER_DIAMETER

    # 3. 위치 기반 분류 (이미지 크기 제공된 경우)
    if image_width and image_height:
        cx = (dim.bbox.x1 + dim.bbox.x2) / 2
        cy = (dim.bbox.y1 + dim.bbox.y2) / 2
        x_ratio = cx / image_width
        y_ratio = cy / image_height

        # 도면 우측 하단(title block, notes) 영역 → OTHER
        if x_ratio > 0.65 and y_ratio > 0.75:
            return MaterialRole.OTHER

        # 도면 상단 가로 방향 치수 (스팬이 넓은 경우) → 전체 치수
        bbox_width = dim.bbox.x2 - dim.bbox.x1
        bbox_height = dim.bbox.y2 - dim.bbox.y1
        is_horizontal = bbox_width > bbox_height * 1.5

        if y_ratio < 0.35 and is_horizontal:
            return MaterialRole.LENGTH

    # 4. 값 크기 기반 추론 (위치 정보 없을 때 fallback)
    v = _parse_numeric(dim.value)
    if v is not None:
        if sorted_values and len(sorted_values) >= 3:
            p70 = sorted_values[int(len(sorted_values) * 0.7)]
            if v >= p70:
                return MaterialRole.OUTER_DIAMETER  # 상위 30% 큰 값 → 주요 소재 치수
        if v >= 200:
            return MaterialRole.OUTER_DIAMETER
        if v < 5:
            return MaterialRole.OTHER  # 공차, 틈새 값

    return MaterialRole.OTHER


def postprocess_dimensions(
    dimensions: List[Dimension],
    image_width: int = 0,
    image_height: int = 0,
    image_path: Optional[str] = None,
) -> List[Dimension]:
    """치수 후처리 파이프라인

    1. 비치수 텍스트 필터링 (날짜, 도번, 섹션 라벨, 벌룬 번호)
    2. 공차 흡수 오류 교정 (486.001 → 486 ±0.01)
    3. 문자 혼동 교정 (B↔8, Ø 숫자 전위)
    4. 신뢰도 기반 ÷10 소수점 교정 (conf=0.85 구간)
    5. MAD 기반 이상치 소수점 교정 (기존)
    6. ★ OpenCV OD/ID/폭 분류기 (신규 — Ø 기호 + 동심원 + 위치)
    7. 소재 역할 분류 (OpenCV가 미분류한 치수만 fallback)

    dimension_service.py의 extract_dimensions()에서 호출한다.
    """
    original_count = len(dimensions)

    # 1. 비치수 텍스트 필터링
    dimensions = filter_non_dimension_text(dimensions)

    # 2. 공차 흡수 오류 교정
    dimensions = fix_tolerance_absorption(dimensions)

    # 3. 문자 혼동 교정
    dimensions = fix_character_confusion(dimensions)

    # 4. 신뢰도 기반 ÷10 소수점 교정
    dimensions = fix_decimal_by_confidence(dimensions)

    # 5. MAD 기반 이상치 소수점 교정 (기존)
    dimensions = correct_decimal_artifacts(dimensions)

    if len(dimensions) != original_count:
        logger.info(
            f"후처리 파이프라인: {original_count}개 → {len(dimensions)}개 "
            f"({original_count - len(dimensions)}개 제거)"
        )

    # 6. ★ OpenCV OD/ID/폭 분류기 (Ø 기호 + 동심원 + 위치)
    dimensions = classify_od_id_width(
        dimensions, image_path=image_path,
        image_width=image_width, image_height=image_height,
    )

    # 7. 역할 분류용 정렬 값 목록 (상대 크기 판단)
    sorted_vals: List[float] = sorted(
        v for d in dimensions
        if (v := _parse_numeric(d.value)) is not None and 0 < v < 5000
    )

    # 8. material_role fallback 분류 (OpenCV가 미분류한 치수만)
    result: List[Dimension] = []
    for d in dimensions:
        if d.material_role is None:
            role = classify_material_role(d, image_width, image_height, sorted_vals)
            result.append(d.model_copy(update={"material_role": role}))
        else:
            result.append(d)

    return result


def extract_dims_from_text_block(
    det: dict, base_idx: int, text: str, confidence_threshold: float
) -> List[Dimension]:
    """긴 텍스트 블록에서 치수 패턴을 추출하여 개별 Dimension으로 변환

    예: "(4)M20 Tap, & Ø17.5 Drill, thru." → [M20, Ø17.5]
    """
    if len(text) < 5:
        return []

    found: List[Dimension] = []
    seen_spans = set()

    for pat in SUB_DIM_PATTERNS:
        for m in pat.finditer(text):
            span = (m.start(), m.end())
            if any(s <= span[0] and span[1] <= e for s, e in seen_spans):
                continue
            seen_spans.add(span)

            sub_text = m.group().strip()
            sub_text = fix_diameter_symbol(sub_text)
            if not is_dimension_pattern(sub_text):
                continue

            dim = parse_paddle_detection(det, base_idx + len(found), sub_text)
            if dim and dim.confidence >= confidence_threshold and is_valid_dimension(dim):
                found.append(dim)

    return found
