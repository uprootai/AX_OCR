"""Config Router - 시스템 설정, 모델, 테스트 이미지, 파일 업로드 API 엔드포인트

시스템 정보, GPU 상태, 캐시 관리, 모델 목록, 클래스 설정,
템플릿, 테스트 이미지, 파일 업로드, 세션 통계/정리 기능 제공
"""

import os
import uuid
import logging
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Config & System"])

# 기본 경로 설정
BASE_DIR = Path(__file__).parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
RESULTS_DIR = BASE_DIR / "results"
CONFIG_DIR = BASE_DIR / "config"
MODELS_DIR = BASE_DIR / "models"
TEST_DRAWINGS_DIR = BASE_DIR / "test_drawings"

# 의존성 주입을 위한 전역 서비스 (api_server.py에서 설정)
_session_service = None


def set_config_services(session_service):
    """서비스 인스턴스 설정"""
    global _session_service
    _session_service = session_service


def get_session_service():
    """세션 서비스 의존성"""
    if _session_service is None:
        raise HTTPException(status_code=500, detail="Session service not initialized")
    return _session_service


# ==================== System Endpoints ====================

@router.get("/system/gpu")
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


@router.get("/system/info")
async def get_system_info():
    """시스템 정보 조회"""
    import json

    session_service = get_session_service()

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


@router.post("/system/cache/clear")
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


# ==================== Test Images Endpoints ====================

@router.get("/test-images")
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


@router.post("/test-images/load")
async def load_test_image(filename: str):
    """테스트 이미지 로드 및 세션 생성"""
    session_service = get_session_service()
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


# ==================== Models Endpoint ====================

@router.get("/models")
async def list_available_models():
    """사용 가능한 AI 모델 목록"""
    models = [
        {
            "id": "yolo_v11n",
            "name": "YOLOv11 Nano",
            "emoji": "\U0001f680",
            "description": "빠른 검출 속도, 낮은 리소스 사용",
            "accuracy": 0.85,
            "speed": "fast"
        },
        {
            "id": "yolo_v11s",
            "name": "YOLOv11 Small",
            "emoji": "\u26a1",
            "description": "균형 잡힌 속도와 정확도",
            "accuracy": 0.88,
            "speed": "medium"
        },
        {
            "id": "yolo_v11m",
            "name": "YOLOv11 Medium",
            "emoji": "\U0001f3af",
            "description": "높은 정확도, 중간 속도",
            "accuracy": 0.91,
            "speed": "medium"
        },
        {
            "id": "yolo_v11x",
            "name": "YOLOv11 XLarge",
            "emoji": "\U0001f52c",
            "description": "최고 정확도, 느린 속도",
            "accuracy": 0.94,
            "speed": "slow"
        }
    ]
    return {"models": models}


# ==================== Upload Endpoint ====================

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    도면 파일 업로드

    - 지원 형식: PDF, PNG, JPG, JPEG
    - 최대 크기: 50MB
    """
    session_service = get_session_service()

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


# ==================== Config Endpoints ====================

@router.get("/config/classes")
async def get_classes():
    """검출 클래스 목록 조회"""
    import json

    classes_file = BASE_DIR / "classes_info_with_pricing.json"

    if not classes_file.exists():
        raise HTTPException(status_code=404, detail="클래스 정보 파일을 찾을 수 없습니다.")

    with open(classes_file, "r", encoding="utf-8") as f:
        classes_data = json.load(f)

    return classes_data


@router.get("/config/template")
async def get_template():
    """현재 템플릿 조회"""
    template_file = CONFIG_DIR / "template.json"

    if not template_file.exists():
        return {"message": "템플릿이 설정되지 않았습니다.", "template": None}

    import json
    with open(template_file, "r", encoding="utf-8") as f:
        template = json.load(f)

    return template


@router.get("/config/class-examples")
async def get_class_examples(drawing_type: str = "electrical"):
    """클래스별 참조 이미지 목록

    Args:
        drawing_type: 도면 타입 ("electrical" 또는 "pid")
    """
    import base64
    import glob

    # drawing_type에 따라 디렉토리 선택
    if drawing_type == "pid":
        class_examples_dir = BASE_DIR / "class_examples_pid"
    else:
        class_examples_dir = BASE_DIR / "class_examples"

    if not class_examples_dir.exists():
        return {"examples": [], "message": f"class_examples 디렉토리가 없습니다. (drawing_type: {drawing_type})"}

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


# ==================== Session Management Endpoints ====================

@router.delete("/sessions/cleanup")
async def cleanup_old_sessions(max_age_hours: int = 24):
    """오래된 세션 정리

    Args:
        max_age_hours: 이 시간보다 오래된 세션 삭제 (기본 24시간)
    """
    from datetime import timedelta

    session_service = get_session_service()

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


@router.get("/sessions/stats")
async def get_sessions_stats():
    """세션 통계"""
    session_service = get_session_service()
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
