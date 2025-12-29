"""
Line Detector API Server
P&ID 라인(배관/신호선) 검출 및 연결성 분석 API

기술:
- OpenCV Line Segment Detector (LSD)
- Hough Line Transform
- Line Thinning (Zhang-Suen Algorithm)
- Line Type Classification

포트: 5016

라우터 구조:
- /api/v1/process, /api/v1/info: process_router
"""

import os
import logging
from datetime import datetime
from typing import Tuple
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Routers
from routers import process_router

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_PORT = int(os.getenv("LINE_DETECTOR_PORT", "5016"))


# =====================
# Schemas
# =====================

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str


class LineSegment(BaseModel):
    id: int
    start_point: Tuple[float, float]
    end_point: Tuple[float, float]
    length: float
    angle: float
    line_type: str
    confidence: float


# =====================
# Lifespan
# =====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("=" * 70)
    logger.info("🚀 Line Detector API Server Starting...")
    logger.info(f"Port: {API_PORT}")
    logger.info("=" * 70)

    yield

    # Shutdown
    logger.info("👋 Shutting down Line Detector API...")


# =====================
# FastAPI App
# =====================

app = FastAPI(
    title="Line Detector API",
    description="P&ID 라인(배관/신호선) 검출 및 연결성 분석 API",
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
app.include_router(process_router)


# =====================
# Health Endpoints
# =====================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스체크"""
    return HealthResponse(
        status="healthy",
        service="line-detector-api",
        version="1.0.0",
        timestamp=datetime.now().isoformat()
    )


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check_v1():
    """헬스체크 (v1 경로)"""
    return await health_check()


# =====================
# Main
# =====================

if __name__ == "__main__":
    logger.info(f"Starting Line Detector API on port {API_PORT}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=API_PORT,
        log_level="info"
    )
