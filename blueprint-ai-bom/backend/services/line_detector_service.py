"""Line Detector Service - 선 검출 및 관계 분석 서비스

Line Detector API (port 5016)와 통신하여 선 검출 수행,
치수선-심볼 관계 추론 등을 처리
"""
import os
import time
import math
import uuid
import logging
import requests
from typing import Dict, Any, List, Optional, Tuple

from schemas.line import (
    Line, Intersection, Point, LineType, LineStyle,
    LineDetectionResult, LineDetectionConfig,
    DimensionLineRelation, DimensionSymbolLink
)

logger = logging.getLogger(__name__)

# Line Detector API URL (Docker: line-detector-api, Local: localhost)
LINE_DETECTOR_API = os.environ.get("LINE_DETECTOR_API_URL", "http://line-detector-api:5016")


class LineDetectorService:
    """선 검출 및 관계 분석 서비스"""

    def __init__(self, api_url: str = LINE_DETECTOR_API):
        self.api_url = api_url
        print(f"✅ LineDetectorService 초기화 완료 (line-detector-api: {self.api_url})")

    def detect_lines(
        self,
        image_path: str,
        config: Optional[LineDetectionConfig] = None
    ) -> Dict[str, Any]:
        """
        이미지에서 선 검출 수행

        Args:
            image_path: 이미지 파일 경로
            config: 선 검출 설정

        Returns:
            선 검출 결과 (lines, intersections, statistics)
        """
        start_time = time.time()
        config = config or LineDetectionConfig()

        try:
            # 파일 읽기
            with open(image_path, 'rb') as f:
                files = {'file': (os.path.basename(image_path), f, 'image/png')}

                # API 호출
                params = {
                    'method': config.method,
                    'merge_lines': config.merge_lines,
                    'classify_types': config.classify_types,
                    'classify_colors': config.classify_colors,
                    'classify_styles': config.classify_styles,
                    'find_intersections_flag': config.find_intersections,
                    'visualize': config.visualize,
                    'min_length': config.min_length,
                    'max_lines': config.max_lines,
                }

                response = requests.post(
                    f"{self.api_url}/api/v1/process",
                    files=files,
                    data=params,
                    timeout=60
                )
                response.raise_for_status()

            result = response.json()
            processing_time = (time.time() - start_time) * 1000

            # 결과 변환 (API가 data 래퍼 사용 시 처리)
            data = result.get('data', result)  # data 래퍼가 있으면 사용, 없으면 result 직접 사용
            lines = self._parse_lines(data.get('lines', []))
            intersections = self._parse_intersections(data.get('intersections', []))

            return {
                'lines': [l.model_dump() for l in lines],
                'intersections': [i.model_dump() for i in intersections],
                'statistics': result.get('statistics', {}),
                'processing_time_ms': processing_time,
                'image_width': result.get('image_width', 0),
                'image_height': result.get('image_height', 0),
                'visualization_base64': result.get('visualization'),
            }

        except requests.exceptions.ConnectionError:
            logger.error(f"Line Detector API 연결 실패: {self.api_url}")
            raise RuntimeError("Line Detector API에 연결할 수 없습니다")
        except Exception as e:
            logger.error(f"선 검출 실패: {str(e)}")
            raise

    def _parse_lines(self, raw_lines: List[Dict]) -> List[Line]:
        """API 결과를 Line 스키마로 변환"""
        lines = []
        for idx, raw in enumerate(raw_lines):
            # id는 문자열이어야 함 - API가 정수를 반환할 수 있음
            raw_id = raw.get('id')
            line_id = str(raw_id) if raw_id is not None else f"line_{idx}"

            # 시작점/끝점 - 두 가지 형식 지원
            # 1. start_point: [x, y] 형식 (Line Detector API v1)
            # 2. x1, y1, x2, y2 형식 (레거시)
            start_point = raw.get('start_point')
            end_point = raw.get('end_point')

            if start_point and end_point:
                start = Point(x=start_point[0], y=start_point[1])
                end = Point(x=end_point[0], y=end_point[1])
            else:
                start = Point(x=raw.get('x1', 0), y=raw.get('y1', 0))
                end = Point(x=raw.get('x2', 0), y=raw.get('y2', 0))

            # 길이와 각도 계산
            length = raw.get('length', self._calculate_length(start, end))
            angle = raw.get('angle', self._calculate_angle(start, end))

            # 선 유형
            line_type = self._parse_line_type(raw.get('line_type', 'unknown'))
            line_style = self._parse_line_style(raw.get('line_style', raw.get('style', 'unknown')))

            lines.append(Line(
                id=line_id,
                start=start,
                end=end,
                length=length,
                angle=angle,
                line_type=line_type,
                line_style=line_style,
                color=raw.get('color'),
                confidence=raw.get('confidence', 1.0),
                thickness=raw.get('thickness'),
                connected_to=raw.get('connected_to', []),
                intersections=raw.get('intersections', []),
            ))

        return lines

    def _parse_intersections(self, raw_ints: List[Dict]) -> List[Intersection]:
        """API 결과를 Intersection 스키마로 변환"""
        intersections = []
        for idx, raw in enumerate(raw_ints):
            # id는 문자열이어야 함 - API가 정수를 반환할 수 있음
            raw_id = raw.get('id')
            int_id = str(raw_id) if raw_id is not None else f"int_{idx}"

            # 두 가지 형식 지원
            # 1. point: [x, y] 형식 (Line Detector API v1)
            # 2. x, y 형식 (레거시)
            point_data = raw.get('point')
            if point_data and isinstance(point_data, list):
                point = Point(x=point_data[0], y=point_data[1])
            else:
                point = Point(x=raw.get('x', 0), y=raw.get('y', 0))

            # line_ids 처리: line1_id, line2_id 또는 line_ids - 문자열로 변환
            line_ids_raw = raw.get('line_ids', [])
            if not line_ids_raw:
                line1 = raw.get('line1_id')
                line2 = raw.get('line2_id')
                if line1 is not None and line2 is not None:
                    line_ids_raw = [line1, line2]
            # 모든 line_id를 문자열로 변환
            line_ids = [str(lid) for lid in line_ids_raw]

            intersections.append(Intersection(
                id=int_id,
                point=point,
                line_ids=line_ids,
                intersection_type=raw.get('type'),
            ))

        return intersections

    def _parse_line_type(self, type_str: str) -> LineType:
        """문자열을 LineType으로 변환"""
        type_map = {
            'process': LineType.PROCESS,
            'cooling': LineType.COOLING,
            'steam': LineType.STEAM,
            'signal': LineType.SIGNAL,
            'electrical': LineType.ELECTRICAL,
            'dimension': LineType.DIMENSION,
            'extension': LineType.EXTENSION,
            'leader': LineType.LEADER,
        }
        return type_map.get(type_str.lower(), LineType.UNKNOWN)

    def _parse_line_style(self, style_str: str) -> LineStyle:
        """문자열을 LineStyle로 변환"""
        style_map = {
            'solid': LineStyle.SOLID,
            'dashed': LineStyle.DASHED,
            'dotted': LineStyle.DOTTED,
            'chain': LineStyle.CHAIN,
            'double_chain': LineStyle.DOUBLE_CHAIN,
        }
        return style_map.get(style_str.lower(), LineStyle.UNKNOWN)

    def _calculate_length(self, start: Point, end: Point) -> float:
        """두 점 사이 거리 계산"""
        return math.sqrt((end.x - start.x) ** 2 + (end.y - start.y) ** 2)

    def _calculate_angle(self, start: Point, end: Point) -> float:
        """두 점 사이 각도 계산 (라디안)"""
        return math.atan2(end.y - start.y, end.x - start.x)

    def find_dimension_lines(
        self,
        lines: List[Line],
        dimensions: List[Dict]
    ) -> List[DimensionLineRelation]:
        """
        치수와 연관된 선(치수선)을 찾아 관계 분석

        Args:
            lines: 검출된 선 목록
            dimensions: 치수 목록 (bbox 포함)

        Returns:
            치수-선 관계 목록
        """
        relations = []

        for dim in dimensions:
            dim_bbox = dim.get('bbox', {})
            dim_id = dim.get('id', '')

            # 치수 bbox의 중심점
            dim_cx = (dim_bbox.get('x1', 0) + dim_bbox.get('x2', 0)) / 2
            dim_cy = (dim_bbox.get('y1', 0) + dim_bbox.get('y2', 0)) / 2

            # 가장 가까운 선 찾기
            best_line = None
            best_distance = float('inf')

            for line in lines:
                # 선의 중심점
                line_cx = (line.start.x + line.end.x) / 2
                line_cy = (line.start.y + line.end.y) / 2

                # 거리 계산
                distance = math.sqrt((dim_cx - line_cx) ** 2 + (dim_cy - line_cy) ** 2)

                if distance < best_distance:
                    best_distance = distance
                    best_line = line

            if best_line and best_distance < 200:  # 200px 이내
                # 방향 결정
                angle_deg = math.degrees(best_line.angle)
                if -10 < angle_deg < 10 or 170 < abs(angle_deg) < 190:
                    direction = 'horizontal'
                elif 80 < abs(angle_deg) < 100:
                    direction = 'vertical'
                else:
                    direction = 'diagonal'

                # 관계 유형 추론
                dim_type = dim.get('dimension_type', 'unknown')
                if dim_type == 'diameter':
                    relation_type = 'diameter'
                elif dim_type == 'radius':
                    relation_type = 'radius'
                elif dim_type == 'angle':
                    relation_type = 'angle'
                else:
                    relation_type = 'distance'

                confidence = max(0.3, 1.0 - (best_distance / 200))

                relations.append(DimensionLineRelation(
                    dimension_id=dim_id,
                    target_type='line',
                    target_id=best_line.id,
                    relation_type=relation_type,
                    direction=direction,
                    confidence=confidence
                ))

        return relations

    def link_dimensions_to_symbols(
        self,
        dimensions: List[Dict],
        symbols: List[Dict],
        lines: Optional[List[Line]] = None
    ) -> List[DimensionSymbolLink]:
        """
        치수를 가장 가까운 심볼에 연결

        Args:
            dimensions: 치수 목록
            symbols: 심볼 검출 목록
            lines: (선택) 선 검출 결과 - 치수선 경로 기반 연결 시 사용

        Returns:
            치수-심볼 연결 결과 목록
        """
        links = []

        for dim in dimensions:
            dim_id = dim.get('id', '')
            dim_bbox = dim.get('bbox', {})

            # 치수 bbox의 중심점
            dim_cx = (dim_bbox.get('x1', 0) + dim_bbox.get('x2', 0)) / 2
            dim_cy = (dim_bbox.get('y1', 0) + dim_bbox.get('y2', 0)) / 2

            # 가장 가까운 심볼 찾기
            best_symbol = None
            best_distance = float('inf')

            for symbol in symbols:
                sym_bbox = symbol.get('bbox', {})

                # 심볼 bbox의 중심점
                sym_cx = (sym_bbox.get('x1', 0) + sym_bbox.get('x2', 0)) / 2
                sym_cy = (sym_bbox.get('y1', 0) + sym_bbox.get('y2', 0)) / 2

                # 거리 계산
                distance = math.sqrt((dim_cx - sym_cx) ** 2 + (dim_cy - sym_cy) ** 2)

                if distance < best_distance:
                    best_distance = distance
                    best_symbol = symbol

            if best_symbol and best_distance < 500:  # 500px 이내
                confidence = max(0.2, 1.0 - (best_distance / 500))

                links.append(DimensionSymbolLink(
                    dimension_id=dim_id,
                    symbol_id=best_symbol.get('id'),
                    link_type='auto',
                    distance=best_distance,
                    confidence=confidence
                ))
            else:
                # 연결할 심볼이 없는 경우
                links.append(DimensionSymbolLink(
                    dimension_id=dim_id,
                    symbol_id=None,
                    link_type='unlinked',
                    distance=best_distance if best_distance != float('inf') else -1,
                    confidence=0.0
                ))

        return links

    def classify_dimension_lines(
        self,
        lines: List[Line],
        dimensions: List[Dict]
    ) -> Tuple[List[Line], List[Line]]:
        """
        치수선과 일반선 분리

        Args:
            lines: 검출된 전체 선 목록
            dimensions: 치수 목록

        Returns:
            (치수선 목록, 일반선 목록)
        """
        dimension_lines = []
        other_lines = []

        # 치수 bbox 영역들
        dim_regions = []
        for dim in dimensions:
            bbox = dim.get('bbox', {})
            dim_regions.append({
                'x1': bbox.get('x1', 0),
                'y1': bbox.get('y1', 0),
                'x2': bbox.get('x2', 0),
                'y2': bbox.get('y2', 0),
            })

        for line in lines:
            # 이미 치수선으로 분류된 경우
            if line.line_type == LineType.DIMENSION:
                dimension_lines.append(line)
                continue

            # 치수 bbox 근처에 있는지 확인
            is_near_dimension = False
            for region in dim_regions:
                # 선의 중심점
                cx = (line.start.x + line.end.x) / 2
                cy = (line.start.y + line.end.y) / 2

                # 확장된 영역 내에 있는지 확인 (50px 마진)
                margin = 50
                if (region['x1'] - margin <= cx <= region['x2'] + margin and
                    region['y1'] - margin <= cy <= region['y2'] + margin):
                    is_near_dimension = True
                    break

            if is_near_dimension:
                # 선 유형을 치수선으로 업데이트
                line.line_type = LineType.DIMENSION
                dimension_lines.append(line)
            else:
                other_lines.append(line)

        return dimension_lines, other_lines

    def health_check(self) -> bool:
        """Line Detector API 상태 확인"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
