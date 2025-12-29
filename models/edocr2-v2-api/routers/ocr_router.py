"""
eDOCr2 Router - OCR Processing Endpoints
"""
import os
import time
import json
import shutil
import logging
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from models.schemas import (
    OCRResponse,
    APIInfoResponse, ParameterSchema, IOSchema, BlueprintFlowMetadata
)
from services.ocr_processor import get_processor
from utils.helpers import allowed_file, cleanup_old_files

logger = logging.getLogger(__name__)

# Configuration
UPLOAD_DIR = Path("/tmp/edocr2/uploads")
RESULTS_DIR = Path("/tmp/edocr2/results")
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

router = APIRouter(prefix="/api", tags=["ocr"])


@router.get("/v1/info", response_model=APIInfoResponse)
async def get_api_info():
    """
    API metadata endpoint

    Provides metadata for automatic API registration in BlueprintFlow and Dashboard.
    """
    port = int(os.getenv("EDOCR2_PORT", 5002))
    return APIInfoResponse(
        id="edocr2-v2",
        name="eDOCr2 v2 API",
        display_name="eDOCr2 v2 OCR",
        version="2.0.0",
        description="Engineering Drawing OCR - dimension/GD&T/text extraction API",
        openapi_url="/openapi.json",
        base_url=f"http://localhost:{port}",
        endpoint="/api/v2/ocr",
        method="POST",
        requires_image=True,
        inputs=[
            IOSchema(
                name="file",
                type="file",
                description="Drawing image file (PDF, PNG, JPG, JPEG, TIFF)",
                required=True
            )
        ],
        outputs=[
            IOSchema(
                name="dimensions",
                type="array",
                description="Extracted dimension list"
            ),
            IOSchema(
                name="gdt_symbols",
                type="array",
                description="Extracted GD&T symbol list"
            ),
            IOSchema(
                name="text_blocks",
                type="array",
                description="Extracted text block list"
            ),
            IOSchema(
                name="processing_time",
                type="float",
                description="Processing time (seconds)"
            )
        ],
        parameters=[
            ParameterSchema(
                name="extract_dimensions",
                type="boolean",
                default=True,
                description="Enable dimension extraction",
                required=False
            ),
            ParameterSchema(
                name="extract_gdt",
                type="boolean",
                default=True,
                description="Enable GD&T extraction",
                required=False
            ),
            ParameterSchema(
                name="extract_text",
                type="boolean",
                default=True,
                description="Enable text extraction",
                required=False
            ),
            ParameterSchema(
                name="use_vl_model",
                type="boolean",
                default=False,
                description="Use Vision Language model (more accurate but slower)",
                required=False
            ),
            ParameterSchema(
                name="visualize",
                type="boolean",
                default=False,
                description="Generate visualization image",
                required=False
            ),
            ParameterSchema(
                name="use_gpu_preprocessing",
                type="boolean",
                default=False,
                description="Use GPU preprocessing (CLAHE, denoising)",
                required=False
            )
        ],
        blueprintflow=BlueprintFlowMetadata(
            icon="file-text",
            color="#8b5cf6",
            category="ocr"
        ),
        output_mappings={
            "dimensions": "data.dimensions",
            "gdt_symbols": "data.gdt_symbols",
            "text_blocks": "data.text_blocks",
            "processing_time": "processing_time"
        }
    )


@router.post("/v2/ocr", response_model=OCRResponse)
async def process_drawing(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Drawing file (PDF, PNG, JPG)"),
    extract_dimensions: bool = Form(True, description="Extract dimension information"),
    extract_gdt: bool = Form(True, description="Extract GD&T information"),
    extract_text: bool = Form(True, description="Extract text information"),
    use_vl_model: bool = Form(False, description="Use Vision Language model"),
    visualize: bool = Form(False, description="Generate visualization image"),
    use_gpu_preprocessing: bool = Form(False, description="Use GPU preprocessing")
):
    """
    Process engineering drawing OCR

    - **file**: Drawing file (PDF, PNG, JPG, JPEG, TIFF)
    - **extract_dimensions**: Extract dimension information
    - **extract_gdt**: Extract GD&T information
    - **extract_text**: Extract text information
    - **use_vl_model**: Use Vision Language model (slower but more accurate)
    - **visualize**: Generate visualization image
    - **use_gpu_preprocessing**: Use GPU preprocessing (CLAHE, denoising)
    """
    start_time = time.time()

    # Validate file
    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Allowed: pdf, png, jpg, jpeg, tiff"
        )

    # Check file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )

    # Save file
    file_id = f"{int(time.time())}_{file.filename}"
    file_path = UPLOAD_DIR / file_id

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"File uploaded: {file_id} ({file_size / 1024:.2f} KB)")

        # OCR processing
        processor = get_processor()
        ocr_result = processor.process_ocr(
            file_path,
            extract_dimensions=extract_dimensions,
            extract_gdt=extract_gdt,
            extract_text=extract_text,
            use_vl_model=use_vl_model,
            visualize=visualize,
            use_gpu_preprocessing=use_gpu_preprocessing
        )

        processing_time = time.time() - start_time

        # Background task: cleanup old files
        background_tasks.add_task(cleanup_old_files, UPLOAD_DIR)

        return {
            "status": "success",
            "data": ocr_result,
            "processing_time": round(processing_time, 2),
            "file_id": file_id
        }

    except Exception as e:
        logger.error(f"Error processing file: {e}")
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/v1/result/{file_id}")
async def get_result(file_id: str):
    """Get processing result (for future async processing)"""
    result_path = RESULTS_DIR / f"{file_id}.json"

    if not result_path.exists():
        raise HTTPException(status_code=404, detail="Result not found")

    with open(result_path, 'r') as f:
        result = json.load(f)

    return JSONResponse(content=result)


@router.delete("/v1/cleanup")
async def cleanup_files(max_age_hours: int = 24):
    """Manual file cleanup"""
    try:
        cleanup_old_files(UPLOAD_DIR, max_age_hours)
        cleanup_old_files(RESULTS_DIR, max_age_hours)
        return {"status": "success", "message": f"Cleaned up files older than {max_age_hours} hours"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
