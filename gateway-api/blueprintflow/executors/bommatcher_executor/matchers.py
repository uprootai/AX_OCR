"""
BOM Matcher — 매칭 로직
strict / fuzzy / hybrid 매칭 전략 및 헬퍼 함수
"""
from typing import Dict, Any, List
from difflib import SequenceMatcher

from .models import BOMEntry, DrawingInfo

# 재질 정규화 매핑
MATERIAL_NORMALIZATION = {
    "SF440": "SF440A",
    "SF-440A": "SF440A",
    "SF 440A": "SF440A",
    "SS-400": "SS400",
    "SS 400": "SS400",
    "SM-490A": "SM490A",
    "SM490": "SM490A",
    "B23": "ASTM B23 GR.2",
    "ASTM B23": "ASTM B23 GR.2",
    "BABBITT": "ASTM B23 GR.2",
    "SUS-304": "SUS304",
    "SUS 304": "SUS304",
    "SCM-440": "SCM440",
    "SCM 440": "SCM440",
}


def normalize_material(material: str) -> str:
    """재질 코드 정규화"""
    if not material:
        return material

    upper = material.upper().strip()

    for key, normalized in MATERIAL_NORMALIZATION.items():
        if key.upper() == upper or key.upper() in upper:
            return normalized

    return upper


def calculate_similarity(s1: str, s2: str) -> float:
    """두 문자열의 유사도 계산 (0-1)"""
    if not s1 or not s2:
        return 0.0
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()


def extract_titleblock_data(inputs: Dict[str, Any]) -> DrawingInfo:
    """Title Block 데이터 추출"""
    titleblock = inputs.get("titleblock_data") or inputs.get("title_block", {})

    if isinstance(titleblock, dict):
        return DrawingInfo(
            drawing_number=titleblock.get("drawing_number", ""),
            revision=titleblock.get("revision", titleblock.get("rev", "")),
            title=titleblock.get("title", titleblock.get("part_name", "")),
            base_material=titleblock.get("material", ""),
            date=titleblock.get("date", ""),
            scale=titleblock.get("scale", ""),
        )

    return DrawingInfo(
        drawing_number="",
        revision="",
        title="",
    )


def extract_partslist_data(inputs: Dict[str, Any]) -> List[Dict]:
    """Parts List 데이터 추출"""
    partslist = inputs.get("partslist_data") or inputs.get("parts_list", {})

    if isinstance(partslist, dict):
        return partslist.get("parts", [])
    elif isinstance(partslist, list):
        return partslist

    # parts 키로 직접 접근
    parts = inputs.get("parts", [])
    if parts:
        return parts

    return []


def extract_dimension_data(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Dimension 데이터 추출"""
    dimension = inputs.get("dimension_data") or inputs.get("bearing_specs", {})

    if isinstance(dimension, dict):
        return dimension

    return {}


def _build_part_dimensions(dimensions: Dict[str, Any]) -> Dict[str, Any]:
    """치수 딕셔너리 생성 헬퍼"""
    return {
        "od": dimensions.get("outer_diameter"),
        "id": dimensions.get("inner_diameter"),
        "length": dimensions.get("length"),
    }


def match_strict(
    parts: List[Dict],
    dimensions: Dict[str, Any],
    validate_material: bool
) -> List[BOMEntry]:
    """정확 일치 매칭"""
    bom_entries = []

    for idx, part in enumerate(parts):
        part_no = str(part.get("no", part.get("part_no", idx + 1)))
        part_name = part.get("part_name", part.get("name", ""))
        material = part.get("material", "")
        quantity = part.get("quantity", 1)

        if validate_material:
            material = normalize_material(material)

        part_dimensions = _build_part_dimensions(dimensions) if dimensions else None

        entry = BOMEntry(
            item_no=idx + 1,
            part_no=part_no,
            part_name=part_name,
            material=material,
            quantity=quantity if isinstance(quantity, int) else 1,
            dimensions=part_dimensions,
            match_confidence=1.0,
            source="partslist",
        )
        bom_entries.append(entry)

    return bom_entries


def match_fuzzy(
    parts: List[Dict],
    dimensions: Dict[str, Any],
    yolo_detections: List[Dict],
    confidence_threshold: float
) -> List[BOMEntry]:
    """유사도 기반 매칭"""
    bom_entries = []

    for idx, part in enumerate(parts):
        part_no = str(part.get("no", part.get("part_no", idx + 1)))
        part_name = part.get("part_name", part.get("name", ""))
        material = normalize_material(part.get("material", ""))
        quantity = part.get("quantity", 1)

        best_match = None
        best_score = 0

        for detection in yolo_detections:
            label = detection.get("label", detection.get("class", ""))
            similarity = calculate_similarity(part_name, label)
            if similarity > best_score and similarity >= confidence_threshold:
                best_score = similarity
                best_match = detection

        part_dimensions = _build_part_dimensions(dimensions) if dimensions else None

        entry = BOMEntry(
            item_no=idx + 1,
            part_no=part_no,
            part_name=part_name,
            material=material,
            quantity=quantity if isinstance(quantity, int) else 1,
            dimensions=part_dimensions,
            match_confidence=best_score if best_match else 0.8,
            source="fuzzy_match" if best_match else "partslist",
        )
        bom_entries.append(entry)

    return bom_entries


def match_hybrid(
    parts: List[Dict],
    dimensions: Dict[str, Any],
    yolo_detections: List[Dict],
    validate_material: bool,
    confidence_threshold: float
) -> List[BOMEntry]:
    """하이브리드 매칭 (정확 일치 우선)"""
    strict_results = match_strict(parts, dimensions, validate_material)

    if yolo_detections:
        for entry in strict_results:
            best_match = None
            best_score = 0

            for detection in yolo_detections:
                label = detection.get("label", detection.get("class", ""))
                similarity = calculate_similarity(entry.part_name, label)
                if similarity > best_score:
                    best_score = similarity
                    best_match = detection

            if best_match and best_score >= confidence_threshold:
                entry.match_confidence = max(entry.match_confidence, best_score)
                entry.source = "hybrid_match"

    return strict_results


def validate_bom(
    bom_entries: List[BOMEntry],
    drawing_info: DrawingInfo
) -> tuple[List[str], List[str]]:
    """BOM 유효성 검사"""
    warnings = []
    unmatched = []

    for entry in bom_entries:
        if not entry.material:
            warnings.append(f"항목 {entry.item_no}: 재질 정보 없음")
        if not entry.part_name:
            warnings.append(f"항목 {entry.item_no}: 품명 정보 없음")
        if entry.match_confidence < 0.5:
            unmatched.append(f"{entry.part_no}: {entry.part_name}")

    if not drawing_info.drawing_number:
        warnings.append("도면번호 정보 없음")
    if not drawing_info.revision:
        warnings.append("리비전 정보 없음")

    return warnings, unmatched


def calculate_overall_confidence(bom_entries: List[BOMEntry]) -> float:
    """전체 매칭 신뢰도 계산"""
    if not bom_entries:
        return 0.0

    confidences = [entry.match_confidence for entry in bom_entries]
    return sum(confidences) / len(confidences)
