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
from services.svg_generator import ocr_to_svg_data
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
    ocr_version = os.getenv("OCR_VERSION", "PP-OCRv4")
    return APIInfoResponse(
        id="paddleocr",
        name="PaddleOCR 3.0 API",
        display_name=f"PaddleOCR {ocr_version}",
        version="3.0.0",
        description=f"{ocr_version}: 106 language support, CPU/GPU compatible",
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
                name="svg_overlay",
                type="string",
                description="SVG overlay for visualization (when include_svg=true)"
            ),
            IOSchema(
                name="processing_time",
                type="float",
                description="Processing time (seconds)"
            )
        ],
        parameters=[
            ParameterSchema(
                name="ocr_version",
                type="select",
                default="PP-OCRv4",
                options=["PP-OCRv4", "PP-OCRv3"],
                description="OCR model version (PP-OCRv4 for CPU compatibility)",
                required=False
            ),
            ParameterSchema(
                name="lang",
                type="select",
                default="en",
                options=["en", "korean", "ch", "japan", "fr", "de", "es", "ru", "ar"],
                description="Recognition language (106 languages available)",
                required=False
            ),
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
                default=0.6,
                description="Box threshold (higher = more accurate boxes)",
                required=False,
                min=0.0,
                max=1.0,
                step=0.05
            ),
            ParameterSchema(
                name="use_textline_orientation",
                type="boolean",
                default=True,
                description="Enable text line orientation classification",
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
            ),
            ParameterSchema(
                name="include_svg",
                type="boolean",
                default=False,
                description="Generate SVG overlay for frontend visualization",
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
            "svg_overlay": "svg_overlay",
            "processing_time": "processing_time"
        }
    )


@router.post("/ocr", response_model=OCRResponse)
async def perform_ocr(
    file: UploadFile = File(..., description="Image file (PNG, JPG, etc.)"),
    det_db_thresh: float = Form(default=0.3, description="Text detection threshold (0-1)"),
    det_db_box_thresh: float = Form(default=0.6, description="Box threshold (0-1)"),
    use_textline_orientation: bool = Form(default=True, description="Enable text line orientation classification"),
    min_confidence: float = Form(default=0.5, description="Minimum confidence filter (0-1)"),
    visualize: bool = Form(default=False, description="Generate OCR result visualization image"),
    include_svg: bool = Form(default=False, description="Generate SVG overlay")
):
    """
    PaddleOCR 3.0 Text Recognition (PP-OCRv5)

    Args:
        file: Image file to analyze
        det_db_thresh: Text detection threshold (lower = more detections)
        det_db_box_thresh: Box threshold (higher = more accurate boxes)
        use_textline_orientation: Enable text line orientation classification
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
        use_textline_orientation = use_textline_orientation if isinstance(use_textline_orientation, bool) else (use_textline_orientation.lower() == 'true' if isinstance(use_textline_orientation, str) else bool(use_textline_orientation))
        visualize = visualize if isinstance(visualize, bool) else (visualize.lower() == 'true' if isinstance(visualize, str) else bool(visualize))
        include_svg = include_svg if isinstance(include_svg, bool) else (include_svg.lower() == 'true' if isinstance(include_svg, str) else bool(include_svg))
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

        # Generate SVG overlay if requested
        svg_overlay = None
        svg_minimal = None
        if include_svg and detections:
            try:
                height, width = img_array.shape[:2]
                image_size = (width, height)

                # Convert detections to dict format for SVG generator
                detection_dicts = []
                for det in detections:
                    if hasattr(det, 'model_dump'):
                        detection_dicts.append(det.model_dump())
                    elif hasattr(det, 'dict'):
                        detection_dicts.append(det.dict())
                    elif isinstance(det, dict):
                        detection_dicts.append(det)

                svg_data = ocr_to_svg_data(detection_dicts, image_size)
                svg_overlay = svg_data["svg"]
                svg_minimal = svg_data["svg_minimal"]
                logger.info(f"SVG overlay generated: {svg_data['detection_count']} detections")
            except Exception as e:
                logger.warning(f"Failed to generate SVG overlay: {e}")

        # Metadata
        metadata = {
            "filename": file.filename,
            "image_size": list(img_array.shape[:2]),
            "parameters": {
                "det_db_thresh": det_db_thresh,
                "det_db_box_thresh": det_db_box_thresh,
                "use_textline_orientation": use_textline_orientation,
                "min_confidence": min_confidence,
                "lang": LANG
            },
            "ocr_version": "PP-OCRv5",
            "api_version": "3.0.0"
        }

        return OCRResponse(
            status="success",
            processing_time=processing_time,
            total_texts=len(detections),
            detections=detections,
            metadata=metadata,
            visualized_image=visualized_image,
            svg_overlay=svg_overlay,
            svg_minimal=svg_minimal
        )

    except Exception as e:
        logger.error(f"OCR processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"OCR processing error: {str(e)}")
