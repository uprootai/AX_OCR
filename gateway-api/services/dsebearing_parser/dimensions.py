"""
DSE Bearing Parser — Dimension Extractor

OCR 결과에서 치수(ISO 공차, 대칭/비대칭 공차, 직경, 나사, 각도,
표면 거칠기 등)를 추출한다.
"""

import re
import logging
from typing import Dict, Any, List, Optional

from .constants import ISO_TOLERANCE_GRADES, SURFACE_ROUGHNESS

logger = logging.getLogger(__name__)

# 확장된 치수 패턴 (우선순위 순)
DIMENSION_PATTERNS = [
    # 1. 나사 (M12x1.5, M16-2, M20×2.5)
    (r"M(\d+\.?\d*)\s*[xX×-]\s*(\d+\.?\d*)", "thread"),
    # 2. 나사 단독 (M12, M16)
    (r"M(\d+)(?![xX×\d])", "thread_single"),
    # 3. ISO 공차 직경 (Ø450H7, φ120h6)
    (r"[ØφΦ⌀]\s*(\d+\.?\d*)\s*([A-Za-z])(\d{1,2})", "iso_diameter"),
    # 4. ISO 공차 선형 (120H7, 50g6) - x, X 제외 (나사와 구분)
    (r"(\d+\.?\d*)\s*([A-WYZa-wyz])(\d{1,2})(?![A-Za-z])", "iso_linear"),
    # 5. 베어링 OD×ID (OD 450 × ID 300)
    (r"OD\s*(\d+\.?\d*)\s*[×xX]\s*ID\s*(\d+\.?\d*)", "bearing_od_id"),
    # 6. 비대칭 공차 - 상하 분리 (120+0.025/-0.000, 50 +0.1 -0.05)
    (r"(\d+\.?\d*)\s*\+\s*(\d+\.?\d*)\s*/?\s*-\s*(\d+\.?\d*)", "asymmetric_tolerance"),
    # 7. 비대칭 공차 - 분수 형태
    (r"(\d+\.?\d*)\s*\(\s*\+\s*(\d+\.?\d*)\s*/\s*-\s*(\d+\.?\d*)\s*\)", "asymmetric_bracket"),
    # 8. 대칭 공차 (120±0.05, 450 ± 0.1)
    (r"(\d+\.?\d*)\s*[±]\s*(\d+\.?\d*)", "symmetric_tolerance"),
    # 9. 직경 단독 (Ø450, φ120)
    (r"[ØφΦ⌀]\s*(\d+\.?\d*)", "diameter"),
    # 10. 각도 분초 (30°15'30")
    (r"(\d+)[°]\s*(\d+)[′']\s*(\d+)?[″\"]?", "angle_dms"),
    # 11. 각도 단순 (45°, 90°)
    (r"(\d+\.?\d*)[°]", "angle"),
    # 12. 표면 거칠기 Ra (Ra 0.8, Ra0.4)
    (r"Ra\s*(\d+\.?\d*)", "roughness_ra"),
    # 13. 표면 거칠기 Rz (Rz 3.2)
    (r"Rz\s*(\d+\.?\d*)", "roughness_rz"),
    # 14. 표면 거칠기 N등급 (N6, N7)
    (r"\b(N\d{1,2})\b", "roughness_n"),
    # 15. 반경 (R10, R5.5)
    (r"R(\d+\.?\d*)(?![aAzZ])", "radius"),
    # 16. 챔퍼 (C2, C1.5, 2×45°)
    (r"C(\d+\.?\d*)", "chamfer"),
    (r"(\d+\.?\d*)\s*[×xX]\s*45[°]", "chamfer_angle"),
    # 17. 일반 선형 치수 (120, 450.5) - 마지막에 배치
    (r"(\d{2,4}\.?\d*)\b", "linear"),
]

# 치수 중요도 정렬 (ISO 공차 > 베어링 > 기타)
PRIORITY_ORDER = {
    "iso_diameter": 1, "iso_linear": 2, "bearing_od_id": 3,
    "asymmetric_tolerance": 4, "asymmetric_bracket": 4,
    "symmetric_tolerance": 5, "diameter": 6, "thread": 7,
    "angle": 8, "roughness_ra": 9, "linear": 10
}


def extract_dimensions(ocr_texts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    OCR 결과에서 주요 치수 추출 (복합 치수 지원)

    지원 패턴:
    - ISO 공차 (Ø450H7, 120h6, 50g6)
    - 대칭 공차 (120±0.05)
    - 비대칭 공차 (120+0.025/-0.000, 50 +0.1 -0.05)
    - 직경 (Ø450, φ120)
    - 나사 (M12x1.5, M16-2)
    - 각도 (45°, 30°15')
    - 표면 거칠기 (Ra 0.8, Rz 3.2, N6)
    - 베어링 OD×ID

    Args:
        ocr_texts: eDOCr2 OCR 결과

    Returns:
        치수 정보 리스트
    """
    dimensions = []
    all_texts = []

    for item in ocr_texts:
        if isinstance(item, dict):
            text = item.get("text", "")
            bbox = item.get("bbox", [])
            confidence = item.get("confidence", 1.0)
        elif isinstance(item, str):
            text = item
            bbox = []
            confidence = 1.0
        else:
            continue
        if text:
            all_texts.append({"text": text.strip(), "bbox": bbox, "confidence": confidence})

    seen_texts: set = set()

    for item in all_texts:
        text = item["text"]
        bbox = item.get("bbox", [])
        confidence = item.get("confidence", 1.0)

        if text in seen_texts:
            continue

        for pattern, dim_type in DIMENSION_PATTERNS:
            match = re.search(pattern, text)
            if match:
                dim_data = _parse_dimension_match(match, dim_type, text, bbox, confidence)
                if dim_data:
                    dimensions.append(dim_data)
                    seen_texts.add(text)
                    break

    dimensions.sort(key=lambda x: PRIORITY_ORDER.get(x.get("type", ""), 99))

    logger.info(f"Dimension 파싱 완료: {len(dimensions)}개 치수")
    return dimensions


def _parse_dimension_match(
    match,
    dim_type: str,
    raw_text: str,
    bbox: List,
    confidence: float,
) -> Optional[Dict[str, Any]]:
    """치수 매칭 결과를 구조화된 데이터로 변환"""
    dim_data: Dict[str, Any] = {
        "raw_text": raw_text,
        "type": dim_type,
        "bbox": bbox,
        "confidence": confidence,
        "unit": "mm",
    }

    try:
        if dim_type == "iso_diameter":
            value = float(match.group(1))
            grade_letter = match.group(2)
            grade_number = match.group(3)
            grade_key = f"{grade_letter}{grade_number}"

            dim_data["value"] = value
            dim_data["iso_grade"] = grade_key

            if grade_key in ISO_TOLERANCE_GRADES:
                tol = ISO_TOLERANCE_GRADES[grade_key]
                dim_data["upper_tolerance"] = tol["upper"]
                dim_data["lower_tolerance"] = tol["lower"]
                dim_data["fit_type"] = _get_fit_type(grade_letter)

        elif dim_type == "iso_linear":
            value = float(match.group(1))
            grade_letter = match.group(2)
            grade_number = match.group(3)
            grade_key = f"{grade_letter}{grade_number}"

            dim_data["value"] = value
            dim_data["iso_grade"] = grade_key

            if grade_key in ISO_TOLERANCE_GRADES:
                tol = ISO_TOLERANCE_GRADES[grade_key]
                dim_data["upper_tolerance"] = tol["upper"]
                dim_data["lower_tolerance"] = tol["lower"]

        elif dim_type == "bearing_od_id":
            dim_data["outer_diameter"] = float(match.group(1))
            dim_data["inner_diameter"] = float(match.group(2))
            dim_data["value"] = dim_data["outer_diameter"]

        elif dim_type in ["asymmetric_tolerance", "asymmetric_bracket"]:
            dim_data["value"] = float(match.group(1))
            dim_data["upper_tolerance"] = float(match.group(2))
            dim_data["lower_tolerance"] = -float(match.group(3))

        elif dim_type == "symmetric_tolerance":
            dim_data["value"] = float(match.group(1))
            tol_value = float(match.group(2))
            dim_data["upper_tolerance"] = tol_value
            dim_data["lower_tolerance"] = -tol_value
            dim_data["tolerance_value"] = tol_value

        elif dim_type == "diameter":
            dim_data["value"] = float(match.group(1))

        elif dim_type == "thread":
            dim_data["nominal_diameter"] = float(match.group(1))
            dim_data["pitch"] = float(match.group(2))
            dim_data["value"] = dim_data["nominal_diameter"]

        elif dim_type == "thread_single":
            dim_data["nominal_diameter"] = float(match.group(1))
            dim_data["value"] = dim_data["nominal_diameter"]

        elif dim_type == "angle_dms":
            degrees = float(match.group(1))
            minutes = float(match.group(2))
            seconds = float(match.group(3)) if match.group(3) else 0
            dim_data["value"] = degrees + minutes / 60 + seconds / 3600
            dim_data["degrees"] = degrees
            dim_data["minutes"] = minutes
            dim_data["seconds"] = seconds
            dim_data["unit"] = "deg"

        elif dim_type == "angle":
            dim_data["value"] = float(match.group(1))
            dim_data["unit"] = "deg"

        elif dim_type == "roughness_ra":
            dim_data["value"] = float(match.group(1))
            dim_data["roughness_type"] = "Ra"
            dim_data["unit"] = "um"

        elif dim_type == "roughness_rz":
            dim_data["value"] = float(match.group(1))
            dim_data["roughness_type"] = "Rz"
            dim_data["unit"] = "um"

        elif dim_type == "roughness_n":
            n_grade = match.group(1)
            dim_data["n_grade"] = n_grade
            if n_grade in SURFACE_ROUGHNESS:
                dim_data["value"] = SURFACE_ROUGHNESS[n_grade]
                dim_data["roughness_type"] = "Ra"
                dim_data["unit"] = "um"

        elif dim_type == "radius":
            dim_data["value"] = float(match.group(1))

        elif dim_type == "chamfer":
            dim_data["value"] = float(match.group(1))

        elif dim_type == "chamfer_angle":
            dim_data["value"] = float(match.group(1))
            dim_data["angle"] = 45

        elif dim_type == "linear":
            value = float(match.group(1))
            if value < 1 or value > 10000:
                return None
            dim_data["value"] = value

        return dim_data

    except (ValueError, AttributeError) as e:
        logger.warning(f"치수 파싱 오류: {raw_text} - {e}")
        return None


def _get_fit_type(grade_letter: str) -> str:
    """ISO 공차 등급 문자로 끼워맞춤 유형 반환"""
    letter = grade_letter.upper()
    if letter in ["H", "G", "F"]:
        return "clearance"
    elif letter in ["K", "M", "N"]:
        return "transition"
    elif letter in ["P", "R", "S"]:
        return "interference"
    else:
        return "unknown"
