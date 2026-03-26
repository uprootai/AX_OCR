"""
Balloon number vs table item number cross-check helpers.
"""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Sequence, Tuple

import fitz
import pdfplumber


BBox = Tuple[float, float, float, float]
TOP_MARGIN = 40.0
BOTTOM_MARGIN = 30.0
MAX_NUMBER_DIGITS = 3
BALLOON_IMAGE_ONLY_VERDICT = "balloon_image_only"
BALLOON_TABLE_ONLY_CRITICAL_VERDICT = "balloon_table_only_critical"


def clean_text(text: object) -> str:
    return " ".join(part.strip() for part in str(text or "").splitlines() if part.strip())


def format_number_list(values: Iterable[int]) -> str:
    numbers = list(values)
    return ", ".join(str(value) for value in numbers) if numbers else "-"


def _is_digit_text(text: str) -> bool:
    return bool(re.fullmatch(rf"\d{{1,{MAX_NUMBER_DIGITS}}}", text))


def _extract_numbers(text: object) -> List[int]:
    values = []
    for token in re.findall(rf"\d{{1,{MAX_NUMBER_DIGITS}}}", str(text or "")):
        values.append(int(token))
    return values


def _unique_sorted(values: Iterable[int]) -> List[int]:
    return sorted(set(values))


def _item_number(value: object) -> int | None:
    text = clean_text(value)
    if text.isdigit():
        return int(text)
    return None


def _header_text(rows: Sequence[Sequence[object]]) -> str:
    if not rows:
        return ""
    header_rows = rows[:3]
    cells = []
    for row in header_rows:
        cells.extend(clean_text(cell) for cell in row if clean_text(cell))
    return " ".join(cells).upper()


def _is_description_table(rows: Sequence[Sequence[object]]) -> bool:
    header = _header_text(rows)
    if "DESCRIPTION" not in header:
        return False
    return any(keyword in header for keyword in ("MATERIAL", "MAT'L", "Q'TY", "QTY"))


def _is_item_header(text: object) -> bool:
    raw = clean_text(text)
    normalized = re.sub(r"[^0-9A-Z]+", "", raw.upper())
    return normalized in {"NO", "ITEM"} or raw == "항목"


def _score_number_column(rows: Sequence[Sequence[object]], col_idx: int, header_row_idx: int) -> int:
    score = 0
    for row in rows[header_row_idx + 1 :]:
        if col_idx >= len(row):
            continue
        score += len(_extract_numbers(row[col_idx]))
    return score


def extract_table_item_numbers(rows: Sequence[Sequence[object]]) -> List[int]:
    candidates: List[Tuple[int, int, int]] = []
    for row_idx, row in enumerate(rows[:5]):
        for col_idx, cell in enumerate(row):
            if not _is_item_header(cell):
                continue
            candidates.append((_score_number_column(rows, col_idx, row_idx), row_idx, col_idx))

    if not candidates:
        return []

    _, header_row_idx, col_idx = max(candidates, key=lambda item: (item[0], item[1], -item[2]))
    numbers: List[int] = []
    for row in rows[header_row_idx + 1 :]:
        if col_idx >= len(row):
            continue
        numbers.extend(_extract_numbers(row[col_idx]))
    return _unique_sorted(numbers)


def _fallback_table_bbox(page_width: float, page_height: float) -> BBox:
    return (page_width * 0.72, 0.0, page_width, page_height * 0.60)


def _collect_table_regions(page: pdfplumber.page.Page) -> Dict[str, object]:
    table_infos = []
    description_rows: List[List[object]] = []
    description_bbox: BBox | None = None

    for table in page.find_tables():
        rows = table.extract()
        bbox = tuple(float(value) for value in table.bbox)
        table_infos.append({"bbox": bbox, "rows": rows})
        if description_bbox is None and _is_description_table(rows):
            description_bbox = bbox
            description_rows = rows

    exclusion_boxes = [info["bbox"] for info in table_infos]
    source = "pdfplumber"
    if description_bbox is None:
        description_bbox = _fallback_table_bbox(page.width, page.height)
        exclusion_boxes.append(description_bbox)
        source = "heuristic_right_top"

    return {
        "description_bbox": description_bbox,
        "description_rows": description_rows,
        "exclusion_boxes": exclusion_boxes,
        "table_count": len(table_infos),
        "source": source,
    }


def _inside_any_box(point_x: float, point_y: float, boxes: Sequence[BBox]) -> bool:
    for x0, y0, x1, y1 in boxes:
        if x0 <= point_x <= x1 and y0 <= point_y <= y1:
            return True
    return False


def extract_balloon_candidates(page: fitz.Page, exclusion_boxes: Sequence[BBox]) -> List[Dict[str, object]]:
    candidates: List[Dict[str, object]] = []
    page_height = float(page.rect.height)

    for block in page.get_text("blocks"):
        x0, y0, x1, y1, text = block[:5]
        cleaned = clean_text(text)
        if not _is_digit_text(cleaned):
            continue
        if y0 < TOP_MARGIN or y1 > page_height - BOTTOM_MARGIN:
            continue

        center_x = (x0 + x1) / 2
        center_y = (y0 + y1) / 2
        if _inside_any_box(center_x, center_y, exclusion_boxes):
            continue

        candidates.append(
            {
                "value": int(cleaned),
                "text": cleaned,
                "bbox": (round(x0, 1), round(y0, 1), round(x1, 1), round(y1, 1)),
            }
        )

    return candidates


def cross_check_page(
    fitz_page: fitz.Page,
    plumber_page: pdfplumber.page.Page,
    page_number: int,
) -> Dict[str, object]:
    table_regions = _collect_table_regions(plumber_page)
    balloon_blocks = extract_balloon_candidates(fitz_page, table_regions["exclusion_boxes"])
    balloon_numbers = _unique_sorted(block["value"] for block in balloon_blocks)
    table_item_numbers = extract_table_item_numbers(table_regions["description_rows"])
    match_numbers = sorted(set(balloon_numbers) & set(table_item_numbers))
    image_only = sorted(set(balloon_numbers) - set(table_item_numbers))
    table_only = sorted(set(table_item_numbers) - set(balloon_numbers))

    if table_regions["source"] != "pdfplumber" and not table_item_numbers:
        status = "SKIP"
    elif not table_item_numbers or not balloon_numbers:
        status = "WARN"
    elif image_only or table_only:
        status = "REVIEW"
    else:
        status = "OK"

    return {
        "page": page_number,
        "page_label": f"Page {page_number}",
        "table_bbox": table_regions["description_bbox"],
        "table_bbox_source": table_regions["source"],
        "table_count": table_regions["table_count"],
        "balloon_numbers": balloon_numbers,
        "balloon_blocks": balloon_blocks,
        "table_item_numbers": table_item_numbers,
        "image_only": image_only,
        "table_only": table_only,
        "match_numbers": match_numbers,
        "match_count": len(match_numbers),
        "status": status,
    }


def cross_check_pdf_pages(pdf_path: str, page_numbers: Sequence[int]) -> List[Dict[str, object]]:
    results: List[Dict[str, object]] = []
    fitz_doc = fitz.open(pdf_path)
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_number in page_numbers:
                results.append(
                    cross_check_page(
                        fitz_page=fitz_doc[page_number - 1],
                        plumber_page=pdf.pages[page_number - 1],
                        page_number=page_number,
                    )
                )
    finally:
        fitz_doc.close()
    return results


def _erp_item_index(erp_parts: Sequence[Dict[str, object]]) -> Dict[int, List[Dict[str, object]]]:
    index: Dict[int, List[Dict[str, object]]] = {}
    for erp_part in erp_parts:
        item_no = _item_number(erp_part.get("item_no"))
        if item_no is None:
            continue
        index.setdefault(item_no, []).append(erp_part)
    return index


def _compare_result_index(compare_results: Sequence[Dict[str, object]]) -> Dict[int, Dict[str, object]]:
    index: Dict[int, Dict[str, object]] = {}
    for result in compare_results:
        drawing = result.get("drawing") or {}
        item_no = _item_number(drawing.get("no"))
        if item_no is None:
            continue
        index[item_no] = result
    return index


def _erp_code_text(erp_parts: Sequence[Dict[str, object]]) -> str:
    codes = [str(erp_part.get("code", "")).strip() for erp_part in erp_parts if str(erp_part.get("code", "")).strip()]
    return ", ".join(codes)


def _balloon_detail_row(
    page_label: str,
    entry_label: str,
    verdict: str,
    severity: str,
    detail: str,
    erp_item: str = "",
    part_list_code: str = "",
    drawing_qty: object = "",
    erp_qty: object = "",
) -> Dict[str, object]:
    return {
        "dataset": "Balloon",
        "section": "Image Cross-Check",
        "page": page_label,
        "drawing_part_no": entry_label,
        "part_list_code": part_list_code,
        "part_list_drawing_no": "",
        "erp_child_item": erp_item,
        "drawing_qty": drawing_qty,
        "erp_qty": erp_qty,
        "qty_compare": "n/a",
        "verdict": verdict,
        "severity": severity,
        "detail": detail,
        "review_status": "미확인",
        "reviewer": "",
        "comment": "",
    }


def _resolve_status(row: Dict[str, object]) -> str:
    if row.get("status") == "SKIP":
        return "SKIP"
    if row.get("image_only_missing_bom") or row.get("table_only_critical"):
        return "CRITICAL"
    if row.get("image_only_in_bom"):
        return "WARN"
    if row.get("table_only"):
        return "REVIEW"
    if row.get("image_only"):
        return "WARN"
    return "OK"


def integrate_balloon_cross_checks(
    cross_checks: Sequence[Dict[str, object]],
    erp_parts: Sequence[Dict[str, object]],
    compare_results: Sequence[Dict[str, object]] | None = None,
) -> Dict[str, object]:
    erp_index = _erp_item_index(erp_parts)
    compare_index = _compare_result_index(compare_results or [])
    detail_rows: List[Dict[str, object]] = []
    alerts: List[Dict[str, object]] = []
    image_cross_checks: List[Dict[str, object]] = []

    for cross_check in cross_checks:
        enriched = dict(cross_check)
        page_label = str(enriched.get("page_label") or enriched.get("page") or "")
        image_only_in_bom: List[int] = []
        image_only_missing_bom: List[int] = []
        table_only_critical: List[int] = []
        row_alerts: List[Dict[str, object]] = []

        for number in enriched.get("image_only", []):
            erp_matches = erp_index.get(number, [])
            erp_codes = _erp_code_text(erp_matches)
            if erp_matches:
                image_only_in_bom.append(number)
                severity = "WARN"
                detail = f"{page_label} Balloon {number}: 도면에 Balloon 있고 BOM에도 있지만 부품리스트 테이블에 누락"
                if erp_codes:
                    detail = f"{detail} (ERP: {erp_codes})"
            else:
                image_only_missing_bom.append(number)
                severity = "CRITICAL"
                detail = f"{page_label} Balloon {number}: 도면에 Balloon 있지만 어디에도 등록 안 됨"

            row = _balloon_detail_row(
                page_label=page_label,
                entry_label=f"Balloon {number}",
                verdict=BALLOON_IMAGE_ONLY_VERDICT,
                severity=severity,
                detail=detail,
                erp_item=erp_codes,
            )
            alert = {"severity": severity, "page": page_label, "number": number, "detail": detail}
            detail_rows.append(row)
            alerts.append(alert)
            row_alerts.append(alert)

        for number in enriched.get("table_only", []):
            erp_matches = erp_index.get(number, [])
            compare_result = compare_index.get(number)
            is_drawing_only = bool(compare_result and compare_result.get("type") == "drawing_only")
            if erp_matches and not is_drawing_only:
                continue

            table_only_critical.append(number)
            compare_drawing = compare_result.get("drawing") if compare_result else {}
            part_list_code = str((compare_drawing or {}).get("part_code", "")).strip()
            drawing_qty = (compare_drawing or {}).get("qty", "")
            erp_codes = _erp_code_text(erp_matches)
            reason = f"{page_label} Table NO {number}: 부품리스트 테이블에는 있으나 도면 Balloon 없음"
            if not erp_matches:
                reason = f"{reason}, ERP BOM에도 대응 항목 없음"
            if is_drawing_only:
                reason = f"{reason}, BOM 비교 결과 drawing_only"

            row = _balloon_detail_row(
                page_label=page_label,
                entry_label=f"Table NO {number}",
                verdict=BALLOON_TABLE_ONLY_CRITICAL_VERDICT,
                severity="CRITICAL",
                detail=reason,
                erp_item=erp_codes,
                part_list_code=part_list_code,
                drawing_qty=drawing_qty,
            )
            alert = {"severity": "CRITICAL", "page": page_label, "number": number, "detail": reason}
            detail_rows.append(row)
            alerts.append(alert)
            row_alerts.append(alert)

        enriched["image_only_in_bom"] = image_only_in_bom
        enriched["image_only_missing_bom"] = image_only_missing_bom
        enriched["table_only_critical"] = table_only_critical
        enriched["alerts"] = row_alerts
        enriched["status"] = _resolve_status(enriched)
        image_cross_checks.append(enriched)

    return {
        "image_cross_checks": image_cross_checks,
        "detail_rows": detail_rows,
        "alerts": alerts,
    }
