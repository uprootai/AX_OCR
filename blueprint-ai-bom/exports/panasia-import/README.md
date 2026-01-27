# Blueprint AI BOM - Self-contained Export Package

## 세션 정보
- **Session ID**: 341a95dd-467e-4e01-a763-00603e7f52bd
- **Export Date**: 2026-01-26 10:26:02
- **Export Type**: Self-contained (Docker 이미지 포함)
- **Port Offset**: +10000
- **Container Prefix**: panasia-

## 🚀 Quick Start

Import 후 브라우저에서 바로 사용 가능:

**UI 접속 URL**: **http://localhost:13000**

## 포함된 서비스

### 🖥️ 프론트엔드 (UI)

| 서비스 | Import 포트 | 접속 URL |
|--------|-------------|----------|
| blueprint-ai-bom-frontend (24.17 MB) | **13000** | http://localhost:13000 |

### ⚙️ 백엔드 (API)

| 서비스 | 원본 포트 | Import 포트 | 컨테이너 이름 |
|--------|----------|-------------|--------------|
| blueprint-ai-bom-backend | 5020 | **15020** | panasia-blueprint-ai-bom-backend (4426.74 MB) |
| gateway-api | 8000 | **18000** | panasia-gateway-api (332.36 MB) |
| yolo-api | 5005 | **15005** | panasia-yolo-api (4426.31 MB) |

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
.\scripts\import.ps1
```

## 서비스 확인

```bash
# 컨테이너 상태
docker ps --filter "name=panasia"

# 로그 확인
docker logs panasia-yolo-api

# API 테스트
curl http://localhost:15005/health
```

## 요구사항
- Docker 20.10+
- docker-compose 2.0+

## 서비스 중지
```bash
cd docker && docker-compose down
docker network rm panasia_network
```
