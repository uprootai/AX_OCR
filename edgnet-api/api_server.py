"""
EDGNet API Server
그래프 신경망 기반 도면 세그멘테이션 마이크로서비스

포트: 5002
기능: 도면을 Contour/Text/Dimension 컴포넌트로 분류
"""

import os
import time
import shutil
import logging
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import torch

# Import from modules
from models.schemas import (
    HealthResponse,
    SegmentRequest,
    SegmentResponse,
    VectorizeRequest,
    VectorizeResponse
)
from services.inference import (
    EDGNetInferenceService,
    check_edgnet_availability,
    check_model_exists
)
from utils.helpers import allowed_file, cleanup_old_files

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =====================
# Configuration
# =====================

UPLOAD_DIR = Path("/tmp/edgnet/uploads")
RESULTS_DIR = Path("/tmp/edgnet/results")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'tiff', 'bmp'}

MODEL_PATH = Path("/models/graphsage_dimension_classifier.pth")

# =====================
# FastAPI App
# =====================

app = FastAPI(
    title="EDGNet API",
    description="Engineering Drawing Graph Neural Network Segmentation Service",
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

# Global inference service
inference_service: EDGNetInferenceService = None


# =====================
# Startup Event
# =====================

@app.on_event("startup")
async def startup_event():
    """Validate EDGNet pipeline and model on startup"""
    global inference_service

    logger.info("Starting EDGNet API...")
    logger.info("Validating EDGNet pipeline...")

    edgnet_available = check_edgnet_availability()
    model_exists = check_model_exists(str(MODEL_PATH))

    if not edgnet_available:
        logger.error("EDGNet pipeline NOT available")
        logger.error("   Install EDGNet from: https://github.com/[repository_url]")
        logger.error("   EDGNet API will return 503 errors until pipeline is installed")
    else:
        logger.info("EDGNet pipeline available")

        if not model_exists:
            logger.error(f"Model file NOT found: {MODEL_PATH}")
            logger.error("   Download model from: [model_url]")
            logger.error("   EDGNet API will return 503 errors until model is available")
        else:
            logger.info(f"Model file found: {MODEL_PATH}")

            # Auto-detect GPU availability
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            logger.info(f"Using device: {device}")
            if device == 'cuda':
                logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
                logger.info(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

            # Initialize inference service
            inference_service = EDGNetInferenceService(
                model_path=str(MODEL_PATH),
                device=device
            )

            logger.info("EDGNet API ready for segmentation")

    logger.info("EDGNet API startup complete")


# =====================
# API Endpoints
# =====================

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint"""
    return {
        "status": "online",
        "service": "EDGNet API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health", response_model=HealthResponse)
@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint

    Returns the current health status of the EDGNet API service.
    """
    is_ready = check_edgnet_availability() and check_model_exists(str(MODEL_PATH))
    status = "healthy" if is_ready else "degraded"

    return {
        "status": status,
        "service": "EDGNet API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v1/segment", response_model=SegmentResponse)
async def segment_drawing(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="도면 이미지 (PNG, JPG)"),
    visualize: bool = Form(True, description="시각화 생성"),
    num_classes: int = Form(3, description="분류 클래스 수 (2 or 3)"),
    save_graph: bool = Form(False, description="그래프 저장")
):
    """
    도면 세그멘테이션 - 컴포넌트 분류

    - **file**: 도면 이미지 (PNG, JPG, TIFF)
    - **visualize**: 분류 결과 시각화 이미지 생성 여부
    - **num_classes**: 2 (Text/Non-text) 또는 3 (Contour/Text/Dimension)
    - **save_graph**: 그래프 구조 JSON 저장 여부
    """
    start_time = time.time()

    # Validate file
    if not allowed_file(file.filename, ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
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

        # Process segmentation
        if inference_service is None:
            raise HTTPException(
                status_code=503,
                detail="Inference service not initialized"
            )

        segment_result = inference_service.process_segmentation(
            file_path,
            visualize=visualize,
            num_classes=num_classes,
            save_graph=save_graph,
            results_dir=RESULTS_DIR
        )

        processing_time = time.time() - start_time

        # Background task: cleanup old files
        background_tasks.add_task(cleanup_old_files, UPLOAD_DIR)

        return {
            "status": "success",
            "data": segment_result,
            "processing_time": round(processing_time, 2),
            "file_id": file_id
        }

    except Exception as e:
        logger.error(f"Error processing file: {e}")
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/vectorize", response_model=VectorizeResponse)
async def vectorize_drawing(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="도면 이미지"),
    save_bezier: bool = Form(True, description="Bezier 곡선 저장")
):
    """
    도면 벡터화

    - **file**: 도면 이미지 (PNG, JPG)
    - **save_bezier**: Bezier 곡선 데이터 JSON 저장 여부
    """
    start_time = time.time()

    # Validate file
    if not allowed_file(file.filename, ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Save file
    file_id = f"{int(time.time())}_{file.filename}"
    file_path = UPLOAD_DIR / file_id

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"File uploaded for vectorization: {file_id}")

        # Process vectorization
        if inference_service is None:
            raise HTTPException(
                status_code=503,
                detail="Inference service not initialized"
            )

        vectorize_result = inference_service.process_vectorization(
            file_path,
            save_bezier=save_bezier
        )

        processing_time = time.time() - start_time

        # Background task
        background_tasks.add_task(cleanup_old_files, UPLOAD_DIR)

        return {
            "status": "success",
            "data": vectorize_result,
            "processing_time": round(processing_time, 2),
            "file_id": file_id
        }

    except Exception as e:
        logger.error(f"Error vectorizing file: {e}")
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/result/{filename}")
async def get_result_file(filename: str):
    """Download result file"""
    file_path = RESULTS_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        media_type='application/octet-stream',
        filename=filename
    )


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
    port = int(os.getenv("EDGNET_PORT", 5002))

    logger.info(f"Starting EDGNet API on port {port}")

    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=False
    )
