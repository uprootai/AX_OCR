"""치수 병합 및 IoU 로직

dimension_service.py에서 분리된 순수 함수 모듈.
멀티 엔진 가중 투표, bbox IoU 중복 제거 등.
"""
import re
import logging
from typing import List, Dict, Optional

from schemas.dimension import Dimension, DimensionType
from schemas.detection import BoundingBox

from .dimension_parser import parse_dimension_text, extract_unit

logger = logging.getLogger(__name__)

# 엔진별 기본 가중치 (OCR Ensemble merge_results 패턴)
ENGINE_BASE_WEIGHTS: Dict[str, float] = {
    "paddleocr": 0.35, "paddleocr_tiled": 0.35,
    "edocr2": 0.40,
    "easyocr": 0.25, "trocr": 0.20, "suryaocr": 0.20, "doctr": 0.25,
}

# 엔진별 치수 유형 특화 보너스
ENGINE_SPECIALTY_BONUS: Dict[str, Dict[str, float]] = {
    "edocr2": {"diameter": 0.15, "radius": 0.10, "tolerance": 0.15, "thread": 0.10},
    "paddleocr": {"length": 0.10},
    "paddleocr_tiled": {"length": 0.10},
}


def compute_iou(a: BoundingBox, b: BoundingBox) -> float:
    """두 BoundingBox의 IoU (Intersection over Union) 계산"""
    x1 = max(a.x1, b.x1)
    y1 = max(a.y1, b.y1)
    x2 = min(a.x2, b.x2)
    y2 = min(a.y2, b.y2)

    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    if intersection == 0:
        return 0.0

    area_a = max(0, a.x2 - a.x1) * max(0, a.y2 - a.y1)
    area_b = max(0, b.x2 - b.x1) * max(0, b.y2 - b.y1)
    union = area_a + area_b - intersection

    if union == 0:
        return 0.0
    return intersection / union


def get_engine_weight(model_id: str, dim_type: Optional[str] = None) -> float:
    """엔진 기본 가중치 + 치수 유형 특화 보너스 반환"""
    base = ENGINE_BASE_WEIGHTS.get(model_id, 0.10)
    if dim_type:
        bonus = ENGINE_SPECIALTY_BONUS.get(model_id, {}).get(dim_type, 0.0)
        return base + bonus
    return base


def normalize_dim_value(text: str) -> str:
    """치수 값 정규화 (비교용): Ø/φ/Φ/⌀ → ø, 공백 제거, 소문자"""
    normalized = text.strip().lower()
    normalized = re.sub(r'[ØφΦ⌀]', 'ø', normalized, flags=re.IGNORECASE)
    normalized = re.sub(r'\s+', '', normalized)
    return normalized


def merge_dimensions(
    dimensions: List[Dimension], iou_threshold: float = 0.5
) -> List[Dimension]:
    """bbox IoU 기반 중복 제거 - confidence 높은 결과 유지"""
    if not dimensions:
        return []

    sorted_dims = sorted(dimensions, key=lambda d: d.confidence, reverse=True)
    kept: List[Dimension] = []

    for dim in sorted_dims:
        is_duplicate = False
        for existing in kept:
            if compute_iou(dim.bbox, existing.bbox) > iou_threshold:
                is_duplicate = True
                break
        if not is_duplicate:
            kept.append(dim)

    return kept


def merge_multi_engine(
    dimensions: List[Dimension], iou_threshold: float = 0.5
) -> List[Dimension]:
    """멀티 엔진 가중 투표 병합 (OCR Ensemble merge_results 패턴)

    1. IoU 클러스터링  2. 값별 가중 투표  3. 최고 득점 선택
    4. 합의 보너스 (+0.05/엔진, 최대 +0.15)  5. 대표 Dimension
    """
    if not dimensions:
        return []

    used = set()
    clusters: List[List[Dimension]] = []
    for i, dim in enumerate(dimensions):
        if i in used:
            continue
        cluster = [dim]
        used.add(i)
        for j in range(i + 1, len(dimensions)):
            if j in used:
                continue
            if compute_iou(dim.bbox, dimensions[j].bbox) > iou_threshold:
                cluster.append(dimensions[j])
                used.add(j)
        clusters.append(cluster)

    merged: List[Dimension] = []
    for cluster in clusters:
        if len(cluster) == 1:
            merged.append(cluster[0])
            continue

        value_votes: Dict[str, float] = {}
        value_engines: Dict[str, List[str]] = {}
        value_original: Dict[str, str] = {}
        value_dims: Dict[str, List[Dimension]] = {}

        for dim in cluster:
            norm = normalize_dim_value(dim.raw_text)
            dt = dim.dimension_type
            dim_type_str = dt.value if hasattr(dt, 'value') else (dt if isinstance(dt, str) else None)
            weight = get_engine_weight(dim.model_id, dim_type_str)
            value_votes[norm] = value_votes.get(norm, 0.0) + weight * dim.confidence
            value_engines.setdefault(norm, []).append(dim.model_id)
            if norm not in value_original:
                value_original[norm] = dim.raw_text
            elif re.search(r'[ØφΦ⌀]', dim.raw_text) and not re.search(r'[ØφΦ⌀]', value_original[norm]):
                value_original[norm] = dim.raw_text
            value_dims.setdefault(norm, []).append(dim)

        best_norm = max(value_votes, key=lambda k: value_votes[k])
        unique_engines = set(value_engines[best_norm])
        agreement_bonus = min(len(unique_engines) * 0.05, 0.15)

        representative = max(value_dims[best_norm], key=lambda d: d.confidence)
        original_text = value_original[best_norm]
        boosted_conf = min(representative.confidence + agreement_bonus, 1.0)

        dim_type, parsed_value, tolerance = parse_dimension_text(original_text)
        result_dim = Dimension(
            id=representative.id,
            bbox=representative.bbox,
            value=parsed_value,
            raw_text=original_text,
            unit=representative.unit or extract_unit(original_text),
            tolerance=tolerance,
            dimension_type=dim_type if dim_type != DimensionType.UNKNOWN else representative.dimension_type,
            confidence=boosted_conf,
            model_id="+".join(sorted(unique_engines)),
            verification_status=representative.verification_status,
            modified_value=representative.modified_value,
            modified_bbox=representative.modified_bbox,
            linked_to=representative.linked_to,
        )
        merged.append(result_dim)

        if len(unique_engines) > 1:
            logger.debug(
                f"가중 투표: '{original_text}' 채택 "
                f"(vote={value_votes[best_norm]:.3f}, engines={list(unique_engines)})"
            )

    logger.info(f"가중 투표 병합 완료: {len(dimensions)}개 → {len(merged)}개")
    return merged
