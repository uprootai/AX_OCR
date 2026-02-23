"""GD&T Parser Service (Phase 7)

기하공차 파싱 서비스
- Feature Control Frame (FCF) 검출
- 기하 특성 심볼 인식 (14종)
- 데이텀 참조 추출
- 공차 값 파싱

Barrel re-export: gdt_symbols, gdt_pattern_matcher 모듈의 공개 API를 재수출
"""

import uuid
import time
import os
import logging
import traceback
import httpx
from typing import Optional, List, Dict, Any

from PIL import Image

# Barrel re-exports (기존 import 경로 호환)
from services.gdt_symbols import (  # noqa: F401
    GDT_SYMBOL_PATTERNS,
    SURFACE_ROUGHNESS_PATTERNS,
    DIMENSION_TOLERANCE_PATTERNS,
    MATERIAL_CONDITION_PATTERNS,
    DATUM_LABEL_PATTERN,
    TOLERANCE_PATTERN,
    DetectedGDTElement,
)
from services.gdt_pattern_matcher import (  # noqa: F401
    match_gdt_symbol,
    match_material_condition,
    extract_datum_references,
    determine_datum_type,
    detect_fcf,
    detect_datums,
    create_fcf,
    create_datum,
    bbox_distance,
    merge_nearby_fcf,
)

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
    GDTParsingResult,
    FCFUpdate,
    ManualFCF,
    ManualDatum,
    GDTSummary,
)

# Logger 설정
logger = logging.getLogger(__name__)

# eDOCr2 OCR API 설정
EDOCR2_API_URL = os.getenv("EDOCR2_API_URL", "http://edocr2-v2-api:5002")
OCR_TIMEOUT = 120.0  # seconds


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
            fcf_elements = detect_fcf(ocr_results, image_width, image_height, config)
            detected_elements.extend(fcf_elements)

        # 2. 데이텀 검출
        if config.detect_datums:
            datum_elements = detect_datums(ocr_results, image_width, image_height, config)
            detected_elements.extend(datum_elements)

        # 3. FCF 객체 생성
        fcf_list = []
        for elem in detected_elements:
            if elem.element_type == 'fcf':
                fcf = create_fcf(elem, image_width, image_height)
                if fcf and fcf.confidence >= config.confidence_threshold:
                    fcf_list.append(fcf)

        # 4. 데이텀 객체 생성
        datums = []
        datum_elems = [e for e in detected_elements if e.element_type == 'datum']
        logger.info(f"[GDT] Processing {len(datum_elems)} datum elements (threshold: {config.confidence_threshold})")
        for elem in datum_elems:
            datum = create_datum(elem, image_width, image_height)
            if datum:
                logger.debug(f"[GDT] Datum '{datum.label}' confidence: {datum.confidence:.2f}")
                if datum.confidence >= config.confidence_threshold:
                    datums.append(datum)
                else:
                    logger.debug(f"[GDT] Datum '{datum.label}' filtered (below threshold)")

        # 5. 근접 심볼 병합
        if config.merge_nearby_symbols:
            fcf_list = merge_nearby_fcf(fcf_list, config.merge_distance)

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
