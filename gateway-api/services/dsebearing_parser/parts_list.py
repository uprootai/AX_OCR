"""
DSE Bearing Parser — Parts List Parser

OCR 결과 또는 Table Detector 결과에서 Parts List를 파싱한다.
"""

import re
import logging
from typing import Dict, Any, List, Optional

from .models import PartsListItem

logger = logging.getLogger(__name__)


def parse_parts_list(
    ocr_texts: List[Dict[str, Any]],
    table_data: Optional[List[List[str]]] = None,
) -> List[PartsListItem]:
    """
    OCR 결과에서 Parts List 파싱

    Args:
        ocr_texts: eDOCr2 OCR 결과
        table_data: Table Detector 결과 (있는 경우)

    Returns:
        List[PartsListItem]: 파싱된 부품 리스트
    """
    items = []

    if table_data:
        items = _parse_from_table(table_data)

    if not items:
        items = _parse_from_ocr(ocr_texts)

    logger.info(f"Parts List 파싱 완료: {len(items)}개 항목")
    return items


def _normalize_table_data(table_data: List) -> List[List[str]]:
    """다양한 테이블 포맷을 2D 배열로 정규화"""
    if not table_data:
        return []

    if isinstance(table_data[0], list):
        return table_data

    if isinstance(table_data[0], dict):
        cells_data = []
        for table in table_data:
            if "cells" in table:
                cells_data.extend(table["cells"])
            elif "data" in table:
                if isinstance(table["data"], list) and table["data"] and isinstance(table["data"][0], list):
                    return table["data"]
                cells_data.extend(table.get("data", []))

        if not cells_data:
            return []

        max_row = max(c.get("row", 0) for c in cells_data if isinstance(c, dict)) + 1
        max_col = max(c.get("col", 0) for c in cells_data if isinstance(c, dict)) + 1
        rows = [["" for _ in range(max_col)] for _ in range(max_row)]

        for cell in cells_data:
            if isinstance(cell, dict):
                r = cell.get("row", 0)
                c = cell.get("col", 0)
                text = cell.get("text", "")
                if r < max_row and c < max_col:
                    rows[r][c] = text

        return rows

    return []


def _parse_from_table(table_data: List) -> List[PartsListItem]:
    """테이블 데이터에서 Parts List 파싱

    다양한 테이블 포맷 지원:
    - List[List[str]]: 2D 배열 (행 × 열)
    - List[Dict]: cells 키를 가진 딕셔너리 리스트
    """
    items = []
    header_found = False
    header_mapping = {}

    normalized_rows = _normalize_table_data(table_data)

    for row in normalized_rows:
        if not row:
            continue

        row_text = " ".join(str(cell) for cell in row).upper()

        if not header_found and any(h in row_text for h in ["NO", "DESCRIPTION", "MATERIAL", "QTY"]):
            header_found = True
            for i, cell in enumerate(row):
                cell_upper = str(cell).upper().strip()
                if "NO" in cell_upper and len(cell_upper) <= 4:
                    header_mapping["no"] = i
                elif "DESC" in cell_upper:
                    header_mapping["description"] = i
                elif "MATERIAL" in cell_upper or "MAT" in cell_upper:
                    header_mapping["material"] = i
                elif "SIZE" in cell_upper or "DWG" in cell_upper:
                    header_mapping["size_dwg_no"] = i
                elif "QTY" in cell_upper or "Q'TY" in cell_upper:
                    header_mapping["qty"] = i
                elif "REMARK" in cell_upper:
                    header_mapping["remark"] = i
            continue

        if header_found and row:
            item = PartsListItem()

            no_idx = header_mapping.get("no", 0)
            if no_idx < len(row):
                no_val = str(row[no_idx]).strip()
                if no_val.isdigit():
                    item.no = no_val
                else:
                    continue

            if "description" in header_mapping and header_mapping["description"] < len(row):
                item.description = str(row[header_mapping["description"]]).strip()

            if "material" in header_mapping and header_mapping["material"] < len(row):
                item.material = str(row[header_mapping["material"]]).strip()

            if "size_dwg_no" in header_mapping and header_mapping["size_dwg_no"] < len(row):
                item.size_dwg_no = str(row[header_mapping["size_dwg_no"]]).strip()

            if "qty" in header_mapping and header_mapping["qty"] < len(row):
                qty_str = str(row[header_mapping["qty"]]).strip()
                try:
                    item.qty = int(re.search(r"\d+", qty_str).group(0))
                except Exception:
                    item.qty = 1

            if "remark" in header_mapping and header_mapping["remark"] < len(row):
                item.remark = str(row[header_mapping["remark"]]).strip()

            if item.no and item.description:
                items.append(item)

    return items


def _parse_from_ocr(ocr_texts: List[Dict[str, Any]]) -> List[PartsListItem]:
    """OCR 텍스트에서 Parts List 패턴 파싱 (노이즈 대응 강화)"""
    items = []
    all_texts = []

    for item in ocr_texts:
        if isinstance(item, dict):
            text = item.get("text", "")
        elif isinstance(item, str):
            text = item
        else:
            continue
        if text:
            all_texts.append(text.strip())

    combined = " ".join(all_texts)

    part_keywords = [
        "RING UPPER", "RING LOWER", "CASING", "LINER", "PAD",
        "HEX SOCKET", "DOWEL PIN", "SHIM PLATE", "BOLT", "NUT",
        "WASHER", "SCREW", "PLATE", "BUSHING", "WEDGE", "PIN",
        "BEARING", "ASSY", "ASSEMBLY", "LOCKING", "BUTTON", "SET PIN"
    ]

    # 1단계: 키워드 기반 파싱
    found_parts: set = set()
    for keyword in part_keywords:
        keyword_pattern = re.compile(
            rf"(\d{{1,2}})\s*[^\w]*{re.escape(keyword)}[^\w]*"
            rf"([A-Z]{{2,}}[A-Z0-9]*|SEE\s*EXCEL[^\|]*)?[^\|]*"
            rf"(T[D0O]\d{{7}}[A-Z\d]*)?",
            re.IGNORECASE
        )
        for match in keyword_pattern.finditer(combined):
            no = match.group(1)
            if no not in found_parts:
                found_parts.add(no)
                material = match.group(2) or "SEE EXCEL BOM"
                material = material.strip()
                if "SEE" in material.upper() or "EXCEL" in material.upper():
                    material = "SEE EXCEL BOM"

                dwg_no = match.group(3) or ""
                dwg_no = dwg_no.replace("O", "0").replace("o", "0")

                items.append(PartsListItem(
                    no=no,
                    description=keyword,
                    material=material,
                    size_dwg_no=dwg_no,
                    qty=1
                ))

    # 2단계: 표준 패턴 매칭
    if not items:
        part_pattern = re.compile(
            r"(\d+)\s+"
            r"([A-Z][A-Z\s]+(?:RING|BOLT|PIN|NUT|PLATE|ASSY|PAD|WASHER|SCREW))\s+"
            r"(SF\d+[A-Z]?|SM\d+[A-Z]?|S[A-Z0-9]+|SEE\s*EXCEL|ASTM[^\s]+)?\s*"
            r"(TD\d+[A-Z\d]*)\s+"
            r"(\d+)",
            re.IGNORECASE
        )
        matches = part_pattern.findall(combined)
        for match in matches:
            items.append(PartsListItem(
                no=match[0],
                description=match[1].strip(),
                material=match[2].strip() if match[2] else "SEE EXCEL BOM",
                size_dwg_no=match[3].strip(),
                qty=int(match[4]) if match[4] else 1
            ))

    # 3단계: 도면번호 패턴으로 역추적
    if not items:
        td_pattern = re.compile(r"(\d{1,2})[^\d]*([A-Z][A-Z\s]+)[^\d]*(T[D0O]\d{7}[A-Z\d]*)", re.IGNORECASE)
        for match in td_pattern.finditer(combined):
            no = match.group(1)
            desc = match.group(2).strip()
            dwg = match.group(3).replace("O", "0").replace("o", "0")
            if len(desc) > 3:
                items.append(PartsListItem(
                    no=no,
                    description=desc,
                    size_dwg_no=dwg,
                ))

    # 4단계: 단순 번호+설명 패턴
    if not items:
        simple_pattern = re.compile(r"(?:^|\s)(\d{1,2})\s+([A-Z][A-Z\s]{3,20})", re.MULTILINE)
        for text in all_texts:
            for match in simple_pattern.finditer(text):
                items.append(PartsListItem(
                    no=match.group(1),
                    description=match.group(2).strip()
                ))

    # 중복 제거 (NO 기준)
    seen: set = set()
    unique_items = []
    for item in items:
        if item.no not in seen:
            seen.add(item.no)
            unique_items.append(item)

    unique_items.sort(key=lambda x: int(x.no) if x.no.isdigit() else 99)

    return unique_items
