"""Session Router - 세션 관리 API 엔드포인트"""

import os
import uuid
import base64
import json
import logging
import aiofiles
import zipfile
import tempfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from schemas.session import (
    SessionResponse,
    SessionDetail,
    SessionStatus,
    SessionImage,
    ImageReviewStatus,
    ImageReviewUpdate,
    BulkReviewRequest,
    SessionImageProgress,
)
from schemas.workflow_session import (
    WorkflowSessionCreate,
    WorkflowSessionResponse,
    WorkflowSessionDetail,
    WorkflowExecuteRequest,
    WorkflowExecuteResponse,
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
    features: str = Query(default="", description="활성화된 기능 목록 (쉼표 구분)")
):
    """이미지 업로드 및 새 세션 생성

    Args:
        file: 업로드할 이미지 파일
        drawing_type: 도면 타입 (auto, mechanical, pid, assembly, electrical, architectural)
        features: 활성화된 기능 목록 (예: "symbol_detection,bom_generation")
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

    # 이미지 크기 추출
    from PIL import Image
    try:
        with Image.open(file_path) as img:
            image_width, image_height = img.size
        logger.info(f"[Session] Image size extracted: {image_width}x{image_height}")
    except Exception as e:
        logger.warning(f"[Session] Failed to extract image size: {e}")
        image_width, image_height = None, None

    # features 파싱 (쉼표 구분 문자열 → 리스트)
    features_list = [f.strip() for f in features.split(",") if f.strip()] if features else []

    # 세션 생성 (drawing_type, features, 이미지 크기 포함)
    session = service.create_session(
        session_id=session_id,
        filename=file.filename,
        file_path=str(file_path),
        drawing_type=dt.value,
        image_width=image_width,
        image_height=image_height,
        features=features_list
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


@router.patch("/{session_id}")
async def update_session(session_id: str, updates: dict):
    """세션 정보 업데이트 (이미지 크기 등)"""
    service = get_session_service()
    session = service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # 허용된 필드만 업데이트 (features, ocr_texts, connections 추가)
    allowed_fields = {"image_width", "image_height", "status", "features", "ocr_texts", "connections", "drawing_type", "drawing_type_source"}
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


# =============================================================================
# Phase 2G: 워크플로우 세션 API (BlueprintFlow → 고객 배포)
# =============================================================================

@router.post("/from-workflow", response_model=WorkflowSessionResponse)
async def create_session_from_workflow(
    request: WorkflowSessionCreate,
):
    """BlueprintFlow 워크플로우로부터 잠긴 세션 생성

    Args:
        request: 워크플로우 세션 생성 요청

    Returns:
        WorkflowSessionResponse: 생성된 세션 정보 (공유 URL, 접근 토큰 포함)
    """
    service = get_session_service()

    session = service.create_locked_session(
        workflow_name=request.name,
        workflow_definition={
            "name": request.name,
            "description": request.description,
            "nodes": request.nodes,
            "edges": request.edges,
        },
        lock_level=request.lock_level.value,
        allowed_parameters=request.allowed_parameters,
        customer_name=request.customer_name,
        expires_in_days=request.expires_in_days,
    )

    # 만료 시간 파싱
    from datetime import datetime as dt
    expires_at_str = session.get("expires_at", "")
    try:
        expires_at = dt.fromisoformat(expires_at_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        expires_at = dt.now()

    logger.info(f"[WorkflowSession] Created locked session: {session['session_id']} for {request.customer_name}")

    return WorkflowSessionResponse(
        session_id=session["session_id"],
        share_url=f"/customer/session/{session['session_id']}",
        access_token=session["access_token"],
        expires_at=expires_at,
        workflow_name=request.name,
    )


@router.get("/{session_id}/workflow", response_model=WorkflowSessionDetail)
async def get_session_workflow(
    session_id: str,
    access_token: Optional[str] = Query(default=None, description="접근 토큰"),
):
    """세션의 워크플로우 정의 조회 (잠금 상태 포함)

    Args:
        session_id: 세션 ID
        access_token: 접근 토큰 (선택)

    Returns:
        WorkflowSessionDetail: 워크플로우 정보
    """
    service = get_session_service()
    session = service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # 접근 권한 검증
    if not service.validate_session_access(session_id, access_token):
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")

    # 만료 시간 파싱
    from datetime import datetime as dt
    expires_at_str = session.get("expires_at")
    expires_at = None
    if expires_at_str:
        try:
            expires_at = dt.fromisoformat(expires_at_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            pass

    return WorkflowSessionDetail(
        session_id=session_id,
        workflow_definition=session.get("workflow_definition"),
        workflow_locked=session.get("workflow_locked", False),
        lock_level=session.get("lock_level", "none"),
        allowed_parameters=session.get("allowed_parameters", []),
        customer_name=session.get("customer_name"),
        access_token=session.get("access_token"),
        expires_at=expires_at,
    )


@router.post("/{session_id}/execute", response_model=WorkflowExecuteResponse)
async def execute_session_workflow(
    session_id: str,
    request: WorkflowExecuteRequest,
    access_token: Optional[str] = Query(default=None, description="접근 토큰"),
):
    """세션 워크플로우 실행

    Args:
        session_id: 세션 ID
        request: 워크플로우 실행 요청 (이미지 ID, 파라미터)
        access_token: 접근 토큰 (선택)

    Returns:
        WorkflowExecuteResponse: 실행 결과
    """
    service = get_session_service()
    session = service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # 접근 권한 검증
    if not service.validate_session_access(session_id, access_token):
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")

    # 파라미터 수정 권한 검증
    if request.parameters:
        valid, error_msg = service.validate_parameter_modification(session_id, request.parameters)
        if not valid:
            raise HTTPException(status_code=403, detail=error_msg)

    # TODO: Gateway API로 워크플로우 실행 위임
    # 현재는 상태만 업데이트
    service.update_session(session_id, {"status": SessionStatus.DETECTING})

    execution_id = str(uuid.uuid4())

    logger.info(f"[WorkflowSession] Executing workflow for session {session_id}, images: {len(request.image_ids)}")

    return WorkflowExecuteResponse(
        execution_id=execution_id,
        session_id=session_id,
        status="running",
        image_count=len(request.image_ids),
        message="워크플로우 실행이 시작되었습니다",
    )


# =============================================================================
# Session Export/Import API
# =============================================================================

class SessionExportData(BaseModel):
    """세션 Export 데이터 구조"""
    export_version: str = "1.0"
    export_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

    # 세션 메타데이터
    session_metadata: dict = Field(default_factory=dict)

    # 검출 결과
    detections: List[dict] = Field(default_factory=list)

    # 검증 상태
    verification_status: dict = Field(default_factory=dict)

    # BOM 데이터
    bom_data: Optional[dict] = None

    # P&ID 특화 데이터 (있는 경우)
    pid_valves: Optional[List[dict]] = None
    pid_equipment: Optional[List[dict]] = None
    pid_checklist: Optional[List[dict]] = None
    pid_deviations: Optional[List[dict]] = None

    # 이미지 데이터 (base64)
    image_data: Optional[dict] = None


class SessionImportRequest(BaseModel):
    """세션 Import 요청"""
    export_data: dict  # SessionExportData 형태의 dict
    new_session_id: Optional[str] = None  # 지정하지 않으면 자동 생성


@router.get("/{session_id}/export/json")
async def export_session_json(
    session_id: str,
    include_image: bool = Query(default=True, description="이미지 포함 여부"),
    include_rejected: bool = Query(default=True, description="거부된 항목 포함 여부")
):
    """세션 JSON Export

    세션의 모든 데이터를 JSON 형태로 내보냅니다.
    다른 환경에서 import하여 동일한 세션을 재현할 수 있습니다.

    Args:
        session_id: 세션 ID
        include_image: 이미지 base64 포함 여부 (기본: True)
        include_rejected: 거부된 항목 포함 여부 (기본: True)

    Returns:
        StreamingResponse: JSON 파일 다운로드
    """
    service = get_session_service()
    session = service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # 필터링: rejected 제외
    detections = session.get("detections", [])
    verification_status = session.get("verification_status", {})

    if not include_rejected:
        detections = [d for d in detections if verification_status.get(d.get("id")) != "rejected"]
        verification_status = {k: v for k, v in verification_status.items() if v != "rejected"}

    # Export 데이터 구성
    export_data = {
        "export_version": "1.0",
        "export_timestamp": datetime.now().isoformat(),
        "session_metadata": {
            "original_session_id": session_id,
            "filename": session.get("filename"),
            "status": session.get("status"),
            "created_at": session.get("created_at"),
            "updated_at": session.get("updated_at"),
            "drawing_type": session.get("drawing_type", "auto"),
            "drawing_type_source": session.get("drawing_type_source", "builder"),
            "drawing_type_confidence": session.get("drawing_type_confidence"),
            "features": session.get("features", []),
            "image_width": session.get("image_width"),
            "image_height": session.get("image_height"),
            "detection_count": len(detections),
            "verified_count": session.get("verified_count", 0),
            "approved_count": session.get("approved_count", 0),
            "rejected_count": session.get("rejected_count", 0) if include_rejected else 0,
        },
        "detections": detections,
        "verification_status": verification_status,
        "bom_data": session.get("bom_data"),
        # P&ID 특화 데이터
        "pid_valves": session.get("pid_valves"),
        "pid_equipment": session.get("pid_equipment"),
        "pid_checklist": session.get("pid_checklist"),
        "pid_deviations": session.get("pid_deviations"),
        # OCR 및 연결 정보
        "ocr_texts": session.get("ocr_texts"),
        "connections": session.get("connections"),
    }

    # 이미지 데이터 추가
    if include_image:
        file_path = Path(session.get("file_path", ""))
        if file_path.exists():
            try:
                with open(file_path, "rb") as f:
                    image_bytes = f.read()

                ext = file_path.suffix.lower()
                mime_types = {
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".png": "image/png",
                    ".bmp": "image/bmp",
                    ".tiff": "image/tiff",
                    ".tif": "image/tiff",
                }

                export_data["image_data"] = {
                    "filename": session.get("filename"),
                    "mime_type": mime_types.get(ext, "application/octet-stream"),
                    "image_base64": base64.b64encode(image_bytes).decode("utf-8"),
                }
            except Exception as e:
                logger.warning(f"Failed to include image in export: {e}")

    # JSON 파일 생성
    json_content = json.dumps(export_data, ensure_ascii=False, indent=2, default=str)
    buffer = BytesIO(json_content.encode("utf-8"))
    buffer.seek(0)

    # 파일명 생성
    filename = session.get("filename", "session")
    if "." in filename:
        filename = filename.rsplit(".", 1)[0]
    export_filename = f"{filename}_session_{session_id[:8]}.json"

    return StreamingResponse(
        buffer,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{export_filename}"'
        }
    )


@router.post("/import", response_model=SessionResponse)
async def import_session_json(
    file: UploadFile = File(...),
    new_session_id: Optional[str] = Query(default=None, description="새 세션 ID (미지정 시 자동 생성)")
):
    """세션 JSON Import

    Export된 세션 JSON을 import하여 동일한 세션을 재현합니다.

    Args:
        file: Export된 JSON 파일
        new_session_id: 새 세션 ID (선택)

    Returns:
        SessionResponse: 생성된 세션 정보
    """
    service = get_session_service()

    # JSON 파일 읽기
    try:
        content = await file.read()
        export_data = json.loads(content.decode("utf-8"))
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"유효하지 않은 JSON 형식: {e}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"파일 읽기 실패: {e}")

    # 버전 확인
    export_version = export_data.get("export_version", "1.0")
    if export_version not in ["1.0"]:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 Export 버전: {export_version}")

    # 메타데이터 추출
    metadata = export_data.get("session_metadata", {})

    # 새 세션 ID 생성
    session_id = new_session_id or str(uuid.uuid4())

    # 이미지 복원
    image_data = export_data.get("image_data")
    file_path = None

    if image_data:
        try:
            # 이미지 디코딩
            image_bytes = base64.b64decode(image_data.get("image_base64", ""))

            # 파일 확장자 결정
            mime_type = image_data.get("mime_type", "image/png")
            ext_map = {
                "image/jpeg": ".jpg",
                "image/png": ".png",
                "image/bmp": ".bmp",
                "image/tiff": ".tiff",
            }
            ext = ext_map.get(mime_type, ".png")

            # 세션 디렉토리 생성 및 이미지 저장
            session_dir = _upload_dir / session_id
            session_dir.mkdir(parents=True, exist_ok=True)

            file_path = session_dir / f"original{ext}"
            with open(file_path, "wb") as f:
                f.write(image_bytes)

            logger.info(f"[Import] Image restored: {file_path}")
        except Exception as e:
            logger.warning(f"[Import] Failed to restore image: {e}")

    # 세션 생성
    session = service.create_session(
        session_id=session_id,
        filename=metadata.get("filename", image_data.get("filename") if image_data else "imported.png"),
        file_path=str(file_path) if file_path else "",
        drawing_type=metadata.get("drawing_type", "auto"),
        image_width=metadata.get("image_width"),
        image_height=metadata.get("image_height"),
        features=metadata.get("features", [])
    )

    # 검출 결과 복원
    detections = export_data.get("detections", [])
    verification_status = export_data.get("verification_status", {})

    if detections:
        service.update_session(session_id, {
            "detections": detections,
            "detection_count": len(detections),
            "verification_status": verification_status,
            "verified_count": len([v for v in verification_status.values() if v != "pending"]),
            "approved_count": len([v for v in verification_status.values() if v in ("approved", "modified", "manual")]),
            "rejected_count": len([v for v in verification_status.values() if v == "rejected"]),
            "status": metadata.get("status", SessionStatus.DETECTED),
        })

    # BOM 데이터 복원
    bom_data = export_data.get("bom_data")
    if bom_data:
        service.update_session(session_id, {
            "bom_data": bom_data,
            "bom_generated": True,
        })

    # P&ID 특화 데이터 복원
    pid_updates = {}
    if export_data.get("pid_valves"):
        pid_updates["pid_valves"] = export_data["pid_valves"]
    if export_data.get("pid_equipment"):
        pid_updates["pid_equipment"] = export_data["pid_equipment"]
    if export_data.get("pid_checklist"):
        pid_updates["pid_checklist"] = export_data["pid_checklist"]
    if export_data.get("pid_deviations"):
        pid_updates["pid_deviations"] = export_data["pid_deviations"]
    if export_data.get("ocr_texts"):
        pid_updates["ocr_texts"] = export_data["ocr_texts"]
    if export_data.get("connections"):
        pid_updates["connections"] = export_data["connections"]

    if pid_updates:
        service.update_session(session_id, pid_updates)

    # 최종 상태 설정
    final_status = metadata.get("status", SessionStatus.DETECTED)
    if bom_data:
        final_status = SessionStatus.COMPLETED
    service.update_session(session_id, {"status": final_status})

    # 응답
    updated_session = service.get_session(session_id)

    logger.info(f"[Import] Session imported successfully: {session_id} (original: {metadata.get('original_session_id')})")

    return SessionResponse(**updated_session)


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

    # 이미지 크기 추출
    from PIL import Image
    try:
        with Image.open(file_path) as img:
            image_width, image_height = img.size

        # 썸네일 생성
        thumbnail_base64 = None
        try:
            with Image.open(file_path) as img:
                img.thumbnail((150, 150))
                from io import BytesIO
                buffer = BytesIO()
                img.save(buffer, format="JPEG", quality=75)
                thumbnail_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        except Exception as e:
            logger.warning(f"[Session] Failed to create thumbnail: {e}")
    except Exception as e:
        logger.warning(f"[Session] Failed to extract image size: {e}")
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

            # 이미지 크기 추출
            from PIL import Image
            try:
                with Image.open(file_path) as img:
                    image_width, image_height = img.size
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
        "new_status": review_status.value,
    }
