"""Session I/O Router - 세션 JSON Export/Import API 엔드포인트"""

import uuid
import base64
import json
import logging
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from schemas.session import SessionResponse, SessionStatus

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
