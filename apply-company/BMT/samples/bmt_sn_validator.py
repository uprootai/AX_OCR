"""
BMT PDF SN validator.

- PyMuPDF 텍스트 추출
- 페이지별 DOC No./SN 추출
- GAR / VD / ITDRA 섹션 일관성 검증
"""

from __future__ import annotations

import os
import re
from collections import Counter
from typing import Dict, List, Tuple

import fitz


SECTION_RANGES: Dict[str, Tuple[int, int]] = {
    "GAR": (1, 3),
    "VD": (4, 13),
    "ITDRA": (14, 22),
}
DOC_NO_PATTERN = re.compile(r"W5X[A-Z0-9-]*-SN\d{4}-[A-Z0-9-]+", re.IGNORECASE)
SN_PATTERN = re.compile(r"SN\d{4}", re.IGNORECASE)


def extract_sn(text: str) -> str:
    match = SN_PATTERN.search(text or "")
    return match.group(0).upper() if match else ""


def extract_doc_no(text: str) -> str:
    match = DOC_NO_PATTERN.search(text or "")
    return match.group(0).upper() if match else ""


def section_for_page(page_number: int) -> str:
    for section, (start, end) in SECTION_RANGES.items():
        if start <= page_number <= end:
            return section
    return "OTHER"


def should_skip_vd_matching(validation: Dict[str, object]) -> bool:
    for section in validation.get("sections", []):
        if section.get("section") == "VD" and section.get("status") != "ok":
            return True
    return False


def validate_pdf_sn_consistency(pdf_path: str) -> Dict[str, object]:
    """PDF 전체 페이지의 DOC No./SN 일관성 검증"""
    expected_sn = extract_sn(os.path.basename(pdf_path))
    pages: List[Dict[str, object]] = []

    doc = fitz.open(pdf_path)
    try:
        for page_index in range(doc.page_count):
            page_number = page_index + 1
            text = doc[page_index].get_text()
            doc_no = extract_doc_no(text)
            sn = extract_sn(doc_no or text)
            section = section_for_page(page_number)
            status = "ok" if sn and (not expected_sn or sn == expected_sn) else "mismatch"
            if not sn:
                status = "missing_doc_no"

            pages.append(
                {
                    "page": page_number,
                    "section": section,
                    "doc_no": doc_no,
                    "sn": sn,
                    "status": status,
                }
            )
    finally:
        doc.close()

    if not expected_sn:
        detected = [page["sn"] for page in pages if page["sn"]]
        if detected:
            expected_sn = Counter(detected).most_common(1)[0][0]

    sections: List[Dict[str, object]] = []
    mismatched_sections: List[Dict[str, object]] = []
    for section_name, (start, end) in SECTION_RANGES.items():
        section_pages = [page for page in pages if page["section"] == section_name]
        detected_sns = [page["sn"] for page in section_pages if page["sn"]]
        sn_counter = Counter(detected_sns)
        representative_sn = sn_counter.most_common(1)[0][0] if sn_counter else ""
        if not representative_sn:
            status = "missing_doc_no"
        elif len(sn_counter) > 1:
            status = "inconsistent"
        elif expected_sn and representative_sn != expected_sn:
            status = "mismatch"
        else:
            status = "ok"

        section_info = {
            "section": section_name,
            "page_range": f"{start}-{end}",
            "pages": [page["page"] for page in section_pages],
            "detected_sns": sorted(sn_counter.keys()),
            "representative_sn": representative_sn,
            "doc_numbers": sorted({page["doc_no"] for page in section_pages if page["doc_no"]}),
            "status": status,
        }
        sections.append(section_info)
        if status != "ok":
            mismatched_sections.append(section_info)

    return {
        "pdf_path": pdf_path,
        "expected_sn": expected_sn,
        "pages": pages,
        "sections": sections,
        "mismatched_sections": mismatched_sections,
        "consistent": not mismatched_sections,
    }
