"""
YOLO P&ID Symbol Detector API Server
P&ID 심볼 검출 API (밸브, 펌프, 계기 등 50+ 클래스)

기술:
- YOLOv8/v11 기반 객체 검출
- P&ID 전용 심볼 클래스 (ISO 10628, ISA 5.1 표준)
- 심볼 유형별 분류 (밸브, 펌프, 계기, 탱크 등)

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
MODEL_PATH = os.getenv("YOLO_PID_MODEL", "yolov8n.pt")  # 기본 모델 (P&ID 학습 필요)


# =====================
# P&ID Symbol Classes (ISO 10628, ISA 5.1 기반)
# =====================

PID_SYMBOL_CLASSES = {
    # Valves (밸브)
    0: {"name": "gate_valve", "category": "valve", "korean": "게이트 밸브"},
    1: {"name": "globe_valve", "category": "valve", "korean": "글로브 밸브"},
    2: {"name": "ball_valve", "category": "valve", "korean": "볼 밸브"},
    3: {"name": "butterfly_valve", "category": "valve", "korean": "버터플라이 밸브"},
    4: {"name": "check_valve", "category": "valve", "korean": "체크 밸브"},
    5: {"name": "needle_valve", "category": "valve", "korean": "니들 밸브"},
    6: {"name": "plug_valve", "category": "valve", "korean": "플러그 밸브"},
    7: {"name": "relief_valve", "category": "valve", "korean": "릴리프 밸브"},
    8: {"name": "safety_valve", "category": "valve", "korean": "안전 밸브"},
    9: {"name": "control_valve", "category": "valve", "korean": "제어 밸브"},
    10: {"name": "solenoid_valve", "category": "valve", "korean": "솔레노이드 밸브"},
    11: {"name": "three_way_valve", "category": "valve", "korean": "3방 밸브"},

    # Pumps (펌프)
    12: {"name": "centrifugal_pump", "category": "pump", "korean": "원심 펌프"},
    13: {"name": "positive_displacement_pump", "category": "pump", "korean": "용적식 펌프"},
    14: {"name": "gear_pump", "category": "pump", "korean": "기어 펌프"},
    15: {"name": "screw_pump", "category": "pump", "korean": "스크류 펌프"},
    16: {"name": "diaphragm_pump", "category": "pump", "korean": "다이아프램 펌프"},
    17: {"name": "vacuum_pump", "category": "pump", "korean": "진공 펌프"},

    # Instruments (계기)
    18: {"name": "pressure_gauge", "category": "instrument", "korean": "압력계"},
    19: {"name": "temperature_gauge", "category": "instrument", "korean": "온도계"},
    20: {"name": "flow_meter", "category": "instrument", "korean": "유량계"},
    21: {"name": "level_indicator", "category": "instrument", "korean": "레벨 지시기"},
    22: {"name": "pressure_transmitter", "category": "instrument", "korean": "압력 트랜스미터"},
    23: {"name": "temperature_transmitter", "category": "instrument", "korean": "온도 트랜스미터"},
    24: {"name": "flow_transmitter", "category": "instrument", "korean": "유량 트랜스미터"},
    25: {"name": "level_transmitter", "category": "instrument", "korean": "레벨 트랜스미터"},
    26: {"name": "controller", "category": "instrument", "korean": "컨트롤러"},
    27: {"name": "indicator", "category": "instrument", "korean": "인디케이터"},
    28: {"name": "recorder", "category": "instrument", "korean": "레코더"},

    # Tanks & Vessels (탱크/용기)
    29: {"name": "horizontal_tank", "category": "tank", "korean": "수평 탱크"},
    30: {"name": "vertical_tank", "category": "tank", "korean": "수직 탱크"},
    31: {"name": "pressure_vessel", "category": "tank", "korean": "압력 용기"},
    32: {"name": "reactor", "category": "tank", "korean": "반응기"},
    33: {"name": "column", "category": "tank", "korean": "컬럼"},
    34: {"name": "drum", "category": "tank", "korean": "드럼"},

    # Heat Exchangers (열교환기)
    35: {"name": "shell_tube_exchanger", "category": "heat_exchanger", "korean": "쉘앤튜브 열교환기"},
    36: {"name": "plate_exchanger", "category": "heat_exchanger", "korean": "판형 열교환기"},
    37: {"name": "air_cooler", "category": "heat_exchanger", "korean": "공냉식 냉각기"},
    38: {"name": "heater", "category": "heat_exchanger", "korean": "히터"},
    39: {"name": "condenser", "category": "heat_exchanger", "korean": "응축기"},
    40: {"name": "reboiler", "category": "heat_exchanger", "korean": "리보일러"},

    # Compressors & Blowers (압축기/송풍기)
    41: {"name": "compressor", "category": "compressor", "korean": "압축기"},
    42: {"name": "blower", "category": "compressor", "korean": "송풍기"},
    43: {"name": "fan", "category": "compressor", "korean": "팬"},
    44: {"name": "turbine", "category": "compressor", "korean": "터빈"},

    # Piping Components (배관 부품)
    45: {"name": "reducer", "category": "piping", "korean": "레듀서"},
    46: {"name": "elbow", "category": "piping", "korean": "엘보"},
    47: {"name": "tee", "category": "piping", "korean": "티"},
    48: {"name": "flange", "category": "piping", "korean": "플랜지"},
    49: {"name": "strainer", "category": "piping", "korean": "스트레이너"},
    50: {"name": "filter", "category": "piping", "korean": "필터"},
    51: {"name": "trap", "category": "piping", "korean": "트랩"},
    52: {"name": "orifice", "category": "piping", "korean": "오리피스"},

    # Misc (기타)
    53: {"name": "motor", "category": "misc", "korean": "모터"},
    54: {"name": "agitator", "category": "misc", "korean": "교반기"},
    55: {"name": "nozzle", "category": "misc", "korean": "노즐"},
    56: {"name": "blind_flange", "category": "misc", "korean": "블라인드 플랜지"},
    57: {"name": "spectacle_blind", "category": "misc", "korean": "스펙터클 블라인드"},
    58: {"name": "expansion_joint", "category": "misc", "korean": "신축이음"},
    59: {"name": "rupture_disc", "category": "misc", "korean": "파열판"},
}

CATEGORY_COLORS = {
    "valve": (0, 255, 0),        # Green
    "pump": (255, 0, 0),         # Blue
    "instrument": (0, 0, 255),   # Red
    "tank": (255, 255, 0),       # Cyan
    "heat_exchanger": (255, 0, 255),  # Magenta
    "compressor": (0, 255, 255), # Yellow
    "piping": (128, 128, 128),   # Gray
    "misc": (128, 0, 128)        # Purple
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

# YOLO 모델 (lazy loading)
yolo_model = None


def load_yolo_model():
    """YOLO 모델 로드 (필요시)"""
    global yolo_model
    if yolo_model is None:
        try:
            from ultralytics import YOLO
            if os.path.exists(MODEL_PATH):
                yolo_model = YOLO(MODEL_PATH)
                logger.info(f"Loaded custom P&ID model: {MODEL_PATH}")
            else:
                # 기본 모델 사용 (P&ID 학습 전)
                yolo_model = YOLO("yolov8n.pt")
                logger.warning(f"Custom model not found, using default: yolov8n.pt")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            raise
    return yolo_model


def detect_pid_symbols(image: np.ndarray, confidence: float = 0.25,
                        iou: float = 0.45, imgsz: int = 640) -> List[Dict]:
    """
    P&ID 심볼 검출

    Note: 실제 P&ID 심볼 검출을 위해서는 P&ID 데이터셋으로 학습된 모델 필요
    현재는 기본 YOLO 모델로 시연용
    """
    model = load_yolo_model()

    # 추론 실행
    results = model.predict(
        image,
        conf=confidence,
        iou=iou,
        imgsz=imgsz,
        verbose=False
    )

    detections = []
    if results and len(results) > 0:
        result = results[0]
        boxes = result.boxes

        for i, box in enumerate(boxes):
            # 바운딩 박스
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])

            # P&ID 심볼 클래스 매핑 (학습된 모델이면 직접 사용, 아니면 시뮬레이션)
            if cls_id < len(PID_SYMBOL_CLASSES):
                symbol_info = PID_SYMBOL_CLASSES[cls_id]
            else:
                # 기본 YOLO 클래스를 P&ID 심볼로 임시 매핑
                symbol_info = {
                    "name": f"symbol_{cls_id}",
                    "category": "misc",
                    "korean": f"심볼 {cls_id}"
                }

            detection = {
                "id": i,
                "class_id": cls_id,
                "class_name": symbol_info["name"],
                "category": symbol_info["category"],
                "korean_name": symbol_info["korean"],
                "confidence": round(conf, 4),
                "bbox": [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)],
                "center": [round((x1 + x2) / 2, 2), round((y1 + y2) / 2, 2)],
                "width": round(x2 - x1, 2),
                "height": round(y2 - y1, 2)
            }
            detections.append(detection)

    return detections


def visualize_detections(image: np.ndarray, detections: List[Dict]) -> np.ndarray:
    """검출 결과 시각화"""
    vis = image.copy()

    for det in detections:
        x1, y1, x2, y2 = [int(v) for v in det["bbox"]]
        category = det.get("category", "misc")
        color = CATEGORY_COLORS.get(category, (128, 128, 128))

        # 바운딩 박스
        cv2.rectangle(vis, (x1, y1), (x2, y2), color, 2)

        # 레이블
        label = f"{det['korean_name']} ({det['confidence']:.2f})"
        (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(vis, (x1, y1 - 20), (x1 + w, y1), color, -1)
        cv2.putText(vis, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    return vis


def numpy_to_base64(image: np.ndarray) -> str:
    """NumPy 이미지를 Base64로 변환"""
    _, buffer = cv2.imencode('.png', image)
    return base64.b64encode(buffer).decode('utf-8')


def get_category_statistics(detections: List[Dict]) -> Dict[str, int]:
    """카테고리별 통계"""
    stats = {}
    for det in detections:
        cat = det.get("category", "misc")
        stats[cat] = stats.get(cat, 0) + 1
    return stats


# =====================
# FastAPI App
# =====================

app = FastAPI(
    title="YOLO P&ID Symbol Detector API",
    description="P&ID 심볼 검출 API (밸브, 펌프, 계기 등 50+ 클래스)",
    version="1.0.0"
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
        version="1.0.0",
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
        "name": "YOLO P&ID",
        "display_name": "P&ID Symbol Detector",
        "version": "1.0.0",
        "description": "P&ID 심볼 검출 API (밸브, 펌프, 계기 등 50+ 클래스)",
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
            {"name": "confidence", "type": "number", "min": 0.1, "max": 1.0, "default": 0.25, "description": "신뢰도 임계값"},
            {"name": "iou", "type": "number", "min": 0.1, "max": 1.0, "default": 0.45, "description": "IoU 임계값"},
            {"name": "imgsz", "type": "select", "options": [320, 640, 1280], "default": 640, "description": "입력 이미지 크기"},
            {"name": "visualize", "type": "boolean", "default": True, "description": "결과 시각화"}
        ],
        "symbol_classes": len(PID_SYMBOL_CLASSES),
        "supported_categories": list(set(s["category"] for s in PID_SYMBOL_CLASSES.values()))
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
            "compressor": "압축기/송풍기",
            "piping": "배관 부품",
            "misc": "기타"
        }
    }


@app.post("/api/v1/process", response_model=ProcessResponse)
async def process(
    file: UploadFile = File(..., description="P&ID 도면 이미지"),
    confidence: float = Form(default=0.25, description="신뢰도 임계값 (0.1-1.0)"),
    iou: float = Form(default=0.45, description="IoU 임계값 (0.1-1.0)"),
    imgsz: int = Form(default=640, description="입력 이미지 크기"),
    visualize: bool = Form(default=True, description="결과 시각화")
):
    """
    P&ID 심볼 검출 메인 엔드포인트

    검출 가능한 심볼:
    - 밸브 (12종): 게이트, 글로브, 볼, 버터플라이, 체크, 제어밸브 등
    - 펌프 (6종): 원심, 기어, 다이아프램 등
    - 계기 (11종): 압력계, 온도계, 유량계, 트랜스미터 등
    - 탱크 (6종): 수평/수직 탱크, 압력용기, 반응기 등
    - 열교환기 (6종): 쉘앤튜브, 판형, 공냉기 등
    - 기타 (19종): 압축기, 배관부품, 모터 등
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

        # 심볼 검출
        detections = detect_pid_symbols(image, confidence, iou, imgsz)
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
                "iou": iou,
                "imgsz": imgsz
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
    logger.info(f"Starting YOLO P&ID Symbol Detector API on port {API_PORT}")
    logger.info(f"Supported symbol classes: {len(PID_SYMBOL_CLASSES)}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=API_PORT,
        log_level="info"
    )
