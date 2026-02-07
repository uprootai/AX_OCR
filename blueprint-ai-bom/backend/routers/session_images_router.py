"""Session Images Router - 다중 이미지 관리/벌크 업로드/리뷰 API 엔드포인트

Phase 2C: 다중 이미지 세션 API
"""

import uuid
import base64
import logging
import aiofiles
import zipfile
from io import BytesIO
from pathlib import Path
from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File, Query

from services.image_utils import resize_image_if_needed

from schemas.session import (
    SessionImage,
    ImageReviewUpdate,
    BulkReviewRequest,
    SessionImageProgress,
)

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


# =============================================================================
# Phase 2C: 다중 이미지 세션 API
# =============================================================================

@router.post("/{session_id}/images", response_model=SessionImage)
async def add_image_to_session(
    session_id: str,
    file: UploadFile = File(...),
):
    """세션에 이미지 추가

    Args:
        session_id: 세션 ID
        file: 업로드할 이미지 파일

    Returns:
        SessionImage: 추가된 이미지 정보
    """
    service = get_session_service()
    session = service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # 파일 확장자 검증
    allowed_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 파일 형식입니다. 허용: {', '.join(allowed_extensions)}"
        )

    # 이미지 ID 생성
    image_id = str(uuid.uuid4())

    # 파일 저장
    session_dir = _upload_dir / session_id / "images"
    session_dir.mkdir(parents=True, exist_ok=True)

    file_path = session_dir / f"{image_id}{file_ext}"

    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    # 이미지 크기 추출 및 필요 시 리사이즈
    from PIL import Image
    try:
        # 대용량 이미지 자동 리사이즈
        resize_result = resize_image_if_needed(file_path)
        if resize_result["resized"]:
            logger.info(f"[Session] 추가 이미지 자동 리사이즈: {resize_result['original_size']} → {resize_result['new_size']}")
        image_width, image_height = resize_result["new_size"]

        # 썸네일 생성
        thumbnail_base64 = None
        try:
            with Image.open(file_path) as img:
                img.thumbnail((150, 150))
                buffer = BytesIO()
                img.save(buffer, format="JPEG", quality=75)
                thumbnail_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        except Exception as e:
            logger.warning(f"[Session] Failed to create thumbnail: {e}")
    except Exception as e:
        logger.warning(f"[Session] Failed to process image: {e}")
        image_width, image_height = None, None
        thumbnail_base64 = None

    # 이미지 추가
    new_image = service.add_image(
        session_id=session_id,
        image_id=image_id,
        filename=file.filename,
        file_path=str(file_path),
        image_width=image_width,
        image_height=image_height,
        thumbnail_base64=thumbnail_base64,
    )

    if not new_image:
        raise HTTPException(status_code=500, detail="이미지 추가에 실패했습니다")

    logger.info(f"[Session] Image added: {image_id} to session {session_id}")

    return SessionImage(**new_image)


@router.get("/{session_id}/images", response_model=List[SessionImage])
async def list_session_images(session_id: str):
    """세션의 이미지 목록 조회

    Args:
        session_id: 세션 ID

    Returns:
        List[SessionImage]: 이미지 목록
    """
    service = get_session_service()
    session = service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    images = service.get_images(session_id)
    return [SessionImage(**img) for img in images]


@router.get("/{session_id}/images/{image_id}", response_model=SessionImage)
async def get_session_image_detail(
    session_id: str,
    image_id: str,
    include_detections: bool = Query(default=True, description="검출 결과 포함 여부"),
):
    """세션의 특정 이미지 조회

    Args:
        session_id: 세션 ID
        image_id: 이미지 ID
        include_detections: 검출 결과 포함 여부

    Returns:
        SessionImage: 이미지 정보
    """
    service = get_session_service()
    session = service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    image = service.get_image(session_id, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다")

    if not include_detections:
        image = {**image, "detections": []}

    return SessionImage(**image)


@router.get("/{session_id}/images/{image_id}/data")
async def get_session_image_data(
    session_id: str,
    image_id: str,
):
    """세션의 특정 이미지 데이터 조회 (base64)

    다중 이미지 세션에서 특정 이미지의 전체 데이터를 반환합니다.

    Args:
        session_id: 세션 ID
        image_id: 이미지 ID

    Returns:
        이미지 데이터 (base64)
    """
    service = get_session_service()
    session = service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    image = service.get_image(session_id, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다")

    file_path = Path(image.get("file_path", ""))
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
        "image_id": image_id,
        "filename": image.get("filename"),
        "mime_type": mime_type,
        "image_base64": base64.b64encode(image_data).decode("utf-8"),
        "image_width": image.get("image_width"),
        "image_height": image.get("image_height"),
    }


@router.patch("/{session_id}/images/{image_id}/review")
async def update_image_review_status(
    session_id: str,
    image_id: str,
    review: ImageReviewUpdate,
):
    """이미지 검토 상태 업데이트

    Args:
        session_id: 세션 ID
        image_id: 이미지 ID
        review: 검토 상태 업데이트 정보

    Returns:
        SessionImage: 업데이트된 이미지 정보
    """
    service = get_session_service()
    session = service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    image = service.get_image(session_id, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다")

    updated_image = service.update_image_review(
        session_id=session_id,
        image_id=image_id,
        review_status=review.review_status.value,
        reviewed_by=review.reviewed_by,
        review_notes=review.review_notes,
    )

    if not updated_image:
        raise HTTPException(status_code=500, detail="이미지 검토 상태 업데이트에 실패했습니다")

    logger.info(f"[Session] Image review updated: {image_id} -> {review.review_status}")

    return SessionImage(**updated_image)


@router.delete("/{session_id}/images/{image_id}")
async def delete_session_image(session_id: str, image_id: str):
    """세션의 이미지 삭제

    Args:
        session_id: 세션 ID
        image_id: 이미지 ID

    Returns:
        삭제 결과
    """
    service = get_session_service()
    session = service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    image = service.get_image(session_id, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다")

    success = service.delete_image(session_id, image_id)

    if not success:
        raise HTTPException(status_code=500, detail="이미지 삭제에 실패했습니다")

    logger.info(f"[Session] Image deleted: {image_id} from session {session_id}")

    return {"status": "deleted", "image_id": image_id}


@router.get("/{session_id}/progress", response_model=SessionImageProgress)
async def get_session_image_progress(session_id: str):
    """세션의 이미지 진행률 조회

    Args:
        session_id: 세션 ID

    Returns:
        SessionImageProgress: 진행률 정보
    """
    service = get_session_service()
    session = service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    progress = service.get_image_progress(session_id)
    return progress


@router.post("/{session_id}/images/bulk-upload")
async def bulk_upload_images(
    session_id: str,
    files: List[UploadFile] = File(...),
):
    """세션에 여러 이미지 일괄 업로드 (ZIP 파일 지원)

    Args:
        session_id: 세션 ID
        files: 업로드할 이미지 파일 목록 (이미지 또는 ZIP 파일)

    Returns:
        업로드 결과
    """
    service = get_session_service()
    session = service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    allowed_image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}
    uploaded = []
    failed = []

    async def process_image(content: bytes, filename: str, original_filename: str = None):
        """이미지 처리 헬퍼 함수"""
        file_ext = Path(filename).suffix.lower()
        display_name = original_filename or filename

        if file_ext not in allowed_image_extensions:
            failed.append({
                "filename": display_name,
                "error": f"지원하지 않는 파일 형식: {file_ext}"
            })
            return

        try:
            # 이미지 ID 생성
            image_id = str(uuid.uuid4())

            # 파일 저장
            session_dir = _upload_dir / session_id / "images"
            session_dir.mkdir(parents=True, exist_ok=True)

            file_path = session_dir / f"{image_id}{file_ext}"

            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)

            # 이미지 크기 추출 및 필요 시 리사이즈
            try:
                resize_result = resize_image_if_needed(file_path)
                if resize_result["resized"]:
                    logger.info(f"[Session] 벌크 업로드 이미지 리사이즈: {resize_result['original_size']} → {resize_result['new_size']}")
                image_width, image_height = resize_result["new_size"]
            except Exception:
                image_width, image_height = None, None

            # 이미지 추가
            new_image = service.add_image(
                session_id=session_id,
                image_id=image_id,
                filename=display_name,
                file_path=str(file_path),
                image_width=image_width,
                image_height=image_height,
            )

            if new_image:
                uploaded.append({
                    "image_id": image_id,
                    "filename": display_name,
                })
            else:
                failed.append({
                    "filename": display_name,
                    "error": "이미지 추가 실패"
                })
        except Exception as e:
            failed.append({
                "filename": display_name,
                "error": str(e)
            })

    for file in files:
        file_ext = Path(file.filename).suffix.lower()

        # ZIP 파일 처리
        if file_ext == ".zip":
            try:
                content = await file.read()
                with zipfile.ZipFile(BytesIO(content), 'r') as zip_ref:
                    for zip_info in zip_ref.infolist():
                        # 디렉토리는 건너뛰기
                        if zip_info.is_dir():
                            continue

                        inner_filename = Path(zip_info.filename).name
                        inner_ext = Path(inner_filename).suffix.lower()

                        # 숨김 파일이나 macOS 메타데이터 건너뛰기
                        if inner_filename.startswith('.') or '__MACOSX' in zip_info.filename:
                            continue

                        # 이미지 파일만 처리
                        if inner_ext in allowed_image_extensions:
                            try:
                                image_content = zip_ref.read(zip_info.filename)
                                await process_image(
                                    image_content,
                                    inner_filename,
                                    f"{file.filename}/{inner_filename}"
                                )
                            except Exception as e:
                                failed.append({
                                    "filename": f"{file.filename}/{inner_filename}",
                                    "error": str(e)
                                })
                logger.info(f"[Session] Processed ZIP file: {file.filename}")
            except zipfile.BadZipFile:
                failed.append({
                    "filename": file.filename,
                    "error": "잘못된 ZIP 파일입니다"
                })
            except Exception as e:
                failed.append({
                    "filename": file.filename,
                    "error": f"ZIP 처리 오류: {str(e)}"
                })
        else:
            # 일반 이미지 파일 처리
            content = await file.read()
            await process_image(content, file.filename)

    logger.info(f"[Session] Bulk upload: {len(uploaded)} succeeded, {len(failed)} failed")

    return {
        "session_id": session_id,
        "uploaded_count": len(uploaded),
        "failed_count": len(failed),
        "uploaded": uploaded,
        "failed": failed,
    }


@router.post("/{session_id}/images/bulk-review")
async def bulk_review_images(
    session_id: str,
    request: BulkReviewRequest,
):
    """여러 이미지 일괄 검토

    Args:
        session_id: 세션 ID
        request: 일괄 검토 요청 (image_ids, review_status, reviewed_by)

    Returns:
        검토 결과
    """
    service = get_session_service()
    session = service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    updated = []
    failed = []

    for image_id in request.image_ids:
        try:
            result = service.update_image_review(
                session_id=session_id,
                image_id=image_id,
                review_status=request.review_status.value,
                reviewed_by=request.reviewed_by,
            )
            if result:
                updated.append(image_id)
            else:
                failed.append({"image_id": image_id, "error": "이미지를 찾을 수 없습니다"})
        except Exception as e:
            failed.append({"image_id": image_id, "error": str(e)})

    logger.info(f"[Session] Bulk review: {len(updated)} updated, {len(failed)} failed")

    return {
        "session_id": session_id,
        "updated_count": len(updated),
        "failed_count": len(failed),
        "updated": updated,
        "failed": failed,
        "new_status": request.review_status.value,
    }
