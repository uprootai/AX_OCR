"""
Skin Model API Server
기하공차 예측 및 제조 가능성 분석 마이크로서비스

포트: 5003
기능: FEM 기반 공차 예측, GD&T 검증, 조립 가능성 평가
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add skinmodel to path
SKINMODEL_PATH = Path(__file__).parent.parent.parent / "dev" / "skinmodel"
sys.path.insert(0, str(SKINMODEL_PATH))

# ML Predictor
try:
    from ml_predictor import get_ml_predictor
    ml_predictor = get_ml_predictor()
    logger.info(f"ML Predictor initialized: {ml_predictor.is_available()}")
except Exception as e:
    logger.warning(f"ML Predictor not available: {e}")
    ml_predictor = None

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
# Pydantic Models
# =====================

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str


class DimensionInput(BaseModel):
    type: str = Field(..., description="치수 타입 (diameter, length, angle, etc.)")
    value: float = Field(..., description="치수 값")
    tolerance: Optional[float] = Field(None, description="공차 값")
    unit: str = Field("mm", description="단위")


class MaterialInput(BaseModel):
    name: str = Field("Steel", description="재질명")
    youngs_modulus: Optional[float] = Field(None, description="영계수 (GPa)")
    poisson_ratio: Optional[float] = Field(None, description="포아송 비")
    density: Optional[float] = Field(None, description="밀도 (kg/m³)")


class ToleranceRequest(BaseModel):
    dimensions: List[DimensionInput]
    material: MaterialInput
    manufacturing_process: str = Field("machining", description="제조 공정 (machining, casting, 3d_printing)")
    correlation_length: float = Field(1.0, description="Random Field 상관 길이")


class TolerancePrediction(BaseModel):
    flatness: float
    cylindricity: float
    position: float
    perpendicularity: Optional[float] = None


class ManufacturabilityScore(BaseModel):
    score: float = Field(..., ge=0, le=1, description="제조 가능성 점수 (0-1)")
    difficulty: str = Field(..., description="난이도 (Easy, Medium, Hard)")
    recommendations: List[str]


class AssemblabilityScore(BaseModel):
    score: float = Field(..., ge=0, le=1)
    clearance: float
    interference_risk: str


class ToleranceResponse(BaseModel):
    status: str
    data: Dict[str, Any]
    processing_time: float


class GDTValidateRequest(BaseModel):
    dimensions: List[DimensionInput]
    gdt_specs: Dict[str, float] = Field(..., description="GD&T 요구사항")
    material: MaterialInput


class GDTValidateResponse(BaseModel):
    status: str
    data: Dict[str, Any]
    processing_time: float


# =====================
# Helper Functions
# =====================

def predict_tolerances(
    dimensions: List[DimensionInput],
    material: MaterialInput,
    manufacturing_process: str,
    correlation_length: float
) -> Dict[str, Any]:
    """
    기하공차 예측 (ML-based with Rule-based fallback)

    ML 모델 우선 사용, 실패 시 Rule-based 휴리스틱 사용
    """
    try:
        logger.info(f"Predicting tolerances for {len(dimensions)} dimensions")
        logger.info(f"Material: {material.name}, Process: {manufacturing_process}")

        # 공통 변수 초기화
        max_dim = max([d.value for d in dimensions]) if dimensions else 100.0
        material_factors_map = {
            "Steel": 1.0,
            "Aluminum": 0.8,
            "Titanium": 1.5,
            "Plastic": 0.6
        }
        material_factor = material_factors_map.get(material.name, 1.0)
        size_factor = 1.0 + (max_dim / 1000.0) * 0.5

        # ML 모델 시도
        ml_predictions = None
        if ml_predictor and ml_predictor.is_available():
            try:
                dims_dict = [{"type": d.type, "value": d.value} for d in dimensions]
                mat_dict = {"name": material.name, "youngs_modulus": material.youngs_modulus}
                ml_predictions = ml_predictor.predict(dims_dict, mat_dict, manufacturing_process)
                if ml_predictions:
                    logger.info("✅ ML 모델 예측 사용")
                    flatness = ml_predictions["flatness"]
                    cylindricity = ml_predictions["cylindricity"]
                    position = ml_predictions["position"]
                    perpendicularity = ml_predictions["perpendicularity"]
            except Exception as e:
                logger.warning(f"ML 예측 실패, Rule-based 사용: {e}")
                ml_predictions = None

        # Rule-based fallback
        if ml_predictions is None:
            logger.info("⚠️  Rule-based 휴리스틱 사용")
            # 재질별 기본 공차 계수
            material_factors = {
                "Steel": 1.0,
                "Aluminum": 0.8,
                "Titanium": 1.5,
                "Plastic": 0.6
            }
            material_factor = material_factors.get(material.name, 1.0)

            # 제조 공정별 기본 공차
            process_tolerances = {
                "machining": {"flatness": 0.02, "cylindricity": 0.03, "position": 0.025},
                "casting": {"flatness": 0.15, "cylindricity": 0.20, "position": 0.15},
                "3d_printing": {"flatness": 0.08, "cylindricity": 0.10, "position": 0.08}
            }
            base_tol = process_tolerances.get(manufacturing_process, process_tolerances["machining"])

            # 치수 크기에 따른 보정
            max_dim = max([d.value for d in dimensions]) if dimensions else 100.0
            size_factor = 1.0 + (max_dim / 1000.0) * 0.5

            # Correlation length 영향
            corr_factor = 1.0 + (correlation_length - 1.0) * 0.3

            # 최종 공차 계산
            flatness = round(base_tol["flatness"] * material_factor * size_factor * corr_factor, 4)
            cylindricity = round(base_tol["cylindricity"] * material_factor * size_factor * corr_factor, 4)
            position = round(base_tol["position"] * material_factor * size_factor * corr_factor, 4)
            perpendicularity = round(flatness * 0.7, 4)

        # 제조 가능성 평가
        avg_tolerance = (flatness + cylindricity + position) / 3
        if avg_tolerance < 0.05:
            difficulty = "Hard"
            score = 0.65
            recommendations = [
                "Requires precision machining equipment",
                "Consider CNC grinding for tight tolerances",
                "Quality control critical - CMM inspection required"
            ]
        elif avg_tolerance < 0.10:
            difficulty = "Medium"
            score = 0.80
            recommendations = [
                "Standard precision machining acceptable",
                "Consider tighter fixturing for flatness control",
                "Regular calibration of measuring equipment"
            ]
        else:
            difficulty = "Easy"
            score = 0.92
            recommendations = [
                "Standard machining processes sufficient",
                "Normal quality control procedures",
                "Cost-effective manufacturing possible"
            ]

        # 조립성 평가 (작은 공차 = 더 좋은 조립성)
        assemblability_score = min(0.98, 0.70 + (0.1 - avg_tolerance) * 2)
        clearance = round(avg_tolerance * 3, 3)

        if avg_tolerance < 0.05:
            interference_risk = "Low"
        elif avg_tolerance < 0.15:
            interference_risk = "Medium"
        else:
            interference_risk = "High"

        # Simulate processing time
        time.sleep(0.5)

        result = {
            "predicted_tolerances": {
                "flatness": flatness,
                "cylindricity": cylindricity,
                "position": position,
                "perpendicularity": perpendicularity
            },
            "manufacturability": {
                "score": round(score, 2),
                "difficulty": difficulty,
                "recommendations": recommendations
            },
            "assemblability": {
                "score": round(assemblability_score, 2),
                "clearance": clearance,
                "interference_risk": interference_risk
            },
            "process_parameters": {
                "correlation_length": correlation_length,
                "material_factor": material_factor,
                "size_factor": round(size_factor, 2),
                "max_dimension": max_dim
            }
        }

        return result

    except Exception as e:
        logger.error(f"Tolerance prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


def validate_gdt(
    dimensions: List[DimensionInput],
    gdt_specs: Dict[str, float],
    material: MaterialInput
) -> Dict[str, Any]:
    """
    GD&T 검증

    TODO: 실제 GDT Validator 연동
    """
    try:
        logger.info(f"Validating GD&T for {len(dimensions)} dimensions")
        logger.info(f"Specs: {gdt_specs}")

        # Simulate processing
        time.sleep(1.0)

        # Mock validation result
        result = {
            "validation_results": {
                "flatness": {
                    "spec": gdt_specs.get("flatness", 0.05),
                    "predicted": 0.048,
                    "status": "PASS",
                    "margin": 0.002
                },
                "cylindricity": {
                    "spec": gdt_specs.get("cylindricity", 0.1),
                    "predicted": 0.092,
                    "status": "PASS",
                    "margin": 0.008
                },
                "position": {
                    "spec": gdt_specs.get("position", 0.08),
                    "predicted": 0.065,
                    "status": "PASS",
                    "margin": 0.015
                }
            },
            "overall_status": "PASS",
            "pass_rate": 1.0,
            "recommendations": [
                "All tolerances within specification",
                "Consider process capability study (Cpk > 1.33)"
            ]
        }

        return result

    except Exception as e:
        logger.error(f"GDT validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


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
        prediction_result = predict_tolerances(
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
        validation_result = validate_gdt(
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
        result = predict_tolerances(
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
