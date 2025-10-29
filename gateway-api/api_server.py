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
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import fitz  # PyMuPDF
from PIL import Image

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
EDOCR2_URL = os.getenv("EDOCR2_URL", "http://localhost:5001")
EDGNET_URL = os.getenv("EDGNET_URL", "http://localhost:5002")
SKINMODEL_URL = os.getenv("SKINMODEL_URL", "http://localhost:5003")

UPLOAD_DIR = Path("/tmp/gateway/uploads")
RESULTS_DIR = Path("/tmp/gateway/results")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


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


class ProcessResponse(BaseModel):
    status: str
    data: Dict[str, Any]
    processing_time: float
    file_id: str


class QuoteRequest(BaseModel):
    material_cost_per_kg: float = Field(5.0, description="재료 단가 (USD/kg)")
    machining_rate_per_hour: float = Field(50.0, description="가공 시간당 비용 (USD/hour)")
    tolerance_premium_factor: float = Field(1.2, description="공차 정밀도 비용 계수")


class QuoteResponse(BaseModel):
    status: str
    data: Dict[str, Any]
    processing_time: float


# =====================
# Helper Functions
# =====================

async def check_service_health(url: str, service_name: str) -> str:
    """서비스 헬스체크"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
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


async def call_edgnet_segment(file_bytes: bytes, filename: str, visualize: bool = True) -> Dict[str, Any]:
    """EDGNet API 호출"""
    try:
        logger.info(f"Calling EDGNet API for {filename}")

        async with httpx.AsyncClient(timeout=60.0) as client:
            files = {"file": (filename, file_bytes, "image/png")}
            data = {"visualize": visualize, "num_classes": 3}

            response = await client.post(
                f"{EDGNET_URL}/api/v1/segment",
                files=files,
                data=data
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail=f"EDGNet failed: {response.text}")

    except Exception as e:
        logger.error(f"EDGNet API call failed: {e}")
        raise HTTPException(status_code=500, detail=f"EDGNet error: {str(e)}")


async def call_edocr2_ocr(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """eDOCr2 API 호출"""
    try:
        logger.info(f"Calling eDOCr2 API for {filename}")

        async with httpx.AsyncClient(timeout=60.0) as client:
            files = {"file": (filename, file_bytes, "application/pdf")}
            data = {
                "extract_dimensions": True,
                "extract_gdt": True,
                "extract_text": True,
                "use_vl_model": False
            }

            response = await client.post(
                f"{EDOCR2_URL}/api/v1/ocr",
                files=files,
                data=data
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail=f"eDOCr2 failed: {response.text}")

    except Exception as e:
        logger.error(f"eDOCr2 API call failed: {e}")
        raise HTTPException(status_code=500, detail=f"eDOCr2 error: {str(e)}")


async def call_skinmodel_tolerance(dimensions: List[Dict], material: Dict) -> Dict[str, Any]:
    """Skin Model API 호출 - 데이터 형식 변환 포함"""
    try:
        logger.info(f"Calling Skin Model API with {len(dimensions)} dimensions")

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
                "manufacturing_process": "machining",
                "correlation_length": 1.0
            }

            logger.info(f"Sending to Skin Model: {data}")

            response = await client.post(
                f"{SKINMODEL_URL}/api/v1/tolerance",
                json=data
            )

            logger.info(f"Skin Model response: {response.status_code}")

            if response.status_code == 200:
                return response.json()
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


@app.post("/api/v1/process", response_model=ProcessResponse)
async def process_drawing(
    file: UploadFile = File(..., description="도면 파일"),
    use_segmentation: bool = Form(True),
    use_ocr: bool = Form(True),
    use_tolerance: bool = Form(True),
    visualize: bool = Form(True)
):
    """
    전체 파이프라인 처리

    - **file**: 도면 파일 (PDF 또는 이미지)
    - **use_segmentation**: EDGNet 세그멘테이션 사용
    - **use_ocr**: eDOCr2 OCR 사용
    - **use_tolerance**: Skin Model 공차 예측 사용
    - **visualize**: 시각화 생성
    """
    start_time = time.time()

    # 파일 읽기
    file_bytes = await file.read()
    file_id = f"{int(time.time())}_{file.filename}"

    logger.info(f"Processing pipeline for {file_id}")
    logger.info(f"Options: segment={use_segmentation}, ocr={use_ocr}, tolerance={use_tolerance}")

    result = {
        "segmentation": None,
        "ocr": None,
        "tolerance": None
    }

    try:
        # PDF 파일인지 확인
        is_pdf = file.filename.lower().endswith('.pdf')

        # 세그멘테이션을 위한 파일 준비 (PDF는 이미지로 변환)
        segmentation_bytes = file_bytes
        segmentation_filename = file.filename
        if use_segmentation and is_pdf:
            logger.info(f"PDF detected, converting to image for segmentation: {file.filename}")
            segmentation_bytes = pdf_to_image(file_bytes)
            # Change extension to .png for converted PDF
            segmentation_filename = file.filename.rsplit('.', 1)[0] + '.png'

        # 병렬 처리 (세그멘테이션 + OCR)
        tasks = []

        if use_segmentation:
            tasks.append(call_edgnet_segment(segmentation_bytes, segmentation_filename, visualize))

        if use_ocr:
            tasks.append(call_edocr2_ocr(file_bytes, file.filename))

        # 병렬 실행
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            idx = 0
            if use_segmentation:
                result["segmentation"] = results[idx] if not isinstance(results[idx], Exception) else {"error": str(results[idx])}
                idx += 1

            if use_ocr:
                result["ocr"] = results[idx] if not isinstance(results[idx], Exception) else {"error": str(results[idx])}

        # 순차 처리 (공차 예측은 OCR 결과 필요)
        if use_tolerance and use_ocr and result["ocr"] and "error" not in result["ocr"]:
            ocr_data = result["ocr"].get("data", {})
            dimensions = ocr_data.get("dimensions", [])
            material = ocr_data.get("text", {}).get("material", "Steel")

            if dimensions:
                tolerance_result = await call_skinmodel_tolerance(
                    dimensions,
                    {"name": material}
                )
                result["tolerance"] = tolerance_result

        processing_time = time.time() - start_time

        return {
            "status": "success",
            "data": result,
            "processing_time": round(processing_time, 2),
            "file_id": file_id
        }

    except Exception as e:
        logger.error(f"Error in pipeline processing: {e}")
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
        material = ocr_data.get("text", {}).get("material", "Steel")

        tolerance_result = await call_skinmodel_tolerance(
            dimensions,
            {"name": material}
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
# Main
# =====================

if __name__ == "__main__":
    port = int(os.getenv("GATEWAY_PORT", 8000))
    workers = int(os.getenv("GATEWAY_WORKERS", 4))

    logger.info(f"Starting Gateway API on port {port} with {workers} workers")
    logger.info(f"Services: eDOCr2={EDOCR2_URL}, EDGNet={EDGNET_URL}, SkinModel={SKINMODEL_URL}")

    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=port,
        workers=workers,
        log_level="info",
        reload=False
    )
