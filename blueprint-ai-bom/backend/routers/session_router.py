"""Session Router - 세션 관리 API 엔드포인트 (업로드/CRUD/목록/상태)"""

import uuid
import base64
import json
import logging
import aiofiles
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Query

from services.image_utils import resize_image_if_needed

from schemas.session import (
    SessionResponse,
    SessionDetail,
    SessionStatus,
)
from schemas.classification import DrawingType

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/sessions", tags=["sessions"])


# 의존성 주입을 위한 전역 서비스 (api_server.py에서 설정)
_session_service = None
_upload_dir = None


def set_session_service(service, upload_dir: Path):
    """서비스 인스턴스 설정"""
    global _session_service, _upload_dir
    _session_service = service
    _upload_dir = upload_dir


def get_session_service():
    """세션 서비스 의존성"""
    if _session_service is None:
        raise HTTPException(status_code=500, detail="Session service not initialized")
    return _session_service


@router.post("/upload", response_model=SessionResponse)
async def upload_image(
    file: UploadFile = File(...),
    drawing_type: str = Query(default="auto", description="도면 타입 (빌더에서 설정)"),
    features: str = Query(default="", description="활성화된 기능 목록 (쉼표 구분)"),
    project_id: Optional[str] = Query(default=None, description="프로젝트 ID"),
    metadata_json: Optional[str] = Query(default=None, description="BOM 메타데이터 (JSON 문자열)")
):
    """이미지 업로드 및 새 세션 생성

    Args:
        file: 업로드할 이미지 파일
        drawing_type: 도면 타입 (auto, mechanical, pid, assembly, electrical, architectural)
        features: 활성화된 기능 목록 (예: "symbol_detection,bom_generation")
        project_id: 프로젝트 ID (BOM 워크플로우에서 사용)
        metadata_json: BOM 메타데이터 JSON 문자열
    """
    service = get_session_service()

    # 파일 확장자 검증
    allowed_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 파일 형식입니다. 허용: {', '.join(allowed_extensions)}"
        )

    # drawing_type 유효성 검사
    try:
        dt = DrawingType(drawing_type)
    except ValueError:
        dt = DrawingType.AUTO

    # 세션 ID 생성
    session_id = str(uuid.uuid4())

    # 파일 저장
    session_dir = _upload_dir / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    file_path = session_dir / f"original{file_ext}"

    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    # 이미지 크기 추출 및 필요 시 리사이즈 (ML 모델 최적화)
    from PIL import Image
    try:
        # 대용량 이미지 자동 리사이즈 (max 8000px, 64MP)
        resize_result = resize_image_if_needed(file_path)
        if resize_result["resized"]:
            logger.info(
                f"[Session] 이미지 자동 리사이즈: "
                f"{resize_result['original_size']} → {resize_result['new_size']}"
            )
        image_width, image_height = resize_result["new_size"]
        logger.info(f"[Session] Image size: {image_width}x{image_height}")
    except Exception as e:
        logger.warning(f"[Session] Failed to process image: {e}")
        image_width, image_height = None, None

    # features 파싱 (쉼표 구분 문자열 → 리스트)
    features_list = [f.strip() for f in features.split(",") if f.strip()] if features else []

    # metadata 파싱 (JSON 문자열 → dict)
    metadata = None
    if metadata_json:
        try:
            metadata = json.loads(metadata_json)
        except json.JSONDecodeError:
            logger.warning(f"[Session] Invalid metadata JSON: {metadata_json[:100]}")

    # 세션 생성 (drawing_type, features, 이미지 크기, project_id, metadata 포함)
    session = service.create_session(
        session_id=session_id,
        filename=file.filename,
        file_path=str(file_path),
        drawing_type=dt.value,
        image_width=image_width,
        image_height=image_height,
        features=features_list,
        project_id=project_id,
        metadata=metadata,
    )

    return SessionResponse(**session)


@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    limit: int = Query(default=50, ge=1, le=100),
    project_id: Optional[str] = Query(default=None, description="프로젝트 ID 필터")
):
    """세션 목록 조회"""
    service = get_session_service()
    if project_id:
        sessions = service.list_sessions_by_project(project_id, limit=limit)
    else:
        sessions = service.list_sessions(limit=limit)
    return [SessionResponse(**s) for s in sessions]


@router.get("/{session_id}", response_model=SessionDetail)
async def get_session(session_id: str, include_image: bool = Query(default=False)):
    """세션 상세 조회"""
    service = get_session_service()
    session = service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # 이미지 base64 처리
    if include_image and session.get("file_path"):
        # 이미지 포함 요청 시 파일에서 로드
        try:
            file_path = Path(session["file_path"])
            if file_path.exists():
                with open(file_path, "rb") as f:
                    image_data = f.read()
                    session["image_base64"] = base64.b64encode(image_data).decode("utf-8")
        except Exception:
            pass
    else:
        # 이미지 미포함 시 명시적으로 제거 (저장된 데이터에 있을 수 있음)
        session.pop("image_base64", None)

    # 커스텀 단가 파일 존재 여부 확인
    if session.get("file_path"):
        pricing_path = Path(session["file_path"]).parent / "pricing.json"
        session["has_custom_pricing"] = pricing_path.exists()
    else:
        session["has_custom_pricing"] = False

    return SessionDetail(**session)


@router.patch("/{session_id}")
async def update_session(session_id: str, updates: dict):
    """세션 정보 업데이트 (이미지 크기 등)"""
    service = get_session_service()
    session = service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # 허용된 필드만 업데이트 (features, ocr_texts, connections, texts, table_results, metadata 추가)
    allowed_fields = {"image_width", "image_height", "status", "features", "ocr_texts", "connections", "drawing_type", "drawing_type_source", "texts", "texts_count", "tables_count", "table_regions_count", "table_results", "metadata", "project_id", "model_type", "template_id"}
    filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}

    if filtered_updates:
        service.update_session(session_id, filtered_updates)

    return {"status": "updated", "session_id": session_id, "updated_fields": list(filtered_updates.keys())}


@router.delete("")
async def delete_all_sessions():
    """모든 세션 삭제"""
    service = get_session_service()
    deleted_count = service.delete_all_sessions()
    return {"status": "deleted", "deleted_count": deleted_count}


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """세션 삭제"""
    service = get_session_service()
    session = service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    service.delete_session(session_id)

    return {"status": "deleted", "session_id": session_id}


@router.get("/{session_id}/image")
async def get_session_image(session_id: str):
    """세션 이미지 조회 (base64)"""
    service = get_session_service()
    session = service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    file_path = Path(session.get("file_path", ""))
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="이미지 파일을 찾을 수 없습니다")

    with open(file_path, "rb") as f:
        image_data = f.read()

    # MIME 타입 결정
    ext = file_path.suffix.lower()
    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".bmp": "image/bmp",
        ".tiff": "image/tiff",
        ".tif": "image/tiff",
    }
    mime_type = mime_types.get(ext, "application/octet-stream")

    return {
        "session_id": session_id,
        "filename": session.get("filename"),
        "mime_type": mime_type,
        "image_base64": base64.b64encode(image_data).decode("utf-8"),
    }
