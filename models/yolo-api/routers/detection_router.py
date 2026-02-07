"""
Detection Router - YOLO Object Detection Endpoints
"""
import time
import uuid
import json
import base64
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

import cv2
import torch
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse

from models.schemas import (
    Detection, DetectionResponse, SVGOverlay,
    APIInfoResponse, ParameterSchema, IOSchema, BlueprintFlowMetadata
)
from services.inference import YOLOInferenceService
from services.registry import ModelRegistry, get_model_registry, get_inference_service
from services.sahi_inference import run_sahi_inference
from utils.helpers import draw_detections_on_image
from config.model_defaults import MODEL_DEFAULTS, get_model_config, get_sahi_config
from services.svg_generator import generate_detection_svg, detections_to_svg_data

logger = logging.getLogger(__name__)

# Configuration
YOLO_API_PORT = 5005
MODELS_DIR = Path('/app/models')
UPLOAD_DIR = Path('/tmp/yolo-api/uploads')
RESULTS_DIR = Path('/tmp/yolo-api/results')

router = APIRouter(prefix="/api/v1", tags=["detection"])


@router.get("/info", response_model=APIInfoResponse)
async def get_api_info():
    """
    API 메타데이터 엔드포인트

    BlueprintFlow 및 Dashboard에서 API를 자동으로 등록하기 위한 메타데이터를 제공합니다.
    """
    return APIInfoResponse(
        id="yolo-detector",
        name="YOLO Detection API",
        display_name="YOLO 객체 검출",
        version="1.0.0",
        description="YOLOv11 기반 도면 심볼/치수/GD&T 검출 API",
        openapi_url="/openapi.json",
        base_url=f"http://localhost:{YOLO_API_PORT}",
        endpoint="/api/v1/detect",
        method="POST",
        requires_image=True,
        inputs=[
            IOSchema(
                name="file",
                type="file",
                description="분석할 도면 이미지 파일",
                required=True
            )
        ],
        outputs=[
            IOSchema(
                name="detections",
                type="array",
                description="검출된 객체 목록 (각 객체는 class_id, class_name, confidence, bbox 포함)"
            ),
            IOSchema(
                name="total_detections",
                type="integer",
                description="총 검출된 객체 개수"
            ),
            IOSchema(
                name="processing_time",
                type="float",
                description="처리 시간 (초)"
            ),
            IOSchema(
                name="visualized_image",
                type="string",
                description="검출 결과가 표시된 이미지 (base64)"
            )
        ],
        parameters=[
            ParameterSchema(
                name="model_type",
                type="select",
                default="yolo11n-general",
                description="용도별 특화 모델 선택",
                required=False,
                options=[
                    "symbol-detector-v1",
                    "dimension-detector-v1",
                    "gdt-detector-v1",
                    "text-region-detector-v1",
                    "yolo11n-general"
                ]
            ),
            ParameterSchema(
                name="confidence",
                type="number",
                default=0.5,
                description="검출 신뢰도 임계값 (낮을수록 더 많이 검출)",
                required=False,
                min=0.0,
                max=1.0,
                step=0.05
            ),
            ParameterSchema(
                name="iou_threshold",
                type="number",
                default=0.45,
                description="NMS IoU 임계값 (겹침 제거, 높을수록 엄격)",
                required=False,
                min=0.0,
                max=1.0,
                step=0.05
            ),
            ParameterSchema(
                name="imgsz",
                type="select",
                default="640",
                description="입력 이미지 크기 (클수록 정확하지만 느림)",
                required=False,
                options=["320", "640", "1280"]
            ),
            ParameterSchema(
                name="visualize",
                type="boolean",
                default=True,
                description="검출 결과 시각화 이미지 생성",
                required=False
            ),
            ParameterSchema(
                name="task",
                type="select",
                default="detect",
                description="검출 모드 (전체 검출 vs 세그멘테이션)",
                required=False,
                options=["detect", "segment"]
            )
        ],
        blueprintflow=BlueprintFlowMetadata(
            icon="🎯",
            color="#3b82f6",
            category="detection"
        ),
        output_mappings={
            "detections": "detections",
            "total_detections": "total_detections",
            "processing_time": "processing_time",
            "visualized_image": "visualized_image"
        }
    )


@router.post("/detect", response_model=DetectionResponse)
async def detect_objects(
    file: UploadFile = File(...),
    model_type: str = Form(default="yolo11n-general", description="Model type (engineering/pid_class_aware/pid_class_agnostic/bom_detector)"),
    confidence: float = Form(default=0.5, description="Confidence threshold (0-1)", alias="conf_threshold"),
    iou_threshold: float = Form(default=0.45, description="NMS IoU threshold (0-1)"),
    imgsz: int = Form(default=640, description="Input image size (320/640/1280)"),
    visualize: bool = Form(default=True, description="Generate visualization image"),
    task: str = Form(default="detect", description="Task type (detect/segment)"),
    # SAHI 슬라이싱 파라미터
    use_sahi: bool = Form(default=False, description="Enable SAHI slicing for large images"),
    slice_height: int = Form(default=512, description="SAHI slice height"),
    slice_width: int = Form(default=512, description="SAHI slice width"),
    overlap_ratio: float = Form(default=0.25, description="SAHI slice overlap ratio (0-0.5)"),
    # TTA (Test Time Augmentation) 파라미터
    augment: bool = Form(default=False, description="Enable Test Time Augmentation (TTA) for higher recall"),
    # SVG 오버레이 파라미터
    include_svg: bool = Form(default=False, description="Include SVG overlay in response"),
):
    """
    Object detection endpoint (all classes)

    Args:
        file: Image file
        model_type: Model type (engineering, pid_class_aware, pid_class_agnostic, bom_detector)
        confidence: Confidence threshold (0-1)
        iou_threshold: NMS IoU threshold (0-1)
        imgsz: Input image size (320, 640, 1280)
        visualize: Generate visualization image
        task: Task type (detect or segment)
        use_sahi: Enable SAHI slicing for large images (recommended for P&ID)
        slice_height: SAHI slice height (256-2048)
        slice_width: SAHI slice width (256-2048)
        overlap_ratio: SAHI slice overlap ratio (0-0.5)

    Returns:
        DetectionResponse with detection results
    """
    start_time = time.time()
    model_registry = get_model_registry()
    inference_service = get_inference_service()

    try:
        # 모델 선택 (레지스트리 기반)
        # 하위 호환성: 기존 model_type 값을 새 모델 ID로 매핑
        model_id_map = {
            "symbol-detector-v1": "engineering",
            "dimension-detector-v1": "engineering",
            "gdt-detector-v1": "engineering",
            "text-region-detector-v1": "engineering",
            "yolo11n-general": "engineering",
            # 새 모델 ID는 그대로 사용
            "engineering": "engineering",
            "pid_symbol": "pid_symbol",  # P&ID 60종 심볼 (클래스 이름 포함)
            "pid_class_agnostic": "pid_class_agnostic",
            "pid_class_aware": "pid_class_aware",
            "bom_detector": "bom_detector",
            "panasia": "panasia",  # 파나시아 MCP Panel 27종 (classExamples 매칭)
        }
        model_id = model_id_map.get(model_type, model_type)

        # 선택된 모델 로드 (캐시 사용)
        selected_service = model_registry.get_inference_service(model_id) if model_registry else None
        if selected_service is None:
            # 폴백: 기본 모델 사용
            logger.warning(f"모델 '{model_id}' 로드 실패, 기본 모델 사용")
            selected_service = inference_service

        if selected_service is None or selected_service.model is None:
            raise HTTPException(status_code=503, detail="Model not loaded")

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

        # 모델별 기본값 적용 (MODEL_DEFAULTS 패턴)
        model_config = get_model_config(model_id)
        sahi_config = get_sahi_config(model_id)

        # 사용자 입력이 기본값과 같으면 모델별 기본값 사용
        is_pid_model = model_id.startswith('pid_')
        if confidence == 0.5:  # 기본값이면 모델별 기본값 사용
            confidence = model_config.get("confidence", 0.5)
        if iou_threshold == 0.45:  # 기본값이면 모델별 기본값 사용
            iou_threshold = model_config.get("iou", 0.45)
        if imgsz == 640:  # 기본값이면 모델별 기본값 사용
            imgsz = model_config.get("imgsz", 640)

        # 모델별 augment(TTA) 자동 활성화 (model_defaults 기반)
        if not augment and model_config.get("augment", False):
            augment = True
            logger.info(f"모델 기본값으로 TTA 활성화: {model_id}")

        # 모델별 SAHI 자동 활성화 (model_defaults 기반)
        if not use_sahi and sahi_config.get("use_sahi", False):
            use_sahi = True
            slice_height = sahi_config.get("slice_size", 512)
            slice_width = sahi_config.get("slice_size", 512)
            overlap_ratio = sahi_config.get("overlap_ratio", 0.25)
            logger.info(f"모델 기본값으로 SAHI 활성화: {model_id}, slice={slice_height}x{slice_width}")

        # SAHI 또는 일반 추론 선택
        if use_sahi:
            # SAHI 슬라이싱 기반 추론
            model_info = model_registry.get_model(model_id) if model_registry else None
            model_file = model_info.get('file', 'best.pt') if model_info else 'best.pt'
            model_path = str(MODELS_DIR / model_file)

            # class_names 오버라이드 준비 (data_yaml 지원)
            sahi_class_names = None
            if model_info and 'class_names' in model_info:
                class_names_list = model_info['class_names']
                sahi_class_names = {i: name for i, name in enumerate(class_names_list)}

            logger.info(f"SAHI 추론: model={model_id}, slice={slice_height}x{slice_width}, overlap={overlap_ratio}")
            detections = run_sahi_inference(
                model_path=model_path,
                image_path=str(file_path),
                confidence=confidence,
                slice_height=slice_height,
                slice_width=slice_width,
                overlap_ratio=overlap_ratio,
                class_names=sahi_class_names
            )

            # SAHI 실패 시 일반 추론으로 폴백
            if detections is None:
                logger.warning("SAHI 추론 실패, 일반 추론으로 폴백")
                detections = selected_service.predict(
                    image_path=str(file_path),
                    conf_threshold=confidence,
                    iou_threshold=iou_threshold,
                    imgsz=imgsz,
                    task=task,
                    augment=augment
                )
        else:
            # 일반 YOLO 추론
            detections = selected_service.predict(
                image_path=str(file_path),
                conf_threshold=confidence,
                iou_threshold=iou_threshold,
                imgsz=imgsz,
                task=task,
                augment=augment
            )

        # Post-processing: map class IDs to proper names from registry
        if model_registry:
            model_info = model_registry.get_model(model_id)
            if model_info and 'class_names' in model_info:
                class_names_list = model_info['class_names']
                for det in detections:
                    if det.class_name.isdigit() or det.class_name.startswith('class_'):
                        class_idx = det.class_id
                        if 0 <= class_idx < len(class_names_list):
                            det.class_name = class_names_list[class_idx]

        # Post-processing: filter text blocks and remove duplicates
        original_count = len(detections)
        # P&ID 모델, bom_detector, panasia는 필터링 건너뛰기 (심볼 검출 모델)
        is_bom_model = model_id == 'bom_detector'
        is_panasia_model = model_id == 'panasia'
        if not is_pid_model and not is_bom_model and not is_panasia_model:
            detections = selected_service.filter_text_blocks(detections, min_confidence=0.65)
            detections = selected_service.remove_duplicate_detections(detections, iou_threshold=0.3)
        filtered_count = len(detections)
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
            'model_used': model_id,
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

        # SVG 오버레이 생성 (include_svg=True인 경우)
        svg_overlay_data = None
        if include_svg and len(detections) > 0:
            # Detection 객체를 dict로 변환
            detections_dict = [
                {
                    "class_id": det.class_id,
                    "class_name": det.class_name,
                    "confidence": det.confidence,
                    "bbox": det.bbox,
                }
                for det in detections
            ]
            svg_data = detections_to_svg_data(
                detections=detections_dict,
                image_size=(img_width, img_height),
                model_type=model_id,
            )
            svg_overlay_data = SVGOverlay(
                svg=svg_data["svg"],
                svg_minimal=svg_data["svg_minimal"],
                width=svg_data["width"],
                height=svg_data["height"],
                detection_count=svg_data["detection_count"],
                model_type=svg_data["model_type"],
            )

        return DetectionResponse(
            status="success",
            file_id=file_id,
            detections=detections,
            total_detections=len(detections),
            processing_time=processing_time,
            model_used=model_id,
            image_size={'width': img_width, 'height': img_height},
            visualized_image=visualized_image_base64,
            svg_overlay=svg_overlay_data,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@router.post("/extract_dimensions")
async def extract_dimensions(
    file: UploadFile = File(...),
    confidence: float = Form(default=0.35, alias="conf_threshold"),
    imgsz: int = Form(default=1280),
    model_type: str = Form(default="dimension-detector-v1")
):
    """
    Extract dimensions (dimensions, GD&T, surface roughness separated)

    Args:
        file: Image file
        confidence: Confidence threshold
        imgsz: Input image size
        model_type: Model type (defaults to dimension-detector-v1)

    Returns:
        Classified detection results
    """
    # Call detect API with dimension-optimized model
    detection_result = await detect_objects(
        file=file,
        model_type=model_type,
        confidence=confidence,
        imgsz=imgsz,
        visualize=True,
        iou_threshold=0.45,
        task="detect"
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


@router.get("/download/{file_id}")
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
