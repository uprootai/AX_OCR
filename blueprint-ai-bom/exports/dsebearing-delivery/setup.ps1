# ============================================================
# Blueprint AI BOM - DSE Bearing 납품 패키지 자동 설치
# 동서기연 터빈 베어링 프로젝트 (Windows PowerShell)
# ============================================================

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$BackendImage = "images\blueprint-ai-bom-backend.tar.gz"
$FrontendImage = "images\blueprint-ai-bom-frontend.tar.gz"
$ProjectJson = "data\project_dsebearing.json"
$BackendUrl = "http://localhost:5020"
$FrontendUrl = "http://localhost:3000"

function Write-Step($num, $msg) {
    Write-Host ""
    Write-Host "[$num/8] $msg" -ForegroundColor Cyan
    Write-Host "------------------------------------------------------------"
}

function Write-Ok($msg) {
    Write-Host "  OK " -ForegroundColor Green -NoNewline
    Write-Host $msg
}

function Write-Err($msg) {
    Write-Host "  ERROR " -ForegroundColor Red -NoNewline
    Write-Host $msg
}

Write-Host "============================================================"
Write-Host "  Blueprint AI BOM - DSE Bearing 설치"
Write-Host "  동서기연 터빈 베어링 프로젝트"
Write-Host "============================================================"

# ---- Step 1: Docker 이미지 로드 ----
Write-Step 1 "Docker 이미지 로드"

if (-not (Test-Path $BackendImage)) {
    Write-Err "$BackendImage 파일을 찾을 수 없습니다."
    exit 1
}
if (-not (Test-Path $FrontendImage)) {
    Write-Err "$FrontendImage 파일을 찾을 수 없습니다."
    exit 1
}

Write-Host "  Backend 이미지 로드 중... (약 2-3분 소요)"
docker load -i $BackendImage
Write-Ok "Backend 이미지 로드 완료"

Write-Host "  Frontend 이미지 로드 중..."
docker load -i $FrontendImage
Write-Ok "Frontend 이미지 로드 완료"

# ---- Step 2: 데이터 디렉토리 초기화 ----
Write-Step 2 "데이터 디렉토리 초기화"

New-Item -ItemType Directory -Path "data" -Force | Out-Null
Write-Ok "data\ 디렉토리 준비 완료"

# ---- Step 3: 서비스 시작 ----
Write-Step 3 "서비스 시작"

docker compose down 2>$null
docker compose up -d
Write-Ok "컨테이너 시작됨"

# ---- Step 4: 백엔드 헬스체크 대기 ----
Write-Step 4 "백엔드 헬스체크 대기 (최대 60초)"

$MaxWait = 60
$Elapsed = 0
$Healthy = $false

while ($Elapsed -lt $MaxWait) {
    try {
        $response = Invoke-WebRequest -Uri "$BackendUrl/health" -UseBasicParsing -TimeoutSec 3
        if ($response.StatusCode -eq 200) {
            Write-Ok "백엔드 정상 응답 (${Elapsed}초)"
            $Healthy = $true
            break
        }
    } catch {
        # 아직 준비 안됨
    }
    Start-Sleep -Seconds 2
    $Elapsed += 2
    Write-Host "`r  대기 중... ${Elapsed}초" -NoNewline
}

if (-not $Healthy) {
    Write-Err "백엔드가 ${MaxWait}초 내에 응답하지 않습니다."
    Write-Host "  docker logs blueprint-ai-bom-backend 명령으로 로그를 확인하세요."
    exit 1
}

# ---- Step 5: 프로젝트 Import ----
Write-Step 5 "프로젝트 데이터 Import"

if (-not (Test-Path $ProjectJson)) {
    Write-Err "$ProjectJson 파일을 찾을 수 없습니다."
    exit 1
}

$fileBytes = [System.IO.File]::ReadAllBytes((Resolve-Path $ProjectJson))
$fileName = [System.IO.Path]::GetFileName($ProjectJson)
$boundary = [System.Guid]::NewGuid().ToString()
$LF = "`r`n"
$bodyLines = (
    "--$boundary",
    "Content-Disposition: form-data; name=`"file`"; filename=`"$fileName`"",
    "Content-Type: application/json",
    "",
    [System.Text.Encoding]::UTF8.GetString($fileBytes),
    "--$boundary--"
) -join $LF
$ImportResult = Invoke-RestMethod -Uri "$BackendUrl/projects/import" `
    -Method Post `
    -ContentType "multipart/form-data; boundary=$boundary" `
    -Body $bodyLines

if ($ImportResult.project_id) {
    Write-Ok "프로젝트 Import 성공"
} else {
    Write-Host "  Import 결과를 확인하세요: $($ImportResult | ConvertTo-Json -Depth 3)" -ForegroundColor Yellow
}

# ---- Step 6: Import 결과 확인 ----
Write-Step 6 "Import 결과 확인"

$ProjectId = if ($ImportResult.project_id) { $ImportResult.project_id } else { "N/A" }
$SessionCount = if ($ImportResult.imported_sessions) { $ImportResult.imported_sessions } `
    elseif ($ImportResult.sessions_imported) { $ImportResult.sessions_imported } `
    elseif ($ImportResult.session_count) { $ImportResult.session_count } `
    else { "N/A" }

Write-Host "  Project ID: $ProjectId"
Write-Host "  Sessions:   $SessionCount"

# ---- Step 7: 접속 URL 출력 ----
Write-Step 7 "접속 정보"

Write-Host ""
Write-Host "  Frontend:  " -NoNewline; Write-Host $FrontendUrl -ForegroundColor Green
Write-Host "  Backend:   " -NoNewline; Write-Host $BackendUrl -ForegroundColor Green
Write-Host "  API Docs:  " -NoNewline; Write-Host "$BackendUrl/docs" -ForegroundColor Green
Write-Host ""

# ---- Step 8: 검증 가이드 ----
Write-Step 8 "검증 가이드"

Write-Host "  1. 브라우저에서 $FrontendUrl 접속"
Write-Host "  2. 프로젝트 목록에서 '동서기연 터빈 베어링' 선택"
Write-Host "  3. BOM 탭: 326개 아이템 확인"
Write-Host "  4. 견적 탭: 총 견적가 100,679,708 원 확인"
Write-Host "  5. 세션 탭: 53개 분석 세션 확인"
Write-Host ""

Write-Host "============================================================"
Write-Host "  설치 완료!" -ForegroundColor Green
Write-Host "  $FrontendUrl 에서 확인하세요."
Write-Host "============================================================"
