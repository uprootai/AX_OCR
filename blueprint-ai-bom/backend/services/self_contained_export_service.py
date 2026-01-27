"""Self-contained Export Service - Docker 이미지 포함 Export

Phase 2F: Self-contained Export 패키지 생성
- Docker 이미지 Export
- docker-compose.yml 동적 생성 (포트 오프셋 적용)
- Import 스크립트 생성
"""

import base64
import json
import mimetypes
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
        "blueprint-ai-bom-frontend": 3000,  # BOM 프론트엔드
        "pid-composer-api": 5021,
        "table-detector-api": 5022,
        "web-ui": 5173,  # BlueprintFlow 편집기 (옵션)
    }

    # 백엔드 → 프론트엔드 자동 포함 매핑
    # 백엔드가 포함되면 해당 프론트엔드도 자동으로 포함
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
    # Blueprint AI BOM 세션에서 사용되는 feature 이름을 서비스로 변환
    # 주의: dimension_ocr는 YOLO 후처리로 별도 OCR 서비스 불필요
    FEATURE_TO_SERVICE_MAP = {
        "symbol_detection": ["yolo-api"],
        # dimension_ocr: YOLO 검출 결과에서 텍스트 추출 (별도 서비스 불필요)
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
        """워크플로우에서 필요한 Docker 서비스 추출

        Args:
            workflow_definition: 워크플로우 정의
            include_web_ui: web-ui (BlueprintFlow 편집기) 포함 여부
            session_features: 세션의 features 배열 (Blueprint AI BOM 용)

        백엔드 서비스가 포함되면 해당 프론트엔드도 자동으로 포함됩니다.
        """
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

        # 2. 세션 features에서 서비스 추출 (Blueprint AI BOM 세션용)
        if session_features:
            # Blueprint AI BOM에서 Export하는 경우 항상 BOM 백엔드 포함
            services.add("blueprint-ai-bom-backend")

            for feature in session_features:
                feature_key = feature.lower().replace("-", "_")
                if feature_key in self.FEATURE_TO_SERVICE_MAP:
                    # 첫 번째 서비스만 추가 (기본 서비스)
                    services.add(self.FEATURE_TO_SERVICE_MAP[feature_key][0])

        # 백엔드가 포함되면 프론트엔드도 자동 포함
        frontends_to_add = set()
        for service in services:
            if service in self.BACKEND_TO_FRONTEND_MAP:
                frontends_to_add.add(self.BACKEND_TO_FRONTEND_MAP[service])
        services.update(frontends_to_add)

        # 옵션: web-ui (BlueprintFlow 편집기) 포함
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

    def get_docker_image_size(self, service_name: str, source_prefix: str = "") -> float:
        """Docker 이미지 크기 조회 (MB)

        Args:
            service_name: 서비스 이름 (예: yolo-api)
            source_prefix: 소스 이미지 접두사 (예: poc_, poc-)
        """
        # 여러 이미지 이름 형식 시도 (prefix 있는 것, 없는 것)
        image_names_to_try = [
            f"{source_prefix}{service_name}:latest",
            f"{service_name}:latest",
        ]

        for image_name in image_names_to_try:
            try:
                result = subprocess.run(
                    ["docker", "image", "inspect", image_name,
                     "--format", "{{.Size}}"],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    size_bytes = int(result.stdout.strip())
                    return round(size_bytes / (1024 * 1024), 2)
            except Exception as e:
                logger.debug(f"Image not found: {image_name}")
                continue

        logger.warning(f"Failed to get image size for {service_name}")
        return 0.0

    def export_docker_images(
        self,
        services: List[str],
        output_dir: Path,
        compress: bool,
        port_offset: int,
        source_prefix: str = ""
    ) -> Dict[str, DockerImageInfo]:
        """Docker 이미지를 tar 파일로 저장

        Args:
            services: 서비스 목록
            output_dir: 출력 디렉토리
            compress: gzip 압축 여부
            port_offset: 포트 오프셋
            source_prefix: 소스 이미지 접두사 (예: poc_, poc-)
        """
        results = {}
        output_dir.mkdir(parents=True, exist_ok=True)

        for service in services:
            # 여러 이미지 이름 형식 시도
            image_names_to_try = [
                f"{source_prefix}{service}:latest",
                f"{service}:latest",
            ]

            found_image = None
            for img_name in image_names_to_try:
                # 이미지 존재 확인
                check_result = subprocess.run(
                    ["docker", "image", "inspect", img_name],
                    capture_output=True, text=True
                )
                if check_result.returncode == 0:
                    found_image = img_name
                    break

            if not found_image:
                logger.warning(f"Docker image not found for {service}, skipping...")
                continue

            # 출력 파일은 항상 표준 이름 사용 (prefix 없이)
            target_image_name = f"{service}:latest"
            file_ext = ".tar.gz" if compress else ".tar"
            output_file = output_dir / f"{service}{file_ext}"

            try:
                # 소스 이미지를 표준 이름으로 태그 (import 시 일관성 위해)
                if found_image != target_image_name:
                    subprocess.run(
                        ["docker", "tag", found_image, target_image_name],
                        check=True, timeout=30
                    )
                    logger.info(f"[Export] Tagged {found_image} as {target_image_name}")

                # 이미지 저장
                if compress:
                    cmd = f"docker save {target_image_name} | gzip > {output_file}"
                    subprocess.run(cmd, shell=True, check=True, timeout=600)
                else:
                    subprocess.run(
                        ["docker", "save", target_image_name, "-o", str(output_file)],
                        check=True, timeout=600
                    )

                size_mb = round(output_file.stat().st_size / (1024 * 1024), 2)
                original_port = self.SERVICE_PORT_MAP.get(service, 5000)
                mapped_port = original_port + port_offset

                results[service] = DockerImageInfo(
                    service_name=service,
                    image_name=target_image_name,
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

        # Nginx 설정 파일 생성 (Frontend용)
        if "blueprint-ai-bom-frontend" in services:
            self._generate_nginx_config(output_dir, container_prefix)

        # BOM Backend 포트 계산
        bom_backend_port = self.SERVICE_PORT_MAP.get("blueprint-ai-bom-backend", 5020) + port_offset

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

# [1/5] Docker 이미지 로드
echo "[1/5] Loading Docker images..."
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

# [2/5] Docker 네트워크 생성
echo ""
echo "[2/5] Creating Docker network..."
docker network create {container_prefix}_network 2>/dev/null || echo "  Network already exists"

# [3/5] 서비스 시작
echo ""
echo "[3/5] Starting services..."
cd docker
docker-compose up -d

# [4/5] Frontend Nginx 설정 업데이트
FRONTEND_CONTAINER="{container_prefix}-blueprint-ai-bom-frontend"
if docker ps --format "{{{{.Names}}}}" | grep -q "$FRONTEND_CONTAINER"; then
    echo ""
    echo "[4/5] Updating frontend nginx configuration..."
    docker cp ../scripts/nginx.conf "$FRONTEND_CONTAINER":/etc/nginx/conf.d/default.conf
    docker exec "$FRONTEND_CONTAINER" nginx -s reload 2>/dev/null || true
    echo "  Nginx configuration updated"
fi

# [5/5] 세션 데이터 자동 복원
cd "$SCRIPT_DIR/.."
if [ -f "session_import.json" ]; then
    echo ""
    echo "[5/5] Restoring session data..."

    # 백엔드가 준비될 때까지 대기 (최대 30초)
    for i in {{1..30}}; do
        if curl -s "http://localhost:{bom_backend_port}/health" | grep -q "healthy"; then
            break
        fi
        echo "  Waiting for backend to be ready... ($i/30)"
        sleep 1
    done

    # 세션 Import
    IMPORT_RESULT=$(curl -s -X POST "http://localhost:{bom_backend_port}/sessions/import" \\
        -F "file=@session_import.json" 2>/dev/null || echo "failed")

    if echo "$IMPORT_RESULT" | grep -q "session_id"; then
        SESSION_ID=$(echo "$IMPORT_RESULT" | grep -o '"session_id":"[^"]*"' | cut -d'"' -f4)
        echo "  ✅ Session restored: $SESSION_ID"
    else
        echo "  ⚠️  Session restore failed (you can manually import session_import.json)"
    fi
else
    echo ""
    echo "[5/5] No session data to restore (session_import.json not found)"
fi

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
$RootDir = Get-Location

# [1/5] Docker 이미지 로드
Write-Host "[1/5] Loading Docker images..." -ForegroundColor Yellow

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

# [2/5] Docker 네트워크 생성
Write-Host ""
Write-Host "[2/5] Creating Docker network..." -ForegroundColor Yellow
docker network create {container_prefix}_network 2>$null
if ($LASTEXITCODE -ne 0) {{ Write-Host "  Network already exists" }}

# [3/5] 서비스 시작
Write-Host ""
Write-Host "[3/5] Starting services..." -ForegroundColor Yellow
Set-Location docker
docker-compose up -d

# [4/5] Frontend Nginx 설정 업데이트
$FrontendContainer = "{container_prefix}-blueprint-ai-bom-frontend"
$RunningContainers = docker ps --format "{{{{.Names}}}}"
if ($RunningContainers -match $FrontendContainer) {{
    Write-Host ""
    Write-Host "[4/5] Updating frontend nginx configuration..." -ForegroundColor Yellow
    docker cp "..\\scripts\\nginx.conf" "${{FrontendContainer}}:/etc/nginx/conf.d/default.conf"
    docker exec $FrontendContainer nginx -s reload 2>$null
    Write-Host "  Nginx configuration updated"
}}

# [5/5] 세션 데이터 자동 복원
Set-Location $RootDir
if (Test-Path "session_import.json") {{
    Write-Host ""
    Write-Host "[5/5] Restoring session data..." -ForegroundColor Yellow

    # 백엔드가 준비될 때까지 대기 (최대 30초)
    for ($i = 1; $i -le 30; $i++) {{
        try {{
            $health = Invoke-RestMethod -Uri "http://localhost:{bom_backend_port}/health" -Method Get -ErrorAction SilentlyContinue
            if ($health.status -eq "healthy") {{ break }}
        }} catch {{}}
        Write-Host "  Waiting for backend to be ready... ($i/30)"
        Start-Sleep -Seconds 1
    }}

    # 세션 Import
    try {{
        $importResult = Invoke-RestMethod -Uri "http://localhost:{bom_backend_port}/sessions/import" `
            -Method Post `
            -Form @{{ file = Get-Item "session_import.json" }} `
            -ErrorAction SilentlyContinue

        if ($importResult.session_id) {{
            Write-Host "  Session restored: $($importResult.session_id)" -ForegroundColor Green
        }}
    }} catch {{
        Write-Host "  Session restore failed (you can manually import session_import.json)" -ForegroundColor Yellow
    }}
}} else {{
    Write-Host ""
    Write-Host "[5/5] No session data to restore (session_import.json not found)" -ForegroundColor Yellow
}}

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

    def _generate_nginx_config(
        self,
        output_dir: Path,
        container_prefix: str
    ) -> None:
        """Frontend용 Nginx 설정 파일 생성"""
        backend_container = f"{container_prefix}-blueprint-ai-bom-backend"

        nginx_config = f'''server {{
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    location / {{
        try_files $uri $uri/ /index.html;
    }}

    location /api {{
        proxy_pass http://{backend_container}:5020;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }}

    location /sessions {{
        proxy_pass http://{backend_container}:5020;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }}

    location /detection {{
        proxy_pass http://{backend_container}:5020;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }}

    location /bom {{
        proxy_pass http://{backend_container}:5020;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }}

    location /health {{
        proxy_pass http://{backend_container}:5020;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }}

    location /export {{
        proxy_pass http://{backend_container}:5020;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }}

    location /customer {{
        proxy_pass http://{backend_container}:5020;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }}

    location /analysis {{
        proxy_pass http://{backend_container}:5020;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }}

    location /verification {{
        proxy_pass http://{backend_container}:5020;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }}

    location /feedback {{
        proxy_pass http://{backend_container}:5020;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }}

    location /projects {{
        proxy_pass http://{backend_container}:5020;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }}

    location /config {{
        proxy_pass http://{backend_container}:5020;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }}

    location /openapi.json {{
        proxy_pass http://{backend_container}:5020;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }}

    location /docs {{
        proxy_pass http://{backend_container}:5020;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }}

    location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg)$ {{
        expires 1y;
        add_header Cache-Control "public, immutable";
    }}
}}
'''
        nginx_path = output_dir / "nginx.conf"
        with open(nginx_path, "w") as f:
            f.write(nginx_config)

        logger.info(f"[Export] Nginx config generated: {nginx_path}")

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
        upload_dir: Path
    ) -> bool:
        """Import 엔드포인트와 호환되는 세션 JSON 생성

        Args:
            session: 세션 데이터
            output_path: 출력 파일 경로
            upload_dir: 업로드 디렉토리 (이미지 파일 위치)

        Returns:
            bool: 성공 여부
        """
        session_id = session.get("session_id", "")
        filename = session.get("filename", "")

        # 이미지 파일 찾기 및 base64 인코딩
        image_data = None
        session_dir = upload_dir / session_id
        logger.info(f"[Export] Looking for session image in: {session_dir}, filename: {filename}")

        if session_dir.exists():
            # 1. 세션의 filename으로 먼저 찾기
            if filename:
                img_path = session_dir / filename
                if img_path.exists():
                    image_data = self._encode_image_file(img_path, filename)

            # 2. filename으로 못 찾으면 이미지 확장자로 찾기
            if not image_data:
                for ext in [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".gif"]:
                    for pattern in [f"original{ext}", f"*{ext}"]:
                        if pattern.startswith("*"):
                            # glob 패턴으로 찾기
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
            logger.warning(f"[Export] No image found for session {session_id}, session_import.json will not have image data")

        # Import 엔드포인트 호환 형식 생성
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
        """Self-contained Export 미리보기

        Args:
            session: 세션 데이터
            template: 템플릿 데이터 (옵션)
            port_offset: 포트 오프셋
            include_web_ui: web-ui (BlueprintFlow 편집기) 포함 여부
            source_prefix: 소스 이미지 접두사 (예: poc_, poc-)
        """
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

        # 크기 및 포트 매핑 조회
        estimated_sizes = {}
        port_mapping = {}
        total_size = 0.0

        for service in required_services:
            size = self.get_docker_image_size(service, source_prefix=source_prefix)
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

            # Import 엔드포인트 호환 세션 파일 생성 (자동 복원용)
            self.generate_importable_session(
                session=session,
                output_path=temp_path / "session_import.json",
                upload_dir=self.upload_dir
            )

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
                    port_offset=port_offset,
                    source_prefix=source_prefix
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
        ui_urls = []
        if "blueprint-ai-bom-frontend" in required_services:
            frontend_port = 3000 + port_offset
            ui_urls.append(f"   ★ Blueprint AI BOM: http://localhost:{frontend_port}")
        if "web-ui" in required_services:
            webui_port = 5173 + port_offset
            ui_urls.append(f"   ★ BlueprintFlow 편집기: http://localhost:{webui_port}")

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
