# Blueprint AI BOM - Self-contained Import (Windows)
# Port Offset: +10000

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Blueprint AI BOM - Self-contained Import" -ForegroundColor Cyan
Write-Host "  (Port Offset: +10000)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location "$ScriptDir\.."

# [1/3] Docker 이미지 로드
Write-Host "[1/3] Loading Docker images..." -ForegroundColor Yellow

$gzFiles = Get-ChildItem -Path "docker\images\*.tar.gz" -ErrorAction SilentlyContinue
foreach ($file in $gzFiles) {
    Write-Host "  Loading: $($file.Name)"
    & gzip -d -c $file.FullName | docker load
}

$tarFiles = Get-ChildItem -Path "docker\images\*.tar" -ErrorAction SilentlyContinue
foreach ($file in $tarFiles) {
    Write-Host "  Loading: $($file.Name)"
    docker load -i $file.FullName
}

# [2/3] Docker 네트워크 생성
Write-Host ""
Write-Host "[2/3] Creating Docker network..." -ForegroundColor Yellow
docker network create panasia_network 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "  Network already exists" }

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
Write-Host "Container prefix: panasia-"
Write-Host "Port offset: +10000"
Write-Host ""
Write-Host "==========================================" -ForegroundColor Magenta
Write-Host "  UI Access URL:" -ForegroundColor Magenta
Write-Host "==========================================" -ForegroundColor Magenta
Write-Host "  * http://localhost:13000" -ForegroundColor Yellow
Write-Host ""
Write-Host "API endpoints:"
Write-Host "  - panasia-blueprint-ai-bom-backend: http://localhost:15020"
Write-Host "  - panasia-gateway-api: http://localhost:18000"
Write-Host "  - panasia-yolo-api: http://localhost:15005"

Write-Host ""
Write-Host "Check status: cd docker; docker-compose ps"
Write-Host "Stop services: cd docker; docker-compose down"
