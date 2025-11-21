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
    GDTValidateResponse,
    MaterialInput,
    APIInfoResponse,
    ParameterSchema,
    IOSchema,
    BlueprintFlowMetadata
)

# Import services
from services.tolerance import tolerance_service

# Import utilities
from utils.visualization import create_tolerance_visualization


# =====================
# Helper Functions
# =====================

def get_material_properties(material_name: str) -> MaterialInput:
    """Convert material name string to MaterialInput object with default properties"""
    material_properties = {
        "aluminum": {"youngs_modulus": 69.0, "poisson_ratio": 0.33, "density": 2700.0},
        "steel": {"youngs_modulus": 200.0, "poisson_ratio": 0.30, "density": 7850.0},
        "stainless": {"youngs_modulus": 193.0, "poisson_ratio": 0.31, "density": 8000.0},
        "titanium": {"youngs_modulus": 110.0, "poisson_ratio": 0.34, "density": 4500.0},
        "plastic": {"youngs_modulus": 2.5, "poisson_ratio": 0.40, "density": 1200.0}
    }

    mat_lower = material_name.lower()
    props = material_properties.get(mat_lower, material_properties["steel"])

    # Capitalize for service compatibility
    display_name = material_name.capitalize() if mat_lower != "stainless" else "Stainless Steel"

    return MaterialInput(
        name=display_name,
        youngs_modulus=props["youngs_modulus"],
        poisson_ratio=props["poisson_ratio"],
        density=props["density"]
    )

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


@app.get("/api/v1/info", response_model=APIInfoResponse)
async def get_api_info():
    """
    API 메타데이터 엔드포인트

    BlueprintFlow 및 Dashboard에서 API를 자동으로 등록하기 위한 메타데이터를 제공합니다.
    """
    port = int(os.getenv("SKINMODEL_PORT", 5003))
    return APIInfoResponse(
        id="skinmodel",
        name="SkinModel API",
        display_name="SkinModel 공차 예측",
        version="1.0.0",
        description="FEM 기반 기하공차 예측 및 제조 가능성 분석 API",
        openapi_url="/openapi.json",
        base_url=f"http://localhost:{port}",
        endpoint="/api/v1/tolerance",
        method="POST",
        requires_image=False,
        inputs=[
            IOSchema(
                name="dimensions",
                type="array",
                description="치수 정보 리스트 (type, value, tolerance, unit)",
                required=True
            ),
            IOSchema(
                name="material",
                type="object",
                description="재질 정보 (name, youngs_modulus, poisson_ratio, density) 또는 문자열 (aluminum/steel/stainless/titanium/plastic)",
                required=True
            )
        ],
        outputs=[
            IOSchema(
                name="tolerance_prediction",
                type="object",
                description="예측된 공차 값 (flatness, cylindricity, position, perpendicularity)"
            ),
            IOSchema(
                name="manufacturability",
                type="object",
                description="제조 가능성 평가 (score, difficulty, recommendations)"
            ),
            IOSchema(
                name="assemblability",
                type="object",
                description="조립 가능성 평가 (score, clearance, interference_risk)"
            ),
            IOSchema(
                name="processing_time",
                type="float",
                description="처리 시간 (초)"
            )
        ],
        parameters=[
            ParameterSchema(
                name="manufacturing_process",
                type="select",
                default="machining",
                description="제조 공정 선택",
                required=False,
                options=["machining", "casting", "3d_printing", "welding", "sheet_metal"]
            ),
            ParameterSchema(
                name="correlation_length",
                type="number",
                default=1.0,
                description="Random Field 상관 길이 (표면 거칠기 영향)",
                required=False,
                min=0.1,
                max=10.0,
                step=0.1
            ),
            ParameterSchema(
                name="task",
                type="select",
                default="tolerance",
                description="분석 작업 선택",
                required=False,
                options=["tolerance", "validate", "manufacturability"]
            )
        ],
        blueprintflow=BlueprintFlowMetadata(
            icon="📐",
            color="#ef4444",
            category="prediction"
        ),
        output_mappings={
            "tolerance_prediction": "data.tolerance_prediction",
            "manufacturability": "data.manufacturability",
            "assemblability": "data.assemblability",
            "processing_time": "processing_time"
        }
    )


@app.post("/api/v1/tolerance", response_model=ToleranceResponse)
async def predict_tolerance(request: ToleranceRequest):
    """
    기하공차 예측 (통합 엔드포인트)

    - **dimensions**: 치수 정보 리스트
    - **material**: 재질 정보 (MaterialInput object or string: aluminum/steel/stainless/titanium/plastic)
    - **manufacturing_process**: 제조 공정 (machining, casting, 3d_printing, welding, sheet_metal)
    - **correlation_length**: Random Field 상관 길이
    - **task**: 분석 작업 (tolerance, validate, manufacturability)
    """
    start_time = time.time()

    try:
        # Convert material string to MaterialInput if needed
        material = request.material
        if isinstance(material, str):
            material = get_material_properties(material)
            logger.info(f"Converted material string '{request.material}' to MaterialInput")

        # Route based on task parameter
        task = request.task or "tolerance"

        if task == "tolerance":
            # 공차 예측
            result = tolerance_service.predict_tolerances(
                request.dimensions,
                material,
                request.manufacturing_process,
                request.correlation_length
            )

            # 시각화 생성
            try:
                visualized_image = create_tolerance_visualization(result)
                if visualized_image:
                    result["visualized_image"] = visualized_image
                    logger.info("✅ Tolerance visualization created")
            except Exception as e:
                logger.warning(f"⚠️ Visualization creation failed: {e}")

        elif task == "validate":
            # GD&T 검증 (기본 스펙 사용)
            default_gdt_specs = {"flatness": 0.05, "cylindricity": 0.05, "position": 0.05}
            result = tolerance_service.validate_gdt(
                request.dimensions,
                default_gdt_specs,
                material
            )

        elif task == "manufacturability":
            # 제조 가능성 분석
            full_result = tolerance_service.predict_tolerances(
                request.dimensions,
                material,
                request.manufacturing_process,
                request.correlation_length
            )
            result = {
                "manufacturability": full_result["manufacturability"],
                "assemblability": full_result.get("assemblability", {}),
                "process_parameters": full_result.get("process_parameters", {})
            }

        else:
            raise HTTPException(status_code=400, detail=f"Invalid task: {task}")

        processing_time = time.time() - start_time

        return {
            "status": "success",
            "data": result,
            "processing_time": round(processing_time, 2)
        }

    except Exception as e:
        logger.error(f"Error in tolerance analysis: {e}")
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
