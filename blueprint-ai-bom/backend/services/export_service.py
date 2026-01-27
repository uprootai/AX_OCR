"""Export Service - 세션 Export 패키지 생성

Phase 2E: 검증 완료된 세션을 ZIP 패키지로 내보내기
Phase 2F: Self-contained Export (Docker 이미지 포함)
"""

import json
import uuid
import zipfile
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from schemas.export import (
    ExportManifest,
    ExportPreview,
    ExportRequest,
    ExportResponse,
    ExportHistoryItem,
    SelfContainedExportRequest,
    SelfContainedExportResponse,
    SelfContainedPreview,
    DockerImageInfo,
)
from services.self_contained_export_service import (
    SelfContainedExportService,
    get_self_contained_export_service,
)

logger = logging.getLogger(__name__)


class ExportService:
    """세션 Export 서비스"""

    def __init__(self, export_dir: Path, upload_dir: Path):
        self.export_dir = export_dir
        self.upload_dir = upload_dir
        self.export_dir.mkdir(parents=True, exist_ok=True)

        # Self-contained Export 서비스 (위임)
        self._self_contained_service = get_self_contained_export_service(
            export_dir, upload_dir
        )

    def get_export_preview(
        self,
        session: Dict[str, Any],
        template: Optional[Dict[str, Any]] = None,
    ) -> ExportPreview:
        """Export 미리보기 생성"""
        session_id = session.get("session_id", "")
        images = session.get("images", [])

        # 이미지별 상태 집계
        status_counts = {
            "pending": 0,
            "processed": 0,
            "approved": 0,
            "rejected": 0,
            "modified": 0,
            "manual_labeled": 0,
        }

        for img in images:
            status = img.get("review_status", "pending")
            if status in status_counts:
                status_counts[status] += 1

        # 완료된 이미지 수
        completed = (
            status_counts["approved"]
            + status_counts["modified"]
            + status_counts["manual_labeled"]
        )
        pending = status_counts["pending"] + status_counts["processed"]

        # Export 가능 여부 판단
        can_export = pending == 0 and completed > 0
        reason = None
        if pending > 0:
            reason = f"{pending}개의 이미지가 검토 대기 중입니다."
        elif completed == 0:
            reason = "승인/수정된 이미지가 없습니다."

        # 예상 파일 크기 계산 (대략적)
        total_size = 0
        for img in images:
            if img.get("review_status") in ("approved", "modified", "manual_labeled"):
                file_path = Path(img.get("file_path", ""))
                if file_path.exists():
                    total_size += file_path.stat().st_size

        estimated_size_mb = total_size / (1024 * 1024)

        return ExportPreview(
            session_id=session_id,
            can_export=can_export,
            reason=reason,
            image_count=len(images),
            detection_count=session.get("detection_count", 0),
            approved_images=status_counts["approved"],
            modified_images=status_counts["modified"] + status_counts["manual_labeled"],
            rejected_images=status_counts["rejected"],
            pending_images=pending,
            estimated_size_mb=round(estimated_size_mb, 2),
            template_id=template.get("template_id") if template else None,
            template_name=template.get("name") if template else None,
        )

    def create_export_package(
        self,
        session: Dict[str, Any],
        request: ExportRequest,
        template: Optional[Dict[str, Any]] = None,
        project: Optional[Dict[str, Any]] = None,
    ) -> ExportResponse:
        """Export ZIP 패키지 생성"""
        session_id = session.get("session_id", "")
        export_id = str(uuid.uuid4())[:8]

        # 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{session.get('filename', 'session')}_{export_id}_{timestamp}.zip"
        export_path = self.export_dir / filename

        # 매니페스트 생성
        images = session.get("images", [])
        detections = session.get("detections", [])

        # 이미지별 통계
        image_stats = {"approved": 0, "rejected": 0, "modified": 0}
        for img in images:
            status = img.get("review_status", "pending")
            if status == "approved":
                image_stats["approved"] += 1
            elif status == "rejected":
                image_stats["rejected"] += 1
            elif status in ("modified", "manual_labeled"):
                image_stats["modified"] += 1

        manifest = ExportManifest(
            export_version="2.0",
            session_id=session_id,
            session_filename=session.get("filename", ""),
            drawing_type=session.get("drawing_type"),
            template_snapshot=template if request.include_template and template else None,
            image_count=len(images),
            detection_count=len(detections),
            approved_count=image_stats["approved"],
            rejected_count=image_stats["rejected"],
            modified_count=image_stats["modified"],
            project_id=project.get("project_id") if project else None,
            project_name=project.get("name") if project else None,
            customer=project.get("customer") if project else None,
            exported_by=request.exported_by,
            notes=request.notes,
        )

        # ZIP 파일 생성
        with zipfile.ZipFile(export_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # 매니페스트 추가
            manifest_json = manifest.model_dump_json(indent=2)
            zf.writestr("manifest.json", manifest_json)

            # 세션 데이터 추가
            session_data = self._prepare_session_data(
                session, request.include_rejected
            )
            zf.writestr("session.json", json.dumps(session_data, indent=2, default=str))

            # 이미지 추가
            if request.include_images:
                for img in images:
                    status = img.get("review_status", "pending")

                    # 거부된 이미지 제외 (옵션)
                    if not request.include_rejected and status == "rejected":
                        continue

                    file_path = Path(img.get("file_path", ""))
                    if file_path.exists():
                        image_id = img.get("image_id", "")
                        archive_name = f"images/{image_id}_{file_path.name}"
                        zf.write(file_path, archive_name)

            # 검출 결과별 크롭 이미지 (있는 경우)
            detections_dir = self.upload_dir / session_id / "detections"
            if detections_dir.exists():
                for det_file in detections_dir.glob("*.jpg"):
                    zf.write(det_file, f"detections/{det_file.name}")

        # 파일 크기 확인
        file_size = export_path.stat().st_size

        logger.info(
            f"[Export] Package created: {filename} ({file_size / 1024:.1f} KB)"
        )

        return ExportResponse(
            success=True,
            session_id=session_id,
            export_id=export_id,
            filename=filename,
            file_path=str(export_path),
            file_size_bytes=file_size,
            created_at=datetime.now().isoformat(),
            manifest=manifest,
        )

    def _prepare_session_data(
        self,
        session: Dict[str, Any],
        include_rejected: bool = False,
    ) -> Dict[str, Any]:
        """세션 데이터 정리 (Export용)"""
        data = {
            "session_id": session.get("session_id"),
            "filename": session.get("filename"),
            "status": session.get("status"),
            "drawing_type": session.get("drawing_type"),
            "features": session.get("features", []),
            "created_at": session.get("created_at"),
            "updated_at": session.get("updated_at"),
            "image_width": session.get("image_width"),
            "image_height": session.get("image_height"),
        }

        # 검출 결과
        detections = session.get("detections", [])
        if not include_rejected:
            verification_status = session.get("verification_status", {})
            detections = [
                d for d in detections
                if verification_status.get(d.get("id")) != "rejected"
            ]
        data["detections"] = detections
        data["detection_count"] = len(detections)

        # 이미지
        images = session.get("images", [])
        if not include_rejected:
            images = [
                img for img in images
                if img.get("review_status") != "rejected"
            ]
        data["images"] = [
            {
                "image_id": img.get("image_id"),
                "filename": img.get("filename"),
                "review_status": img.get("review_status"),
                "detection_count": img.get("detection_count", 0),
                "verified_count": img.get("verified_count", 0),
                "reviewed_at": img.get("reviewed_at"),
                "reviewed_by": img.get("reviewed_by"),
            }
            for img in images
        ]
        data["image_count"] = len(data["images"])

        # BOM 데이터 (있는 경우)
        if session.get("bom_data"):
            data["bom_data"] = session["bom_data"]

        return data

    def list_exports(self, session_id: str) -> List[ExportHistoryItem]:
        """세션의 Export 이력 조회"""
        exports = []

        # Export 디렉토리에서 해당 세션의 파일 검색
        for export_file in self.export_dir.glob(f"*_{session_id[:8]}_*.zip"):
            try:
                stat = export_file.stat()
                exports.append(
                    ExportHistoryItem(
                        export_id=export_file.stem.split("_")[1],
                        session_id=session_id,
                        filename=export_file.name,
                        file_size_bytes=stat.st_size,
                        created_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to read export file: {export_file}, {e}")

        # 최신순 정렬
        exports.sort(key=lambda x: x.created_at, reverse=True)

        return exports

    def get_export_file(self, filename: str) -> Optional[Path]:
        """Export 파일 경로 조회"""
        file_path = self.export_dir / filename
        if file_path.exists():
            return file_path
        return None

    def delete_export(self, filename: str) -> bool:
        """Export 파일 삭제"""
        file_path = self.export_dir / filename
        if file_path.exists():
            file_path.unlink()
            logger.info(f"[Export] File deleted: {filename}")
            return True
        return False

    # =========================================================================
    # Self-contained Export (Docker 이미지 포함) - 위임 메서드
    # =========================================================================

    def get_self_contained_preview(
        self,
        session: Dict[str, Any],
        template: Optional[Dict[str, Any]] = None,
        port_offset: int = 10000,
        source_prefix: str = "poc_",
    ) -> SelfContainedPreview:
        """Self-contained Export 미리보기 (위임)"""
        return self._self_contained_service.get_preview(
            session, template, port_offset, source_prefix=source_prefix
        )

    def create_self_contained_package(
        self,
        session: Dict[str, Any],
        request: SelfContainedExportRequest,
        template: Optional[Dict[str, Any]] = None,
        project: Optional[Dict[str, Any]] = None,
    ) -> SelfContainedExportResponse:
        """Self-contained Export 패키지 생성 (위임)"""
        return self._self_contained_service.create_package(
            session=session,
            request=request,
            prepare_session_data_func=self._prepare_session_data,
            template=template,
            project=project,
        )


# Singleton instance
_export_service: Optional[ExportService] = None


def get_export_service(export_dir: Path, upload_dir: Path) -> ExportService:
    """Export 서비스 인스턴스 조회"""
    global _export_service
    if _export_service is None:
        _export_service = ExportService(export_dir, upload_dir)
    return _export_service
