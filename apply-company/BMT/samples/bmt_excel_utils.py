"""
BMT Excel helpers.

- zipfile + xml.etree 기반 XLSX 파서
- GVU Part List(VALVE LIST / SENSOR LIST / Fitting List) 추출
"""

from __future__ import annotations

import re
import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, Iterable, List


XML_NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
DOC_NO_PATTERN = re.compile(r"W5X[A-Z0-9-]*-SN\d{4}-[A-Z0-9-]+", re.IGNORECASE)
SN_PATTERN = re.compile(r"SN\d{4}", re.IGNORECASE)


def normalize_header(value: str) -> str:
    """헤더 비교용 정규화 문자열"""
    text = value or ""
    return re.sub(r"[^0-9A-Za-z가-힣]+", "", text).lower()


def parse_numeric_qty(value: object) -> int:
    """수량 문자열에서 정수값 추출"""
    text = str(value or "").strip().replace(",", "")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return 0
    return int(float(match.group()))


def unique_preserve(values: Iterable[str]) -> List[str]:
    """순서를 유지한 중복 제거"""
    seen = set()
    items: List[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        items.append(text)
    return items


def _clean_code(value: object) -> str:
    return str(value or "").strip()


def _extract_doc_no(values: Iterable[str]) -> str:
    for value in values:
        text = str(value or "")
        match = DOC_NO_PATTERN.search(text)
        if match:
            return match.group(0).upper()
    return ""


def _extract_sensor_tag(raw_tag: str, remark: str) -> str:
    tag = _clean_code(raw_tag)
    if tag and tag != "-":
        return tag

    remark_text = _clean_code(remark)
    match = re.search(r"Valve\s*No\s*:?\s*([A-Z0-9/-]+)", remark_text, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return tag


class SimpleXlsxReader:
    """공유 문자열과 워크시트 XML만 읽는 최소 XLSX reader"""

    def __init__(self, xlsx_path: str) -> None:
        self.xlsx_path = xlsx_path
        self.archive = zipfile.ZipFile(xlsx_path)
        self.shared_strings = self._load_shared_strings()
        self.sheet_targets = self._load_sheet_targets()

    def close(self) -> None:
        self.archive.close()

    def __enter__(self) -> "SimpleXlsxReader":
        return self

    def __exit__(self, exc_type, exc, exc_tb) -> None:
        self.close()

    @property
    def sheet_names(self) -> List[str]:
        return list(self.sheet_targets.keys())

    def iter_sheet_rows(self, sheet_name: str) -> List[Dict[str, str]]:
        """시트의 각 row를 column-letter -> value 형태로 반환"""
        target = self.sheet_targets[sheet_name]
        xml_path = target if target.startswith("xl/") else f"xl/{target}"
        root = ET.parse(self.archive.open(xml_path)).getroot()
        rows: List[Dict[str, str]] = []
        for row in root.findall(".//x:sheetData/x:row", {"x": XML_NS["main"]}):
            cells: Dict[str, str] = {}
            for cell in row.findall("x:c", {"x": XML_NS["main"]}):
                ref = cell.get("r", "")
                col = "".join(char for char in ref if char.isalpha())
                cells[col] = self._cell_value(cell)
            rows.append(cells)
        return rows

    def _cell_value(self, cell: ET.Element) -> str:
        value_node = cell.find("x:v", {"x": XML_NS["main"]})
        if value_node is None or value_node.text is None:
            return ""

        text = value_node.text
        if cell.get("t") == "s":
            return self.shared_strings[int(text)]
        return text

    def _load_shared_strings(self) -> List[str]:
        strings: List[str] = []
        try:
            root = ET.parse(self.archive.open("xl/sharedStrings.xml")).getroot()
        except KeyError:
            return strings

        for si in root.findall(".//x:si", {"x": XML_NS["main"]}):
            text = "".join(
                node.text or "" for node in si.iter(f"{{{XML_NS['main']}}}t")
            )
            strings.append(text)
        return strings

    def _load_sheet_targets(self) -> Dict[str, str]:
        workbook = ET.parse(self.archive.open("xl/workbook.xml")).getroot()
        rels = ET.parse(self.archive.open("xl/_rels/workbook.xml.rels")).getroot()
        rel_map: Dict[str, str] = {}

        for rel in rels:
            if not rel.tag.endswith("Relationship"):
                continue
            rel_id = rel.get("Id")
            target = rel.get("Target")
            if rel_id and target:
                rel_map[rel_id] = target

        targets: Dict[str, str] = {}
        for sheet in workbook.findall(".//x:sheets/x:sheet", {"x": XML_NS["main"]}):
            name = sheet.get("name", "")
            rel_id = sheet.get(f"{{{XML_NS['rel']}}}id", "")
            if name and rel_id in rel_map:
                targets[name] = rel_map[rel_id]
        return targets


def _find_header_row(
    rows: List[Dict[str, str]],
    required_headers: Iterable[str],
) -> int:
    required = {normalize_header(header) for header in required_headers}
    for index, row in enumerate(rows):
        normalized = {normalize_header(value) for value in row.values() if value}
        if required.issubset(normalized):
            return index
    raise ValueError(f"필수 헤더를 찾을 수 없습니다: {sorted(required)}")


def _header_columns(row: Dict[str, str]) -> Dict[str, str]:
    return {normalize_header(value): column for column, value in row.items() if value}


def _get_value(row: Dict[str, str], column: str) -> str:
    return _clean_code(row.get(column, ""))


def _pick_primary_code(candidates: Iterable[str]) -> str:
    for candidate in unique_preserve(candidates):
        if candidate not in {"-", "N/A"}:
            return candidate
    return ""


def _parse_valve_list(rows: List[Dict[str, str]]) -> List[Dict[str, object]]:
    header_index = _find_header_row(rows, ["CODE", "Type", "Q'TY"])
    headers = _header_columns(rows[header_index])
    code_col = headers["code"]
    type_col = headers["type"]
    qty_col = headers["qty"]
    remark_col = headers.get("remark", "")
    drawing_col = headers.get("drawingno", "")
    erp_code_col = headers.get("erpcode", "")

    carry: Dict[str, str] = {}
    valves: List[Dict[str, object]] = []
    blank_rows = 0
    for row in rows[header_index + 1 :]:
        raw_code = _get_value(row, code_col)
        if raw_code == "Total Price":
            break

        row_values = [raw_code]
        for column in [type_col, qty_col, remark_col, drawing_col, erp_code_col]:
            if column:
                row_values.append(_get_value(row, column))

        if not any(row_values):
            blank_rows += 1
            if blank_rows >= 5 and valves:
                break
            continue
        blank_rows = 0

        if not raw_code:
            continue

        type_value = _get_value(row, type_col) or carry.get("type", "")
        qty_value = _get_value(row, qty_col) or carry.get("qty", "")
        remark_value = _get_value(row, remark_col) if remark_col else ""
        drawing_value = _get_value(row, drawing_col) if drawing_col else ""
        erp_code_value = _get_value(row, erp_code_col) if erp_code_col else ""

        carry.update(
            {
                "type": type_value or carry.get("type", ""),
                "qty": qty_value or carry.get("qty", ""),
                "remark": remark_value or carry.get("remark", ""),
                "drawing_ref": drawing_value or carry.get("drawing_ref", ""),
                "erp_code": erp_code_value or carry.get("erp_code", ""),
            }
        )

        code_candidates = unique_preserve(
            [
                carry.get("erp_code", ""),
                carry.get("remark", ""),
                carry.get("drawing_ref", ""),
            ]
        )
        valves.append(
            {
                "tag": raw_code,
                "qty": parse_numeric_qty(carry.get("qty", "")),
                "type": carry.get("type", ""),
                "drawing_no": _pick_primary_code(code_candidates),
                "drawing_ref": carry.get("drawing_ref", ""),
                "erp_code": carry.get("erp_code", ""),
                "code_candidates": code_candidates,
                "source_sheet": "VALVE LIST",
            }
        )
    return valves


def _parse_sensor_list(rows: List[Dict[str, str]]) -> List[Dict[str, object]]:
    header_index = _find_header_row(rows, ["Instrument Code.", "Q'TY", "Part No."])
    headers = _header_columns(rows[header_index])
    code_col = headers["instrumentcode"]
    qty_col = headers["qty"]
    item_col = headers.get("item", "")
    part_no_col = headers.get("partno", "")
    remark_col = headers.get("remark", "")
    item_code_col = headers.get("품목코드", "")

    sensors: List[Dict[str, object]] = []
    blank_rows = 0
    for row in rows[header_index + 1 :]:
        raw_code = _get_value(row, code_col)
        qty_value = _get_value(row, qty_col)
        part_no = _get_value(row, part_no_col) if part_no_col else ""
        item_code = _get_value(row, item_code_col) if item_code_col else ""
        remark = _get_value(row, remark_col) if remark_col else ""
        item_name = _get_value(row, item_col) if item_col else ""

        if not any([raw_code, qty_value, part_no, item_code, remark, item_name]):
            blank_rows += 1
            if blank_rows >= 5 and sensors:
                break
            continue
        blank_rows = 0

        tag = _extract_sensor_tag(raw_code, remark)
        code_candidates = unique_preserve([part_no, item_code])
        sensors.append(
            {
                "tag": tag,
                "qty": parse_numeric_qty(qty_value),
                "item": item_name,
                "drawing_no": _pick_primary_code(code_candidates),
                "part_no": part_no,
                "item_code": item_code,
                "remark": remark,
                "code_candidates": code_candidates,
                "source_sheet": "SENSOR LIST",
            }
        )
    return sensors


def _parse_fitting_list(rows: List[Dict[str, str]]) -> List[Dict[str, object]]:
    header_index = _find_header_row(rows, ["종류", "수량"])
    headers = _header_columns(rows[header_index])
    code_col = headers["종류"]
    qty_col = headers["수량"]

    fittings: Dict[str, Dict[str, object]] = {}
    blank_rows = 0
    carry_note = ""
    for row in rows[header_index + 1 :]:
        code = _get_value(row, code_col)
        qty_value = _get_value(row, qty_col)
        note = next(
            (
                _clean_code(value)
                for column, value in row.items()
                if column not in {code_col, qty_col} and _clean_code(value)
            ),
            "",
        )

        if not any([code, qty_value, note]):
            blank_rows += 1
            if blank_rows >= 5 and fittings:
                break
            continue
        blank_rows = 0

        if note:
            carry_note = note
        if not code:
            continue

        item = fittings.setdefault(
            code,
            {
                "part_code": code,
                "qty": 0,
                "note": carry_note,
                "source_sheet": "Fitting List",
            },
        )
        item["qty"] += parse_numeric_qty(qty_value)
        if carry_note and not item.get("note"):
            item["note"] = carry_note

    return list(fittings.values())


def parse_gvu_part_list(xlsx_path: str) -> Dict[str, object]:
    """GVU Part List에서 Valve/Sensor/Fitting 목록과 문서 메타데이터 추출"""
    with SimpleXlsxReader(xlsx_path) as reader:
        valve_rows = reader.iter_sheet_rows("VALVE LIST")
        sensor_rows = reader.iter_sheet_rows("SENSOR LIST")
        fitting_rows = reader.iter_sheet_rows("Fitting List") if "Fitting List" in reader.sheet_names else []
        workbook_strings = reader.shared_strings

    row_values = []
    for row in valve_rows + sensor_rows + fitting_rows:
        row_values.extend(row.values())

    doc_no = _extract_doc_no(row_values) or _extract_doc_no(workbook_strings)
    referenced_sns = sorted({match.upper() for text in workbook_strings for match in SN_PATTERN.findall(text)})
    return {
        "doc_no": doc_no,
        "referenced_sns": referenced_sns,
        "valves": _parse_valve_list(valve_rows),
        "sensors": _parse_sensor_list(sensor_rows),
        "fittings": _parse_fitting_list(fitting_rows) if fitting_rows else [],
    }
