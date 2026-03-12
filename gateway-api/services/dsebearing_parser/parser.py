"""
DSE Bearing Parser — Main Parser Class

DSEBearingParser: 개별 파서 함수들을 하나의 클래스 인터페이스로 묶는다.
기존 코드 호환성 유지를 위해 메서드 위임 방식 사용.
"""

import logging
from typing import Dict, Any, List, Optional

from .models import TitleBlockData, PartsListItem
from .constants import ISO_TOLERANCE_GRADES, SURFACE_ROUGHNESS
from .title_block import (
    parse_title_block,
    _extract_drawing_number,
    _extract_revision,
    _extract_part_name,
    _normalize_ocr_text,
    _extract_material,
    _extract_date,
    _extract_misc_info,
)
from .parts_list import parse_parts_list, _normalize_table_data, _parse_from_table, _parse_from_ocr
from .dimensions import extract_dimensions, _parse_dimension_match, _get_fit_type

logger = logging.getLogger(__name__)


class DSEBearingParser:
    """DSE Bearing 도면 파서"""

    # 클래스 수준 상수 (기존 코드 호환)
    DRAWING_NUMBER_PATTERNS = [
        r"TD\d{7}",
        r"TD\d{6}",
        r"[A-Z]{2}\d{5,8}",
    ]
    REVISION_PATTERNS = [
        r"REV[.\s]*([A-Z])",
        r"Rev[.\s]*([A-Z])",
        r"\bR([A-Z])\b",
        r"[Rr]evision[:\s]*([A-Z])",
    ]
    MATERIAL_PATTERNS = [
        r"SF\d{2,3}[A-Z]?",
        r"SM\d{3}[A-Z]?",
        r"S45C[-N]?",
        r"SS\d{3}",
        r"STS\d{3}",
        r"SCM\d{3}",
        r"ASTM\s*[AB]\d+",
        r"ASTM\s*B23\s*GR[.\s]*\d",
    ]
    PART_NAME_KEYWORDS = [
        "BEARING", "RING", "CASING", "PAD", "ASSY", "ASSEMBLY",
        "UPPER", "LOWER", "THRUST", "SHIM", "PLATE", "BOLT",
        "PIN", "NUT", "WASHER", "WEDGE", "BUSHING", "LINER",
    ]
    DATE_PATTERNS = [
        r"\d{4}[./]\d{2}[./]\d{2}",
        r"\d{2}[./]\d{2}[./]\d{4}",
        r"\d{4}-\d{2}-\d{2}",
    ]
    ISO_TOLERANCE_GRADES = ISO_TOLERANCE_GRADES
    SURFACE_ROUGHNESS = SURFACE_ROUGHNESS

    # --- Title Block ---

    def parse_title_block(self, ocr_texts: List[Dict[str, Any]]) -> TitleBlockData:
        return parse_title_block(ocr_texts)

    def _extract_drawing_number(self, texts: List[str], combined: str) -> str:
        return _extract_drawing_number(texts, combined)

    def _extract_revision(self, texts: List[str], combined: str) -> str:
        return _extract_revision(texts, combined)

    def _extract_part_name(self, texts: List[str], combined: str) -> str:
        return _extract_part_name(texts, combined)

    def _normalize_ocr_text(self, text: str) -> str:
        return _normalize_ocr_text(text)

    def _extract_material(self, texts: List[str], combined: str) -> str:
        return _extract_material(texts, combined)

    def _extract_date(self, texts: List[str], combined: str) -> str:
        return _extract_date(texts, combined)

    def _extract_misc_info(self, result: TitleBlockData, texts: List[str], combined: str):
        return _extract_misc_info(result, texts, combined)

    # --- Parts List ---

    def parse_parts_list(
        self,
        ocr_texts: List[Dict[str, Any]],
        table_data: Optional[List[List[str]]] = None,
    ) -> List[PartsListItem]:
        return parse_parts_list(ocr_texts, table_data)

    def _normalize_table_data(self, table_data: List) -> List[List[str]]:
        return _normalize_table_data(table_data)

    def _parse_from_table(self, table_data: List) -> List[PartsListItem]:
        return _parse_from_table(table_data)

    def _parse_from_ocr(self, ocr_texts: List[Dict[str, Any]]) -> List[PartsListItem]:
        return _parse_from_ocr(ocr_texts)

    # --- Dimensions ---

    def extract_dimensions(self, ocr_texts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return extract_dimensions(ocr_texts)

    def _parse_dimension_match(
        self,
        match,
        dim_type: str,
        raw_text: str,
        bbox: List,
        confidence: float,
    ) -> Optional[Dict[str, Any]]:
        return _parse_dimension_match(match, dim_type, raw_text, bbox, confidence)

    def _get_fit_type(self, grade_letter: str) -> str:
        return _get_fit_type(grade_letter)
