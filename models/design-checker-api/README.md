# Design Checker API

P&ID 도면 설계 오류 검출 및 규정 검증 API

## Overview

- **Purpose**: P&ID 설계 규칙 검증 및 오류 검출
- **Port**: 5019
- **GPU**: Not required (CPU only)
- **Categories**: connectivity, symbol, labeling, specification, standard, safety, bwms

## Key Features

| Feature | Description |
|---------|-------------|
| **Connectivity** | 심볼 간 연결 무결성 검사 |
| **Symbol** | 심볼 규격 준수 검사 |
| **Labeling** | 태그/라벨 규칙 검사 |
| **BWMS** | TECHCROSS BWMS 전용 7개 규칙 |
| **Rule Management** | Excel 업로드, YAML 저장, 프로필 관리 |

## Quick Start (Standalone)

### Prerequisites
- Docker & Docker Compose
- No GPU required

### 1. Run the API

```bash
cd models/design-checker-api
docker-compose -f docker-compose.single.yml up -d
docker logs design-checker-api-standalone -f
```

### 2. Check Health

```bash
curl http://localhost:5019/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "design-checker-api",
  "version": "1.0.0",
  "rules_count": 27
}
```

### 3. API Documentation

Open in browser: **http://localhost:5019/docs**

## API Endpoints

### Health Check
```bash
GET /api/v1/health
```

### Design Check
```bash
POST /api/v1/check
Content-Type: application/json

Body:
{
  "symbols": [...],       # YOLO 검출 결과
  "connections": [...],   # PID Analyzer 연결 분석 결과
  "texts": [...],         # OCR 텍스트 결과
  "categories": "all",    # 검사 카테고리
  "severity_threshold": "warning",
  "include_bwms": true
}
```

### BWMS Check
```bash
POST /api/v1/check/bwms
```

### Rules Management
```bash
GET /api/v1/rules              # 규칙 목록
POST /api/v1/rules/enable      # 규칙 활성화
POST /api/v1/rules/disable     # 규칙 비활성화
```

### Checklist Management
```bash
POST /api/v1/checklist/upload  # Excel 업로드
GET /api/v1/checklist/template # 템플릿 다운로드
GET /api/v1/checklist/current  # 현재 체크리스트
```

## Testing

```bash
curl -X POST http://localhost:5019/api/v1/check \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": [
      {"class_name": "valve", "tag": "V-001", "bbox": {"x1": 100, "y1": 200, "x2": 150, "y2": 250}}
    ],
    "connections": [
      {"from": "V-001", "to": "P-001", "type": "process"}
    ],
    "categories": "all",
    "include_bwms": true
  }'
```

## Response Example

```json
{
  "status": "success",
  "data": {
    "violations": [
      {
        "rule_id": "CONN-001",
        "category": "connectivity",
        "severity": "error",
        "message": "밸브 V-003이 어떤 배관에도 연결되지 않음",
        "location": {"x": 500, "y": 300}
      }
    ],
    "summary": {
      "total_rules": 27,
      "checked": 27,
      "passed": 25,
      "failed": 2
    },
    "compliance_score": 92.6
  },
  "processing_time": 0.35
}
```

## Docker Image Distribution

### Build Image
```bash
docker build -t ax-design-checker-api:latest .
```

### Save Image for Distribution
```bash
docker save ax-design-checker-api:latest -o design-checker-api.tar
```

### Run Standalone Container
```bash
docker run -d \
  --name design-checker-api \
  -p 5019:5019 \
  ax-design-checker-api:latest
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DESIGN_CHECKER_PORT` | 5019 | API server port |
| `RULES_PATH` | /app/config | Rules configuration path |

## Performance

| Metric | Value |
|--------|-------|
| Single check | ~0.3s |
| Memory | ~1GB |
| CPU | 2 cores recommended |

## Project Structure

```
design-checker-api/
├── Dockerfile
├── README.md
├── api_server.py           # FastAPI application (167 lines)
├── schemas.py              # Pydantic models
├── constants.py            # Rule definitions
├── checker.py              # Validation logic
├── bwms_rules.py           # BWMS rules
├── rule_loader.py          # YAML-based rule management
├── excel_parser.py         # Excel checklist parser
├── routers/
│   ├── check_router.py     # /api/v1/check
│   ├── rules_router.py     # /api/v1/rules/*
│   └── checklist_router.py # /api/v1/checklist/*
├── config/                 # Rule configuration files
│   ├── common/
│   ├── ecs/
│   ├── hychlor/
│   └── custom/
└── requirements.txt
```

## Supported Standards

| Standard | Description |
|----------|-------------|
| **ISO 10628** | P&ID 표준 |
| **ISA 5.1** | 계기 심볼 표준 |
| **TECHCROSS BWMS** | 선박평형수처리시스템 규정 |

## Integration with AX PoC

This API is part of the **AX Drawing Analysis System**.

- **Main Project**: [ax-poc](https://github.com/your-org/ax-poc)
- **Usage in Pipeline**: Design validation stage
- **Inputs**: YOLO detections, PID Analyzer connections

## License

Part of the AX Project (2025)

## Support

For issues or questions:
1. Check API documentation: http://localhost:5019/docs
2. Review logs: `docker logs design-checker-api-standalone`
3. Contact: AX Project Team

---

**Version**: 1.0.0
**Last Updated**: 2025-12-31
**Maintained By**: AX Project Team
