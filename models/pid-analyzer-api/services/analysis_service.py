"""
P&ID Analysis Service
핵심 분석 함수 모음

- 심볼 연결 분석
- BOM 생성
- 그래프 시각화
"""

import os
import re
import base64
import logging
import math
from typing import Optional, List, Dict, Tuple
from collections import defaultdict

import cv2
import numpy as np
import httpx

logger = logging.getLogger(__name__)

# Configuration
EASYOCR_API_URL = os.getenv("EASYOCR_API_URL", "http://easyocr-api:5015/api/v1/ocr")

# =====================
# Constants
# =====================

# Line color type mapping (from Line Detector)
LINE_COLOR_TYPES = {
    'process': {'korean': '공정 라인', 'pipe_type': 'main_process'},
    'water': {'korean': '냉각수/급수', 'pipe_type': 'utility'},
    'steam': {'korean': '증기/가열', 'pipe_type': 'utility'},
    'signal': {'korean': '신호선', 'pipe_type': 'instrument'},
    'electrical': {'korean': '전기', 'pipe_type': 'electrical'},
    'drain': {'korean': '배수', 'pipe_type': 'utility'},
    'air': {'korean': '공기/가스', 'pipe_type': 'utility'},
    'unknown': {'korean': '미분류', 'pipe_type': 'unknown'},
}

# Line style type mapping (from Line Detector)
LINE_STYLE_TYPES = {
    'solid': {'korean': '실선', 'signal_type': 'process', 'description': '주요 공정 배관'},
    'dashed': {'korean': '점선', 'signal_type': 'instrument', 'description': '계장 신호선'},
    'dotted': {'korean': '점점선', 'signal_type': 'auxiliary', 'description': '보조/옵션 라인'},
    'dash_dot': {'korean': '일점쇄선', 'signal_type': 'centerline', 'description': '경계선/중심선'},
    'unknown': {'korean': '미분류', 'signal_type': 'unknown', 'description': '분류 불가'},
}

# Instrument type mapping
INSTRUMENT_TYPES = {
    "FC": {"name": "Flow Controller", "category": "controller"},
    "FI": {"name": "Flow Indicator", "category": "indicator"},
    "FT": {"name": "Flow Transmitter", "category": "transmitter"},
    "TC": {"name": "Temperature Controller", "category": "controller"},
    "TI": {"name": "Temperature Indicator", "category": "indicator"},
    "TT": {"name": "Temperature Transmitter", "category": "transmitter"},
    "LC": {"name": "Level Controller", "category": "controller"},
    "LI": {"name": "Level Indicator", "category": "indicator"},
    "LT": {"name": "Level Transmitter", "category": "transmitter"},
    "PC": {"name": "Pressure Controller", "category": "controller"},
    "PI": {"name": "Pressure Indicator", "category": "indicator"},
    "PT": {"name": "Pressure Transmitter", "category": "transmitter"},
    "SC": {"name": "Speed Controller", "category": "controller"},
    "SI": {"name": "Speed Indicator", "category": "indicator"},
}


# =====================
# OCR Integration
# =====================

def detect_instruments_via_ocr(image_bytes: bytes) -> List[Dict]:
    """
    EasyOCR을 사용하여 이미지에서 계기 태그 검출

    Args:
        image_bytes: 이미지 바이트 데이터

    Returns:
        검출된 계기 목록 (id, tag, class_name, category, bbox, center, confidence)
    """
    try:
        with httpx.Client(timeout=120.0) as client:
            files = {"file": ("image.png", image_bytes, "image/png")}
            data = {"lang": "en"}
            response = client.post(EASYOCR_API_URL, files=files, data=data)

        if response.status_code != 200:
            logger.warning(f"EasyOCR API error: {response.status_code}")
            return []

        result = response.json()
        texts = result.get("texts", [])
        if not texts:
            texts = result.get("data", {}).get("texts", [])

        # 계기 태그 패턴 (FC-1, TI-3, LC-2 등)
        tag_pattern = re.compile(r'([FTLPSC][ICTR])-?(\d+)', re.IGNORECASE)
        instruments = []
        instrument_id = 10000  # YOLO ID와 충돌 방지

        for text_item in texts:
            text = text_item.get("text", "")
            bbox = text_item.get("bbox", [])
            confidence = text_item.get("confidence", 0)

            match = tag_pattern.search(text.upper())
            if match:
                code = match.group(1).upper()
                number = match.group(2)
                tag = f"{code}-{number}"

                # bbox 중심 계산 (EasyOCR: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]])
                if bbox and isinstance(bbox[0], list):
                    xs = [p[0] for p in bbox]
                    ys = [p[1] for p in bbox]
                    center = [(min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2]
                    norm_bbox = [min(xs), min(ys), max(xs), max(ys)]
                elif len(bbox) >= 4:
                    center = [(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2]
                    norm_bbox = bbox[:4]
                else:
                    center = [0, 0]
                    norm_bbox = [0, 0, 0, 0]

                inst_info = INSTRUMENT_TYPES.get(code, {"name": "Unknown Instrument", "category": "misc"})

                instruments.append({
                    "id": instrument_id,
                    "tag": tag,
                    "class_name": inst_info["name"],
                    "category": inst_info["category"],
                    "instrument_code": code,
                    "bbox": norm_bbox,
                    "center": center,
                    "confidence": confidence,
                    "source": "ocr"
                })
                instrument_id += 1

        # 중복 태그 제거
        seen_tags = set()
        unique = []
        for inst in instruments:
            if inst["tag"] not in seen_tags:
                seen_tags.add(inst["tag"])
                unique.append(inst)

        logger.info(f"OCR 검출: {len(unique)}개 계기 태그")
        return unique

    except Exception as e:
        logger.error(f"OCR instrument detection error: {e}")
        return []


def merge_symbols_with_ocr(yolo_symbols: List[Dict], ocr_instruments: List[Dict],
                           match_distance: float = 80) -> List[Dict]:
    """
    YOLO 심볼과 OCR 계기 태그 병합

    1. OCR 태그를 근처 YOLO 심볼에 매칭 (태그 정보 추가)
    2. 매칭되지 않은 OCR 계기는 새 심볼로 추가

    Args:
        yolo_symbols: YOLO 검출 심볼 (model_type=pid_class_aware)
        ocr_instruments: OCR 검출 계기
        match_distance: 매칭 최대 거리 (픽셀)

    Returns:
        병합된 심볼 목록
    """
    merged = [s.copy() for s in yolo_symbols]  # 원본 보존
    matched_ocr_ids = set()

    # OCR 계기를 YOLO 심볼에 매칭
    for ocr_inst in ocr_instruments:
        ocr_center = ocr_inst.get("center", [0, 0])
        best_match = None
        best_dist = match_distance

        for symbol in merged:
            sym_center = symbol.get("center", [0, 0])
            dist = ((ocr_center[0] - sym_center[0])**2 +
                    (ocr_center[1] - sym_center[1])**2)**0.5

            if dist < best_dist:
                best_dist = dist
                best_match = symbol

        if best_match:
            # YOLO 심볼에 OCR 태그 정보 추가
            best_match["tag"] = ocr_inst["tag"]
            best_match["instrument_code"] = ocr_inst.get("instrument_code", "")
            best_match["ocr_confidence"] = ocr_inst.get("confidence", 0)
            matched_ocr_ids.add(ocr_inst["id"])
            logger.debug(f"매칭: {ocr_inst['tag']} -> {best_match.get('class_name')}")

    # 매칭되지 않은 OCR 계기를 새 심볼로 추가
    for ocr_inst in ocr_instruments:
        if ocr_inst["id"] not in matched_ocr_ids:
            merged.append({
                **ocr_inst,
                "source": "ocr_only"
            })
            logger.debug(f"새 심볼 추가: {ocr_inst['tag']}")

    logger.info(f"심볼 병합: {len(yolo_symbols)} YOLO + {len(ocr_instruments)} OCR -> {len(merged)} 통합")
    return merged


# =====================
# Connection Analysis
# =====================

def normalize_bbox(symbol: Dict) -> Optional[Tuple[float, float, float, float]]:
    """
    다양한 bbox 형식을 [x1, y1, x2, y2]로 정규화

    지원 형식:
    1. YOLO API: {"bbox": {"x": x, "y": y, "width": w, "height": h}}
    2. 리스트: {"bbox": [x1, y1, x2, y2]}
    3. 직접 좌표: {"x": x, "y": y, "width": w, "height": h}
    4. xyxy 형식: {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
    """
    bbox = symbol.get('bbox')

    # 형식 1: YOLO API 딕셔너리 형식 {"bbox": {"x": x, "y": y, "width": w, "height": h}}
    if isinstance(bbox, dict):
        x = bbox.get('x', 0)
        y = bbox.get('y', 0)
        w = bbox.get('width', 0)
        h = bbox.get('height', 0)
        if w > 0 and h > 0:
            return (x, y, x + w, y + h)

    # 형식 2: 리스트 형식 [x1, y1, x2, y2]
    if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
        return tuple(bbox)

    # 형식 3: 심볼 직접 좌표 {"x": x, "y": y, "width": w, "height": h}
    if 'x' in symbol and 'y' in symbol and 'width' in symbol and 'height' in symbol:
        x = symbol['x']
        y = symbol['y']
        w = symbol['width']
        h = symbol['height']
        return (x, y, x + w, y + h)

    # 형식 4: xyxy 형식
    if 'x1' in symbol and 'y1' in symbol and 'x2' in symbol and 'y2' in symbol:
        return (symbol['x1'], symbol['y1'], symbol['x2'], symbol['y2'])

    return None


def point_to_symbol_distance(point: Tuple[float, float], symbol: Dict) -> float:
    """점에서 심볼 bbox까지의 최소 거리 계산"""
    bbox = normalize_bbox(symbol)
    if bbox is None:
        return float('inf')

    x1, y1, x2, y2 = [float(v) for v in bbox]
    px, py = float(point[0]), float(point[1])

    # bbox 내부에 있으면 0 반환
    if x1 <= px <= x2 and y1 <= py <= y2:
        return 0

    # 가장 가까운 점 계산
    closest_x = max(x1, min(px, x2))
    closest_y = max(y1, min(py, y2))

    return ((px - closest_x) ** 2 + (py - closest_y) ** 2) ** 0.5


def find_nearest_symbol(point: Tuple[float, float], symbols: List[Dict],
                        max_distance: float = 50) -> Optional[Dict]:
    """점에서 가장 가까운 심볼 찾기"""
    nearest = None
    min_dist = max_distance

    for symbol in symbols:
        dist = point_to_symbol_distance(point, symbol)
        if dist < min_dist:
            min_dist = dist
            nearest = symbol

    return nearest


def find_symbol_connections(symbols: List[Dict], lines: List[Dict],
                            intersections: List[Dict]) -> List[Dict]:
    """
    심볼 간 연결 관계 분석 (개선된 알고리즘)

    알고리즘:
    1. 각 라인의 끝점에서 가장 가까운 심볼 찾기 (거리 기반)
    2. 라인 경로를 따라 심볼 연결 추적
    3. 교차점을 통한 간접 연결 탐지
    4. 중복 연결 제거 및 신뢰도 계산
    """
    connections = []
    connection_id = 0
    seen_pairs = set()  # 중복 방지

    # 설정값 (고해상도 도면 지원: 3000x2000+ 이미지 기준)
    DIRECT_MARGIN = 150  # 직접 연결 최대 거리 (픽셀)
    EXTENDED_MARGIN = 250  # 확장 연결 최대 거리

    # 1. 직접 연결 탐지 (라인 끝점이 심볼에 닿는 경우)
    for line in lines:
        start_raw = line.get('start_point', [0, 0])
        end_raw = line.get('end_point', [0, 0])
        start = (float(start_raw[0]), float(start_raw[1]))
        end = (float(end_raw[0]), float(end_raw[1]))

        from_symbol = find_nearest_symbol(start, symbols, DIRECT_MARGIN)
        to_symbol = find_nearest_symbol(end, symbols, DIRECT_MARGIN)

        if from_symbol and to_symbol and from_symbol['id'] != to_symbol['id']:
            pair_key = tuple(sorted([from_symbol['id'], to_symbol['id']]))

            if pair_key not in seen_pairs:
                seen_pairs.add(pair_key)

                # 연결 거리 계산
                from_dist = point_to_symbol_distance(start, from_symbol)
                to_dist = point_to_symbol_distance(end, to_symbol)
                avg_dist = (from_dist + to_dist) / 2

                # 신뢰도 계산 (거리가 가까울수록 높음)
                confidence = max(0, 1 - (avg_dist / DIRECT_MARGIN))

                # 색상 기반 라인 정보 추출
                color_type = line.get('color_type', 'unknown')
                color_info = LINE_COLOR_TYPES.get(color_type, LINE_COLOR_TYPES['unknown'])

                # 스타일 기반 라인 정보 추출
                line_style = line.get('line_style', 'unknown')
                style_info = LINE_STYLE_TYPES.get(line_style, LINE_STYLE_TYPES['unknown'])

                connections.append({
                    'id': connection_id,
                    'from_symbol': {
                        'id': from_symbol['id'],
                        'class_name': from_symbol.get('class_name', 'unknown'),
                        'category': from_symbol.get('category', 'misc'),
                        'center': from_symbol.get('center', [0, 0])
                    },
                    'to_symbol': {
                        'id': to_symbol['id'],
                        'class_name': to_symbol.get('class_name', 'unknown'),
                        'category': to_symbol.get('category', 'misc'),
                        'center': to_symbol.get('center', [0, 0])
                    },
                    'line_type': line.get('line_type', 'unknown'),
                    'color_type': color_type,
                    'color_type_korean': color_info['korean'],
                    'pipe_type': color_info['pipe_type'],
                    'line_style': line_style,
                    'line_style_korean': style_info['korean'],
                    'signal_type': style_info['signal_type'],
                    'connection_type': 'direct',
                    'confidence': round(confidence, 2),
                    'distance': round(avg_dist, 1),
                    'line_id': line.get('id', 0),
                    # 실제 라인 경로 정보 추가 (시각화용)
                    'line_path': [
                        list(start),
                        list(end)
                    ]
                })
                connection_id += 1

    # 2. 교차점 기반 연결 탐지
    if intersections:
        # 라인 ID로 인덱싱
        line_by_id = {line.get('id', i): line for i, line in enumerate(lines)}

        # 교차점별 연결된 라인 그룹화
        intersection_lines = defaultdict(list)
        for inter in intersections:
            point_data = inter.get('point', [])
            if point_data:
                inter_point = (point_data[0], point_data[1])
            else:
                inter_point = (inter.get('x', 0), inter.get('y', 0))

            line1_id = inter.get('line1_id')
            line2_id = inter.get('line2_id')

            if line1_id is not None and line1_id in line_by_id:
                intersection_lines[inter_point].append(line_by_id[line1_id])
            if line2_id is not None and line2_id in line_by_id:
                intersection_lines[inter_point].append(line_by_id[line2_id])

        # 같은 교차점을 공유하는 라인들의 심볼 연결 발견
        for inter_point, inter_lines in intersection_lines.items():
            if len(inter_lines) >= 2:
                connected_symbols = []
                for line in inter_lines:
                    start = tuple(line.get('start_point', [0, 0]))
                    end = tuple(line.get('end_point', [0, 0]))

                    start_dist = ((start[0] - inter_point[0])**2 + (start[1] - inter_point[1])**2)**0.5
                    end_dist = ((end[0] - inter_point[0])**2 + (end[1] - inter_point[1])**2)**0.5

                    far_point = start if start_dist > end_dist else end
                    symbol = find_nearest_symbol(far_point, symbols, EXTENDED_MARGIN)

                    if symbol:
                        connected_symbols.append({
                            'symbol': symbol,
                            'line_type': line.get('line_type', 'unknown'),
                            'color_type': line.get('color_type', 'unknown'),
                            'line_style': line.get('line_style', 'unknown'),
                            'line_id': line.get('id', 0),
                            'line_start': list(far_point),
                            'line_end': list(inter_point)
                        })

                # 교차점을 통해 연결된 심볼들 짝짓기
                for i in range(len(connected_symbols)):
                    for j in range(i + 1, len(connected_symbols)):
                        s1 = connected_symbols[i]['symbol']
                        s2 = connected_symbols[j]['symbol']

                        if s1['id'] != s2['id']:
                            pair_key = tuple(sorted([s1['id'], s2['id']]))

                            if pair_key not in seen_pairs:
                                seen_pairs.add(pair_key)

                                color_type = connected_symbols[i].get('color_type', 'unknown')
                                color_info = LINE_COLOR_TYPES.get(color_type, LINE_COLOR_TYPES['unknown'])

                                line_style = connected_symbols[i].get('line_style', 'unknown')
                                style_info = LINE_STYLE_TYPES.get(line_style, LINE_STYLE_TYPES['unknown'])

                                line_path = [
                                    connected_symbols[i]['line_start'],
                                    list(inter_point),
                                    connected_symbols[j]['line_start']
                                ]

                                connections.append({
                                    'id': connection_id,
                                    'from_symbol': {
                                        'id': s1['id'],
                                        'class_name': s1.get('class_name', 'unknown'),
                                        'category': s1.get('category', 'misc'),
                                        'center': s1.get('center', [0, 0])
                                    },
                                    'to_symbol': {
                                        'id': s2['id'],
                                        'class_name': s2.get('class_name', 'unknown'),
                                        'category': s2.get('category', 'misc'),
                                        'center': s2.get('center', [0, 0])
                                    },
                                    'line_type': connected_symbols[i]['line_type'],
                                    'color_type': color_type,
                                    'color_type_korean': color_info['korean'],
                                    'pipe_type': color_info['pipe_type'],
                                    'line_style': line_style,
                                    'line_style_korean': style_info['korean'],
                                    'signal_type': style_info['signal_type'],
                                    'connection_type': 'via_intersection',
                                    'confidence': 0.7,
                                    'intersection_point': list(inter_point),
                                    'line_ids': [connected_symbols[i]['line_id'], connected_symbols[j]['line_id']],
                                    'line_path': line_path
                                })
                                connection_id += 1

    # 신뢰도 순으로 정렬
    connections.sort(key=lambda x: x.get('confidence', 0), reverse=True)

    return connections


def build_connectivity_graph(symbols: List[Dict], connections: List[Dict]) -> Dict:
    """
    연결성 그래프 구축

    출력: NetworkX 호환 형식의 그래프 데이터
    """
    adjacency = defaultdict(list)

    for conn in connections:
        from_id = conn['from_symbol']['id']
        to_id = conn['to_symbol']['id']

        adjacency[from_id].append({
            'target': to_id,
            'line_type': conn['line_type'],
            'connection_id': conn['id']
        })
        adjacency[to_id].append({
            'target': from_id,
            'line_type': conn['line_type'],
            'connection_id': conn['id']
        })

    nodes = list(set(
        [conn['from_symbol']['id'] for conn in connections] +
        [conn['to_symbol']['id'] for conn in connections]
    ))

    return {
        'nodes': [{'id': s['id'], **s} for s in symbols if s['id'] in nodes],
        'edges': connections,
        'adjacency': dict(adjacency),
        'statistics': {
            'node_count': len(nodes),
            'edge_count': len(connections),
            'isolated_symbols': len([s for s in symbols if s['id'] not in nodes])
        }
    }


# =====================
# Path Finding (BFS/DFS)
# =====================

def find_path_bfs(adjacency: Dict, start_id: int, end_id: int) -> Dict:
    """
    BFS로 두 노드 간 최단 경로 찾기

    Args:
        adjacency: 인접 리스트 {node_id: [{'target': ..., 'line_type': ...}, ...]}
        start_id: 시작 노드 ID
        end_id: 도착 노드 ID

    Returns:
        {
            'found': bool,
            'path': [node_id, ...],
            'path_length': int,
            'edges': [{'from': ..., 'to': ..., 'line_type': ...}, ...]
        }
    """
    from collections import deque

    if start_id == end_id:
        return {
            'found': True,
            'path': [start_id],
            'path_length': 0,
            'edges': []
        }

    visited = {start_id}
    # queue: (current_node, path, edges)
    queue = deque([(start_id, [start_id], [])])

    while queue:
        current, path, edges = queue.popleft()

        for neighbor in adjacency.get(current, []):
            target = neighbor['target']
            edge_info = {
                'from': current,
                'to': target,
                'line_type': neighbor.get('line_type', 'unknown'),
                'connection_id': neighbor.get('connection_id')
            }

            if target == end_id:
                return {
                    'found': True,
                    'path': path + [target],
                    'path_length': len(path),
                    'edges': edges + [edge_info]
                }

            if target not in visited:
                visited.add(target)
                queue.append((target, path + [target], edges + [edge_info]))

    return {
        'found': False,
        'path': [],
        'path_length': -1,
        'edges': []
    }


def find_path_dfs(adjacency: Dict, start_id: int, end_id: int,
                  max_depth: int = 50) -> Dict:
    """
    DFS로 두 노드 간 경로 찾기

    Args:
        adjacency: 인접 리스트
        start_id: 시작 노드 ID
        end_id: 도착 노드 ID
        max_depth: 최대 탐색 깊이 (무한 루프 방지)

    Returns:
        {
            'found': bool,
            'path': [node_id, ...],
            'path_length': int,
            'edges': [...]
        }
    """
    if start_id == end_id:
        return {
            'found': True,
            'path': [start_id],
            'path_length': 0,
            'edges': []
        }

    visited = set()

    def dfs(current: int, path: List[int], edges: List[Dict], depth: int):
        if depth > max_depth:
            return None

        if current == end_id:
            return {'path': path, 'edges': edges}

        visited.add(current)

        for neighbor in adjacency.get(current, []):
            target = neighbor['target']
            if target not in visited:
                edge_info = {
                    'from': current,
                    'to': target,
                    'line_type': neighbor.get('line_type', 'unknown'),
                    'connection_id': neighbor.get('connection_id')
                }
                result = dfs(target, path + [target], edges + [edge_info], depth + 1)
                if result:
                    return result

        visited.remove(current)  # 백트래킹
        return None

    result = dfs(start_id, [start_id], [], 0)

    if result:
        return {
            'found': True,
            'path': result['path'],
            'path_length': len(result['path']) - 1,
            'edges': result['edges']
        }

    return {
        'found': False,
        'path': [],
        'path_length': -1,
        'edges': []
    }


def find_all_paths(adjacency: Dict, start_id: int, end_id: int,
                   max_depth: int = 20, max_paths: int = 100) -> List[Dict]:
    """
    두 노드 간 모든 경로 찾기 (DFS 기반)

    Args:
        adjacency: 인접 리스트
        start_id: 시작 노드 ID
        end_id: 도착 노드 ID
        max_depth: 최대 탐색 깊이
        max_paths: 최대 경로 수

    Returns:
        [{'path': [...], 'path_length': int, 'edges': [...]}, ...]
    """
    all_paths = []

    def dfs(current: int, path: List[int], edges: List[Dict], visited: set):
        if len(all_paths) >= max_paths:
            return

        if len(path) > max_depth:
            return

        if current == end_id:
            all_paths.append({
                'path': path.copy(),
                'path_length': len(path) - 1,
                'edges': edges.copy()
            })
            return

        for neighbor in adjacency.get(current, []):
            target = neighbor['target']
            if target not in visited:
                edge_info = {
                    'from': current,
                    'to': target,
                    'line_type': neighbor.get('line_type', 'unknown'),
                    'connection_id': neighbor.get('connection_id')
                }
                visited.add(target)
                path.append(target)
                edges.append(edge_info)

                dfs(target, path, edges, visited)

                path.pop()
                edges.pop()
                visited.remove(target)

    visited = {start_id}
    dfs(start_id, [start_id], [], visited)

    return all_paths


def is_reachable(adjacency: Dict, start_id: int, end_id: int) -> bool:
    """
    두 노드 간 연결 가능 여부 확인 (BFS)

    Args:
        adjacency: 인접 리스트
        start_id: 시작 노드 ID
        end_id: 도착 노드 ID

    Returns:
        bool: 연결 가능 여부
    """
    result = find_path_bfs(adjacency, start_id, end_id)
    return result['found']


def get_connected_components(adjacency: Dict, all_node_ids: List[int]) -> List[List[int]]:
    """
    연결된 컴포넌트 찾기 (Union-Find / BFS)

    Args:
        adjacency: 인접 리스트
        all_node_ids: 모든 노드 ID 목록

    Returns:
        [[node_ids in component1], [node_ids in component2], ...]
    """
    from collections import deque

    visited = set()
    components = []

    for start_id in all_node_ids:
        if start_id in visited:
            continue

        # BFS로 연결된 모든 노드 탐색
        component = []
        queue = deque([start_id])
        visited.add(start_id)

        while queue:
            current = queue.popleft()
            component.append(current)

            for neighbor in adjacency.get(current, []):
                target = neighbor['target']
                if target not in visited:
                    visited.add(target)
                    queue.append(target)

        components.append(component)

    return components


def check_path_contains(path: List[int], symbols: List[Dict],
                        required_classes: List[str]) -> Dict:
    """
    경로에 특정 심볼 클래스가 포함되어 있는지 확인

    Args:
        path: 노드 ID 경로 [id1, id2, ...]
        symbols: 심볼 목록
        required_classes: 필수 클래스명 목록 ['check_valve', 'pump', ...]

    Returns:
        {
            'all_present': bool,
            'found_classes': ['check_valve', ...],
            'missing_classes': ['pump', ...],
            'class_positions': {'check_valve': 2, ...}  # 경로 내 위치
        }
    """
    # 심볼 ID → 클래스명 매핑
    id_to_class = {s['id']: s.get('class_name', 'unknown') for s in symbols}

    # 경로 내 클래스 수집
    path_classes = [id_to_class.get(node_id, 'unknown') for node_id in path]

    found = []
    missing = []
    positions = {}

    for req_class in required_classes:
        if req_class in path_classes:
            found.append(req_class)
            positions[req_class] = path_classes.index(req_class)
        else:
            missing.append(req_class)

    return {
        'all_present': len(missing) == 0,
        'found_classes': found,
        'missing_classes': missing,
        'class_positions': positions,
        'path_classes': path_classes
    }


def find_symbols_between(adjacency: Dict, symbols: List[Dict],
                         start_class: str, end_class: str) -> List[Dict]:
    """
    두 심볼 클래스 사이의 경로와 중간 심볼 찾기

    Args:
        adjacency: 인접 리스트
        symbols: 심볼 목록
        start_class: 시작 심볼 클래스 (예: 'ECU')
        end_class: 끝 심볼 클래스 (예: 'ANU')

    Returns:
        [{
            'start_symbol': {...},
            'end_symbol': {...},
            'path': [...],
            'intermediate_symbols': [{...}, ...],
            'path_length': int
        }, ...]
    """
    # 클래스별 심볼 그룹화
    class_to_symbols = defaultdict(list)
    id_to_symbol = {}
    for s in symbols:
        class_name = s.get('class_name', 'unknown')
        class_to_symbols[class_name].append(s)
        id_to_symbol[s['id']] = s

    start_symbols = class_to_symbols.get(start_class, [])
    end_symbols = class_to_symbols.get(end_class, [])

    results = []

    for start_sym in start_symbols:
        for end_sym in end_symbols:
            if start_sym['id'] == end_sym['id']:
                continue

            path_result = find_path_bfs(adjacency, start_sym['id'], end_sym['id'])

            if path_result['found']:
                # 중간 심볼 추출 (시작/끝 제외)
                intermediate_ids = path_result['path'][1:-1]
                intermediate_symbols = [id_to_symbol[nid] for nid in intermediate_ids
                                        if nid in id_to_symbol]

                results.append({
                    'start_symbol': start_sym,
                    'end_symbol': end_sym,
                    'path': path_result['path'],
                    'path_length': path_result['path_length'],
                    'edges': path_result['edges'],
                    'intermediate_symbols': intermediate_symbols,
                    'intermediate_classes': [s.get('class_name') for s in intermediate_symbols]
                })

    return results


# =====================
# List Generation
# =====================

def generate_bom(symbols: List[Dict]) -> List[Dict]:
    """
    BOM (Bill of Materials) 생성

    심볼 목록에서 부품 리스트 추출
    """
    bom = []

    # 카테고리별 그룹화
    category_items = defaultdict(list)
    for symbol in symbols:
        category = symbol.get('category', 'misc')
        category_items[category].append(symbol)

    item_no = 1
    for category, items in category_items.items():
        # 같은 종류의 심볼 그룹화
        class_groups = defaultdict(list)
        for item in items:
            class_name = item.get('class_name', 'unknown')
            class_groups[class_name].append(item)

        for class_name, group in class_groups.items():
            korean_name = group[0].get('korean_name', class_name)

            bom_item = {
                'item_no': item_no,
                'tag_number': f"{category.upper()[:3]}-{item_no:03d}",
                'description': korean_name,
                'class_name': class_name,
                'category': category,
                'quantity': len(group),
                'specifications': {
                    'type': class_name,
                    'instances': [
                        {
                            'id': s['id'],
                            'position': s.get('center', [0, 0]),
                            'confidence': s.get('confidence', 0)
                        }
                        for s in group
                    ]
                }
            }
            bom.append(bom_item)
            item_no += 1

    return bom


def generate_valve_signal_list(symbols: List[Dict], connections: List[Dict]) -> List[Dict]:
    """
    밸브 시그널 리스트 생성

    밸브 심볼 및 관련 제어 연결 정보 추출
    """
    valve_list = []

    # 밸브 심볼 필터링
    valves = [s for s in symbols if s.get('category') == 'valve']

    for i, valve in enumerate(valves):
        valve_id = valve['id']

        # 이 밸브에 연결된 계기/컨트롤러 찾기
        connected_instruments = []
        for conn in connections:
            if conn['from_symbol']['id'] == valve_id:
                if conn['to_symbol']['category'] == 'instrument':
                    connected_instruments.append(conn['to_symbol'])
            elif conn['to_symbol']['id'] == valve_id:
                if conn['from_symbol']['category'] == 'instrument':
                    connected_instruments.append(conn['from_symbol'])

        valve_list.append({
            'item_no': i + 1,
            'tag_number': f"V-{i + 1:03d}",
            'valve_type': valve.get('class_name', 'unknown'),
            'korean_name': valve.get('korean_name', valve.get('class_name', '')),
            'position': valve.get('center', [0, 0]),
            'signal_type': 'pneumatic' if 'control' in valve.get('class_name', '') else 'manual',
            'connected_instruments': connected_instruments,
            'control_signal': len(connected_instruments) > 0
        })

    return valve_list


def generate_equipment_list(symbols: List[Dict]) -> List[Dict]:
    """
    장비 리스트 생성

    주요 장비 (탱크, 펌프, 열교환기, 압축기) 목록 추출
    """
    equipment_categories = ['tank', 'pump', 'heat_exchanger', 'compressor']
    equipment_list = []

    equipment_no = 1
    for symbol in symbols:
        if symbol.get('category') in equipment_categories:
            category = symbol.get('category')
            prefix = {
                'tank': 'T',
                'pump': 'P',
                'heat_exchanger': 'E',
                'compressor': 'C'
            }.get(category, 'X')

            equipment_list.append({
                'equipment_no': equipment_no,
                'tag_number': f"{prefix}-{equipment_no:03d}",
                'type': symbol.get('class_name', 'unknown'),
                'korean_name': symbol.get('korean_name', ''),
                'category': category,
                'position': symbol.get('center', [0, 0]),
                'confidence': symbol.get('confidence', 0),
                'specifications': {
                    'bbox': symbol.get('bbox', []),
                    'size': {
                        'width': symbol.get('width', 0),
                        'height': symbol.get('height', 0)
                    }
                }
            })
            equipment_no += 1

    return equipment_list


# =====================
# Visualization
# =====================

def is_nearly_orthogonal(pt1: tuple, pt2: tuple, angle_threshold: float = 15.0) -> bool:
    """두 점을 연결하는 선이 거의 수평/수직인지 확인 (각도 임계값 기준)"""
    dx = abs(pt2[0] - pt1[0])
    dy = abs(pt2[1] - pt1[1])

    if dx < 1 and dy < 1:
        return True  # 같은 점

    angle = math.degrees(math.atan2(dy, dx))

    # 0°(수평) 또는 90°(수직)에 가까운지 확인
    return angle < angle_threshold or angle > (90 - angle_threshold)


def draw_orthogonal_path(vis: np.ndarray, pt1: tuple, pt2: tuple, color: tuple, thickness: int = 2):
    """두 점 사이에 직교 경로(L자형) 그리기 - 수평 먼저, 그 다음 수직"""
    mid_pt = (pt2[0], pt1[1])  # 수평 이동 후 수직 이동
    cv2.line(vis, pt1, mid_pt, color, thickness, cv2.LINE_AA)
    cv2.line(vis, mid_pt, pt2, color, thickness, cv2.LINE_AA)


def visualize_graph(image: np.ndarray, symbols: List[Dict],
                    connections: List[Dict]) -> np.ndarray:
    """
    연결 그래프 시각화 (직교 경로 사용)

    개선 v2:
    - 대각선 대신 직교 경로(L자형) 그리기
    - 너무 긴 연결은 필터링 (오탐 방지)
    - 거의 수평/수직인 라인만 직선으로 그리기
    """
    vis = image.copy()
    img_height, img_width = vis.shape[:2]

    # 색상 정의 (라인 타입별)
    COLOR_MAP = {
        'pipe': (0, 200, 0),        # 초록 (배관)
        'process': (0, 200, 0),     # 초록 (공정)
        'signal': (200, 0, 0),      # 파랑 (신호선)
        'instrument': (200, 0, 0),  # 파랑 (계장)
        'unknown': (100, 100, 100)  # 회색
    }

    # 최대 연결 거리 (이미지 대각선의 30% 이상이면 오탐으로 간주)
    max_connection_dist = ((img_width ** 2 + img_height ** 2) ** 0.5) * 0.3

    # 연결선 그리기
    drawn_count = 0
    for conn in connections:
        line_type = conn.get('line_type', 'unknown')
        color_type = conn.get('color_type', 'unknown')
        color = COLOR_MAP.get(line_type, COLOR_MAP.get(color_type, COLOR_MAP['unknown']))

        line_path = conn.get('line_path', [])

        if line_path and len(line_path) >= 2:
            pt1 = (int(line_path[0][0]), int(line_path[0][1]))
            pt2 = (int(line_path[-1][0]), int(line_path[-1][1]))
        else:
            from_center = conn['from_symbol']['center']
            to_center = conn['to_symbol']['center']
            pt1 = (int(from_center[0]), int(from_center[1]))
            pt2 = (int(to_center[0]), int(to_center[1]))

        dist = ((pt2[0] - pt1[0]) ** 2 + (pt2[1] - pt1[1]) ** 2) ** 0.5

        if dist > max_connection_dist:
            continue

        if dist < 10:
            continue

        if is_nearly_orthogonal(pt1, pt2, angle_threshold=20.0):
            cv2.line(vis, pt1, pt2, color, 2, cv2.LINE_AA)
        else:
            draw_orthogonal_path(vis, pt1, pt2, color, 2)

        cv2.circle(vis, pt1, 3, (0, 0, 255), -1)
        cv2.circle(vis, pt2, 3, (0, 0, 255), -1)

        drawn_count += 1

    logger.info(f"시각화: {drawn_count}/{len(connections)} 연결 그려짐 (거리 필터 적용)")

    # 심볼 바운딩박스 및 ID 표시
    for symbol in symbols:
        # normalize_bbox를 사용하여 다양한 bbox 형식 지원
        normalized = normalize_bbox(symbol)
        center = symbol.get('center', [0, 0])

        if normalized is not None:
            x1, y1, x2, y2 = [int(v) for v in normalized]
            cv2.rectangle(vis, (x1, y1), (x2, y2), (100, 100, 255), 1)

        pt = (int(center[0]), int(center[1]))
        text = str(symbol['id'])
        (text_w, text_h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
        cv2.rectangle(vis, (pt[0] - 2, pt[1] - text_h - 2),
                      (pt[0] + text_w + 2, pt[1] + 2), (0, 0, 0), -1)
        cv2.putText(vis, text, pt, cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

    return vis


def numpy_to_base64(image: np.ndarray) -> str:
    """NumPy 이미지를 Base64로 변환"""
    _, buffer = cv2.imencode('.png', image)
    return base64.b64encode(buffer).decode('utf-8')
