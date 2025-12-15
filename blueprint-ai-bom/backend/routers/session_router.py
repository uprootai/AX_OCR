"""Session Router - 세션 관리 API 엔드포인트"""

import os
import uuid
import base64
import aiofiles
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Query

from schemas.session import SessionResponse, SessionDetail, SessionStatus


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
async def upload_image(file: UploadFile = File(...)):
    """이미지 업로드 및 새 세션 생성"""
    service = get_session_service()

    # 파일 확장자 검증
    allowed_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 파일 형식입니다. 허용: {', '.join(allowed_extensions)}"
        )

    # 세션 ID 생성
    session_id = str(uuid.uuid4())

    # 파일 저장
    session_dir = _upload_dir / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    file_path = session_dir / f"original{file_ext}"

    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    # 세션 생성
    session = service.create_session(
        session_id=session_id,
        filename=file.filename,
        file_path=str(file_path)
    )

    return SessionResponse(**session)


@router.get("", response_model=List[SessionResponse])
async def list_sessions(limit: int = Query(default=50, ge=1, le=100)):
    """세션 목록 조회"""
    service = get_session_service()
    sessions = service.list_sessions(limit=limit)
    return [SessionResponse(**s) for s in sessions]


@router.get("/{session_id}", response_model=SessionDetail)
async def get_session(session_id: str, include_image: bool = Query(default=False)):
    """세션 상세 조회"""
    service = get_session_service()
    session = service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # 이미지 base64 인코딩 (옵션)
    if include_image and session.get("file_path"):
        try:
            file_path = Path(session["file_path"])
            if file_path.exists():
                with open(file_path, "rb") as f:
                    image_data = f.read()
                    session["image_base64"] = base64.b64encode(image_data).decode("utf-8")
        except Exception:
            pass

    return SessionDetail(**session)


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
