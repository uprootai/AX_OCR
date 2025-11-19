"""
Gateway API Server
통합 오케스트레이션 및 워크플로우 관리 마이크로서비스

포트: 8000
기능: 전체 파이프라인 통합, 견적서 생성, 워크플로우 관리
"""

import os
import sys
import json
import time
import asyncio
import logging
import base64
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import io

import httpx
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse, Response, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import fitz  # PyMuPDF
from PIL import Image
import cv2
import numpy as np

# Import cost estimator and PDF generator
from cost_estimator import get_cost_estimator
from pdf_generator import get_pdf_generator

# Import refactored modules
from models import (
    HealthResponse, ProcessRequest, ProcessResponse, ProcessData,
    YOLOResults, OCRResults, SegmentationResults, ToleranceResult,
    QuoteRequest, QuoteResponse, QuoteData, CostBreakdown
)
from utils import (
    ProgressTracker, progress_store,
    is_false_positive, pdf_to_image, calculate_bbox_iou,
    format_class_name, redraw_yolo_visualization, crop_bbox,
    match_yolo_with_ocr
)
from services import (
    call_yolo_detect, call_edocr2_ocr, call_paddleocr,
    call_edgnet_segment, call_skinmodel_tolerance,
    process_yolo_crop_ocr, ensemble_ocr_results, calculate_quote
)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Gateway API",
    description="Integrated Orchestration Service for Engineering Drawing Processing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:5174,http://localhost:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)

# Configuration
EDOCR_V1_URL = os.getenv("EDOCR_V1_URL", "http://edocr2-api:5001")
EDOCR_V2_URL = os.getenv("EDOCR_V2_URL", "http://edocr2-v2-api:5002")
EDOCR2_URL = os.getenv("EDOCR2_URL", EDOCR_V2_URL)  # Use V2 for better performance
EDGNET_URL = os.getenv("EDGNET_URL", "http://edgnet-api:5002")  # Internal container port
SKINMODEL_URL = os.getenv("SKINMODEL_URL", "http://skinmodel-api:5003")
VL_API_URL = os.getenv("VL_API_URL", "http://vl-api:5004")
YOLO_API_URL = os.getenv("YOLO_API_URL", "http://yolo-api:5005")
PADDLEOCR_API_URL = os.getenv("PADDLEOCR_API_URL", "http://paddleocr-api:5006")

UPLOAD_DIR = Path("/tmp/gateway/uploads")
RESULTS_DIR = Path("/tmp/gateway/results")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)



# =====================
# Custom OpenAPI Schema
# =====================

def custom_openapi():
    """커스텀 OpenAPI 스키마 생성 - 중첩된 모델 포함"""
    if app.openapi_schema:
        return app.openapi_schema

    from fastapi.openapi.utils import get_openapi

    # 기본 OpenAPI 스키마 생성
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # 중첩된 모델들을 명시적으로 추가
    nested_models = {
        "DetectionResult": DetectionResult,
        "YOLOResults": YOLOResults,
        "DimensionData": DimensionData,
        "OCRResults": OCRResults,
        "ComponentData": ComponentData,
        "SegmentationResults": SegmentationResults,
        "ToleranceResult": ToleranceResult,
        "ProcessData": ProcessData,
        "CostBreakdown": CostBreakdown,
        "QuoteData": QuoteData,
    }

    for model_name, model_class in nested_models.items():
        if model_name not in openapi_schema["components"]["schemas"]:
            openapi_schema["components"]["schemas"][model_name] = model_class.model_json_schema()

    # ProcessResponse의 data 필드를 ProcessData로 참조 업데이트
    if "ProcessResponse" in openapi_schema["components"]["schemas"]:
        openapi_schema["components"]["schemas"]["ProcessResponse"]["properties"]["data"] = {
            "$ref": "#/components/schemas/ProcessData"
        }

    # QuoteResponse의 data 필드를 QuoteData로 참조 업데이트
    if "QuoteResponse" in openapi_schema["components"]["schemas"]:
        openapi_schema["components"]["schemas"]["QuoteResponse"]["properties"]["data"] = {
            "$ref": "#/components/schemas/QuoteData"
        }

    app.openapi_schema = openapi_schema
    return app.openapi_schema

# 커스텀 OpenAPI 스키마 적용
app.openapi = custom_openapi


# =====================
# Helper Functions
# =====================

async def check_service_health(url: str, service_name: str) -> str:
    """서비스 헬스체크"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # eDOCr v2 uses /api/v2/health, others use /api/v1/health
            if "edocr2-v2-api" in url:
                health_endpoint = f"{url}/api/v2/health"
            else:
                health_endpoint = f"{url}/api/v1/health"

            response = await client.get(health_endpoint)
            if response.status_code == 200:
                return "healthy"
            else:
                return f"unhealthy (status={response.status_code})"
    except Exception as e:
        logger.warning(f"{service_name} health check failed: {e}")
        return f"unreachable ({str(e)})"


def pdf_to_image(pdf_bytes: bytes, dpi: int = 150) -> bytes:
    """
    PDF의 첫 페이지를 PNG 이미지로 변환

    Args:
        pdf_bytes: PDF 파일의 바이트 데이터
        dpi: 이미지 해상도 (기본 150)

    Returns:
        PNG 이미지의 바이트 데이터
    """
    try:
        logger.info(f"Converting PDF to image (DPI={dpi})")

        # PDF 열기
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")

        # 첫 페이지 가져오기
        page = pdf_document[0]

        # 이미지로 렌더링 (DPI 설정)
        zoom = dpi / 72  # 72 DPI가 기본값
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        # PIL Image로 변환
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # PNG로 저장
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        pdf_document.close()

        logger.info(f"PDF converted to image: {pix.width}x{pix.height}px")
        return img_byte_arr.getvalue()

    except Exception as e:
        logger.error(f"PDF to image conversion failed: {e}")
        raise HTTPException(status_code=500, detail=f"PDF conversion error: {str(e)}")


async def call_edgnet_segment(file_bytes: bytes, filename: str, visualize: bool = True, num_classes: int = 3, save_graph: bool = False) -> Dict[str, Any]:
    """EDGNet API 호출"""
    try:
        # 파일 확장자에서 content-type 결정
        import mimetypes
        content_type = mimetypes.guess_type(filename)[0] or "image/png"
        logger.info(f"Calling EDGNet API for {filename} (content-type: {content_type}, num_classes={num_classes}, visualize={visualize}, save_graph={save_graph})")

        async with httpx.AsyncClient(timeout=60.0) as client:
            files = {"file": (filename, file_bytes, content_type)}
            data = {
                "visualize": visualize,
                "num_classes": num_classes,
                "save_graph": save_graph
            }

            response = await client.post(
                f"{EDGNET_URL}/api/v1/segment",
                files=files,
                data=data
            )

            logger.info(f"EDGNet API status: {response.status_code}")
            if response.status_code == 200:
                edgnet_response = response.json()
                logger.info(f"EDGNet response keys: {edgnet_response.keys()}")
                logger.info(f"EDGNet components count: {len(edgnet_response.get('components', []))}")
                logger.info(f"EDGNet nodes count: {edgnet_response.get('graph', {}).get('node_count', 0)}")
                return edgnet_response
            else:
                raise HTTPException(status_code=response.status_code, detail=f"EDGNet failed: {response.text}")

    except Exception as e:
        logger.error(f"EDGNet API call failed: {e}")
        raise HTTPException(status_code=500, detail=f"EDGNet error: {str(e)}")


async def call_edocr2_ocr(
    file_bytes: bytes,
    filename: str,
    extract_dimensions: bool = True,
    extract_gdt: bool = True,
    extract_text: bool = True,
    extract_tables: bool = True,
    visualize: bool = False,
    language: str = 'eng',
    cluster_threshold: int = 20
) -> Dict[str, Any]:
    """eDOCr2 API 호출"""
    try:
        # 파일 확장자에서 content-type 결정 (PDF 또는 이미지)
        import mimetypes
        content_type = mimetypes.guess_type(filename)[0]
        if content_type is None:
            # 파일 확장자로 추측
            if filename.lower().endswith('.pdf'):
                content_type = "application/pdf"
            else:
                content_type = "image/png"
        logger.info(f"Calling eDOCr2 API for {filename} (content-type: {content_type})")
        logger.info(f"  extract: dim={extract_dimensions}, gdt={extract_gdt}, text={extract_text}, tables={extract_tables}")
        logger.info(f"  visualize={visualize}, language={language}, cluster_threshold={cluster_threshold}")

        async with httpx.AsyncClient(timeout=60.0) as client:
            files = {"file": (filename, file_bytes, content_type)}
            data = {
                "extract_dimensions": extract_dimensions,
                "extract_gdt": extract_gdt,
                "extract_text": extract_text,
                "extract_tables": extract_tables,
                "visualize": visualize,
                "language": language,
                "cluster_threshold": cluster_threshold
            }

            response = await client.post(
                f"{EDOCR2_URL}/api/v2/ocr",
                files=files,
                data=data
            )

            logger.info(f"eDOCr2 API status: {response.status_code}")
            if response.status_code == 200:
                edocr_response = response.json()
                logger.info(f"eDOCr2 response keys: {edocr_response.keys()}")

                # eDOCr v2 returns data in "data" field
                edocr_data = edocr_response.get('data', {})
                dimensions_count = len(edocr_data.get('dimensions', []))
                gdt_count = len(edocr_data.get('gdt', []))
                possible_text_count = len(edocr_data.get('possible_text', []))
                logger.info(f"eDOCr2 results: {dimensions_count} dims, {gdt_count} gdts, {possible_text_count} possible_text")

                # Return the data field (not the full response)
                return edocr_data
            else:
                raise HTTPException(status_code=response.status_code, detail=f"eDOCr2 failed: {response.text}")

    except Exception as e:
        logger.error(f"eDOCr2 API call failed: {e}")
        raise HTTPException(status_code=500, detail=f"eDOCr2 error: {str(e)}")


async def call_yolo_detect(file_bytes: bytes, filename: str, conf_threshold: float = 0.25, iou_threshold: float = 0.7, imgsz: int = 1280, visualize: bool = True) -> Dict[str, Any]:
    """YOLO API 호출"""
    try:
        # 파일 확장자에서 content-type 결정
        import mimetypes
        content_type = mimetypes.guess_type(filename)[0] or "image/png"
        logger.info(f"Calling YOLO API for {filename} (content-type: {content_type}, conf={conf_threshold}, iou={iou_threshold}, imgsz={imgsz}, visualize={visualize})")

        async with httpx.AsyncClient(timeout=60.0) as client:
            files = {"file": (filename, file_bytes, content_type)}
            data = {
                "conf_threshold": conf_threshold,
                "iou_threshold": iou_threshold,
                "imgsz": imgsz,
                "visualize": visualize
            }

            response = await client.post(
                f"{YOLO_API_URL}/api/v1/detect",
                files=files,
                data=data
            )

            logger.info(f"YOLO API status: {response.status_code}")
            if response.status_code == 200:
                yolo_response = response.json()
                logger.info(f"YOLO API response keys: {yolo_response.keys()}")
                logger.info(f"YOLO total_detections: {yolo_response.get('total_detections', 'NOT FOUND')}")
                logger.info(f"YOLO detections count: {len(yolo_response.get('detections', []))}")
                return yolo_response
            else:
                raise HTTPException(status_code=response.status_code, detail=f"YOLO failed: {response.text}")

    except Exception as e:
        logger.error(f"YOLO API call failed: {e}")
        raise HTTPException(status_code=500, detail=f"YOLO error: {str(e)}")


def calculate_bbox_iou(bbox1: Dict[str, int], bbox2: Dict[str, int]) -> float:
    """
    두 바운딩 박스의 IoU (Intersection over Union) 계산

    Args:
        bbox1, bbox2: {x, y, width, height} 형식의 바운딩 박스

    Returns:
        IoU 값 (0.0 ~ 1.0)
    """
    x1_1, y1_1 = bbox1['x'], bbox1['y']
    x2_1, y2_1 = x1_1 + bbox1['width'], y1_1 + bbox1['height']

    x1_2, y1_2 = bbox2['x'], bbox2['y']
    x2_2, y2_2 = x1_2 + bbox2['width'], y1_2 + bbox2['height']

    # Intersection
    x1_i = max(x1_1, x1_2)
    y1_i = max(y1_1, y1_2)
    x2_i = min(x2_1, x2_2)
    y2_i = min(y2_1, y2_2)

    if x2_i < x1_i or y2_i < y1_i:
        return 0.0

    intersection = (x2_i - x1_i) * (y2_i - y1_i)

    # Union
    area1 = bbox1['width'] * bbox1['height']
    area2 = bbox2['width'] * bbox2['height']
    union = area1 + area2 - intersection

    return intersection / union if union > 0 else 0.0


# YOLO 클래스명 매핑 (시각화용)
CLASS_DISPLAY_NAMES = {
    'diameter_dim': 'Diameter (Ø)',
    'linear_dim': 'Linear Dim',
    'radius_dim': 'Radius (R)',
    'angular_dim': 'Angular',
    'chamfer_dim': 'Chamfer',
    'tolerance_dim': 'Tolerance',
    'reference_dim': 'Reference',
    'flatness': 'Flatness (⏥)',
    'cylindricity': 'Cylindricity (⌭)',
    'position': 'Position (⌖)',
    'perpendicularity': 'Perpendicular (⊥)',
    'parallelism': 'Parallel (∥)',
    'surface_roughness': 'Roughness (Ra)',
    'text_block': 'Text'
}


def format_class_name(class_name: str) -> str:
    """클래스명을 사람이 읽기 쉬운 형태로 변환"""
    return CLASS_DISPLAY_NAMES.get(class_name, class_name)


def redraw_yolo_visualization(image_bytes: bytes, detections: List[Dict]) -> str:
    """
    매칭된 검출 결과로 시각화 이미지 재생성

    Args:
        image_bytes: 원본 이미지 바이트
        detections: 검출 목록 (bbox, class_name, class_id, confidence, value 포함)

    Returns:
        Base64 인코딩된 시각화 이미지
    """
    # bytes → numpy array
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    annotated_img = image.copy()

    # 색상 정의 (BGR)
    colors = {
        'dimension': (255, 100, 0),     # Blue
        'gdt': (0, 255, 100),           # Green
        'surface': (0, 165, 255),       # Orange
        'text': (255, 255, 0)           # Cyan
    }

    for det in detections:
        bbox = det.get('bbox', {})
        x1 = bbox.get('x', 0)
        y1 = bbox.get('y', 0)
        x2 = x1 + bbox.get('width', 0)
        y2 = y1 + bbox.get('height', 0)

        class_id = det.get('class_id', 0)
        class_name = det.get('class_name', '')
        confidence = det.get('confidence', 0.0)
        value = det.get('value')

        # 색상 선택
        if class_id <= 6:
            color = colors['dimension']
        elif class_id <= 11:
            color = colors['gdt']
        elif class_id == 12:
            color = colors['surface']
        else:
            color = colors['text']

        # 박스 그리기
        cv2.rectangle(annotated_img, (x1, y1), (x2, y2), color, 2)

        # 라벨 그리기 (OCR 값 포함)
        display_name = format_class_name(class_name)
        if value:
            # OCR 값이 있으면 표시
            label = f"{display_name}: {value} ({confidence:.2f})"
        else:
            # OCR 값이 없으면 클래스명과 신뢰도만
            label = f"{display_name} ({confidence:.2f})"

        (label_w, label_h), _ = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
        )

        # 라벨 배경
        cv2.rectangle(
            annotated_img,
            (x1, y1 - label_h - 12),
            (x1 + label_w + 10, y1),
            color,
            -1
        )

        # 라벨 텍스트
        cv2.putText(
            annotated_img,
            label,
            (x1 + 5, y1 - 6),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

    # 범례(Legend) 추가
    legend_height = 140
    legend_width = 280
    legend_x = 10
    legend_y = 10

    # 범례 배경
    overlay = annotated_img.copy()
    cv2.rectangle(overlay, (legend_x, legend_y), (legend_x + legend_width, legend_y + legend_height), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.7, annotated_img, 0.3, 0, annotated_img)

    # 범례 테두리
    cv2.rectangle(annotated_img, (legend_x, legend_y), (legend_x + legend_width, legend_y + legend_height), (255, 255, 255), 2)

    # 범례 제목
    cv2.putText(annotated_img, "Detection Classes", (legend_x + 10, legend_y + 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # 범례 항목
    legend_items = [
        ("Dimensions", colors['dimension']),
        ("GD&T Symbols", colors['gdt']),
        ("Surface Roughness", colors['surface']),
        ("Text Blocks", colors['text'])
    ]

    y_offset = legend_y + 50
    for label, color in legend_items:
        # 색상 박스
        cv2.rectangle(annotated_img, (legend_x + 10, y_offset - 10), (legend_x + 30, y_offset + 5), color, -1)
        cv2.rectangle(annotated_img, (legend_x + 10, y_offset - 10), (legend_x + 30, y_offset + 5), (255, 255, 255), 1)
        # 라벨
        cv2.putText(annotated_img, label, (legend_x + 40, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        y_offset += 25

    # numpy array → Base64
    _, buffer = cv2.imencode('.jpg', annotated_img)
    img_base64 = base64.b64encode(buffer).decode('utf-8')

    return img_base64


def match_yolo_with_ocr(yolo_detections: List[Dict], ocr_dimensions: List[Dict], iou_threshold: float = 0.3) -> List[Dict]:
    """
    YOLO 검출 결과와 OCR 치수 결과를 매칭

    Args:
        yolo_detections: YOLO 검출 목록 (bbox, class_name, confidence 포함)
        ocr_dimensions: OCR 치수 목록 (bbox or location, value 포함)
        iou_threshold: IoU 임계값 (기본 0.3)

    Returns:
        value 필드가 추가된 YOLO 검출 목록
    """
    # Debug: OCR dimensions 구조 확인
    if ocr_dimensions:
        logger.info(f"[DEBUG] First OCR dimension keys: {list(ocr_dimensions[0].keys())}")
        logger.info(f"[DEBUG] First OCR dimension sample: {ocr_dimensions[0]}")

    if yolo_detections:
        logger.info(f"[DEBUG] First YOLO detection keys: {list(yolo_detections[0].keys())}")
        logger.info(f"[DEBUG] First YOLO bbox: {yolo_detections[0].get('bbox', {})}")

    matched_detections = []

    for idx, yolo_det in enumerate(yolo_detections):
        yolo_bbox = yolo_det.get('bbox', {})
        matched_value = None
        max_iou = 0.0
        best_ocr_idx = -1

        # OCR 결과와 매칭 시도
        for ocr_idx, ocr_dim in enumerate(ocr_dimensions):
            # OCR bbox 처리: bbox 필드가 있으면 사용, 없으면 location 폴리곤을 bbox로 변환
            ocr_bbox = ocr_dim.get('bbox')
            if not ocr_bbox and 'location' in ocr_dim:
                # location은 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]] 형태의 폴리곤
                location = ocr_dim['location']
                if location and len(location) >= 2:
                    # 모든 점의 x, y 좌표에서 최소/최대값 추출
                    xs = [p[0] for p in location]
                    ys = [p[1] for p in location]
                    x_min, x_max = min(xs), max(xs)
                    y_min, y_max = min(ys), max(ys)
                    ocr_bbox = {
                        'x': x_min,
                        'y': y_min,
                        'width': x_max - x_min,
                        'height': y_max - y_min
                    }

            if not ocr_bbox:
                continue

            iou = calculate_bbox_iou(yolo_bbox, ocr_bbox)

            # IoU가 임계값 이상이고 최대값이면 매칭
            if iou > iou_threshold and iou > max_iou:
                max_iou = iou
                matched_value = ocr_dim.get('value', ocr_dim.get('text'))
                best_ocr_idx = ocr_idx

        # 매칭 결과 추가
        matched_det = yolo_det.copy()
        if matched_value:
            matched_det['value'] = matched_value
            matched_det['matched_iou'] = round(max_iou, 3)
            logger.info(f"[MATCH] YOLO #{idx} matched with OCR #{best_ocr_idx}: value='{matched_value}', IoU={max_iou:.3f}")

        matched_detections.append(matched_det)

    return matched_detections


def upscale_image_region(image_bytes: bytes, bbox: Dict[str, int], scale: int = 4) -> bytes:
    """
    이미지의 특정 영역을 확대

    Args:
        image_bytes: 원본 이미지 바이트
        bbox: 바운딩 박스 {x, y, width, height}
        scale: 확대 배율 (기본 4x)

    Returns:
        확대된 이미지 영역의 바이트
    """
    try:
        # bytes → PIL Image
        image = Image.open(io.BytesIO(image_bytes))

        # 영역 추출
        x = bbox['x']
        y = bbox['y']
        w = bbox['width']
        h = bbox['height']

        # 여백 추가 (10%)
        margin = int(min(w, h) * 0.1)
        x = max(0, x - margin)
        y = max(0, y - margin)
        w = min(image.width - x, w + 2 * margin)
        h = min(image.height - y, h + 2 * margin)

        # 크롭
        cropped = image.crop((x, y, x + w, y + h))

        # 확대 (Lanczos 리샘플링으로 고품질 유지)
        upscaled = cropped.resize(
            (w * scale, h * scale),
            Image.Resampling.LANCZOS
        )

        # PIL Image → bytes
        img_byte_arr = io.BytesIO()
        upscaled.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        logger.info(f"Upscaled region from {w}x{h} to {w*scale}x{h*scale}")
        return img_byte_arr.getvalue()

    except Exception as e:
        logger.error(f"Upscaling failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upscale error: {str(e)}")


async def call_paddleocr(
    file_bytes: bytes,
    filename: str,
    min_confidence: float = 0.3,
    det_db_thresh: float = 0.3,
    det_db_box_thresh: float = 0.5,
    use_angle_cls: bool = True
) -> Dict[str, Any]:
    """PaddleOCR API 호출"""
    try:
        import mimetypes
        content_type = mimetypes.guess_type(filename)[0] or "image/png"
        logger.info(f"Calling PaddleOCR API for {filename} (min_conf={min_confidence})")

        async with httpx.AsyncClient(timeout=30.0) as client:
            files = {"file": (filename, file_bytes, content_type)}
            data = {
                "min_confidence": str(min_confidence),
                "det_db_thresh": str(det_db_thresh),
                "det_db_box_thresh": str(det_db_box_thresh),
                "use_angle_cls": str(use_angle_cls).lower()
            }

            response = await client.post(
                f"{PADDLEOCR_API_URL}/api/v1/ocr",
                files=files,
                data=data
            )

            if response.status_code == 200:
                ocr_response = response.json()
                logger.info(f"PaddleOCR detected {ocr_response.get('total_texts', 0)} texts")
                return ocr_response
            else:
                raise HTTPException(status_code=response.status_code, detail=f"PaddleOCR failed: {response.text}")

    except Exception as e:
        logger.error(f"PaddleOCR API call failed: {e}")
        raise HTTPException(status_code=500, detail=f"PaddleOCR error: {str(e)}")


def crop_bbox(
    image_bytes: bytes,
    bbox: Dict,
    padding: float = 0.1,
    min_size: int = 50,
    upscale_small: bool = True,
    upscale_factor: float = 2.0
) -> bytes:
    """
    YOLO bbox로 이미지 crop (패딩 추가, 최소 크기 보장, 작은 영역 upscaling)

    Args:
        image_bytes: 원본 이미지
        bbox: YOLO 바운딩 박스 {x, y, width, height}
        padding: crop 시 패딩 비율 (기본 10%)
        min_size: 최소 crop 크기 (픽셀, 기본 50)
        upscale_small: 작은 crop을 upscale할지 여부 (기본 True)
        upscale_factor: upscale 배율 (기본 2.0x)
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))

        x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']
        logger.info(f"Crop bbox: x={x}, y={y}, w={w}, h={h}, img_size=({image.width}, {image.height})")

        # bbox가 이미지 밖에 있는지 확인
        if x >= image.width or y >= image.height or x + w <= 0 or y + h <= 0:
            raise ValueError(f"BBox completely outside image bounds")

        # bbox를 이미지 경계 내로 클램핑
        x = max(0, min(x, image.width - 1))
        y = max(0, min(y, image.height - 1))
        w = max(1, min(w, image.width - x))
        h = max(1, min(h, image.height - y))

        # 패딩 추가
        padding_x = max(1, int(w * padding))
        padding_y = max(1, int(h * padding))

        # 좌표 계산 (패딩 포함, 이미지 경계 내로 클램핑)
        x1 = max(0, x - padding_x)
        y1 = max(0, y - padding_y)
        x2 = min(image.width, x + w + padding_x)
        y2 = min(image.height, y + h + padding_y)

        # 최소 크기 보장
        crop_width = x2 - x1
        crop_height = y2 - y1

        if crop_width < min_size:
            # 중심을 유지하면서 확장
            center_x = (x1 + x2) / 2
            x1 = max(0, int(center_x - min_size / 2))
            x2 = min(image.width, x1 + min_size)
            crop_width = x2 - x1

        if crop_height < min_size:
            center_y = (y1 + y2) / 2
            y1 = max(0, int(center_y - min_size / 2))
            y2 = min(image.height, y1 + min_size)
            crop_height = y2 - y1

        logger.info(f"Crop coords (clamped): ({x1}, {y1}, {x2}, {y2}), size: {crop_width}x{crop_height}")
        cropped = image.crop((x1, y1, x2, y2))

        # 작은 영역 upscaling (OCR 정확도 향상)
        if upscale_small and (crop_width < min_size * 2 or crop_height < min_size * 2):
            new_width = int(crop_width * upscale_factor)
            new_height = int(crop_height * upscale_factor)
            cropped = cropped.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.info(f"Upscaled small crop: {crop_width}x{crop_height} → {new_width}x{new_height}")

        # PIL Image → bytes
        img_byte_arr = io.BytesIO()
        cropped.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        return img_byte_arr.getvalue()

    except Exception as e:
        logger.error(f"Crop failed: {e}")
        raise HTTPException(status_code=500, detail=f"Crop error: {str(e)}")


def is_false_positive(text: str) -> bool:
    """
    False Positive 판별: 도면 메타데이터인지 확인

    필터링 대상:
    - 도면 번호 (Rev, DWG, E3, 12-016840 등)
    - 참조 번호 (412-311197 등)
    - 공차 병합 오인식 (+0+0, -0.1-0.2 등)
    """
    import re

    # 패턴 1: Revision 번호 (Rev.3, Rev.1 등)
    if re.search(r'\bRev\.?\d+\b', text, re.IGNORECASE):
        return True

    # 패턴 2: DWG 번호
    if re.search(r'\bDWG\b', text, re.IGNORECASE):
        return True

    # 패턴 3: 하이픈으로 연결된 긴 번호 (12-016840, 412-311197 등)
    if re.match(r'^\d{2,}-\d{5,}', text):
        return True

    # 패턴 4: 문서 번호 (E3003810 등)
    if re.match(r'^[A-Z]\d{6,}', text):
        return True

    # 패턴 5: 공차 병합 오인식 (+0+0, -0.1-0.2, +0.2+0 등)
    if re.match(r'^[+-]\d+\.?\d*[+-]\d+\.?\d*$', text):
        return True

    # 패턴 6: ME-C, S60, S60/65ME-C 같은 기종 번호
    if re.search(r'\bME-C\b|^S\d{2}(/\d{2})?ME-C$', text, re.IGNORECASE):
        return True

    # 패턴 7: 괄호로 감싸진 revision (Rev.3), (Rev.1) 등
    if re.search(r'\(Rev\.\d+\)', text, re.IGNORECASE):
        return True

    return False


async def process_yolo_crop_ocr(
    image_bytes: bytes,
    yolo_detections: List[Dict],
    dimension_class_ids: List[int] = [0, 1, 2, 3, 4, 5, 6],  # diameter, linear, angular, radial, chamfer, counterbore, countersink
    min_confidence: float = 0.5,
    padding: float = 0.1
) -> Dict[str, Any]:
    """
    YOLO 검출 객체별 개별 eDOCr2 OCR 처리

    각 YOLO 검출 영역을 crop하여 eDOCr2로 개별 OCR 수행

    Args:
        image_bytes: 원본 이미지
        yolo_detections: YOLO 검출 결과 리스트
        dimension_class_ids: 치수 관련 클래스 ID 리스트
        min_confidence: OCR 최소 신뢰도 (현재 사용 안 함, eDOCr2는 자체 신뢰도 사용)
        padding: crop 시 패딩 비율

    Returns:
        OCR 결과 집계 (dimensions, total_texts, processing_time 등)
    """
    start_time = time.time()

    # 치수 관련 객체만 필터링
    dimension_detections = [
        d for d in yolo_detections
        if d.get('class_id', 99) in dimension_class_ids
    ]

    logger.info(f"YOLO Crop OCR: {len(dimension_detections)} dimension objects to process")

    if len(dimension_detections) == 0:
        return {
            "dimensions": [],
            "total_texts": 0,
            "crop_count": 0,
            "successful_crops": 0,
            "processing_time": time.time() - start_time
        }

    # 각 detection을 crop하고 병렬 OCR 처리
    crop_tasks = []
    task_metadata = []

    for idx, det in enumerate(dimension_detections):
        try:
            bbox = det['bbox']
            cropped_bytes = crop_bbox(image_bytes, bbox, padding)

            # 비동기 eDOCr2 OCR 호출 태스크 생성
            task = call_edocr2_ocr(
                cropped_bytes,
                f"crop_{idx}.png",
                extract_dimensions=True,
                extract_gdt=False,
                extract_text=True,
                extract_tables=False,
                visualize=False,
                language='eng',
                cluster_threshold=20
            )
            crop_tasks.append(task)
            task_metadata.append((idx, det))
        except Exception as e:
            logger.error(f"Crop failed for detection {idx}: {e}")
            continue

    # crop 실패로 tasks가 비어있으면 조기 반환
    if len(crop_tasks) == 0:
        logger.warning("All crops failed - no tasks to process")
        return {
            "dimensions": [],
            "total_texts": 0,
            "crop_count": len(dimension_detections),
            "successful_crops": 0,
            "processing_time": time.time() - start_time
        }

    # 진정한 병렬 실행 (asyncio.gather로 모든 태스크를 동시 실행)
    logger.info(f"Running {len(crop_tasks)} OCR tasks in parallel with asyncio.gather()")
    ocr_raw_results = await asyncio.gather(*crop_tasks, return_exceptions=True)

    # 결과 정리
    ocr_results = []
    for (idx, det), result in zip(task_metadata, ocr_raw_results):
        if isinstance(result, Exception):
            logger.error(f"OCR failed for crop {idx}: {result}")
            ocr_results.append({
                "crop_idx": idx,
                "yolo_detection": det,
                "status": "error",
                "error": str(result)
            })
        else:
            ocr_results.append({
                "crop_idx": idx,
                "yolo_detection": det,
                "ocr_result": result,
                "status": "success"
            })

    # 결과 집계 및 필터링
    all_dimensions = []
    successful_crops = sum(1 for r in ocr_results if r['status'] == 'success')

    for result in ocr_results:
        if result['status'] != 'success':
            continue

        ocr_data = result['ocr_result']

        # eDOCr2 응답 형식: dimensions 배열 직접 확인
        dimensions = ocr_data.get('dimensions', [])

        for dim in dimensions:
            # eDOCr2 dimension 구조: {value: str, unit: str, type: str, bbox: {...}, confidence: float}
            value = dim.get('value', '').strip()
            conf = dim.get('confidence', 1.0)  # eDOCr2는 confidence가 없을 수 있음

            # 필터링: 숫자 포함된 값만
            if any(c.isdigit() for c in value) and len(value) >= 1:
                # False Positive 필터링: 도면 메타데이터 제외
                if is_false_positive(value):
                    logger.debug(f"Filtered False Positive: '{value}'")
                    continue

                all_dimensions.append({
                    "value": value,
                    "unit": dim.get('unit', 'mm'),
                    "type": dim.get('type', 'dimension'),
                    "confidence": conf,
                    "crop_idx": result['crop_idx'],
                    "yolo_class": result['yolo_detection']['class_name'],
                    "bbox": dim.get('bbox')
                })

    # 신뢰도 순 정렬
    all_dimensions.sort(key=lambda x: x['confidence'], reverse=True)

    processing_time = time.time() - start_time

    failed_crops = len(dimension_detections) - successful_crops
    success_rate = (successful_crops / len(dimension_detections) * 100) if len(dimension_detections) > 0 else 0

    logger.info(f"YOLO Crop OCR completed: {len(all_dimensions)} dimensions from {successful_crops}/{len(dimension_detections)} crops ({success_rate:.1f}% success) in {processing_time:.2f}s")

    # 실패한 crop 정보 수집
    failed_crop_details = [
        {
            "crop_idx": r["crop_idx"],
            "yolo_class": r["yolo_detection"]["class_name"],
            "error": r["error"]
        }
        for r in ocr_results if r["status"] == "error"
    ]

    return {
        "dimensions": all_dimensions,
        "total_texts": len(all_dimensions),
        "crop_count": len(dimension_detections),
        "successful_crops": successful_crops,
        "failed_crops": failed_crops,
        "success_rate": success_rate,
        "failed_crop_details": failed_crop_details if failed_crops > 0 else [],
        "processing_time": processing_time
    }


def ensemble_ocr_results(
    yolo_crop_results: List[Dict],
    edocr_results: List[Dict],
    yolo_weight: float = 0.6,
    edocr_weight: float = 0.4,
    similarity_threshold: float = 0.7
) -> List[Dict]:
    """
    YOLO Crop OCR과 eDOCr v2 결과를 앙상블 융합

    전략:
    1. 두 결과에서 모두 발견된 치수: 높은 신뢰도로 채택
    2. 한쪽에만 있는 치수: 가중치 적용 후 임계값 이상이면 채택
    3. 유사한 치수 값: 더 높은 신뢰도 선택

    Args:
        yolo_crop_results: YOLO Crop OCR 결과 리스트
        edocr_results: eDOCr v2 결과 리스트
        yolo_weight: YOLO 결과 가중치 (기본 0.6 - 재현율 우수)
        edocr_weight: eDOCr 결과 가중치 (기본 0.4)
        similarity_threshold: 텍스트 유사도 임계값
    """
    import difflib

    merged = []
    used_edocr = set()

    # YOLO 결과를 기준으로 병합
    for yolo_dim in yolo_crop_results:
        yolo_text = str(yolo_dim.get('value', '')).strip()
        yolo_conf = yolo_dim.get('confidence', 0) * yolo_weight

        # eDOCr 결과에서 유사한 항목 찾기
        best_match = None
        best_similarity = 0

        for idx, edocr_dim in enumerate(edocr_results):
            if idx in used_edocr:
                continue

            edocr_text = str(edocr_dim.get('value', '')).strip()
            similarity = difflib.SequenceMatcher(None, yolo_text, edocr_text).ratio()

            if similarity > best_similarity and similarity >= similarity_threshold:
                best_similarity = similarity
                best_match = (idx, edocr_dim, similarity)

        if best_match:
            # 두 결과가 유사함 - 더 높은 신뢰도 선택
            idx, edocr_dim, similarity = best_match
            edocr_conf = edocr_dim.get('confidence', 0.8) * edocr_weight  # eDOCr은 신뢰도 정보 없으면 0.8 가정

            if yolo_conf >= edocr_conf:
                merged_dim = yolo_dim.copy()
                merged_dim['confidence'] = min(1.0, yolo_conf + edocr_conf * similarity)
                merged_dim['source'] = 'yolo_crop_ocr'
                merged_dim['confirmed_by'] = 'edocr_v2'
            else:
                merged_dim = edocr_dim.copy()
                merged_dim['confidence'] = min(1.0, edocr_conf + yolo_conf * similarity)
                merged_dim['source'] = 'edocr_v2'
                merged_dim['confirmed_by'] = 'yolo_crop_ocr'

            merged.append(merged_dim)
            used_edocr.add(idx)
        else:
            # YOLO에만 있음
            if yolo_conf >= 0.3:  # 가중치 적용 후 임계값 (0.6 * 0.5 = 0.3, 실제 confidence 0.5 이상)
                merged_dim = yolo_dim.copy()
                merged_dim['source'] = 'yolo_crop_ocr'
                merged.append(merged_dim)

    # eDOCr에만 있는 항목 추가
    for idx, edocr_dim in enumerate(edocr_results):
        if idx not in used_edocr:
            edocr_conf = edocr_dim.get('confidence', 0.8) * edocr_weight
            if edocr_conf >= 0.4:  # eDOCr 임계값은 낮게 (정밀도 보완)
                merged_dim = edocr_dim.copy()
                merged_dim['source'] = 'edocr_v2'
                merged.append(merged_dim)

    # 신뢰도 순 정렬
    merged.sort(key=lambda x: x.get('confidence', 0), reverse=True)

    logger.info(f"Ensemble merged: {len(yolo_crop_results)} YOLO + {len(edocr_results)} eDOCr → {len(merged)} total")

    return merged


async def call_skinmodel_tolerance(
    dimensions: List[Dict],
    material: Dict,
    material_type: str = 'steel',
    manufacturing_process: str = 'machining',
    correlation_length: float = 10.0
) -> Dict[str, Any]:
    """Skin Model API 호출 - 데이터 형식 변환 포함"""
    try:
        logger.info(f"Calling Skin Model API with {len(dimensions)} dimensions")
        logger.info(f"  material_type={material_type}, manufacturing_process={manufacturing_process}, correlation_length={correlation_length}")

        # Transform dimensions to match Skin Model API format
        # Only include dimensions with valid numeric values
        transformed_dimensions = []
        skipped_count = 0

        for dim in dimensions:
            # Validate that the value can be converted to float
            value_str = str(dim.get("value", ""))
            try:
                # Try to parse as float (this filters out non-numeric values)
                value_float = float(value_str)

                transformed_dim = {
                    "type": dim.get("type", "length"),
                    "value": value_float,
                    "unit": dim.get("unit", "mm")
                }

                # Parse tolerance string (e.g., "±0.1" -> 0.1)
                tolerance_str = dim.get("tolerance")
                if tolerance_str:
                    try:
                        # Remove ± symbol and convert to float
                        tolerance_value = float(str(tolerance_str).replace("±", "").strip())
                        transformed_dim["tolerance"] = tolerance_value
                    except (ValueError, AttributeError):
                        # If parsing fails, skip tolerance field (it's optional)
                        pass

                transformed_dimensions.append(transformed_dim)

            except (ValueError, TypeError):
                # Skip non-numeric values (e.g., "1mm", "(8)45", "Rev. 1", etc.)
                skipped_count += 1
                logger.warning(f"Skipping non-numeric dimension value: {value_str}")
                continue

        if skipped_count > 0:
            logger.info(f"Filtered out {skipped_count} non-numeric dimensions from {len(dimensions)} total")

        if not transformed_dimensions:
            logger.warning("No valid numeric dimensions for Skin Model after filtering")
            return {
                "status": "skipped",
                "data": {
                    "message": "No valid numeric dimensions available for tolerance analysis",
                    "skipped_count": skipped_count
                }
            }

        async with httpx.AsyncClient(timeout=30.0) as client:
            data = {
                "dimensions": transformed_dimensions,
                "material": material,
                "manufacturing_process": manufacturing_process,
                "correlation_length": correlation_length
            }

            logger.info(f"Sending to Skin Model: {data}")

            response = await client.post(
                f"{SKINMODEL_URL}/api/v1/tolerance",
                json=data
            )

            logger.info(f"Skin Model API status: {response.status_code}")

            if response.status_code == 200:
                skinmodel_response = response.json()
                logger.info(f"Skin Model response keys: {skinmodel_response.keys()}")
                if 'data' in skinmodel_response and 'manufacturability' in skinmodel_response['data']:
                    manu_data = skinmodel_response['data']['manufacturability']
                    logger.info(f"Skin Model manufacturability: {manu_data.get('score', 0)}%, difficulty: {manu_data.get('difficulty', 'Unknown')}")
                return skinmodel_response
            else:
                logger.error(f"Skin Model error response: {response.text}")
                raise HTTPException(status_code=response.status_code, detail=f"Skin Model failed: {response.text}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Skin Model API call failed: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Skin Model error: {str(e)}")


def calculate_quote(
    ocr_data: Dict,
    tolerance_data: Dict,
    material_cost_per_kg: float,
    machining_rate_per_hour: float,
    tolerance_premium_factor: float
) -> Dict[str, Any]:
    """견적 계산"""
    try:
        # Mock 계산 (실제 구현 시 도메인 로직으로 대체)
        dimensions = ocr_data.get("data", {}).get("dimensions", [])
        manufacturability = tolerance_data.get("data", {}).get("manufacturability", {})

        # 재료비 추정 (간단한 체적 계산)
        estimated_volume = 0.05  # m³ (Mock)
        material_density = 7850  # kg/m³ (Steel)
        material_weight = estimated_volume * material_density
        material_cost = material_weight * material_cost_per_kg

        # 가공비 추정
        difficulty_multiplier = {
            "Easy": 1.0,
            "Medium": 1.5,
            "Hard": 2.5
        }.get(manufacturability.get("difficulty", "Medium"), 1.5)

        estimated_machining_hours = 20.0 * difficulty_multiplier
        machining_cost = estimated_machining_hours * machining_rate_per_hour

        # 공차 프리미엄
        num_tight_tolerances = len([d for d in dimensions if d.get("tolerance")])
        tolerance_premium = num_tight_tolerances * 100 * tolerance_premium_factor

        total_cost = material_cost + machining_cost + tolerance_premium

        return {
            "quote_id": f"Q{int(time.time())}",
            "breakdown": {
                "material_cost": round(material_cost, 2),
                "machining_cost": round(machining_cost, 2),
                "tolerance_premium": round(tolerance_premium, 2),
                "total": round(total_cost, 2)
            },
            "details": {
                "material_weight_kg": round(material_weight, 2),
                "estimated_machining_hours": round(estimated_machining_hours, 1),
                "num_tight_tolerances": num_tight_tolerances,
                "difficulty": manufacturability.get("difficulty", "Medium")
            },
            "lead_time_days": 15,
            "confidence": 0.85
        }

    except Exception as e:
        logger.error(f"Quote calculation failed: {e}")
        return {"error": str(e)}


# =====================
# API Endpoints
# =====================

@app.get("/", response_model=HealthResponse)
async def root():
    """루트 엔드포인트"""
    services = {
        "edocr2": await check_service_health(EDOCR2_URL, "eDOCr2"),
        "edgnet": await check_service_health(EDGNET_URL, "EDGNet"),
        "skinmodel": await check_service_health(SKINMODEL_URL, "Skin Model")
    }

    all_healthy = all(status == "healthy" for status in services.values())

    return {
        "status": "online" if all_healthy else "degraded",
        "service": "Gateway API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "services": services
    }


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """헬스체크"""
    services = {
        "edocr2": await check_service_health(EDOCR2_URL, "eDOCr2"),
        "edgnet": await check_service_health(EDGNET_URL, "EDGNet"),
        "skinmodel": await check_service_health(SKINMODEL_URL, "Skin Model")
    }

    all_healthy = all(status == "healthy" for status in services.values())

    return {
        "status": "healthy" if all_healthy else "degraded",
        "service": "Gateway API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "services": services
    }


@app.get("/api/v1/sample-image")
async def get_sample_image(path: str):
    """샘플 이미지 파일 제공"""
    try:
        # Security: only allow specific test image paths
        allowed_paths = [
            "/datasets/combined/images/test/synthetic_random_synthetic_test_000003.jpg",
            "/datasets/combined/images/test/synthetic_random_synthetic_test_000001.jpg",
            "/datasets/combined/images/test/synthetic_random_synthetic_test_000002.jpg"
        ]

        if path not in allowed_paths:
            raise HTTPException(status_code=403, detail="Access to this path is not allowed")

        # Use absolute path as-is (already mounted in container at /datasets)
        file_path = Path(path)

        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Image not found: {path}")

        return FileResponse(
            path=str(file_path),
            media_type="image/jpeg",
            filename=file_path.name
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving sample image: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/progress/{job_id}")
async def get_progress_stream(job_id: str):
    """Server-Sent Events endpoint for real-time progress updates"""

    async def event_generator():
        """Generate SSE events"""
        last_index = 0
        timeout_count = 0
        max_timeout = 120  # 2 minutes timeout

        while timeout_count < max_timeout:
            # Get progress updates
            progress_list = progress_store.get(job_id, [])

            # Send new updates
            if len(progress_list) > last_index:
                for update in progress_list[last_index:]:
                    yield f"data: {json.dumps(update)}\n\n"
                last_index = len(progress_list)
                timeout_count = 0  # Reset timeout

            # Check if job is complete (look for "complete" step)
            if progress_list:
                last_update = progress_list[-1]
                if last_update.get("step") == "complete" and last_update.get("status") == "completed":
                    yield f"data: {json.dumps({'status': 'done'})}\n\n"
                    break
                # Also check for error in any step
                if last_update.get("status") == "error":
                    yield f"data: {json.dumps({'status': 'done'})}\n\n"
                    break

            # Wait before checking again
            await asyncio.sleep(0.5)
            timeout_count += 1

        # Timeout
        if timeout_count >= max_timeout:
            yield f"data: {json.dumps({'status': 'timeout'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.post("/api/v1/process", response_model=ProcessResponse)
async def process_drawing(
    file: UploadFile = File(..., description="도면 파일"),
    pipeline_mode: str = Form(default="speed", description="파이프라인 모드: hybrid (정확도 우선) 또는 speed (속도 우선)"),
    use_segmentation: bool = Form(True),
    use_ocr: bool = Form(True),
    use_tolerance: bool = Form(True),
    use_yolo_crop_ocr: bool = Form(default=False, description="YOLO crop 기반 개별 OCR 사용 (재현율 향상)"),
    use_ensemble: bool = Form(default=False, description="앙상블 전략 사용 (YOLO Crop OCR + eDOCr v2 융합)"),
    visualize: bool = Form(True),
    # YOLO 하이퍼파라미터
    yolo_conf_threshold: float = Form(default=0.25, description="YOLO confidence threshold (0-1)"),
    yolo_iou_threshold: float = Form(default=0.7, description="YOLO IoU threshold (0-1)"),
    yolo_imgsz: int = Form(default=1280, description="YOLO input image size"),
    yolo_visualize: bool = Form(default=True, description="YOLO visualization"),
    # eDOCr2 하이퍼파라미터
    edocr_extract_dimensions: bool = Form(default=True, description="eDOCr2 extract dimensions"),
    edocr_extract_gdt: bool = Form(default=True, description="eDOCr2 extract GD&T"),
    edocr_extract_text: bool = Form(default=True, description="eDOCr2 extract text"),
    edocr_extract_tables: bool = Form(default=True, description="eDOCr2 extract tables"),
    edocr_visualize: bool = Form(default=False, description="eDOCr2 visualization"),
    edocr_language: str = Form(default='eng', description="eDOCr2 Tesseract language code"),
    edocr_cluster_threshold: int = Form(default=20, description="eDOCr2 clustering threshold"),
    # EDGNet 하이퍼파라미터
    edgnet_num_classes: int = Form(default=3, description="EDGNet number of classes"),
    edgnet_visualize: bool = Form(default=True, description="EDGNet visualization"),
    edgnet_save_graph: bool = Form(default=False, description="EDGNet save graph"),
    # PaddleOCR 하이퍼파라미터
    paddle_det_db_thresh: float = Form(default=0.3, description="PaddleOCR detection threshold"),
    paddle_det_db_box_thresh: float = Form(default=0.5, description="PaddleOCR box threshold"),
    paddle_min_confidence: float = Form(default=0.5, description="PaddleOCR min confidence"),
    paddle_use_angle_cls: bool = Form(default=True, description="PaddleOCR use angle classification"),
    # Skin Model 하이퍼파라미터
    skin_material: str = Form(default='steel', description="Skin Model material"),
    skin_manufacturing_process: str = Form(default='machining', description="Skin Model manufacturing process"),
    skin_correlation_length: float = Form(default=10.0, description="Skin Model correlation length")
):
    """
    전체 파이프라인 처리

    - **file**: 도면 파일 (PDF 또는 이미지)
    - **pipeline_mode**: 파이프라인 모드
      - **hybrid**: 하이브리드 (정확도 ~95%, 10-15초) - YOLO → Upscale → eDOCr + EDGNet 병렬
      - **speed**: 속도 우선 (정확도 ~93%, 8-10초) - YOLO + eDOCr + EDGNet 3-way 병렬
    - **use_segmentation**: EDGNet 세그멘테이션 사용
    - **use_ocr**: eDOCr2 OCR 사용
    - **use_tolerance**: Skin Model 공차 예측 사용
    - **visualize**: 시각화 생성
    """
    start_time = time.time()

    # 파일 읽기
    file_bytes = await file.read()
    file_id = f"{int(time.time())}_{file.filename}"

    # Initialize progress tracker
    tracker = ProgressTracker(file_id)
    tracker.update("initialize", "started", f"파이프라인 시작: {pipeline_mode} 모드", {
        "filename": file.filename,
        "pipeline_mode": pipeline_mode,
        "options": {
            "use_ocr": use_ocr,
            "use_segmentation": use_segmentation,
            "use_tolerance": use_tolerance,
            "visualize": visualize
        }
    })

    logger.info(f"Processing pipeline for {file_id}")
    logger.info(f"Pipeline mode: {pipeline_mode}")
    logger.info(f"Options: segment={use_segmentation}, ocr={use_ocr}, tolerance={use_tolerance}")

    result = {
        "yolo_results": None,
        "segmentation_results": None,
        "ocr_results": None,
        "tolerance_results": None,
        "ensemble": None,
        "pipeline_mode": pipeline_mode,
        "job_id": file_id  # Include job_id for progress tracking
    }

    try:
        # PDF 파일인지 확인
        is_pdf = file.filename.lower().endswith('.pdf')

        # 이미지 파일 준비 (PDF는 이미지로 변환)
        image_bytes = file_bytes
        image_filename = file.filename
        if is_pdf:
            logger.info(f"PDF detected, converting to image: {file.filename}")
            image_bytes = pdf_to_image(file_bytes)
            image_filename = file.filename.rsplit('.', 1)[0] + '.png'

        # =============================================
        # 파이프라인 모드별 처리
        # =============================================

        if pipeline_mode == "hybrid":
            # 하이브리드 파이프라인: YOLO → Upscale → eDOCr + EDGNet 병렬
            logger.info("🔵 Running HYBRID pipeline (accuracy priority)")
            tracker.update("pipeline", "started", "🔵 하이브리드 파이프라인 시작 (정확도 우선)")

            # Step 1: YOLO 객체 검출
            logger.info("Step 1: YOLO detection")
            tracker.update("yolo", "running", "Step 1: YOLO 객체 검출 중...")
            yolo_result = await call_yolo_detect(image_bytes, image_filename, conf_threshold=yolo_conf_threshold, iou_threshold=yolo_iou_threshold, imgsz=yolo_imgsz, visualize=yolo_visualize)
            result["yolo_results"] = yolo_result

            detections_count = yolo_result.get("total_detections", 0) if yolo_result else 0
            tracker.update("yolo", "completed", f"Step 1 완료: {detections_count}개 객체 검출", {
                "detection_count": detections_count,
                "processing_time": yolo_result.get("processing_time", 0) if yolo_result else 0
            })

            # Step 2: 병렬 정밀 분석
            logger.info("Step 2: Parallel analysis (Upscale+OCR + Segmentation)")
            tracker.update("parallel", "running", "Step 2: 병렬 정밀 분석 시작")
            tasks = []

            # 2a: 검출된 영역 Upscale + eDOCr
            if use_ocr and yolo_result and yolo_result.get("total_detections", 0) > 0:
                # Upscaling은 동기 함수이므로 여기서 실행
                # 치수 관련 검출만 Upscale (class_id 0-6)
                detections = yolo_result.get("detections", [])
                dimension_detections = [d for d in detections if d.get("class_id", 99) <= 6]

                if dimension_detections:
                    logger.info(f"Upscaling {len(dimension_detections)} dimension regions")
                    tracker.update("upscale", "running", f"이미지 업스케일링 중: {len(dimension_detections)}개 영역", {
                        "dimension_count": len(dimension_detections)
                    })
                    # 간단화: 전체 이미지에 OCR 적용 (실제로는 각 영역별로 Upscale 후 OCR 가능)
                    tasks.append(call_edocr2_ocr(
                        file_bytes if is_pdf else image_bytes,
                        file.filename,
                        extract_dimensions=edocr_extract_dimensions,
                        extract_gdt=edocr_extract_gdt,
                        extract_text=edocr_extract_text,
                        extract_tables=edocr_extract_tables,
                        visualize=edocr_visualize,
                        language=edocr_language,
                        cluster_threshold=edocr_cluster_threshold
                    ))
                else:
                    tasks.append(call_edocr2_ocr(
                        file_bytes if is_pdf else image_bytes,
                        file.filename,
                        extract_dimensions=edocr_extract_dimensions,
                        extract_gdt=edocr_extract_gdt,
                        extract_text=edocr_extract_text,
                        extract_tables=edocr_extract_tables,
                        visualize=edocr_visualize,
                        language=edocr_language,
                        cluster_threshold=edocr_cluster_threshold
                    ))
            elif use_ocr:
                tasks.append(call_edocr2_ocr(
                    file_bytes if is_pdf else image_bytes,
                    file.filename,
                    extract_dimensions=edocr_extract_dimensions,
                    extract_gdt=edocr_extract_gdt,
                    extract_text=edocr_extract_text,
                    extract_tables=edocr_extract_tables,
                    visualize=edocr_visualize,
                    language=edocr_language,
                    cluster_threshold=edocr_cluster_threshold
                ))

            # 2b: EDGNet 세그멘테이션
            if use_segmentation:
                tracker.update("edgnet", "running", "EDGNet 세그멘테이션 시작...")
                tasks.append(call_edgnet_segment(
                    image_bytes,
                    image_filename,
                    visualize=edgnet_visualize,
                    num_classes=edgnet_num_classes,
                    save_graph=edgnet_save_graph
                ))

            # 병렬 실행
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                idx = 0

                if use_ocr:
                    result["ocr_results"] = results[idx] if not isinstance(results[idx], Exception) else {"error": str(results[idx])}
                    if not isinstance(results[idx], Exception):
                        dims_count = len(results[idx].get("data", {}).get("dimensions", []))
                        tracker.update("ocr", "completed", f"eDOCr2 OCR 완료: {dims_count}개 치수 추출", {
                            "dimensions_count": dims_count
                        })
                    else:
                        tracker.update("ocr", "error", f"eDOCr2 OCR 실패: {str(results[idx])}")
                    idx += 1

                if use_segmentation:
                    result["segmentation_results"] = results[idx] if not isinstance(results[idx], Exception) else {"error": str(results[idx])}
                    if not isinstance(results[idx], Exception):
                        comps_count = results[idx].get("data", {}).get("num_components", 0)
                        tracker.update("edgnet", "completed", f"EDGNet 세그멘테이션 완료: {comps_count}개 컴포넌트", {
                            "components_count": comps_count
                        })
                    else:
                        tracker.update("edgnet", "error", f"EDGNet 실패: {str(results[idx])}")

        else:  # speed mode
            # 속도 우선 파이프라인: YOLO + eDOCr + EDGNet 3-way 병렬
            logger.info("🟢 Running SPEED pipeline (speed priority)")
            tracker.update("pipeline", "started", "🟢 속도 우선 파이프라인 시작")

            # Step 1: 3-way 병렬 처리
            logger.info("Step 1: 3-way parallel processing (YOLO + eDOCr + EDGNet)")
            tracker.update("parallel", "running", "Step 1: 3-way 병렬 처리 시작 (YOLO + eDOCr + EDGNet)")
            tasks = []

            tasks.append(call_yolo_detect(image_bytes, image_filename, conf_threshold=yolo_conf_threshold, iou_threshold=yolo_iou_threshold, imgsz=yolo_imgsz, visualize=yolo_visualize))

            if use_ocr:
                tasks.append(call_edocr2_ocr(
                    file_bytes if is_pdf else image_bytes,
                    file.filename,
                    extract_dimensions=edocr_extract_dimensions,
                    extract_gdt=edocr_extract_gdt,
                    extract_text=edocr_extract_text,
                    extract_tables=edocr_extract_tables,
                    visualize=edocr_visualize,
                    language=edocr_language,
                    cluster_threshold=edocr_cluster_threshold
                ))

            if use_segmentation:
                tasks.append(call_edgnet_segment(
                    image_bytes,
                    image_filename,
                    visualize=edgnet_visualize,
                    num_classes=edgnet_num_classes,
                    save_graph=edgnet_save_graph
                ))

            # 병렬 실행
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 결과 할당
            logger.info(f"[SPEED MODE DEBUG] Got {len(results)} results from parallel tasks")
            logger.info(f"[SPEED MODE DEBUG] Result[0] type: {type(results[0])}, is Exception: {isinstance(results[0], Exception)}")

            result["yolo_results"] = results[0] if not isinstance(results[0], Exception) else {"error": str(results[0])}
            if not isinstance(results[0], Exception):
                detections_count = results[0].get("total_detections", 0)
                has_viz = "visualized_image" in results[0]
                viz_len = len(results[0].get("visualized_image", "")) if has_viz else 0
                logger.info(f"[SPEED MODE DEBUG] YOLO result keys: {list(results[0].keys())}")
                logger.info(f"[SPEED MODE DEBUG] has visualized_image: {has_viz}, length: {viz_len}")
                tracker.update("yolo", "completed", f"YOLO 완료: {detections_count}개 객체 검출", {
                    "detection_count": detections_count
                })
            else:
                tracker.update("yolo", "error", f"YOLO 실패: {str(results[0])}")

            idx = 1
            if use_ocr:
                result["ocr_results"] = results[idx] if not isinstance(results[idx], Exception) else {"error": str(results[idx])}
                if not isinstance(results[idx], Exception):
                    # call_edocr2_ocr() returns edocr_data directly, not wrapped in "data" key
                    dims_count = len(results[idx].get("dimensions", []))
                    tracker.update("ocr", "completed", f"eDOCr2 완료: {dims_count}개 치수 추출", {
                        "dimensions_count": dims_count
                    })
                else:
                    tracker.update("ocr", "error", f"eDOCr2 실패: {str(results[idx])}")
                idx += 1

            if use_segmentation:
                result["segmentation_results"] = results[idx] if not isinstance(results[idx], Exception) else {"error": str(results[idx])}
                if not isinstance(results[idx], Exception):
                    comps_count = results[idx].get("data", {}).get("num_components", 0)
                    tracker.update("edgnet", "completed", f"EDGNet 완료: {comps_count}개 컴포넌트", {
                        "components_count": comps_count
                    })
                else:
                    tracker.update("edgnet", "error", f"EDGNet 실패: {str(results[idx])}")

            tracker.update("parallel", "completed", "3-way 병렬 처리 완료")

        # =============================================
        # YOLO Crop OCR (선택적)
        # =============================================
        logger.info(f"YOLO Crop OCR check: use_yolo_crop_ocr={use_yolo_crop_ocr}, yolo_results_exists={result.get('yolo_results') is not None}")
        if use_yolo_crop_ocr and result.get("yolo_results"):
            logger.info("Step N: YOLO Crop OCR")
            tracker.update("yolo_crop_ocr", "running", "YOLO crop 기반 개별 OCR 시작...")

            yolo_detections = result["yolo_results"].get("detections", [])
            if yolo_detections:
                try:
                    yolo_crop_ocr_result = await process_yolo_crop_ocr(
                        image_bytes=file_bytes,
                        yolo_detections=yolo_detections,
                        call_edocr2_ocr_func=call_edocr2_ocr,
                        crop_bbox_func=crop_bbox,
                        is_false_positive_func=is_false_positive,
                        dimension_class_ids=[0, 1, 2, 3, 4, 5, 6],
                        min_confidence=paddle_min_confidence,
                        padding=0.1
                    )
                    result["yolo_crop_ocr_results"] = yolo_crop_ocr_result
                    tracker.update("yolo_crop_ocr", "completed",
                                   f"YOLO Crop OCR 완료: {yolo_crop_ocr_result['total_texts']}개 치수 검출",
                                   {"dimensions_count": yolo_crop_ocr_result['total_texts'],
                                    "crop_count": yolo_crop_ocr_result['crop_count'],
                                    "successful_crops": yolo_crop_ocr_result['successful_crops']})
                except Exception as e:
                    logger.error(f"YOLO Crop OCR failed: {e}")
                    tracker.update("yolo_crop_ocr", "error", f"YOLO Crop OCR 실패: {str(e)}")
                    result["yolo_crop_ocr_results"] = {"error": str(e)}
            else:
                tracker.update("yolo_crop_ocr", "skipped", "YOLO 검출 결과 없음")
                result["yolo_crop_ocr_results"] = None

        # =============================================
        # 공통: 앙상블 병합 (YOLO Crop OCR + eDOCr 결과 융합)
        # =============================================
        logger.info("Step N+1: Ensemble merging")
        tracker.update("ensemble", "running", "앙상블 병합 시작...")
        ensemble_dimensions = []

        # 앙상블 전략: YOLO Crop OCR + eDOCr v2 결과 융합
        if result.get("yolo_results") and result.get("ocr_results"):
            yolo_detections = result["yolo_results"].get("detections", [])
            # ocr_results는 call_edocr2_ocr()에서 edocr_data를 직접 반환하므로 {"dimensions": [...], ...} 형태
            ocr_results_data = result["ocr_results"]
            ocr_dimensions = ocr_results_data.get("dimensions", [])

            # =============================================
            # YOLO 검출 결과에 OCR 값 매칭
            # =============================================
            logger.info(f"Matching YOLO detections ({len(yolo_detections)}) with OCR dimensions ({len(ocr_dimensions)})")
            matched_yolo_detections = match_yolo_with_ocr(
                yolo_detections=yolo_detections,
                ocr_dimensions=ocr_dimensions,
                iou_threshold=0.3
            )

            # 매칭된 결과로 YOLO 결과 업데이트
            result["yolo_results"]["detections"] = matched_yolo_detections
            matched_count = sum(1 for d in matched_yolo_detections if d.get('value'))
            logger.info(f"Matched {matched_count}/{len(yolo_detections)} YOLO detections with OCR values")

            # 시각화 이미지 재생성 (OCR 값이 포함된 버전)
            # YOLO 시각화가 이미 생성되어 있고, 매칭된 값이 있으면 재생성
            if result["yolo_results"].get("visualized_image") and matched_count > 0:
                try:
                    logger.info(f"Regenerating visualization with {matched_count} matched OCR values...")
                    updated_viz_base64 = redraw_yolo_visualization(file_bytes, matched_yolo_detections)
                    result["yolo_results"]["visualized_image"] = updated_viz_base64
                    logger.info(f"✅ Updated visualization with {matched_count} matched values")
                except Exception as e:
                    logger.error(f"Failed to regenerate visualization: {e}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")

            # 고급 앙상블 전략 사용 시
            if use_ensemble and use_yolo_crop_ocr and result.get("yolo_crop_ocr_results"):
                yolo_crop_dims = result["yolo_crop_ocr_results"].get("dimensions", [])

                # 신뢰도 가중치 기반 융합
                ensemble_dimensions = ensemble_ocr_results(
                    yolo_crop_results=yolo_crop_dims,
                    edocr_results=ocr_dimensions,
                    yolo_weight=0.6,  # YOLO Crop OCR 가중치 (재현율 우수)
                    edocr_weight=0.4,  # eDOCr v2 가중치 (정밀도 보완)
                    similarity_threshold=0.7
                )

                result["ensemble"] = {
                    "dimensions": ensemble_dimensions,
                    "yolo_detections_count": len(yolo_detections),
                    "ocr_dimensions_count": len(ocr_dimensions),
                    "yolo_crop_ocr_count": len(yolo_crop_dims),
                    "strategy": "Advanced Ensemble (YOLO Crop OCR + eDOCr v2, weighted fusion)"
                }
                tracker.update("ensemble", "completed",
                               f"고급 앙상블 융합 완료: {len(ensemble_dimensions)}개 치수 (YOLO {len(yolo_crop_dims)} + eDOCr {len(ocr_dimensions)} → {len(ensemble_dimensions)})", {
                    "ensemble_count": len(ensemble_dimensions),
                    "yolo_crop_count": len(yolo_crop_dims),
                    "edocr_count": len(ocr_dimensions)
                })

            # 기본 앙상블: 단순 병합
            elif use_yolo_crop_ocr and result.get("yolo_crop_ocr_results"):
                yolo_crop_dims = result["yolo_crop_ocr_results"].get("dimensions", [])

                # 기본: eDOCr 치수 사용
                ensemble_dimensions = ocr_dimensions.copy()

                # 중복 제거를 위한 간단한 전략: 텍스트가 같으면 제외
                existing_texts = {d.get("value", "") for d in ensemble_dimensions}
                for dim in yolo_crop_dims:
                    if dim.get("value", "") not in existing_texts:
                        ensemble_dimensions.append(dim)
                        existing_texts.add(dim.get("value", ""))

                result["ensemble"] = {
                    "dimensions": ensemble_dimensions,
                    "yolo_detections_count": len(yolo_detections),
                    "ocr_dimensions_count": len(ocr_dimensions),
                    "yolo_crop_ocr_count": len(yolo_crop_dims),
                    "strategy": "Simple Merge (eDOCr + YOLO Crop OCR, deduped)"
                }
                tracker.update("ensemble", "completed",
                               f"단순 병합 완료: {len(ensemble_dimensions)}개 치수 (eDOCr {len(ocr_dimensions)} + YOLO Crop {len(yolo_crop_dims) - (len(ensemble_dimensions) - len(ocr_dimensions))} 중복제거)", {
                    "ensemble_count": len(ensemble_dimensions),
                    "yolo_count": len(yolo_detections),
                    "edocr_count": len(ocr_dimensions),
                    "yolo_crop_count": len(yolo_crop_dims)
                })
            else:
                # YOLO Crop OCR 미사용
                ensemble_dimensions = ocr_dimensions.copy()
                result["ensemble"] = {
                    "dimensions": ensemble_dimensions,
                    "yolo_detections_count": len(yolo_detections),
                    "ocr_dimensions_count": len(ocr_dimensions),
                    "strategy": "eDOCr values + YOLO bbox confidence"
                }
                tracker.update("ensemble", "completed", f"앙상블 병합 완료: {len(ensemble_dimensions)}개 치수", {
                    "ensemble_count": len(ensemble_dimensions),
                    "yolo_count": len(yolo_detections),
                    "ocr_count": len(ocr_dimensions)
                })
        elif result.get("ocr_results"):
            ensemble_dimensions = result["ocr_results"].get("data", {}).get("dimensions", [])
            result["ensemble"] = {
                "dimensions": ensemble_dimensions,
                "source": "eDOCr only"
            }
            tracker.update("ensemble", "completed", f"앙상블 완료: eDOCr만 사용 ({len(ensemble_dimensions)}개 치수)")

        # =============================================
        # 공차 예측 (앙상블 결과 사용)
        # =============================================
        if use_tolerance and ensemble_dimensions:
            logger.info("Step N+1: Tolerance prediction")
            tracker.update("tolerance", "running", "Skin Model 공차 예측 시작...")
            material = result.get("ocr_results", {}).get("data", {}).get("text", {}).get("material") or "Steel"

            tolerance_result = await call_skinmodel_tolerance(
                ensemble_dimensions,
                {"name": material},
                material_type=skin_material,
                manufacturing_process=skin_manufacturing_process,
                correlation_length=skin_correlation_length
            )
            result["tolerance_results"] = tolerance_result
            tracker.update("tolerance", "completed", "공차 예측 완료")

        processing_time = time.time() - start_time

        # Final update
        tracker.update("complete", "completed", f"✅ 파이프라인 완료 (총 {round(processing_time, 2)}초)", {
            "total_time": round(processing_time, 2),
            "pipeline_mode": pipeline_mode
        })

        # Debug: Check if visualized_image is in final response
        if "yolo_results" in result:
            has_viz_final = "visualized_image" in result.get("yolo_results", {})
            viz_len_final = len(result.get("yolo_results", {}).get("visualized_image", "")) if has_viz_final else 0
            logger.info(f"[FINAL RESPONSE DEBUG] yolo_results has visualized_image: {has_viz_final}, length: {viz_len_final}")

        # =============================================
        # 결과 저장 (JSON + 시각화 이미지) - 프로젝트별 디렉토리
        # =============================================
        saved_files = {}

        # 프로젝트별 디렉토리 생성
        project_dir = RESULTS_DIR / file_id
        project_dir.mkdir(parents=True, exist_ok=True)

        # JSON 결과 저장
        result_json_path = project_dir / "result.json"
        with open(result_json_path, 'w', encoding='utf-8') as f:
            json.dump({
                "file_id": file_id,
                "filename": file.filename,
                "timestamp": datetime.now().isoformat(),
                "pipeline_mode": pipeline_mode,
                "processing_time": round(processing_time, 2),
                "data": result
            }, f, indent=2, ensure_ascii=False, default=str)
        saved_files["result_json"] = str(result_json_path)
        logger.info(f"✅ Saved result JSON: {result_json_path}")

        # YOLO 시각화 이미지 저장
        if "yolo_results" in result and result["yolo_results"].get("visualized_image"):
            try:
                viz_img_base64 = result["yolo_results"]["visualized_image"]
                viz_img_data = base64.b64decode(viz_img_base64)
                viz_img_path = project_dir / "yolo_visualization.jpg"
                with open(viz_img_path, 'wb') as f:
                    f.write(viz_img_data)
                saved_files["yolo_visualization"] = str(viz_img_path)
                logger.info(f"✅ Saved YOLO visualization: {viz_img_path}")
            except Exception as e:
                logger.error(f"Failed to save YOLO visualization: {e}")

        # 원본 파일 저장 (참고용)
        original_file_path = project_dir / f"original{Path(file.filename).suffix}"
        with open(original_file_path, 'wb') as f:
            f.write(file_bytes)
        saved_files["original_file"] = str(original_file_path)
        logger.info(f"✅ Saved original file: {original_file_path}")

        # 다운로드 URL 생성
        download_urls = {}
        if "yolo_visualization" in saved_files:
            download_urls["yolo_visualization"] = f"/api/v1/download/{file_id}/yolo_visualization"
        if "result_json" in saved_files:
            download_urls["result_json"] = f"/api/v1/download/{file_id}/result_json"
        if "original_file" in saved_files:
            download_urls["original"] = f"/api/v1/download/{file_id}/original"

        return {
            "status": "success",
            "data": result,
            "processing_time": round(processing_time, 2),
            "file_id": file_id,
            "saved_files": saved_files,  # 저장된 파일 경로 정보 (서버 내부용)
            "download_urls": download_urls  # 다운로드 URL (클라이언트용)
        }

    except Exception as e:
        logger.error(f"Error in pipeline processing: {e}")
        tracker.update("error", "error", f"오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/quote", response_model=QuoteResponse)
async def generate_quote(
    file: UploadFile = File(..., description="도면 파일"),
    material_cost_per_kg: float = Form(5.0),
    machining_rate_per_hour: float = Form(50.0),
    tolerance_premium_factor: float = Form(1.2)
):
    """
    견적서 생성 (전체 파이프라인 + 견적 계산)

    - **file**: 도면 파일
    - **material_cost_per_kg**: 재료 단가 (USD/kg)
    - **machining_rate_per_hour**: 가공 시간당 비용 (USD/hour)
    - **tolerance_premium_factor**: 공차 정밀도 비용 계수
    """
    start_time = time.time()

    # 파일 읽기
    file_bytes = await file.read()

    try:
        # 전체 파이프라인 실행 (병렬)
        logger.info("Running full pipeline for quote generation")

        ocr_task = call_edocr2_ocr(file_bytes, file.filename)
        segment_task = call_edgnet_segment(file_bytes, file.filename, visualize=False)

        ocr_result, segment_result = await asyncio.gather(ocr_task, segment_task, return_exceptions=True)

        if isinstance(ocr_result, Exception):
            raise ocr_result

        # 공차 예측
        ocr_data = ocr_result.get("data", {})
        dimensions = ocr_data.get("dimensions", [])
        material = ocr_data.get("text", {}).get("material") or "Steel"

        tolerance_result = await call_skinmodel_tolerance(
            dimensions,
            {"name": material},
            material_type=skin_material,
            manufacturing_process=skin_manufacturing_process,
            correlation_length=skin_correlation_length
        )

        # 견적 계산
        quote_data = calculate_quote(
            ocr_result,
            tolerance_result,
            material_cost_per_kg,
            machining_rate_per_hour,
            tolerance_premium_factor
        )

        processing_time = time.time() - start_time

        return {
            "status": "success",
            "data": {
                "quote": quote_data,
                "ocr_summary": {
                    "dimensions_count": len(dimensions),
                    "drawing_number": ocr_data.get("text", {}).get("drawing_number"),
                    "material": material
                },
                "tolerance_summary": tolerance_result.get("data", {}).get("manufacturability", {})
            },
            "processing_time": round(processing_time, 2)
        }

    except Exception as e:
        logger.error(f"Error in quote generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================
# VL Model Integrated Endpoints
# =====================

@app.post("/api/v1/process_with_vl")
async def process_with_vl(
    file: UploadFile = File(...),
    model: str = Form(default="claude-3-5-sonnet-20241022"),
    quantity: int = Form(default=1),
    customer_name: str = Form(default="N/A")
):
    """
    VL 모델 기반 통합 처리 (eDOCr 대체)

    - Information Block 추출
    - 치수 추출 (VL 모델)
    - 제조 공정 추론
    - 비용 산정
    - QC Checklist 생성
    - 견적서 PDF 생성
    """
    start_time = time.time()

    try:
        # 파일 읽기
        file_bytes = await file.read()
        filename = file.filename or "unknown.pdf"

        logger.info(f"Starting VL-based processing for {filename}")

        # PDF를 이미지로 변환 (필요시)
        if filename.lower().endswith('.pdf'):
            image_bytes = pdf_to_image(file_bytes, dpi=200)
        else:
            image_bytes = file_bytes

        # 1. Information Block 추출
        logger.info("Step 1: Extracting information block...")
        async with httpx.AsyncClient(timeout=120.0) as client:
            files_info = {"file": (filename, image_bytes, "image/png")}
            data_info = {
                "query_fields": json.dumps(["name", "part number", "material", "scale", "weight"]),
                "model": model
            }

            response_info = await client.post(
                f"{VL_API_URL}/api/v1/extract_info_block",
                files=files_info,
                data=data_info
            )

            if response_info.status_code != 200:
                raise HTTPException(status_code=response_info.status_code, detail=f"Info extraction failed: {response_info.text}")

            info_block_data = response_info.json()["data"]

        # 2. 치수 추출 (VL 모델)
        logger.info("Step 2: Extracting dimensions with VL model...")
        async with httpx.AsyncClient(timeout=120.0) as client:
            files_dim = {"file": (filename, image_bytes, "image/png")}
            data_dim = {"model": model}

            response_dim = await client.post(
                f"{VL_API_URL}/api/v1/extract_dimensions",
                files=files_dim,
                data=data_dim
            )

            if response_dim.status_code != 200:
                raise HTTPException(status_code=response_dim.status_code, detail=f"Dimension extraction failed: {response_dim.text}")

            dimensions_data = response_dim.json()["data"]

        # 3. 제조 공정 추론 (같은 이미지 2번 사용 - info block + part views)
        logger.info("Step 3: Inferring manufacturing processes...")
        async with httpx.AsyncClient(timeout=120.0) as client:
            # 임시로 같은 이미지 사용
            files_proc = {
                "info_block": (filename, image_bytes, "image/png"),
                "part_views": (filename, image_bytes, "image/png")
            }
            data_proc = {"model": "gpt-4o"}

            response_proc = await client.post(
                f"{VL_API_URL}/api/v1/infer_manufacturing_process",
                files=files_proc,
                data=data_proc
            )

            if response_proc.status_code != 200:
                logger.warning(f"Process inference failed: {response_proc.text}")
                manufacturing_processes = {"Machining": "General machining processes"}
            else:
                manufacturing_processes = response_proc.json()["data"]

        # 4. QC Checklist 생성
        logger.info("Step 4: Generating QC checklist...")
        async with httpx.AsyncClient(timeout=120.0) as client:
            files_qc = {"file": (filename, image_bytes, "image/png")}
            data_qc = {"model": "gpt-4o"}

            response_qc = await client.post(
                f"{VL_API_URL}/api/v1/generate_qc_checklist",
                files=files_qc,
                data=data_qc
            )

            if response_qc.status_code != 200:
                logger.warning(f"QC checklist generation failed: {response_qc.text}")
                qc_checklist = []
            else:
                qc_checklist = response_qc.json()["data"]

        # 5. 비용 산정
        logger.info("Step 5: Estimating cost...")
        cost_estimator = get_cost_estimator()

        material = info_block_data.get("material", "Mild Steel")

        cost_breakdown = cost_estimator.estimate_cost(
            manufacturing_processes=manufacturing_processes,
            material=material,
            dimensions=dimensions_data,
            gdt_count=0,  # VL 모델은 GD&T 개수를 직접 반환하지 않음
            tolerance_count=len([d for d in dimensions_data if '±' in d or '+' in d or '-' in d]),
            quantity=quantity
        )

        # 6. 견적서 PDF 생성
        logger.info("Step 6: Generating quote PDF...")
        pdf_generator = get_pdf_generator()

        quote_number = f"Q-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        quote_data = {
            "quote_number": quote_number,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "customer_name": customer_name,
            "part_info": {
                "name": info_block_data.get("name", "N/A"),
                "part_number": info_block_data.get("part number", "N/A"),
                "material": material,
                "quantity": quantity
            },
            "cost_breakdown": cost_breakdown,
            "qc_checklist": qc_checklist,
            "manufacturing_processes": manufacturing_processes
        }

        pdf_bytes = pdf_generator.generate_quote_pdf(quote_data)

        # PDF 저장
        pdf_path = RESULTS_DIR / f"{quote_number}.pdf"
        with open(pdf_path, 'wb') as f:
            f.write(pdf_bytes)

        processing_time = time.time() - start_time

        logger.info(f"VL-based processing completed in {processing_time:.2f}s")

        return JSONResponse({
            "status": "success",
            "data": {
                "quote_number": quote_number,
                "info_block": info_block_data,
                "dimensions": dimensions_data,
                "dimensions_count": len(dimensions_data),
                "manufacturing_processes": manufacturing_processes,
                "cost_breakdown": cost_breakdown,
                "qc_checklist": qc_checklist,
                "pdf_path": str(pdf_path)
            },
            "processing_time": round(processing_time, 2),
            "model_used": model
        })

    except Exception as e:
        logger.error(f"VL-based processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/download/{file_id}/{file_type}")
async def download_result_file(file_id: str, file_type: str):
    """
    결과 파일 다운로드

    Args:
        file_id: 파일 ID
        file_type: 파일 타입 (original, yolo_visualization, result_json)
    """
    try:
        project_dir = RESULTS_DIR / file_id

        if not project_dir.exists():
            raise HTTPException(status_code=404, detail=f"Project {file_id} not found")

        # 파일 타입에 따른 경로 결정
        if file_type == "yolo_visualization":
            file_path = project_dir / "yolo_visualization.jpg"
            media_type = "image/jpeg"
            filename = f"{file_id}_yolo_visualization.jpg"
        elif file_type == "result_json":
            file_path = project_dir / "result.json"
            media_type = "application/json"
            filename = f"{file_id}_result.json"
        elif file_type == "original":
            # 원본 파일 찾기 (확장자 모름)
            original_files = list(project_dir.glob("original.*"))
            if not original_files:
                raise HTTPException(status_code=404, detail="Original file not found")
            file_path = original_files[0]
            media_type = "application/octet-stream"
            filename = f"{file_id}_original{file_path.suffix}"
        else:
            raise HTTPException(status_code=400, detail=f"Invalid file_type: {file_type}")

        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File {file_type} not found")

        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=filename
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/download_quote/{quote_number}")
async def download_quote(quote_number: str):
    """견적서 PDF 다운로드"""
    try:
        pdf_path = RESULTS_DIR / f"{quote_number}.pdf"

        if not pdf_path.exists():
            raise HTTPException(status_code=404, detail=f"Quote {quote_number} not found")

        return FileResponse(
            path=str(pdf_path),
            media_type="application/pdf",
            filename=f"quote_{quote_number}.pdf"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading quote: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================
# Main
# =====================

if __name__ == "__main__":
    port = int(os.getenv("GATEWAY_PORT", 8000))
    workers = int(os.getenv("GATEWAY_WORKERS", 4))

    logger.info(f"Starting Gateway API on port {port} with {workers} workers")
    logger.info(f"Services: eDOCr2={EDOCR2_URL}, EDGNet={EDGNET_URL}, SkinModel={SKINMODEL_URL}, VL={VL_API_URL}, YOLO={YOLO_API_URL}")

    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=port,
        workers=workers,
        log_level="info",
        reload=False
    )
