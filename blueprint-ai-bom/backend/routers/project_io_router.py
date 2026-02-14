"""Project I/O Router - 프로젝트 Export/Import API 엔드포인트

프로젝트 단위 Export/Import:
- Export: 프로젝트 메타 + BOM 데이터 + 모든 세션 → JSON 다운로드
- Import: JSON → 프로젝트 + 세션 복원
"""

import json
import uuid
import logging
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse

from services.project_service import get_project_service
from services.bom_pdf_parser import BOMPDFParser
from routers.session_io_router import build_session_export_dict

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["Projects - I/O"])


# 의존성 주입을 위한 전역 서비스
_session_service = None
_upload_dir = None


def set_project_io_services(session_service, upload_dir: Path):
    """서비스 인스턴스 설정 (api_server.py에서 호출)"""
    global _session_service, _upload_dir
    _session_service = session_service
    _upload_dir = upload_dir


def _get_session_service():
    if _session_service is None:
        raise HTTPException(status_code=500, detail="Session service not initialized")
    return _session_service


# =============================================================================
# Project Export
# =============================================================================

@router.get("/{project_id}/export")
async def export_project(
    project_id: str,
    include_images: bool = Query(default=False, description="세션 이미지 base64 포함 여부 (용량 주의)"),
    include_rejected: bool = Query(default=True, description="거부된 항목 포함 여부"),
):
    """프로젝트 전체 Export

    프로젝트 메타데이터 + BOM 데이터 + 모든 세션을 하나의 JSON으로 내보냅니다.

    Args:
        project_id: 프로젝트 ID
        include_images: 세션 이미지 포함 여부 (기본: False, 포함 시 용량 큼)
        include_rejected: 거부된 항목 포함 여부 (기본: True)

    Returns:
        StreamingResponse: JSON 파일 다운로드
    """
    data_dir = Path("/app/data")
    project_service = get_project_service(data_dir)
    session_service = _get_session_service()

    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")

    # BOM 데이터 로드
    project_dir = project_service.projects_dir / project_id
    bom_parser = BOMPDFParser()
    bom_data = bom_parser.load_bom_items(project_dir)

    # 세션 목록 조회 및 export
    # BOM에서 참조하는 session_id도 포함하여 누락 방지
    sessions = session_service.list_sessions_by_project(project_id)
    exported_sids = set()
    session_exports = []

    for session in sessions:
        sid = session.get("session_id", "")
        exported_sids.add(sid)
        full_session = session_service.get_session(sid)
        if full_session:
            session_export = build_session_export_dict(
                full_session, sid,
                include_image=include_images,
                include_rejected=include_rejected,
            )
            session_exports.append(session_export)

    # BOM에서 참조하지만 목록에 없는 세션도 파일에서 직접 로드
    if isinstance(bom_data, dict):
        bom_session_ids = {
            item.get("session_id") for item in bom_data.get("items", [])
            if item.get("session_id")
        }
        missing_sids = bom_session_ids - exported_sids
        for sid in missing_sids:
            full_session = session_service.get_session(sid)
            if full_session:
                exported_sids.add(sid)
                session_export = build_session_export_dict(
                    full_session, sid,
                    include_image=include_images,
                    include_rejected=include_rejected,
                )
                session_exports.append(session_export)
        if missing_sids:
            logger.info(f"[Project Export] {len(missing_sids)} additional sessions loaded from BOM references")

    # 통계 계산
    total_quotation = project.get("total_quotation", 0)
    bom_item_count = project.get("bom_item_count", 0)

    # Export 데이터 구성
    export_data = {
        "export_version": "2.0",
        "export_type": "project",
        "export_timestamp": datetime.now().isoformat(),
        "project_metadata": {
            "original_project_id": project_id,
            "name": project.get("name"),
            "customer": project.get("customer"),
            "project_type": project.get("project_type", "general"),
            "description": project.get("description"),
            "default_features": project.get("default_features", []),
            "default_template_id": project.get("default_template_id"),
            "default_template_name": project.get("default_template_name"),
            "default_model_type": project.get("default_model_type"),
            "bom_source": project.get("bom_source"),
            "drawing_folder": project.get("drawing_folder"),
            "session_count": len(sessions),
            "bom_item_count": bom_item_count,
            "total_quotation": total_quotation,
        },
        "bom_data": bom_data,
        "sessions": session_exports,
    }

    # JSON 생성
    json_content = json.dumps(export_data, ensure_ascii=False, indent=2, default=str)
    buffer = BytesIO(json_content.encode("utf-8"))
    buffer.seek(0)

    # 파일명 생성 (한글 지원: RFC 5987)
    safe_name = (project.get("name") or "project").replace(" ", "_")[:30]
    export_filename = f"{safe_name}_{project_id}.json"
    ascii_filename = f"project_{project_id}.json"
    encoded_filename = quote(export_filename)

    logger.info(
        f"[Project Export] {project_id}: {len(session_exports)} sessions, "
        f"bom_items={bom_item_count}, images={'Y' if include_images else 'N'}"
    )

    return StreamingResponse(
        buffer,
        media_type="application/json",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{ascii_filename}"; '
                f"filename*=UTF-8''{encoded_filename}"
            )
        },
    )


# =============================================================================
# Project Import
# =============================================================================

@router.post("/import")
async def import_project(
    file: UploadFile = File(...),
):
    """프로젝트 JSON Import

    Export된 프로젝트 JSON을 import하여 프로젝트 + 세션을 복원합니다.
    새로운 project_id와 session_id가 자동 생성됩니다.

    Args:
        file: Export된 JSON 파일

    Returns:
        dict: 생성된 프로젝트 정보
    """
    data_dir = Path("/app/data")
    project_service = get_project_service(data_dir)
    session_service = _get_session_service()

    # JSON 파일 읽기
    try:
        content = await file.read()
        export_data = json.loads(content.decode("utf-8"))
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"유효하지 않은 JSON 형식: {e}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"파일 읽기 실패: {e}")

    # 버전 확인
    export_version = export_data.get("export_version")
    export_type = export_data.get("export_type")

    if export_version != "2.0" or export_type != "project":
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 형식입니다. export_version=2.0, export_type=project 필요 "
                   f"(받은 값: version={export_version}, type={export_type})"
        )

    meta = export_data.get("project_metadata", {})

    # 새 프로젝트 생성
    from schemas.project import ProjectCreate
    project_create = ProjectCreate(
        name=meta.get("name", "Imported Project"),
        customer=meta.get("customer", "Unknown"),
        project_type=meta.get("project_type", "general"),
        description=meta.get("description"),
        default_template_id=meta.get("default_template_id"),
        default_model_type=meta.get("default_model_type"),
        default_features=meta.get("default_features", []),
        bom_source=meta.get("bom_source"),
        drawing_folder=meta.get("drawing_folder"),
    )

    project = project_service.create_project(project_create)
    new_project_id = project["project_id"]

    # BOM 데이터 복원
    bom_data = export_data.get("bom_data")
    if bom_data:
        project_dir = project_service.projects_dir / new_project_id
        bom_parser = BOMPDFParser()
        bom_parser.save_bom_items(project_dir, bom_data)

        # BOM 통계 업데이트
        if isinstance(bom_data, dict):
            project["bom_item_count"] = bom_data.get("total_items", 0)
            project["quotation_item_count"] = bom_data.get("part_count", 0)
        elif isinstance(bom_data, list):
            project["bom_item_count"] = len(bom_data)
        project_service._save_project(new_project_id)

    # 세션 복원
    session_exports = export_data.get("sessions", [])
    imported_sessions = []
    failed_sessions = []

    for session_data in session_exports:
        try:
            new_session_id = str(uuid.uuid4())
            session_meta = session_data.get("session_metadata", {})

            # 이미지 복원
            import base64
            image_data = session_data.get("image_data")
            file_path = None

            if image_data and _upload_dir:
                try:
                    image_bytes = base64.b64decode(image_data.get("image_base64", ""))
                    mime_type = image_data.get("mime_type", "image/png")
                    ext_map = {
                        "image/jpeg": ".jpg", "image/png": ".png",
                        "image/bmp": ".bmp", "image/tiff": ".tiff",
                    }
                    ext = ext_map.get(mime_type, ".png")

                    session_dir = _upload_dir / new_session_id
                    session_dir.mkdir(parents=True, exist_ok=True)
                    file_path = session_dir / f"original{ext}"
                    with open(file_path, "wb") as f:
                        f.write(image_bytes)
                except Exception as e:
                    logger.warning(f"[Project Import] Image restore failed for session: {e}")

            # 세션 생성
            session = session_service.create_session(
                session_id=new_session_id,
                filename=session_meta.get("filename", "imported.png"),
                file_path=str(file_path) if file_path else "",
                drawing_type=session_meta.get("drawing_type", "auto"),
                image_width=session_meta.get("image_width"),
                image_height=session_meta.get("image_height"),
                features=session_meta.get("features", []),
            )

            # 프로젝트에 연결 + metadata 복원
            update_fields = {"project_id": new_project_id}
            if session_meta.get("metadata"):
                update_fields["metadata"] = session_meta["metadata"]
            session_service.update_session(new_session_id, update_fields)

            # 검출 결과 복원
            detections = session_data.get("detections", [])
            verification_status = session_data.get("verification_status", {})

            if detections:
                session_service.update_session(new_session_id, {
                    "detections": detections,
                    "detection_count": len(detections),
                    "verification_status": verification_status,
                    "verified_count": len([v for v in verification_status.values() if v != "pending"]),
                    "approved_count": len([v for v in verification_status.values() if v in ("approved", "modified", "manual")]),
                    "rejected_count": len([v for v in verification_status.values() if v == "rejected"]),
                    "status": session_meta.get("status", "detected"),
                })

            # BOM 데이터 복원
            session_bom = session_data.get("bom_data")
            if session_bom:
                session_service.update_session(new_session_id, {
                    "bom_data": session_bom,
                    "bom_generated": True,
                })

            # P&ID 데이터 복원
            pid_updates = {}
            for key in ("pid_valves", "pid_equipment", "pid_checklist", "pid_deviations", "ocr_texts", "connections"):
                if session_data.get(key):
                    pid_updates[key] = session_data[key]
            if pid_updates:
                session_service.update_session(new_session_id, pid_updates)

            # 최종 상태 설정
            final_status = session_meta.get("status", "detected")
            if session_bom:
                final_status = "completed"
            session_service.update_session(new_session_id, {"status": final_status})

            imported_sessions.append({
                "original_session_id": session_meta.get("original_session_id"),
                "new_session_id": new_session_id,
                "filename": session_meta.get("filename"),
            })
        except Exception as e:
            logger.error(f"[Project Import] Session import failed: {e}")
            failed_sessions.append(str(e))

    # BOM session_id 리맵 (원본 ID → 새 ID) + 고아 세션 스텁 생성
    stub_count = 0
    if bom_data and isinstance(bom_data, dict) and bom_data.get("items"):
        session_id_map = {
            s["original_session_id"]: s["new_session_id"]
            for s in imported_sessions if s.get("original_session_id")
        }
        project_dir = project_service.projects_dir / new_project_id
        bom_parser = BOMPDFParser()
        saved_bom = bom_parser.load_bom_items(project_dir)

        if isinstance(saved_bom, dict) and saved_bom.get("items"):
            # 리맵 안 되는 session_id 수집 → 스텁 세션 생성
            orphan_sids = set()
            for item in saved_bom["items"]:
                old_sid = item.get("session_id")
                if old_sid and old_sid not in session_id_map:
                    orphan_sids.add(old_sid)

            for orphan_sid in orphan_sids:
                orphan_items = [i for i in saved_bom["items"] if i.get("session_id") == orphan_sid]
                if not orphan_items:
                    continue
                first = orphan_items[0]
                matched_file = first.get("matched_file", "")
                filename = Path(matched_file).name if matched_file else f"{first.get('drawing_number', 'unknown')}.pdf"
                item_nos = [str(i.get("item_no", "")) for i in orphan_items]

                new_stub_id = str(uuid.uuid4())
                try:
                    session_service.create_session(
                        session_id=new_stub_id,
                        filename=filename,
                        file_path="",
                        drawing_type="dimension_bom",
                        features=["dimension_ocr", "table_extraction", "bom_generation", "title_block_ocr"],
                    )
                    session_service.update_session(new_stub_id, {
                        "project_id": new_project_id,
                        "metadata": {
                            "drawing_number": first.get("drawing_number", ""),
                            "bom_item_no": ",".join(item_nos),
                            "bom_item_nos": item_nos,
                            "bom_level": first.get("level", "part"),
                            "material": first.get("material", ""),
                            "bom_quantity": sum(i.get("quantity", 1) for i in orphan_items),
                            "bom_line_count": len(orphan_items),
                            "bom_description": first.get("description", ""),
                            "quote_status": "pending",
                            "size": first.get("size", ""),
                            "weight_kg": first.get("weight_kg"),
                            "doc_revision": first.get("doc_revision"),
                            "part_no": first.get("part_no"),
                            "remark": first.get("remark"),
                            "assembly_refs": [
                                {"assembly": i.get("assembly_drawing_number", ""), "item_no": str(i.get("item_no", "")), "quantity": i.get("quantity", 1)}
                                for i in orphan_items if i.get("assembly_drawing_number")
                            ],
                        },
                    })
                    session_id_map[orphan_sid] = new_stub_id
                    stub_count += 1
                except Exception as e:
                    logger.warning(f"[Project Import] Stub session creation failed for {orphan_sid}: {e}")

            # 전체 리맵 적용
            remapped = 0
            for item in saved_bom["items"]:
                old_sid = item.get("session_id")
                if old_sid and old_sid in session_id_map:
                    item["session_id"] = session_id_map[old_sid]
                    remapped += 1
            bom_parser.save_bom_items(project_dir, saved_bom)
            logger.info(
                f"[Project Import] BOM session_id remapped: {remapped}/{len(saved_bom['items'])}, "
                f"stub sessions: {stub_count}"
            )

    # 프로젝트 통계 업데이트
    project_service.update_session_counts(new_project_id, session_service)

    logger.info(
        f"[Project Import] {new_project_id}: {len(imported_sessions)} sessions imported, "
        f"{len(failed_sessions)} failed (original: {meta.get('original_project_id')})"
    )

    return {
        "project_id": new_project_id,
        "name": project.get("name"),
        "customer": project.get("customer"),
        "project_type": project.get("project_type"),
        "imported_sessions": len(imported_sessions),
        "failed_sessions": len(failed_sessions),
        "sessions": imported_sessions,
        "message": f"프로젝트가 성공적으로 Import되었습니다. ({len(imported_sessions)}개 세션)",
    }
