"""
eDOCr2 API Server
Engineering Drawing OCR Processing Microservice

Port: 5002
Features: Extract dimensions, GD&T, and text from engineering drawings
"""
import os

# CRITICAL: Force CPU-only mode for TensorFlow
# The GPU XLA/JIT compilation has libdevice issues causing Floor operations to fail
# Using CPU is more stable and the OCR model is small enough that CPU is sufficient
os.environ['CUDA_VISIBLE_DEVICES'] = ''  # Hide all GPUs from TensorFlow
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Reduce TF logging

import tensorflow as tf

# Verify no GPU is visible
print(f"TensorFlow GPUs visible: {tf.config.list_physical_devices('GPU')}")

# Force eager execution mode (no graph compilation)
tf.config.run_functions_eagerly(True)

import time
import json
import shutil
import logging
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from models.schemas import (
    HealthResponse, OCRResponse,
    APIInfoResponse, ParameterSchema, IOSchema, BlueprintFlowMetadata
)
from services.ocr_processor import load_models, get_processor
from utils.helpers import allowed_file, cleanup_old_files

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="eDOCr2 v2 API",
    description="Engineering Drawing OCR Service",
    version="2.0.0",
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
UPLOAD_DIR = Path("/tmp/edocr2/uploads")
RESULTS_DIR = Path("/tmp/edocr2/results")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


# =====================
# Startup/Shutdown Events
# =====================

@app.on_event("startup")
async def startup_event():
    """Load models on startup"""
    logger.info("🚀 Starting eDOCr2 API...")
    load_models()
    logger.info("✅ eDOCr2 API ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("👋 Shutting down eDOCr2 API...")


# =====================
# API Endpoints
# =====================

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint"""
    return {
        "status": "online",
        "service": "eDOCr2 v2 API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/v1/health", response_model=HealthResponse)
@app.get("/api/v2/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "eDOCr2 v2 API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/v1/info", response_model=APIInfoResponse)
async def get_api_info():
    """
    API 메타데이터 엔드포인트

    BlueprintFlow 및 Dashboard에서 API를 자동으로 등록하기 위한 메타데이터를 제공합니다.
    """
    port = int(os.getenv("EDOCR2_PORT", 5002))
    return APIInfoResponse(
        id="edocr2-v2",
        name="eDOCr2 v2 API",
        display_name="eDOCr2 v2 OCR",
        version="2.0.0",
        description="Engineering Drawing OCR - 치수/GD&T/텍스트 추출 전문 API",
        openapi_url="/openapi.json",
        base_url=f"http://localhost:{port}",
        endpoint="/api/v2/ocr",
        method="POST",
        requires_image=True,
        inputs=[
            IOSchema(
                name="file",
                type="file",
                description="분석할 도면 이미지 파일 (PDF, PNG, JPG, JPEG, TIFF)",
                required=True
            )
        ],
        outputs=[
            IOSchema(
                name="dimensions",
                type="array",
                description="추출된 치수 정보 목록"
            ),
            IOSchema(
                name="gdt_symbols",
                type="array",
                description="추출된 GD&T 심볼 목록"
            ),
            IOSchema(
                name="text_blocks",
                type="array",
                description="추출된 텍스트 블록 목록"
            ),
            IOSchema(
                name="processing_time",
                type="float",
                description="처리 시간 (초)"
            )
        ],
        parameters=[
            ParameterSchema(
                name="extract_dimensions",
                type="boolean",
                default=True,
                description="치수 정보 추출 활성화",
                required=False
            ),
            ParameterSchema(
                name="extract_gdt",
                type="boolean",
                default=True,
                description="GD&T 정보 추출 활성화",
                required=False
            ),
            ParameterSchema(
                name="extract_text",
                type="boolean",
                default=True,
                description="텍스트 정보 추출 활성화",
                required=False
            ),
            ParameterSchema(
                name="use_vl_model",
                type="boolean",
                default=False,
                description="Vision Language 모델 사용 (더 정확하지만 느림)",
                required=False
            ),
            ParameterSchema(
                name="visualize",
                type="boolean",
                default=False,
                description="결과 시각화 이미지 생성",
                required=False
            ),
            ParameterSchema(
                name="use_gpu_preprocessing",
                type="boolean",
                default=False,
                description="GPU 전처리 사용 (CLAHE, 노이즈 제거)",
                required=False
            )
        ],
        blueprintflow=BlueprintFlowMetadata(
            icon="📄",
            color="#8b5cf6",
            category="ocr"
        ),
        output_mappings={
            "dimensions": "data.dimensions",
            "gdt_symbols": "data.gdt_symbols",
            "text_blocks": "data.text_blocks",
            "processing_time": "processing_time"
        }
    )


@app.post("/api/v2/ocr", response_model=OCRResponse)
async def process_drawing(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Drawing file (PDF, PNG, JPG)"),
    extract_dimensions: bool = Form(True, description="Extract dimension information"),
    extract_gdt: bool = Form(True, description="Extract GD&T information"),
    extract_text: bool = Form(True, description="Extract text information"),
    use_vl_model: bool = Form(False, description="Use Vision Language model"),
    visualize: bool = Form(False, description="Generate visualization image"),
    use_gpu_preprocessing: bool = Form(False, description="Use GPU preprocessing")
):
    """
    Process engineering drawing OCR

    - **file**: Drawing file (PDF, PNG, JPG, JPEG, TIFF)
    - **extract_dimensions**: Extract dimension information
    - **extract_gdt**: Extract GD&T information
    - **extract_text**: Extract text information
    - **use_vl_model**: Use Vision Language model (slower but more accurate)
    - **visualize**: Generate visualization image
    - **use_gpu_preprocessing**: Use GPU preprocessing (CLAHE, denoising)
    """
    start_time = time.time()

    # Validate file
    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: pdf, png, jpg, jpeg, tiff"
        )

    # Check file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )

    # Save file
    file_id = f"{int(time.time())}_{file.filename}"
    file_path = UPLOAD_DIR / file_id

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"File uploaded: {file_id} ({file_size / 1024:.2f} KB)")

        # OCR processing
        processor = get_processor()
        ocr_result = processor.process_ocr(
            file_path,
            extract_dimensions=extract_dimensions,
            extract_gdt=extract_gdt,
            extract_text=extract_text,
            use_vl_model=use_vl_model,
            visualize=visualize,
            use_gpu_preprocessing=use_gpu_preprocessing
        )

        processing_time = time.time() - start_time

        # Background task: cleanup old files
        background_tasks.add_task(cleanup_old_files, UPLOAD_DIR)

        return {
            "status": "success",
            "data": ocr_result,
            "processing_time": round(processing_time, 2),
            "file_id": file_id
        }

    except Exception as e:
        logger.error(f"Error processing file: {e}")
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/result/{file_id}")
async def get_result(file_id: str):
    """Get processing result (for future async processing)"""
    result_path = RESULTS_DIR / f"{file_id}.json"

    if not result_path.exists():
        raise HTTPException(status_code=404, detail="Result not found")

    with open(result_path, 'r') as f:
        result = json.load(f)

    return JSONResponse(content=result)


@app.delete("/api/v1/cleanup")
async def cleanup_files(max_age_hours: int = 24):
    """Manual file cleanup"""
    try:
        cleanup_old_files(UPLOAD_DIR, max_age_hours)
        cleanup_old_files(RESULTS_DIR, max_age_hours)
        return {"status": "success", "message": f"Cleaned up files older than {max_age_hours} hours"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================
# Main
# =====================

if __name__ == "__main__":
    port = int(os.getenv("EDOCR2_PORT", 5001))
    workers = int(os.getenv("EDOCR2_WORKERS", 4))

    logger.info(f"Starting eDOCr2 API on port {port} with {workers} workers")

    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=port,
        workers=workers,
        log_level="info",
        reload=False
    )
