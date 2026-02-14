"""Self-contained Export Service - Docker 이미지 포함 Export

Phase 2F: Self-contained Export 패키지 생성
- Docker 이미지 Export
- docker-compose.yml 동적 생성 (포트 오프셋 적용)
- Import 스크립트 생성
"""

import base64
import json
import mimetypes
import shutil
import tempfile
import uuid
import zipfile
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from schemas.export import (
    SelfContainedExportRequest,
    SelfContainedExportResponse,
    SelfContainedPreview,
)

from services.export_docker_handler import (
    get_docker_image_size,
    export_docker_images,
    generate_docker_compose,
)
from services.export_script_generator import (
    generate_import_scripts,
    generate_readme,
)

logger = logging.getLogger(__name__)


class SelfContainedExportService:
    """Self-contained Export 서비스 (Docker 이미지 포함)"""

    # 노드 타입 → Docker 서비스 매핑
    NODE_TO_SERVICE_MAP = {
        "yolo": "yolo-api",
        "edocr2": "edocr2-v2-api",
        "paddleocr": "paddleocr-api",
        "skinmodel": "skinmodel-api",
        "vl": "vl-api",
        "edgnet": "edgnet-api",
        "knowledge": "knowledge-api",
        "tesseract": "tesseract-api",
        "trocr": "trocr-api",
        "esrgan": "esrgan-api",
        "ocr-ensemble": "ocr-ensemble-api",
        "surya-ocr": "surya-ocr-api",
        "doctr": "doctr-api",
        "easyocr": "easyocr-api",
        "line-detector": "line-detector-api",
        "table-detector": "table-detector-api",
        "pid-analyzer": "pid-analyzer-api",
        "design-checker": "design-checker-api",
        "pid-composer": "pid-composer-api",
        "blueprint-ai-bom": "blueprint-ai-bom-backend",
    }

    # 서비스 → 원본 포트 매핑
    SERVICE_PORT_MAP = {
        "gateway-api": 8000,
        "edocr2-v2-api": 5002,
        "edgnet-api": 5012,
        "skinmodel-api": 5003,
        "vl-api": 5004,
        "yolo-api": 5005,
        "paddleocr-api": 5006,
        "knowledge-api": 5007,
        "tesseract-api": 5008,
        "trocr-api": 5009,
        "esrgan-api": 5010,
        "ocr-ensemble-api": 5011,
        "surya-ocr-api": 5013,
        "doctr-api": 5014,
        "easyocr-api": 5015,
        "line-detector-api": 5016,
        "pid-analyzer-api": 5018,
        "design-checker-api": 5019,
        "blueprint-ai-bom-backend": 5020,
        "blueprint-ai-bom-frontend": 3000,  # BOM 프론트엔드
        "pid-composer-api": 5021,
        "table-detector-api": 5022,
        "web-ui": 5173,  # BlueprintFlow 편집기 (옵션)
    }

    # 백엔드 → 프론트엔드 자동 포함 매핑
    BACKEND_TO_FRONTEND_MAP = {
        "blueprint-ai-bom-backend": "blueprint-ai-bom-frontend",
    }

    # 프론트엔드 서비스 목록 (docker-compose 생성 시 특별 처리)
    FRONTEND_SERVICES = {"blueprint-ai-bom-frontend", "web-ui"}

    # 옵션 서비스 (기본적으로 포함되지 않음, 요청 시에만 포함)
    OPTIONAL_SERVICES = {
        "web-ui": {
            "description": "BlueprintFlow 편집기 (워크플로우 편집 필요 시)",
            "port": 5173,
            "depends_on": ["gateway-api"],
        }
    }

    # 세션 features → Docker 서비스 매핑
    FEATURE_TO_SERVICE_MAP = {
        "symbol_detection": ["yolo-api"],
        "text_ocr": ["paddleocr-api", "tesseract-api"],
        "general_ocr": ["paddleocr-api"],
        "table_extraction": ["table-detector-api"],
        "pid_analysis": ["pid-analyzer-api", "line-detector-api"],
        "design_check": ["design-checker-api"],
        "tolerance_analysis": ["skinmodel-api"],
        "knowledge_graph": ["knowledge-api"],
        "vl_classification": ["vl-api"],
        "edge_detection": ["edgnet-api"],
        "image_enhancement": ["esrgan-api"],
    }

    def __init__(self, export_dir: Path, upload_dir: Path):
        self.export_dir = export_dir
        self.upload_dir = upload_dir
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def get_mapped_port(self, service: str, port_offset: int) -> int:
        """포트 오프셋이 적용된 포트 반환"""
        original_port = self.SERVICE_PORT_MAP.get(service, 5000)
        return original_port + port_offset

    def detect_required_services(
        self,
        workflow_definition: Dict[str, Any],
        include_web_ui: bool = False,
        session_features: Optional[List[str]] = None
    ) -> List[str]:
        """워크플로우에서 필요한 Docker 서비스 추출"""
        services = {"gateway-api"}  # Gateway는 항상 필요

        # 1. 워크플로우 노드에서 서비스 추출
        nodes = workflow_definition.get("nodes", [])
        for node in nodes:
            node_type = node.get("type", "").lower().replace("_", "-")

            if node_type in self.NODE_TO_SERVICE_MAP:
                services.add(self.NODE_TO_SERVICE_MAP[node_type])
            elif node_type == "edocr":
                services.add("edocr2-v2-api")
            elif node_type in ("paddle", "paddle-ocr"):
                services.add("paddleocr-api")
            elif node_type in ("bom", "ai-bom"):
                services.add("blueprint-ai-bom-backend")

        # 2. 세션 features에서 서비스 추출
        if session_features:
            services.add("blueprint-ai-bom-backend")
            for feature in session_features:
                feature_key = feature.lower().replace("-", "_")
                if feature_key in self.FEATURE_TO_SERVICE_MAP:
                    services.add(self.FEATURE_TO_SERVICE_MAP[feature_key][0])

        # 백엔드가 포함되면 프론트엔드도 자동 포함
        frontends_to_add = set()
        for service in services:
            if service in self.BACKEND_TO_FRONTEND_MAP:
                frontends_to_add.add(self.BACKEND_TO_FRONTEND_MAP[service])
        services.update(frontends_to_add)

        if include_web_ui:
            services.add("web-ui")

        return sorted(list(services))

    def get_workflow_node_types(
        self,
        workflow_definition: Dict[str, Any]
    ) -> List[str]:
        """워크플로우에서 사용된 노드 타입 추출"""
        nodes = workflow_definition.get("nodes", [])
        node_types = set()
        for node in nodes:
            node_type = node.get("type", "")
            if node_type:
                node_types.add(node_type)
        return sorted(list(node_types))

    def _encode_image_file(self, img_path: Path, filename: str) -> Optional[Dict[str, Any]]:
        """이미지 파일을 base64로 인코딩"""
        try:
            with open(img_path, "rb") as f:
                image_bytes = f.read()

            mime_type, _ = mimetypes.guess_type(str(img_path))
            if not mime_type:
                mime_type = "image/png"

            result = {
                "filename": filename,
                "image_base64": base64.b64encode(image_bytes).decode("utf-8"),
                "mime_type": mime_type,
                "file_size": len(image_bytes)
            }
            logger.info(f"[Export] Image encoded: {img_path.name} ({len(image_bytes)} bytes)")
            return result
        except Exception as e:
            logger.warning(f"[Export] Failed to encode image {img_path}: {e}")
            return None

    def generate_importable_session(
        self,
        session: Dict[str, Any],
        output_path: Path,
        upload_dir: Path,
        project_id: Optional[str] = None,
    ) -> bool:
        """Import 엔드포인트와 호환되는 세션 JSON 생성"""
        session_id = session.get("session_id", "")
        filename = session.get("filename", "")

        image_data = None
        session_dir = upload_dir / session_id
        logger.info(f"[Export] Looking for session image in: {session_dir}, filename: {filename}")

        if session_dir.exists():
            if filename:
                img_path = session_dir / filename
                if img_path.exists():
                    image_data = self._encode_image_file(img_path, filename)

            if not image_data:
                for ext in [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".gif"]:
                    for pattern in [f"original{ext}", f"*{ext}"]:
                        if pattern.startswith("*"):
                            matches = list(session_dir.glob(pattern))
                            if matches:
                                img_path = matches[0]
                                image_data = self._encode_image_file(img_path, filename or img_path.name)
                                break
                        else:
                            img_path = session_dir / pattern
                            if img_path.exists():
                                image_data = self._encode_image_file(img_path, filename or img_path.name)
                                break
                    if image_data:
                        break
        else:
            logger.warning(f"[Export] Session directory not found: {session_dir}")

        if not image_data:
            logger.warning(f"[Export] No image found for session {session_id}")

        importable_data = {
            "export_version": "1.0",
            "session_metadata": {
                "session_id": session_id,
                "filename": session.get("filename", ""),
                "status": session.get("status", "uploaded"),
                "drawing_type": session.get("drawing_type", "auto"),
                "image_width": session.get("image_width"),
                "image_height": session.get("image_height"),
                "features": session.get("features", []),
                "created_at": session.get("created_at"),
                "template_id": session.get("template_id"),
                "template_name": session.get("template_name"),
                "project_id": project_id or session.get("project_id"),
            },
            "image_data": image_data,
            "detections": session.get("detections", []),
            "verification_status": {
                d.get("id"): d.get("verification_status", "pending")
                for d in session.get("detections", [])
            },
            "bom_data": session.get("bom_data"),
            "ocr_texts": session.get("ocr_texts", []),
        }

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(importable_data, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"[Export] Importable session JSON created: {output_path}")
            return True
        except Exception as e:
            logger.error(f"[Export] Failed to create importable session: {e}")
            return False

    def get_preview(
        self,
        session: Dict[str, Any],
        template: Optional[Dict[str, Any]] = None,
        port_offset: int = 10000,
        include_web_ui: bool = False,
        source_prefix: str = "poc_",
    ) -> SelfContainedPreview:
        """Self-contained Export 미리보기"""
        session_id = session.get("session_id", "")

        workflow_def = (
            template.get("workflow_definition", {})
            if template
            else session.get("workflow_definition", {})
        )
        session_features = session.get("features", [])
        required_services = self.detect_required_services(
            workflow_def,
            include_web_ui=include_web_ui,
            session_features=session_features
        )
        node_types = self.get_workflow_node_types(workflow_def)

        estimated_sizes = {}
        port_mapping = {}
        total_size = 0.0

        for service in required_services:
            size = get_docker_image_size(service, source_prefix=source_prefix)
            estimated_sizes[service] = size
            total_size += size

            original_port = self.SERVICE_PORT_MAP.get(service, 5000)
            port_mapping[service] = {
                "original": original_port,
                "mapped": original_port + port_offset
            }

        can_export = len(required_services) > 0
        reason = None if can_export else "워크플로우에 분석 노드가 없습니다."

        return SelfContainedPreview(
            session_id=session_id,
            can_export=can_export,
            reason=reason,
            required_services=required_services,
            estimated_sizes_mb=estimated_sizes,
            total_estimated_size_mb=round(total_size, 2),
            port_mapping=port_mapping,
            workflow_node_types=node_types,
        )

    def create_package(
        self,
        session: Dict[str, Any],
        request: SelfContainedExportRequest,
        prepare_session_data_func,
        template: Optional[Dict[str, Any]] = None,
        project: Optional[Dict[str, Any]] = None,
    ) -> SelfContainedExportResponse:
        """Self-contained Export 패키지 생성"""
        session_id = session.get("session_id", "")
        export_id = str(uuid.uuid4())[:8]
        port_offset = request.port_offset
        container_prefix = request.container_prefix
        include_web_ui = getattr(request, 'include_web_ui', False)
        source_prefix = getattr(request, 'source_image_prefix', 'poc_')

        workflow_def = (
            template.get("workflow_definition", {})
            if template
            else session.get("workflow_definition", {})
        )
        session_features = session.get("features", [])
        required_services = self.detect_required_services(
            workflow_def,
            include_web_ui=include_web_ui,
            session_features=session_features
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            images = session.get("images", [])
            detections = session.get("detections", [])

            port_mapping = {}
            for service in required_services:
                original_port = self.SERVICE_PORT_MAP.get(service, 5000)
                port_mapping[service] = {
                    "original": original_port,
                    "mapped": original_port + port_offset
                }

            manifest_data = {
                "export_version": "3.0",
                "export_timestamp": datetime.now().isoformat(),
                "export_type": "self-contained",
                "session_id": session_id,
                "session_filename": session.get("filename", ""),
                "drawing_type": session.get("drawing_type"),
                "image_count": len(images),
                "detection_count": len(detections),
                "included_services": required_services,
                "port_offset": port_offset,
                "container_prefix": container_prefix,
                "port_mapping": port_mapping,
                "exported_by": request.exported_by,
                "notes": request.notes,
            }

            with open(temp_path / "manifest.json", "w") as f:
                json.dump(manifest_data, f, indent=2, default=str)

            session_data = prepare_session_data_func(session, include_rejected=False)
            with open(temp_path / "session.json", "w") as f:
                json.dump(session_data, f, indent=2, default=str)

            self.generate_importable_session(
                session=session,
                output_path=temp_path / "session_import.json",
                upload_dir=self.upload_dir,
                project_id=project.get("project_id") if project else None,
            )

            # 프로젝트 데이터 및 GT 라벨 포함
            if project:
                project_export = {
                    "name": project.get("name"),
                    "customer": project.get("customer"),
                    "project_type": project.get("project_type"),
                    "description": project.get("description"),
                    "default_features": project.get("default_features", []),
                    "default_model_type": project.get("default_model_type"),
                }
                with open(temp_path / "project.json", "w", encoding="utf-8") as f:
                    json.dump(project_export, f, indent=2, ensure_ascii=False)

                manifest_data["project_id"] = project.get("project_id")
                manifest_data["project_name"] = project.get("name")

                # GT 라벨 파일 복사
                gt_folder = Path(project.get("gt_folder", ""))
                if gt_folder.exists():
                    gt_files = list(gt_folder.glob("*.txt"))
                    if gt_files:
                        gt_dest = temp_path / "gt_labels"
                        gt_dest.mkdir()
                        for gt_file in gt_files:
                            shutil.copy2(gt_file, gt_dest / gt_file.name)
                        logger.info(f"[Export] GT labels copied: {len(gt_files)} files")

                # manifest 파일 재기록 (project 정보 추가)
                with open(temp_path / "manifest.json", "w") as f:
                    json.dump(manifest_data, f, indent=2, default=str)

            # 참조 GT 라벨 파일 포함 (test_drawings/labels/)
            gt_ref_dir = Path(__file__).parent.parent / "test_drawings" / "labels"
            if gt_ref_dir.exists():
                session_filename = session.get("filename", "")
                base_name = Path(session_filename).stem
                gt_ref_file = gt_ref_dir / f"{base_name}.txt"
                if gt_ref_file.exists():
                    gt_ref_dest = temp_path / "gt_reference"
                    gt_ref_dest.mkdir(exist_ok=True)
                    shutil.copy2(gt_ref_file, gt_ref_dest / gt_ref_file.name)
                    # classes 파일도 복사 (클래스 매핑용)
                    for cls_file in gt_ref_dir.glob("classes*.txt"):
                        shutil.copy2(cls_file, gt_ref_dest / cls_file.name)
                    logger.info(f"[Export] Reference GT copied: {gt_ref_file.name}")

            docker_images_info = {}
            docker_total_size = 0.0

            if request.include_images:
                images_dir = temp_path / "images"
                images_dir.mkdir()
                for img in images:
                    file_path = Path(img.get("file_path", ""))
                    if file_path.exists():
                        image_id = img.get("image_id", "")
                        dest_path = images_dir / f"{image_id}_{file_path.name}"
                        shutil.copy2(file_path, dest_path)

            if request.include_docker:
                docker_dir = temp_path / "docker"
                docker_dir.mkdir()
                images_out_dir = docker_dir / "images"
                images_out_dir.mkdir()

                docker_images_info = export_docker_images(
                    required_services, images_out_dir,
                    compress=request.compress_images,
                    port_offset=port_offset,
                    service_port_map=self.SERVICE_PORT_MAP,
                    source_prefix=source_prefix
                )

                for info in docker_images_info.values():
                    docker_total_size += info.size_mb

                generate_docker_compose(
                    required_services,
                    docker_dir / "docker-compose.yml",
                    port_offset=port_offset,
                    container_prefix=container_prefix,
                    service_port_map=self.SERVICE_PORT_MAP,
                    frontend_services=self.FRONTEND_SERVICES,
                    backend_to_frontend_map=self.BACKEND_TO_FRONTEND_MAP,
                )

                scripts_dir = temp_path / "scripts"
                generate_import_scripts(
                    scripts_dir, required_services,
                    port_offset=port_offset,
                    container_prefix=container_prefix,
                    service_port_map=self.SERVICE_PORT_MAP,
                    frontend_services=self.FRONTEND_SERVICES,
                )

            readme = generate_readme(
                session_id, required_services, docker_images_info,
                request.include_docker, port_offset, container_prefix,
                service_port_map=self.SERVICE_PORT_MAP,
                frontend_services=self.FRONTEND_SERVICES,
            )
            with open(temp_path / "README.md", "w") as f:
                f.write(readme)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{session.get('filename', 'session')}_{export_id}_{timestamp}_self_contained.zip"
            export_path = self.export_dir / filename

            with zipfile.ZipFile(export_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for file_path in temp_path.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(temp_path)
                        zf.write(file_path, arcname)

        file_size = export_path.stat().st_size
        logger.info(
            f"[Export] Self-contained package: {filename} "
            f"({file_size / (1024*1024):.1f} MB, offset=+{port_offset})"
        )

        # 프론트엔드 URL 포함
        ui_urls = []
        if "blueprint-ai-bom-frontend" in required_services:
            frontend_port = 3000 + port_offset
            ui_urls.append(f"   ★ Blueprint AI BOM: http://localhost:{frontend_port}")
        if "web-ui" in required_services:
            webui_port = 5173 + port_offset
            ui_urls.append(f"   ★ BlueprintFlow 편집기: http://localhost:{webui_port}")

        frontend_url_info = ""
        if ui_urls:
            frontend_url_info = f"""
5. UI 접속:
{chr(10).join(ui_urls)}
"""

        import_instructions = f"""
1. 패키지 압축 해제:
   unzip {filename}

2. Import 스크립트 실행:
   # Linux/macOS
   chmod +x scripts/import.sh && ./scripts/import.sh

   # Windows (PowerShell)
   .\\scripts\\import.ps1

3. 서비스 상태 확인:
   cd docker && docker-compose ps

4. 포트 정보:
   - 포트 오프셋: +{port_offset}
   - 컨테이너 접두사: {container_prefix}-
   - 예: yolo-api (5005) → {container_prefix}-yolo-api:{5005 + port_offset}
{frontend_url_info}"""

        return SelfContainedExportResponse(
            success=True,
            session_id=session_id,
            export_id=export_id,
            filename=filename,
            file_path=str(export_path),
            file_size_bytes=file_size,
            created_at=datetime.now().isoformat(),
            included_services=required_services,
            docker_images=list(docker_images_info.values()),
            docker_images_size_mb=round(docker_total_size, 2),
            port_offset=port_offset,
            import_instructions=import_instructions,
        )


# Singleton
_self_contained_export_service: Optional[SelfContainedExportService] = None


def get_self_contained_export_service(
    export_dir: Path, upload_dir: Path
) -> SelfContainedExportService:
    global _self_contained_export_service
    if _self_contained_export_service is None:
        _self_contained_export_service = SelfContainedExportService(export_dir, upload_dir)
    return _self_contained_export_service
