"""
eDOCr v1 OCR Router
OCR 관련 API 엔드포인트
"""

import os
import time
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from ..utils import UPLOAD_DIR, RESULTS_DIR, ALLOWED_EXTENSIONS
from ..services.ocr_service import ocr_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["OCR"])


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "eDOCr v1 API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "edocr_available": ocr_service.edocr_available,
        "models_loaded": ocr_service.models_loaded if ocr_service.edocr_available else False
    }


@router.post("/ocr")
async def process_drawing(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Drawing file (PDF, PNG, JPG)"),
    extract_dimensions: bool = Form(True, description="Extract dimension info"),
    extract_gdt: bool = Form(True, description="Extract GD&T info"),
    extract_text: bool = Form(True, description="Extract text info"),
    visualize: bool = Form(False, description="Generate visualization"),
    remove_watermark: bool = Form(False, description="Remove watermark"),
    cluster_threshold: int = Form(20, description="Dimension clustering threshold")
):
    """
    Process drawing OCR (eDOCr v1)

    - **file**: Drawing file (PDF, PNG, JPG)
    - **extract_dimensions**: Extract dimension information
    - **extract_gdt**: Extract GD&T information
    - **extract_text**: Extract text information
    - **visualize**: Generate visualization image
    - **remove_watermark**: Remove watermark
    - **cluster_threshold**: Dimension clustering threshold (px)
    """
    start_time = time.time()

    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    file_ext = file.filename.rsplit('.', 1)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed: {ALLOWED_EXTENSIONS}"
        )

    # Save uploaded file
    file_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    file_path = UPLOAD_DIR / file_id

    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        logger.info(f"File saved: {file_path}")

        # Process OCR
        result = ocr_service.process_ocr(
            file_path,
            extract_dimensions=extract_dimensions,
            extract_gdt=extract_gdt,
            extract_text=extract_text,
            visualize=visualize,
            remove_watermark=remove_watermark,
            cluster_threshold=cluster_threshold
        )

        processing_time = time.time() - start_time

        # Cleanup in background
        background_tasks.add_task(lambda: file_path.unlink(missing_ok=True))

        return {
            "status": "success",
            "data": result,
            "processing_time": processing_time,
            "file_id": file_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/visualization/{filename}")
async def get_visualization(filename: str):
    """Return visualization image"""
    file_path = RESULTS_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Visualization not found")

    return FileResponse(file_path)


@router.post("/ocr/enhanced")
async def ocr_enhanced(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    extract_dimensions: bool = Form(True),
    extract_gdt: bool = Form(True),
    extract_text: bool = Form(False),
    visualize: bool = Form(False),
    remove_watermark: bool = Form(False),
    cluster_threshold: int = Form(20),
    strategy: str = Form("edgnet"),
    vl_provider: str = Form("openai")
):
    """
    Enhanced OCR with performance improvement strategies

    **Strategies**:
    - `basic`: Original eDOCr (baseline) - 50% dimension, 0% GD&T
    - `edgnet`: EDGNet-enhanced - 60% dimension, 50% GD&T
    - `vl`: VL-powered - 85% dimension, 75% GD&T
    - `hybrid`: EDGNet + VL - 90% dimension, 80% GD&T
    """
    try:
        start_time = time.time()
        logger.info(f"Enhanced OCR: strategy={strategy}, provider={vl_provider}")

        # Save uploaded file
        file_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        file_path = UPLOAD_DIR / file_id

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Run standard OCR
        ocr_result = ocr_service.process_ocr(
            file_path,
            extract_dimensions=extract_dimensions,
            extract_gdt=extract_gdt,
            extract_text=extract_text,
            visualize=visualize,
            remove_watermark=remove_watermark,
            cluster_threshold=cluster_threshold
        )

        # Basic strategy: return as-is
        if strategy == 'basic':
            processing_time = time.time() - start_time
            background_tasks.add_task(lambda: file_path.unlink(missing_ok=True))

            return {
                "status": "success",
                "data": ocr_result,
                "processing_time": processing_time,
                "file_id": file_id,
                "enhancement": {
                    "strategy": "basic",
                    "description": "Original eDOCr",
                    "enhancements_applied": ["none"]
                }
            }

        # Enhanced strategies - import enhancers
        try:
            import cv2
            import numpy as np
            from enhancers import EnhancedOCRPipeline

            pipeline = EnhancedOCRPipeline(
                edgnet_url=os.getenv("EDGNET_URL", "http://edgnet-api:5002"),
                vl_provider=vl_provider,
                vl_api_key=os.getenv(f"{vl_provider.upper()}_API_KEY")
            )

            # Load image
            if file_path.suffix.lower() == '.pdf':
                from pdf2image import convert_from_path
                images = convert_from_path(str(file_path))
                img = np.array(images[0])
            else:
                img = cv2.imread(str(file_path))

            # Run enhancement
            enhancement_result = pipeline.run(
                strategy=strategy,
                image_path=file_path,
                img=img,
                original_gdt_boxes=[],
                original_gdt=ocr_result.get('gdt', [])
            )

            # Merge results
            ocr_result['gdt'] = enhancement_result['enhanced_gdt']

            processing_time = time.time() - start_time
            background_tasks.add_task(lambda: file_path.unlink(missing_ok=True))

            return {
                "status": "success",
                "data": ocr_result,
                "processing_time": processing_time,
                "file_id": file_id,
                "enhancement": {
                    "strategy": enhancement_result['strategy'],
                    "description": enhancement_result['description'],
                    "enhancements_applied": enhancement_result['enhancements_applied'],
                    "stats": enhancement_result['stats'],
                    "enhancement_time": enhancement_result['processing_time']
                }
            }

        except ImportError as e:
            logger.warning(f"Enhancers not available: {e}, falling back to basic")
            processing_time = time.time() - start_time
            background_tasks.add_task(lambda: file_path.unlink(missing_ok=True))

            return {
                "status": "success",
                "data": ocr_result,
                "processing_time": processing_time,
                "file_id": file_id,
                "enhancement": {
                    "strategy": "basic",
                    "description": "Enhancers not available, using basic",
                    "enhancements_applied": ["none"]
                }
            }

    except Exception as e:
        logger.error(f"Enhanced OCR failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
