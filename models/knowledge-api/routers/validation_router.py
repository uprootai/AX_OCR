"""
Validation Router - ISO/ASME Standard Validation Endpoints
"""
import logging

from fastapi import APIRouter, HTTPException

from models.schemas import (
    StandardValidationRequest, StandardValidationResponse
)
from services.state import get_standard_validator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/validate", tags=["validation"])


@router.post("/standard", response_model=StandardValidationResponse)
async def validate_standard(request: StandardValidationRequest):
    """
    ISO/ASME standard validation

    - ISO 1101 GD&T validation
    - ASME Y14.5 validation
    - Thread specification validation
    - Surface finish validation
    """
    standard_validator = get_standard_validator()
    if not standard_validator:
        raise HTTPException(status_code=503, detail="Standard validator unavailable")

    try:
        validation_result = await standard_validator.validate(
            dimension=request.dimension,
            tolerance=request.tolerance,
            gdt_symbol=request.gdt_symbol,
            surface_finish=request.surface_finish,
            thread_spec=request.thread_spec
        )

        return StandardValidationResponse(
            status="success",
            is_valid=validation_result["is_valid"],
            errors=validation_result.get("errors", []),
            warnings=validation_result.get("warnings", []),
            suggestions=validation_result.get("suggestions", []),
            matched_standards=validation_result.get("matched_standards", [])
        )
    except Exception as e:
        logger.error(f"Standard validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
