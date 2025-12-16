#!/usr/bin/env python3
"""
YOLOv11 API Server for Engineering Drawing Analysis
Port: 5005

통합 YOLO API - 여러 모델을 동적으로 로딩하여 사용
"""
import os
import time
import json
import uuid
import base64
import yaml
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

import cv2
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch

from models.schemas import (
    Detection, DetectionResponse, HealthResponse,
    APIInfoResponse, ParameterSchema, IOSchema, BlueprintFlowMetadata
)
from services.inference import YOLOInferenceService
from utils.helpers import draw_detections_on_image

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# =====================
# Configuration
# =====================

YOLO_API_PORT = int(os.getenv('YOLO_API_PORT', '5005'))
YOLO_MODEL_PATH = os.getenv('YOLO_MODEL_PATH', '/app/models/best.pt')
MODELS_DIR = Path('/app/models')
MODEL_REGISTRY_PATH = MODELS_DIR / 'model_registry.yaml'
UPLOAD_DIR = Path('/tmp/yolo-api/uploads')
RESULTS_DIR = Path('/tmp/yolo-api/results')

# Create directories
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# =====================
# SAHI Sliced Inference
# =====================

# SAHI 캐시 (모델 경로별)
_sahi_model_cache: Dict[str, Any] = {}


def run_sahi_inference(
    model_path: str,
    image_path: str,
    confidence: float = 0.25,
    slice_height: int = 512,
    slice_width: int = 512,
    overlap_ratio: float = 0.25
) -> List[Dict[str, Any]]:
    """
    SAHI 슬라이싱 기반 추론

    대형 이미지에서 작은 객체를 검출하기 위한 슬라이싱 기법
    """
    try:
        from sahi import AutoDetectionModel
        from sahi.predict import get_sliced_prediction

        # 캐시에서 SAHI 모델 가져오기 또는 생성
        if model_path not in _sahi_model_cache:
            logger.info(f"SAHI 모델 로딩: {model_path}")
            sahi_model = AutoDetectionModel.from_pretrained(
                model_type="yolov8",
                model_path=model_path,
                confidence_threshold=confidence,
                device="cuda:0" if torch.cuda.is_available() else "cpu"
            )
            _sahi_model_cache[model_path] = sahi_model
        else:
            sahi_model = _sahi_model_cache[model_path]
            # confidence 업데이트
            sahi_model.confidence_threshold = confidence

        # SAHI 슬라이싱 추론
        result = get_sliced_prediction(
            image_path,
            sahi_model,
            slice_height=slice_height,
            slice_width=slice_width,
            overlap_height_ratio=overlap_ratio,
            overlap_width_ratio=overlap_ratio,
            perform_standard_pred=True,
            postprocess_type="NMS",
            postprocess_match_threshold=0.5
        )

        # Detection 객체 형식으로 변환
        from models.schemas import Detection
        detections = []
        for i, pred in enumerate(result.object_prediction_list):
            bbox = pred.bbox.to_xyxy()
            x1, y1, x2, y2 = bbox

            # bbox를 Dict[str, int] 형식으로 변환 (schemas.py 스키마와 일치)
            detection = Detection(
                class_id=pred.category.id if pred.category else 0,
                class_name=pred.category.name if pred.category else "object",
                confidence=round(pred.score.value, 4),
                bbox={
                    'x': int(x1),
                    'y': int(y1),
                    'width': int(x2 - x1),
                    'height': int(y2 - y1)
                }
            )
            detections.append(detection)

        logger.info(f"SAHI 검출 완료: {len(detections)}개")
        return detections

    except ImportError:
        logger.warning("SAHI not installed, falling back to standard inference")
        return None
    except Exception as e:
        logger.error(f"SAHI inference error: {e}")
        import traceback
        traceback.print_exc()
        return None


# =====================
# Model Registry
# =====================

class ModelRegistry:
    """YAML 기반 모델 레지스트리 관리"""

    def __init__(self, registry_path: Path, models_dir: Path):
        self.registry_path = registry_path
        self.models_dir = models_dir
        self._registry: Dict[str, Any] = {}
        self._model_cache: Dict[str, YOLOInferenceService] = {}
        self.load_registry()

    def load_registry(self):
        """레지스트리 파일 로드"""
        if self.registry_path.exists():
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                self._registry = yaml.safe_load(f) or {}
            logger.info(f"모델 레지스트리 로드: {len(self._registry.get('models', {}))}개 모델")
        else:
            self._registry = {'models': {}, 'default_model': 'engineering'}
            self.save_registry()
            logger.info("새 모델 레지스트리 생성")

    def save_registry(self):
        """레지스트리 파일 저장"""
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            yaml.dump(self._registry, f, allow_unicode=True, default_flow_style=False)

    def get_models(self) -> Dict[str, Any]:
        """등록된 모델 목록"""
        models = {}
        for model_id, info in self._registry.get('models', {}).items():
            file_path = self.models_dir / info.get('file', '')
            models[model_id] = {
                **info,
                'id': model_id,
                'file_exists': file_path.exists(),
                'file_size_mb': round(file_path.stat().st_size / 1024 / 1024, 2) if file_path.exists() else 0
            }
        return models

    def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """특정 모델 정보"""
        return self._registry.get('models', {}).get(model_id)

    def get_default_model(self) -> str:
        """기본 모델 ID"""
        return self._registry.get('default_model', 'engineering')

    def add_model(self, model_id: str, info: Dict[str, Any]):
        """모델 등록"""
        if 'models' not in self._registry:
            self._registry['models'] = {}
        self._registry['models'][model_id] = info
        self.save_registry()
        logger.info(f"모델 등록: {model_id}")

    def update_model(self, model_id: str, info: Dict[str, Any]):
        """모델 정보 업데이트"""
        if model_id in self._registry.get('models', {}):
            self._registry['models'][model_id].update(info)
            self.save_registry()
            logger.info(f"모델 업데이트: {model_id}")

    def delete_model(self, model_id: str) -> bool:
        """모델 삭제 (파일은 유지, 레지스트리에서만 제거)"""
        if model_id in self._registry.get('models', {}):
            del self._registry['models'][model_id]
            if model_id in self._model_cache:
                del self._model_cache[model_id]
            self.save_registry()
            logger.info(f"모델 삭제: {model_id}")
            return True
        return False

    def get_inference_service(self, model_id: str) -> Optional[YOLOInferenceService]:
        """모델 로드 (캐시 사용)"""
        # 캐시에 있으면 반환
        if model_id in self._model_cache:
            return self._model_cache[model_id]

        # 레지스트리에서 모델 정보 조회
        model_info = self.get_model(model_id)
        if not model_info:
            logger.warning(f"모델을 찾을 수 없음: {model_id}")
            return None

        # 모델 파일 경로
        model_path = self.models_dir / model_info.get('file', '')
        if not model_path.exists():
            logger.warning(f"모델 파일이 없음: {model_path}")
            return None

        # 모델 로드
        logger.info(f"모델 로딩: {model_id} ({model_path})")
        service = YOLOInferenceService(str(model_path))
        service.load_model()

        # 캐시에 저장
        self._model_cache[model_id] = service
        return service


# Global model registry
model_registry: Optional[ModelRegistry] = None


# =====================
# FastAPI App
# =====================

app = FastAPI(
    title="YOLOv11 Drawing Analysis API",
    description="통합 YOLO API - 다중 모델 지원 (기계도면, P&ID 등)",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global inference service (기본 모델용, 하위 호환성)
inference_service: Optional[YOLOInferenceService] = None


# =====================
# Startup / Shutdown
# =====================

@app.on_event("startup")
async def startup_event():
    """Load model registry and default model on startup"""
    global inference_service, model_registry

    print("=" * 70)
    print("🚀 YOLOv11 통합 API Server Starting...")
    print("=" * 70)

    # 모델 레지스트리 초기화
    model_registry = ModelRegistry(MODEL_REGISTRY_PATH, MODELS_DIR)

    # 기본 모델 로드
    default_model = model_registry.get_default_model()
    inference_service = model_registry.get_inference_service(default_model)

    if inference_service is None:
        # 폴백: 환경변수 모델 경로 사용
        logger.warning(f"기본 모델 로드 실패, 폴백: {YOLO_MODEL_PATH}")
        inference_service = YOLOInferenceService(YOLO_MODEL_PATH)
        inference_service.load_model()

    print(f"📦 등록된 모델: {len(model_registry.get_models())}개")
    print(f"✅ 기본 모델: {default_model}")

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


@app.get("/api/v1/info", response_model=APIInfoResponse)
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


@app.post("/api/v1/detect", response_model=DetectionResponse)
async def detect_objects(
    file: UploadFile = File(...),
    model_type: str = Form(default="yolo11n-general", description="Model type (engineering/pid_symbol/pid_class_agnostic/pid_class_aware)"),
    confidence: float = Form(default=0.5, description="Confidence threshold (0-1)", alias="conf_threshold"),
    iou_threshold: float = Form(default=0.45, description="NMS IoU threshold (0-1)"),
    imgsz: int = Form(default=640, description="Input image size (320/640/1280)"),
    visualize: bool = Form(default=True, description="Generate visualization image"),
    task: str = Form(default="detect", description="Task type (detect/segment)"),
    # SAHI 슬라이싱 파라미터
    use_sahi: bool = Form(default=False, description="Enable SAHI slicing for large images"),
    slice_height: int = Form(default=512, description="SAHI slice height"),
    slice_width: int = Form(default=512, description="SAHI slice width"),
    overlap_ratio: float = Form(default=0.25, description="SAHI slice overlap ratio (0-0.5)")
):
    """
    Object detection endpoint (all classes)

    Args:
        file: Image file
        model_type: Model type (engineering, pid_symbol, pid_class_agnostic, pid_class_aware)
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
            "pid_symbol": "pid_symbol",
            "pid_class_agnostic": "pid_class_agnostic",
            "pid_class_aware": "pid_class_aware",
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

        # P&ID 모델이면서 use_sahi=False인 경우 자동으로 SAHI 활성화
        is_pid_model = model_id.startswith('pid_')
        if is_pid_model and not use_sahi:
            use_sahi = True
            logger.info(f"P&ID 모델 자동 SAHI 활성화: {model_id}")

        # SAHI 또는 일반 추론 선택
        if use_sahi:
            # SAHI 슬라이싱 기반 추론
            model_info = model_registry.get_model(model_id) if model_registry else None
            model_file = model_info.get('file', 'best.pt') if model_info else 'best.pt'
            model_path = str(MODELS_DIR / model_file)

            logger.info(f"SAHI 추론: model={model_id}, slice={slice_height}x{slice_width}, overlap={overlap_ratio}")
            detections = run_sahi_inference(
                model_path=model_path,
                image_path=str(file_path),
                confidence=confidence,
                slice_height=slice_height,
                slice_width=slice_width,
                overlap_ratio=overlap_ratio
            )

            # SAHI 실패 시 일반 추론으로 폴백
            if detections is None:
                logger.warning("SAHI 추론 실패, 일반 추론으로 폴백")
                detections = selected_service.predict(
                    image_path=str(file_path),
                    conf_threshold=confidence,
                    iou_threshold=iou_threshold,
                    imgsz=imgsz,
                    task=task
                )
        else:
            # 일반 YOLO 추론
            detections = selected_service.predict(
                image_path=str(file_path),
                conf_threshold=confidence,
                iou_threshold=iou_threshold,
                imgsz=imgsz,
                task=task
            )

        # Post-processing: filter text blocks and remove duplicates
        original_count = len(detections)
        # P&ID 모델 또는 bom_detector는 필터링 건너뛰기 (Streamlit과 동일하게)
        is_bom_model = model_id == 'bom_detector'
        if not is_pid_model and not is_bom_model:
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

        return DetectionResponse(
            status="success",
            file_id=file_id,
            detections=detections,
            total_detections=len(detections),
            processing_time=processing_time,
            model_used=model_id,
            image_size={'width': img_width, 'height': img_height},
            visualized_image=visualized_image_base64
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@app.post("/api/v1/extract_dimensions")
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
# Model Registry API
# =====================

class ModelInfo(BaseModel):
    """모델 정보 스키마"""
    name: str
    description: str
    best_for: Optional[str] = None
    classes: Optional[int] = None
    file: Optional[str] = None


@app.get("/api/v1/models")
async def get_models():
    """
    등록된 모델 목록 조회

    Returns:
        models: 모델 목록 (ID, 이름, 설명, 파일 크기 등)
        default_model: 기본 모델 ID
    """
    if model_registry is None:
        raise HTTPException(status_code=503, detail="Model registry not initialized")

    models = model_registry.get_models()
    return {
        "models": list(models.values()),
        "default_model": model_registry.get_default_model(),
        "total": len(models)
    }


@app.get("/api/v1/models/{model_id}")
async def get_model(model_id: str):
    """특정 모델 정보 조회"""
    if model_registry is None:
        raise HTTPException(status_code=503, detail="Model registry not initialized")

    models = model_registry.get_models()
    if model_id not in models:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")

    return models[model_id]


@app.post("/api/v1/models/{model_id}")
async def add_or_update_model(model_id: str, info: ModelInfo):
    """
    모델 등록/수정

    모델 파일(.pt)은 별도로 업로드해야 함
    """
    if model_registry is None:
        raise HTTPException(status_code=503, detail="Model registry not initialized")

    model_data = info.dict(exclude_none=True)

    if model_registry.get_model(model_id):
        model_registry.update_model(model_id, model_data)
        return {"message": f"Model '{model_id}' updated", "model_id": model_id}
    else:
        model_registry.add_model(model_id, model_data)
        return {"message": f"Model '{model_id}' added", "model_id": model_id}


@app.delete("/api/v1/models/{model_id}")
async def delete_model(model_id: str):
    """모델 삭제 (레지스트리에서만 제거, 파일은 유지)"""
    if model_registry is None:
        raise HTTPException(status_code=503, detail="Model registry not initialized")

    if model_id == model_registry.get_default_model():
        raise HTTPException(status_code=400, detail="Cannot delete default model")

    if model_registry.delete_model(model_id):
        return {"message": f"Model '{model_id}' deleted"}
    else:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")


@app.post("/api/v1/models/{model_id}/upload")
async def upload_model_file(
    model_id: str,
    file: UploadFile = File(..., description="YOLO 모델 파일 (.pt)")
):
    """모델 파일 업로드"""
    if model_registry is None:
        raise HTTPException(status_code=503, detail="Model registry not initialized")

    if not file.filename.endswith('.pt'):
        raise HTTPException(status_code=400, detail="Only .pt files are allowed")

    # 파일 저장
    file_path = MODELS_DIR / f"{model_id}.pt"
    content = await file.read()
    with open(file_path, 'wb') as f:
        f.write(content)

    # 레지스트리에 파일 경로 업데이트
    if model_registry.get_model(model_id):
        model_registry.update_model(model_id, {"file": f"{model_id}.pt"})
    else:
        model_registry.add_model(model_id, {"file": f"{model_id}.pt", "name": model_id})

    # 캐시 무효화 (다음 요청시 새 모델 로드)
    if model_id in model_registry._model_cache:
        del model_registry._model_cache[model_id]

    file_size_mb = len(content) / 1024 / 1024
    return {
        "message": f"Model file uploaded: {file.filename}",
        "model_id": model_id,
        "file_size_mb": round(file_size_mb, 2)
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
