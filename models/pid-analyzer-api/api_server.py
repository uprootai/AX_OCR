"""
P&ID Analyzer API Server
P&ID 연결성 분석 및 BOM 추출 API

기술:
- Graph 기반 연결성 분석
- 심볼-라인 연결 관계 추출
- BOM (Bill of Materials) 자동 생성
- 밸브 시그널 리스트 생성
- 장비 리스트 생성

포트: 5018
"""
import os
import time
import logging
import base64
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from collections import defaultdict

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import cv2
import numpy as np
import httpx
import re
import io

# 장비 분석 모듈 (범용)
from equipment_analyzer import (
    # 범용 API (신규)
    detect_equipment,
    get_equipment_summary,
    check_profile_context,
    generate_equipment_list_excel,
    extract_signal_region_equipment,
    get_available_profiles,
    get_profile_equipment_types,
    EQUIPMENT_PROFILES,
    # Legacy 호환 (BWMS)
    detect_bwms_equipment,
    get_bwms_equipment_summary,
    check_bwms_context,
    generate_bwms_equipment_list_excel,
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_PORT = int(os.getenv("PID_ANALYZER_PORT", "5018"))
EASYOCR_API_URL = os.getenv("EASYOCR_API_URL", "http://easyocr-api:5015/api/v1/ocr")

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
# Schemas
# =====================

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str


class Connection(BaseModel):
    id: int
    from_symbol: Dict[str, Any]
    to_symbol: Dict[str, Any]
    line_type: str
    line_id: int


class BOMItem(BaseModel):
    item_no: int
    tag_number: str
    description: str
    category: str
    quantity: int
    specifications: Dict[str, Any]


class ProcessResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    processing_time: float
    error: Optional[str] = None


# =====================
# Core Functions
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


def point_to_symbol_distance(point: Tuple[float, float], symbol: Dict) -> float:
    """점에서 심볼 bbox까지의 최소 거리 계산"""
    bbox = symbol.get('bbox', [])
    if len(bbox) != 4:
        return float('inf')

    x1, y1, x2, y2 = bbox
    px, py = point

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

    # 설정값
    DIRECT_MARGIN = 50  # 직접 연결 최대 거리 (픽셀)
    EXTENDED_MARGIN = 100  # 확장 연결 최대 거리

    # 1. 직접 연결 탐지 (라인 끝점이 심볼에 닿는 경우)
    for line in lines:
        start = tuple(line.get('start_point', [0, 0]))
        end = tuple(line.get('end_point', [0, 0]))

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
    # 교차점을 통해 연결된 라인들을 추적하여 심볼 연결 발견
    if intersections:
        # 라인 ID로 인덱싱
        line_by_id = {line.get('id', i): line for i, line in enumerate(lines)}

        # 교차점별 연결된 라인 그룹화
        intersection_lines = defaultdict(list)
        for inter in intersections:
            # 교차점 좌표 (point 배열 형식 또는 x,y 형식 모두 지원)
            point_data = inter.get('point', [])
            if point_data:
                inter_point = (point_data[0], point_data[1])
            else:
                inter_point = (inter.get('x', 0), inter.get('y', 0))

            # 교차하는 두 라인 ID 가져오기
            line1_id = inter.get('line1_id')
            line2_id = inter.get('line2_id')

            if line1_id is not None and line1_id in line_by_id:
                intersection_lines[inter_point].append(line_by_id[line1_id])
            if line2_id is not None and line2_id in line_by_id:
                intersection_lines[inter_point].append(line_by_id[line2_id])

        # 같은 교차점을 공유하는 라인들의 심볼 연결 발견
        for inter_point, inter_lines in intersection_lines.items():
            if len(inter_lines) >= 2:
                # 각 라인에서 교차점 반대편 끝점의 심볼 찾기
                connected_symbols = []
                for line in inter_lines:
                    start = tuple(line.get('start_point', [0, 0]))
                    end = tuple(line.get('end_point', [0, 0]))

                    # 교차점에서 먼 끝점 찾기
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
                            # 라인 경로 정보 (far_point -> intersection)
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

                                # 색상 정보 추출
                                color_type = connected_symbols[i].get('color_type', 'unknown')
                                color_info = LINE_COLOR_TYPES.get(color_type, LINE_COLOR_TYPES['unknown'])

                                # 스타일 정보 추출
                                line_style = connected_symbols[i].get('line_style', 'unknown')
                                style_info = LINE_STYLE_TYPES.get(line_style, LINE_STYLE_TYPES['unknown'])

                                # 교차점을 통한 실제 라인 경로: 심볼1 -> 교차점 -> 심볼2
                                line_path = [
                                    connected_symbols[i]['line_start'],  # 심볼1 근처 끝점
                                    list(inter_point),                    # 교차점
                                    connected_symbols[j]['line_start']   # 심볼2 근처 끝점
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
                                    'confidence': 0.7,  # 간접 연결은 신뢰도 낮춤
                                    'intersection_point': list(inter_point),
                                    'line_ids': [connected_symbols[i]['line_id'], connected_symbols[j]['line_id']],
                                    # 실제 라인 경로 (심볼1 -> 교차점 -> 심볼2)
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
    # 인접 리스트 생성
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

    # 그래프 통계
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


def is_nearly_orthogonal(pt1: tuple, pt2: tuple, angle_threshold: float = 15.0) -> bool:
    """두 점을 연결하는 선이 거의 수평/수직인지 확인 (각도 임계값 기준)"""
    import math
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
        # 라인 타입에 따른 색상 선택
        line_type = conn.get('line_type', 'unknown')
        color_type = conn.get('color_type', 'unknown')
        color = COLOR_MAP.get(line_type, COLOR_MAP.get(color_type, COLOR_MAP['unknown']))

        # line_path에서 시작점과 끝점 추출
        line_path = conn.get('line_path', [])

        if line_path and len(line_path) >= 2:
            pt1 = (int(line_path[0][0]), int(line_path[0][1]))
            pt2 = (int(line_path[-1][0]), int(line_path[-1][1]))
        else:
            # line_path가 없으면 심볼 중심점 사용
            from_center = conn['from_symbol']['center']
            to_center = conn['to_symbol']['center']
            pt1 = (int(from_center[0]), int(from_center[1]))
            pt2 = (int(to_center[0]), int(to_center[1]))

        # 연결 거리 계산
        dist = ((pt2[0] - pt1[0]) ** 2 + (pt2[1] - pt1[1]) ** 2) ** 0.5

        # 너무 긴 연결은 건너뛰기 (오탐 가능성 높음)
        if dist > max_connection_dist:
            continue

        # 매우 짧은 연결도 건너뛰기 (같은 심볼 내 연결)
        if dist < 10:
            continue

        # 거의 수평/수직이면 직선, 아니면 직교 경로(L자형)
        if is_nearly_orthogonal(pt1, pt2, angle_threshold=20.0):
            cv2.line(vis, pt1, pt2, color, 2, cv2.LINE_AA)
        else:
            draw_orthogonal_path(vis, pt1, pt2, color, 2)

        # 끝점 표시
        cv2.circle(vis, pt1, 3, (0, 0, 255), -1)
        cv2.circle(vis, pt2, 3, (0, 0, 255), -1)

        drawn_count += 1

    logger.info(f"시각화: {drawn_count}/{len(connections)} 연결 그려짐 (거리 필터 적용)")

    # 심볼 바운딩박스 및 ID 표시
    for symbol in symbols:
        bbox = symbol.get('bbox', [])
        center = symbol.get('center', [0, 0])

        # 바운딩박스 그리기
        if len(bbox) == 4:
            x1, y1, x2, y2 = [int(v) for v in bbox]
            cv2.rectangle(vis, (x1, y1), (x2, y2), (100, 100, 255), 1)

        # ID 텍스트 표시
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


# =====================
# FastAPI App
# =====================

app = FastAPI(
    title="P&ID Analyzer API",
    description="P&ID 연결성 분석 및 BOM 추출 API",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================
# API Endpoints
# =====================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스체크"""
    return HealthResponse(
        status="healthy",
        service="pid-analyzer-api",
        version="1.0.0",
        timestamp=datetime.now().isoformat()
    )


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check_v1():
    """헬스체크 (v1 경로)"""
    return await health_check()


@app.get("/api/v1/info")
async def get_info():
    """API 정보 (BlueprintFlow 메타데이터)"""
    return {
        "id": "pid-analyzer",
        "name": "P&ID Analyzer",
        "display_name": "P&ID 연결성 분석기",
        "version": "1.0.0",
        "description": "P&ID 연결성 분석 및 BOM 추출 API",
        "base_url": f"http://localhost:{API_PORT}",
        "endpoint": "/api/v1/analyze",
        "method": "POST",
        "requires_image": False,
        "blueprintflow": {
            "category": "analysis",
            "color": "#ef4444",
            "icon": "Network"
        },
        "inputs": [
            {"name": "symbols", "type": "Detection[]", "required": True, "description": "YOLO 검출 결과 (model_type=pid_class_aware)"},
            {"name": "lines", "type": "LineSegment[]", "required": True, "description": "Line Detector 결과"},
            {"name": "image", "type": "Image", "required": False, "description": "원본 이미지 (시각화용)"}
        ],
        "outputs": [
            {"name": "connections", "type": "Connection[]", "description": "연결 관계 목록"},
            {"name": "graph", "type": "Graph", "description": "연결성 그래프"},
            {"name": "bom", "type": "BOMItem[]", "description": "부품 리스트"},
            {"name": "valve_list", "type": "ValveSignal[]", "description": "밸브 시그널 리스트"},
            {"name": "equipment_list", "type": "Equipment[]", "description": "장비 리스트"}
        ],
        "parameters": [
            {"name": "generate_bom", "type": "boolean", "default": True, "description": "BOM 생성"},
            {"name": "generate_valve_list", "type": "boolean", "default": True, "description": "밸브 시그널 리스트 생성"},
            {"name": "generate_equipment_list", "type": "boolean", "default": True, "description": "장비 리스트 생성"},
            {"name": "enable_ocr", "type": "boolean", "default": True, "description": "OCR 기반 계기 태그 검출 (EasyOCR)"},
            {"name": "visualize", "type": "boolean", "default": True, "description": "결과 시각화"}
        ]
    }


@app.post("/api/v1/analyze", response_model=ProcessResponse)
async def analyze(
    symbols: List[Dict] = Body(..., description="YOLO 검출 결과 (model_type=pid_class_aware)"),
    lines: List[Dict] = Body(default=[], description="Line Detector 결과"),
    intersections: List[Dict] = Body(default=[], description="교차점 정보"),
    image_base64: Optional[str] = Body(default=None, description="원본 이미지 (Base64)"),
    should_generate_bom: bool = Body(default=True, alias="generate_bom"),
    should_generate_valve_list: bool = Body(default=True, alias="generate_valve_list"),
    should_generate_equipment_list: bool = Body(default=True, alias="generate_equipment_list"),
    enable_ocr: bool = Body(default=True, alias="enable_ocr", description="OCR 기반 계기 태그 검출 활성화"),
    visualize: bool = Body(default=True)
):
    """
    P&ID 분석 메인 엔드포인트

    기능:
    - 심볼 간 연결 관계 분석
    - 연결성 그래프 구축
    - BOM 자동 생성
    - 밸브 시그널 리스트 생성
    - 장비 리스트 생성
    - OCR 기반 계기 태그 검출 및 병합 (옵션)
    """
    start_time = time.time()

    try:
        logger.info(f"Analyzing P&ID: {len(symbols)} symbols, {len(lines)} lines, OCR={enable_ocr}")

        # OCR 기반 계기 검출 (이미지가 있고 enable_ocr이 True인 경우)
        ocr_instruments = []
        merged_symbols = symbols

        if enable_ocr and image_base64:
            try:
                image_bytes = base64.b64decode(image_base64)
                ocr_instruments = detect_instruments_via_ocr(image_bytes)
                if ocr_instruments:
                    merged_symbols = merge_symbols_with_ocr(symbols, ocr_instruments)
                    logger.info(f"OCR detected {len(ocr_instruments)} instruments, merged total: {len(merged_symbols)}")
            except Exception as e:
                logger.warning(f"OCR detection failed, using YOLO symbols only: {e}")
                merged_symbols = symbols

        # 연결 관계 분석 (병합된 심볼 사용)
        connections = find_symbol_connections(merged_symbols, lines, intersections)
        logger.info(f"Found {len(connections)} connections")

        # 연결성 그래프 구축 (병합된 심볼 사용)
        graph = build_connectivity_graph(merged_symbols, connections)

        # BOM 생성 (병합된 심볼 사용)
        bom_result = []
        if should_generate_bom:
            bom_result = generate_bom(merged_symbols)
            logger.info(f"Generated BOM with {len(bom_result)} items")

        # 밸브 시그널 리스트 (병합된 심볼 사용)
        valve_list_result = []
        if should_generate_valve_list:
            valve_list_result = generate_valve_signal_list(merged_symbols, connections)
            logger.info(f"Generated valve list with {len(valve_list_result)} items")

        # 장비 리스트 (병합된 심볼 사용)
        equipment_list_result = []
        if should_generate_equipment_list:
            equipment_list_result = generate_equipment_list(merged_symbols)
            logger.info(f"Generated equipment list with {len(equipment_list_result)} items")

        # 시각화 (병합된 심볼 사용)
        visualization_base64 = None
        if visualize and image_base64:
            try:
                # Base64 이미지 디코딩
                image_data = base64.b64decode(image_base64)
                nparr = np.frombuffer(image_data, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                if image is not None:
                    vis_image = visualize_graph(image, merged_symbols, connections)
                    visualization_base64 = numpy_to_base64(vis_image)
            except Exception as e:
                logger.warning(f"Visualization failed: {e}")

        processing_time = time.time() - start_time

        result = {
            "connections": connections,
            "graph": graph,
            "bom": bom_result,
            "valve_list": valve_list_result,
            "equipment_list": equipment_list_result,
            "visualization": visualization_base64,
            "ocr_instruments": ocr_instruments,  # OCR 검출 결과 추가
            "statistics": {
                "total_symbols": len(merged_symbols),
                "yolo_symbols": len(symbols),
                "ocr_instruments": len(ocr_instruments),
                "total_connections": len(connections),
                "bom_items": len(bom_result),
                "valves": len(valve_list_result),
                "equipment": len(equipment_list_result),
                # 색상 기반 연결 통계
                "connections_by_color_type": {
                    color_type: len([c for c in connections if c.get('color_type') == color_type])
                    for color_type in set(c.get('color_type', 'unknown') for c in connections)
                },
                "connections_by_pipe_type": {
                    pipe_type: len([c for c in connections if c.get('pipe_type') == pipe_type])
                    for pipe_type in set(c.get('pipe_type', 'unknown') for c in connections)
                },
                # 스타일 기반 연결 통계
                "connections_by_line_style": {
                    style: len([c for c in connections if c.get('line_style') == style])
                    for style in set(c.get('line_style', 'unknown') for c in connections)
                },
                "connections_by_signal_type": {
                    sig_type: len([c for c in connections if c.get('signal_type') == sig_type])
                    for sig_type in set(c.get('signal_type', 'unknown') for c in connections)
                }
            }
        }

        return ProcessResponse(
            success=True,
            data=result,
            processing_time=round(processing_time, 3)
        )

    except Exception as e:
        logger.error(f"Analysis error: {e}")
        import traceback
        traceback.print_exc()
        return ProcessResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=str(e)
        )


@app.post("/api/v1/process", response_model=ProcessResponse)
async def process(
    file: UploadFile = File(..., description="P&ID 도면 이미지 (결합 분석용)"),
):
    """
    이미지 직접 입력 시 내부적으로 YOLO와 Line Detector 호출
    (외부 API 호출 필요)
    """
    return ProcessResponse(
        success=False,
        data={},
        processing_time=0,
        error="Direct image processing not implemented. Use /api/v1/analyze with pre-processed data."
    )


# =====================
# BWMS API Endpoints
# =====================

PADDLEOCR_API_URL = os.getenv("PADDLEOCR_API_URL", "http://paddleocr-api:5006/api/v1/ocr")


@app.post("/api/v1/bwms/detect-equipment")
async def detect_bwms_equipment_endpoint(
    file: UploadFile = File(..., description="P&ID 도면 이미지"),
    language: str = Form(default="en", description="OCR 언어 (en/ko)")
):
    """
    BWMS 장비 태그 검출 API

    P&ID 도면에서 BWMS 전용 장비(ECU, FMU, HGU 등)를 자동 인식합니다.
    """
    start_time = time.time()

    try:
        # 이미지 읽기
        image_bytes = await file.read()

        # PaddleOCR로 텍스트 추출
        async with httpx.AsyncClient(timeout=120.0) as client:
            files = {"file": (file.filename, image_bytes, file.content_type)}
            data = {"language": language}
            response = await client.post(PADDLEOCR_API_URL, files=files, data=data)

        if response.status_code != 200:
            return ProcessResponse(
                success=False,
                data={},
                processing_time=time.time() - start_time,
                error=f"OCR API error: {response.status_code}"
            )

        ocr_result = response.json()
        ocr_texts = ocr_result.get('detections', [])

        if not ocr_texts:
            ocr_texts = ocr_result.get('texts', [])

        logger.info(f"OCR detected {len(ocr_texts)} texts")

        # BWMS 컨텍스트 확인
        bwms_context = check_bwms_context(ocr_texts)

        # BWMS 장비 검출
        equipment = detect_bwms_equipment(ocr_texts)
        summary = get_bwms_equipment_summary(equipment)

        processing_time = time.time() - start_time

        return ProcessResponse(
            success=True,
            data={
                'equipment': equipment,
                'summary': summary,
                'bwms_context': bwms_context,
                'ocr_count': len(ocr_texts)
            },
            processing_time=round(processing_time, 3)
        )

    except Exception as e:
        logger.error(f"BWMS detection error: {e}")
        import traceback
        traceback.print_exc()
        return ProcessResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=str(e)
        )


@app.post("/api/v1/bwms/generate-equipment-list")
async def generate_bwms_equipment_list_endpoint(
    file: UploadFile = File(..., description="P&ID 도면 이미지"),
    project_name: str = Form(default="Unknown Project", description="프로젝트명"),
    hull_no: str = Form(default="N/A", description="선체 번호"),
    drawing_no: str = Form(default="N/A", description="도면 번호"),
    language: str = Form(default="en", description="OCR 언어")
):
    """
    BWMS Equipment List Excel 생성 API

    P&ID 도면에서 BWMS 장비를 검출하고 Excel 파일로 출력합니다.
    """
    from fastapi.responses import Response

    start_time = time.time()

    try:
        # 이미지 읽기
        image_bytes = await file.read()

        # PaddleOCR로 텍스트 추출
        async with httpx.AsyncClient(timeout=120.0) as client:
            files = {"file": (file.filename, image_bytes, "image/png")}
            data = {"language": language}
            response = await client.post(PADDLEOCR_API_URL, files=files, data=data)

        if response.status_code != 200:
            return ProcessResponse(
                success=False,
                data={},
                processing_time=time.time() - start_time,
                error=f"OCR API error: {response.status_code}"
            )

        ocr_result = response.json()
        ocr_texts = ocr_result.get('detections', [])

        if not ocr_texts:
            ocr_texts = ocr_result.get('texts', [])

        # BWMS 장비 검출
        equipment = detect_bwms_equipment(ocr_texts)

        if not equipment:
            return ProcessResponse(
                success=False,
                data={},
                processing_time=time.time() - start_time,
                error="No BWMS equipment detected in the image"
            )

        # Excel 생성
        project_info = {
            'name': project_name,
            'hull_no': hull_no,
            'drawing_no': drawing_no
        }

        excel_bytes = generate_bwms_equipment_list_excel(equipment, project_info)

        # 파일명 생성
        filename = f"BWMS_Equipment_List_{hull_no}_{datetime.now().strftime('%Y%m%d')}.xlsx"

        logger.info(f"Generated Excel: {filename} with {len(equipment)} equipment")

        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Equipment-Count": str(len(equipment)),
                "X-Processing-Time": str(round(time.time() - start_time, 3))
            }
        )

    except ImportError as e:
        return ProcessResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=f"Missing dependency: {e}. Install with: pip install openpyxl"
        )
    except Exception as e:
        logger.error(f"Excel generation error: {e}")
        import traceback
        traceback.print_exc()
        return ProcessResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=str(e)
        )


@app.get("/api/v1/bwms/equipment-types")
async def get_bwms_equipment_types():
    """
    BWMS 장비 타입 목록 조회 (Legacy)

    지원하는 BWMS 장비 타입 및 설명을 반환합니다.
    새로운 API: /api/v1/equipment/profiles/bwms/types 사용 권장
    """
    bwms_profile = EQUIPMENT_PROFILES.get('bwms', {})
    bwms_equipment = bwms_profile.get('equipment', {})

    return {
        "success": True,
        "data": {
            "equipment_types": [
                {
                    "type": equip_type,
                    "name_ko": info["name_ko"],
                    "name_en": info["name_en"],
                    "description": info["description"],
                    "category": info["category"],
                    "pattern": info["pattern"]
                }
                for equip_type, info in bwms_equipment.items()
            ],
            "total_types": len(bwms_equipment)
        }
    }


# =====================
# Generic Equipment API Endpoints (신규 범용 API)
# =====================

@app.get("/api/v1/equipment/profiles")
async def list_equipment_profiles():
    """
    사용 가능한 장비 프로파일 목록 조회

    프로파일: 특정 산업/분야에 맞는 장비 패턴 세트
    - bwms: 선박 평형수 처리 시스템
    - hvac: 공조 시스템
    - process: 일반 공정
    """
    return {
        "success": True,
        "data": {
            "profiles": get_available_profiles(),
            "total": len(EQUIPMENT_PROFILES)
        }
    }


@app.get("/api/v1/equipment/profiles/{profile_id}")
async def get_equipment_profile_detail(profile_id: str):
    """
    특정 프로파일 상세 정보 조회
    """
    profile = EQUIPMENT_PROFILES.get(profile_id)
    if not profile:
        return {
            "success": False,
            "error": f"Profile '{profile_id}' not found. Available: {list(EQUIPMENT_PROFILES.keys())}"
        }

    return {
        "success": True,
        "data": {
            "id": profile_id,
            "name": profile['name'],
            "name_ko": profile['name_ko'],
            "description": profile['description'],
            "context_keywords": profile.get('context_keywords', []),
            "equipment_types": get_profile_equipment_types(profile_id),
            "equipment_count": len(profile['equipment'])
        }
    }


@app.post("/api/v1/equipment/detect")
async def detect_equipment_endpoint(
    file: UploadFile = File(..., description="P&ID 도면 이미지"),
    profile_id: str = Form(default="bwms", description="장비 프로파일 (bwms/hvac/process)"),
    language: str = Form(default="en", description="OCR 언어 (en/ko)")
):
    """
    장비 태그 검출 API (범용)

    선택한 프로파일에 따라 P&ID 도면에서 장비 태그를 자동 인식합니다.

    Parameters:
    - profile_id: 사용할 장비 프로파일 (bwms, hvac, process)
    - language: OCR 언어 설정
    """
    start_time = time.time()

    try:
        # 프로파일 유효성 검사
        if profile_id not in EQUIPMENT_PROFILES:
            return ProcessResponse(
                success=False,
                data={"available_profiles": list(EQUIPMENT_PROFILES.keys())},
                processing_time=time.time() - start_time,
                error=f"Unknown profile: {profile_id}"
            )

        # 이미지 읽기
        image_bytes = await file.read()

        # PaddleOCR로 텍스트 추출
        async with httpx.AsyncClient(timeout=120.0) as client:
            files = {"file": (file.filename, image_bytes, file.content_type)}
            data = {"language": language}
            response = await client.post(PADDLEOCR_API_URL, files=files, data=data)

        if response.status_code != 200:
            return ProcessResponse(
                success=False,
                data={},
                processing_time=time.time() - start_time,
                error=f"OCR API error: {response.status_code}"
            )

        ocr_result = response.json()
        ocr_texts = ocr_result.get('detections', [])
        if not ocr_texts:
            ocr_texts = ocr_result.get('texts', [])

        logger.info(f"OCR detected {len(ocr_texts)} texts")

        # 프로파일 컨텍스트 확인
        context_check = check_profile_context(ocr_texts, profile_id)

        # 장비 검출 (선택된 프로파일 사용)
        equipment = detect_equipment(ocr_texts, profile_id=profile_id)
        summary = get_equipment_summary(equipment) if equipment else {}

        processing_time = time.time() - start_time

        return ProcessResponse(
            success=True,
            data={
                'equipment': equipment,
                'summary': summary,
                'profile': {
                    'id': profile_id,
                    'name': EQUIPMENT_PROFILES[profile_id]['name_ko']
                },
                'context_check': context_check,
                'ocr_count': len(ocr_texts)
            },
            processing_time=round(processing_time, 3)
        )

    except Exception as e:
        logger.error(f"Equipment detection error: {e}")
        import traceback
        traceback.print_exc()
        return ProcessResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=str(e)
        )


@app.post("/api/v1/equipment/export-excel")
async def export_equipment_excel_endpoint(
    file: UploadFile = File(..., description="P&ID 도면 이미지"),
    profile_id: str = Form(default="bwms", description="장비 프로파일"),
    project_name: str = Form(default="Unknown Project", description="프로젝트명"),
    drawing_no: str = Form(default="N/A", description="도면 번호"),
    language: str = Form(default="en", description="OCR 언어")
):
    """
    장비 목록 Excel 내보내기 API (범용)

    P&ID 도면에서 장비를 검출하고 Excel 파일로 출력합니다.

    Parameters:
    - profile_id: 사용할 장비 프로파일
    - project_name: Excel에 표시할 프로젝트명
    - drawing_no: 도면 번호
    """
    from fastapi.responses import Response

    start_time = time.time()

    try:
        # 프로파일 유효성 검사
        if profile_id not in EQUIPMENT_PROFILES:
            return ProcessResponse(
                success=False,
                data={"available_profiles": list(EQUIPMENT_PROFILES.keys())},
                processing_time=time.time() - start_time,
                error=f"Unknown profile: {profile_id}"
            )

        # 이미지 읽기
        image_bytes = await file.read()

        # PaddleOCR로 텍스트 추출
        async with httpx.AsyncClient(timeout=120.0) as client:
            files = {"file": (file.filename, image_bytes, "image/png")}
            data = {"language": language}
            response = await client.post(PADDLEOCR_API_URL, files=files, data=data)

        if response.status_code != 200:
            return ProcessResponse(
                success=False,
                data={},
                processing_time=time.time() - start_time,
                error=f"OCR API error: {response.status_code}"
            )

        ocr_result = response.json()
        ocr_texts = ocr_result.get('detections', [])
        if not ocr_texts:
            ocr_texts = ocr_result.get('texts', [])

        # 장비 검출
        equipment = detect_equipment(ocr_texts, profile_id=profile_id)

        if not equipment:
            return ProcessResponse(
                success=False,
                data={},
                processing_time=time.time() - start_time,
                error=f"No equipment detected with profile '{profile_id}'"
            )

        # Excel 생성
        project_info = {
            'name': project_name,
            'drawing_no': drawing_no
        }

        excel_bytes = generate_equipment_list_excel(equipment, project_info, profile_id)

        # 파일명 생성
        profile_name = profile_id.upper()
        filename = f"{profile_name}_Equipment_List_{drawing_no}_{datetime.now().strftime('%Y%m%d')}.xlsx"

        logger.info(f"Generated Excel: {filename} with {len(equipment)} equipment")

        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Equipment-Count": str(len(equipment)),
                "X-Profile": profile_id,
                "X-Processing-Time": str(round(time.time() - start_time, 3))
            }
        )

    except ImportError as e:
        return ProcessResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=f"Missing dependency: {e}. Install with: pip install openpyxl"
        )
    except Exception as e:
        logger.error(f"Excel export error: {e}")
        import traceback
        traceback.print_exc()
        return ProcessResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=str(e)
        )


# =====================
# Main
# =====================

if __name__ == "__main__":
    logger.info(f"Starting P&ID Analyzer API on port {API_PORT}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=API_PORT,
        log_level="info"
    )
