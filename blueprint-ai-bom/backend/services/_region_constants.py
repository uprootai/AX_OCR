"""Region Constants - 영역 분할 공유 상수 및 데이터클래스

region_analysis.py, region_merging.py, region_segmenter.py에서 공유하는
상수와 데이터 구조를 정의합니다.

분리 일자: 2026-02-23
원본: region_segmenter.py
"""

import os
from typing import Tuple
from dataclasses import dataclass

from schemas.region import RegionType

# 영역 분할 설정 (환경변수로 커스터마이징 가능)
TITLE_BLOCK_X_RATIO = float(os.environ.get("REGION_TITLE_BLOCK_X", "0.6"))
TITLE_BLOCK_Y_RATIO = float(os.environ.get("REGION_TITLE_BLOCK_Y", "0.8"))
BOM_TABLE_X_RATIO = float(os.environ.get("REGION_BOM_TABLE_X", "0.65"))
BOM_TABLE_Y_END_RATIO = float(os.environ.get("REGION_BOM_TABLE_Y_END", "0.35"))
LEGEND_X_END_RATIO = float(os.environ.get("REGION_LEGEND_X_END", "0.2"))
LEGEND_Y_END_RATIO = float(os.environ.get("REGION_LEGEND_Y_END", "0.3"))
NOTE_X_END_RATIO = float(os.environ.get("REGION_NOTE_X_END", "0.4"))
NOTE_Y_RATIO = float(os.environ.get("REGION_NOTE_Y", "0.75"))
BRIGHTNESS_THRESHOLD = int(os.environ.get("REGION_BRIGHTNESS_THRESHOLD", "10"))
LINE_DIFF_THRESHOLD = int(os.environ.get("REGION_LINE_DIFF_THRESHOLD", "30"))
MIN_TABLE_LINES = int(os.environ.get("REGION_MIN_TABLE_LINES", "3"))
VARIANCE_THRESHOLD = int(os.environ.get("REGION_VARIANCE_THRESHOLD", "2000"))

# DocLayout-YOLO 설정
USE_DOCLAYOUT = os.environ.get("USE_DOCLAYOUT", "true").lower() == "true"
DOCLAYOUT_FALLBACK_TO_HEURISTIC = os.environ.get("DOCLAYOUT_FALLBACK_TO_HEURISTIC", "true").lower() == "true"


@dataclass
class RegionDetectionResult:
    """내부 영역 검출 결과"""
    region_type: RegionType
    bbox: Tuple[float, float, float, float]  # x1, y1, x2, y2 in pixels
    confidence: float
    source: str = "heuristic"  # heuristic, vlm, manual
