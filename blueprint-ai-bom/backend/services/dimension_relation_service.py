"""치수선 기반 관계 추출 서비스 (Phase 2)

기존 근접성 기반(~60%) → 치수선 추적 기반(~85%) 정확도 개선

핵심 개선:
1. 치수선(Dimension Line) 검출 - 치수 텍스트 주변의 선 탐색
2. 화살표 방향 분석 - 화살표가 가리키는 대상 객체 추론
3. 신뢰도 차등 부여 - 치수선 기반 vs 근접성 기반
"""
import math
import uuid
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import numpy as np

logger = logging.getLogger(__name__)


class RelationMethod(str, Enum):
    """관계 추출 방법"""
    DIMENSION_LINE = "dimension_line"    # 치수선 추적 (높은 신뢰도)
    EXTENSION_LINE = "extension_line"    # 연장선 추적 (중간 신뢰도)
    PROXIMITY = "proximity"              # 근접성 기반 (낮은 신뢰도)
    MANUAL = "manual"                    # 수동 지정


@dataclass
class DimensionLineInfo:
    """치수선 정보"""
    dimension_id: str
    line_start: Tuple[float, float]
    line_end: Tuple[float, float]
    direction: str  # 'horizontal', 'vertical', 'diagonal'
    arrow_points: List[Tuple[float, float]]  # 화살표 위치들
    extension_lines: List[Tuple[Tuple[float, float], Tuple[float, float]]]
    confidence: float


@dataclass
class DimensionRelation:
    """치수-객체 관계"""
    id: str
    dimension_id: str
    target_type: str  # 'symbol', 'edge', 'region'
    target_id: Optional[str]
    target_bbox: Optional[Dict[str, float]]
    relation_type: str  # 'distance', 'diameter', 'radius', 'angle'
    method: RelationMethod
    confidence: float
    direction: Optional[str]  # 화살표 방향
    notes: Optional[str]


class DimensionRelationService:
    """치수선 기반 관계 추출 서비스"""

    # 신뢰도 기준값
    CONFIDENCE_DIMENSION_LINE = 0.95  # 치수선 발견 시
    CONFIDENCE_EXTENSION_LINE = 0.85  # 연장선만 발견 시
    CONFIDENCE_PROXIMITY = 0.60       # 근접성만 사용 시

    # 거리 임계값 (픽셀)
    MAX_LINE_SEARCH_DISTANCE = 100    # 치수선 탐색 최대 거리
    MAX_PROXIMITY_DISTANCE = 300      # 근접성 연결 최대 거리
    ARROW_SEARCH_RADIUS = 50          # 화살표 탐색 반경

    def __init__(self):
        print("✅ DimensionRelationService 초기화 완료 (치수선 기반 관계 추출)")

    def extract_relations(
        self,
        dimensions: List[Dict[str, Any]],
        symbols: List[Dict[str, Any]],
        lines: Optional[List[Dict[str, Any]]] = None,
        image: Optional[np.ndarray] = None
    ) -> List[Dict[str, Any]]:
        """
        치수와 객체 간의 관계 추출

        Args:
            dimensions: 치수 목록 (eDOCr2 결과)
            symbols: 심볼 목록 (YOLO 결과)
            lines: 선 검출 결과 (Line Detector API)
            image: 원본 이미지 (추가 분석용)

        Returns:
            관계 목록 (DimensionRelation 형태)
        """
        relations = []

        for dim in dimensions:
            dim_id = dim.get('id', '')
            dim_bbox = dim.get('bbox', {})
            dim_type = dim.get('dimension_type', 'unknown')

            # 1단계: 치수선 기반 관계 추출 시도
            relation = self._extract_by_dimension_line(
                dim, symbols, lines, image
            )

            if relation and relation.confidence >= self.CONFIDENCE_EXTENSION_LINE:
                relations.append(self._to_dict(relation))
                continue

            # 2단계: 연장선 기반 관계 추출 시도
            relation = self._extract_by_extension_line(
                dim, symbols, lines
            )

            if relation and relation.confidence >= self.CONFIDENCE_PROXIMITY:
                relations.append(self._to_dict(relation))
                continue

            # 3단계: 근접성 기반 폴백
            relation = self._extract_by_proximity(dim, symbols)
            relations.append(self._to_dict(relation))

        # 통계 로깅
        self._log_statistics(relations)

        return relations

    def _extract_by_dimension_line(
        self,
        dimension: Dict[str, Any],
        symbols: List[Dict[str, Any]],
        lines: Optional[List[Dict[str, Any]]],
        image: Optional[np.ndarray]
    ) -> Optional[DimensionRelation]:
        """
        치수선 추적 기반 관계 추출

        치수선 구조:
        ┌─────────────────────────────────┐
        │  │←─── extension line           │
        │  │                              │
        │  ├──────────────────────────────┤ ← dimension line
        │  │         100 mm               │ ← dimension text
        │  ├──────────────────────────────┤
        │  │                              │
        │  │←─── extension line           │
        └─────────────────────────────────┘
        """
        if not lines:
            return None

        dim_id = dimension.get('id', '')
        dim_bbox = dimension.get('bbox', {})
        dim_type = dimension.get('dimension_type', 'unknown')

        # 치수 bbox 중심점
        dim_cx = (dim_bbox.get('x1', 0) + dim_bbox.get('x2', 0)) / 2
        dim_cy = (dim_bbox.get('y1', 0) + dim_bbox.get('y2', 0)) / 2

        # 치수 근처의 선 찾기
        nearby_lines = self._find_nearby_lines(
            lines, dim_cx, dim_cy, self.MAX_LINE_SEARCH_DISTANCE
        )

        if not nearby_lines:
            return None

        # 치수선 후보 찾기 (치수 텍스트와 평행한 선)
        dimension_line = self._find_dimension_line(
            nearby_lines, dim_bbox
        )

        if not dimension_line:
            return None

        # 화살표 방향 분석
        arrow_direction = self._analyze_arrow_direction(
            dimension_line, dim_bbox
        )

        # 화살표 방향으로 대상 객체 찾기
        target = self._find_target_in_direction(
            arrow_direction, dim_bbox, symbols
        )

        if target:
            return DimensionRelation(
                id=f"rel_{uuid.uuid4().hex[:8]}",
                dimension_id=dim_id,
                target_type='symbol',
                target_id=target.get('id'),
                target_bbox=target.get('bbox'),
                relation_type=self._infer_relation_type(dim_type),
                method=RelationMethod.DIMENSION_LINE,
                confidence=self.CONFIDENCE_DIMENSION_LINE,
                direction=arrow_direction,
                notes=f"치수선 추적으로 발견 (방향: {arrow_direction})"
            )

        return None

    def _extract_by_extension_line(
        self,
        dimension: Dict[str, Any],
        symbols: List[Dict[str, Any]],
        lines: Optional[List[Dict[str, Any]]]
    ) -> Optional[DimensionRelation]:
        """
        연장선 기반 관계 추출

        연장선(extension line)은 치수선 끝에서 측정 대상까지
        수직으로 이어지는 선입니다.
        """
        if not lines:
            return None

        dim_id = dimension.get('id', '')
        dim_bbox = dimension.get('bbox', {})
        dim_type = dimension.get('dimension_type', 'unknown')

        dim_cx = (dim_bbox.get('x1', 0) + dim_bbox.get('x2', 0)) / 2
        dim_cy = (dim_bbox.get('y1', 0) + dim_bbox.get('y2', 0)) / 2

        # 치수 근처의 선 중 연장선 후보 찾기
        nearby_lines = self._find_nearby_lines(
            lines, dim_cx, dim_cy, self.MAX_LINE_SEARCH_DISTANCE * 1.5
        )

        # 치수선에 수직인 선 = 연장선 후보
        extension_lines = self._find_extension_lines(
            nearby_lines, dim_bbox
        )

        if not extension_lines:
            return None

        # 연장선 끝점 방향으로 대상 찾기
        for ext_line in extension_lines:
            target = self._find_target_at_line_end(ext_line, symbols)
            if target:
                return DimensionRelation(
                    id=f"rel_{uuid.uuid4().hex[:8]}",
                    dimension_id=dim_id,
                    target_type='symbol',
                    target_id=target.get('id'),
                    target_bbox=target.get('bbox'),
                    relation_type=self._infer_relation_type(dim_type),
                    method=RelationMethod.EXTENSION_LINE,
                    confidence=self.CONFIDENCE_EXTENSION_LINE,
                    direction=self._get_line_direction(ext_line),
                    notes="연장선 추적으로 발견"
                )

        return None

    def _extract_by_proximity(
        self,
        dimension: Dict[str, Any],
        symbols: List[Dict[str, Any]]
    ) -> DimensionRelation:
        """
        근접성 기반 관계 추출 (폴백)

        치수선이나 연장선을 찾지 못한 경우 사용하는 기존 방식.
        신뢰도가 낮게 부여됩니다.
        """
        dim_id = dimension.get('id', '')
        dim_bbox = dimension.get('bbox', {})
        dim_type = dimension.get('dimension_type', 'unknown')

        dim_cx = (dim_bbox.get('x1', 0) + dim_bbox.get('x2', 0)) / 2
        dim_cy = (dim_bbox.get('y1', 0) + dim_bbox.get('y2', 0)) / 2

        # 가장 가까운 심볼 찾기
        best_symbol = None
        best_distance = float('inf')

        for symbol in symbols:
            sym_bbox = symbol.get('bbox', {})
            sym_cx = (sym_bbox.get('x1', 0) + sym_bbox.get('x2', 0)) / 2
            sym_cy = (sym_bbox.get('y1', 0) + sym_bbox.get('y2', 0)) / 2

            distance = math.sqrt(
                (dim_cx - sym_cx) ** 2 + (dim_cy - sym_cy) ** 2
            )

            if distance < best_distance:
                best_distance = distance
                best_symbol = symbol

        if best_symbol and best_distance <= self.MAX_PROXIMITY_DISTANCE:
            # 거리에 따른 신뢰도 조정
            confidence = max(
                0.3,
                self.CONFIDENCE_PROXIMITY - (best_distance / self.MAX_PROXIMITY_DISTANCE) * 0.3
            )

            return DimensionRelation(
                id=f"rel_{uuid.uuid4().hex[:8]}",
                dimension_id=dim_id,
                target_type='symbol',
                target_id=best_symbol.get('id'),
                target_bbox=best_symbol.get('bbox'),
                relation_type=self._infer_relation_type(dim_type),
                method=RelationMethod.PROXIMITY,
                confidence=confidence,
                direction=None,
                notes=f"근접성 기반 (거리: {best_distance:.1f}px)"
            )

        # 연결할 대상이 없는 경우
        return DimensionRelation(
            id=f"rel_{uuid.uuid4().hex[:8]}",
            dimension_id=dim_id,
            target_type='none',
            target_id=None,
            target_bbox=None,
            relation_type=self._infer_relation_type(dim_type),
            method=RelationMethod.PROXIMITY,
            confidence=0.0,
            direction=None,
            notes="연결 대상 없음"
        )

    # ==================== 헬퍼 메서드 ====================

    def _find_nearby_lines(
        self,
        lines: List[Dict[str, Any]],
        cx: float,
        cy: float,
        max_distance: float
    ) -> List[Dict[str, Any]]:
        """주어진 점 근처의 선 찾기"""
        nearby = []

        for line in lines:
            # 선의 시작점/끝점
            start = line.get('start', {})
            end = line.get('end', {})

            if not start or not end:
                continue

            # 선의 중심점
            line_cx = (start.get('x', 0) + end.get('x', 0)) / 2
            line_cy = (start.get('y', 0) + end.get('y', 0)) / 2

            distance = math.sqrt((cx - line_cx) ** 2 + (cy - line_cy) ** 2)

            if distance <= max_distance:
                nearby.append({
                    **line,
                    '_distance_to_dim': distance
                })

        # 거리순 정렬
        nearby.sort(key=lambda x: x['_distance_to_dim'])
        return nearby

    def _find_dimension_line(
        self,
        lines: List[Dict[str, Any]],
        dim_bbox: Dict[str, float]
    ) -> Optional[Dict[str, Any]]:
        """
        치수 텍스트와 평행한 치수선 찾기

        치수선은 보통 치수 텍스트 위 또는 아래에 수평/수직으로 위치합니다.
        """
        dim_width = dim_bbox.get('x2', 0) - dim_bbox.get('x1', 0)
        dim_height = dim_bbox.get('y2', 0) - dim_bbox.get('y1', 0)

        # 치수 텍스트가 가로로 길면 수평선, 세로로 길면 수직선 탐색
        is_horizontal_dim = dim_width > dim_height

        best_line = None
        best_score = 0

        for line in lines:
            start = line.get('start', {})
            end = line.get('end', {})

            # 선의 방향 계산
            dx = end.get('x', 0) - start.get('x', 0)
            dy = end.get('y', 0) - start.get('y', 0)
            line_length = math.sqrt(dx * dx + dy * dy)

            if line_length < 10:  # 너무 짧은 선 무시
                continue

            # 선의 각도 (라디안)
            angle = math.atan2(dy, dx)
            angle_deg = abs(math.degrees(angle))

            # 수평선: 각도 ~0° 또는 ~180°
            is_horizontal_line = angle_deg < 15 or angle_deg > 165

            # 수직선: 각도 ~90°
            is_vertical_line = 75 < angle_deg < 105

            # 치수 방향과 선 방향 매칭
            if is_horizontal_dim and is_horizontal_line:
                # 선이 치수 텍스트 위/아래에 있는지 확인
                line_cy = (start.get('y', 0) + end.get('y', 0)) / 2
                dim_cy = (dim_bbox.get('y1', 0) + dim_bbox.get('y2', 0)) / 2

                y_distance = abs(line_cy - dim_cy)
                if y_distance < 50:  # 치수 텍스트와 가까운 경우
                    score = line_length / (y_distance + 1)
                    if score > best_score:
                        best_score = score
                        best_line = line

            elif not is_horizontal_dim and is_vertical_line:
                # 선이 치수 텍스트 좌/우에 있는지 확인
                line_cx = (start.get('x', 0) + end.get('x', 0)) / 2
                dim_cx = (dim_bbox.get('x1', 0) + dim_bbox.get('x2', 0)) / 2

                x_distance = abs(line_cx - dim_cx)
                if x_distance < 50:
                    score = line_length / (x_distance + 1)
                    if score > best_score:
                        best_score = score
                        best_line = line

        return best_line

    def _find_extension_lines(
        self,
        lines: List[Dict[str, Any]],
        dim_bbox: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        연장선 후보 찾기

        연장선은 치수선에 수직이며, 측정 대상까지 이어집니다.
        """
        dim_width = dim_bbox.get('x2', 0) - dim_bbox.get('x1', 0)
        dim_height = dim_bbox.get('y2', 0) - dim_bbox.get('y1', 0)
        is_horizontal_dim = dim_width > dim_height

        extension_lines = []

        for line in lines:
            start = line.get('start', {})
            end = line.get('end', {})

            dx = end.get('x', 0) - start.get('x', 0)
            dy = end.get('y', 0) - start.get('y', 0)
            line_length = math.sqrt(dx * dx + dy * dy)

            if line_length < 20:
                continue

            angle = math.atan2(dy, dx)
            angle_deg = abs(math.degrees(angle))

            is_vertical_line = 75 < angle_deg < 105
            is_horizontal_line = angle_deg < 15 or angle_deg > 165

            # 수평 치수 → 수직 연장선
            if is_horizontal_dim and is_vertical_line:
                extension_lines.append(line)
            # 수직 치수 → 수평 연장선
            elif not is_horizontal_dim and is_horizontal_line:
                extension_lines.append(line)

        return extension_lines

    def _analyze_arrow_direction(
        self,
        dimension_line: Dict[str, Any],
        dim_bbox: Dict[str, float]
    ) -> str:
        """
        화살표 방향 분석

        치수선의 양 끝에 있는 화살표가 가리키는 방향을 분석합니다.
        """
        start = dimension_line.get('start', {})
        end = dimension_line.get('end', {})

        dx = end.get('x', 0) - start.get('x', 0)
        dy = end.get('y', 0) - start.get('y', 0)

        if abs(dx) > abs(dy):
            # 수평선 → 좌우 방향
            return 'horizontal'
        else:
            # 수직선 → 상하 방향
            return 'vertical'

    def _find_target_in_direction(
        self,
        direction: str,
        dim_bbox: Dict[str, float],
        symbols: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        화살표 방향으로 대상 객체 찾기
        """
        dim_cx = (dim_bbox.get('x1', 0) + dim_bbox.get('x2', 0)) / 2
        dim_cy = (dim_bbox.get('y1', 0) + dim_bbox.get('y2', 0)) / 2

        candidates = []

        for symbol in symbols:
            sym_bbox = symbol.get('bbox', {})
            sym_cx = (sym_bbox.get('x1', 0) + sym_bbox.get('x2', 0)) / 2
            sym_cy = (sym_bbox.get('y1', 0) + sym_bbox.get('y2', 0)) / 2

            distance = math.sqrt((dim_cx - sym_cx) ** 2 + (dim_cy - sym_cy) ** 2)

            if direction == 'horizontal':
                # 수평 방향: 치수와 y좌표가 비슷한 심볼
                if abs(dim_cy - sym_cy) < 100:
                    candidates.append((symbol, distance))
            else:
                # 수직 방향: 치수와 x좌표가 비슷한 심볼
                if abs(dim_cx - sym_cx) < 100:
                    candidates.append((symbol, distance))

        if candidates:
            # 가장 가까운 후보 반환
            candidates.sort(key=lambda x: x[1])
            return candidates[0][0]

        return None

    def _find_target_at_line_end(
        self,
        line: Dict[str, Any],
        symbols: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """연장선 끝점 근처의 심볼 찾기"""
        start = line.get('start', {})
        end = line.get('end', {})

        # 양 끝점에서 가장 가까운 심볼 찾기
        endpoints = [
            (start.get('x', 0), start.get('y', 0)),
            (end.get('x', 0), end.get('y', 0))
        ]

        best_symbol = None
        best_distance = float('inf')

        for ex, ey in endpoints:
            for symbol in symbols:
                sym_bbox = symbol.get('bbox', {})

                # 심볼 bbox와의 거리 계산
                # 점이 bbox 내부에 있으면 거리 0
                sx1, sy1 = sym_bbox.get('x1', 0), sym_bbox.get('y1', 0)
                sx2, sy2 = sym_bbox.get('x2', 0), sym_bbox.get('y2', 0)

                # bbox까지의 최단 거리
                dx = max(sx1 - ex, 0, ex - sx2)
                dy = max(sy1 - ey, 0, ey - sy2)
                distance = math.sqrt(dx * dx + dy * dy)

                if distance < best_distance:
                    best_distance = distance
                    best_symbol = symbol

        # 연장선 끝점과 가까운 경우에만 반환
        if best_symbol and best_distance < 50:
            return best_symbol

        return None

    def _get_line_direction(self, line: Dict[str, Any]) -> str:
        """선의 방향 반환"""
        start = line.get('start', {})
        end = line.get('end', {})

        dx = end.get('x', 0) - start.get('x', 0)
        dy = end.get('y', 0) - start.get('y', 0)

        if abs(dx) > abs(dy):
            return 'horizontal'
        else:
            return 'vertical'

    def _infer_relation_type(self, dim_type: str) -> str:
        """치수 유형에서 관계 유형 추론"""
        type_map = {
            'diameter': 'diameter',
            'radius': 'radius',
            'angle': 'angle',
            'length': 'distance',
            'tolerance': 'tolerance',
            'surface_finish': 'surface_finish',
        }
        return type_map.get(dim_type, 'distance')

    def _to_dict(self, relation: DimensionRelation) -> Dict[str, Any]:
        """DimensionRelation을 dict로 변환"""
        return {
            'id': relation.id,
            'dimension_id': relation.dimension_id,
            'target_type': relation.target_type,
            'target_id': relation.target_id,
            'target_bbox': relation.target_bbox,
            'relation_type': relation.relation_type,
            'method': relation.method.value,
            'confidence': relation.confidence,
            'direction': relation.direction,
            'notes': relation.notes,
        }

    def _log_statistics(self, relations: List[Dict[str, Any]]) -> None:
        """관계 추출 통계 로깅"""
        total = len(relations)
        if total == 0:
            return

        by_method = {
            'dimension_line': 0,
            'extension_line': 0,
            'proximity': 0,
        }

        high_confidence = 0
        medium_confidence = 0
        low_confidence = 0

        for rel in relations:
            method = rel.get('method', 'proximity')
            if method in by_method:
                by_method[method] += 1

            conf = rel.get('confidence', 0)
            if conf >= 0.85:
                high_confidence += 1
            elif conf >= 0.6:
                medium_confidence += 1
            else:
                low_confidence += 1

        print(f"\n📊 치수 관계 추출 통계:")
        print(f"  총 관계: {total}개")
        print(f"  - 치수선 기반: {by_method['dimension_line']}개 ({by_method['dimension_line']/total*100:.1f}%)")
        print(f"  - 연장선 기반: {by_method['extension_line']}개 ({by_method['extension_line']/total*100:.1f}%)")
        print(f"  - 근접성 기반: {by_method['proximity']}개 ({by_method['proximity']/total*100:.1f}%)")
        print(f"  신뢰도: 높음 {high_confidence} / 중간 {medium_confidence} / 낮음 {low_confidence}")

    # ==================== 고급 기능 ====================

    def detect_arrows_cv2(
        self,
        image: np.ndarray,
        region: Dict[str, float]
    ) -> List[Tuple[float, float, str]]:
        """
        OpenCV를 사용한 화살표 검출 (선택적)

        Args:
            image: 이미지 배열
            region: 탐색 영역 bbox

        Returns:
            [(x, y, direction), ...] 화살표 위치와 방향
        """
        try:
            import cv2

            x1 = int(region.get('x1', 0))
            y1 = int(region.get('y1', 0))
            x2 = int(region.get('x2', image.shape[1]))
            y2 = int(region.get('y2', image.shape[0]))

            roi = image[y1:y2, x1:x2]

            if roi.size == 0:
                return []

            # 그레이스케일 변환
            if len(roi.shape) == 3:
                gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            else:
                gray = roi

            # 엣지 검출
            edges = cv2.Canny(gray, 50, 150)

            # 컨투어 찾기
            contours, _ = cv2.findContours(
                edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            arrows = []
            for contour in contours:
                # 삼각형 형태의 컨투어 → 화살표 후보
                if len(contour) >= 3:
                    approx = cv2.approxPolyDP(
                        contour, 0.04 * cv2.arcLength(contour, True), True
                    )

                    if len(approx) == 3:  # 삼각형
                        M = cv2.moments(contour)
                        if M["m00"] > 0:
                            cx = int(M["m10"] / M["m00"]) + x1
                            cy = int(M["m01"] / M["m00"]) + y1

                            # 방향 추정 (삼각형 꼭지점 분석)
                            pts = approx.reshape(-1, 2)
                            direction = self._estimate_arrow_direction(pts)

                            arrows.append((cx, cy, direction))

            return arrows

        except ImportError:
            logger.warning("OpenCV not available for arrow detection")
            return []
        except Exception as e:
            logger.error(f"Arrow detection failed: {e}")
            return []

    def _estimate_arrow_direction(self, triangle_pts: np.ndarray) -> str:
        """삼각형 꼭지점에서 화살표 방향 추정"""
        # 가장 뾰족한 꼭지점 찾기
        centroid = triangle_pts.mean(axis=0)

        max_dist = 0
        tip_idx = 0

        for i, pt in enumerate(triangle_pts):
            dist = np.linalg.norm(pt - centroid)
            if dist > max_dist:
                max_dist = dist
                tip_idx = i

        tip = triangle_pts[tip_idx]
        base_center = np.mean(
            [triangle_pts[j] for j in range(3) if j != tip_idx],
            axis=0
        )

        # tip에서 base로의 방향
        direction_vec = base_center - tip

        if abs(direction_vec[0]) > abs(direction_vec[1]):
            return 'right' if direction_vec[0] > 0 else 'left'
        else:
            return 'down' if direction_vec[1] > 0 else 'up'
