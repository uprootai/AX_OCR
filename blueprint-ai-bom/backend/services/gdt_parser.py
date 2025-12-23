"""GD&T Parser Service (Phase 7)

기하공차 파싱 서비스
- Feature Control Frame (FCF) 검출
- 기하 특성 심볼 인식 (14종)
- 데이텀 참조 추출
- 공차 값 파싱
"""

import uuid
import re
import time
import os
import logging
import traceback
import httpx
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field

from PIL import Image
import numpy as np

# Logger 설정
logger = logging.getLogger(__name__)

# eDOCr2 OCR API 설정
EDOCR2_API_URL = os.getenv("EDOCR2_API_URL", "http://edocr2-v2-api:5002")
OCR_TIMEOUT = 120.0  # seconds

from schemas.detection import BoundingBox, VerificationStatus
from schemas.gdt import (
    GeometricCharacteristic,
    MaterialCondition,
    GDTCategory,
    CHARACTERISTIC_CATEGORY_MAP,
    CHARACTERISTIC_SYMBOLS,
    CHARACTERISTIC_LABELS,
    DatumReference,
    ToleranceZone,
    FeatureControlFrame,
    DatumFeature,
    GDTParsingConfig,
    GDTParsingResult,
    FCFUpdate,
    ManualFCF,
    ManualDatum,
    GDTSummary,
)


# GD&T 심볼 패턴 (OCR 텍스트에서 검출)
GDT_SYMBOL_PATTERNS = {
    # Form (형상 공차)
    GeometricCharacteristic.STRAIGHTNESS: [r'[-─—]', r'직진도', r'straightness'],
    GeometricCharacteristic.FLATNESS: [r'[▱◇□]', r'평면도', r'flatness', r'flat'],
    GeometricCharacteristic.CIRCULARITY: [r'[○◯⚪]', r'진원도', r'circularity', r'roundness'],
    GeometricCharacteristic.CYLINDRICITY: [r'[⌭]', r'원통도', r'cylindricity'],

    # Profile (윤곽 공차)
    GeometricCharacteristic.PROFILE_LINE: [r'[⌒]', r'선.*윤곽', r'profile.*line'],
    GeometricCharacteristic.PROFILE_SURFACE: [r'[⌓]', r'면.*윤곽', r'profile.*surface', r'Ra\d', r'R[az]\s*\d'],

    # Orientation (방향 공차)
    GeometricCharacteristic.ANGULARITY: [r'[∠]', r'경사도', r'angularity', r'\d+°'],
    GeometricCharacteristic.PERPENDICULARITY: [r'[⊥]', r'직각도', r'perpendicularity', r'perp'],
    GeometricCharacteristic.PARALLELISM: [r'[∥‖//]', r'평행도', r'parallelism'],

    # Location (위치 공차)
    GeometricCharacteristic.POSITION: [r'[⌖⊕⊙\+]', r'위치도', r'position', r'true.*position', r'TP'],
    GeometricCharacteristic.CONCENTRICITY: [r'[◎⊚]', r'동심도', r'concentricity', r'coaxiality', r'conc'],
    GeometricCharacteristic.SYMMETRY: [r'[⌯≡]', r'대칭도', r'symmetry', r'sym'],

    # Runout (흔들림 공차)
    GeometricCharacteristic.CIRCULAR_RUNOUT: [r'[↗→]', r'원주.*흔들림', r'circular.*runout', r'TIR'],
    GeometricCharacteristic.TOTAL_RUNOUT: [r'[⇗⟹]', r'전체.*흔들림', r'total.*runout'],
}

# 표면 거칠기 패턴 (Ra, Rz, Rt 등)
SURFACE_ROUGHNESS_PATTERNS = [
    r'R[aztp]\s*\d+\.?\d*',  # Ra3.2, Rz6.3
    r'√\s*\d+\.?\d*',        # √3.2
    r'∇\s*\d+\.?\d*',        # ∇표기
]

# 공차 표기 패턴 (치수 공차)
DIMENSION_TOLERANCE_PATTERNS = [
    r'[±]\s*\d+\.?\d*',           # ±0.1
    r'\+\d+\.?\d*\s*[-/]\s*\d+\.?\d*',  # +0.2/-0.1
    r'\(\d+\.?\d*\)',              # (177) 참조 치수
]

# 재료 조건 수정자 패턴
MATERIAL_CONDITION_PATTERNS = {
    MaterialCondition.MMC: [r'[Ⓜ]', r'\(M\)', r'MMC', r'최대.*실체'],
    MaterialCondition.LMC: [r'[Ⓛ]', r'\(L\)', r'LMC', r'최소.*실체'],
    MaterialCondition.RFS: [r'[Ⓢ]', r'\(S\)', r'RFS'],
}

# 데이텀 레이블 패턴
DATUM_LABEL_PATTERN = r'[A-Z](?:\s*-\s*[A-Z])?'

# 공차 값 패턴 (예: 0.05, ⌀0.1, 0.02 A B)
TOLERANCE_PATTERN = r'(?:⌀|φ|Ø)?\s*(\d+(?:\.\d+)?)\s*(mm|in)?'


@dataclass
class DetectedGDTElement:
    """검출된 GD&T 요소"""
    element_type: str  # 'fcf', 'datum', 'symbol'
    bbox: Tuple[float, float, float, float]
    text: str
    confidence: float
    parsed_data: Dict[str, Any] = field(default_factory=dict)


class GDTParser:
    """GD&T 파서 서비스"""

    def __init__(self):
        # 세션별 GD&T 데이터 저장
        self.session_fcf: Dict[str, List[FeatureControlFrame]] = {}
        self.session_datums: Dict[str, List[DatumFeature]] = {}

    async def parse(
        self,
        session_id: str,
        image_path: str,
        config: Optional[GDTParsingConfig] = None,
        ocr_results: Optional[List[Dict[str, Any]]] = None,
    ) -> GDTParsingResult:
        """
        GD&T 파싱 실행

        Args:
            session_id: 세션 ID
            image_path: 이미지 파일 경로
            config: 파싱 설정
            ocr_results: 기존 OCR 결과 (없으면 새로 실행)

        Returns:
            GDTParsingResult: 파싱 결과
        """
        logger.info(f"[GDT] === Parse started for session: {session_id} ===")
        logger.info(f"[GDT] Image path: {image_path}")
        logger.info(f"[GDT] OCR results provided: {ocr_results is not None}")

        start_time = time.time()
        config = config or GDTParsingConfig()

        # 이미지 로드
        try:
            image = Image.open(image_path)
            image_width, image_height = image.size
        except Exception as e:
            raise ValueError(f"이미지 로드 실패: {e}")

        # OCR 결과가 없으면 시뮬레이션 (실제로는 OCR API 호출)
        if ocr_results is None:
            ocr_results = await self._run_ocr(image_path, config.ocr_engine)

        # GD&T 요소 검출
        detected_elements: List[DetectedGDTElement] = []

        # 1. FCF 검출
        if config.detect_fcf:
            fcf_elements = self._detect_fcf(ocr_results, image_width, image_height, config)
            detected_elements.extend(fcf_elements)

        # 2. 데이텀 검출
        if config.detect_datums:
            datum_elements = self._detect_datums(ocr_results, image_width, image_height, config)
            detected_elements.extend(datum_elements)

        # 3. FCF 객체 생성
        fcf_list = []
        for elem in detected_elements:
            if elem.element_type == 'fcf':
                fcf = self._create_fcf(elem, image_width, image_height)
                if fcf and fcf.confidence >= config.confidence_threshold:
                    fcf_list.append(fcf)

        # 4. 데이텀 객체 생성
        datums = []
        datum_elements = [e for e in detected_elements if e.element_type == 'datum']
        logger.info(f"[GDT] Processing {len(datum_elements)} datum elements (threshold: {config.confidence_threshold})")
        for elem in datum_elements:
            datum = self._create_datum(elem, image_width, image_height)
            if datum:
                logger.debug(f"[GDT] Datum '{datum.label}' confidence: {datum.confidence:.2f}")
                if datum.confidence >= config.confidence_threshold:
                    datums.append(datum)
                else:
                    logger.debug(f"[GDT] Datum '{datum.label}' filtered (below threshold)")

        # 5. 근접 심볼 병합
        if config.merge_nearby_symbols:
            fcf_list = self._merge_nearby_fcf(fcf_list, config.merge_distance)

        # 세션에 저장
        self.session_fcf[session_id] = fcf_list
        self.session_datums[session_id] = datums

        # 통계 계산
        fcf_by_category: Dict[str, int] = {}
        fcf_by_characteristic: Dict[str, int] = {}

        for fcf in fcf_list:
            # 카테고리별
            category = CHARACTERISTIC_CATEGORY_MAP.get(fcf.characteristic)
            if category:
                cat_name = category.value
                fcf_by_category[cat_name] = fcf_by_category.get(cat_name, 0) + 1

            # 특성별
            char_name = fcf.characteristic.value
            fcf_by_characteristic[char_name] = fcf_by_characteristic.get(char_name, 0) + 1

        processing_time_ms = (time.time() - start_time) * 1000

        return GDTParsingResult(
            session_id=session_id,
            fcf_list=fcf_list,
            datums=datums,
            image_width=image_width,
            image_height=image_height,
            total_fcf=len(fcf_list),
            total_datums=len(datums),
            processing_time_ms=processing_time_ms,
            fcf_by_category=fcf_by_category,
            fcf_by_characteristic=fcf_by_characteristic,
        )

    async def _run_ocr(
        self,
        image_path: str,
        ocr_engine: str = "edocr2"
    ) -> List[Dict[str, Any]]:
        """
        OCR API 호출하여 텍스트 추출

        Returns:
            OCR 결과 리스트: [{"text": str, "bbox": [x1,y1,x2,y2], "confidence": float}, ...]
        """
        ocr_results: List[Dict[str, Any]] = []

        logger.info(f"[GDT] Starting OCR for image: {image_path}")
        logger.debug(f"[GDT] OCR URL: {EDOCR2_API_URL}/api/v2/ocr")

        try:
            async with httpx.AsyncClient(timeout=OCR_TIMEOUT) as client:
                # 이미지 파일 전송
                with open(image_path, "rb") as f:
                    files = {"file": (os.path.basename(image_path), f, "image/jpeg")}
                    response = await client.post(
                        f"{EDOCR2_API_URL}/api/v2/ocr",
                        files=files
                    )

                if response.status_code != 200:
                    logger.error(f"[GDT] OCR API error: {response.status_code}")
                    return []

                data = response.json()
                ocr_data = data.get("data", {})

                # 1. 치수 데이터 변환 (GD&T 패턴 포함 가능)
                for dim in ocr_data.get("dimensions", []):
                    location = dim.get("location", [[0,0], [0,0], [0,0], [0,0]])
                    # 4점 폴리곤을 bbox로 변환
                    xs = [p[0] for p in location]
                    ys = [p[1] for p in location]
                    bbox = [min(xs), min(ys), max(xs), max(ys)]

                    text = dim.get("value", "")
                    tolerance = dim.get("tolerance")
                    if tolerance:
                        text += f" {tolerance}"

                    ocr_results.append({
                        "text": text,
                        "bbox": bbox,
                        "confidence": 0.9,
                        "type": "dimension"
                    })

                # 2. 일반 텍스트 변환
                text_data = ocr_data.get("text", {})
                if isinstance(text_data, dict):
                    for key, value in text_data.items():
                        if isinstance(value, str) and value.strip():
                            ocr_results.append({
                                "text": value,
                                "bbox": [0, 0, 100, 20],  # 위치 정보 없음
                                "confidence": 0.8,
                                "type": "text"
                            })

                # 3. possible_text 변환 (잠재적 GD&T 포함)
                for item in ocr_data.get("possible_text", []):
                    location = item.get("location", [[0,0], [0,0], [0,0], [0,0]])
                    xs = [p[0] for p in location]
                    ys = [p[1] for p in location]
                    bbox = [min(xs), min(ys), max(xs), max(ys)]

                    ocr_results.append({
                        "text": item.get("text", ""),
                        "bbox": bbox,
                        "confidence": 0.7,
                        "type": "possible_text"
                    })

                # 4. GD&T 데이터 (eDOCr2에서 직접 감지된 경우)
                for gdt in ocr_data.get("gdt", []):
                    location = gdt.get("location", [[0,0], [0,0], [0,0], [0,0]])
                    xs = [p[0] for p in location]
                    ys = [p[1] for p in location]
                    bbox = [min(xs), min(ys), max(xs), max(ys)]

                    ocr_results.append({
                        "text": gdt.get("symbol", "") + " " + gdt.get("value", ""),
                        "bbox": bbox,
                        "confidence": 0.95,
                        "type": "gdt"
                    })

                logger.info(f"[GDT] OCR completed: {len(ocr_results)} items")

        except httpx.TimeoutException:
            logger.warning(f"[GDT] OCR timeout after {OCR_TIMEOUT}s")
        except FileNotFoundError as e:
            logger.error(f"[GDT] Image file not found: {e}")
        except Exception as e:
            logger.error(f"[GDT] OCR error: {e}")
            logger.debug(f"[GDT] Traceback: {traceback.format_exc()}")

        return ocr_results

    def _detect_fcf(
        self,
        ocr_results: List[Dict[str, Any]],
        image_width: int,
        image_height: int,
        config: GDTParsingConfig
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
            characteristic = self._match_gdt_symbol(text)
            if characteristic:
                # 공차 값 추출
                tolerance_match = re.search(TOLERANCE_PATTERN, text)
                tolerance_value = float(tolerance_match.group(1)) if tolerance_match else 0.0
                tolerance_unit = tolerance_match.group(2) if tolerance_match and tolerance_match.group(2) else "mm"

                # 직경 공차 여부
                is_diameter = bool(re.search(r'[⌀φØ]', text))

                # 재료 조건
                material_condition = self._match_material_condition(text)

                # 데이텀 참조 추출
                datum_refs = self._extract_datum_references(text)

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

    def _detect_datums(
        self,
        ocr_results: List[Dict[str, Any]],
        image_width: int,
        image_height: int,
        config: GDTParsingConfig
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
            result_type = result.get('type', 'unknown')

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
                                    'datum_type': self._determine_datum_type(len(seen_labels)),
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
                                        'datum_type': self._determine_datum_type(len(seen_labels)),
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
                                    'datum_type': self._determine_datum_type(len(seen_labels)),
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

    def _determine_datum_type(self, order: int) -> str:
        """데이텀 순서에 따른 타입 결정"""
        if order == 1:
            return 'primary'
        elif order == 2:
            return 'secondary'
        else:
            return 'tertiary'

    def _match_gdt_symbol(self, text: str) -> Optional[GeometricCharacteristic]:
        """텍스트에서 GD&T 심볼 매칭"""
        text_lower = text.lower()

        for characteristic, patterns in GDT_SYMBOL_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return characteristic

        return None

    def _match_material_condition(self, text: str) -> MaterialCondition:
        """재료 조건 수정자 매칭"""
        for condition, patterns in MATERIAL_CONDITION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return condition

        return MaterialCondition.NONE

    def _extract_datum_references(self, text: str) -> List[Dict[str, Any]]:
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

    def _create_fcf(
        self,
        element: DetectedGDTElement,
        image_width: int,
        image_height: int
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

    def _create_datum(
        self,
        element: DetectedGDTElement,
        image_width: int,
        image_height: int
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

    def _merge_nearby_fcf(
        self,
        fcf_list: List[FeatureControlFrame],
        merge_distance: float
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
                    distance = self._bbox_distance(fcf1.bbox, fcf2.bbox)
                    if distance < merge_distance:
                        # 신뢰도가 높은 쪽 선택
                        if fcf2.confidence > best_fcf.confidence:
                            best_fcf = fcf2
                        used.add(j)

            merged.append(best_fcf)
            used.add(i)

        return merged

    def _bbox_distance(self, bbox1: BoundingBox, bbox2: BoundingBox) -> float:
        """두 bbox 중심 간 거리"""
        cx1 = (bbox1.x1 + bbox1.x2) / 2
        cy1 = (bbox1.y1 + bbox1.y2) / 2
        cx2 = (bbox2.x1 + bbox2.x2) / 2
        cy2 = (bbox2.y1 + bbox2.y2) / 2

        return ((cx2 - cx1) ** 2 + (cy2 - cy1) ** 2) ** 0.5

    # =========== FCF 관리 ===========

    def get_fcf_list(self, session_id: str) -> List[FeatureControlFrame]:
        """세션의 FCF 목록 조회"""
        return self.session_fcf.get(session_id, [])

    def get_fcf(self, session_id: str, fcf_id: str) -> Optional[FeatureControlFrame]:
        """특정 FCF 조회"""
        fcf_list = self.session_fcf.get(session_id, [])
        for fcf in fcf_list:
            if fcf.id == fcf_id:
                return fcf
        return None

    def update_fcf(
        self,
        session_id: str,
        update: FCFUpdate
    ) -> Optional[FeatureControlFrame]:
        """FCF 업데이트"""
        fcf_list = self.session_fcf.get(session_id, [])

        for i, fcf in enumerate(fcf_list):
            if fcf.id == update.fcf_id:
                if update.characteristic is not None:
                    fcf.characteristic = update.characteristic
                    fcf.category = CHARACTERISTIC_CATEGORY_MAP.get(update.characteristic)
                if update.tolerance_value is not None:
                    fcf.tolerance.value = update.tolerance_value
                if update.tolerance_unit is not None:
                    fcf.tolerance.unit = update.tolerance_unit
                if update.datums is not None:
                    fcf.datums = update.datums
                if update.verification_status is not None:
                    fcf.verification_status = update.verification_status
                if update.notes is not None:
                    fcf.notes = update.notes

                self.session_fcf[session_id][i] = fcf
                return fcf

        return None

    def add_fcf(
        self,
        session_id: str,
        manual_fcf: ManualFCF,
        image_width: int,
        image_height: int
    ) -> FeatureControlFrame:
        """수동 FCF 추가"""
        # 데이텀 참조 변환
        datum_refs = manual_fcf.datums or []

        # 정규화 좌표
        bbox_normalized = [
            manual_fcf.bbox.x1 / image_width,
            manual_fcf.bbox.y1 / image_height,
            manual_fcf.bbox.x2 / image_width,
            manual_fcf.bbox.y2 / image_height,
        ]

        fcf = FeatureControlFrame(
            id=str(uuid.uuid4()),
            characteristic=manual_fcf.characteristic,
            category=CHARACTERISTIC_CATEGORY_MAP.get(manual_fcf.characteristic),
            tolerance=ToleranceZone(
                value=manual_fcf.tolerance_value,
                unit=manual_fcf.tolerance_unit,
                diameter=manual_fcf.diameter,
                material_condition=manual_fcf.material_condition,
            ),
            datums=datum_refs,
            bbox=manual_fcf.bbox,
            bbox_normalized=bbox_normalized,
            confidence=1.0,  # 수동 추가는 신뢰도 100%
            verification_status=VerificationStatus.APPROVED,
        )

        if session_id not in self.session_fcf:
            self.session_fcf[session_id] = []

        self.session_fcf[session_id].append(fcf)
        return fcf

    def delete_fcf(self, session_id: str, fcf_id: str) -> bool:
        """FCF 삭제"""
        fcf_list = self.session_fcf.get(session_id, [])

        for i, fcf in enumerate(fcf_list):
            if fcf.id == fcf_id:
                del self.session_fcf[session_id][i]
                return True

        return False

    # =========== 데이텀 관리 ===========

    def get_datums(self, session_id: str) -> List[DatumFeature]:
        """세션의 데이텀 목록 조회"""
        return self.session_datums.get(session_id, [])

    def get_datum(self, session_id: str, datum_id: str) -> Optional[DatumFeature]:
        """특정 데이텀 조회"""
        datums = self.session_datums.get(session_id, [])
        for datum in datums:
            if datum.id == datum_id:
                return datum
        return None

    def add_datum(
        self,
        session_id: str,
        manual_datum: ManualDatum,
        image_width: int,
        image_height: int
    ) -> DatumFeature:
        """수동 데이텀 추가"""
        bbox_normalized = [
            manual_datum.bbox.x1 / image_width,
            manual_datum.bbox.y1 / image_height,
            manual_datum.bbox.x2 / image_width,
            manual_datum.bbox.y2 / image_height,
        ]

        datum = DatumFeature(
            id=str(uuid.uuid4()),
            label=manual_datum.label.upper(),
            bbox=manual_datum.bbox,
            bbox_normalized=bbox_normalized,
            datum_type=manual_datum.datum_type,
            confidence=1.0,
            verification_status=VerificationStatus.APPROVED,
        )

        if session_id not in self.session_datums:
            self.session_datums[session_id] = []

        self.session_datums[session_id].append(datum)
        return datum

    def delete_datum(self, session_id: str, datum_id: str) -> bool:
        """데이텀 삭제"""
        datums = self.session_datums.get(session_id, [])

        for i, datum in enumerate(datums):
            if datum.id == datum_id:
                del self.session_datums[session_id][i]
                return True

        return False

    # =========== 요약 ===========

    def get_summary(self, session_id: str) -> GDTSummary:
        """GD&T 요약 정보"""
        fcf_list = self.session_fcf.get(session_id, [])
        datums = self.session_datums.get(session_id, [])

        # 카테고리별 FCF 수
        fcf_by_category: Dict[str, int] = {}
        fcf_by_characteristic: Dict[str, int] = {}
        verified_count = 0
        pending_count = 0
        total_confidence = 0.0
        low_confidence_count = 0

        for fcf in fcf_list:
            # 카테고리별
            category = CHARACTERISTIC_CATEGORY_MAP.get(fcf.characteristic)
            if category:
                cat_name = category.value
                fcf_by_category[cat_name] = fcf_by_category.get(cat_name, 0) + 1

            # 특성별
            char_name = fcf.characteristic.value
            fcf_by_characteristic[char_name] = fcf_by_characteristic.get(char_name, 0) + 1

            # 검증 상태
            if fcf.verification_status == VerificationStatus.APPROVED:
                verified_count += 1
            else:
                pending_count += 1

            # 신뢰도
            total_confidence += fcf.confidence
            if fcf.confidence < 0.7:
                low_confidence_count += 1

        avg_confidence = total_confidence / len(fcf_list) if fcf_list else 0.0
        datum_labels = sorted(set(d.label for d in datums))

        return GDTSummary(
            session_id=session_id,
            total_fcf=len(fcf_list),
            fcf_by_category=fcf_by_category,
            fcf_by_characteristic=fcf_by_characteristic,
            total_datums=len(datums),
            datum_labels=datum_labels,
            verified_fcf=verified_count,
            pending_fcf=pending_count,
            avg_confidence=avg_confidence,
            low_confidence_count=low_confidence_count,
        )


# 싱글톤 인스턴스
gdt_parser = GDTParser()
