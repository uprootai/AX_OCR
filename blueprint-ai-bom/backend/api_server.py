"""
Blueprint AI BOM - Backend API Server

AI 기반 도면 분석 및 BOM 생성 API
"""

import os
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from routers.session_router import router as session_router_api, set_session_service
from routers.detection_router import router as detection_router_api, set_detection_service
from routers.bom_router import router as bom_router_api, set_bom_service
# Analysis 라우터 패키지 (5개 모듈로 분할됨)
from routers.analysis import (
    core_router,
    dimension_router,
    line_router,
    region_router,
    gdt_router,
    set_core_services,
    set_line_services,
    set_region_services,
    set_gdt_services,
)
from routers.verification_router import router as verification_router_api, set_verification_services
from routers.classification_router import router as classification_router_api, set_classification_services
from routers.relation_router import router as relation_router_api, set_relation_services
from routers.feedback_router import router as feedback_router_api, set_feedback_services
from routers.midterm_router import router as midterm_router_api, set_session_service as set_midterm_session_service
from routers.longterm_router import router as longterm_router_api, set_session_service as set_longterm_session_service
from routers.pid_features_router import router as pid_features_router_api, set_pid_features_service
from routers.settings_router import router as settings_router_api
from schemas.session import SessionCreate, SessionResponse
from services.session_service import SessionService
from services.detection_service import DetectionService
from services.bom_service import BOMService
from services.dimension_service import DimensionService
from services.line_detector_service import LineDetectorService
from services.dimension_relation_service import DimensionRelationService
from services.connectivity_analyzer import ConnectivityAnalyzer  # Phase 6: P&ID 연결 분석
from services.region_segmenter import RegionSegmenter  # Phase 5: 영역 분할
from services.gdt_parser import GDTParser  # Phase 7: GD&T 파싱

# 기본 경로 설정 (Docker에서는 /app 기준)
BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
RESULTS_DIR = BASE_DIR / "results"
CONFIG_DIR = BASE_DIR / "config"
MODELS_DIR = BASE_DIR / "models"

# 디렉토리 생성
UPLOAD_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)
CONFIG_DIR.mkdir(exist_ok=True)

# FastAPI 앱 생성
app = FastAPI(
    title="Blueprint AI BOM API",
    description="AI 기반 도면 분석 및 BOM 생성 솔루션 + P&ID 분석 기능",
    version="10.6.0",  # v10.6: P&ID 분석 기능 (밸브, 장비, 체크리스트)
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 서비스 인스턴스 생성
session_service = SessionService(UPLOAD_DIR, RESULTS_DIR)

# YOLO 모델 경로 (존재하면 로드)
model_path = MODELS_DIR / "best.pt"
if not model_path.exists():
    model_path = None

detection_service = DetectionService(model_path=model_path)
bom_service = BOMService(output_dir=RESULTS_DIR)
dimension_service = DimensionService()  # v2: 치수 OCR 서비스
line_detector_service = LineDetectorService()  # v2: 선 검출 서비스
relation_service = DimensionRelationService()  # Phase 2: 치수선 기반 관계 추출
connectivity_analyzer = ConnectivityAnalyzer()  # Phase 6: P&ID 연결 분석
region_segmenter = RegionSegmenter()  # Phase 5: 영역 분할
gdt_parser = GDTParser()  # Phase 7: GD&T 파싱

# 라우터에 서비스 주입
set_session_service(session_service, UPLOAD_DIR)
set_detection_service(detection_service, session_service)
set_bom_service(bom_service, session_service)
# Analysis 패키지 서비스 주입 (5개 라우터)
set_core_services(dimension_service, detection_service, session_service, relation_service)
set_line_services(line_detector_service, connectivity_analyzer)
set_region_services(region_segmenter)
set_gdt_services(gdt_parser)
set_verification_services(session_service)  # v3: Active Learning 검증
set_classification_services(session_service)  # v4: VLM 분류
set_relation_services(session_service, line_detector_service)  # Phase 2: 치수선 기반 관계
set_feedback_services(session_service)  # Phase 8: 피드백 루프
set_midterm_session_service(session_service)  # 중기 로드맵: 용접, 거칠기, 수량, 벌룬
set_longterm_session_service(session_service)  # 장기 로드맵: 영역, 노트, 리비전, VLM
set_pid_features_service(session_service)  # P&ID 분석 기능: 밸브, 장비, 체크리스트

# 라우터 등록 (prefix 없이 - 라우터 내부에 이미 prefix 있음)
app.include_router(session_router_api, tags=["Session"])
app.include_router(detection_router_api, tags=["Detection"])
app.include_router(bom_router_api, tags=["BOM"])
# Analysis 패키지 라우터 등록 (5개 모듈)
app.include_router(core_router, tags=["Analysis Core"])
app.include_router(dimension_router, tags=["Dimensions"])
app.include_router(line_router, tags=["Lines & Connectivity"])
app.include_router(region_router, tags=["Regions"])
app.include_router(gdt_router, tags=["GD&T & Title Block"])
app.include_router(verification_router_api, tags=["Verification"])  # v3: Active Learning
app.include_router(classification_router_api, tags=["Classification"])  # v4: VLM 분류
app.include_router(relation_router_api, tags=["Relations"])  # Phase 2: 치수선 기반 관계
app.include_router(feedback_router_api, tags=["Feedback"])  # Phase 8: 피드백 루프
app.include_router(midterm_router_api, tags=["Mid-term Features"])  # 중기 로드맵: 용접, 거칠기, 수량, 벌룬
app.include_router(longterm_router_api, tags=["Long-term Features"])  # 장기 로드맵: 영역, 노트, 리비전, VLM
app.include_router(pid_features_router_api, tags=["P&ID Features"])  # P&ID 분석 기능: 밸브, 장비, 체크리스트
app.include_router(settings_router_api, tags=["Settings"])  # API 키 설정


@app.get("/")
async def root():
    """API 상태 확인"""
    return {
        "name": "Blueprint AI BOM API",
        "version": "8.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy"}


@app.get("/api/system/gpu")
async def get_gpu_status():
    """GPU 상태 조회"""
    try:
        import subprocess
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total', '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(', ')
            gpu_util = int(parts[0])
            memory_used = int(parts[1])
            memory_total = int(parts[2])
            memory_percent = (memory_used / memory_total) * 100 if memory_total > 0 else 0
            return {
                "available": True,
                "gpu_util": gpu_util,
                "memory_used": memory_used,
                "memory_total": memory_total,
                "memory_percent": round(memory_percent, 1)
            }
    except Exception:
        pass
    return {
        "available": False,
        "gpu_util": 0,
        "memory_used": 0,
        "memory_total": 0,
        "memory_percent": 0
    }


@app.get("/api/system/info")
async def get_system_info():
    """시스템 정보 조회"""
    import json

    # 클래스 정보
    classes_file = BASE_DIR / "classes_info_with_pricing.json"
    class_count = 0
    pricing_count = 0
    if classes_file.exists():
        with open(classes_file, "r", encoding="utf-8") as f:
            classes_data = json.load(f)
            # Dict 형식: {class_name: {모델명, 단가, ...}}
            if isinstance(classes_data, dict):
                class_count = len(classes_data)
                pricing_count = sum(1 for v in classes_data.values() if isinstance(v, dict) and v.get("단가", 0) > 0)
            # List 형식: [{class_name, unit_price, ...}]
            elif isinstance(classes_data, list):
                class_count = len(classes_data)
                pricing_count = sum(1 for c in classes_data if isinstance(c, dict) and c.get("unit_price", 0) > 0)

    # 세션 수
    session_count = len(session_service.list_sessions(limit=1000))

    return {
        "class_count": class_count,
        "pricing_count": pricing_count,
        "session_count": session_count,
        "model_name": "YOLO v11",
        "version": "7.0.0"
    }


@app.post("/api/system/cache/clear")
async def clear_cache(cache_type: str = "all"):
    """캐시 정리"""
    import shutil
    import gc

    cleared = []

    if cache_type in ["all", "uploads"]:
        # 오래된 업로드 파일 정리 (7일 이상)
        import time
        now = time.time()
        for session_dir in UPLOAD_DIR.iterdir():
            if session_dir.is_dir():
                dir_time = session_dir.stat().st_mtime
                if now - dir_time > 7 * 24 * 60 * 60:  # 7일
                    shutil.rmtree(session_dir, ignore_errors=True)
                    cleared.append(session_dir.name)

    if cache_type in ["all", "memory"]:
        # Python 메모리 가비지 컬렉션
        gc.collect()
        cleared.append("memory")

    return {
        "status": "success",
        "cache_type": cache_type,
        "cleared": cleared,
        "message": f"{len(cleared)}개 항목 정리 완료"
    }


# ==================== Test Images API ====================

TEST_DRAWINGS_DIR = BASE_DIR / "test_drawings"

@app.get("/api/test-images")
async def list_test_images():
    """테스트 이미지 목록 조회"""
    if not TEST_DRAWINGS_DIR.exists():
        return {"images": []}

    images = []
    allowed_extensions = {".png", ".jpg", ".jpeg", ".pdf"}

    for file_path in TEST_DRAWINGS_DIR.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in allowed_extensions:
            images.append({
                "filename": file_path.name,
                "path": str(file_path),
                "size": file_path.stat().st_size,
                "type": file_path.suffix.lower()[1:]  # Remove the dot
            })

    return {"images": sorted(images, key=lambda x: x["filename"])}


@app.post("/api/test-images/load")
async def load_test_image(filename: str):
    """테스트 이미지 로드 및 세션 생성"""
    file_path = TEST_DRAWINGS_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="테스트 이미지를 찾을 수 없습니다.")

    # 세션 ID 생성
    session_id = str(uuid.uuid4())

    # 파일 복사
    session_dir = UPLOAD_DIR / session_id
    session_dir.mkdir(exist_ok=True)

    import shutil
    dest_path = session_dir / filename
    shutil.copy(file_path, dest_path)

    # 세션 정보 저장
    session_info = session_service.create_session(
        session_id=session_id,
        filename=filename,
        file_path=str(dest_path)
    )

    return {
        "session_id": session_id,
        "filename": filename,
        "file_path": str(dest_path),
        "status": "uploaded",
        "message": "테스트 이미지 로드 완료"
    }


# ==================== Models API ====================

@app.get("/api/models")
async def list_available_models():
    """사용 가능한 AI 모델 목록"""
    models = [
        {
            "id": "yolo_v11n",
            "name": "YOLOv11 Nano",
            "emoji": "🚀",
            "description": "빠른 검출 속도, 낮은 리소스 사용",
            "accuracy": 0.85,
            "speed": "fast"
        },
        {
            "id": "yolo_v11s",
            "name": "YOLOv11 Small",
            "emoji": "⚡",
            "description": "균형 잡힌 속도와 정확도",
            "accuracy": 0.88,
            "speed": "medium"
        },
        {
            "id": "yolo_v11m",
            "name": "YOLOv11 Medium",
            "emoji": "🎯",
            "description": "높은 정확도, 중간 속도",
            "accuracy": 0.91,
            "speed": "medium"
        },
        {
            "id": "yolo_v11x",
            "name": "YOLOv11 XLarge",
            "emoji": "🔬",
            "description": "최고 정확도, 느린 속도",
            "accuracy": 0.94,
            "speed": "slow"
        }
    ]
    return {"models": models}


# ==================== Ground Truth API ====================

# Reference GT (read-only, from test_drawings)
GT_LABELS_DIR = BASE_DIR / "test_drawings" / "labels"
GT_CLASSES_FILE = BASE_DIR / "test_drawings" / "classes.txt"

# Uploaded GT (writable, for user uploads)
GT_UPLOAD_DIR = BASE_DIR / "uploads" / "gt_labels"


def load_gt_classes() -> list[str]:
    """GT 클래스 목록 로드"""
    if not GT_CLASSES_FILE.exists():
        return []
    with open(GT_CLASSES_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def parse_yolo_label(label_file: Path, img_width: int, img_height: int, classes: list[str]) -> list[dict]:
    """YOLO 형식 라벨 파싱 (normalized -> absolute coords)"""
    if not label_file.exists():
        return []

    labels = []
    with open(label_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            parts = line.split()
            if len(parts) < 5:
                continue

            try:
                class_id = int(parts[0])
                x_center = float(parts[1])
                y_center = float(parts[2])
                width = float(parts[3])
                height = float(parts[4])

                # Convert normalized coords to absolute
                x1 = int((x_center - width / 2) * img_width)
                y1 = int((y_center - height / 2) * img_height)
                x2 = int((x_center + width / 2) * img_width)
                y2 = int((y_center + height / 2) * img_height)

                # Get class name
                class_name = classes[class_id] if class_id < len(classes) else f"class_{class_id}"

                labels.append({
                    "class_id": class_id,
                    "class_name": class_name,
                    "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                    "x_center": x_center,
                    "y_center": y_center,
                    "width": width,
                    "height": height,
                })
            except (ValueError, IndexError):
                continue

    return labels


def find_gt_label_file(base_name: str) -> Path | None:
    """GT 라벨 파일 찾기 (업로드된 파일 우선, 없으면 레퍼런스 파일)"""
    # 업로드된 GT 먼저 확인
    uploaded_file = GT_UPLOAD_DIR / f"{base_name}.txt"
    if uploaded_file.exists():
        return uploaded_file
    # 레퍼런스 GT 확인
    reference_file = GT_LABELS_DIR / f"{base_name}.txt"
    if reference_file.exists():
        return reference_file
    return None


def load_gt_classes_for_file(label_file: Path) -> list[str]:
    """라벨 파일에 해당하는 클래스 목록 로드"""
    # 업로드된 GT인 경우 uploads의 classes.txt 사용
    if label_file.parent == GT_UPLOAD_DIR:
        classes_file = GT_UPLOAD_DIR / "classes.txt"
        if classes_file.exists():
            with open(classes_file, "r", encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip()]
    # 레퍼런스 GT classes
    return load_gt_classes()


@app.get("/api/ground-truth/{filename}")
async def get_ground_truth(filename: str, img_width: int = 1000, img_height: int = 1000):
    """이미지 파일명에 해당하는 Ground Truth 라벨 조회

    Args:
        filename: 이미지 파일명 (예: img_00031.jpg)
        img_width: 이미지 너비 (절대 좌표 변환용)
        img_height: 이미지 높이 (절대 좌표 변환용)
    """
    # Remove extension and find label file
    base_name = Path(filename).stem
    label_file = find_gt_label_file(base_name)

    if not label_file:
        return {
            "filename": filename,
            "has_ground_truth": False,
            "labels": [],
            "count": 0,
            "message": f"GT 라벨 파일을 찾을 수 없습니다: {base_name}.txt"
        }

    classes = load_gt_classes_for_file(label_file)
    labels = parse_yolo_label(label_file, img_width, img_height, classes)

    return {
        "filename": filename,
        "has_ground_truth": True,
        "labels": labels,
        "count": len(labels),
        "classes": classes,
        "label_file": str(label_file.name)
    }


@app.get("/api/ground-truth")
async def list_available_ground_truth():
    """사용 가능한 GT 라벨 목록 조회 (업로드된 파일 + 레퍼런스 파일)"""
    label_files = []
    seen_names = set()

    # 업로드된 GT 먼저 (우선순위 높음)
    if GT_UPLOAD_DIR.exists():
        for f in GT_UPLOAD_DIR.iterdir():
            if f.is_file() and f.suffix == ".txt" and f.name != "classes.txt":
                label_files.append({
                    "filename": f.stem,
                    "label_file": f.name,
                    "size": f.stat().st_size,
                    "source": "uploaded"
                })
                seen_names.add(f.stem)

    # 레퍼런스 GT (업로드된 파일이 없는 경우만)
    if GT_LABELS_DIR.exists():
        for f in GT_LABELS_DIR.iterdir():
            if f.is_file() and f.suffix == ".txt" and f.name != "classes.txt" and not f.name.startswith("README"):
                if f.stem not in seen_names:
                    label_files.append({
                        "filename": f.stem,
                        "label_file": f.name,
                        "size": f.stat().st_size,
                        "source": "reference"
                    })

    classes = load_gt_classes()

    return {
        "labels": sorted(label_files, key=lambda x: x["filename"]),
        "count": len(label_files),
        "classes": classes,
        "classes_count": len(classes)
    }


@app.post("/api/ground-truth/upload")
async def upload_ground_truth(
    file: UploadFile = File(...),
    filename: str = None,
    img_width: int = 1000,
    img_height: int = 1000
):
    """GT 라벨 파일 업로드

    지원 형식:
    - JSON: [{"class_name": "...", "bbox": {"x1": 0, "y1": 0, "x2": 100, "y2": 100}}, ...]
    - TXT (YOLO 형식): class_id x_center y_center width height (per line)
    - XML (Pascal VOC 형식)

    Args:
        file: 업로드할 GT 파일
        filename: 저장할 파일명 (없으면 원본 파일명 사용)
        img_width: 이미지 너비 (좌표 변환용)
        img_height: 이미지 높이 (좌표 변환용)
    """
    import json
    import xml.etree.ElementTree as ET

    # 파일명 결정
    original_name = Path(file.filename).stem
    target_name = filename if filename else original_name
    target_name = Path(target_name).stem  # 확장자 제거

    # GT 업로드 디렉토리 생성 (writable)
    GT_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    content = await file.read()
    content_str = content.decode('utf-8')

    labels = []
    classes = load_gt_classes()

    try:
        # JSON 형식
        if file.filename.endswith('.json'):
            data = json.loads(content_str)
            if isinstance(data, list):
                for item in data:
                    class_name = item.get('class_name', item.get('label', 'unknown'))
                    bbox = item.get('bbox', item.get('bndbox', {}))

                    # class_id 찾기 또는 추가
                    if class_name in classes:
                        class_id = classes.index(class_name)
                    else:
                        classes.append(class_name)
                        class_id = len(classes) - 1

                    # bbox를 YOLO 형식으로 변환 (x_center, y_center, width, height - normalized)
                    x1 = bbox.get('x1', bbox.get('xmin', 0))
                    y1 = bbox.get('y1', bbox.get('ymin', 0))
                    x2 = bbox.get('x2', bbox.get('xmax', 0))
                    y2 = bbox.get('y2', bbox.get('ymax', 0))

                    x_center = ((x1 + x2) / 2) / img_width
                    y_center = ((y1 + y2) / 2) / img_height
                    w = (x2 - x1) / img_width
                    h = (y2 - y1) / img_height

                    labels.append(f"{class_id} {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}")

        # XML (Pascal VOC) 형식
        elif file.filename.endswith('.xml'):
            root = ET.fromstring(content_str)
            for obj in root.findall('object'):
                class_name = obj.find('name').text
                bndbox = obj.find('bndbox')

                if class_name in classes:
                    class_id = classes.index(class_name)
                else:
                    classes.append(class_name)
                    class_id = len(classes) - 1

                x1 = float(bndbox.find('xmin').text)
                y1 = float(bndbox.find('ymin').text)
                x2 = float(bndbox.find('xmax').text)
                y2 = float(bndbox.find('ymax').text)

                x_center = ((x1 + x2) / 2) / img_width
                y_center = ((y1 + y2) / 2) / img_height
                w = (x2 - x1) / img_width
                h = (y2 - y1) / img_height

                labels.append(f"{class_id} {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}")

        # TXT (YOLO) 형식 - 그대로 저장
        elif file.filename.endswith('.txt'):
            labels = [line.strip() for line in content_str.split('\n') if line.strip()]

        else:
            raise HTTPException(status_code=400, detail=f"지원하지 않는 형식: {file.filename}")

        # YOLO 형식으로 저장 (uploads 디렉토리에 저장)
        label_file = GT_UPLOAD_DIR / f"{target_name}.txt"
        with open(label_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(labels))

        # 클래스 파일 저장 (uploads 디렉토리에)
        classes_file = GT_UPLOAD_DIR / "classes.txt"
        with open(classes_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(classes))

        return {
            "success": True,
            "filename": target_name,
            "label_file": str(label_file.name),
            "label_count": len(labels),
            "message": f"GT 라벨 {len(labels)}개가 저장되었습니다."
        }

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"JSON 파싱 오류: {str(e)}")
    except ET.ParseError as e:
        raise HTTPException(status_code=400, detail=f"XML 파싱 오류: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GT 업로드 실패: {str(e)}")


@app.post("/api/ground-truth/compare")
async def compare_with_ground_truth(
    filename: str,
    detections: list[dict],
    img_width: int = 1000,
    img_height: int = 1000,
    iou_threshold: float = 0.3,
    model_type: str = None,
    class_agnostic: bool = False
):
    """검출 결과와 Ground Truth 비교 (TP/FP/FN 계산)

    Args:
        filename: 이미지 파일명
        detections: 검출 결과 리스트 [{class_name, bbox: {x1,y1,x2,y2}}]
        img_width: 이미지 너비
        img_height: 이미지 높이
        iou_threshold: IoU 임계값 (기본 0.3)
        model_type: 모델 타입 (bom_detector 등) - 해당 클래스 파일 사용
        class_agnostic: True면 클래스 무관하게 위치(IoU)만으로 매칭
    """
    # Load GT (업로드된 파일 우선)
    base_name = Path(filename).stem
    label_file = find_gt_label_file(base_name)

    if not label_file:
        return {
            "error": "GT 라벨 파일을 찾을 수 없습니다",
            "has_ground_truth": False,
            "filename": filename,
            "searched_label": f"{base_name}.txt"
        }

    # 모델 타입에 따른 클래스 파일 선택
    if model_type:
        # 업로드된 GT 디렉토리 먼저 확인
        model_classes_file = GT_UPLOAD_DIR / f"classes_{model_type}.txt"
        if not model_classes_file.exists():
            model_classes_file = GT_LABELS_DIR / f"classes_{model_type}.txt"
        if model_classes_file.exists():
            with open(model_classes_file, "r", encoding="utf-8") as f:
                classes = [line.strip() for line in f if line.strip()]
        else:
            classes = load_gt_classes_for_file(label_file)
    else:
        classes = load_gt_classes_for_file(label_file)

    gt_labels = parse_yolo_label(label_file, img_width, img_height, classes)

    # Debug logging
    logger.debug(f"GT Compare: class_agnostic={class_agnostic}, model_type={model_type}")
    logger.debug(f"  filename={filename}, gt_count={len(gt_labels)}, det_count={len(detections)}")

    def calculate_iou(box1: dict, box2: dict) -> float:
        """IoU 계산"""
        x1 = max(box1["x1"], box2["x1"])
        y1 = max(box1["y1"], box2["y1"])
        x2 = min(box1["x2"], box2["x2"])
        y2 = min(box1["y2"], box2["y2"])

        if x2 <= x1 or y2 <= y1:
            return 0.0

        intersection = (x2 - x1) * (y2 - y1)
        area1 = (box1["x2"] - box1["x1"]) * (box1["y2"] - box1["y1"])
        area2 = (box2["x2"] - box2["x1"]) * (box2["y2"] - box2["y1"])
        union = area1 + area2 - intersection

        return intersection / union if union > 0 else 0.0

    # Match detections with GT
    matched_gt = set()
    matched_det = set()
    tp_matches = []

    for i, det in enumerate(detections):
        det_bbox = det.get("bbox", {})
        det_class = det.get("class_name", "")

        best_iou = 0
        best_gt_idx = -1

        for j, gt in enumerate(gt_labels):
            if j in matched_gt:
                continue

            iou = calculate_iou(det_bbox, gt["bbox"])
            gt_class = gt.get("class_name", "")

            # class_agnostic 모드: 위치(IoU)만으로 매칭 (클래스 무시)
            # 일반 모드: 클래스 매칭 + IoU threshold 조건
            if class_agnostic:
                # 위치만 확인
                if iou > best_iou and iou >= iou_threshold:
                    best_iou = iou
                    best_gt_idx = j
                    if iou > 0.5:
                        logger.debug(f"  Match found: det[{i}] <-> gt[{j}], IoU={iou:.3f}")
            else:
                # 클래스도 일치해야 함
                if det_class == gt_class and iou > best_iou and iou >= iou_threshold:
                    best_iou = iou
                    best_gt_idx = j

        if best_gt_idx >= 0:
            matched_gt.add(best_gt_idx)
            matched_det.add(i)
            tp_matches.append({
                "detection_idx": i,
                "gt_idx": best_gt_idx,
                "iou": best_iou,
                "det_class": det_class,
                "gt_class": gt_labels[best_gt_idx]["class_name"],
                "gt_bbox": gt_labels[best_gt_idx]["bbox"],  # GT bbox for frontend cropping
                "class_match": det_class == gt_labels[best_gt_idx]["class_name"]
            })

    # Calculate metrics
    tp = len(tp_matches)
    fp = len(detections) - tp
    fn = len(gt_labels) - tp

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    # FP details (detections that didn't match any GT)
    fp_detections = [detections[i] for i in range(len(detections)) if i not in matched_det]

    # FN details (GT that weren't detected)
    fn_labels = [gt_labels[i] for i in range(len(gt_labels)) if i not in matched_gt]

    return {
        "filename": filename,
        "has_ground_truth": True,
        "metrics": {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": round(precision * 100, 2),
            "recall": round(recall * 100, 2),
            "f1_score": round(f1 * 100, 2),
            "iou_threshold": iou_threshold
        },
        "gt_count": len(gt_labels),
        "detection_count": len(detections),
        "tp_matches": tp_matches,
        "fp_detections": fp_detections,
        "fn_labels": fn_labels
    }


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    도면 파일 업로드

    - 지원 형식: PDF, PNG, JPG, JPEG
    - 최대 크기: 50MB
    """
    # 파일 확장자 검증
    allowed_extensions = {".pdf", ".png", ".jpg", ".jpeg"}
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 파일 형식입니다. 지원 형식: {', '.join(allowed_extensions)}"
        )

    # 세션 ID 생성
    session_id = str(uuid.uuid4())

    # 파일 저장
    session_dir = UPLOAD_DIR / session_id
    session_dir.mkdir(exist_ok=True)

    file_path = session_dir / file.filename

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # 세션 정보 저장
    session_info = session_service.create_session(
        session_id=session_id,
        filename=file.filename,
        file_path=str(file_path)
    )

    return {
        "session_id": session_id,
        "filename": file.filename,
        "file_path": str(file_path),
        "status": "uploaded",
        "message": "파일 업로드 완료. /api/detection/detect 를 호출하여 검출을 시작하세요."
    }


@app.get("/api/config/classes")
async def get_classes():
    """검출 클래스 목록 조회"""
    import json

    classes_file = BASE_DIR / "classes_info_with_pricing.json"

    if not classes_file.exists():
        raise HTTPException(status_code=404, detail="클래스 정보 파일을 찾을 수 없습니다.")

    with open(classes_file, "r", encoding="utf-8") as f:
        classes_data = json.load(f)

    return classes_data


@app.get("/api/config/template")
async def get_template():
    """현재 템플릿 조회"""
    template_file = CONFIG_DIR / "template.json"

    if not template_file.exists():
        return {"message": "템플릿이 설정되지 않았습니다.", "template": None}

    import json
    with open(template_file, "r", encoding="utf-8") as f:
        template = json.load(f)

    return template


@app.get("/api/config/class-examples")
async def get_class_examples():
    """클래스별 참조 이미지 목록"""
    import base64
    import glob

    class_examples_dir = BASE_DIR / "class_examples"

    if not class_examples_dir.exists():
        return {"examples": [], "message": "class_examples 디렉토리가 없습니다."}

    examples = []
    pattern = str(class_examples_dir / "*.jpg")
    files = sorted(glob.glob(pattern))

    for file_path in files:
        try:
            filename = os.path.basename(file_path)

            # 클래스 이름 추출 (class_XX_클래스명.jpg 패턴)
            # 예: class_00_10_BUZZER_HY-256-2(AC220V)_p01.jpg
            parts = filename.split('_', 2)
            if len(parts) >= 3:
                # 나머지 부분에서 _p01.jpg 또는 .jpg 제거
                remaining = parts[2]
                if remaining.endswith('_p01.jpg'):
                    remaining = remaining[:-8]
                elif remaining.endswith('.jpg'):
                    remaining = remaining[:-4]
                class_name = remaining
            else:
                class_name = filename.replace('.jpg', '')

            # 이미지를 base64로 인코딩
            with open(file_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')

            examples.append({
                "class_name": class_name,
                "image_base64": image_data,
                "filename": filename
            })
        except Exception as e:
            logger.warning(f"Error loading example {file_path}: {e}")
            continue

    return {"examples": examples, "count": len(examples)}


@app.delete("/api/sessions/cleanup")
async def cleanup_old_sessions(max_age_hours: int = 24):
    """오래된 세션 정리

    Args:
        max_age_hours: 이 시간보다 오래된 세션 삭제 (기본 24시간)
    """
    from datetime import timedelta
    import shutil

    cleaned_count = 0
    error_count = 0
    cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

    sessions = session_service.list_sessions(limit=1000)

    for session in sessions:
        try:
            created_at = datetime.fromisoformat(session.get("created_at", ""))
            if created_at < cutoff_time:
                session_service.delete_session(session["session_id"])
                cleaned_count += 1
        except Exception as e:
            logger.warning(f"Error cleaning session {session.get('session_id')}: {e}")
            error_count += 1

    return {
        "cleaned_count": cleaned_count,
        "error_count": error_count,
        "message": f"{max_age_hours}시간 이상 된 세션 {cleaned_count}개 삭제됨"
    }


@app.get("/api/sessions/stats")
async def get_sessions_stats():
    """세션 통계"""
    sessions = session_service.list_sessions(limit=1000)

    total = len(sessions)
    by_status = {}

    for session in sessions:
        status = session.get("status", "unknown")
        by_status[status] = by_status.get(status, 0) + 1

    # 가장 오래된 세션
    oldest = None
    if sessions:
        oldest = min(sessions, key=lambda s: s.get("created_at", ""))

    return {
        "total_sessions": total,
        "by_status": by_status,
        "oldest_session": {
            "session_id": oldest.get("session_id") if oldest else None,
            "created_at": oldest.get("created_at") if oldest else None
        } if oldest else None
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=5020,
        reload=True
    )
