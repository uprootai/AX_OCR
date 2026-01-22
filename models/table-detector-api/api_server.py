"""
Table Detector API Server
테이블 검출 및 구조 추출 API

기술:
- Microsoft Table Transformer (TATR) - 테이블 영역 검출
- img2table - 테이블 구조 인식 및 내용 추출
- 다양한 OCR 엔진 연동 (PaddleOCR, EasyOCR, Tesseract)

포트: 5022
카테고리: detection
"""

import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Routers
from routers import table_router

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
API_PORT = int(os.getenv("TABLE_DETECTOR_PORT", "5022"))


# =====================
# Schemas
# =====================

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str
    models_loaded: bool = False


# =====================
# Model State
# =====================

model_state = {
    "tatr_loaded": False,
    "img2table_ready": False
}


# =====================
# Lifespan
# =====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("=" * 70)
    logger.info("Starting Table Detector API Server...")
    logger.info(f"Port: {API_PORT}")

    # Load models
    try:
        from services.table_detector_service import initialize_models
        model_state["tatr_loaded"], model_state["img2table_ready"] = initialize_models()
        logger.info(f"TATR loaded: {model_state['tatr_loaded']}")
        logger.info(f"img2table ready: {model_state['img2table_ready']}")
    except Exception as e:
        logger.warning(f"Model initialization warning: {e}")
        model_state["img2table_ready"] = True  # img2table doesn't need preloading

    logger.info("Table Detector API Server Ready")
    logger.info("=" * 70)

    yield

    # Shutdown
    logger.info("Shutting down Table Detector API...")


# =====================
# FastAPI App
# =====================

app = FastAPI(
    title="Table Detector API",
    description="테이블 검출 및 구조 추출 API (TATR + img2table)",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(table_router)


# =====================
# Health Endpoints
# =====================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스체크"""
    return HealthResponse(
        status="healthy",
        service="table-detector-api",
        version="1.0.0",
        timestamp=datetime.now().isoformat(),
        models_loaded=model_state.get("img2table_ready", False)
    )


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check_v1():
    """헬스체크 (v1 경로)"""
    return await health_check()


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "Table Detector API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "detect": "/api/v1/detect",
            "extract": "/api/v1/extract",
            "analyze": "/api/v1/analyze",
            "health": "/health"
        }
    }


# =====================
# Main
# =====================

if __name__ == "__main__":
    logger.info(f"Starting Table Detector API on port {API_PORT}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=API_PORT,
        log_level="info"
    )
