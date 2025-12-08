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

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_PORT = int(os.getenv("PID_ANALYZER_PORT", "5018"))


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

def find_symbol_connections(symbols: List[Dict], lines: List[Dict],
                            intersections: List[Dict]) -> List[Dict]:
    """
    심볼 간 연결 관계 분석

    알고리즘:
    1. 각 라인의 끝점이 어떤 심볼의 bbox 내에 있는지 확인
    2. 양쪽 끝점이 각각 다른 심볼에 연결되면 두 심볼이 연결된 것
    """
    connections = []
    connection_id = 0

    for line in lines:
        start = line['start_point']
        end = line['end_point']

        from_symbol = None
        to_symbol = None

        for symbol in symbols:
            bbox = symbol.get('bbox', [])
            if len(bbox) == 4:
                x1, y1, x2, y2 = bbox

                # 시작점이 심볼 내에 있는지 (약간의 마진 허용)
                margin = 10
                if (x1 - margin <= start[0] <= x2 + margin and
                    y1 - margin <= start[1] <= y2 + margin):
                    from_symbol = symbol

                # 끝점이 심볼 내에 있는지
                if (x1 - margin <= end[0] <= x2 + margin and
                    y1 - margin <= end[1] <= y2 + margin):
                    to_symbol = symbol

        # 두 심볼이 연결된 경우
        if from_symbol and to_symbol and from_symbol['id'] != to_symbol['id']:
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
                'line_id': line.get('id', 0)
            })
            connection_id += 1

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


def visualize_graph(image: np.ndarray, symbols: List[Dict],
                    connections: List[Dict]) -> np.ndarray:
    """
    연결 그래프 시각화
    """
    vis = image.copy()

    # 연결선 그리기
    for conn in connections:
        from_center = conn['from_symbol']['center']
        to_center = conn['to_symbol']['center']

        color = (0, 255, 0) if conn['line_type'] == 'pipe' else (255, 0, 0)

        pt1 = (int(from_center[0]), int(from_center[1]))
        pt2 = (int(to_center[0]), int(to_center[1]))

        cv2.line(vis, pt1, pt2, color, 2)
        cv2.circle(vis, pt1, 5, (0, 0, 255), -1)
        cv2.circle(vis, pt2, 5, (0, 0, 255), -1)

    # 심볼 ID 표시
    for symbol in symbols:
        center = symbol.get('center', [0, 0])
        pt = (int(center[0]), int(center[1]))
        cv2.putText(vis, str(symbol['id']), pt, cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (255, 255, 255), 2)

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
            {"name": "symbols", "type": "Detection[]", "required": True, "description": "YOLO-PID 검출 결과"},
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
            {"name": "visualize", "type": "boolean", "default": True, "description": "결과 시각화"}
        ]
    }


@app.post("/api/v1/analyze", response_model=ProcessResponse)
async def analyze(
    symbols: List[Dict] = Body(..., description="YOLO-PID 검출 결과"),
    lines: List[Dict] = Body(default=[], description="Line Detector 결과"),
    intersections: List[Dict] = Body(default=[], description="교차점 정보"),
    image_base64: Optional[str] = Body(default=None, description="원본 이미지 (Base64)"),
    should_generate_bom: bool = Body(default=True, alias="generate_bom"),
    should_generate_valve_list: bool = Body(default=True, alias="generate_valve_list"),
    should_generate_equipment_list: bool = Body(default=True, alias="generate_equipment_list"),
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
    """
    start_time = time.time()

    try:
        logger.info(f"Analyzing P&ID: {len(symbols)} symbols, {len(lines)} lines")

        # 연결 관계 분석
        connections = find_symbol_connections(symbols, lines, intersections)
        logger.info(f"Found {len(connections)} connections")

        # 연결성 그래프 구축
        graph = build_connectivity_graph(symbols, connections)

        # BOM 생성
        bom_result = []
        if should_generate_bom:
            bom_result = generate_bom(symbols)
            logger.info(f"Generated BOM with {len(bom_result)} items")

        # 밸브 시그널 리스트
        valve_list_result = []
        if should_generate_valve_list:
            valve_list_result = generate_valve_signal_list(symbols, connections)
            logger.info(f"Generated valve list with {len(valve_list_result)} items")

        # 장비 리스트
        equipment_list_result = []
        if should_generate_equipment_list:
            equipment_list_result = generate_equipment_list(symbols)
            logger.info(f"Generated equipment list with {len(equipment_list_result)} items")

        # 시각화
        visualization_base64 = None
        if visualize and image_base64:
            try:
                # Base64 이미지 디코딩
                image_data = base64.b64decode(image_base64)
                nparr = np.frombuffer(image_data, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                if image is not None:
                    vis_image = visualize_graph(image, symbols, connections)
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
            "statistics": {
                "total_symbols": len(symbols),
                "total_connections": len(connections),
                "bom_items": len(bom_result),
                "valves": len(valve_list_result),
                "equipment": len(equipment_list_result)
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
    이미지 직접 입력 시 내부적으로 YOLO-PID와 Line Detector 호출
    (외부 API 호출 필요)
    """
    return ProcessResponse(
        success=False,
        data={},
        processing_time=0,
        error="Direct image processing not implemented. Use /api/v1/analyze with pre-processed data."
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
