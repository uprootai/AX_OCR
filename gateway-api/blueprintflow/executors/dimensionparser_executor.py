"""
Dimension Parser Executor
베어링 도면 치수를 구조화된 형태로 파싱

지원 패턴:
- OD670×ID440 → {outer_diameter: 670, inner_diameter: 440}
- 1100×ID680×200L → {width: 1100, inner_diameter: 680, length: 200}
- Ø25H7 → {diameter: 25, tolerance: "H7"}
- 50.0±0.1 → {value: 50.0, tolerance: "±0.1"}
- ⌀25 → {diameter: 25, symbol: "⌀"}
"""
from typing import Dict, Any, Optional, List, Tuple, Callable
import re
from dataclasses import dataclass, asdict

from ..executors.base_executor import BaseNodeExecutor
from ..executors.executor_registry import ExecutorRegistry


@dataclass
class BearingDimension:
    """베어링 치수 데이터 클래스"""
    raw_text: str = ""
    dimension_type: str = "unknown"
    outer_diameter: Optional[float] = None
    inner_diameter: Optional[float] = None
    diameter: Optional[float] = None
    length: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    value: Optional[float] = None
    tolerance: Optional[str] = None
    tolerance_upper: Optional[float] = None
    tolerance_lower: Optional[float] = None
    fit_class: Optional[str] = None
    unit: str = "mm"
    confidence: float = 1.0
    bbox: Optional[List[float]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class BearingSpec:
    """종합 베어링 사양"""
    outer_diameter: Optional[float] = None
    inner_diameter: Optional[float] = None
    length: Optional[float] = None
    width: Optional[float] = None
    bore_diameter: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


class DimensionParserExecutor(BaseNodeExecutor):
    """Dimension Parser 실행기"""

    # 치수 패턴 정의 (순서 중요 - 더 구체적인 패턴 먼저)
    DIMENSION_PATTERNS: List[Tuple[str, str, Callable]] = [
        # OD670×ID440 (외경×내경)
        (
            r"OD\s*(\d+\.?\d*)\s*[×xX]\s*ID\s*(\d+\.?\d*)",
            "bearing_od_id",
            lambda m: {
                "outer_diameter": float(m.group(1)),
                "inner_diameter": float(m.group(2)),
                "dimension_type": "bearing"
            }
        ),
        # ID440×OD670 (내경×외경)
        (
            r"ID\s*(\d+\.?\d*)\s*[×xX]\s*OD\s*(\d+\.?\d*)",
            "bearing_id_od",
            lambda m: {
                "inner_diameter": float(m.group(1)),
                "outer_diameter": float(m.group(2)),
                "dimension_type": "bearing"
            }
        ),
        # 1100×ID680×200L (폭×내경×길이)
        (
            r"(\d+\.?\d*)\s*[×xX]\s*ID\s*(\d+\.?\d*)\s*[×xX]\s*(\d+\.?\d*)\s*L",
            "bearing_w_id_l",
            lambda m: {
                "width": float(m.group(1)),
                "inner_diameter": float(m.group(2)),
                "length": float(m.group(3)),
                "dimension_type": "bearing"
            }
        ),
        # OD670×200L (외경×길이)
        (
            r"OD\s*(\d+\.?\d*)\s*[×xX]\s*(\d+\.?\d*)\s*L",
            "bearing_od_l",
            lambda m: {
                "outer_diameter": float(m.group(1)),
                "length": float(m.group(2)),
                "dimension_type": "bearing"
            }
        ),
        # Ø25H7 또는 ⌀25H7 (직경 + 공차등급)
        (
            r"[ØφΦ⌀]\s*(\d+\.?\d*)\s*([A-Z][a-z]?\d+)?",
            "diameter_tolerance",
            lambda m: {
                "diameter": float(m.group(1)),
                "tolerance": m.group(2) if m.group(2) else None,
                "fit_class": m.group(2) if m.group(2) else None,
                "dimension_type": "diameter"
            }
        ),
        # 50.0±0.1 또는 50.0+0.1/-0.05 (양공차)
        (
            r"(\d+\.?\d*)\s*[±]\s*(\d+\.?\d*)",
            "symmetric_tolerance",
            lambda m: {
                "value": float(m.group(1)),
                "tolerance": f"±{m.group(2)}",
                "tolerance_upper": float(m.group(2)),
                "tolerance_lower": -float(m.group(2)),
                "dimension_type": "linear"
            }
        ),
        # 50.0 +0.1/-0.05 (비대칭 공차)
        (
            r"(\d+\.?\d*)\s*\+\s*(\d+\.?\d*)\s*/\s*-\s*(\d+\.?\d*)",
            "asymmetric_tolerance",
            lambda m: {
                "value": float(m.group(1)),
                "tolerance": f"+{m.group(2)}/-{m.group(3)}",
                "tolerance_upper": float(m.group(2)),
                "tolerance_lower": -float(m.group(3)),
                "dimension_type": "linear"
            }
        ),
        # H7, h6, g6 등 (공차 등급만)
        (
            r"\b([A-Z][a-z]?)(\d+)\b",
            "fit_class",
            lambda m: {
                "fit_class": f"{m.group(1)}{m.group(2)}",
                "tolerance": f"{m.group(1)}{m.group(2)}",
                "dimension_type": "fit"
            }
        ),
        # 360×190 (일반 치수)
        (
            r"(\d+\.?\d*)\s*[×xX]\s*(\d+\.?\d*)",
            "general_dimension",
            lambda m: {
                "width": float(m.group(1)),
                "height": float(m.group(2)),
                "dimension_type": "general"
            }
        ),
        # R25 (반지름)
        (
            r"R\s*(\d+\.?\d*)",
            "radius",
            lambda m: {
                "value": float(m.group(1)),
                "dimension_type": "radius"
            }
        ),
        # C2 또는 C2×45° (챔퍼)
        (
            r"C\s*(\d+\.?\d*)(?:\s*[×xX]\s*(\d+\.?\d*)\s*°)?",
            "chamfer",
            lambda m: {
                "value": float(m.group(1)),
                "dimension_type": "chamfer"
            }
        ),
    ]

    # GD&T 기호 패턴
    GDT_PATTERNS = [
        (r"[⌀ØφΦ]", "diameter", "직경"),
        (r"⊥", "perpendicularity", "직각도"),
        (r"//", "parallelism", "평행도"),
        (r"○", "circularity", "진원도"),
        (r"⌭", "cylindricity", "원통도"),
        (r"—", "flatness", "평면도"),
        (r"∠", "angularity", "경사도"),
        (r"↗", "position", "위치도"),
        (r"⊙", "concentricity", "동심도"),
        (r"⌓", "symmetry", "대칭도"),
        (r"↺", "runout", "흔들림"),
        (r"⌰", "total_runout", "총 흔들림"),
    ]

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
        dimension_texts: List[str] = []

        # 헬퍼: 입력을 문자열로 변환
        def to_string(value: Any) -> str:
            if isinstance(value, str):
                return value
            elif isinstance(value, dict):
                # dict에서 text 필드 추출 시도
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
                # dict 형태의 결과 처리
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
        # dict인 경우 문자열 변환
        if isinstance(raw_text, dict):
            raw_text = to_string(raw_text)
        elif not isinstance(raw_text, str):
            raw_text = str(raw_text) if raw_text else ""

        if raw_text:
            # 치수로 보이는 패턴 추출
            potential_dims = re.findall(
                r"(?:OD|ID|[ØφΦ⌀]|R|C)?\s*\d+\.?\d*(?:\s*[×xX±]\s*\d+\.?\d*)*(?:\s*[A-Z]\d+)?",
                raw_text
            )
            dimension_texts.extend(potential_dims)

        # 치수 파싱
        parsed_dimensions: List[BearingDimension] = []
        all_gdt_symbols: List[Dict[str, str]] = []

        for text in dimension_texts:
            # 안전한 문자열 변환
            if not isinstance(text, str):
                text = str(text) if text else ""
            text = text.strip()
            if not text or len(text) < 2:
                continue

            dim = self._parse_dimension(text)
            if dim:
                dim.unit = unit
                parsed_dimensions.append(dim)

            # GD&T 기호 추출
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
