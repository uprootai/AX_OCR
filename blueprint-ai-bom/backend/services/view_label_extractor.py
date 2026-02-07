"""뷰 라벨 추출 서비스

도면에서 뷰 라벨(SECTION A-A, DETAIL B, VIEW C-C 등)을 인식하고 파싱합니다.

지원 뷰 타입:
- SECTION: 단면도 (SECTION A-A, 단면 A-A)
- DETAIL: 상세도 (DETAIL B, DETAIL C SCALE 2:1)
- VIEW: 투영도 (VIEW A-A, 정면도, 측면도)
- ENLARGED: 확대도 (ENLARGED VIEW, ENLARGED DETAIL)
- AUXILIARY: 보조 투영도

추출 정보:
- 뷰 타입 (section, detail, view, enlarged, auxiliary)
- 식별자 (A-A, B, C-C 등)
- 스케일 (SCALE 2:1 등)
- 연결 정보 (절단선 위치)
"""

import re
import uuid
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple

logger = logging.getLogger(__name__)


class ViewType(str, Enum):
    """뷰 타입"""
    SECTION = "section"         # 단면도
    DETAIL = "detail"           # 상세도
    VIEW = "view"               # 일반 투영도
    ENLARGED = "enlarged"       # 확대도
    AUXILIARY = "auxiliary"     # 보조 투영도
    ISOMETRIC = "isometric"     # 등각 투영도
    FRONT = "front"             # 정면도
    SIDE = "side"               # 측면도
    TOP = "top"                 # 평면도
    BOTTOM = "bottom"           # 저면도
    UNKNOWN = "unknown"


@dataclass
class ViewLabel:
    """추출된 뷰 라벨"""
    id: str
    view_type: ViewType
    identifier: str                          # A-A, B, C 등
    scale: Optional[str] = None              # "2:1", "1:2" 등
    full_text: str = ""                      # 원본 텍스트
    bbox: Optional[List[float]] = None       # [x1, y1, x2, y2]
    confidence: float = 0.0
    source: str = "ocr"                      # ocr, regex

    # 연결 정보
    cutting_line_id: Optional[str] = None    # 연결된 절단선 ID
    cutting_line_markers: List[Dict] = field(default_factory=list)  # A, A 마커 위치


@dataclass
class ViewLabelExtractionResult:
    """뷰 라벨 추출 결과"""
    view_labels: List[ViewLabel] = field(default_factory=list)
    cutting_line_markers: List[Dict[str, Any]] = field(default_factory=list)
    total_views: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)
    processing_time_ms: float = 0.0


class ViewLabelExtractor:
    """뷰 라벨 추출기"""

    # 뷰 라벨 패턴 (영문)
    SECTION_PATTERNS = [
        r'SECTION\s+([A-Z])\s*[-–—]\s*([A-Z])',           # SECTION A-A
        r'SEC(?:TION|T)?\.?\s+([A-Z])\s*[-–—]\s*([A-Z])', # SEC. A-A, SECT A-A
        r'CROSS\s*SECTION\s+([A-Z])\s*[-–—]\s*([A-Z])',   # CROSS SECTION A-A
        r'X-SECTION\s+([A-Z])\s*[-–—]\s*([A-Z])',         # X-SECTION A-A
    ]

    DETAIL_PATTERNS = [
        r'DETAIL\s+([A-Z])\s*(?:\(?\s*SCALE\s*[:\s]*(\d+)\s*[:\s]*(\d+)\s*\)?)?',  # DETAIL A (SCALE 2:1)
        r'DET(?:AIL)?\.?\s+([A-Z])\s*(?:\(?\s*SCALE\s*[:\s]*(\d+)\s*[:\s]*(\d+)\s*\)?)?',
        r'ENLARGED\s+DETAIL\s+([A-Z])',                   # ENLARGED DETAIL A
    ]

    VIEW_PATTERNS = [
        r'VIEW\s+([A-Z])\s*[-–—]\s*([A-Z])',              # VIEW A-A
        r'VIEW\s+([A-Z])',                                 # VIEW A
        r'AUXILIARY\s+VIEW\s+([A-Z])',                     # AUXILIARY VIEW A
        r'AUX(?:ILIARY)?\.?\s+VIEW\s+([A-Z])',
    ]

    ENLARGED_PATTERNS = [
        r'ENLARGED\s+VIEW\s*(?:([A-Z]))?',                # ENLARGED VIEW A
        r'ENLARGED\s+([A-Z])',                             # ENLARGED A
        r'ENLG(?:D)?\.?\s+([A-Z])',                        # ENLGD A
    ]

    # 뷰 라벨 패턴 (한국어)
    KO_SECTION_PATTERNS = [
        r'단면\s*([A-Z])\s*[-–—]\s*([A-Z])',              # 단면 A-A
        r'단면도\s*([A-Z])\s*[-–—]\s*([A-Z])',            # 단면도 A-A
        r'절단면\s*([A-Z])\s*[-–—]\s*([A-Z])',            # 절단면 A-A
    ]

    KO_DETAIL_PATTERNS = [
        r'상세\s*([A-Z])',                                # 상세 A
        r'상세도\s*([A-Z])',                              # 상세도 A
        r'확대\s*상세\s*([A-Z])',                         # 확대 상세 A
    ]

    KO_VIEW_PATTERNS = [
        r'정면도',                                         # 정면도
        r'측면도',                                         # 측면도
        r'평면도',                                         # 평면도
        r'저면도',                                         # 저면도
        r'배면도',                                         # 배면도
        r'우측면도',                                       # 우측면도
        r'좌측면도',                                       # 좌측면도
    ]

    # 스케일 패턴
    SCALE_PATTERN = r'SCALE\s*[:\s]*(\d+)\s*[:\s]*(\d+)'
    KO_SCALE_PATTERN = r'척도\s*[:\s]*(\d+)\s*[:\s]*(\d+)'

    # 절단선 마커 패턴 (원 안에 문자)
    CUTTING_MARKER_PATTERN = r'^([A-Z])$'  # 단일 대문자

    def __init__(self):
        self.all_patterns = {
            ViewType.SECTION: self.SECTION_PATTERNS + self.KO_SECTION_PATTERNS,
            ViewType.DETAIL: self.DETAIL_PATTERNS + self.KO_DETAIL_PATTERNS,
            ViewType.VIEW: self.VIEW_PATTERNS,
            ViewType.ENLARGED: self.ENLARGED_PATTERNS,
        }

    def extract_view_labels(
        self,
        ocr_results: List[Dict[str, Any]],
        image_width: Optional[int] = None,
        image_height: Optional[int] = None,
    ) -> ViewLabelExtractionResult:
        """
        OCR 결과에서 뷰 라벨 추출

        Args:
            ocr_results: OCR 결과 목록 [{text, bbox, confidence}, ...]
            image_width: 이미지 너비 (bbox 정규화용)
            image_height: 이미지 높이

        Returns:
            ViewLabelExtractionResult
        """
        import time
        start_time = time.time()

        view_labels: List[ViewLabel] = []
        cutting_markers: List[Dict[str, Any]] = []

        for ocr in ocr_results:
            text = ocr.get("text", "").strip().upper()
            if not text or len(text) < 1:
                continue

            bbox = ocr.get("bbox")
            confidence = ocr.get("confidence", 0.5)

            # 정규화된 bbox로 변환
            norm_bbox = self._normalize_bbox(bbox, image_width, image_height)

            # 1. 뷰 라벨 매칭
            view_label = self._match_view_label(text, norm_bbox, confidence)
            if view_label:
                view_labels.append(view_label)
                continue

            # 2. 절단선 마커 매칭 (단일 대문자)
            marker = self._match_cutting_marker(text, norm_bbox, confidence)
            if marker:
                cutting_markers.append(marker)

        # 3. 한국어 투영도 이름 매칭 (정면도, 측면도 등)
        for ocr in ocr_results:
            text = ocr.get("text", "").strip()
            ko_view = self._match_korean_view(text, ocr.get("bbox"), ocr.get("confidence", 0.5))
            if ko_view:
                view_labels.append(ko_view)

        # 4. 뷰 라벨과 절단선 마커 연결
        self._link_markers_to_views(view_labels, cutting_markers)

        # 통계 계산
        by_type = {}
        for vl in view_labels:
            vtype = vl.view_type.value
            by_type[vtype] = by_type.get(vtype, 0) + 1

        processing_time = (time.time() - start_time) * 1000

        return ViewLabelExtractionResult(
            view_labels=view_labels,
            cutting_line_markers=cutting_markers,
            total_views=len(view_labels),
            by_type=by_type,
            processing_time_ms=processing_time,
        )

    def _match_view_label(
        self,
        text: str,
        bbox: Optional[List[float]],
        confidence: float
    ) -> Optional[ViewLabel]:
        """뷰 라벨 패턴 매칭"""

        for view_type, patterns in self.all_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    groups = match.groups()

                    # 식별자 추출
                    if view_type == ViewType.SECTION:
                        identifier = f"{groups[0]}-{groups[1]}" if len(groups) >= 2 else groups[0]
                    elif view_type == ViewType.DETAIL:
                        identifier = groups[0] if groups else ""
                        # 스케일 추출
                        scale = None
                        if len(groups) >= 3 and groups[1] and groups[2]:
                            scale = f"{groups[1]}:{groups[2]}"
                    else:
                        identifier = groups[0] if groups else ""

                    # 별도 스케일 패턴 매칭
                    scale = None
                    scale_match = re.search(self.SCALE_PATTERN, text, re.IGNORECASE)
                    if not scale_match:
                        scale_match = re.search(self.KO_SCALE_PATTERN, text)
                    if scale_match:
                        scale = f"{scale_match.group(1)}:{scale_match.group(2)}"

                    return ViewLabel(
                        id=f"view_{uuid.uuid4().hex[:8]}",
                        view_type=view_type,
                        identifier=identifier,
                        scale=scale,
                        full_text=text,
                        bbox=bbox,
                        confidence=confidence,
                        source="regex",
                    )

        return None

    def _match_cutting_marker(
        self,
        text: str,
        bbox: Optional[List[float]],
        confidence: float
    ) -> Optional[Dict[str, Any]]:
        """절단선 마커 매칭 (원 안의 단일 대문자)"""

        # 단일 대문자인 경우만
        if re.match(self.CUTTING_MARKER_PATTERN, text.strip()):
            return {
                "id": f"marker_{uuid.uuid4().hex[:8]}",
                "letter": text.strip(),
                "bbox": bbox,
                "confidence": confidence,
            }

        return None

    def _match_korean_view(
        self,
        text: str,
        bbox: Optional[List[float]],
        confidence: float
    ) -> Optional[ViewLabel]:
        """한국어 투영도 이름 매칭"""

        view_map = {
            "정면도": ViewType.FRONT,
            "측면도": ViewType.SIDE,
            "우측면도": ViewType.SIDE,
            "좌측면도": ViewType.SIDE,
            "평면도": ViewType.TOP,
            "저면도": ViewType.BOTTOM,
            "배면도": ViewType.VIEW,
            "등각도": ViewType.ISOMETRIC,
            "등각투상도": ViewType.ISOMETRIC,
        }

        for ko_name, view_type in view_map.items():
            if ko_name in text:
                return ViewLabel(
                    id=f"view_{uuid.uuid4().hex[:8]}",
                    view_type=view_type,
                    identifier=ko_name,
                    full_text=text,
                    bbox=self._normalize_bbox(bbox, None, None),
                    confidence=confidence,
                    source="regex",
                )

        return None

    def _link_markers_to_views(
        self,
        view_labels: List[ViewLabel],
        markers: List[Dict[str, Any]]
    ):
        """뷰 라벨과 절단선 마커 연결"""

        for vl in view_labels:
            if vl.view_type == ViewType.SECTION:
                # A-A 형식에서 A 추출
                letter = vl.identifier.split("-")[0] if "-" in vl.identifier else vl.identifier

                # 같은 문자를 가진 마커 찾기
                matching_markers = [m for m in markers if m.get("letter") == letter]

                if len(matching_markers) >= 2:
                    # 두 개의 마커가 있으면 연결
                    vl.cutting_line_markers = matching_markers[:2]
                elif len(matching_markers) == 1:
                    vl.cutting_line_markers = matching_markers

    def _normalize_bbox(
        self,
        bbox: Optional[Any],
        width: Optional[int],
        height: Optional[int]
    ) -> Optional[List[float]]:
        """bbox 정규화"""

        if bbox is None:
            return None

        # 폴리곤 형식 [[x1,y1], [x2,y2], ...] → [x_min, y_min, x_max, y_max]
        if isinstance(bbox, (list, tuple)) and len(bbox) >= 4:
            # 첫 번째 요소가 리스트/튜플이면 폴리곤 형식
            if isinstance(bbox[0], (list, tuple)):
                try:
                    xs = [p[0] for p in bbox]
                    ys = [p[1] for p in bbox]
                    bbox = [min(xs), min(ys), max(xs), max(ys)]
                except (IndexError, TypeError):
                    return None

            # [x1, y1, x2, y2] 형식 확인
            if all(isinstance(v, (int, float)) for v in bbox[:4]):
                if width and height:
                    return [
                        bbox[0] / width,
                        bbox[1] / height,
                        bbox[2] / width,
                        bbox[3] / height,
                    ]
                return list(bbox[:4])

        return None


# 싱글톤 인스턴스
view_label_extractor = ViewLabelExtractor()
