"""
테크로스 (techcross) 도면 파서
도면 유형: pid — P&ID 공정배관계장도

생성일: 2026-03-12
"""

import logging
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# =====================
# 데이터 모델
# =====================

@dataclass
class TitleBlockData:
    """표제란 파싱 결과"""
    drawing_number: Optional[str] = None
    revision: Optional[str] = None
    part_name: Optional[str] = None
    material: Optional[str] = None
    drawn_by: Optional[str] = None
    drawn_date: Optional[str] = None
    approved_by: Optional[str] = None
    scale: Optional[str] = None
    sheet: Optional[str] = None
    raw_fields: Dict[str, str] = field(default_factory=dict)


@dataclass
class PartsListItem:
    """부품 목록 항목"""
    item_no: Optional[str] = None
    description: Optional[str] = None
    material: Optional[str] = None
    quantity: Optional[int] = None
    part_number: Optional[str] = None
    remarks: Optional[str] = None


# =====================
# 파싱 패턴 (고객별 커스터마이징)
# =====================

# @AX:ANCHOR — techcross 도면 번호 패턴
DRAWING_NUMBER_PATTERNS = [
    # TODO: 테크로스 도면 번호 패턴으로 교체
    r"[A-Z]{2}\d{5,8}",
    r"\d{4}-\d{4}",
]

REVISION_PATTERNS = [
    r"REV[.\s]*([A-Z])",
    r"Rev[.\s]*([A-Z0-9]+)",
    # TODO: 테크로스 리비전 패턴 추가
]

MATERIAL_PATTERNS = [
    r"S[A-Z]\d{2,3}[A-Z]?",
    r"ASTM\s*[AB]\d+",
    # TODO: 테크로스 자재 코드 패턴 추가
]


# =====================
# Title Block 파싱
# =====================

def parse_title_block(ocr_text: str, raw_texts: Optional[List[str]] = None) -> TitleBlockData:
    """표제란 파싱"""
    result = TitleBlockData()
    if not ocr_text:
        return result
    result.drawing_number = _extract_drawing_number(ocr_text)
    result.revision = _extract_revision(ocr_text)
    result.material = _extract_material(ocr_text)
    # TODO: 테크로스 특화 필드 추출 로직 구현
    return result


def _extract_drawing_number(text: str) -> Optional[str]:
    for pattern in DRAWING_NUMBER_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None


def _extract_revision(text: str) -> Optional[str]:
    for pattern in REVISION_PATTERNS:
        match = re.search(pattern, text)
        if match:
            groups = match.groups()
            return groups[0] if groups else match.group(0)
    return None


def _extract_material(text: str) -> Optional[str]:
    for pattern in MATERIAL_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None


# =====================
# Parts List 파싱
# =====================

def parse_parts_list(
    table_data: Optional[List[Dict[str, Any]]] = None,
    ocr_text: Optional[str] = None,
) -> List[PartsListItem]:
    """부품 목록 파싱"""
    if table_data:
        return _parse_from_table(table_data)
    if ocr_text:
        return _parse_from_ocr(ocr_text)
    return []


def _parse_from_table(table_data: List[Dict[str, Any]]) -> List[PartsListItem]:
    items = []
    for row in table_data:
        # TODO: 테크로스 테이블 컬럼 매핑으로 교체
        item = PartsListItem(
            item_no=row.get("NO") or row.get("ITEM") or row.get("no"),
            description=row.get("DESCRIPTION") or row.get("DESC") or row.get("description"),
            material=row.get("MATERIAL") or row.get("MAT") or row.get("material"),
            quantity=_safe_int(row.get("QTY") or row.get("qty") or row.get("QUANTITY")),
            part_number=row.get("PART_NO") or row.get("P/N") or row.get("part_no"),
        )
        items.append(item)
    return items


def _parse_from_ocr(ocr_text: str) -> List[PartsListItem]:
    # TODO: 테크로스 OCR 폴백 파싱 구현
    logger.warning("OCR fallback parsing not yet implemented for techcross")
    return []


def _safe_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(str(value).strip())
    except (ValueError, TypeError):
        return None


# =====================
# Dimensions 파싱
# =====================

def extract_dimensions(ocr_text: str) -> List[Dict[str, Any]]:
    """치수 정보 추출"""
    dimensions = []
    mm_pattern = r"(\d+(?:\.\d+)?)\s*(?:mm|MM)"
    for match in re.finditer(mm_pattern, ocr_text):
        dimensions.append({
            "value": float(match.group(1)),
            "unit": "mm",
            "tolerance": None,
            "type": "linear",
            "raw": match.group(0),
        })
    tolerance_pattern = r"(\d+(?:\.\d+)?)\s*([+-]\d+(?:\.\d+)?)"
    for match in re.finditer(tolerance_pattern, ocr_text):
        dimensions.append({
            "value": float(match.group(1)),
            "unit": "mm",
            "tolerance": match.group(2),
            "type": "toleranced",
            "raw": match.group(0),
        })
    # TODO: 테크로스 특화 치수 패턴 추가
    return dimensions


# =====================
# 메인 파서 클래스
# =====================

class TechcrossParser:
    """
    테크로스 도면 파서
    도면 유형: pid
    """
    DRAWING_TYPE = "pid"
    CUSTOMER_ID = "techcross"
    CUSTOMER_NAME = "테크로스"

    def __init__(self):
        logger.info(f"Initializing {self.CUSTOMER_NAME} parser (type: {self.DRAWING_TYPE})")

    def parse_title_block(self, ocr_text: str, raw_texts=None) -> Dict[str, Any]:
        result = parse_title_block(ocr_text, raw_texts)
        return {
            "drawing_number": result.drawing_number,
            "revision": result.revision,
            "part_name": result.part_name,
            "material": result.material,
            "drawn_by": result.drawn_by,
            "drawn_date": result.drawn_date,
            "approved_by": result.approved_by,
            "scale": result.scale,
            "sheet": result.sheet,
        }

    def parse_parts_list(self, table_data=None, ocr_text=None) -> List[Dict[str, Any]]:
        items = parse_parts_list(table_data, ocr_text)
        return [
            {
                "item_no": i.item_no,
                "description": i.description,
                "material": i.material,
                "quantity": i.quantity,
                "part_number": i.part_number,
                "remarks": i.remarks,
            }
            for i in items
        ]

    def extract_dimensions(self, ocr_text: str) -> List[Dict[str, Any]]:
        return extract_dimensions(ocr_text)


_parser_instance = None


def get_parser() -> TechcrossParser:
    """파서 인스턴스 반환 (싱글톤)"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = TechcrossParser()
    return _parser_instance
