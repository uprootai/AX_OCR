"""
PaddleOCR Router - OCR Processing Endpoints
"""
import os
import time
import logging

from fastapi import APIRouter, File, UploadFile, HTTPException, Form

from models.schemas import (
    OCRResponse,
    APIInfoResponse, ParameterSchema, IOSchema, BlueprintFlowMetadata
)
from services.ocr import get_ocr_service
from utils.helpers import image_to_numpy, draw_ocr_results

logger = logging.getLogger(__name__)

PORT = int(os.getenv("PADDLEOCR_PORT", "5006"))
LANG = os.getenv("OCR_LANG", "en")

router = APIRouter(prefix="/api/v1", tags=["ocr"])


@router.get("/info", response_model=APIInfoResponse)
async def get_api_info():
    """
    API metadata endpoint

    Provides metadata for automatic API registration in BlueprintFlow and Dashboard.
    """
    return APIInfoResponse(
        id="paddleocr",
        name="PaddleOCR API",
        display_name="PaddleOCR Text Recognition",
        version="1.0.0",
        description="PaddlePaddle based drawing text recognition API",
        openapi_url="/openapi.json",
        base_url=f"http://localhost:{PORT}",
        endpoint="/api/v1/ocr",
        method="POST",
        requires_image=True,
        inputs=[
            IOSchema(
                name="file",
                type="file",
                description="Drawing image file",
                required=True
            )
        ],
        outputs=[
            IOSchema(
                name="detections",
                type="array",
                description="Detected text list (each text includes text, confidence, bbox, position)"
            ),
            IOSchema(
                name="total_texts",
                type="integer",
                description="Total detected text count"
            ),
            IOSchema(
                name="processing_time",
                type="float",
                description="Processing time (seconds)"
            )
        ],
        parameters=[
            ParameterSchema(
                name="det_db_thresh",
                type="number",
                default=0.3,
                description="Text detection threshold (lower = more detections)",
                required=False,
                min=0.0,
                max=1.0,
                step=0.05
            ),
            ParameterSchema(
                name="det_db_box_thresh",
                type="number",
                default=0.5,
                description="Box threshold (higher = more accurate boxes)",
                required=False,
                min=0.0,
                max=1.0,
                step=0.05
            ),
            ParameterSchema(
                name="use_angle_cls",
                type="boolean",
                default=True,
                description="Enable rotated text detection",
                required=False
            ),
            ParameterSchema(
                name="min_confidence",
                type="number",
                default=0.5,
                description="Minimum confidence filter",
                required=False,
                min=0.0,
                max=1.0,
                step=0.05
            ),
            ParameterSchema(
                name="visualize",
                type="boolean",
                default=False,
                description="Generate OCR result visualization image",
                required=False
            )
        ],
        blueprintflow=BlueprintFlowMetadata(
            icon="file-text",
            color="#10b981",
            category="ocr"
        ),
        output_mappings={
            "detections": "detections",
            "total_texts": "total_texts",
            "processing_time": "processing_time"
        }
    )


@router.post("/ocr", response_model=OCRResponse)
async def perform_ocr(
    file: UploadFile = File(..., description="Image file (PNG, JPG, etc.)"),
    det_db_thresh: float = Form(default=0.3, description="Text detection threshold (0-1)"),
    det_db_box_thresh: float = Form(default=0.5, description="Box threshold (0-1)"),
    use_angle_cls: bool = Form(default=True, description="Enable rotated text detection"),
    min_confidence: float = Form(default=0.5, description="Minimum confidence filter (0-1)"),
    visualize: bool = Form(default=False, description="Generate OCR result visualization image")
):
    """
    PaddleOCR Text Recognition

    Args:
        file: Image file to analyze
        det_db_thresh: Text detection threshold (lower = more detections)
        det_db_box_thresh: Box threshold (higher = more accurate boxes)
        use_angle_cls: Enable rotated text detection
        min_confidence: Minimum confidence filter

    Returns:
        OCRResponse with detection results
    """
    start_time = time.time()

    ocr_service = get_ocr_service()
    if ocr_service is None or ocr_service.model is None:
        raise HTTPException(status_code=503, detail="PaddleOCR model not loaded")

    # Form parameter type conversion
    try:
        min_confidence = float(min_confidence) if isinstance(min_confidence, str) else min_confidence
        det_db_thresh = float(det_db_thresh) if isinstance(det_db_thresh, str) else det_db_thresh
        det_db_box_thresh = float(det_db_box_thresh) if isinstance(det_db_box_thresh, str) else det_db_box_thresh
        use_angle_cls = use_angle_cls if isinstance(use_angle_cls, bool) else (use_angle_cls.lower() == 'true' if isinstance(use_angle_cls, str) else bool(use_angle_cls))
        visualize = visualize if isinstance(visualize, bool) else (visualize.lower() == 'true' if isinstance(visualize, str) else bool(visualize))
    except (ValueError, AttributeError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameter type: {e}")

    try:
        # Read image
        image_bytes = await file.read()
        logger.info(f"Processing image: {file.filename}, size: {len(image_bytes)} bytes")

        # Convert to numpy array
        img_array = image_to_numpy(image_bytes)
        logger.info(f"Image shape: {img_array.shape}")

        # Run PaddleOCR inference
        detections = ocr_service.predict(img_array, min_confidence=min_confidence)

        processing_time = time.time() - start_time

        logger.info(f"OCR completed: {len(detections)} texts detected in {processing_time:.2f}s")

        # Generate visualization if requested
        visualized_image = None
        if visualize and detections:
            visualized_image = draw_ocr_results(img_array, detections)
            logger.info("Visualization image generated")

        # Metadata
        metadata = {
            "filename": file.filename,
            "image_size": list(img_array.shape[:2]),
            "parameters": {
                "det_db_thresh": det_db_thresh,
                "det_db_box_thresh": det_db_box_thresh,
                "use_angle_cls": use_angle_cls,
                "min_confidence": min_confidence,
                "lang": LANG
            }
        }

        return OCRResponse(
            status="success",
            processing_time=processing_time,
            total_texts=len(detections),
            detections=detections,
            metadata=metadata,
            visualized_image=visualized_image
        )

    except Exception as e:
        logger.error(f"OCR processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"OCR processing error: {str(e)}")
