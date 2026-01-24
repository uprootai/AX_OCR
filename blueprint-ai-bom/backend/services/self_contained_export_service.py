"""Self-contained Export Service - Docker 이미지 포함 Export

Phase 2F: Self-contained Export 패키지 생성
- Docker 이미지 Export
- docker-compose.yml 동적 생성 (포트 오프셋 적용)
- Import 스크립트 생성
"""

import json
import os
import subprocess
import tempfile
import uuid
import zipfile
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

import yaml

from schemas.export import (
    SelfContainedExportRequest,
    SelfContainedExportResponse,
    SelfContainedPreview,
    DockerImageInfo,
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
        "blueprint-ai-bom-frontend": 3000,  # 프론트엔드 추가
        "pid-composer-api": 5021,
        "table-detector-api": 5022,
    }

    # 백엔드 → 프론트엔드 자동 포함 매핑
    # 백엔드가 포함되면 해당 프론트엔드도 자동으로 포함
    BACKEND_TO_FRONTEND_MAP = {
        "blueprint-ai-bom-backend": "blueprint-ai-bom-frontend",
    }

    # 프론트엔드 서비스 목록 (docker-compose 생성 시 특별 처리)
    FRONTEND_SERVICES = {"blueprint-ai-bom-frontend"}

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
        workflow_definition: Dict[str, Any]
    ) -> List[str]:
        """워크플로우에서 필요한 Docker 서비스 추출

        백엔드 서비스가 포함되면 해당 프론트엔드도 자동으로 포함됩니다.
        """
        services = {"gateway-api"}  # Gateway는 항상 필요

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

        # 백엔드가 포함되면 프론트엔드도 자동 포함
        frontends_to_add = set()
        for service in services:
            if service in self.BACKEND_TO_FRONTEND_MAP:
                frontends_to_add.add(self.BACKEND_TO_FRONTEND_MAP[service])
        services.update(frontends_to_add)

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

    def get_docker_image_size(self, service_name: str) -> float:
        """Docker 이미지 크기 조회 (MB)"""
        try:
            result = subprocess.run(
                ["docker", "image", "inspect", f"{service_name}:latest",
                 "--format", "{{.Size}}"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                size_bytes = int(result.stdout.strip())
                return round(size_bytes / (1024 * 1024), 2)
        except Exception as e:
            logger.warning(f"Failed to get image size for {service_name}: {e}")
        return 0.0

    def export_docker_images(
        self,
        services: List[str],
        output_dir: Path,
        compress: bool,
        port_offset: int
    ) -> Dict[str, DockerImageInfo]:
        """Docker 이미지를 tar 파일로 저장"""
        results = {}
        output_dir.mkdir(parents=True, exist_ok=True)

        for service in services:
            image_name = f"{service}:latest"
            file_ext = ".tar.gz" if compress else ".tar"
            output_file = output_dir / f"{service}{file_ext}"

            try:
                if compress:
                    cmd = f"docker save {image_name} | gzip > {output_file}"
                    subprocess.run(cmd, shell=True, check=True, timeout=600)
                else:
                    subprocess.run(
                        ["docker", "save", image_name, "-o", str(output_file)],
                        check=True, timeout=600
                    )

                size_mb = round(output_file.stat().st_size / (1024 * 1024), 2)
                original_port = self.SERVICE_PORT_MAP.get(service, 5000)
                mapped_port = original_port + port_offset

                results[service] = DockerImageInfo(
                    service_name=service,
                    image_name=image_name,
                    file_name=output_file.name,
                    size_mb=size_mb,
                    original_port=original_port,
                    mapped_port=mapped_port
                )
                logger.info(f"[Export] Docker image saved: {service} ({size_mb} MB)")

            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to export Docker image {service}: {e}")
            except subprocess.TimeoutExpired:
                logger.error(f"Timeout exporting Docker image {service}")

        return results

    def generate_docker_compose(
        self,
        services: List[str],
        output_path: Path,
        port_offset: int,
        container_prefix: str
    ) -> str:
        """docker-compose.yml 생성 (포트 오프셋 및 컨테이너 접두사 적용)"""
        compose_content = {
            "version": "3.8",
            "services": {},
            "networks": {
                "imported_network": {
                    "name": f"{container_prefix}_network",
                    "driver": "bridge"
                }
            }
        }

        for service in services:
            original_port = self.SERVICE_PORT_MAP.get(service, 5000)
            mapped_port = original_port + port_offset
            container_name = f"{container_prefix}-{service}"

            # 환경변수에서 내부 URL도 오프셋 적용
            env_vars = ["PYTHONUNBUFFERED=1"]

            if service == "gateway-api":
                env_vars.extend([
                    f"GATEWAY_PORT={original_port}",
                    "GATEWAY_WORKERS=1",
                ])
                # Gateway가 다른 서비스 호출 시 오프셋 적용된 URL 사용
                for svc in services:
                    if svc != "gateway-api":
                        svc_port = self.SERVICE_PORT_MAP.get(svc, 5000)
                        svc_name = f"{container_prefix}-{svc}"
                        env_key = svc.upper().replace("-", "_") + "_URL"
                        env_vars.append(f"{env_key}=http://{svc_name}:{svc_port}")

            elif service == "yolo-api":
                env_vars.append(f"YOLO_API_PORT={original_port}")
            elif service == "edocr2-v2-api":
                env_vars.append(f"EDOCR2_PORT={original_port}")
            elif service == "paddleocr-api":
                env_vars.extend([f"PADDLEOCR_PORT={original_port}", "USE_GPU=false"])
            elif service == "blueprint-ai-bom-backend":
                yolo_container = f"{container_prefix}-yolo-api"
                env_vars.extend([
                    f"BOM_PORT={original_port}",
                    f"YOLO_API_URL=http://{yolo_container}:5005"
                ])
            elif service == "blueprint-ai-bom-frontend":
                # 프론트엔드는 특별 처리 (아래에서 별도 생성)
                pass
            else:
                # 기본 포트 환경변수
                port_env_key = service.upper().replace("-", "_") + "_PORT"
                env_vars.append(f"{port_env_key}={original_port}")

            # 프론트엔드 서비스는 별도 처리
            if service in self.FRONTEND_SERVICES:
                backend_service = None
                # 해당 프론트엔드의 백엔드 찾기
                for backend, frontend in self.BACKEND_TO_FRONTEND_MAP.items():
                    if frontend == service:
                        backend_service = backend
                        break

                backend_container = f"{container_prefix}-{backend_service}" if backend_service else None

                compose_content["services"][service] = {
                    "image": f"{service}:latest",
                    "container_name": container_name,
                    "ports": [f"{mapped_port}:80"],  # nginx는 80 포트
                    "environment": [
                        # nginx가 백엔드로 프록시할 수 있도록 설정
                        f"BACKEND_URL=http://{backend_container}:5020" if backend_container else "",
                    ],
                    "depends_on": [backend_service] if backend_service and backend_service in services else [],
                    "networks": ["imported_network"],
                    "restart": "unless-stopped"
                }
                # 빈 환경변수 제거
                compose_content["services"][service]["environment"] = [
                    e for e in compose_content["services"][service]["environment"] if e
                ]
                continue  # 다음 서비스로

            compose_content["services"][service] = {
                "image": f"{service}:latest",
                "container_name": container_name,
                "ports": [f"{mapped_port}:{original_port}"],
                "environment": env_vars,
                "networks": ["imported_network"],
                "restart": "unless-stopped"
            }

        with open(output_path, "w") as f:
            yaml.dump(compose_content, f, default_flow_style=False, sort_keys=False)

        return str(output_path)

    def generate_import_scripts(
        self,
        output_dir: Path,
        services: List[str],
        port_offset: int,
        container_prefix: str
    ) -> None:
        """Import 스크립트 생성"""
        output_dir.mkdir(parents=True, exist_ok=True)

        # Linux/macOS import.sh
        sh_script = f'''#!/bin/bash
set -e

echo "=========================================="
echo "  Blueprint AI BOM - Self-contained Import"
echo "  (Port Offset: +{port_offset})"
echo "=========================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
cd "$SCRIPT_DIR/.."

# [1/3] Docker 이미지 로드
echo "[1/3] Loading Docker images..."
for img in docker/images/*.tar.gz; do
    if [ -f "$img" ]; then
        echo "  Loading: $(basename "$img")"
        gunzip -c "$img" | docker load
    fi
done

for img in docker/images/*.tar; do
    if [ -f "$img" ]; then
        echo "  Loading: $(basename "$img")"
        docker load -i "$img"
    fi
done

# [2/3] Docker 네트워크 생성
echo ""
echo "[2/3] Creating Docker network..."
docker network create {container_prefix}_network 2>/dev/null || echo "  Network already exists"

# [3/3] 서비스 시작
echo ""
echo "[3/3] Starting services..."
cd docker
docker-compose up -d

echo ""
echo "=========================================="
echo "  Import Complete!"
echo "=========================================="
echo ""
echo "컨테이너 접두사: {container_prefix}-"
echo "포트 오프셋: +{port_offset}"
echo ""
'''
        # 프론트엔드 URL 먼저 표시
        frontend_services = [s for s in services if s in self.FRONTEND_SERVICES]
        backend_services = [s for s in services if s not in self.FRONTEND_SERVICES]

        if frontend_services:
            sh_script += 'echo "=========================================="\n'
            sh_script += 'echo "  UI 접속 URL:"\n'
            sh_script += 'echo "=========================================="\n'
            for service in frontend_services:
                original_port = self.SERVICE_PORT_MAP.get(service, 3000)
                mapped_port = original_port + port_offset
                sh_script += f'echo "  ★ http://localhost:{mapped_port}"\n'
            sh_script += 'echo ""\n'

        sh_script += 'echo "API endpoints:"\n'
        for service in backend_services:
            original_port = self.SERVICE_PORT_MAP.get(service, 5000)
            mapped_port = original_port + port_offset
            sh_script += f'echo "  - {container_prefix}-{service}: http://localhost:{mapped_port}"\n'

        sh_script += f'''
echo ""
echo "서비스 상태 확인:"
echo "  cd docker && docker-compose ps"
echo ""
echo "서비스 중지:"
echo "  cd docker && docker-compose down"
'''

        sh_path = output_dir / "import.sh"
        with open(sh_path, "w", newline="\n") as f:
            f.write(sh_script)
        os.chmod(sh_path, 0o755)

        # Windows import.ps1
        ps_script = f'''# Blueprint AI BOM - Self-contained Import (Windows)
# Port Offset: +{port_offset}

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Blueprint AI BOM - Self-contained Import" -ForegroundColor Cyan
Write-Host "  (Port Offset: +{port_offset})" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location "$ScriptDir\\.."

# [1/3] Docker 이미지 로드
Write-Host "[1/3] Loading Docker images..." -ForegroundColor Yellow

$gzFiles = Get-ChildItem -Path "docker\\images\\*.tar.gz" -ErrorAction SilentlyContinue
foreach ($file in $gzFiles) {{
    Write-Host "  Loading: $($file.Name)"
    & gzip -d -c $file.FullName | docker load
}}

$tarFiles = Get-ChildItem -Path "docker\\images\\*.tar" -ErrorAction SilentlyContinue
foreach ($file in $tarFiles) {{
    Write-Host "  Loading: $($file.Name)"
    docker load -i $file.FullName
}}

# [2/3] Docker 네트워크 생성
Write-Host ""
Write-Host "[2/3] Creating Docker network..." -ForegroundColor Yellow
docker network create {container_prefix}_network 2>$null
if ($LASTEXITCODE -ne 0) {{ Write-Host "  Network already exists" }}

# [3/3] 서비스 시작
Write-Host ""
Write-Host "[3/3] Starting services..." -ForegroundColor Yellow
Set-Location docker
docker-compose up -d

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "  Import Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Container prefix: {container_prefix}-"
Write-Host "Port offset: +{port_offset}"
Write-Host ""
'''
        # 프론트엔드 URL 먼저 표시
        if frontend_services:
            ps_script += 'Write-Host "==========================================" -ForegroundColor Magenta\n'
            ps_script += 'Write-Host "  UI Access URL:" -ForegroundColor Magenta\n'
            ps_script += 'Write-Host "==========================================" -ForegroundColor Magenta\n'
            for service in frontend_services:
                original_port = self.SERVICE_PORT_MAP.get(service, 3000)
                mapped_port = original_port + port_offset
                ps_script += f'Write-Host "  * http://localhost:{mapped_port}" -ForegroundColor Yellow\n'
            ps_script += 'Write-Host ""\n'

        ps_script += 'Write-Host "API endpoints:"\n'
        for service in backend_services:
            original_port = self.SERVICE_PORT_MAP.get(service, 5000)
            mapped_port = original_port + port_offset
            ps_script += f'Write-Host "  - {container_prefix}-{service}: http://localhost:{mapped_port}"\n'

        ps_script += '''
Write-Host ""
Write-Host "Check status: cd docker; docker-compose ps"
Write-Host "Stop services: cd docker; docker-compose down"
'''

        ps_path = output_dir / "import.ps1"
        with open(ps_path, "w", newline="\r\n") as f:
            f.write(ps_script)

        logger.info(f"[Export] Import scripts generated in {output_dir}")

    def get_preview(
        self,
        session: Dict[str, Any],
        template: Optional[Dict[str, Any]] = None,
        port_offset: int = 10000,
    ) -> SelfContainedPreview:
        """Self-contained Export 미리보기"""
        session_id = session.get("session_id", "")

        workflow_def = (
            template.get("workflow_definition", {})
            if template
            else session.get("workflow_definition", {})
        )
        required_services = self.detect_required_services(workflow_def)
        node_types = self.get_workflow_node_types(workflow_def)

        # 크기 및 포트 매핑 조회
        estimated_sizes = {}
        port_mapping = {}
        total_size = 0.0

        for service in required_services:
            size = self.get_docker_image_size(service)
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

        workflow_def = (
            template.get("workflow_definition", {})
            if template
            else session.get("workflow_definition", {})
        )
        required_services = self.detect_required_services(workflow_def)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            images = session.get("images", [])
            detections = session.get("detections", [])

            # 포트 매핑 정보 생성
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

                docker_images_info = self.export_docker_images(
                    required_services, images_out_dir,
                    compress=request.compress_images,
                    port_offset=port_offset
                )

                for info in docker_images_info.values():
                    docker_total_size += info.size_mb

                self.generate_docker_compose(
                    required_services,
                    docker_dir / "docker-compose.yml",
                    port_offset=port_offset,
                    container_prefix=container_prefix
                )

                scripts_dir = temp_path / "scripts"
                self.generate_import_scripts(
                    scripts_dir, required_services,
                    port_offset=port_offset,
                    container_prefix=container_prefix
                )

            readme = self._generate_readme(
                session_id, required_services, docker_images_info,
                request.include_docker, port_offset, container_prefix
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
        frontend_url_info = ""
        if "blueprint-ai-bom-frontend" in required_services:
            frontend_port = 3000 + port_offset
            frontend_url_info = f"""
5. UI 접속:
   브라우저에서 http://localhost:{frontend_port} 접속
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

    def _generate_readme(
        self,
        session_id: str,
        services: List[str],
        docker_images: Dict[str, DockerImageInfo],
        include_docker: bool,
        port_offset: int,
        container_prefix: str
    ) -> str:
        """README.md 생성"""
        # 프론트엔드와 백엔드 분리
        frontend_services = [s for s in services if s in self.FRONTEND_SERVICES]
        backend_services = [s for s in services if s not in self.FRONTEND_SERVICES]

        # 프론트엔드 URL 계산
        frontend_url = ""
        if "blueprint-ai-bom-frontend" in services:
            frontend_port = 3000 + port_offset
            frontend_url = f"http://localhost:{frontend_port}"

        readme = f"""# Blueprint AI BOM - Self-contained Export Package

## 세션 정보
- **Session ID**: {session_id}
- **Export Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Export Type**: Self-contained (Docker 이미지 포함)
- **Port Offset**: +{port_offset}
- **Container Prefix**: {container_prefix}-

"""
        # 프론트엔드가 있으면 Quick Start 섹션 추가
        if frontend_url:
            readme += f"""## 🚀 Quick Start

Import 후 브라우저에서 바로 사용 가능:

**UI 접속 URL**: **{frontend_url}**

"""

        readme += """## 포함된 서비스

"""
        # 프론트엔드 섹션
        if frontend_services:
            readme += """### 🖥️ 프론트엔드 (UI)

| 서비스 | Import 포트 | 접속 URL |
|--------|-------------|----------|
"""
            for service in frontend_services:
                original_port = self.SERVICE_PORT_MAP.get(service, 0)
                mapped_port = original_port + port_offset
                size_info = ""
                if service in docker_images:
                    size_info = f" ({docker_images[service].size_mb} MB)"
                readme += f"| {service}{size_info} | **{mapped_port}** | http://localhost:{mapped_port} |\n"

            readme += "\n"

        # 백엔드 섹션
        if backend_services:
            readme += """### ⚙️ 백엔드 (API)

| 서비스 | 원본 포트 | Import 포트 | 컨테이너 이름 |
|--------|----------|-------------|--------------|
"""
            for service in backend_services:
                original_port = self.SERVICE_PORT_MAP.get(service, 0)
                mapped_port = original_port + port_offset
                container_name = f"{container_prefix}-{service}"
                size_info = ""
                if service in docker_images:
                    size_info = f" ({docker_images[service].size_mb} MB)"
                readme += f"| {service} | {original_port} | **{mapped_port}** | {container_name}{size_info} |\n"

        if include_docker:
            readme += f"""
## Import 방법

### Linux/macOS
```bash
unzip <패키지명>.zip -d blueprint-export
cd blueprint-export
chmod +x scripts/import.sh
./scripts/import.sh
```

### Windows (PowerShell)
```powershell
Expand-Archive <패키지명>.zip -DestinationPath blueprint-export
cd blueprint-export
.\\scripts\\import.ps1
```

## 서비스 확인

```bash
# 컨테이너 상태
docker ps --filter "name={container_prefix}"

# 로그 확인
docker logs {container_prefix}-yolo-api

# API 테스트
curl http://localhost:{5005 + port_offset}/health
```

## 요구사항
- Docker 20.10+
- docker-compose 2.0+

## 서비스 중지
```bash
cd docker && docker-compose down
docker network rm {container_prefix}_network
```
"""
        return readme


# Singleton
_self_contained_export_service: Optional[SelfContainedExportService] = None


def get_self_contained_export_service(
    export_dir: Path, upload_dir: Path
) -> SelfContainedExportService:
    global _self_contained_export_service
    if _self_contained_export_service is None:
        _self_contained_export_service = SelfContainedExportService(export_dir, upload_dir)
    return _self_contained_export_service
