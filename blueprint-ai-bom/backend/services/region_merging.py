"""Region Merging - Region merge, overlap calculation, deduplication

도면 영역 병합/중복 제거 로직
- DocLayout-YOLO 기반 영역 검출 (ML 기반)
- VLM 기반 영역 검출 (Phase 4 연동)
- 휴리스틱 + VLM/DocLayout 결과 병합
- IoU 기반 겹치는 영역 병합
- VLM 폴백 필요 여부 판단

분리 일자: 2026-02-23
원본: region_segmenter.py
"""

import logging
from typing import List, Tuple

from schemas.region import RegionType

logger = logging.getLogger(__name__)

from services._region_constants import RegionDetectionResult


# =========== DocLayout-YOLO 검출 ===========

def detect_regions_doclayout(
    image_path: str,
    width: int,
    height: int
) -> List[RegionDetectionResult]:
    """DocLayout-YOLO 기반 영역 검출 (ML 기반, 빠른 추론)"""
    try:
        from services.layout_analyzer import get_layout_analyzer

        analyzer = get_layout_analyzer()
        if not analyzer.is_available:
            logger.warning("[RegionSegmenter] DocLayout-YOLO 사용 불가")
            return []

        # DocLayout-YOLO 추론
        detections = analyzer.detect(image_path)

        regions = []
        for det in detections:
            # DocLayout 클래스 → RegionType 매핑
            region_type = map_doclayout_to_region_type(det.region_type)

            regions.append(RegionDetectionResult(
                region_type=region_type,
                bbox=det.bbox,
                confidence=det.confidence,
                source="doclayout"
            ))

        return regions

    except ImportError as e:
        logger.warning(f"[RegionSegmenter] layout_analyzer 모듈 없음: {e}")
        return []
    except Exception as e:
        logger.error(f"[RegionSegmenter] DocLayout-YOLO 검출 실패: {e}")
        return []


def map_doclayout_to_region_type(doclayout_type: str) -> RegionType:
    """DocLayout 클래스명을 RegionType으로 매핑"""
    mapping = {
        "TITLE_BLOCK": RegionType.TITLE_BLOCK,
        "BOM_TABLE": RegionType.BOM_TABLE,
        "MAIN_VIEW": RegionType.MAIN_VIEW,
        "NOTES": RegionType.NOTES,
        "OTHER": RegionType.UNKNOWN,
        "LEGEND": RegionType.LEGEND,
        "DETAIL_VIEW": RegionType.DETAIL_VIEW,
        "SECTION_VIEW": RegionType.SECTION_VIEW,
    }
    return mapping.get(doclayout_type, RegionType.UNKNOWN)


# =========== VLM 검출 ===========

def needs_vlm_fallback(regions: List[RegionDetectionResult]) -> bool:
    """VLM 폴백이 필요한지 확인"""
    if not regions:
        return True

    # 평균 신뢰도가 0.5 미만이면 VLM 폴백
    avg_confidence = sum(r.confidence for r in regions) / len(regions)
    if avg_confidence < 0.5:
        return True

    # 메인 뷰가 없으면 VLM 폴백
    has_main_view = any(r.region_type == RegionType.MAIN_VIEW for r in regions)
    if not has_main_view:
        return True

    return False


async def detect_regions_vlm(
    image_path: str
) -> List[RegionDetectionResult]:
    """VLM 기반 영역 검출 (Phase 4 VLMClassifier 활용)"""
    try:
        from services.vlm_classifier import vlm_classifier

        result = await vlm_classifier.classify_drawing(image_path=image_path)

        vlm_regions = []
        for region in result.regions:
            # 정규화 좌표를 픽셀 좌표로 변환
            # VLM은 정규화 좌표 반환, 여기서는 임시로 저장
            vlm_regions.append(RegionDetectionResult(
                region_type=RegionType(region.region_type.value),
                bbox=tuple(region.bbox),  # 정규화 좌표 그대로
                confidence=region.confidence,
                source="vlm"
            ))

        return vlm_regions

    except Exception as e:
        logger.error(f"[RegionSegmenter] VLM 연동 실패: {e}")
        return []


# =========== 영역 병합 ===========

def merge_regions(
    heuristic_regions: List[RegionDetectionResult],
    vlm_regions: List[RegionDetectionResult]
) -> List[RegionDetectionResult]:
    """휴리스틱과 VLM 결과 병합"""
    merged = list(heuristic_regions)

    for vlm_region in vlm_regions:
        # 같은 타입의 영역이 있는지 확인
        found = False
        for i, h_region in enumerate(merged):
            if h_region.region_type == vlm_region.region_type:
                # VLM 신뢰도가 더 높으면 교체
                if vlm_region.confidence > h_region.confidence:
                    merged[i] = vlm_region
                found = True
                break

        if not found:
            merged.append(vlm_region)

    return merged


def merge_overlapping_regions(
    regions: List[RegionDetectionResult],
    overlap_threshold: float
) -> List[RegionDetectionResult]:
    """겹치는 영역 병합"""
    if len(regions) <= 1:
        return regions

    merged = []
    used = set()

    for i, r1 in enumerate(regions):
        if i in used:
            continue

        best_region = r1
        for j, r2 in enumerate(regions):
            if i == j or j in used:
                continue

            iou = calculate_iou(r1.bbox, r2.bbox)
            if iou > overlap_threshold:
                # 신뢰도가 높은 쪽 선택
                if r2.confidence > best_region.confidence:
                    best_region = r2
                used.add(j)

        merged.append(best_region)
        used.add(i)

    return merged


def calculate_iou(
    bbox1: Tuple[float, float, float, float],
    bbox2: Tuple[float, float, float, float]
) -> float:
    """IoU 계산"""
    x1 = max(bbox1[0], bbox2[0])
    y1 = max(bbox1[1], bbox2[1])
    x2 = min(bbox1[2], bbox2[2])
    y2 = min(bbox1[3], bbox2[3])

    if x2 <= x1 or y2 <= y1:
        return 0.0

    intersection = (x2 - x1) * (y2 - y1)
    area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
    area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
    union = area1 + area2 - intersection

    return intersection / union if union > 0 else 0.0
