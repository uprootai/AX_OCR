#!/usr/bin/env python3
"""
YOLOv11 API Server for Engineering Drawing Analysis
Port: 5005
"""
import os
import time
import json
import uuid
import base64
from pathlib import Path
from typing import Optional

import cv2
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import torch

from models.schemas import Detection, DetectionResponse, HealthResponse
from services.inference import YOLOInferenceService
from utils.helpers import draw_detections_on_image

# =====================
# Configuration
# =====================

YOLO_API_PORT = int(os.getenv('YOLO_API_PORT', '5005'))
YOLO_MODEL_PATH = os.getenv('YOLO_MODEL_PATH', '/app/models/best.pt')
UPLOAD_DIR = Path('/tmp/yolo-api/uploads')
RESULTS_DIR = Path('/tmp/yolo-api/results')

# Create directories
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# =====================
# FastAPI App
# =====================

app = FastAPI(
    title="YOLOv11 Drawing Analysis API",
    description="Engineering drawing dimension/GD&T extraction API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global inference service
inference_service: Optional[YOLOInferenceService] = None


# =====================
# Startup / Shutdown
# =====================

@app.on_event("startup")
async def startup_event():
    """Load model on startup"""
    global inference_service

    print("=" * 70)
    print("🚀 YOLOv11 API Server Starting...")
    print("=" * 70)

    inference_service = YOLOInferenceService(YOLO_MODEL_PATH)
    inference_service.load_model()

    print("=" * 70)
    print(f"✅ Server ready on port {YOLO_API_PORT}")
    print("=" * 70)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🛑 Shutting down YOLOv11 API Server...")


# =====================
# API Endpoints
# =====================

@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    gpu_name = None
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)

    return HealthResponse(
        status="healthy",
        model_loaded=inference_service is not None and inference_service.model is not None,
        model_path=YOLO_MODEL_PATH,
        device=inference_service.device if inference_service else "unknown",
        gpu_available=torch.cuda.is_available(),
        gpu_name=gpu_name
    )


@app.post("/api/v1/detect", response_model=DetectionResponse)
async def detect_objects(
    file: UploadFile = File(...),
    conf_threshold: float = Form(default=0.35),
    iou_threshold: float = Form(default=0.45),
    imgsz: int = Form(default=1280),
    visualize: bool = Form(default=True)
):
    """
    Object detection endpoint (all classes)

    Args:
        file: Image file
        conf_threshold: Confidence threshold (0-1)
        iou_threshold: NMS IoU threshold (0-1)
        imgsz: Input image size
        visualize: Generate visualization image

    Returns:
        DetectionResponse with detection results
    """
    if inference_service is None or inference_service.model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    start_time = time.time()

    try:
        # Save uploaded file
        file_id = str(uuid.uuid4())
        file_ext = Path(file.filename).suffix
        file_path = UPLOAD_DIR / f"{file_id}{file_ext}"

        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)

        # Load image for size info
        image = cv2.imread(str(file_path))
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        img_height, img_width = image.shape[:2]

        # Run YOLO inference
        detections = inference_service.predict(
            image_path=str(file_path),
            conf_threshold=conf_threshold,
            iou_threshold=iou_threshold,
            imgsz=imgsz
        )

        # Post-processing: filter text blocks and remove duplicates
        original_count = len(detections)
        detections = inference_service.filter_text_blocks(detections, min_confidence=0.65)
        filtered_count = len(detections)
        detections = inference_service.remove_duplicate_detections(detections, iou_threshold=0.3)
        final_count = len(detections)

        # Generate visualization
        visualized_image_base64 = None
        if visualize and len(detections) > 0:
            annotated_img = draw_detections_on_image(image, detections)
            viz_path = RESULTS_DIR / f"{file_id}_annotated.jpg"
            cv2.imwrite(str(viz_path), annotated_img)

            # Encode to base64
            _, buffer = cv2.imencode('.jpg', annotated_img)
            visualized_image_base64 = base64.b64encode(buffer).decode('utf-8')

        # Save JSON result
        result_json = {
            'file_id': file_id,
            'detections': [det.dict() for det in detections],
            'total_detections': len(detections),
            'processing_time': time.time() - start_time,
            'model_used': YOLO_MODEL_PATH,
            'image_size': {'width': img_width, 'height': img_height},
            'filtering_stats': {
                'original_count': original_count,
                'after_text_filter': filtered_count,
                'final_count': final_count,
                'text_blocks_removed': original_count - filtered_count,
                'duplicates_removed': filtered_count - final_count
            }
        }

        json_path = RESULTS_DIR / f"{file_id}_result.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result_json, f, indent=2, ensure_ascii=False)

        processing_time = time.time() - start_time

        return DetectionResponse(
            status="success",
            file_id=file_id,
            detections=detections,
            total_detections=len(detections),
            processing_time=processing_time,
            model_used=YOLO_MODEL_PATH,
            image_size={'width': img_width, 'height': img_height},
            visualized_image=visualized_image_base64
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@app.post("/api/v1/extract_dimensions")
async def extract_dimensions(
    file: UploadFile = File(...),
    conf_threshold: float = Form(default=0.35),
    imgsz: int = Form(default=1280)
):
    """
    Extract dimensions (dimensions, GD&T, surface roughness separated)

    Args:
        file: Image file
        conf_threshold: Confidence threshold
        imgsz: Input image size

    Returns:
        Classified detection results
    """
    # Call detect API
    detection_result = await detect_objects(
        file=file,
        conf_threshold=conf_threshold,
        imgsz=imgsz,
        visualize=True
    )

    # Classify by class
    dimensions = [d for d in detection_result.detections if d.class_id <= 6]
    gdt_symbols = [d for d in detection_result.detections if 7 <= d.class_id <= 11]
    surface_roughness = [d for d in detection_result.detections if d.class_id == 12]
    text_blocks = [d for d in detection_result.detections if d.class_id == 13]

    return {
        'status': 'success',
        'file_id': detection_result.file_id,
        'dimensions': dimensions,
        'gdt_symbols': gdt_symbols,
        'surface_roughness': surface_roughness,
        'text_blocks': text_blocks,
        'total_detections': detection_result.total_detections,
        'processing_time': detection_result.processing_time,
        'model_used': detection_result.model_used
    }


@app.get("/api/v1/download/{file_id}")
async def download_result(
    file_id: str,
    result_type: str = "annotated"
):
    """
    Download result file

    Args:
        file_id: File ID
        result_type: Result type (annotated, json)

    Returns:
        File response
    """
    from fastapi.responses import FileResponse

    if result_type == "annotated":
        file_path = RESULTS_DIR / f"{file_id}_annotated.jpg"
        media_type = "image/jpeg"
    elif result_type == "json":
        file_path = RESULTS_DIR / f"{file_id}_result.json"
        media_type = "application/json"
    else:
        raise HTTPException(status_code=400, detail="Invalid result_type")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=file_path.name
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "YOLOv11 Drawing Analysis API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/api/v1/health",
            "detect": "/api/v1/detect",
            "extract_dimensions": "/api/v1/extract_dimensions",
            "download": "/api/v1/download/{file_id}",
            "docs": "/docs"
        }
    }


# =====================
# Main
# =====================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=YOLO_API_PORT,
        reload=False,
        log_level="info"
    )
