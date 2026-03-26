"""
BMT 도면-BOM 자동 비교 파이프라인

- pdfplumber 테이블 추출 (병합셀 후처리 포함)
- ERP BOM 엑셀 파싱 (zipfile + xml.etree)
- 3단계 매칭: exact -> prefix -> fuzzy
- 동의어 사전 매칭
- GVU SN 자동 검증
- Excel 리포트 생성
"""

from __future__ import annotations

import os
import re
from difflib import SequenceMatcher
from typing import Dict, List

import fitz
import pdfplumber

from bmt_balloon_checker import cross_check_pdf_pages, format_number_list, integrate_balloon_cross_checks
from bmt_excel_utils import SimpleXlsxReader, parse_gvu_part_list, parse_numeric_qty, unique_preserve
from bmt_report import write_comparison_report
from bmt_sn_validator import should_skip_vd_matching, validate_pdf_sn_consistency


RAW_CODE_SYNONYMS = {
    "ANSI B18.2.3.5M-M8x1.25x16": ["HB-M8-15L"],
}


def normalize_code(code: object) -> str:
    """문자열 비교용 코드 정규화"""
    text = str(code or "").upper()
    text = re.sub(r"\s+", "", text)
    return text


def build_synonym_index(raw_mapping: Dict[str, List[str]]) -> Dict[str, set]:
    """양방향 동의어 인덱스 생성"""
    index: Dict[str, set] = {}
    for left, values in raw_mapping.items():
        left_key = normalize_code(left)
        index.setdefault(left_key, set())
        for value in values:
            right_key = normalize_code(value)
            index[left_key].add(right_key)
            index.setdefault(right_key, set()).add(left_key)
    return index


SYNONYM_INDEX = build_synonym_index(RAW_CODE_SYNONYMS)


# 1. PDF 테이블 추출 — 병합셀 후처리 포함

def extract_parts_from_table(raw_table, has_no_column: bool = True):
    """pdfplumber raw 테이블 -> 부품 리스트 (병합셀 split 처리)"""
    parts = []
    if not raw_table or len(raw_table) < 2:
        return parts

    for row in raw_table[1:]:
        if has_no_column:
            no_val = str(row[0]).strip() if row[0] else ""
            desc_val = str(row[1]).strip() if len(row) > 1 and row[1] else ""
            mat_val = str(row[2]).strip() if len(row) > 2 and row[2] else ""
            qty_val = str(row[3]).strip() if len(row) > 3 and row[3] else ""
            rmk_val = str(row[4]).strip() if len(row) > 4 and row[4] else ""
        else:
            no_val = ""
            desc_val = str(row[0]).strip() if row[0] else ""
            mat_val = str(row[1]).strip() if len(row) > 1 and row[1] else ""
            qty_val = str(row[2]).strip() if len(row) > 2 and row[2] else ""
            rmk_val = str(row[3]).strip() if len(row) > 3 and row[3] else ""

        if "\n" in no_val or "\n" in desc_val:
            nos = no_val.split("\n") if no_val else [""]
            descs = desc_val.split("\n") if desc_val else [""]
            mats = mat_val.split("\n") if mat_val else [""]
            qtys = qty_val.split("\n") if qty_val else [""]
            max_len = max(len(nos), len(descs))
            for index in range(max_len):
                parts.append(
                    {
                        "no": nos[index].strip() if index < len(nos) else "",
                        "description": descs[index].strip() if index < len(descs) else "",
                        "material": mats[index].strip() if index < len(mats) else "",
                        "qty": qtys[index].strip() if index < len(qtys) else "",
                        "remark": rmk_val if index == 0 else "",
                        "merged": True,
                    }
                )
        else:
            parts.append(
                {
                    "no": no_val,
                    "description": desc_val,
                    "material": mat_val,
                    "qty": qty_val,
                    "remark": rmk_val,
                    "merged": False,
                }
            )

    return parts


def find_description_table(tables):
    """pdfplumber 테이블 목록에서 Description 테이블 찾기"""
    for table in tables:
        if not table or len(table) <= 2:
            continue
        header_str = " ".join(str(cell) for cell in table[0] if cell)
        if "DESCRIPTION" in header_str and ("MATERIAL" in header_str or "Q'TY" in header_str):
            return table, "NO" in header_str
    return None, True


def extract_fb2fb6_parts(tables):
    """1번 자료(FB2FB6) 전용 — 한글 부품리스트 추출"""
    if len(tables) < 2:
        return []

    parts_table = tables[1]
    parts = []
    for row in parts_table:
        if row[1] and row[1].strip():
            items = row[1].strip().split("\n")
            qtys = row[3].strip().split("\n") if row[3] else []
            part_codes = row[4].strip().split("\n") if row[4] else []
            descs = row[7].strip().split("\n") if len(row) > 7 and row[7] else []

            for index, item in enumerate(items):
                item = item.strip()
                if item.isdigit():
                    parts.append(
                        {
                            "no": item,
                            "description": descs[index].strip() if index < len(descs) else "",
                            "material": "",
                            "qty": qtys[index].strip() if index < len(qtys) else "0",
                            "part_code": part_codes[index].strip() if index < len(part_codes) else "",
                            "merged": len(items) > 1,
                        }
                    )
    return parts


# 2. ERP BOM 엑셀 파싱

def parse_erp_bom(xlsx_path, level: str = ".1"):
    """ERP BOM 엑셀 -> 지정 level 자품목 리스트"""
    with SimpleXlsxReader(xlsx_path) as reader:
        rows = reader.iter_sheet_rows(reader.sheet_names[0])

    erp_parts = []
    for cells in rows:
        if cells.get("A") != level:
            continue

        code = str(cells.get("C", "")).strip()
        if not code:
            continue

        erp_parts.append(
            {
                "item_no": str(cells.get("B", "")).strip(),
                "code": code,
                "qty": parse_numeric_qty(cells.get("L", "0")),
                "description": str(cells.get("D", "")).strip(),
                "tag_hint": str(cells.get("Y", "")).strip(),
            }
        )
    return erp_parts


# 3. 3단계 매칭 + 동의어

def fuzzy_ratio(a, b):
    """두 문자열의 유사도 (0~1)"""
    return SequenceMatcher(None, normalize_code(a), normalize_code(b)).ratio()


def format_code_diff(left: object, right: object) -> str:
    """두 코드의 차이 구간을 대괄호로 감싼 diff 문자열"""
    left_text = str(left or "")
    right_text = str(right or "")
    matcher = SequenceMatcher(None, left_text, right_text)

    def render(side: str) -> str:
        parts = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                parts.append(left_text[i1:i2] if side == "left" else right_text[j1:j2])
                continue
            chunk = left_text[i1:i2] if side == "left" else right_text[j1:j2]
            if chunk:
                parts.append(f"[{chunk}]")
        return "".join(parts)

    return f"{render('left')} ↔ {render('right')}"


def are_synonyms(left: object, right: object) -> bool:
    """동의어 사전 기반 코드 매칭"""
    left_key = normalize_code(left)
    right_key = normalize_code(right)
    return right_key in SYNONYM_INDEX.get(left_key, set())


def compare_parts(drawing_parts, erp_parts, code_key="part_code", fuzzy_threshold=0.75):
    """도면 부품 vs ERP BOM 3단계 비교 + 동의어 사전"""
    results = []
    erp_remaining = list(erp_parts)

    for drawing_part in drawing_parts:
        drawing_code = drawing_part.get(code_key, "")
        drawing_qty = parse_numeric_qty(drawing_part.get("qty", 0))
        normalized_drawing = normalize_code(drawing_code)
        match = {"drawing": drawing_part, "erp": None, "type": None, "detail": ""}

        for index, erp_part in enumerate(erp_remaining):
            if normalized_drawing == normalize_code(erp_part["code"]):
                qty_ok = drawing_qty == erp_part["qty"]
                match["erp"] = erp_part
                match["type"] = "exact" if qty_ok else "qty_mismatch"
                match["detail"] = "품번+수량 일치" if qty_ok else f"수량 불일치 ({drawing_qty}↔{erp_part['qty']})"
                erp_remaining.pop(index)
                break

        if not match["type"] and normalized_drawing:
            for index, erp_part in enumerate(erp_remaining):
                normalized_erp = normalize_code(erp_part["code"])
                if normalized_erp.startswith(normalized_drawing) or normalized_drawing.startswith(normalized_erp):
                    suffix = erp_part["code"]
                    if normalized_erp.startswith(normalized_drawing):
                        suffix = erp_part["code"][len(drawing_code) :]
                    elif normalized_drawing.startswith(normalized_erp):
                        suffix = drawing_code[len(erp_part["code"]) :]
                    match["erp"] = erp_part
                    match["type"] = "prefix"
                    match["detail"] = (
                        f"접두/접미 차이: {format_code_diff(drawing_code, erp_part['code'])}"
                        if suffix or drawing_code != erp_part["code"]
                        else "접두/접미 차이"
                    )
                    erp_remaining.pop(index)
                    break

        if not match["type"] and normalized_drawing:
            best_ratio = 0.0
            best_index = -1
            for index, erp_part in enumerate(erp_remaining):
                ratio = fuzzy_ratio(drawing_code, erp_part["code"])
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_index = index

            if best_ratio >= fuzzy_threshold and best_index >= 0:
                erp_part = erp_remaining[best_index]
                match["erp"] = erp_part
                match["type"] = "fuzzy"
                match["detail"] = f"유사도 {best_ratio:.0%}: {format_code_diff(drawing_code, erp_part['code'])}"
                erp_remaining.pop(best_index)

        if not match["type"] and normalized_drawing:
            for index, erp_part in enumerate(erp_remaining):
                if are_synonyms(drawing_code, erp_part["code"]):
                    match["erp"] = erp_part
                    match["type"] = "synonym"
                    match["detail"] = "동의어 사전 매칭"
                    erp_remaining.pop(index)
                    break

        if not match["type"]:
            match["type"] = "drawing_only"
            match["detail"] = "ERP에 대응 코드 없음"

        results.append(match)

    for erp_part in erp_remaining:
        results.append(
            {
                "drawing": None,
                "erp": erp_part,
                "type": "erp_only",
                "detail": "도면에 없음",
            }
        )

    return results


def summarize_results(results: List[Dict[str, object]]) -> Dict[str, int]:
    """결과 타입별 카운트"""
    counts = {
        "exact": 0,
        "qty_mismatch": 0,
        "prefix": 0,
        "fuzzy": 0,
        "synonym": 0,
        "drawing_only": 0,
        "erp_only": 0,
    }
    for result in results:
        result_type = result["type"]
        if result_type in counts:
            counts[result_type] += 1
    counts["bom_only"] = counts["erp_only"]
    counts["unmatched"] = counts["drawing_only"] + counts["erp_only"]
    return counts


def select_part_list_code(entry: Dict[str, object], erp_parts: List[Dict[str, object]]) -> str:
    """Part List 후보 코드 중 ERP 매칭 가능성이 가장 높은 값 선택"""
    candidates = unique_preserve(
        list(entry.get("code_candidates", []))
        + [
            str(entry.get("drawing_no", "")),
            str(entry.get("erp_code", "")),
            str(entry.get("part_no", "")),
            str(entry.get("item_code", "")),
        ]
    )
    erp_codes = [erp_part["code"] for erp_part in erp_parts]

    for candidate in candidates:
        if any(normalize_code(candidate) == normalize_code(erp_code) for erp_code in erp_codes):
            return candidate

    for candidate in candidates:
        if any(are_synonyms(candidate, erp_code) for erp_code in erp_codes):
            return candidate

    for candidate in candidates:
        if any(
            normalize_code(erp_code).startswith(normalize_code(candidate))
            or normalize_code(candidate).startswith(normalize_code(erp_code))
            for erp_code in erp_codes
        ):
            return candidate

    best_candidate = ""
    best_ratio = 0.0
    for candidate in candidates:
        for erp_code in erp_codes:
            ratio = fuzzy_ratio(candidate, erp_code)
            if ratio > best_ratio:
                best_ratio = ratio
                best_candidate = candidate

    return best_candidate or (candidates[0] if candidates else "")


def compare_gvu_parts(vd_pages, valve_list, erp_parts):
    """VD TAG -> Part List -> ERP BOM 3단계 매칭"""
    tag_to_part = {
        normalize_code(entry["tag"]): entry
        for entry in valve_list
        if str(entry.get("tag", "")).strip()
    }
    grouped_parts: Dict[str, Dict[str, object]] = {}
    results = []

    for page in vd_pages:
        if not page["tags"]:
            results.append(
                {
                    "drawing": {
                        "part_code": page.get("drawing_no", f"Page {page['page']}"),
                        "qty": 0,
                        "tags": [],
                        "page_numbers": [page["page"]],
                        "part_list_codes": [],
                        "drawing_no": page.get("drawing_no", ""),
                    },
                    "erp": None,
                    "type": "drawing_only",
                    "detail": "VD 페이지에서 TAG NO. 추출 실패",
                }
            )
            continue

        for tag in page["tags"]:
            entry = tag_to_part.get(normalize_code(tag))
            if not entry:
                results.append(
                    {
                        "drawing": {
                            "part_code": tag,
                            "qty": 0,
                            "tags": [tag],
                            "page_numbers": [page["page"]],
                            "part_list_codes": [],
                            "drawing_no": page.get("drawing_no", ""),
                        },
                        "erp": None,
                        "type": "drawing_only",
                        "detail": "Part List에 TAG 매핑 없음",
                    }
                )
                continue

            selected_code = select_part_list_code(entry, erp_parts) or entry.get("drawing_no") or tag
            group_key = normalize_code(selected_code or tag)
            grouped = grouped_parts.setdefault(
                group_key,
                {
                    "part_code": selected_code,
                    "qty": 0,
                    "tags": [],
                    "page_numbers": [],
                    "part_list_codes": [],
                    "drawing_no": "",
                    "drawing_ref": "",
                    "type": "",
                },
            )
            grouped["qty"] += max(parse_numeric_qty(entry.get("qty", 0)), 1)
            grouped["tags"].append(tag)
            grouped["page_numbers"].append(page["page"])
            grouped["part_list_codes"].append(entry.get("tag", tag))
            grouped["drawing_no"] = grouped["drawing_no"] or entry.get("drawing_no", "")
            grouped["drawing_ref"] = grouped["drawing_ref"] or entry.get("drawing_ref", "")
            grouped["type"] = grouped["type"] or entry.get("type", "")

    drawing_parts = []
    for grouped in grouped_parts.values():
        drawing_parts.append(
            {
                "part_code": grouped["part_code"],
                "qty": grouped["qty"],
                "tags": unique_preserve(grouped["tags"]),
                "page_numbers": sorted(set(grouped["page_numbers"])),
                "part_list_codes": unique_preserve(grouped["part_list_codes"]),
                "drawing_no": grouped["drawing_no"],
                "drawing_ref": grouped["drawing_ref"],
                "type": grouped["type"],
            }
        )

    matched = compare_parts(drawing_parts, erp_parts, code_key="part_code")
    for result in matched:
        drawing = result.get("drawing")
        erp_part = result.get("erp")
        parts = []
        if drawing:
            tags = ", ".join(drawing.get("tags", []))
            pages = ", ".join(str(page_number) for page_number in drawing.get("page_numbers", []))
            if tags:
                parts.append(f"TAG={tags}")
            if pages:
                parts.append(f"Page={pages}")
            if drawing.get("drawing_no"):
                parts.append(f"PartList={drawing['drawing_no']}")
        elif erp_part and erp_part.get("tag_hint"):
            parts.append(f"ERP TAG={erp_part['tag_hint']}")

        if parts:
            result["detail"] = " | ".join(parts + [result["detail"]])

    return results + matched


# 4. VD / ITDRA 메타 파서

def clean_block_text(text: str) -> str:
    return " ".join(part.strip() for part in text.splitlines() if part.strip())


def normalize_label(text: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "", str(text or "").upper())


def block_value_by_label(blocks, label_text: str) -> str:
    """블록 좌표 기준으로 라벨 오른쪽 값 추출"""
    label_key = normalize_label(label_text)
    label_blocks = []
    for block in blocks:
        text = clean_block_text(block[4])
        if normalize_label(text) == label_key:
            label_blocks.append(block)

    best_value = ""
    best_score = None
    for label_block in label_blocks:
        lx0, ly0, lx1, ly1 = label_block[:4]
        label_y = (ly0 + ly1) / 2
        for block in blocks:
            if block == label_block:
                continue
            x0, y0, _, y1, text = block[:5]
            value = clean_block_text(text)
            if not value:
                continue
            if x0 <= lx1 - 5:
                continue
            y_delta = abs(((y0 + y1) / 2) - label_y)
            if y_delta > 16:
                continue
            score = (y_delta, x0 - lx1)
            if best_score is None or score < best_score:
                best_score = score
                best_value = value
    return best_value


def split_tags(tag_text: str) -> List[str]:
    tags = []
    for item in re.split(r"[/,\n]+", tag_text or ""):
        cleaned = item.strip().upper()
        if cleaned:
            tags.append(cleaned)
    return unique_preserve(tags)


def parse_vd_page_metadata(doc, page_num: int) -> Dict[str, object]:
    """VD 페이지의 TAG / DRAWING NO 메타데이터 추출"""
    page = doc[page_num - 1]
    blocks = page.get_text("blocks")
    drawing_no = block_value_by_label(blocks, "DRAWING NO")
    tag_text = block_value_by_label(blocks, "TAG NO")
    return {
        "page": page_num,
        "drawing_no": drawing_no,
        "tag_text": tag_text,
        "tags": split_tags(tag_text),
        "sn": re.search(r"SN\d{4}", drawing_no or "")[0] if re.search(r"SN\d{4}", drawing_no or "") else "",
    }


def collect_vd_pages(pdf_path: str) -> List[Dict[str, object]]:
    """VD 상세 페이지의 메타데이터와 Description 테이블 수집"""
    vd_pages = []
    fitz_doc = fitz.open(pdf_path)
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num in range(6, 14):
                page = pdf.pages[page_num - 1]
                tables = page.extract_tables()
                desc_table, has_no = find_description_table(tables)
                parts = extract_parts_from_table(desc_table, has_no_column=has_no) if desc_table else []
                metadata = parse_vd_page_metadata(fitz_doc, page_num)
                metadata.update(
                    {
                        "parts": parts,
                        "merged_count": sum(1 for part in parts if part["merged"]),
                        "has_table": bool(desc_table),
                    }
                )
                vd_pages.append(metadata)
    finally:
        fitz_doc.close()
    return vd_pages


def parse_itdra_page(doc, page_num: int):
    """ITDRA 페이지에서 키-값 스펙 추출"""
    page = doc[page_num - 1]
    text = page.get_text()
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    spec = {}
    for line in lines:
        if "Tag No" in line:
            tag_match = re.search(r"Tag No\.?\s*(.+)", line)
            if tag_match:
                spec["tag_no"] = tag_match.group(1).strip()

    for line in lines:
        if "DRAWING NO" in line.upper():
            index = lines.index(line)
            drawing_match = re.search(r"W5X\S+", line)
            if not drawing_match and index + 1 < len(lines):
                drawing_match = re.search(r"W5X\S+", lines[index + 1])
            if drawing_match:
                spec["drawing_no"] = drawing_match.group(0)

    key_values = [
        "Subject",
        "Maker",
        "Model",
        "Transmitter setting range",
        "Output signal",
        "Electrical connection",
        "Process connection",
        "Sensor element",
        "Max. Ambient temp",
        "Ex Protection",
        "IECEx Cert No",
        "Pressure range",
        "Ambient temperature",
        "Supply voltage",
        "Flow principle",
    ]

    for key in key_values:
        for index, line in enumerate(lines):
            if key.lower() not in line.lower():
                continue
            after = line.split(key, 1)[-1].strip().lstrip(":").strip()
            if after and len(after) > 2:
                spec[key] = after
            elif index + 1 < len(lines):
                spec[key] = lines[index + 1].strip()
            break

    parts = []
    in_parts = False
    for line in lines:
        if "POS" in line and "DESCRIPTION" in line:
            in_parts = True
            continue
        if in_parts:
            pos_match = re.match(r"^(\d+)\s+(.+)", line)
            if pos_match:
                parts.append({"pos": pos_match.group(1), "description": pos_match.group(2).strip()})
            elif line and not any(keyword in line for keyword in ["Rev", "Issue", "PURCHASER", "CLIENT"]):
                if parts:
                    parts[-1]["description"] += " " + line
            else:
                in_parts = False

    spec["parts"] = parts
    return spec


# 5. 리포트 유틸

def result_status_for_report(result_type: str) -> str:
    if result_type == "drawing_only":
        return "drawing_only"
    if result_type == "erp_only":
        return "bom_only"
    return result_type


def quantity_compare_text(result: Dict[str, object]) -> str:
    if result.get("type") == "skipped":
        return "skipped"

    drawing = result.get("drawing")
    erp_part = result.get("erp")
    if not drawing or not erp_part:
        return "n/a"

    drawing_qty = parse_numeric_qty(drawing.get("qty", 0))
    erp_qty = parse_numeric_qty(erp_part.get("qty", 0))
    operator = "=" if drawing_qty == erp_qty else "!="
    return f"{drawing_qty} {operator} {erp_qty}"


def summary_row(dataset: str, results: List[Dict[str, object]], status: str = "ok", notes: str = "") -> Dict[str, object]:
    counts = summarize_results(results)
    return {
        "dataset": dataset,
        "records": len(results),
        "exact": counts["exact"],
        "qty_mismatch": counts["qty_mismatch"],
        "prefix": counts["prefix"],
        "fuzzy": counts["fuzzy"],
        "synonym": counts["synonym"],
        "drawing_only": counts["drawing_only"],
        "bom_only": counts["bom_only"],
        "status": status,
        "notes": notes,
    }


def build_detail_rows(fb_results, gvu_results, gvu_skip_reason: str, fitting_results=None):
    detail_rows = []
    fitting_results = fitting_results or []

    for result in fb_results:
        drawing = result.get("drawing") or {}
        erp_part = result.get("erp") or {}
        detail_rows.append(
            {
                "dataset": "FB2FB6",
                "section": "PARTS",
                "page": "",
                "drawing_part_no": drawing.get("part_code", ""),
                "part_list_code": drawing.get("part_code", ""),
                "part_list_drawing_no": "",
                "erp_child_item": erp_part.get("code", ""),
                "drawing_qty": parse_numeric_qty(drawing.get("qty", 0)) if drawing else "",
                "erp_qty": erp_part.get("qty", ""),
                "qty_compare": quantity_compare_text(result),
                "verdict": result_status_for_report(result["type"]),
                "detail": result["detail"],
                "review_status": "미확인",
                "reviewer": "",
                "comment": "",
            }
        )

    for result in gvu_results:
        drawing = result.get("drawing") or {}
        erp_part = result.get("erp") or {}
        detail_rows.append(
            {
                "dataset": "GVU-VD",
                "section": "VD",
                "page": ", ".join(str(page) for page in drawing.get("page_numbers", [])) if drawing else "",
                "drawing_part_no": ", ".join(drawing.get("tags", [])) if drawing else "",
                "part_list_code": ", ".join(drawing.get("part_list_codes", [])) if drawing else "",
                "part_list_drawing_no": drawing.get("drawing_no", "") if drawing else "",
                "erp_child_item": erp_part.get("code", ""),
                "drawing_qty": parse_numeric_qty(drawing.get("qty", 0)) if drawing else "",
                "erp_qty": erp_part.get("qty", ""),
                "qty_compare": quantity_compare_text(result),
                "verdict": result_status_for_report(result["type"]),
                "detail": result["detail"],
                "review_status": "미확인",
                "reviewer": "",
                "comment": "",
            }
        )

    for result in fitting_results:
        drawing = result.get("drawing") or {}
        erp_part = result.get("erp") or {}
        detail_rows.append(
            {
                "dataset": "GVU-Fitting",
                "section": "Fitting List",
                "page": "",
                "drawing_part_no": drawing.get("part_code", ""),
                "part_list_code": drawing.get("part_code", ""),
                "part_list_drawing_no": drawing.get("note", ""),
                "erp_child_item": erp_part.get("code", ""),
                "drawing_qty": parse_numeric_qty(drawing.get("qty", 0)) if drawing else "",
                "erp_qty": erp_part.get("qty", ""),
                "qty_compare": quantity_compare_text(result),
                "verdict": result_status_for_report(result["type"]),
                "detail": result["detail"],
                "review_status": "미확인",
                "reviewer": "",
                "comment": "",
            }
        )

    if gvu_skip_reason:
        detail_rows.append(
            {
                "dataset": "GVU-VD",
                "section": "VD",
                "page": "4-13",
                "drawing_part_no": "",
                "part_list_code": "",
                "part_list_drawing_no": "",
                "erp_child_item": "",
                "drawing_qty": "",
                "erp_qty": "",
                "qty_compare": "skipped",
                "verdict": "skipped",
                "detail": gvu_skip_reason,
                "review_status": "미확인",
                "reviewer": "",
                "comment": "",
            }
        )

    return detail_rows


def counts_text(counts: Dict[str, int]) -> str:
    return (
        "exact={exact} | qty_mismatch={qty_mismatch} | prefix={prefix} | fuzzy={fuzzy} | "
        "synonym={synonym} | drawing_only={drawing_only} | bom_only={bom_only}"
    ).format(**counts)


def select_relevant_erp_parts(
    drawing_parts: List[Dict[str, object]],
    erp_parts: List[Dict[str, object]],
    code_key: str = "part_code",
    fuzzy_threshold: float = 0.75,
) -> List[Dict[str, object]]:
    candidates = []
    for erp_part in erp_parts:
        erp_code = erp_part["code"]
        for drawing_part in drawing_parts:
            drawing_code = drawing_part.get(code_key, "")
            normalized_drawing = normalize_code(drawing_code)
            normalized_erp = normalize_code(erp_code)
            if not normalized_drawing:
                continue
            if normalized_drawing == normalized_erp:
                candidates.append(erp_part)
                break
            if normalized_erp.startswith(normalized_drawing) or normalized_drawing.startswith(normalized_erp):
                candidates.append(erp_part)
                break
            if are_synonyms(drawing_code, erp_code) or fuzzy_ratio(drawing_code, erp_code) >= fuzzy_threshold:
                candidates.append(erp_part)
                break
    return candidates


def print_result_lines(results: List[Dict[str, object]], code_key: str) -> None:
    icons = {
        "exact": "✅",
        "qty_mismatch": "🟠",
        "prefix": "⚠️",
        "fuzzy": "🟡",
        "synonym": "🟣",
        "drawing_only": "🔴",
        "erp_only": "🔴",
    }
    for result in results:
        drawing = result.get("drawing")
        erp_part = result.get("erp")
        drawing_code = "-"
        if drawing:
            drawing_code = drawing.get(code_key, "")
            if drawing.get("tags"):
                drawing_code = ",".join(drawing["tags"])
        erp_code = erp_part["code"] if erp_part else "-"
        print(f"    {icons[result['type']]} {drawing_code:<35s} ↔ {erp_code:<35s} {result['detail']}")


# 6. 메인 실행

def run_pipeline(base_dir):
    """전체 파이프라인 실행"""
    print("=" * 70)
    print("BMT 도면-BOM 자동 비교 파이프라인")
    print("=" * 70)

    pdf1 = os.path.join(base_dir, "1_FB2FB6-32A-1S-D011-1SDNA-36L-KGS.pdf")
    xlsx1 = os.path.join(base_dir, "1_FB2FB6-32A-1S-D011-1SDNA-36L-KGS__BOM.xlsx")
    pdf2 = os.path.join(base_dir, "2_W5XGVU-SN2709-GARRB.pdf")
    xlsx_part_list = os.path.join(base_dir, "2_W5XGVU-SN2709-PLRA_Part List.xlsx")
    xlsx_gvu_erp = os.path.join(base_dir, "2_W5XHEGVU-SN2709-DNV.xlsx")

    print("\n[1번 자료] FB2FB6 개별 밸브")
    with pdfplumber.open(pdf1) as pdf:
        drawing_parts = extract_fb2fb6_parts(pdf.pages[0].extract_tables())
    erp_parts = parse_erp_bom(xlsx1)
    fb_results = compare_parts(drawing_parts, erp_parts, code_key="part_code")
    fb_counts = summarize_results(fb_results)
    print(f"  도면 추출: {len(drawing_parts)}개 (병합셀 후처리 적용)")
    print(f"  ERP BOM: {len(erp_parts)}개")
    print(f"  결과: {counts_text(fb_counts)}")
    print_result_lines(fb_results, code_key="part_code")

    print("\n[1번 자료] FB2FB6 — Balloon vs 부품리스트 NO.")
    fb_cross_checks = cross_check_pdf_pages(pdf1, [1])
    for cross_check in fb_cross_checks:
        cross_check["page_label"] = "FB2FB6 Page 1"
    fb_balloon = integrate_balloon_cross_checks(fb_cross_checks, erp_parts, fb_results)
    for cross_check in fb_balloon["image_cross_checks"]:
        print(
            f"  Page 1: image=[{format_number_list(cross_check['balloon_numbers'])}] | "
            f"table=[{format_number_list(cross_check['table_item_numbers'])}] | "
            f"image_only=[{format_number_list(cross_check['image_only'])}] | "
            f"table_only=[{format_number_list(cross_check['table_only'])}] | "
            f"match={cross_check['match_count']} | status={cross_check['status']}"
        )
    for alert in fb_balloon["alerts"]:
        print(f"  {alert['severity']:<8s} {alert['detail']}")

    print("\n[2번 자료] GVU 스키드 — SN 자동 검증")
    sn_validation = validate_pdf_sn_consistency(pdf2)
    print(f"  예상 SN: {sn_validation['expected_sn']}")
    for section in sn_validation["sections"]:
        detected = ", ".join(section["detected_sns"]) or "-"
        icon = "✅" if section["status"] == "ok" else "⚠️"
        print(f"  {icon} {section['section']:<6s} ({section['page_range']}): {detected}")

    print("\n[2번 자료] GVU 스키드 — Part List 파싱")
    part_list = parse_gvu_part_list(xlsx_part_list)
    gvu_erp_parts = parse_erp_bom(xlsx_gvu_erp)
    referenced_sns = ", ".join(part_list["referenced_sns"])
    print(f"  VALVE LIST: {len(part_list['valves'])}개")
    print(f"  SENSOR LIST: {len(part_list['sensors'])}개")
    print(f"  Fitting LIST: {len(part_list['fittings'])}개")
    print(f"  Part List Doc No.: {part_list['doc_no']}")
    print(f"  Part List 참조 SN: {referenced_sns}")
    print(f"  ERP BOM(.1): {len(gvu_erp_parts)}개")

    print("\n[2번 자료] GVU 스키드 — Fitting List vs ERP BOM")
    fitting_erp_parts = select_relevant_erp_parts(part_list["fittings"], gvu_erp_parts)
    fitting_results = compare_parts(part_list["fittings"], fitting_erp_parts, code_key="part_code")
    fitting_counts = summarize_results(fitting_results)
    print(f"  Fitting List: {len(part_list['fittings'])}개 (코드 기준 집계)")
    print(f"  ERP BOM(관련 후보): {len(fitting_erp_parts)}개")
    print(f"  결과: {counts_text(fitting_counts)}")
    print_result_lines(fitting_results, code_key="part_code")

    print("\n[2번 자료] GVU 스키드 — VD 밸브 상세도")
    vd_pages = collect_vd_pages(pdf2)
    for page in vd_pages:
        total = len(page["parts"])
        merged = page["merged_count"]
        tag_text = page["tag_text"] or "-"
        status = "✅" if page["has_table"] else "❌"
        if page["has_table"]:
            detail = f"{total}개" if merged == 0 else f"{total}개 (병합셀 {merged}개 복원)"
        else:
            detail = "Description 테이블 미발견"
        print(f"  {status} Page {page['page']:2d}: TAG={tag_text:<8s} | SN={page['sn'] or '-':<6s} | {detail}")

    gvu_results = []
    gvu_skip_reason = ""
    if should_skip_vd_matching(sn_validation):
        vd_section = next(
            (section for section in sn_validation["sections"] if section["section"] == "VD"),
            {},
        )
        detected_sn = vd_section.get("representative_sn", "UNKNOWN")
        expected_sn = sn_validation.get("expected_sn", "UNKNOWN")
        gvu_skip_reason = f"VD 섹션 SN {detected_sn} != 예상 SN {expected_sn} -> VD-ERP 매칭 스킵"
        print(f"  ⚠️ {gvu_skip_reason}")
    else:
        print("\n[2번 자료] GVU 스키드 — VD TAG -> Part List -> ERP BOM")
        gvu_results = compare_gvu_parts(vd_pages, part_list["valves"], gvu_erp_parts)
        gvu_counts = summarize_results(gvu_results)
        print(f"  결과: {counts_text(gvu_counts)}")
        print_result_lines(gvu_results, code_key="part_code")

    print("\n[2번 자료] GVU 스키드 — Balloon vs Description NO.")
    vd_cross_checks = cross_check_pdf_pages(pdf2, [page["page"] for page in vd_pages])
    for cross_check in vd_cross_checks:
        cross_check["page_label"] = f"GVU VD Page {cross_check['page']}"
    gvu_balloon = integrate_balloon_cross_checks(vd_cross_checks, gvu_erp_parts, gvu_results)
    for cross_check in gvu_balloon["image_cross_checks"]:
        print(
            f"  Page {cross_check['page']:2d}: image=[{format_number_list(cross_check['balloon_numbers'])}] | "
            f"table=[{format_number_list(cross_check['table_item_numbers'])}] | "
            f"image_only=[{format_number_list(cross_check['image_only'])}] | "
            f"table_only=[{format_number_list(cross_check['table_only'])}] | "
            f"match={cross_check['match_count']} | status={cross_check['status']}"
        )
    for alert in gvu_balloon["alerts"]:
        print(f"  {alert['severity']:<8s} {alert['detail']}")

    print("\n[2번 자료] GVU 스키드 — ITDRA 계장기기도")
    doc = fitz.open(pdf2)
    try:
        for page_num in range(16, 23):
            spec = parse_itdra_page(doc, page_num)
            print(
                f"  Page {page_num} (ITDRA-{page_num - 15:02d}): "
                f"Tag={spec.get('tag_no', '?')}, "
                f"Maker={spec.get('Maker', '?')}, "
                f"Drawing={spec.get('drawing_no', '?')}, "
                f"부품={len(spec.get('parts', []))}개"
            )
    finally:
        doc.close()

    report_notes = []
    if referenced_sns:
        report_notes.append(f"Part List refs={referenced_sns}")
    if gvu_skip_reason:
        report_notes.append(gvu_skip_reason)

    summary_rows = [
        summary_row(
            "FB2FB6",
            fb_results,
            notes=f"동의어 사전 {fb_counts['synonym']}건" if fb_counts["synonym"] else "",
        ),
        summary_row(
            "GVU-Fitting",
            fitting_results,
            notes=f"관련 ERP 후보 {len(fitting_erp_parts)}건",
        ),
        summary_row(
            "GVU-VD",
            gvu_results,
            status="skipped" if gvu_skip_reason else "ok",
            notes=" / ".join(report_notes),
        ),
    ]
    detail_rows = build_detail_rows(fb_results, gvu_results, gvu_skip_reason, fitting_results=fitting_results)
    detail_rows.extend(fb_balloon["detail_rows"])
    detail_rows.extend(gvu_balloon["detail_rows"])
    image_cross_checks = fb_balloon["image_cross_checks"] + gvu_balloon["image_cross_checks"]
    report_path = os.path.join(base_dir, "BMT_BOM_verification_report.xlsx")
    write_comparison_report(
        report_path,
        summary_rows,
        detail_rows,
        sn_validation,
        image_cross_checks=image_cross_checks,
    )
    print(f"\n[리포트] {report_path}")

    return fb_results


if __name__ == "__main__":
    base_dir = os.path.join(os.path.dirname(__file__), "..", "도면&BOM AI검증 솔루션 관련 자료")
    run_pipeline(base_dir)
