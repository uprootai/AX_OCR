"""Export Script Generator - Import 스크립트 및 설정 파일 생성

self_contained_export_service.py에서 추출된 모듈:
- generate_import_scripts(): Linux/Windows import 스크립트 생성
- generate_nginx_config(): Frontend용 Nginx 설정 파일 생성
- generate_readme(): README.md 생성
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from schemas.export import DockerImageInfo

logger = logging.getLogger(__name__)


def generate_import_scripts(
    output_dir: Path,
    services: List[str],
    port_offset: int,
    container_prefix: str,
    service_port_map: Dict[str, int],
    frontend_services: Set[str],
) -> None:
    """Import 스크립트 생성"""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Nginx 설정 파일 생성 (Frontend용)
    if "blueprint-ai-bom-frontend" in services:
        generate_nginx_config(output_dir, container_prefix)

    # BOM Backend 포트 계산
    bom_backend_port = service_port_map.get("blueprint-ai-bom-backend", 5020) + port_offset

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

# [5/7] 백엔드 대기
cd "$SCRIPT_DIR/.."
echo ""
echo "[5/8] Waiting for backend to be ready..."
for i in {{1..30}}; do
    if curl -s "http://localhost:{bom_backend_port}/health" | grep -q "healthy"; then
        echo "  Backend is ready"
        break
    fi
    echo "  Waiting for backend... ($i/30)"
    sleep 1
done

# [6/8] 프로젝트 및 GT 복원
PROJECT_ID=""
if [ -f "project.json" ]; then
    echo ""
    echo "[6/8] Restoring project and GT labels..."
    PROJECT_RESULT=$(curl -s -X POST "http://localhost:{bom_backend_port}/projects" \\
        -H "Content-Type: application/json" \\
        -d @project.json 2>/dev/null || echo "failed")

    if echo "$PROJECT_RESULT" | grep -q "project_id"; then
        PROJECT_ID=$(echo "$PROJECT_RESULT" | grep -o '"project_id":"[^"]*"' | cut -d'"' -f4)
        echo "  ✅ Project restored: $PROJECT_ID"

        # GT 라벨 업로드
        if [ -d "gt_labels" ] && [ -n "$PROJECT_ID" ]; then
            GT_COUNT=$(ls -1 gt_labels/*.txt 2>/dev/null | wc -l)
            if [ "$GT_COUNT" -gt 0 ]; then
                GT_FILES=""
                for f in gt_labels/*.txt; do
                    GT_FILES="$GT_FILES -F files=@$f"
                done
                GT_RESULT=$(curl -s -X POST "http://localhost:{bom_backend_port}/projects/$PROJECT_ID/gt" \\
                    $GT_FILES 2>/dev/null || echo "failed")
                echo "  ✅ GT labels uploaded: $GT_COUNT files"
            fi
        fi
    else
        echo "  ⚠️  Project restore failed"
    fi
else
    echo ""
    echo "[6/8] No project data to restore (project.json not found)"
fi

# [7/8] 참조 GT 라벨 주입 (test_drawings/labels/)
BACKEND_CONTAINER="{container_prefix}-blueprint-ai-bom-backend"
if [ -d "gt_reference" ]; then
    GT_REF_COUNT=$(ls -1 gt_reference/*.txt 2>/dev/null | wc -l)
    if [ "$GT_REF_COUNT" -gt 0 ]; then
        echo ""
        echo "[7/8] Injecting reference GT labels into backend..."
        docker exec "$BACKEND_CONTAINER" mkdir -p /app/test_drawings/labels 2>/dev/null || true
        for f in gt_reference/*.txt; do
            docker cp "$f" "$BACKEND_CONTAINER":/app/test_drawings/labels/
        done
        echo "  ✅ Reference GT labels injected: $GT_REF_COUNT files"
    fi
else
    echo ""
    echo "[7/8] No reference GT labels to inject"
fi

# [8/8] 세션 데이터 자동 복원
if [ -f "session_import.json" ]; then
    echo ""
    echo "[8/8] Restoring session data..."

    # 프로젝트 연결 파라미터
    IMPORT_URL="http://localhost:{bom_backend_port}/sessions/import"
    if [ -n "$PROJECT_ID" ]; then
        IMPORT_URL="$IMPORT_URL?project_id=$PROJECT_ID"
    fi

    IMPORT_RESULT=$(curl -s -X POST "$IMPORT_URL" \\
        -F "file=@session_import.json" 2>/dev/null || echo "failed")

    if echo "$IMPORT_RESULT" | grep -q "session_id"; then
        SESSION_ID=$(echo "$IMPORT_RESULT" | grep -o '"session_id":"[^"]*"' | cut -d'"' -f4)
        echo "  ✅ Session restored: $SESSION_ID"
        if [ -n "$PROJECT_ID" ]; then
            echo "  ✅ Session linked to project: $PROJECT_ID"
        fi
    else
        echo "  ⚠️  Session restore failed (you can manually import session_import.json)"
    fi
else
    echo ""
    echo "[8/8] No session data to restore (session_import.json not found)"
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
    frontend_svc_list = [s for s in services if s in frontend_services]
    backend_svc_list = [s for s in services if s not in frontend_services]

    if frontend_svc_list:
        sh_script += 'echo "=========================================="\n'
        sh_script += 'echo "  UI 접속 URL:"\n'
        sh_script += 'echo "=========================================="\n'
        for service in frontend_svc_list:
            original_port = service_port_map.get(service, 3000)
            mapped_port = original_port + port_offset
            sh_script += f'echo "  ★ http://localhost:{mapped_port}"\n'
        sh_script += 'echo ""\n'

    sh_script += 'echo "API endpoints:"\n'
    for service in backend_svc_list:
        original_port = service_port_map.get(service, 5000)
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

# [5/7] 백엔드 대기
Set-Location $RootDir
Write-Host ""
Write-Host "[5/8] Waiting for backend to be ready..." -ForegroundColor Yellow
for ($i = 1; $i -le 30; $i++) {{
    try {{
        $health = Invoke-RestMethod -Uri "http://localhost:{bom_backend_port}/health" -Method Get -ErrorAction SilentlyContinue
        if ($health.status -eq "healthy") {{
            Write-Host "  Backend is ready"
            break
        }}
    }} catch {{}}
    Write-Host "  Waiting for backend... ($i/30)"
    Start-Sleep -Seconds 1
}}

# [6/8] 프로젝트 및 GT 복원
$ProjectId = ""
if (Test-Path "project.json") {{
    Write-Host ""
    Write-Host "[6/8] Restoring project and GT labels..." -ForegroundColor Yellow
    try {{
        $projectData = Get-Content "project.json" -Raw
        $projectResult = Invoke-RestMethod -Uri "http://localhost:{bom_backend_port}/projects" `
            -Method Post `
            -Body $projectData `
            -ContentType "application/json" `
            -ErrorAction SilentlyContinue

        if ($projectResult.project_id) {{
            $ProjectId = $projectResult.project_id
            Write-Host "  Project restored: $ProjectId" -ForegroundColor Green

            # GT 라벨 업로드
            if ((Test-Path "gt_labels") -and $ProjectId) {{
                $gtFiles = Get-ChildItem -Path "gt_labels\\*.txt" -ErrorAction SilentlyContinue
                if ($gtFiles.Count -gt 0) {{
                    $form = @{{}}
                    foreach ($f in $gtFiles) {{
                        $form["files"] = Get-Item $f.FullName
                    }}
                    # 다중 파일 업로드는 curl 사용
                    $gtArgs = @("-s", "-X", "POST", "http://localhost:{bom_backend_port}/projects/$ProjectId/gt")
                    foreach ($f in $gtFiles) {{
                        $gtArgs += "-F"
                        $gtArgs += "files=@$($f.FullName)"
                    }}
                    & curl @gtArgs 2>$null | Out-Null
                    Write-Host "  GT labels uploaded: $($gtFiles.Count) files" -ForegroundColor Green
                }}
            }}
        }}
    }} catch {{
        Write-Host "  Project restore failed" -ForegroundColor Yellow
    }}
}} else {{
    Write-Host ""
    Write-Host "[6/8] No project data to restore (project.json not found)" -ForegroundColor Yellow
}}

# [7/8] 참조 GT 라벨 주입 (test_drawings/labels/)
$BackendContainer = "{container_prefix}-blueprint-ai-bom-backend"
if (Test-Path "gt_reference") {{
    $gtRefFiles = Get-ChildItem -Path "gt_reference\\*.txt" -ErrorAction SilentlyContinue
    if ($gtRefFiles.Count -gt 0) {{
        Write-Host ""
        Write-Host "[7/8] Injecting reference GT labels into backend..." -ForegroundColor Yellow
        docker exec $BackendContainer mkdir -p /app/test_drawings/labels 2>$null
        foreach ($f in $gtRefFiles) {{
            docker cp $f.FullName "${{BackendContainer}}:/app/test_drawings/labels/"
        }}
        Write-Host "  Reference GT labels injected: $($gtRefFiles.Count) files" -ForegroundColor Green
    }}
}} else {{
    Write-Host ""
    Write-Host "[7/8] No reference GT labels to inject" -ForegroundColor Yellow
}}

# [8/8] 세션 데이터 자동 복원
if (Test-Path "session_import.json") {{
    Write-Host ""
    Write-Host "[8/8] Restoring session data..." -ForegroundColor Yellow

    $importUrl = "http://localhost:{bom_backend_port}/sessions/import"
    if ($ProjectId) {{
        $importUrl = "$importUrl?project_id=$ProjectId"
    }}

    try {{
        $importResult = Invoke-RestMethod -Uri $importUrl `
            -Method Post `
            -Form @{{ file = Get-Item "session_import.json" }} `
            -ErrorAction SilentlyContinue

        if ($importResult.session_id) {{
            Write-Host "  Session restored: $($importResult.session_id)" -ForegroundColor Green
            if ($ProjectId) {{
                Write-Host "  Session linked to project: $ProjectId" -ForegroundColor Green
            }}
        }}
    }} catch {{
        Write-Host "  Session restore failed (you can manually import session_import.json)" -ForegroundColor Yellow
    }}
}} else {{
    Write-Host ""
    Write-Host "[8/8] No session data to restore (session_import.json not found)" -ForegroundColor Yellow
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
    if frontend_svc_list:
        ps_script += 'Write-Host "==========================================" -ForegroundColor Magenta\n'
        ps_script += 'Write-Host "  UI Access URL:" -ForegroundColor Magenta\n'
        ps_script += 'Write-Host "==========================================" -ForegroundColor Magenta\n'
        for service in frontend_svc_list:
            original_port = service_port_map.get(service, 3000)
            mapped_port = original_port + port_offset
            ps_script += f'Write-Host "  * http://localhost:{mapped_port}" -ForegroundColor Yellow\n'
        ps_script += 'Write-Host ""\n'

    ps_script += 'Write-Host "API endpoints:"\n'
    for service in backend_svc_list:
        original_port = service_port_map.get(service, 5000)
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


def generate_nginx_config(
    output_dir: Path,
    container_prefix: str,
) -> None:
    """Frontend용 Nginx 설정 파일 생성

    프론트엔드는 VITE_API_URL=/api 로 빌드되어 모든 API 요청이 /api/... 로 발생.
    /api/ prefix를 제거(rewrite)하고 백엔드로 전달해야 함.
    """
    backend_container = f"{container_prefix}-blueprint-ai-bom-backend"

    nginx_config = f'''server {{
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # API proxy — /api/ 프리픽스를 제거하고 백엔드로 전달
    # 프론트엔드는 VITE_API_URL=/api 로 빌드되어 모든 API 요청이 /api/... 로 발생
    location /api/ {{
        rewrite ^/api(/.*)$ $1 break;
        proxy_pass http://{backend_container}:5020;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 1800s;
        proxy_connect_timeout 60s;
        proxy_send_timeout 1800s;
    }}

    # Cache static assets
    location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg)$ {{
        expires 1y;
        add_header Cache-Control "public, immutable";
    }}

    # SPA routing — 모든 나머지 요청은 index.html로 (React Router 처리)
    location / {{
        try_files $uri $uri/ /index.html;
    }}
}}
'''
    nginx_path = output_dir / "nginx.conf"
    with open(nginx_path, "w") as f:
        f.write(nginx_config)

    logger.info(f"[Export] Nginx config generated: {nginx_path}")


def generate_readme(
    session_id: str,
    services: List[str],
    docker_images: Dict[str, DockerImageInfo],
    include_docker: bool,
    port_offset: int,
    container_prefix: str,
    service_port_map: Dict[str, int],
    frontend_services: Set[str],
) -> str:
    """README.md 생성"""
    # 프론트엔드와 백엔드 분리
    frontend_svc_list = [s for s in services if s in frontend_services]
    backend_svc_list = [s for s in services if s not in frontend_services]

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
    if frontend_svc_list:
        readme += """### 🖥️ 프론트엔드 (UI)

| 서비스 | Import 포트 | 접속 URL |
|--------|-------------|----------|
"""
        for service in frontend_svc_list:
            original_port = service_port_map.get(service, 0)
            mapped_port = original_port + port_offset
            size_info = ""
            if service in docker_images:
                size_info = f" ({docker_images[service].size_mb} MB)"
            readme += f"| {service}{size_info} | **{mapped_port}** | http://localhost:{mapped_port} |\n"

        readme += "\n"

    # 백엔드 섹션
    if backend_svc_list:
        readme += """### ⚙️ 백엔드 (API)

| 서비스 | 원본 포트 | Import 포트 | 컨테이너 이름 |
|--------|----------|-------------|--------------|
"""
        for service in backend_svc_list:
            original_port = service_port_map.get(service, 0)
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
