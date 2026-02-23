"""Region Analysis - Edge detection, mask generation, analysis functions

도면 영역 분석을 위한 독립 함수들
- 표제란 검출 (우하단 영역 분석)
- BOM 테이블 검출 (테이블 패턴 감지)
- 메인 뷰 영역 계산
- 범례 검출 (P&ID 도면용)
- 노트/주석 영역 검출
- 면적 계산 유틸리티

분리 일자: 2026-02-23
원본: region_segmenter.py
"""

import logging
from typing import Optional, List, Tuple

from PIL import Image
import numpy as np

from schemas.region import RegionType, RegionSegmentationConfig

logger = logging.getLogger(__name__)

# 영역 분할 설정 (환경변수 값은 region_segmenter.py에서 정의)
from services._region_constants import (
    TITLE_BLOCK_X_RATIO,
    TITLE_BLOCK_Y_RATIO,
    BOM_TABLE_X_RATIO,
    BOM_TABLE_Y_END_RATIO,
    LEGEND_X_END_RATIO,
    LEGEND_Y_END_RATIO,
    NOTE_X_END_RATIO,
    NOTE_Y_RATIO,
    BRIGHTNESS_THRESHOLD,
    LINE_DIFF_THRESHOLD,
    MIN_TABLE_LINES,
    VARIANCE_THRESHOLD,
    RegionDetectionResult,
)


def detect_regions_heuristic(
    image: Image.Image,
    width: int,
    height: int,
    config: RegionSegmentationConfig,
    title_block_hints: dict,
    bom_table_hints: dict,
) -> List[RegionDetectionResult]:
    """휴리스틱 기반 영역 검출"""
    regions = []
    min_area = config.min_region_area * width * height

    # 1. 표제란 검출 (우하단)
    if config.detect_title_block:
        title_block = detect_title_block(image, width, height)
        if title_block and get_area(title_block.bbox) >= min_area:
            regions.append(title_block)

    # 2. BOM 테이블 검출
    if config.detect_bom_table:
        bom_table = detect_bom_table(image, width, height)
        if bom_table and get_area(bom_table.bbox) >= min_area:
            regions.append(bom_table)

    # 3. 메인 뷰 (나머지 영역)
    main_view = detect_main_view(width, height, regions)
    if main_view and get_area(main_view.bbox) >= min_area:
        regions.append(main_view)

    # 4. 범례 검출 (P&ID 도면용)
    if config.detect_legend:
        legend = detect_legend(image, width, height)
        if legend and get_area(legend.bbox) >= min_area:
            regions.append(legend)

    # 5. 노트/주석 영역 검출
    if config.detect_notes:
        notes = detect_notes(image, width, height)
        for note in notes:
            if get_area(note.bbox) >= min_area:
                regions.append(note)

    return regions


def detect_title_block(
    image: Image.Image,
    width: int,
    height: int
) -> Optional[RegionDetectionResult]:
    """표제란 검출 (우하단 영역 분석)"""
    # 일반적인 표제란 위치: 우하단 30% x 20% 영역
    # 또는 하단 전체 15% 영역

    # 방법 1: 고정 비율 기반 (환경변수로 커스터마이징 가능)
    x1 = int(width * TITLE_BLOCK_X_RATIO)
    y1 = int(height * TITLE_BLOCK_Y_RATIO)
    x2 = width
    y2 = height

    # 이미지 분석으로 실제 경계 찾기 (간단한 엣지 검출)
    try:
        # PIL을 numpy로 변환
        img_array = np.array(image.convert('L'))

        # 우하단 영역 분석
        region = img_array[y1:y2, x1:x2]

        # 수평/수직 라인 검출로 표제란 경계 확인
        # 간단한 휴리스틱: 평균 밝기가 주변과 다르면 표제란으로 판단
        avg_brightness = np.mean(region)
        main_brightness = np.mean(img_array[:y1, :x1])

        if abs(avg_brightness - main_brightness) > BRIGHTNESS_THRESHOLD:  # 밝기 차이가 있으면
            return RegionDetectionResult(
                region_type=RegionType.TITLE_BLOCK,
                bbox=(x1, y1, x2, y2),
                confidence=0.8,
                source="heuristic"
            )
    except Exception:
        pass

    # 기본 영역 반환
    return RegionDetectionResult(
        region_type=RegionType.TITLE_BLOCK,
        bbox=(x1, y1, x2, y2),
        confidence=0.6,
        source="heuristic"
    )


def detect_bom_table(
    image: Image.Image,
    width: int,
    height: int
) -> Optional[RegionDetectionResult]:
    """BOM 테이블 검출 (우상단 또는 우측)"""
    # BOM 테이블은 보통 우상단 또는 표제란 위에 위치 (환경변수로 커스터마이징 가능)
    x1 = int(width * BOM_TABLE_X_RATIO)
    y1 = 0
    x2 = width
    y2 = int(height * BOM_TABLE_Y_END_RATIO)

    try:
        img_array = np.array(image.convert('L'))
        region = img_array[y1:y2, x1:x2]

        # 테이블 패턴 감지: 수평선이 여러 개 있는지 확인
        # 간단한 휴리스틱: 수평 그래디언트 분석
        if len(region) > 0:
            row_means = np.mean(region, axis=1)
            # 급격한 변화 횟수 계산 (테이블 라인)
            diff = np.abs(np.diff(row_means))
            line_count = np.sum(diff > LINE_DIFF_THRESHOLD)

            if line_count >= MIN_TABLE_LINES:  # 최소 라인 수
                return RegionDetectionResult(
                    region_type=RegionType.BOM_TABLE,
                    bbox=(x1, y1, x2, y2),
                    confidence=0.7,
                    source="heuristic"
                )
    except Exception:
        pass

    return None


def detect_main_view(
    width: int,
    height: int,
    existing_regions: List[RegionDetectionResult]
) -> RegionDetectionResult:
    """메인 뷰 영역 계산 (다른 영역 제외)"""
    # 기본: 전체 이미지에서 표제란 영역 제외
    x1, y1 = 0, 0
    x2, y2 = width, height

    for region in existing_regions:
        if region.region_type == RegionType.TITLE_BLOCK:
            # 표제란이 우하단이면 메인 뷰는 그 위쪽
            if region.bbox[1] > height * 0.5:
                y2 = min(y2, region.bbox[1])
            # 표제란이 우측이면 메인 뷰는 그 왼쪽
            if region.bbox[0] > width * 0.5:
                x2 = min(x2, region.bbox[0])

        elif region.region_type == RegionType.BOM_TABLE:
            # BOM 테이블이 우상단이면 그 아래쪽도 제외
            if region.bbox[1] < height * 0.5 and region.bbox[0] > width * 0.5:
                pass  # 메인 뷰에 영향 없음 (우상단은 이미 작음)

    return RegionDetectionResult(
        region_type=RegionType.MAIN_VIEW,
        bbox=(x1, y1, x2, y2),
        confidence=0.9,
        source="heuristic"
    )


def detect_legend(
    image: Image.Image,
    width: int,
    height: int
) -> Optional[RegionDetectionResult]:
    """범례 검출 (P&ID 도면용)"""
    # 범례는 보통 좌상단 또는 우하단에 위치
    # 표제란과 구분하기 어려우므로 낮은 신뢰도로 반환

    # 좌상단 영역 확인 (환경변수로 커스터마이징 가능)
    x1 = 0
    y1 = 0
    x2 = int(width * LEGEND_X_END_RATIO)
    y2 = int(height * LEGEND_Y_END_RATIO)

    try:
        img_array = np.array(image.convert('L'))
        region = img_array[y1:y2, x1:x2]

        # 범례 패턴: 작은 심볼들이 반복되는 패턴
        if len(region) > 0:
            # 분산이 높으면 다양한 심볼이 있을 가능성
            variance = np.var(region)
            if variance > VARIANCE_THRESHOLD:  # 높은 분산
                return RegionDetectionResult(
                    region_type=RegionType.LEGEND,
                    bbox=(x1, y1, x2, y2),
                    confidence=0.5,
                    source="heuristic"
                )
    except Exception:
        pass

    return None


def detect_notes(
    image: Image.Image,
    width: int,
    height: int
) -> List[RegionDetectionResult]:
    """노트/주석 영역 검출"""
    notes = []

    # 일반적인 노트 위치: 좌하단 (환경변수로 커스터마이징 가능)
    x1 = 0
    y1 = int(height * NOTE_Y_RATIO)
    x2 = int(width * NOTE_X_END_RATIO)
    y2 = int(height * 0.95)

    try:
        img_array = np.array(image.convert('L'))
        region = img_array[y1:y2, x1:x2]

        if len(region) > 0:
            # 텍스트가 많은 영역: 중간 밝기 분산
            mean_val = np.mean(region)
            if 100 < mean_val < 200:  # 텍스트가 있으면 중간 밝기
                notes.append(RegionDetectionResult(
                    region_type=RegionType.NOTES,
                    bbox=(x1, y1, x2, y2),
                    confidence=0.5,
                    source="heuristic"
                ))
    except Exception:
        pass

    return notes


def get_area(
    bbox: Tuple[float, float, float, float]
) -> float:
    """영역 면적 계산"""
    return (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
