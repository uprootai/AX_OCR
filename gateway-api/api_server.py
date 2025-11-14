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

# Import cost estimator and PDF generator
from cost_estimator import get_cost_estimator
from pdf_generator import get_pdf_generator

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

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
EDOCR_V1_URL = os.getenv("EDOCR_V1_URL", "http://edocr2-api-v1:5001")
EDOCR_V2_URL = os.getenv("EDOCR_V2_URL", "http://edocr2-api-v2:5002")
EDOCR2_URL = os.getenv("EDOCR2_URL", EDOCR_V2_URL)  # Use V2 for better performance
EDGNET_URL = os.getenv("EDGNET_URL", "http://edgnet-api:5002")  # Internal container port
SKINMODEL_URL = os.getenv("SKINMODEL_URL", "http://skinmodel-api:5003")
VL_API_URL = os.getenv("VL_API_URL", "http://vl-api:5004")
YOLO_API_URL = os.getenv("YOLO_API_URL", "http://yolo-api:5005")

UPLOAD_DIR = Path("/tmp/gateway/uploads")
RESULTS_DIR = Path("/tmp/gateway/results")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# =====================
# Progress Tracking
# =====================

# Global dictionary to store progress for each job_id
progress_store: Dict[str, List[Dict[str, Any]]] = {}

class ProgressTracker:
    """Track pipeline progress for real-time updates"""

    def __init__(self, job_id: str):
        self.job_id = job_id
        progress_store[job_id] = []

    def update(self, step: str, status: str, message: str, data: Dict[str, Any] = None):
        """Add progress update"""
        progress_entry = {
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "status": status,  # 'started', 'running', 'completed', 'error'
            "message": message,
            "data": data or {}
        }
        progress_store[self.job_id].append(progress_entry)
        logger.info(f"[{self.job_id}] {step}: {message}")

    def get_progress(self) -> List[Dict[str, Any]]:
        """Get all progress updates"""
        return progress_store.get(self.job_id, [])

    def cleanup(self):
        """Remove progress data after completion"""
        if self.job_id in progress_store:
            del progress_store[self.job_id]


# =====================
# Pydantic Models
# =====================

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str
    services: Dict[str, str]


class ProcessRequest(BaseModel):
    use_segmentation: bool = Field(True, description="EDGNet 세그멘테이션 사용")
    use_ocr: bool = Field(True, description="eDOCr2 OCR 사용")
    use_tolerance: bool = Field(True, description="Skin Model 공차 예측 사용")
    visualize: bool = Field(True, description="시각화 생성")


class DetectionResult(BaseModel):
    """YOLO 검출 결과"""
    class_id: int = Field(..., description="클래스 ID")
    class_name: str = Field(..., description="클래스 이름")
    confidence: float = Field(..., description="신뢰도 (0-1)")
    bbox: Dict[str, int] = Field(..., description="바운딩 박스 {x, y, width, height}")

class YOLOResults(BaseModel):
    """YOLO 검출 결과"""
    detections: List[DetectionResult] = Field(default=[], description="검출된 객체 목록")
    total_detections: int = Field(0, description="총 검출 개수")
    processing_time: float = Field(0, description="YOLO 처리 시간 (초)")
    model_used: Optional[str] = Field(None, description="사용된 모델")

class DimensionData(BaseModel):
    """치수 정보"""
    value: Optional[str] = Field(None, description="치수 값")
    unit: Optional[str] = Field(None, description="단위")
    tolerance: Optional[Dict[str, Any]] = Field(None, description="공차 정보")
    bbox: Optional[Dict[str, int]] = Field(None, description="위치")

class OCRResults(BaseModel):
    """OCR 결과"""
    dimensions: List[DimensionData] = Field(default=[], description="추출된 치수")
    gdt_symbols: List[Dict[str, Any]] = Field(default=[], description="GD&T 기호")
    text_blocks: List[Dict[str, Any]] = Field(default=[], description="텍스트 블록")
    tables: List[Dict[str, Any]] = Field(default=[], description="테이블 데이터")
    processing_time: float = Field(0, description="OCR 처리 시간 (초)")

class ComponentData(BaseModel):
    """세그멘테이션 컴포넌트"""
    component_id: int = Field(..., description="컴포넌트 ID")
    class_id: int = Field(..., description="클래스 ID (0=배경, 1=윤곽선, 2=텍스트, 3=치수)")
    bbox: Dict[str, int] = Field(..., description="바운딩 박스")
    area: int = Field(..., description="면적 (픽셀)")

class SegmentationResults(BaseModel):
    """세그멘테이션 결과"""
    components: List[ComponentData] = Field(default=[], description="감지된 컴포넌트")
    total_components: int = Field(0, description="총 컴포넌트 수")
    processing_time: float = Field(0, description="세그멘테이션 처리 시간 (초)")

class ToleranceResult(BaseModel):
    """공차 예측 결과"""
    feasibility_score: float = Field(..., description="제조 가능성 점수 (0-1)")
    predicted_tolerance: float = Field(..., description="예측된 공차 (mm)")
    material: Optional[str] = Field(None, description="재질")
    manufacturing_process: Optional[str] = Field(None, description="제조 공정")
    processing_time: float = Field(0, description="공차 예측 처리 시간 (초)")

class ProcessData(BaseModel):
    """전체 처리 결과 데이터"""
    yolo_results: Optional[YOLOResults] = Field(None, description="YOLO 검출 결과")
    ocr_results: Optional[OCRResults] = Field(None, description="OCR 추출 결과")
    segmentation_results: Optional[SegmentationResults] = Field(None, description="세그멘테이션 결과")
    tolerance_results: Optional[ToleranceResult] = Field(None, description="공차 예측 결과")
    pipeline_mode: str = Field("hybrid", description="사용된 파이프라인 모드")

    model_config = {
        "json_schema_extra": {
            "example": {
                "yolo_results": {
                    "detections": [
                        {
                            "class_id": 1,
                            "class_name": "linear_dim",
                            "confidence": 0.92,
                            "bbox": {"x": 100, "y": 200, "width": 50, "height": 30}
                        }
                    ],
                    "total_detections": 28,
                    "processing_time": 0.15
                },
                "ocr_results": {
                    "dimensions": [
                        {
                            "value": "50.5",
                            "unit": "mm",
                            "tolerance": {"upper": "+0.1", "lower": "-0.1"}
                        }
                    ],
                    "processing_time": 2.34
                },
                "segmentation_results": {
                    "components": [
                        {
                            "component_id": 1,
                            "class_id": 1,
                            "bbox": {"x": 10, "y": 20, "width": 100, "height": 50},
                            "area": 5000
                        }
                    ],
                    "total_components": 15,
                    "processing_time": 1.23
                },
                "tolerance_results": {
                    "feasibility_score": 0.85,
                    "predicted_tolerance": 0.05,
                    "material": "aluminum",
                    "manufacturing_process": "machining",
                    "processing_time": 0.45
                },
                "pipeline_mode": "hybrid"
            }
        }
    }

class ProcessResponse(BaseModel):
    """전체 파이프라인 처리 응답"""
    status: str = Field(..., description="처리 상태 (success/error)")
    data: ProcessData = Field(..., description="처리 결과 데이터")
    processing_time: float = Field(..., description="총 처리 시간 (초)")
    file_id: str = Field(..., description="파일 식별자")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "success",
                "data": {
                    "yolo_results": {
                        "total_detections": 28,
                        "processing_time": 0.15
                    },
                    "ocr_results": {
                        "dimensions": [],
                        "processing_time": 2.34
                    },
                    "pipeline_mode": "hybrid"
                },
                "processing_time": 5.67,
                "file_id": "abc123-def456"
            }
        }
    }


class QuoteRequest(BaseModel):
    material_cost_per_kg: float = Field(5.0, description="재료 단가 (USD/kg)")
    machining_rate_per_hour: float = Field(50.0, description="가공 시간당 비용 (USD/hour)")
    tolerance_premium_factor: float = Field(1.2, description="공차 정밀도 비용 계수")


class CostBreakdown(BaseModel):
    """비용 세부 내역"""
    material_cost: float = Field(..., description="재료비 (USD)")
    machining_cost: float = Field(..., description="가공비 (USD)")
    tolerance_premium: float = Field(..., description="공차 정밀도 추가 비용 (USD)")
    total_cost: float = Field(..., description="총 비용 (USD)")

class QuoteData(BaseModel):
    """견적서 데이터"""
    quote_number: str = Field(..., description="견적서 번호")
    part_name: Optional[str] = Field(None, description="부품 이름")
    material: Optional[str] = Field(None, description="재질")
    estimated_weight: Optional[float] = Field(None, description="예상 중량 (kg)")
    estimated_machining_time: Optional[float] = Field(None, description="예상 가공 시간 (시간)")
    cost_breakdown: CostBreakdown = Field(..., description="비용 세부 내역")
    dimensions_analyzed: int = Field(0, description="분석된 치수 개수")
    gdt_analyzed: int = Field(0, description="분석된 GD&T 개수")
    confidence_score: float = Field(0, description="견적 신뢰도 (0-1)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "quote_number": "Q2025-001",
                "part_name": "Intermediate Shaft",
                "material": "Steel",
                "estimated_weight": 2.5,
                "estimated_machining_time": 4.5,
                "cost_breakdown": {
                    "material_cost": 12.50,
                    "machining_cost": 225.00,
                    "tolerance_premium": 27.00,
                    "total_cost": 264.50
                },
                "dimensions_analyzed": 15,
                "gdt_analyzed": 5,
                "confidence_score": 0.88
            }
        }
    }

class QuoteResponse(BaseModel):
    """견적서 생성 응답"""
    status: str = Field(..., description="처리 상태 (success/error)")
    data: QuoteData = Field(..., description="견적서 데이터")
    processing_time: float = Field(..., description="처리 시간 (초)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "success",
                "data": {
                    "quote_number": "Q2025-001",
                    "cost_breakdown": {
                        "material_cost": 12.50,
                        "machining_cost": 225.00,
                        "tolerance_premium": 27.00,
                        "total_cost": 264.50
                    },
                    "confidence_score": 0.88
                },
                "processing_time": 1.23
            }
        }
    }


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
            # All services use v1 API for health checks
            response = await client.get(f"{url}/api/v1/health")
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
                dimensions_count = len(edocr_response.get('dimensions', []))
                gdt_count = len(edocr_response.get('gdt_symbols', []))
                logger.info(f"eDOCr2 dimensions: {dimensions_count}, GD&T: {gdt_count}")
                return edocr_response
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
        transformed_dimensions = []
        for dim in dimensions:
            transformed_dim = {
                "type": dim.get("type", "length"),
                "value": dim.get("value", 0.0),
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
        "yolo": None,
        "segmentation": None,
        "ocr": None,
        "tolerance": None,
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
            result["yolo"] = yolo_result

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
                    result["ocr"] = results[idx] if not isinstance(results[idx], Exception) else {"error": str(results[idx])}
                    if not isinstance(results[idx], Exception):
                        dims_count = len(results[idx].get("data", {}).get("dimensions", []))
                        tracker.update("ocr", "completed", f"eDOCr2 OCR 완료: {dims_count}개 치수 추출", {
                            "dimensions_count": dims_count
                        })
                    else:
                        tracker.update("ocr", "error", f"eDOCr2 OCR 실패: {str(results[idx])}")
                    idx += 1

                if use_segmentation:
                    result["segmentation"] = results[idx] if not isinstance(results[idx], Exception) else {"error": str(results[idx])}
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
            result["yolo"] = results[0] if not isinstance(results[0], Exception) else {"error": str(results[0])}
            if not isinstance(results[0], Exception):
                detections_count = results[0].get("total_detections", 0)
                tracker.update("yolo", "completed", f"YOLO 완료: {detections_count}개 객체 검출", {
                    "detection_count": detections_count
                })
            else:
                tracker.update("yolo", "error", f"YOLO 실패: {str(results[0])}")

            idx = 1
            if use_ocr:
                result["ocr"] = results[idx] if not isinstance(results[idx], Exception) else {"error": str(results[idx])}
                if not isinstance(results[idx], Exception):
                    dims_count = len(results[idx].get("data", {}).get("dimensions", []))
                    tracker.update("ocr", "completed", f"eDOCr2 완료: {dims_count}개 치수 추출", {
                        "dimensions_count": dims_count
                    })
                else:
                    tracker.update("ocr", "error", f"eDOCr2 실패: {str(results[idx])}")
                idx += 1

            if use_segmentation:
                result["segmentation"] = results[idx] if not isinstance(results[idx], Exception) else {"error": str(results[idx])}
                if not isinstance(results[idx], Exception):
                    comps_count = results[idx].get("data", {}).get("num_components", 0)
                    tracker.update("edgnet", "completed", f"EDGNet 완료: {comps_count}개 컴포넌트", {
                        "components_count": comps_count
                    })
                else:
                    tracker.update("edgnet", "error", f"EDGNet 실패: {str(results[idx])}")

            tracker.update("parallel", "completed", "3-way 병렬 처리 완료")

        # =============================================
        # 공통: 앙상블 병합 (YOLO + eDOCr 결과 통합)
        # =============================================
        logger.info("Step N: Ensemble merging")
        tracker.update("ensemble", "running", "앙상블 병합 시작...")
        ensemble_dimensions = []

        # YOLO bbox 우선, eDOCr 값 우선 전략
        if result.get("yolo") and result.get("ocr"):
            yolo_detections = result["yolo"].get("detections", [])
            ocr_dimensions = result["ocr"].get("data", {}).get("dimensions", [])

            # 간단한 앙상블: eDOCr 치수를 사용하되, YOLO 검출 개수를 메타데이터로 추가
            ensemble_dimensions = ocr_dimensions
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
        elif result.get("ocr"):
            ensemble_dimensions = result["ocr"].get("data", {}).get("dimensions", [])
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
            material = result.get("ocr", {}).get("data", {}).get("text", {}).get("material") or "Steel"

            tolerance_result = await call_skinmodel_tolerance(
                ensemble_dimensions,
                {"name": material},
                material_type=skin_material,
                manufacturing_process=skin_manufacturing_process,
                correlation_length=skin_correlation_length
            )
            result["tolerance"] = tolerance_result
            tracker.update("tolerance", "completed", "공차 예측 완료")

        processing_time = time.time() - start_time

        # Final update
        tracker.update("complete", "completed", f"✅ 파이프라인 완료 (총 {round(processing_time, 2)}초)", {
            "total_time": round(processing_time, 2),
            "pipeline_mode": pipeline_mode
        })

        return {
            "status": "success",
            "data": result,
            "processing_time": round(processing_time, 2),
            "file_id": file_id
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
