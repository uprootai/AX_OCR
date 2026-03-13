"""
Dimension Parser — 실행기 클래스
DimensionParserExecutor: 베어링 도면 치수를 구조화된 형태로 파싱
"""
from typing import Dict, Any, Optional, List
import re

from ..base_executor import BaseNodeExecutor
from ..executor_registry import ExecutorRegistry
from .models import BearingDimension, BearingSpec
from .patterns import DIMENSION_PATTERNS, GDT_PATTERNS


class DimensionParserExecutor(BaseNodeExecutor):
    """Dimension Parser 실행기"""

    # 클래스 수준에서 패턴 참조
    DIMENSION_PATTERNS = DIMENSION_PATTERNS
    GDT_PATTERNS = GDT_PATTERNS

    def _parse_dimension(self, text: str) -> Optional[BearingDimension]:
        """단일 치수 텍스트 파싱"""
        text = text.strip()
        if not text:
            return None

        for pattern, pattern_name, extractor in self.DIMENSION_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    data = extractor(match)
                    return BearingDimension(raw_text=text, **data)
                except (ValueError, IndexError):
                    continue

        # 패턴 매칭 실패 시 숫자만 추출
        numbers = re.findall(r"\d+\.?\d*", text)
        if numbers:
            return BearingDimension(
                raw_text=text,
                value=float(numbers[0]),
                dimension_type="unknown",
                confidence=0.5
            )

        return None

    def _extract_gdt_symbols(self, text: str) -> List[Dict[str, str]]:
        """GD&T 기호 추출"""
        symbols = []
        for pattern, symbol_type, korean_name in self.GDT_PATTERNS:
            if re.search(pattern, text):
                symbols.append({
                    "symbol": re.search(pattern, text).group(0),
                    "type": symbol_type,
                    "name": korean_name
                })
        return symbols

    def _extract_tolerances(self, dimensions: List[BearingDimension]) -> List[Dict[str, Any]]:
        """공차 목록 추출"""
        tolerances = []
        for dim in dimensions:
            if dim.tolerance:
                tol_type = "fit" if dim.fit_class else "dimensional"
                tolerances.append({
                    "value": dim.tolerance,
                    "type": tol_type,
                    "upper": dim.tolerance_upper,
                    "lower": dim.tolerance_lower,
                })
            if dim.fit_class and not dim.tolerance:
                tolerances.append({
                    "value": dim.fit_class,
                    "type": "fit",
                })
        return tolerances

    def _calculate_bearing_specs(self, dimensions: List[BearingDimension]) -> BearingSpec:
        """종합 베어링 사양 계산"""
        spec = BearingSpec()

        for dim in dimensions:
            if dim.outer_diameter and not spec.outer_diameter:
                spec.outer_diameter = dim.outer_diameter
            if dim.inner_diameter and not spec.inner_diameter:
                spec.inner_diameter = dim.inner_diameter
            if dim.length and not spec.length:
                spec.length = dim.length
            if dim.width and not spec.width:
                spec.width = dim.width
            if dim.diameter and dim.dimension_type == "bore" and not spec.bore_diameter:
                spec.bore_diameter = dim.diameter

        return spec

    def _calculate_confidence(self, dimensions: List[BearingDimension]) -> float:
        """전체 파싱 신뢰도 계산"""
        if not dimensions:
            return 0.0

        total_confidence = sum(dim.confidence for dim in dimensions)
        avg_confidence = total_confidence / len(dimensions)

        # 베어링 관련 치수가 있으면 보너스
        bearing_dims = [d for d in dimensions if d.dimension_type == "bearing"]
        if bearing_dims:
            avg_confidence = min(1.0, avg_confidence + 0.1)

        return avg_confidence

    def _collect_dimension_texts(self, inputs: Dict[str, Any]) -> List[str]:
        """입력에서 치수 텍스트 수집"""
        dimension_texts: List[str] = []

        def to_string(value: Any) -> str:
            if isinstance(value, str):
                return value
            elif isinstance(value, dict):
                return str(value.get("text", value.get("value", "")))
            elif isinstance(value, (int, float)):
                return str(value)
            elif value is None:
                return ""
            else:
                return str(value)

        # 1. 직접 입력된 치수
        direct_dims = inputs.get("dimensions", [])
        if direct_dims:
            if isinstance(direct_dims, list):
                for d in direct_dims:
                    text = to_string(d)
                    if text:
                        dimension_texts.append(text)
            elif isinstance(direct_dims, str):
                dimension_texts.append(direct_dims)

        # 2. eDOCr2/OCR 결과에서 추출
        text_results = inputs.get("text_results", [])
        if text_results:
            if isinstance(text_results, list):
                for result in text_results:
                    text = to_string(result)
                    if text:
                        dimension_texts.append(text)
            elif isinstance(text_results, dict):
                for key in ["text", "texts", "results", "data"]:
                    if key in text_results:
                        val = text_results[key]
                        if isinstance(val, list):
                            for item in val:
                                text = to_string(item)
                                if text:
                                    dimension_texts.append(text)
                        elif isinstance(val, str):
                            dimension_texts.append(val)
                        break
            elif isinstance(text_results, str):
                dimension_texts.append(text_results)

        # 3. raw OCR 텍스트에서 추출 (숫자 포함된 것만)
        raw_text = inputs.get("raw_text", "")
        if isinstance(raw_text, dict):
            raw_text = to_string(raw_text)
        elif not isinstance(raw_text, str):
            raw_text = str(raw_text) if raw_text else ""

        if raw_text:
            potential_dims = re.findall(
                r"(?:OD|ID|[ØφΦ⌀]|R|C)?\s*\d+\.?\d*(?:\s*[×xX±]\s*\d+\.?\d*)*(?:\s*[A-Z]\d+)?",
                raw_text
            )
            dimension_texts.extend(potential_dims)

        return dimension_texts

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dimension Parser 실행

        Parameters:
            - text_results: eDOCr2 OCR 결과 (텍스트 + bbox)
            - dimensions: 치수 텍스트 목록 (직접 입력)
            - dimension_type: 치수 유형
            - parse_tolerance: 공차 파싱 여부
            - parse_gdt: GD&T 파싱 여부
            - extract_od_id: OD/ID 분류 여부

        Returns:
            - parsed_dimensions: 구조화된 베어링 치수 목록
            - bearing_specs: 종합 베어링 사양
            - tolerances: 공차 목록
            - gdt_symbols: GD&T 기호 목록
            - dimensions_count: 파싱된 치수 개수
            - confidence: 파싱 신뢰도
        """
        # 이전 노드 결과 패스스루
        passthrough_data = {
            "detections": inputs.get("detections", []),
            "title_block": inputs.get("title_block", {}),
            "parts_list": inputs.get("parts_list", {}),
        }

        # 파라미터 추출
        dimension_type = self.parameters.get("dimension_type", "bearing")
        parse_tolerance = self.parameters.get("parse_tolerance", True)
        parse_gdt = self.parameters.get("parse_gdt", True)
        unit = self.parameters.get("unit", "mm")

        # 치수 텍스트 수집
        dimension_texts = self._collect_dimension_texts(inputs)

        # 치수 파싱
        parsed_dimensions: List[BearingDimension] = []
        all_gdt_symbols: List[Dict[str, str]] = []

        for text in dimension_texts:
            if not isinstance(text, str):
                text = str(text) if text else ""
            text = text.strip()
            if not text or len(text) < 2:
                continue

            dim = self._parse_dimension(text)
            if dim:
                dim.unit = unit
                parsed_dimensions.append(dim)

            if parse_gdt:
                gdt = self._extract_gdt_symbols(text)
                all_gdt_symbols.extend(gdt)

        # 공차 추출
        tolerances = []
        if parse_tolerance:
            tolerances = self._extract_tolerances(parsed_dimensions)

        # 베어링 사양 계산
        bearing_specs = self._calculate_bearing_specs(parsed_dimensions)

        # 신뢰도 계산
        confidence = self._calculate_confidence(parsed_dimensions)

        # 중복 GD&T 제거
        seen_gdt = set()
        unique_gdt = []
        for g in all_gdt_symbols:
            key = (g["type"], g["symbol"])
            if key not in seen_gdt:
                seen_gdt.add(key)
                unique_gdt.append(g)

        output = {
            # 파싱 결과
            "parsed_dimensions": [d.to_dict() for d in parsed_dimensions],
            "bearing_specs": bearing_specs.to_dict(),
            "tolerances": tolerances,
            "gdt_symbols": unique_gdt,
            "dimensions_count": len(parsed_dimensions),
            "confidence": confidence,
            # 처리 정보
            "dimension_type": dimension_type,
            "unit": unit,
            "raw_count": len(dimension_texts),
            # 원본 이미지 패스스루
            "image": inputs.get("image", ""),
            # 이전 노드 결과 패스스루
            **passthrough_data,
        }

        return output

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        if "dimension_type" in self.parameters:
            dtype = self.parameters["dimension_type"]
            if dtype not in ["bearing", "general", "shaft", "housing"]:
                return False, "dimension_type은 'bearing', 'general', 'shaft', 'housing' 중 하나여야 합니다"

        if "unit" in self.parameters:
            unit = self.parameters["unit"]
            if unit not in ["mm", "inch", "auto"]:
                return False, "unit은 'mm', 'inch', 'auto' 중 하나여야 합니다"

        return True, None

    def get_input_schema(self) -> Dict[str, Any]:
        """입력 스키마"""
        return {
            "type": "object",
            "properties": {
                "text_results": {
                    "type": "array",
                    "description": "eDOCr2 OCR 결과"
                },
                "dimensions": {
                    "type": "array",
                    "description": "치수 텍스트 목록"
                }
            }
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """출력 스키마"""
        return {
            "type": "object",
            "properties": {
                "parsed_dimensions": {
                    "type": "array",
                    "description": "구조화된 치수 목록"
                },
                "bearing_specs": {
                    "type": "object",
                    "description": "종합 베어링 사양"
                },
                "tolerances": {
                    "type": "array",
                    "description": "공차 목록"
                },
                "confidence": {
                    "type": "number",
                    "description": "파싱 신뢰도"
                }
            }
        }


# 실행기 등록
ExecutorRegistry.register("dimensionparser", DimensionParserExecutor)
ExecutorRegistry.register("dimension_parser", DimensionParserExecutor)
ExecutorRegistry.register("bearing_dimension", DimensionParserExecutor)
