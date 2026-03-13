"""
BOM Matcher — 실행기
BOMMatcher 클래스: execute, validate_parameters, 입출력 스키마, 레지스트리 등록
"""
from typing import Dict, Any, Optional, List
from dataclasses import asdict
import logging
import math

from ...executors.base_executor import BaseNodeExecutor
from ...executors.executor_registry import ExecutorRegistry

from .models import BOMEntry, DrawingInfo
from .matchers import (
    extract_titleblock_data,
    extract_partslist_data,
    extract_dimension_data,
    match_strict,
    match_fuzzy,
    match_hybrid,
    validate_bom,
    calculate_overall_confidence,
    MATERIAL_NORMALIZATION,
    normalize_material,
    calculate_similarity,
)

logger = logging.getLogger(__name__)


def _generate_quote(
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
                    volume = (math.pi / 4) * ((od/10)**2 - (id_/10)**2) * (length/10)  # cm³
                    weight = volume * 7.85 / 1000  # kg
                    part["weight"] = round(weight, 2)

            parts_for_quote.append(part)

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


class BOMMatcher(BaseNodeExecutor):
    """BOM Matcher 실행기"""

    # 재질 정규화 매핑 (PartsListExecutor와 동일, 하위 호환)
    MATERIAL_NORMALIZATION = MATERIAL_NORMALIZATION

    # 하위 호환 메서드 — 모듈 함수를 인스턴스 메서드로 위임
    def _normalize_material(self, material: str) -> str:
        return normalize_material(material)

    def _calculate_similarity(self, s1: str, s2: str) -> float:
        return calculate_similarity(s1, s2)

    def _extract_titleblock_data(self, inputs: Dict[str, Any]) -> DrawingInfo:
        return extract_titleblock_data(inputs)

    def _extract_partslist_data(self, inputs: Dict[str, Any]) -> List[Dict]:
        return extract_partslist_data(inputs)

    def _extract_dimension_data(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        return extract_dimension_data(inputs)

    def _match_strict(self, parts, dimensions, validate_material):
        return match_strict(parts, dimensions, validate_material)

    def _match_fuzzy(self, parts, dimensions, yolo_detections, confidence_threshold):
        return match_fuzzy(parts, dimensions, yolo_detections, confidence_threshold)

    def _match_hybrid(self, parts, dimensions, yolo_detections, validate_material, confidence_threshold):
        return match_hybrid(parts, dimensions, yolo_detections, validate_material, confidence_threshold)

    def _validate_bom(self, bom_entries, drawing_info):
        return validate_bom(bom_entries, drawing_info)

    def _calculate_overall_confidence(self, bom_entries):
        return calculate_overall_confidence(bom_entries)

    def _generate_quote(self, bom_entries, customer_id=None, material_markup=1.3, labor_markup=1.5):
        return _generate_quote(bom_entries, customer_id, material_markup, labor_markup)

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
        match_strategy = self.parameters.get("match_strategy", "hybrid")
        confidence_threshold = self.parameters.get("confidence_threshold", 0.7)
        include_dimensions = self.parameters.get("include_dimensions", True)
        include_tolerances = self.parameters.get("include_tolerances", True)
        validate_material = self.parameters.get("validate_material", True)
        generate_quote = self.parameters.get("generate_quote", False)
        customer_id = self.parameters.get("customer_id")
        material_markup = self.parameters.get("material_markup", 1.3)
        labor_markup = self.parameters.get("labor_markup", 1.5)

        drawing_info = extract_titleblock_data(inputs)
        parts = extract_partslist_data(inputs)
        dimensions = extract_dimension_data(inputs) if include_dimensions else {}
        yolo_detections = inputs.get("yolo_detections") or inputs.get("detections", [])
        tolerances = inputs.get("tolerances", [])

        if not parts:
            return {
                "bom": [],
                "drawing_info": asdict(drawing_info),
                "match_confidence": 0.0,
                "unmatched_items": [],
                "warnings": ["Parts List 데이터가 없습니다"],
                "error": "No parts list data provided",
                "image": inputs.get("image", ""),
            }

        if match_strategy == "strict":
            bom_entries = match_strict(parts, dimensions, validate_material)
        elif match_strategy == "fuzzy":
            bom_entries = match_fuzzy(parts, dimensions, yolo_detections, confidence_threshold)
        else:  # hybrid
            bom_entries = match_hybrid(
                parts, dimensions, yolo_detections,
                validate_material, confidence_threshold
            )

        if include_tolerances and tolerances:
            for entry in bom_entries:
                entry.tolerances = [str(t) for t in tolerances[:3]]

        warnings, unmatched = validate_bom(bom_entries, drawing_info)
        overall_confidence = calculate_overall_confidence(bom_entries)
        bom_list = [asdict(entry) for entry in bom_entries]

        quote_data = None
        if generate_quote and bom_entries:
            logger.info(f"견적 생성 시작: {len(bom_entries)}개 항목, 고객: {customer_id}")
            quote_result = _generate_quote(
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

        return {
            "bom": bom_list,
            "drawing_info": asdict(drawing_info),
            "match_confidence": overall_confidence,
            "unmatched_items": unmatched,
            "warnings": warnings,
            "bom_count": len(bom_entries),
            "match_strategy": match_strategy,
            "quote": quote_data,
            "generate_quote": generate_quote,
            "image": inputs.get("image", ""),
            "parts_count": len(parts),
            "has_dimensions": bool(dimensions),
        }

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        if "match_strategy" in self.parameters:
            strategy = self.parameters["match_strategy"]
            if strategy not in ["strict", "fuzzy", "hybrid"]:
                return False, "match_strategy는 'strict', 'fuzzy', 'hybrid' 중 하나여야 합니다"

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
