"""GD&T Pattern Matcher

GD&T 심볼/특성 검출 및 패턴 매칭 순수 함수들
- GD&T 심볼 매칭
- 재료 조건 수정자 매칭
- 데이텀 참조 추출
- FCF 검출 (Feature Control Frame)
- 데이텀 검출
- FCF/데이텀 객체 생성
- 근접 FCF 병합
"""

import uuid
import re
import logging
from typing import Optional, List, Dict, Any

from schemas.detection import BoundingBox, VerificationStatus
from schemas.gdt import (
    GeometricCharacteristic,
    MaterialCondition,
    CHARACTERISTIC_CATEGORY_MAP,
    DatumReference,
    ToleranceZone,
    FeatureControlFrame,
    DatumFeature,
    GDTParsingConfig,
)

from services.gdt_symbols import (
    GDT_SYMBOL_PATTERNS,
    SURFACE_ROUGHNESS_PATTERNS,
    DIMENSION_TOLERANCE_PATTERNS,
    MATERIAL_CONDITION_PATTERNS,
    TOLERANCE_PATTERN,
    DetectedGDTElement,
)

logger = logging.getLogger(__name__)


# =========== 심볼/특성 매칭 함수 ===========

def match_gdt_symbol(text: str) -> Optional[GeometricCharacteristic]:
    """텍스트에서 GD&T 심볼 매칭"""
    text_lower = text.lower()

    for characteristic, patterns in GDT_SYMBOL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return characteristic

    return None


def match_material_condition(text: str) -> MaterialCondition:
    """재료 조건 수정자 매칭"""
    for condition, patterns in MATERIAL_CONDITION_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return condition

    return MaterialCondition.NONE


def extract_datum_references(text: str) -> List[Dict[str, Any]]:
    """데이텀 참조 추출"""
    datum_refs = []

    # 패턴: A B C 또는 A-B-C
    matches = re.findall(r'([A-Z])(?:\s*[-]?\s*)?', text)

    for i, label in enumerate(matches[:3]):  # 최대 3개
        # 재료 조건 확인 (레이블 다음에 있을 수 있음)
        mc = MaterialCondition.NONE
        datum_refs.append({
            'label': label,
            'material_condition': mc.value,
            'order': i + 1,
        })

    return datum_refs


def determine_datum_type(order: int) -> str:
    """데이텀 순서에 따른 타입 결정"""
    if order == 1:
        return 'primary'
    elif order == 2:
        return 'secondary'
    else:
        return 'tertiary'


# =========== FCF 검출 ===========

def detect_fcf(
    ocr_results: List[Dict[str, Any]],
    image_width: int,
    image_height: int,
    config: GDTParsingConfig,
) -> List[DetectedGDTElement]:
    """FCF 검출 (Feature Control Frame)"""
    elements = []

    for result in ocr_results:
        text = result.get('text', '')
        bbox = result.get('bbox', [0, 0, 0, 0])
        confidence = result.get('confidence', 0.5)
        result_type = result.get('type', 'unknown')

        # 1. 표면 거칠기 검출 (Ra, Rz 등)
        for pattern in SURFACE_ROUGHNESS_PATTERNS:
            roughness_match = re.search(pattern, text, re.IGNORECASE)
            if roughness_match:
                # 표면 거칠기 값 추출
                value_match = re.search(r'(\d+\.?\d*)', roughness_match.group())
                roughness_value = float(value_match.group(1)) if value_match else 0.0

                elements.append(DetectedGDTElement(
                    element_type='fcf',
                    bbox=tuple(bbox),
                    text=text,
                    confidence=confidence * 0.9,  # 약간 낮은 신뢰도
                    parsed_data={
                        'characteristic': GeometricCharacteristic.PROFILE_SURFACE,
                        'tolerance_value': roughness_value,
                        'tolerance_unit': 'μm',
                        'is_diameter': False,
                        'material_condition': MaterialCondition.NONE,
                        'datum_refs': [],
                        'is_surface_roughness': True,
                    }
                ))
                break  # 하나의 OCR 결과에서 하나만 추출

        # 2. GD&T 심볼 패턴 매칭
        characteristic = match_gdt_symbol(text)
        if characteristic:
            # 공차 값 추출
            tolerance_match = re.search(TOLERANCE_PATTERN, text)
            tolerance_value = float(tolerance_match.group(1)) if tolerance_match else 0.0
            tolerance_unit = tolerance_match.group(2) if tolerance_match and tolerance_match.group(2) else "mm"

            # 직경 공차 여부
            is_diameter = bool(re.search(r'[⌀φØ]', text))

            # 재료 조건
            material_condition = match_material_condition(text)

            # 데이텀 참조 추출
            datum_refs = extract_datum_references(text)

            elements.append(DetectedGDTElement(
                element_type='fcf',
                bbox=tuple(bbox),
                text=text,
                confidence=confidence,
                parsed_data={
                    'characteristic': characteristic,
                    'tolerance_value': tolerance_value,
                    'tolerance_unit': tolerance_unit,
                    'is_diameter': is_diameter,
                    'material_condition': material_condition,
                    'datum_refs': datum_refs,
                }
            ))

        # 3. 치수 공차 패턴 (dimension 타입에서)
        if result_type == 'dimension':
            for pattern in DIMENSION_TOLERANCE_PATTERNS:
                if re.search(pattern, text):
                    tol_match = re.search(r'(\d+\.?\d*)', text)
                    tol_value = float(tol_match.group(1)) if tol_match else 0.0

                    elements.append(DetectedGDTElement(
                        element_type='fcf',
                        bbox=tuple(bbox),
                        text=text,
                        confidence=confidence * 0.8,
                        parsed_data={
                            'characteristic': GeometricCharacteristic.POSITION,  # 기본값
                            'tolerance_value': tol_value,
                            'tolerance_unit': 'mm',
                            'is_diameter': False,
                            'material_condition': MaterialCondition.NONE,
                            'datum_refs': [],
                            'is_dimension_tolerance': True,
                        }
                    ))
                    break

    logger.info(f"[GDT] Detected {len(elements)} FCF elements")
    return elements


# =========== 데이텀 검출 ===========

def detect_datums(
    ocr_results: List[Dict[str, Any]],
    image_width: int,
    image_height: int,
    config: GDTParsingConfig,
) -> List[DetectedGDTElement]:
    """데이텀 검출 (기준면/기준점)"""
    elements = []
    seen_labels = set()

    # 제외할 패턴 (데이텀이 아닌 것들)
    exclude_patterns = [
        r'^R[aztp]',          # 표면 거칠기 (Ra, Rz)
        r'^\d',               # 숫자로 시작
        r'^[A-Z]\d{2,}',      # 도면번호 패턴 (A12-311197)
        r'Rev\.',             # 리비전
        r'DWG',               # 도면
    ]

    # 1단계: 단독 데이텀 패턴 (정확한 매칭)
    exact_datum_patterns = [
        r'^[A-Z]$',                    # 단일 대문자 (A, B, C)
        r'^[A-Z]\d?$',                 # 대문자 또는 대문자+숫자 (A, A1)
        r'^[-△▽▲▼][A-Z][-△▽▲▼]?$',    # 데이텀 심볼 (-A-, △A, ▲B)
        r'^\[[A-Z]\]$',                # 대괄호 ([A], [B])
        r'^[A-Z]\s*[-–—]\s*[A-Z]$',    # 복합 데이텀 (A-B)
    ]

    # 2단계: 텍스트 내 데이텀 참조 패턴 (공차 뒤에 오는 데이텀)
    embedded_datum_patterns = [
        r'(?:±|\+|-|\/)\s*[\d.]+\s+([A-Z])(?:\s+([A-Z]))?(?:\s+([A-Z]))?$',  # ±0.1 A B C
        r'(?:⌀|φ|Ø)\s*[\d.]+\s+([A-Z])(?:\s+([A-Z]))?(?:\s+([A-Z]))?$',      # ⌀0.05 A B
        r'\)\s*([A-Z])(?:\s+([A-Z]))?(?:\s+([A-Z]))?$',                        # (M) A B
    ]

    for result in ocr_results:
        text = result.get('text', '').strip()
        bbox = result.get('bbox', [0, 0, 0, 0])
        confidence = result.get('confidence', 0.5)

        # 제외 패턴 체크
        should_exclude = False
        for pattern in exclude_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                should_exclude = True
                break
        if should_exclude:
            continue

        # 1단계: 정확한 데이텀 패턴 매칭
        for pattern in exact_datum_patterns:
            if re.match(pattern, text):
                labels = re.findall(r'[A-Z]', text)
                for label in labels:
                    if label not in seen_labels:
                        seen_labels.add(label)
                        elements.append(DetectedGDTElement(
                            element_type='datum',
                            bbox=tuple(bbox),
                            text=text,
                            confidence=confidence,
                            parsed_data={
                                'label': label,
                                'datum_type': determine_datum_type(len(seen_labels)),
                            }
                        ))
                break

        # 2단계: 텍스트 내 데이텀 참조 추출
        for pattern in embedded_datum_patterns:
            match = re.search(pattern, text)
            if match:
                # 그룹에서 데이텀 레이블 추출
                for group in match.groups():
                    if group and group not in seen_labels:
                        # 단일 대문자인지 확인 (M, L, S는 재료 조건이므로 제외)
                        if len(group) == 1 and group not in ['M', 'L', 'S']:
                            seen_labels.add(group)
                            elements.append(DetectedGDTElement(
                                element_type='datum',
                                bbox=tuple(bbox),
                                text=text,
                                confidence=confidence * 0.9,  # 내장 패턴은 신뢰도 약간 낮춤
                                parsed_data={
                                    'label': group,
                                    'datum_type': determine_datum_type(len(seen_labels)),
                                    'extracted_from': 'embedded',
                                }
                            ))
                break

    # 3단계: 도면에서 일반적인 데이텀 위치 기반 추정
    # (OCR에서 검출되지 않은 경우 이미지 하단/우측 영역의 단독 문자 확인)
    if len(elements) == 0:
        for result in ocr_results:
            text = result.get('text', '').strip()
            bbox = result.get('bbox', [0, 0, 0, 0])
            confidence = result.get('confidence', 0.5)

            # 2-3 글자 텍스트에서 대문자만 있는 경우 (예: "A", "AB", "B1")
            if 1 <= len(text) <= 3 and text.isalnum():
                labels = [c for c in text if c.isupper() and c not in ['M', 'L', 'S', 'R']]
                for label in labels:
                    if label not in seen_labels:
                        seen_labels.add(label)
                        elements.append(DetectedGDTElement(
                            element_type='datum',
                            bbox=tuple(bbox),
                            text=text,
                            confidence=max(confidence * 0.85, 0.6),  # 최소 0.6 보장
                            parsed_data={
                                'label': label,
                                'datum_type': determine_datum_type(len(seen_labels)),
                                'extracted_from': 'inferred',
                            }
                        ))

    # 디버그: 검출된 데이텀 출력
    if elements:
        logger.info(f"[GDT] Detected {len(elements)} datums: {[e.parsed_data.get('label') for e in elements]}")
    else:
        logger.debug(f"[GDT] No datums detected from {len(ocr_results)} OCR items")
        # 디버그: 짧은 텍스트 출력
        short_texts = [r.get('text', '')[:20] for r in ocr_results if len(r.get('text', '')) <= 10]
        if short_texts:
            logger.debug(f"[GDT] Short texts found: {short_texts[:10]}")

    return elements


# =========== 객체 생성 ===========

def create_fcf(
    element: DetectedGDTElement,
    image_width: int,
    image_height: int,
) -> Optional[FeatureControlFrame]:
    """FCF 객체 생성"""
    data = element.parsed_data
    characteristic = data.get('characteristic')

    if not characteristic:
        return None

    # 데이텀 참조 변환
    datum_refs = []
    for ref in data.get('datum_refs', []):
        datum_refs.append(DatumReference(
            label=ref['label'],
            material_condition=MaterialCondition(ref['material_condition']),
            order=ref['order'],
        ))

    # 정규화 좌표
    bbox_normalized = [
        element.bbox[0] / image_width,
        element.bbox[1] / image_height,
        element.bbox[2] / image_width,
        element.bbox[3] / image_height,
    ]

    return FeatureControlFrame(
        id=str(uuid.uuid4()),
        characteristic=characteristic,
        category=CHARACTERISTIC_CATEGORY_MAP.get(characteristic),
        tolerance=ToleranceZone(
            value=data.get('tolerance_value', 0.0),
            unit=data.get('tolerance_unit', 'mm'),
            diameter=data.get('is_diameter', False),
            material_condition=MaterialCondition(data.get('material_condition', 'none')),
        ),
        datums=datum_refs,
        bbox=BoundingBox(
            x1=element.bbox[0],
            y1=element.bbox[1],
            x2=element.bbox[2],
            y2=element.bbox[3],
        ),
        bbox_normalized=bbox_normalized,
        confidence=element.confidence,
        raw_text=element.text,
    )


def create_datum(
    element: DetectedGDTElement,
    image_width: int,
    image_height: int,
) -> Optional[DatumFeature]:
    """데이텀 객체 생성"""
    data = element.parsed_data

    bbox_normalized = [
        element.bbox[0] / image_width,
        element.bbox[1] / image_height,
        element.bbox[2] / image_width,
        element.bbox[3] / image_height,
    ]

    return DatumFeature(
        id=str(uuid.uuid4()),
        label=data.get('label', 'A'),
        bbox=BoundingBox(
            x1=element.bbox[0],
            y1=element.bbox[1],
            x2=element.bbox[2],
            y2=element.bbox[3],
        ),
        bbox_normalized=bbox_normalized,
        datum_type=data.get('datum_type', 'primary'),
        confidence=element.confidence,
    )


# =========== 근접 병합 ===========

def bbox_distance(bbox1: BoundingBox, bbox2: BoundingBox) -> float:
    """두 bbox 중심 간 거리"""
    cx1 = (bbox1.x1 + bbox1.x2) / 2
    cy1 = (bbox1.y1 + bbox1.y2) / 2
    cx2 = (bbox2.x1 + bbox2.x2) / 2
    cy2 = (bbox2.y1 + bbox2.y2) / 2

    return ((cx2 - cx1) ** 2 + (cy2 - cy1) ** 2) ** 0.5


def merge_nearby_fcf(
    fcf_list: List[FeatureControlFrame],
    merge_distance: float,
) -> List[FeatureControlFrame]:
    """근접 FCF 병합"""
    if len(fcf_list) <= 1:
        return fcf_list

    # 간단한 구현: 같은 특성의 근접 FCF 병합
    merged = []
    used = set()

    for i, fcf1 in enumerate(fcf_list):
        if i in used:
            continue

        best_fcf = fcf1
        for j, fcf2 in enumerate(fcf_list):
            if i == j or j in used:
                continue

            # 같은 특성이고 근접한 경우
            if fcf1.characteristic == fcf2.characteristic:
                distance = bbox_distance(fcf1.bbox, fcf2.bbox)
                if distance < merge_distance:
                    # 신뢰도가 높은 쪽 선택
                    if fcf2.confidence > best_fcf.confidence:
                        best_fcf = fcf2
                    used.add(j)

        merged.append(best_fcf)
        used.add(i)

    return merged
