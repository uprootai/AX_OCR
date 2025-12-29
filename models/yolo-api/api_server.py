#!/usr/bin/env python3
"""
YOLOv11 API Server for Engineering Drawing Analysis
Port: 5005

통합 YOLO API - 여러 모델을 동적으로 로딩하여 사용
"""
import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager

import torch
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models.schemas import HealthResponse
from services import (
    YOLOInferenceService,
    ModelRegistry,
    set_model_state,
    get_inference_service,
)
from routers import detection_router, models_router

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# =====================
# Configuration
# =====================

YOLO_API_PORT = int(os.getenv('YOLO_API_PORT', '5005'))
YOLO_MODEL_PATH = os.getenv('YOLO_MODEL_PATH', '/app/models/best.pt')
MODELS_DIR = Path('/app/models')
MODEL_REGISTRY_PATH = MODELS_DIR / 'model_registry.yaml'
UPLOAD_DIR = Path('/tmp/yolo-api/uploads')
RESULTS_DIR = Path('/tmp/yolo-api/results')

# Create directories
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# =====================
# Lifespan
# =====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model registry and default model on startup, cleanup on shutdown"""
    # Startup
    print("=" * 70)
    print("🚀 YOLOv11 통합 API Server Starting...")
    print("=" * 70)

    # 모델 레지스트리 초기화
    model_registry = ModelRegistry(MODEL_REGISTRY_PATH, MODELS_DIR)

    # 기본 모델 로드
    default_model = model_registry.get_default_model()
    inference_service = model_registry.get_inference_service(default_model)

    if inference_service is None:
        # 폴백: 환경변수 모델 경로 사용
        logger.warning(f"기본 모델 로드 실패, 폴백: {YOLO_MODEL_PATH}")
        inference_service = YOLOInferenceService(YOLO_MODEL_PATH)
        inference_service.load_model()

    # Set global state
    set_model_state(model_registry, inference_service)

    print(f"📦 등록된 모델: {len(model_registry.get_models())}개")
    print(f"✅ 기본 모델: {default_model}")

    print("=" * 70)
    print(f"✅ Server ready on port {YOLO_API_PORT}")
    print("=" * 70)

    yield

    # Shutdown
    print("🛑 Shutting down YOLOv11 API Server...")


# =====================
# FastAPI App
# =====================

app = FastAPI(
    title="YOLOv11 Drawing Analysis API",
    description="통합 YOLO API - 다중 모델 지원 (기계도면, P&ID 등)",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(detection_router)
app.include_router(models_router)


# =====================
# Health & Root Endpoints
# =====================

@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    inference_service = get_inference_service()
    gpu_name = None
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)

    return HealthResponse(
        status="healthy",
        model_loaded=inference_service is not None and inference_service.model is not None,
        model_path=YOLO_MODEL_PATH,
        device=inference_service.device if inference_service else "unknown",
        gpu_available=torch.cuda.is_available(),
        gpu_name=gpu_name
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "YOLOv11 Drawing Analysis API",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "health": "/api/v1/health",
            "info": "/api/v1/info",
            "detect": "/api/v1/detect",
            "extract_dimensions": "/api/v1/extract_dimensions",
            "download": "/api/v1/download/{file_id}",
            "models": "/api/v1/models",
            "docs": "/docs"
        }
    }


# =====================
# Main
# =====================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=YOLO_API_PORT,
        reload=False,
        log_level="info"
    )
