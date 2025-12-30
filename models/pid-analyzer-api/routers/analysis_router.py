"""
P&ID Analysis Router
/api/v1/analyze, /api/v1/process 엔드포인트
"""

import os
import time
import base64
import logging
from typing import Optional, List, Dict

from fastapi import APIRouter, File, UploadFile, Body
import cv2
import numpy as np

from services.analysis_service import (
    detect_instruments_via_ocr,
    merge_symbols_with_ocr,
    find_symbol_connections,
    build_connectivity_graph,
    generate_bom,
    generate_valve_signal_list,
    generate_equipment_list,
    visualize_graph,
    numpy_to_base64,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Analysis"])

# Configuration
API_PORT = int(os.getenv("PID_ANALYZER_PORT", "5018"))


# =====================
# Schemas (inline for router)
# =====================

from pydantic import BaseModel


class ProcessResponse(BaseModel):
    success: bool
    data: Dict
    processing_time: float
    error: Optional[str] = None


# =====================
# Endpoints
# =====================

@router.get("/info")
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
            {"name": "texts", "type": "OCRText[]", "required": False, "description": "OCR 텍스트 결과 (PaddleOCR, SIGNAL FOR BWMS 영역 밸브 추출용)"},
            {"name": "regions", "type": "Region[]", "required": False, "description": "Line Detector 영역 (점선 박스, BWMS Signal 영역)"},
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


@router.post("/analyze", response_model=ProcessResponse)
async def analyze(
    symbols: List[Dict] = Body(..., description="YOLO 검출 결과 (model_type=pid_class_aware)"),
    lines: List[Dict] = Body(default=[], description="Line Detector 결과"),
    intersections: List[Dict] = Body(default=[], description="교차점 정보"),
    texts: List[Dict] = Body(default=[], description="OCR 텍스트 결과 (PaddleOCR 등)"),
    regions: List[Dict] = Body(default=[], description="Line Detector 영역 (점선 박스 등)"),
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
        # 심볼 전처리: ID가 없는 경우 자동 할당
        for i, sym in enumerate(symbols):
            if 'id' not in sym:
                class_name = sym.get('class_name', sym.get('label', 'symbol'))
                sym['id'] = f"{class_name}_{i+1}"

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

        # 밸브 시그널 리스트
        # 1순위: OCR 텍스트 + Line Detector 영역 기반 추출 (SIGNAL FOR BWMS 영역)
        # 2순위: YOLO 심볼 기반 추출 (기존 방식)
        valve_list_result = []
        region_valve_extraction = {}
        if should_generate_valve_list:
            # OCR + Region 기반 추출 시도
            if texts:
                try:
                    from region_extractor import get_extractor
                    extractor = get_extractor()
                    region_result = extractor.extract(
                        regions=regions,
                        texts=texts,
                        rule_ids=["valve_signal_bwms"],
                        region_expand_margin=150  # 영역 확장 마진
                    )
                    region_valves = region_result.get("all_extracted_items", [])
                    if region_valves:
                        # Region 기반 추출 결과를 valve_list 형식으로 변환
                        for i, valve in enumerate(region_valves):
                            valve_list_result.append({
                                "item_no": i + 1,
                                "tag_number": valve.get("id", f"V-{i+1:03d}"),
                                "valve_type": valve.get("type", "valve_tag"),
                                "korean_name": "BWMS 밸브",
                                "position": valve.get("center", [0, 0]),
                                "signal_type": "SIGNAL FOR BWMS",
                                "confidence": valve.get("confidence", 0.0),
                                "source": "ocr_region"
                            })
                        region_valve_extraction = region_result.get("statistics", {})
                        logger.info(f"Region-based valve extraction: {len(valve_list_result)} valves from OCR")
                except Exception as e:
                    logger.warning(f"Region-based valve extraction failed: {e}")

            # Region 기반 추출 결과가 없으면 YOLO 심볼 기반 추출
            if not valve_list_result:
                valve_list_result = generate_valve_signal_list(merged_symbols, connections)
                logger.info(f"Symbol-based valve list: {len(valve_list_result)} items")

        # 장비 리스트 (병합된 심볼 사용)
        equipment_list_result = []
        if should_generate_equipment_list:
            equipment_list_result = generate_equipment_list(merged_symbols)
            logger.info(f"Generated equipment list with {len(equipment_list_result)} items")

        # 시각화 (병합된 심볼 사용)
        visualization_base64 = None
        if visualize and image_base64:
            try:
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
            "ocr_instruments": ocr_instruments,
            "statistics": {
                "total_symbols": len(merged_symbols),
                "yolo_symbols": len(symbols),
                "ocr_instruments": len(ocr_instruments),
                "ocr_texts": len(texts),
                "line_detector_regions": len(regions),
                "total_connections": len(connections),
                "bom_items": len(bom_result),
                "valves": len(valve_list_result),
                "valve_extraction_method": "ocr_region" if region_valve_extraction else "symbol_based",
                "region_valve_stats": region_valve_extraction,
                "equipment": len(equipment_list_result),
                "connections_by_color_type": {
                    color_type: len([c for c in connections if c.get('color_type') == color_type])
                    for color_type in set(c.get('color_type', 'unknown') for c in connections)
                },
                "connections_by_pipe_type": {
                    pipe_type: len([c for c in connections if c.get('pipe_type') == pipe_type])
                    for pipe_type in set(c.get('pipe_type', 'unknown') for c in connections)
                },
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


@router.post("/process", response_model=ProcessResponse)
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
