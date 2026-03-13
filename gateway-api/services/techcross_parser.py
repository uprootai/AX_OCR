"""
테크로스 (techcross) P&ID 도면 파서
도면 유형: P&ID (BWMS/ECS 선박 설비)

장비 태그, 밸브 신호, Equipment List 매칭 전용.
생성일: 2026-03-12, 업데이트: 2026-03-13
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
    """P&ID 표제란 파싱 결과"""
    drawing_number: Optional[str] = None
    revision: Optional[str] = None
    title: Optional[str] = None
    system: Optional[str] = None  # BWMS, ECS, HYCHLOR
    ship_no: Optional[str] = None
    class_society: Optional[str] = None  # 선급 (DNV, LR, BV 등)
    drawn_by: Optional[str] = None
    drawn_date: Optional[str] = None
    approved_by: Optional[str] = None
    scale: Optional[str] = None
    sheet: Optional[str] = None
    raw_fields: Dict[str, str] = field(default_factory=dict)


@dataclass
class EquipmentTag:
    """P&ID 장비 태그"""
    tag_id: str           # e.g., "ECU 1000B"
    tag_type: str         # e.g., "ECU" (Electro Chlorination Unit)
    tag_number: str       # e.g., "1000B"
    full_name: str        # e.g., "Electro Chlorination Unit"
    confidence: float = 0.0


@dataclass
class ValveTag:
    """밸브 태그"""
    tag_id: str           # e.g., "BWV8"
    valve_type: str       # e.g., "BWV" (Ballast Water Valve)
    number: str           # e.g., "8"
    signal_type: Optional[str] = None  # SIGNAL FOR BWMS
    confidence: float = 0.0


@dataclass
class PartsListItem:
    """Equipment List 항목"""
    item_no: Optional[str] = None
    description: Optional[str] = None
    tag_id: Optional[str] = None
    quantity: Optional[int] = None
    connection_size: Optional[str] = None
    remarks: Optional[str] = None


# =====================
# 테크로스 장비 사전 (BWMS/ECS 표준)
# =====================

# @AX:ANCHOR — 테크로스 표준 장비 약어 사전
EQUIPMENT_DICTIONARY: Dict[str, str] = {
    "CPC": "Central Process Controller",
    "PDE": "Power Distribution Equipment",
    "ECU": "Electro Chlorination Unit",
    "PRU": "Power Rectifier Unit",
    "ANU": "Analyzer Unit",
    "TSU": "TRO Sensor Unit",
    "APU": "Alkali Production Unit",
    "FMU": "Flow Measurement Unit",
    "FTS": "Filtration System",
    "CSU": "Chemical Storage Unit",
    "GDS": "Gas Detection System",
    "EWU": "Electrode Washing Unit",
    "PCU": "Process Control Unit",
}

# @AX:ANCHOR — 테크로스 밸브 타입 사전
VALVE_DICTIONARY: Dict[str, str] = {
    "BWV": "Ballast Water Valve",
    "FCV": "Flow Control Valve",
    "SOV": "Solenoid Valve",
    "CHV": "Check Valve",
    "PRV": "Pressure Relief Valve",
    "BFV": "Butterfly Valve",
    "BLV": "Ball Valve",
}

# 장비 태그 패턴: "ECU 1000B", "PDE-12A", "NO.1 APU"
EQUIPMENT_TAG_PATTERN = re.compile(
    r"(?:NO\.?\s*\d+\s+)?("
    + "|".join(EQUIPMENT_DICTIONARY.keys())
    + r")[\s\-]*([\w\d]*)",
    re.IGNORECASE
)

# 밸브 태그 패턴: "BWV8", "FCV01"
VALVE_TAG_PATTERN = re.compile(
    r"(" + "|".join(VALVE_DICTIONARY.keys()) + r")[\s\-]*(\d+[A-Z]?)",
    re.IGNORECASE
)

# 도면 번호 패턴 (테크로스: TP-XXXX-XXX 또는 DWG-XXXX)
DRAWING_NUMBER_PATTERNS = [
    r"TP[\-_]\w{3,4}[\-_]\d{2,4}",
    r"DWG[\-_]\d{4,8}",
    r"[A-Z]{2,4}[\-_]\d{4,6}[\-_][A-Z]{1,3}",
]

# 시스템 키워드
SYSTEM_KEYWORDS = {
    "BWMS": "Ballast Water Management System",
    "ECS": "Electro Chlorination System",
    "HYCHLOR": "Hydrogen Chlorination System",
}

# 선급 키워드
CLASS_SOCIETIES = ["DNV", "LR", "BV", "ABS", "NK", "KR", "CCS", "RINA"]


# =====================
# 장비 태그 추출
# =====================

def extract_equipment_tags(ocr_texts: List[Dict[str, Any]]) -> List[EquipmentTag]:
    """OCR 결과에서 장비 태그 추출"""
    tags: List[EquipmentTag] = []
    seen: set = set()

    for item in ocr_texts:
        text = item.get("text", "")
        conf = item.get("confidence", 0.0)

        for match in EQUIPMENT_TAG_PATTERN.finditer(text):
            tag_type = match.group(1).upper()
            tag_number = match.group(2) or ""
            tag_id = f"{tag_type} {tag_number}".strip() if tag_number else tag_type

            if tag_id not in seen:
                seen.add(tag_id)
                tags.append(EquipmentTag(
                    tag_id=tag_id,
                    tag_type=tag_type,
                    tag_number=tag_number,
                    full_name=EQUIPMENT_DICTIONARY.get(tag_type, "Unknown"),
                    confidence=conf,
                ))

    logger.info(f"Extracted {len(tags)} equipment tags")
    return tags


# =====================
# 밸브 태그 추출
# =====================

def extract_valve_tags(ocr_texts: List[Dict[str, Any]]) -> List[ValveTag]:
    """OCR 결과에서 밸브 태그 추출"""
    tags: List[ValveTag] = []
    seen: set = set()

    for item in ocr_texts:
        text = item.get("text", "")
        conf = item.get("confidence", 0.0)

        for match in VALVE_TAG_PATTERN.finditer(text):
            valve_type = match.group(1).upper()
            number = match.group(2)
            tag_id = f"{valve_type}{number}"

            if tag_id not in seen:
                seen.add(tag_id)
                tags.append(ValveTag(
                    tag_id=tag_id,
                    valve_type=valve_type,
                    number=number,
                    confidence=conf,
                ))

    logger.info(f"Extracted {len(tags)} valve tags")
    return tags


# =====================
# 표제란 파싱
# =====================

def parse_title_block(ocr_text: str, raw_texts: Optional[List[str]] = None) -> TitleBlockData:
    """P&ID 표제란 파싱"""
    result = TitleBlockData()
    if not ocr_text:
        return result

    # 도면 번호
    for pattern in DRAWING_NUMBER_PATTERNS:
        match = re.search(pattern, ocr_text)
        if match:
            result.drawing_number = match.group(0)
            break

    # 리비전
    rev_match = re.search(r"REV[.\s]*([A-Z0-9]+)", ocr_text, re.IGNORECASE)
    if rev_match:
        result.revision = rev_match.group(1)

    # 시스템 식별
    for keyword, full_name in SYSTEM_KEYWORDS.items():
        if keyword in ocr_text.upper():
            result.system = keyword
            break

    # 선급 식별
    for society in CLASS_SOCIETIES:
        if society in ocr_text.upper():
            result.class_society = society
            break

    return result


# =====================
# Equipment List 매칭
# =====================

def match_equipment_list(
    detected_tags: List[EquipmentTag],
    standard_list: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    검출된 장비 태그와 표준 Equipment List 매칭

    Args:
        detected_tags: OCR에서 추출된 장비 태그
        standard_list: 표준 Equipment List (Excel에서 로드)

    Returns:
        매칭 결과 (matched, unmatched, missing)
    """
    detected_set = {t.tag_type for t in detected_tags}
    standard_set = {item.get("tag_type", "").upper() for item in standard_list}

    matched = detected_set & standard_set
    in_drawing_only = detected_set - standard_set
    in_list_only = standard_set - detected_set

    return {
        "matched": sorted(matched),
        "in_drawing_only": sorted(in_drawing_only),
        "in_list_only": sorted(in_list_only),
        "match_rate": len(matched) / max(len(standard_set), 1) * 100,
        "total_detected": len(detected_tags),
        "total_standard": len(standard_list),
    }


# =====================
# Parts List 파싱
# =====================

def parse_parts_list(
    table_data: Optional[List[Dict[str, Any]]] = None,
    ocr_text: Optional[str] = None,
) -> List[PartsListItem]:
    """Equipment List / Parts List 파싱"""
    if table_data:
        return _parse_from_table(table_data)
    return []


def _parse_from_table(table_data: List[Dict[str, Any]]) -> List[PartsListItem]:
    items = []
    for row in table_data:
        item = PartsListItem(
            item_no=row.get("NO") or row.get("ITEM") or row.get("no"),
            description=row.get("DESCRIPTION") or row.get("DESC") or row.get("description"),
            tag_id=row.get("TAG") or row.get("TAG_ID") or row.get("tag"),
            quantity=_safe_int(row.get("QTY") or row.get("qty") or row.get("QUANTITY")),
            connection_size=row.get("SIZE") or row.get("CONNECTION") or row.get("connection_size"),
            remarks=row.get("REMARKS") or row.get("REMARK"),
        )
        items.append(item)
    return items


def _safe_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(str(value).strip())
    except (ValueError, TypeError):
        return None


# =====================
# 메인 파서 클래스
# =====================

class TechcrossParser:
    """
    테크로스 P&ID 도면 파서
    BWMS/ECS 설비 도면 전용
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
            "title": result.title,
            "system": result.system,
            "ship_no": result.ship_no,
            "class_society": result.class_society,
        }

    def extract_equipment(self, ocr_texts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        tags = extract_equipment_tags(ocr_texts)
        return [
            {"tag_id": t.tag_id, "tag_type": t.tag_type, "tag_number": t.tag_number,
             "full_name": t.full_name, "confidence": t.confidence}
            for t in tags
        ]

    def extract_valves(self, ocr_texts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        tags = extract_valve_tags(ocr_texts)
        return [
            {"tag_id": t.tag_id, "valve_type": t.valve_type, "number": t.number,
             "confidence": t.confidence}
            for t in tags
        ]

    def match_equipment_list(
        self, detected_tags: List[EquipmentTag], standard_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        return match_equipment_list(detected_tags, standard_list)

    def parse_parts_list(self, table_data=None, ocr_text=None) -> List[Dict[str, Any]]:
        items = parse_parts_list(table_data, ocr_text)
        return [
            {"item_no": i.item_no, "description": i.description, "tag_id": i.tag_id,
             "quantity": i.quantity, "connection_size": i.connection_size, "remarks": i.remarks}
            for i in items
        ]


_parser_instance = None


def get_parser() -> TechcrossParser:
    """파서 인스턴스 반환 (싱글톤)"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = TechcrossParser()
    return _parser_instance
