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

라우터 구조:
- /api/v1/analyze, /api/v1/process: analysis_router
- /api/v1/bwms/*: bwms_router
- /api/v1/equipment/*: equipment_router
- /api/v1/region-*, /api/v1/valve-signal/*: region_router
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
from routers import (
    analysis_router,
    bwms_router,
    equipment_router,
    region_router,
    dwg_router,
)

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


# =====================
# Lifespan
# =====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("=" * 70)
    logger.info("🚀 P&ID Analyzer API Server Starting...")
    logger.info(f"Port: {API_PORT}")
    logger.info("=" * 70)

    yield

    # Shutdown
    logger.info("👋 Shutting down P&ID Analyzer API...")


# =====================
# FastAPI App
# =====================

app = FastAPI(
    title="P&ID Analyzer API",
    description="P&ID 연결성 분석 및 BOM 추출 API",
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
app.include_router(analysis_router)
app.include_router(bwms_router)
app.include_router(equipment_router)
app.include_router(region_router)
app.include_router(dwg_router)


# =====================
# Health Endpoints
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
