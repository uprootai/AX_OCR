"""
DSE Bearing Parser — Title Block Parser

OCR 결과에서 Title Block 정보(도면번호, Rev, 품명, 재질, 날짜 등)를 추출한다.
"""

import re
import logging
from typing import Dict, Any, List

from .models import TitleBlockData
from .constants import (
    DRAWING_NUMBER_PATTERNS,
    REVISION_PATTERNS,
    MATERIAL_PATTERNS,
    PART_NAME_KEYWORDS,
    DATE_PATTERNS,
)

logger = logging.getLogger(__name__)


def parse_title_block(ocr_texts: List[Dict[str, Any]]) -> TitleBlockData:
    """
    OCR 결과에서 Title Block 정보 추출

    Args:
        ocr_texts: eDOCr2 OCR 결과 리스트 [{"text": "...", "bbox": [...], ...}, ...]

    Returns:
        TitleBlockData: 파싱된 Title Block 정보
    """
    result = TitleBlockData()
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

    result.raw_texts = all_texts
    combined_text = " ".join(all_texts)

    result.drawing_number = _extract_drawing_number(all_texts, combined_text)
    result.revision = _extract_revision(all_texts, combined_text)
    result.part_name = _extract_part_name(all_texts, combined_text)
    result.material = _extract_material(all_texts, combined_text)
    result.date = _extract_date(all_texts, combined_text)
    _extract_misc_info(result, all_texts, combined_text)

    logger.info(f"Title Block 파싱 완료: {result.drawing_number}, Rev.{result.revision}")
    return result


def _extract_drawing_number(texts: List[str], combined: str) -> str:
    """도면번호 추출"""
    for pattern in DRAWING_NUMBER_PATTERNS:
        for text in texts:
            match = re.search(pattern, text.upper())
            if match:
                return match.group(0)

        match = re.search(pattern, combined.upper())
        if match:
            return match.group(0)

    return ""


def _extract_revision(texts: List[str], combined: str) -> str:
    """Rev 추출"""
    for pattern in REVISION_PATTERNS:
        for text in texts:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        match = re.search(pattern, combined, re.IGNORECASE)
        if match:
            return match.group(1)

    # 단독 A, B, C, D 등 (Rev 옆에 있는 경우)
    for i, text in enumerate(texts):
        if "REV" in text.upper() and i + 1 < len(texts):
            next_text = texts[i + 1].strip()
            if len(next_text) == 1 and next_text.isalpha():
                return next_text.upper()

    return ""


def _extract_part_name(texts: List[str], combined: str) -> str:
    """품명 추출"""
    best_match = ""
    best_score = 0

    for text in texts:
        upper_text = text.upper()
        score = sum(1 for kw in PART_NAME_KEYWORDS if kw in upper_text)
        if score > best_score and len(text) > 5:
            best_score = score
            best_match = text

    if not best_match:
        for text in texts:
            if any(kw in text.upper() for kw in ["BEARING", "RING", "CASING", "ASSY"]):
                best_match = text
                break

    return best_match.strip()


def _normalize_ocr_text(text: str) -> str:
    """OCR 오류 보정 (일반적인 문자 혼동 수정)"""
    normalized = text
    # SF 다음에 오는 O를 0으로
    normalized = re.sub(r"(SF[A-Z]?)([O0]+)([O0A-Z]*)",
                      lambda m: m.group(1).replace('A', '') +
                               m.group(2).replace('O', '0') +
                               m.group(3).replace('O', '0'),
                      normalized)
    # SFA로 시작하면 SF로 보정 (SFA40A → SF440A)
    normalized = re.sub(r"SFA(\d)", r"SF4\1", normalized)
    return normalized


def _extract_material(texts: List[str], combined: str) -> str:
    """재질 추출 (OCR 오류 보정 포함)"""
    materials = []

    normalized_texts = [_normalize_ocr_text(t.upper()) for t in texts]
    normalized_combined = _normalize_ocr_text(combined.upper())

    for pattern in MATERIAL_PATTERNS:
        for text in texts:
            matches = re.findall(pattern, text.upper())
            materials.extend(matches)

        matches = re.findall(pattern, combined.upper())
        materials.extend(matches)

        for text in normalized_texts:
            matches = re.findall(pattern, text)
            materials.extend(matches)

        matches = re.findall(pattern, normalized_combined)
        materials.extend(matches)

    # 추가 패턴: OCR 오류 변형 (SFA40A, SFA4OA 등)
    ocr_error_patterns = [
        r"SFA\d{1,2}[O0]?[A-Z]?",  # SFA40A, SFA4OA
        r"SF[O0]\d{1,2}[A-Z]?",    # SF04A (잘못된 순서)
    ]
    for pattern in ocr_error_patterns:
        matches = re.findall(pattern, combined.upper())
        for match in matches:
            corrected = match.replace('O', '0')
            if corrected.startswith('SFA'):
                corrected = 'SF4' + corrected[3:]
            materials.append(corrected)

    materials = list(set(materials))

    if materials:
        for mat in materials:
            if mat.startswith("SF") and any(c.isdigit() for c in mat):
                return mat
        return materials[0]

    return ""


def _extract_date(texts: List[str], combined: str) -> str:
    """날짜 추출"""
    for pattern in DATE_PATTERNS:
        for text in texts:
            match = re.search(pattern, text)
            if match:
                return match.group(0)

        match = re.search(pattern, combined)
        if match:
            return match.group(0)

    return ""


def _extract_misc_info(result: TitleBlockData, texts: List[str], combined: str):
    """기타 정보 추출 (크기, Scale, Sheet 등)"""
    # Size (A1, A2, A3, A4 등)
    size_match = re.search(r"\b(A[0-4])\b", combined)
    if size_match:
        result.size = size_match.group(1)

    # Scale
    scale_patterns = [
        r"SCALE[:\s]*([\d:]+|N/?S)",
        r"Scale[:\s]*([\d:]+|N/?S)",
        r"(\d+:\d+)",
    ]
    for pattern in scale_patterns:
        match = re.search(pattern, combined, re.IGNORECASE)
        if match:
            result.scale = match.group(1)
            break

    # Sheet
    sheet_match = re.search(r"(\d+)/(\d+)\s*(?:SHEET|sheet)?", combined)
    if sheet_match:
        result.sheet = f"{sheet_match.group(1)}/{sheet_match.group(2)}"

    # Company
    company_keywords = ["DOOSAN", "DSE", "ENERBILITY"]
    for kw in company_keywords:
        if kw in combined.upper():
            result.company = "DOOSAN Enerbility"
            break
