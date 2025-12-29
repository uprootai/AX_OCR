"""
SkinModel Tolerance Router - Tolerance Analysis Endpoints
"""
import os
import time
import logging
from typing import Union

from fastapi import APIRouter, HTTPException

# Import models
from models.schemas import (
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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["tolerance"])


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


# =====================
# Endpoints
# =====================

@router.get("/info", response_model=APIInfoResponse)
async def get_api_info():
    """
    API metadata endpoint

    Provides metadata for automatic API registration in BlueprintFlow and Dashboard.
    """
    port = int(os.getenv("SKINMODEL_PORT", 5003))
    return APIInfoResponse(
        id="skinmodel",
        name="SkinModel API",
        display_name="SkinModel Tolerance Prediction",
        version="1.0.0",
        description="FEM-based geometric tolerance prediction and manufacturability analysis API",
        openapi_url="/openapi.json",
        base_url=f"http://localhost:{port}",
        endpoint="/api/v1/tolerance",
        method="POST",
        requires_image=False,
        inputs=[
            IOSchema(
                name="dimensions",
                type="array",
                description="Dimension info list (type, value, tolerance, unit)",
                required=True
            ),
            IOSchema(
                name="material",
                type="object",
                description="Material info (name, youngs_modulus, poisson_ratio, density) or string (aluminum/steel/stainless/titanium/plastic)",
                required=True
            )
        ],
        outputs=[
            IOSchema(
                name="tolerance_prediction",
                type="object",
                description="Predicted tolerance values (flatness, cylindricity, position, perpendicularity)"
            ),
            IOSchema(
                name="manufacturability",
                type="object",
                description="Manufacturability assessment (score, difficulty, recommendations)"
            ),
            IOSchema(
                name="assemblability",
                type="object",
                description="Assemblability assessment (score, clearance, interference_risk)"
            ),
            IOSchema(
                name="processing_time",
                type="float",
                description="Processing time (seconds)"
            )
        ],
        parameters=[
            ParameterSchema(
                name="manufacturing_process",
                type="select",
                default="machining",
                description="Manufacturing process selection",
                required=False,
                options=["machining", "casting", "3d_printing", "welding", "sheet_metal"]
            ),
            ParameterSchema(
                name="correlation_length",
                type="number",
                default=1.0,
                description="Random Field correlation length (surface roughness effect)",
                required=False,
                min=0.1,
                max=10.0,
                step=0.1
            ),
            ParameterSchema(
                name="task",
                type="select",
                default="tolerance",
                description="Analysis task selection",
                required=False,
                options=["tolerance", "validate", "manufacturability"]
            )
        ],
        blueprintflow=BlueprintFlowMetadata(
            icon="square-ruler",
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


@router.post("/tolerance", response_model=ToleranceResponse)
async def predict_tolerance(request: ToleranceRequest):
    """
    Geometric Tolerance Prediction (Unified Endpoint)

    - **dimensions**: Dimension info list
    - **material**: Material info (MaterialInput object or string: aluminum/steel/stainless/titanium/plastic)
    - **manufacturing_process**: Manufacturing process (machining, casting, 3d_printing, welding, sheet_metal)
    - **correlation_length**: Random Field correlation length
    - **task**: Analysis task (tolerance, validate, manufacturability)
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
            # Tolerance prediction
            result = tolerance_service.predict_tolerances(
                request.dimensions,
                material,
                request.manufacturing_process,
                request.correlation_length
            )

            # Create visualization
            try:
                visualized_image = create_tolerance_visualization(result)
                if visualized_image:
                    result["visualized_image"] = visualized_image
                    logger.info("Tolerance visualization created")
            except Exception as e:
                logger.warning(f"Visualization creation failed: {e}")

        elif task == "validate":
            # GD&T validation (using default specs)
            default_gdt_specs = {"flatness": 0.05, "cylindricity": 0.05, "position": 0.05}
            result = tolerance_service.validate_gdt(
                request.dimensions,
                default_gdt_specs,
                material
            )

        elif task == "manufacturability":
            # Manufacturability analysis
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


@router.post("/validate", response_model=GDTValidateResponse)
async def validate_gdt_specs(request: GDTValidateRequest):
    """
    GD&T Validation

    - **dimensions**: Dimension info list
    - **gdt_specs**: GD&T requirements (flatness, cylindricity, position, etc.)
    - **material**: Material info
    """
    start_time = time.time()

    try:
        # GD&T validation
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


@router.post("/manufacturability")
async def analyze_manufacturability(request: ToleranceRequest):
    """
    Manufacturability Analysis

    Provides manufacturing difficulty and recommendations based on dimensions, tolerances, and material.
    """
    start_time = time.time()

    try:
        # Convert material if needed
        material = request.material
        if isinstance(material, str):
            material = get_material_properties(material)

        # Tolerance prediction (includes manufacturability)
        result = tolerance_service.predict_tolerances(
            request.dimensions,
            material,
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
