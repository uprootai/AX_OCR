"""
YOLO P&ID Symbol Detector API Server (SAHI Enhanced)
P&ID 심볼 검출 API - SAHI (Slicing Aided Hyper Inference) 기반

기술:
- YOLOv8 기반 객체 검출
- SAHI: 대형 이미지 슬라이싱 기반 고해상도 검출
- Class-agnostic 또는 Class-aware 검출 모드

포트: 5017
"""
import os
import io
import time
import logging
import base64
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import cv2
import numpy as np

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_PORT = int(os.getenv("YOLO_PID_PORT", "5017"))
MODEL_PATH = os.getenv("YOLO_PID_MODEL", "pid_symbol_detector.pt")

# SAHI 설정 (최적화됨)
SAHI_SLICE_HEIGHT = 512  # 작은 심볼 검출 향상
SAHI_SLICE_WIDTH = 512
SAHI_OVERLAP_RATIO = 0.25  # 경계 누락 방지
DEFAULT_CONFIDENCE = 0.10  # 더 많은 심볼 검출

# =====================
# P&ID Symbol Classes (Stage 2: 32-class model)
# =====================

PID_SYMBOL_CLASSES = {
    0: {"name": "Agitator", "category": "equipment", "korean": "교반기"},
    1: {"name": "Air-cooled Exchanger", "category": "heat_exchanger", "korean": "공냉식 열교환기"},
    2: {"name": "Ball valve", "category": "valve", "korean": "볼 밸브"},
    3: {"name": "Blind End", "category": "piping", "korean": "블라인드 엔드"},
    4: {"name": "Centrifugal compressor", "category": "compressor", "korean": "원심 압축기"},
    5: {"name": "Centrifugal pump", "category": "pump", "korean": "원심 펌프"},
    6: {"name": "Check valve", "category": "valve", "korean": "체크 밸브"},
    7: {"name": "Column", "category": "tank", "korean": "컬럼"},
    8: {"name": "Compressor", "category": "compressor", "korean": "압축기"},
    9: {"name": "Condenser", "category": "heat_exchanger", "korean": "응축기"},
    10: {"name": "Control valve", "category": "valve", "korean": "제어 밸브"},
    11: {"name": "Decanter", "category": "tank", "korean": "디캔터"},
    12: {"name": "Exchanger", "category": "heat_exchanger", "korean": "열교환기"},
    13: {"name": "Fan", "category": "equipment", "korean": "팬"},
    14: {"name": "Flange", "category": "piping", "korean": "플랜지"},
    15: {"name": "Gate Valve", "category": "valve", "korean": "게이트 밸브"},
    16: {"name": "Globe Valve", "category": "valve", "korean": "글로브 밸브"},
    17: {"name": "Hand Valve", "category": "valve", "korean": "핸드 밸브"},
    18: {"name": "In-line Instrument", "category": "instrument", "korean": "인라인 계기"},
    19: {"name": "Motor", "category": "equipment", "korean": "모터"},
    20: {"name": "Off-sheet", "category": "piping", "korean": "오프시트"},
    21: {"name": "Pump", "category": "pump", "korean": "펌프"},
    22: {"name": "Reboiler", "category": "heat_exchanger", "korean": "리보일러"},
    23: {"name": "Reciprocating compressor", "category": "compressor", "korean": "왕복 압축기"},
    24: {"name": "Reciprocating pump", "category": "pump", "korean": "왕복 펌프"},
    25: {"name": "Reducer", "category": "piping", "korean": "레듀서"},
    26: {"name": "Regulator", "category": "instrument", "korean": "레귤레이터"},
    27: {"name": "Round Instrument", "category": "instrument", "korean": "원형 계기"},
    28: {"name": "Separator", "category": "tank", "korean": "분리기"},
    29: {"name": "Valve", "category": "valve", "korean": "밸브"},
}

CATEGORY_COLORS = {
    "valve": (0, 255, 0),        # Green
    "pump": (255, 0, 0),         # Blue
    "instrument": (0, 0, 255),   # Red
    "tank": (255, 255, 0),       # Cyan
    "heat_exchanger": (255, 0, 255),  # Magenta
    "compressor": (0, 255, 255), # Yellow
    "piping": (128, 128, 128),   # Gray
    "equipment": (128, 0, 128),  # Purple
    "symbol": (255, 128, 0)      # Orange (class-agnostic)
}


# =====================
# Schemas
# =====================

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str


class Detection(BaseModel):
    id: int
    class_id: int
    class_name: str
    category: str
    korean_name: str
    confidence: float
    bbox: List[float]  # [x1, y1, x2, y2]
    center: List[float]  # [cx, cy]


class ProcessResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    processing_time: float
    error: Optional[str] = None


# =====================
# Core Functions
# =====================

# SAHI 모델 (lazy loading)
sahi_model = None


def load_sahi_model(confidence: float = 0.15):
    """SAHI 모델 로드 (필요시)"""
    global sahi_model

    try:
        from sahi import AutoDetectionModel

        # 모델 경로 확인
        model_path = MODEL_PATH
        if not os.path.exists(model_path):
            # Docker 컨테이너 내부 경로
            model_path = "/app/pid_symbol_detector.pt"

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at {MODEL_PATH} or {model_path}")

        sahi_model = AutoDetectionModel.from_pretrained(
            model_type="yolov8",
            model_path=model_path,
            confidence_threshold=confidence,
            device="cuda:0" if os.path.exists("/dev/nvidia0") else "cpu"
        )
        logger.info(f"Loaded SAHI model from: {model_path}")
        logger.info(f"Device: {'cuda:0' if os.path.exists('/dev/nvidia0') else 'cpu'}")

    except ImportError:
        logger.warning("SAHI not installed, falling back to direct YOLO inference")
        sahi_model = None
    except Exception as e:
        logger.error(f"Failed to load SAHI model: {e}")
        sahi_model = None

    return sahi_model


def detect_pid_symbols_sahi(image: np.ndarray, confidence: float = 0.15,
                             slice_height: int = 1024, slice_width: int = 1024,
                             overlap_ratio: float = 0.2,
                             class_agnostic: bool = True) -> List[Dict]:
    """
    SAHI 기반 P&ID 심볼 검출

    Args:
        image: 입력 이미지
        confidence: 신뢰도 임계값
        slice_height: 슬라이스 높이
        slice_width: 슬라이스 너비
        overlap_ratio: 슬라이스 오버랩 비율
        class_agnostic: True면 모든 심볼을 "Symbol"로 분류
    """
    try:
        from sahi import AutoDetectionModel
        from sahi.predict import get_sliced_prediction

        # 모델 로드 (confidence가 변경되면 재로드)
        global sahi_model
        if sahi_model is None:
            load_sahi_model(confidence)

        if sahi_model is None:
            # SAHI 없이 기본 YOLO 사용
            return detect_pid_symbols_basic(image, confidence)

        # 임시 파일로 저장 (SAHI는 파일 경로 필요)
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name
            cv2.imwrite(temp_path, image)

        try:
            # SAHI 슬라이싱 추론
            result = get_sliced_prediction(
                temp_path,
                sahi_model,
                slice_height=slice_height,
                slice_width=slice_width,
                overlap_height_ratio=overlap_ratio,
                overlap_width_ratio=overlap_ratio,
                perform_standard_pred=True,
                postprocess_type="NMS",
                postprocess_match_threshold=0.5
            )
        finally:
            # 임시 파일 삭제
            os.unlink(temp_path)

        detections = []
        for i, pred in enumerate(result.object_prediction_list):
            bbox = pred.bbox.to_xyxy()
            x1, y1, x2, y2 = bbox
            conf = pred.score.value
            cls_id = pred.category.id if pred.category else 0
            cls_name = pred.category.name if pred.category else "Symbol"

            # Class-agnostic 모드
            if class_agnostic:
                cls_name = "Symbol"
                category = "symbol"
                korean_name = "심볼"
            else:
                # Class-aware 모드: PID_SYMBOL_CLASSES 사용
                if cls_id < len(PID_SYMBOL_CLASSES):
                    symbol_info = PID_SYMBOL_CLASSES[cls_id]
                    cls_name = symbol_info["name"]
                    category = symbol_info["category"]
                    korean_name = symbol_info["korean"]
                else:
                    category = "symbol"
                    korean_name = cls_name

            detection = {
                "id": i,
                "class_id": cls_id,
                "class_name": cls_name,
                "category": category,
                "korean_name": korean_name,
                "confidence": round(conf, 4),
                "bbox": [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)],
                "center": [round((x1 + x2) / 2, 2), round((y1 + y2) / 2, 2)],
                "width": round(x2 - x1, 2),
                "height": round(y2 - y1, 2)
            }
            detections.append(detection)

        return detections

    except ImportError:
        logger.warning("SAHI not available, using basic YOLO detection")
        return detect_pid_symbols_basic(image, confidence)
    except Exception as e:
        logger.error(f"SAHI detection error: {e}")
        import traceback
        traceback.print_exc()
        return detect_pid_symbols_basic(image, confidence)


def detect_pid_symbols_basic(image: np.ndarray, confidence: float = 0.25) -> List[Dict]:
    """기본 YOLO 검출 (SAHI 없이)"""
    try:
        from ultralytics import YOLO

        model_path = MODEL_PATH
        if not os.path.exists(model_path):
            model_path = "/app/pid_symbol_detector.pt"

        if not os.path.exists(model_path):
            logger.error(f"Model not found: {model_path}")
            return []

        model = YOLO(model_path)
        results = model.predict(image, conf=confidence, verbose=False)

        detections = []
        if results and len(results) > 0:
            result = results[0]
            boxes = result.boxes

            for i, box in enumerate(boxes):
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])

                detection = {
                    "id": i,
                    "class_id": cls_id,
                    "class_name": "Symbol",
                    "category": "symbol",
                    "korean_name": "심볼",
                    "confidence": round(conf, 4),
                    "bbox": [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)],
                    "center": [round((x1 + x2) / 2, 2), round((y1 + y2) / 2, 2)],
                    "width": round(x2 - x1, 2),
                    "height": round(y2 - y1, 2)
                }
                detections.append(detection)

        return detections

    except Exception as e:
        logger.error(f"Basic detection error: {e}")
        return []


def visualize_detections(image: np.ndarray, detections: List[Dict]) -> np.ndarray:
    """검출 결과 시각화"""
    vis = image.copy()

    for det in detections:
        x1, y1, x2, y2 = [int(v) for v in det["bbox"]]
        category = det.get("category", "symbol")
        color = CATEGORY_COLORS.get(category, (255, 128, 0))

        # 바운딩 박스
        cv2.rectangle(vis, (x1, y1), (x2, y2), color, 2)

        # 레이블
        label = f"{det['class_name']} {det['confidence']:.2f}"
        (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(vis, (x1, y1 - 20), (x1 + w + 4, y1), color, -1)
        cv2.putText(vis, label, (x1 + 2, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    return vis


def numpy_to_base64(image: np.ndarray) -> str:
    """NumPy 이미지를 Base64로 변환"""
    _, buffer = cv2.imencode('.png', image)
    return base64.b64encode(buffer).decode('utf-8')


def get_category_statistics(detections: List[Dict]) -> Dict[str, int]:
    """카테고리별 통계"""
    stats = {}
    for det in detections:
        cat = det.get("category", "symbol")
        stats[cat] = stats.get(cat, 0) + 1
    return stats


# =====================
# FastAPI App
# =====================

app = FastAPI(
    title="YOLO P&ID Symbol Detector API (SAHI Enhanced)",
    description="P&ID 심볼 검출 API - SAHI 기반 대형 이미지 고해상도 검출",
    version="2.0.0"
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

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스체크"""
    return HealthResponse(
        status="healthy",
        service="yolo-pid-api",
        version="2.0.0",
        timestamp=datetime.now().isoformat()
    )


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check_v1():
    """헬스체크 (v1 경로)"""
    return await health_check()


@app.get("/api/v1/info")
async def get_info():
    """API 정보 (BlueprintFlow 메타데이터)"""
    return {
        "id": "yolo-pid",
        "name": "YOLO P&ID (SAHI)",
        "display_name": "P&ID Symbol Detector (SAHI Enhanced)",
        "version": "2.0.0",
        "description": "P&ID 심볼 검출 API - SAHI 기반 대형 이미지 고해상도 검출",
        "base_url": f"http://localhost:{API_PORT}",
        "endpoint": "/api/v1/process",
        "method": "POST",
        "requires_image": True,
        "blueprintflow": {
            "category": "detection",
            "color": "#10b981",
            "icon": "CircuitBoard"
        },
        "inputs": [
            {"name": "image", "type": "Image", "required": True, "description": "P&ID 도면 이미지"}
        ],
        "outputs": [
            {"name": "detections", "type": "Detection[]", "description": "검출된 심볼 목록"},
            {"name": "statistics", "type": "object", "description": "카테고리별 통계"},
            {"name": "visualization", "type": "Image", "description": "시각화 이미지"}
        ],
        "parameters": [
            {"name": "confidence", "type": "number", "min": 0.05, "max": 1.0, "default": 0.10, "description": "신뢰도 임계값"},
            {"name": "slice_height", "type": "number", "min": 256, "max": 2048, "default": 512, "description": "SAHI 슬라이스 높이"},
            {"name": "slice_width", "type": "number", "min": 256, "max": 2048, "default": 512, "description": "SAHI 슬라이스 너비"},
            {"name": "overlap_ratio", "type": "number", "min": 0.1, "max": 0.5, "default": 0.25, "description": "슬라이스 오버랩 비율"},
            {"name": "class_agnostic", "type": "boolean", "default": False, "description": "Class-agnostic 모드 (False=32클래스 분류)"},
            {"name": "visualize", "type": "boolean", "default": True, "description": "결과 시각화"}
        ],
        "symbol_classes": len(PID_SYMBOL_CLASSES),
        "detection_method": "SAHI (Slicing Aided Hyper Inference)"
    }


@app.get("/api/v1/classes")
async def get_classes():
    """P&ID 심볼 클래스 목록"""
    return {
        "total_classes": len(PID_SYMBOL_CLASSES),
        "classes": PID_SYMBOL_CLASSES,
        "categories": {
            "valve": "밸브",
            "pump": "펌프",
            "instrument": "계기",
            "tank": "탱크/용기",
            "heat_exchanger": "열교환기",
            "compressor": "압축기",
            "piping": "배관 부품",
            "equipment": "장비"
        }
    }


@app.post("/api/v1/process", response_model=ProcessResponse)
async def process(
    file: UploadFile = File(..., description="P&ID 도면 이미지"),
    confidence: float = Form(default=0.10, description="신뢰도 임계값 (0.05-1.0)"),
    slice_height: int = Form(default=512, description="SAHI 슬라이스 높이"),
    slice_width: int = Form(default=512, description="SAHI 슬라이스 너비"),
    overlap_ratio: float = Form(default=0.25, description="슬라이스 오버랩 비율"),
    class_agnostic: bool = Form(default=False, description="Class-agnostic 모드 (False=32클래스 분류)"),
    visualize: bool = Form(default=True, description="결과 시각화")
):
    """
    P&ID 심볼 검출 메인 엔드포인트 (SAHI Enhanced)

    SAHI (Slicing Aided Hyper Inference):
    - 대형 P&ID 도면을 작은 슬라이스로 분할하여 검출
    - 슬라이스 결과를 NMS로 병합하여 최종 결과 생성
    - 작은 심볼도 놓치지 않고 검출

    검출 모드:
    - class_agnostic=True: 모든 심볼을 "Symbol"로 분류 (추천)
    - class_agnostic=False: 30개 클래스로 분류 (밸브, 펌프, 계기 등)
    """
    start_time = time.time()

    try:
        # 이미지 로드
        image_bytes = await file.read()
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        logger.info(f"Processing P&ID image: {file.filename}, size: {image.shape}")
        logger.info(f"SAHI params: slice={slice_height}x{slice_width}, overlap={overlap_ratio}, conf={confidence}")

        # SAHI 기반 심볼 검출
        detections = detect_pid_symbols_sahi(
            image,
            confidence=confidence,
            slice_height=slice_height,
            slice_width=slice_width,
            overlap_ratio=overlap_ratio,
            class_agnostic=class_agnostic
        )
        logger.info(f"Detected {len(detections)} P&ID symbols")

        # 카테고리별 통계
        category_stats = get_category_statistics(detections)

        # 시각화
        visualization_base64 = None
        if visualize and detections:
            vis_image = visualize_detections(image, detections)
            visualization_base64 = numpy_to_base64(vis_image)

        processing_time = time.time() - start_time

        result = {
            "detections": detections,
            "statistics": {
                "total_symbols": len(detections),
                "by_category": category_stats
            },
            "visualization": visualization_base64,
            "image_size": {"width": image.shape[1], "height": image.shape[0]},
            "parameters": {
                "confidence": confidence,
                "slice_height": slice_height,
                "slice_width": slice_width,
                "overlap_ratio": overlap_ratio,
                "class_agnostic": class_agnostic,
                "detection_method": "SAHI"
            }
        }

        return ProcessResponse(
            success=True,
            data=result,
            processing_time=round(processing_time, 3)
        )

    except Exception as e:
        logger.error(f"Processing error: {e}")
        import traceback
        traceback.print_exc()
        return ProcessResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=str(e)
        )


# =====================
# Main
# =====================

if __name__ == "__main__":
    logger.info(f"Starting YOLO P&ID Symbol Detector API (SAHI Enhanced) on port {API_PORT}")
    logger.info(f"Model path: {MODEL_PATH}")
    logger.info(f"SAHI config: slice={SAHI_SLICE_HEIGHT}x{SAHI_SLICE_WIDTH}, overlap={SAHI_OVERLAP_RATIO}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=API_PORT,
        log_level="info"
    )
