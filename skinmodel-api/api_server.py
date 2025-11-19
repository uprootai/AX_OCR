"""
Skin Model API Server
기하공차 예측 및 제조 가능성 분석 마이크로서비스

포트: 5003
기능: FEM 기반 공차 예측, GD&T 검증, 조립 가능성 평가
"""

import os
import time
import logging
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import models
from models.schemas import (
    HealthResponse,
    ToleranceRequest,
    ToleranceResponse,
    GDTValidateRequest,
    GDTValidateResponse
)

# Import services
from services.tolerance import tolerance_service

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Skin Model API",
    description="Geometric Tolerance Prediction and Manufacturability Analysis Service",
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


# =====================
# API Endpoints
# =====================

@app.get("/", response_model=HealthResponse)
async def root():
    """루트 엔드포인트"""
    return {
        "status": "online",
        "service": "Skin Model API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health", response_model=HealthResponse)
@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint / 헬스체크

    Returns the current health status of the Skin Model API service.
    """
    return {
        "status": "healthy",
        "service": "Skin Model API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v1/tolerance", response_model=ToleranceResponse)
async def predict_tolerance(request: ToleranceRequest):
    """
    기하공차 예측

    - **dimensions**: 치수 정보 리스트
    - **material**: 재질 정보
    - **manufacturing_process**: 제조 공정 (machining, casting, 3d_printing)
    - **correlation_length**: Random Field 상관 길이
    """
    start_time = time.time()

    try:
        # 공차 예측
        prediction_result = tolerance_service.predict_tolerances(
            request.dimensions,
            request.material,
            request.manufacturing_process,
            request.correlation_length
        )

        processing_time = time.time() - start_time

        return {
            "status": "success",
            "data": prediction_result,
            "processing_time": round(processing_time, 2)
        }

    except Exception as e:
        logger.error(f"Error in tolerance prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/validate", response_model=GDTValidateResponse)
async def validate_gdt_specs(request: GDTValidateRequest):
    """
    GD&T 검증

    - **dimensions**: 치수 정보 리스트
    - **gdt_specs**: GD&T 요구사항 (flatness, cylindricity, position 등)
    - **material**: 재질 정보
    """
    start_time = time.time()

    try:
        # GD&T 검증
        validation_result = tolerance_service.validate_gdt(
            request.dimensions,
            request.gdt_specs,
            request.material
        )

        processing_time = time.time() - start_time

        return {
            "status": "success",
            "data": validation_result,
            "processing_time": round(processing_time, 2)
        }

    except Exception as e:
        logger.error(f"Error in GDT validation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/manufacturability")
async def analyze_manufacturability(request: ToleranceRequest):
    """
    제조 가능성 분석

    치수, 공차, 재질 정보를 기반으로 제조 난이도 및 권장사항 제공
    """
    start_time = time.time()

    try:
        # 공차 예측 (제조 가능성 포함)
        result = tolerance_service.predict_tolerances(
            request.dimensions,
            request.material,
            request.manufacturing_process,
            request.correlation_length
        )

        processing_time = time.time() - start_time

        return {
            "status": "success",
            "data": {
                "manufacturability": result["manufacturability"],
                "assemblability": result.get("assemblability", {}),
                "process_parameters": result.get("process_parameters", {})
            },
            "processing_time": round(processing_time, 2)
        }

    except Exception as e:
        logger.error(f"Error in manufacturability analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================
# Main
# =====================

if __name__ == "__main__":
    port = int(os.getenv("SKINMODEL_PORT", 5003))
    workers = int(os.getenv("SKINMODEL_WORKERS", 2))

    logger.info(f"Starting Skin Model API on port {port} with {workers} workers")

    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=port,
        workers=workers,
        log_level="info",
        reload=False
    )
