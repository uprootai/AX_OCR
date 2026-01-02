"""
PID Composer API Server
P&ID 도면 레이어 합성 및 시각화 API

Features:
- 심볼, 라인, 텍스트, 영역 레이어 합성
- SVG 오버레이 생성 (프론트엔드용)
- 이미지 렌더링 (서버 사이드)
- 스타일 커스터마이징

Port: 5021
"""

import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from routers import compose_router

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_PORT = int(os.getenv("PID_COMPOSER_PORT", "5021"))


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
    logger.info("🎨 PID Composer API Server Starting...")
    logger.info(f"Port: {API_PORT}")
    logger.info("=" * 70)

    yield

    # Shutdown
    logger.info("👋 Shutting down PID Composer API...")


# =====================
# FastAPI App
# =====================

app = FastAPI(
    title="PID Composer API",
    description="P&ID 도면 레이어 합성 및 시각화 API - 심볼, 라인, 텍스트, 영역 통합 렌더링",
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
app.include_router(compose_router)


# =====================
# Health Endpoints
# =====================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스체크"""
    return HealthResponse(
        status="healthy",
        service="pid-composer-api",
        version="1.0.0",
        timestamp=datetime.now().isoformat()
    )


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check_v1():
    """헬스체크 (v1 경로)"""
    return await health_check()


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "PID Composer API",
        "version": "1.0.0",
        "description": "P&ID 도면 레이어 합성 및 시각화",
        "endpoints": {
            "health": "/health",
            "info": "/api/v1/info",
            "compose": "/api/v1/compose",
            "compose_layers": "/api/v1/compose/layers",
            "docs": "/docs"
        }
    }


# =====================
# Main
# =====================

if __name__ == "__main__":
    logger.info(f"Starting PID Composer API on port {API_PORT}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=API_PORT,
        log_level="info"
    )
