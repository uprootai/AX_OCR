"""
BOM Matcher Executor
Title Block + Parts List + Dimension Parser → 통합 BOM 생성

매칭 전략:
1. strict: 정확한 필드 일치만 매칭
2. fuzzy: 유사도 기반 매칭 (Levenshtein)
3. hybrid: 정확 일치 우선, 실패 시 유사도 매칭

견적 생성:
- price_database 서비스 연동으로 재질별/부품별 단가 계산
- 고객별 할인율 적용
- 수량 할인 자동 계산
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import re
import logging
from difflib import SequenceMatcher

from ..executors.base_executor import BaseNodeExecutor
from ..executors.executor_registry import ExecutorRegistry

logger = logging.getLogger(__name__)


@dataclass
class BOMEntry:
    """BOM 항목"""
    item_no: int
    part_no: str
    part_name: str
    material: str
    quantity: int
    dimensions: Optional[Dict[str, Any]] = None
    tolerances: Optional[List[str]] = None
    match_confidence: float = 1.0
    source: str = "partslist"


@dataclass
class DrawingInfo:
    """도면 메타 정보"""
    drawing_number: str
    revision: str
    title: str
    base_material: Optional[str] = None
    date: Optional[str] = None
    scale: Optional[str] = None


class BOMMatcher(BaseNodeExecutor):
    """BOM Matcher 실행기"""

    # 재질 정규화 매핑 (PartsListExecutor와 동일)
    MATERIAL_NORMALIZATION = {
        "SF440": "SF440A",
        "SF-440A": "SF440A",
        "SF 440A": "SF440A",
        "SS-400": "SS400",
        "SS 400": "SS400",
        "SM-490A": "SM490A",
        "SM490": "SM490A",
        "B23": "ASTM B23 GR.2",
        "ASTM B23": "ASTM B23 GR.2",
        "BABBITT": "ASTM B23 GR.2",
        "SUS-304": "SUS304",
        "SUS 304": "SUS304",
        "SCM-440": "SCM440",
        "SCM 440": "SCM440",
    }

    def _normalize_material(self, material: str) -> str:
        """재질 코드 정규화"""
        if not material:
            return material

        upper = material.upper().strip()

        # 정규화 매핑 확인
        for key, normalized in self.MATERIAL_NORMALIZATION.items():
            if key.upper() == upper or key.upper() in upper:
                return normalized

        return upper

    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """두 문자열의 유사도 계산 (0-1)"""
        if not s1 or not s2:
            return 0.0
        return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()

    def _extract_titleblock_data(self, inputs: Dict[str, Any]) -> DrawingInfo:
        """Title Block 데이터 추출"""
        titleblock = inputs.get("titleblock_data") or inputs.get("title_block", {})

        if isinstance(titleblock, dict):
            return DrawingInfo(
                drawing_number=titleblock.get("drawing_number", ""),
                revision=titleblock.get("revision", titleblock.get("rev", "")),
                title=titleblock.get("title", titleblock.get("part_name", "")),
                base_material=titleblock.get("material", ""),
                date=titleblock.get("date", ""),
                scale=titleblock.get("scale", ""),
            )

        return DrawingInfo(
            drawing_number="",
            revision="",
            title="",
        )

    def _extract_partslist_data(self, inputs: Dict[str, Any]) -> List[Dict]:
        """Parts List 데이터 추출"""
        partslist = inputs.get("partslist_data") or inputs.get("parts_list", {})

        if isinstance(partslist, dict):
            return partslist.get("parts", [])
        elif isinstance(partslist, list):
            return partslist

        # parts 키로 직접 접근
        parts = inputs.get("parts", [])
        if parts:
            return parts

        return []

    def _extract_dimension_data(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Dimension 데이터 추출"""
        dimension = inputs.get("dimension_data") or inputs.get("bearing_specs", {})

        if isinstance(dimension, dict):
            return dimension

        return {}

    def _match_strict(
        self,
        parts: List[Dict],
        dimensions: Dict[str, Any],
        validate_material: bool
    ) -> List[BOMEntry]:
        """정확 일치 매칭"""
        bom_entries = []

        for idx, part in enumerate(parts):
            part_no = str(part.get("no", part.get("part_no", idx + 1)))
            part_name = part.get("part_name", part.get("name", ""))
            material = part.get("material", "")
            quantity = part.get("quantity", 1)

            # 재질 정규화
            if validate_material:
                material = self._normalize_material(material)

            # 치수 매칭 (있는 경우)
            part_dimensions = None
            if dimensions:
                part_dimensions = {
                    "od": dimensions.get("outer_diameter"),
                    "id": dimensions.get("inner_diameter"),
                    "length": dimensions.get("length"),
                }

            entry = BOMEntry(
                item_no=idx + 1,
                part_no=part_no,
                part_name=part_name,
                material=material,
                quantity=quantity if isinstance(quantity, int) else 1,
                dimensions=part_dimensions,
                match_confidence=1.0,
                source="partslist",
            )
            bom_entries.append(entry)

        return bom_entries

    def _match_fuzzy(
        self,
        parts: List[Dict],
        dimensions: Dict[str, Any],
        yolo_detections: List[Dict],
        confidence_threshold: float
    ) -> List[BOMEntry]:
        """유사도 기반 매칭"""
        bom_entries = []

        for idx, part in enumerate(parts):
            part_no = str(part.get("no", part.get("part_no", idx + 1)))
            part_name = part.get("part_name", part.get("name", ""))
            material = self._normalize_material(part.get("material", ""))
            quantity = part.get("quantity", 1)

            # YOLO 검출과 매칭 시도
            best_match = None
            best_score = 0

            for detection in yolo_detections:
                label = detection.get("label", detection.get("class", ""))
                similarity = self._calculate_similarity(part_name, label)
                if similarity > best_score and similarity >= confidence_threshold:
                    best_score = similarity
                    best_match = detection

            # 치수 매칭
            part_dimensions = None
            if dimensions:
                part_dimensions = {
                    "od": dimensions.get("outer_diameter"),
                    "id": dimensions.get("inner_diameter"),
                    "length": dimensions.get("length"),
                }

            entry = BOMEntry(
                item_no=idx + 1,
                part_no=part_no,
                part_name=part_name,
                material=material,
                quantity=quantity if isinstance(quantity, int) else 1,
                dimensions=part_dimensions,
                match_confidence=best_score if best_match else 0.8,
                source="fuzzy_match" if best_match else "partslist",
            )
            bom_entries.append(entry)

        return bom_entries

    def _match_hybrid(
        self,
        parts: List[Dict],
        dimensions: Dict[str, Any],
        yolo_detections: List[Dict],
        validate_material: bool,
        confidence_threshold: float
    ) -> List[BOMEntry]:
        """하이브리드 매칭 (정확 일치 우선)"""
        # 먼저 정확 일치 시도
        strict_results = self._match_strict(parts, dimensions, validate_material)

        # 낮은 신뢰도 항목에 대해 fuzzy 매칭 보강
        if yolo_detections:
            for entry in strict_results:
                best_match = None
                best_score = 0

                for detection in yolo_detections:
                    label = detection.get("label", detection.get("class", ""))
                    similarity = self._calculate_similarity(entry.part_name, label)
                    if similarity > best_score:
                        best_score = similarity
                        best_match = detection

                if best_match and best_score >= confidence_threshold:
                    entry.match_confidence = max(entry.match_confidence, best_score)
                    entry.source = "hybrid_match"

        return strict_results

    def _validate_bom(
        self,
        bom_entries: List[BOMEntry],
        drawing_info: DrawingInfo
    ) -> tuple[List[str], List[str]]:
        """BOM 유효성 검사"""
        warnings = []
        unmatched = []

        # 재질 검증
        for entry in bom_entries:
            if not entry.material:
                warnings.append(f"항목 {entry.item_no}: 재질 정보 없음")
            if not entry.part_name:
                warnings.append(f"항목 {entry.item_no}: 품명 정보 없음")
            if entry.match_confidence < 0.5:
                unmatched.append(f"{entry.part_no}: {entry.part_name}")

        # 도면 정보 검증
        if not drawing_info.drawing_number:
            warnings.append("도면번호 정보 없음")
        if not drawing_info.revision:
            warnings.append("리비전 정보 없음")

        return warnings, unmatched

    def _calculate_overall_confidence(self, bom_entries: List[BOMEntry]) -> float:
        """전체 매칭 신뢰도 계산"""
        if not bom_entries:
            return 0.0

        confidences = [entry.match_confidence for entry in bom_entries]
        return sum(confidences) / len(confidences)

    def _generate_quote(
        self,
        bom_entries: List[BOMEntry],
        customer_id: Optional[str] = None,
        material_markup: float = 1.3,
        labor_markup: float = 1.5
    ) -> Dict[str, Any]:
        """
        BOM 기반 견적 생성

        Args:
            bom_entries: BOM 항목 목록
            customer_id: 고객 ID (할인 적용)
            material_markup: 재질 마크업
            labor_markup: 가공비 마크업

        Returns:
            견적 데이터
        """
        try:
            from services.price_database import get_price_database

            price_db = get_price_database()

            # BOM 항목을 price_database 형식으로 변환
            parts_for_quote = []
            for entry in bom_entries:
                part = {
                    "no": entry.part_no,
                    "description": entry.part_name,
                    "material": entry.material,
                    "qty": entry.quantity,
                    "weight": 1.0,  # 기본값
                }

                # 치수 데이터가 있으면 무게 추정
                if entry.dimensions:
                    od = entry.dimensions.get("od")
                    id_ = entry.dimensions.get("id")
                    length = entry.dimensions.get("length")

                    if od and id_ and length:
                        # 중공 원통 무게 계산 (밀도 7.85 kg/dm³)
                        import math
                        volume = (math.pi / 4) * ((od/10)**2 - (id_/10)**2) * (length/10)  # cm³
                        weight = volume * 7.85 / 1000  # kg
                        part["weight"] = round(weight, 2)

                parts_for_quote.append(part)

            # 견적 계산
            quote = price_db.calculate_quote(
                parts=parts_for_quote,
                customer_id=customer_id,
                material_markup=material_markup,
                labor_markup=labor_markup
            )

            return {
                "success": True,
                "quote": quote,
            }

        except Exception as e:
            logger.error(f"견적 생성 오류: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        BOM Matcher 실행

        Parameters:
            - titleblock_data: Title Block Parser 출력
            - partslist_data: Parts List Parser 출력
            - dimension_data: Dimension Parser 출력
            - yolo_detections: YOLO 검출 결과 (선택)
            - match_strategy: 매칭 전략 (strict/fuzzy/hybrid)
            - confidence_threshold: 최소 신뢰도
            - include_dimensions: 치수 포함 여부
            - include_tolerances: 공차 포함 여부
            - validate_material: 재질 검증 여부
            - generate_quote: 견적 생성 여부
            - customer_id: 고객 ID (할인 적용)
            - material_markup: 재질 마크업 (기본 1.3)
            - labor_markup: 가공비 마크업 (기본 1.5)

        Returns:
            - bom: 통합 BOM 목록
            - drawing_info: 도면 메타 정보
            - match_confidence: 전체 매칭 신뢰도
            - unmatched_items: 미매칭 항목
            - warnings: 경고 목록
            - quote: 견적 데이터 (generate_quote=True 시)
        """
        # 파라미터 추출
        match_strategy = self.parameters.get("match_strategy", "hybrid")
        confidence_threshold = self.parameters.get("confidence_threshold", 0.7)
        include_dimensions = self.parameters.get("include_dimensions", True)
        include_tolerances = self.parameters.get("include_tolerances", True)
        validate_material = self.parameters.get("validate_material", True)
        # 견적 생성 파라미터
        generate_quote = self.parameters.get("generate_quote", False)
        customer_id = self.parameters.get("customer_id")
        material_markup = self.parameters.get("material_markup", 1.3)
        labor_markup = self.parameters.get("labor_markup", 1.5)

        # 입력 데이터 추출
        drawing_info = self._extract_titleblock_data(inputs)
        parts = self._extract_partslist_data(inputs)
        dimensions = self._extract_dimension_data(inputs) if include_dimensions else {}
        yolo_detections = inputs.get("yolo_detections") or inputs.get("detections", [])
        tolerances = inputs.get("tolerances", [])

        # 입력 검증
        if not parts:
            return {
                "bom": [],
                "drawing_info": asdict(drawing_info),
                "match_confidence": 0.0,
                "unmatched_items": [],
                "warnings": ["Parts List 데이터가 없습니다"],
                "error": "No parts list data provided",
                # 원본 데이터 패스스루
                "image": inputs.get("image", ""),
            }

        # 매칭 실행
        if match_strategy == "strict":
            bom_entries = self._match_strict(parts, dimensions, validate_material)
        elif match_strategy == "fuzzy":
            bom_entries = self._match_fuzzy(
                parts, dimensions, yolo_detections, confidence_threshold
            )
        else:  # hybrid
            bom_entries = self._match_hybrid(
                parts, dimensions, yolo_detections,
                validate_material, confidence_threshold
            )

        # 공차 추가
        if include_tolerances and tolerances:
            for entry in bom_entries:
                entry.tolerances = [str(t) for t in tolerances[:3]]

        # 유효성 검사
        warnings, unmatched = self._validate_bom(bom_entries, drawing_info)

        # 전체 신뢰도 계산
        overall_confidence = self._calculate_overall_confidence(bom_entries)

        # 출력 형식 변환
        bom_list = [asdict(entry) for entry in bom_entries]

        # 견적 생성 (옵션)
        quote_data = None
        if generate_quote and bom_entries:
            logger.info(f"견적 생성 시작: {len(bom_entries)}개 항목, 고객: {customer_id}")
            quote_result = self._generate_quote(
                bom_entries=bom_entries,
                customer_id=customer_id,
                material_markup=material_markup,
                labor_markup=labor_markup
            )
            if quote_result.get("success"):
                quote_data = quote_result.get("quote")
                logger.info(f"견적 생성 완료: 총액 {quote_data.get('total', 0):,} {quote_data.get('currency', 'KRW')}")
            else:
                warnings.append(f"견적 생성 실패: {quote_result.get('error')}")

        output = {
            "bom": bom_list,
            "drawing_info": asdict(drawing_info),
            "match_confidence": overall_confidence,
            "unmatched_items": unmatched,
            "warnings": warnings,
            "bom_count": len(bom_entries),
            "match_strategy": match_strategy,
            # 견적 데이터
            "quote": quote_data,
            "generate_quote": generate_quote,
            # 원본 이미지 패스스루
            "image": inputs.get("image", ""),
            # 이전 노드 결과 패스스루
            "parts_count": len(parts),
            "has_dimensions": bool(dimensions),
        }

        return output

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        # match_strategy 검증
        if "match_strategy" in self.parameters:
            strategy = self.parameters["match_strategy"]
            if strategy not in ["strict", "fuzzy", "hybrid"]:
                return False, "match_strategy는 'strict', 'fuzzy', 'hybrid' 중 하나여야 합니다"

        # confidence_threshold 검증
        if "confidence_threshold" in self.parameters:
            threshold = self.parameters["confidence_threshold"]
            if not (0 <= threshold <= 1):
                return False, "confidence_threshold는 0과 1 사이여야 합니다"

        return True, None

    def get_input_schema(self) -> Dict[str, Any]:
        """입력 스키마"""
        return {
            "type": "object",
            "properties": {
                "titleblock_data": {
                    "type": "object",
                    "description": "Title Block Parser 출력"
                },
                "partslist_data": {
                    "type": "array",
                    "description": "Parts List Parser 출력"
                },
                "dimension_data": {
                    "type": "object",
                    "description": "Dimension Parser 출력"
                },
                "yolo_detections": {
                    "type": "array",
                    "description": "YOLO 검출 결과 (선택)"
                }
            },
            "required": []
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """출력 스키마"""
        return {
            "type": "object",
            "properties": {
                "bom": {
                    "type": "array",
                    "description": "통합 BOM 목록"
                },
                "drawing_info": {
                    "type": "object",
                    "description": "도면 메타 정보"
                },
                "match_confidence": {
                    "type": "number",
                    "description": "매칭 신뢰도 (0-1)"
                },
                "unmatched_items": {
                    "type": "array",
                    "description": "미매칭 항목"
                },
                "warnings": {
                    "type": "array",
                    "description": "경고 목록"
                }
            }
        }


# 실행기 등록
ExecutorRegistry.register("bommatcher", BOMMatcher)
ExecutorRegistry.register("bom_matcher", BOMMatcher)
ExecutorRegistry.register("bearing_bom", BOMMatcher)
