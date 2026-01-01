# P&ID Analyzer API

P&ID 연결성 분석 및 BOM 추출 API

## Overview

- **Purpose**: P&ID 심볼 연결 분석, BOM/Valve List/Equipment List 생성
- **Port**: 5018
- **GPU**: Not required (CPU only)
- **Outputs**: Connections, BOM, Valve Signal List, Equipment List

## Key Features

| Feature | Description |
|---------|-------------|
| **Connectivity Analysis** | 심볼 간 연결 관계 분석 |
| **BOM Generation** | 부품 리스트 자동 생성 |
| **Valve Signal List** | BWMS 밸브 시그널 리스트 추출 |
| **Equipment List** | 장비 리스트 추출 |
| **OCR Integration** | EasyOCR 기반 계기 태그 검출 |
| **Region-based Extraction** | 점선 박스 영역 텍스트 추출 |

## Quick Start (Standalone)

### Prerequisites
- Docker & Docker Compose

### 1. Run the API

```bash
cd models/pid-analyzer-api
docker-compose -f docker-compose.single.yml up -d
docker logs pid-analyzer-api-standalone -f
```

### 2. Check Health

```bash
curl http://localhost:5018/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "pid-analyzer-api",
  "version": "1.0.0"
}
```

### 3. API Documentation

Open in browser: **http://localhost:5018/docs**

## API Endpoints

### Health Check
```bash
GET /api/v1/health
```

### P&ID Analysis
```bash
POST /api/v1/analyze
Content-Type: application/json

Body:
{
  "symbols": [...],           # YOLO 검출 결과
  "lines": [...],             # Line Detector 결과
  "intersections": [...],     # 교차점 정보
  "generate_bom": true,
  "generate_valve_list": true,
  "generate_equipment_list": true,
  "enable_ocr": true,
  "visualize": true
}
```

### Valve Signal List Extraction (Image)
```bash
POST /api/v1/valve-signal/extract
Content-Type: multipart/form-data

Parameters:
- file: P&ID image file
- rule_id: extraction rule (default: valve_signal_bwms)
- language: OCR language (default: en)
```

### Valve Signal List Excel Export
```bash
POST /api/v1/valve-signal/export-excel
Content-Type: multipart/form-data

Parameters:
- file: P&ID image file
- rule_id: extraction rule
- project_name: project name for Excel
- drawing_no: drawing number
```

### Region Rules Management
```bash
GET /api/v1/region-rules              # List all rules
GET /api/v1/region-rules/{rule_id}    # Get specific rule
POST /api/v1/region-rules             # Create new rule
PUT /api/v1/region-rules/{rule_id}    # Update rule
DELETE /api/v1/region-rules/{rule_id} # Delete rule
```

### Region Text Extraction
```bash
POST /api/v1/region-text/extract
Content-Type: application/json

Body:
{
  "regions": [...],    # Line Detector regions
  "texts": [...],      # OCR texts
  "rule_ids": [...],   # Rules to apply
  "text_margin": 30
}
```

## Testing

### Basic Analysis
```bash
curl -X POST http://localhost:5018/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": [
      {"id": "valve-1", "class_name": "gate_valve", "bbox": [100, 200, 150, 250]}
    ],
    "lines": [
      {"id": "line-1", "points": [[150, 225], [300, 225]], "color_type": "process"}
    ],
    "generate_bom": true
  }'
```

### Valve Signal List Extraction
```bash
curl -X POST http://localhost:5018/api/v1/valve-signal/extract \
  -F "file=@pid_bwms.png" \
  -F "rule_id=valve_signal_bwms" \
  -F "language=en"
```

## Response Example

### Analysis Response
```json
{
  "status": "success",
  "data": {
    "connections": [
      {
        "source_id": "valve-1",
        "target_id": "pump-1",
        "line_id": "line-1",
        "color_type": "process",
        "pipe_type": "main"
      }
    ],
    "graph": {
      "nodes": ["valve-1", "pump-1"],
      "edges": [{"source": "valve-1", "target": "pump-1"}]
    },
    "bom": [
      {"tag": "V-001", "type": "Gate Valve", "size": "DN50", "material": "SUS304"}
    ],
    "valve_list": [
      {"tag": "BWV-101", "type": "Ball Valve", "position": "NO", "signal": "XS-101"}
    ],
    "statistics": {
      "total_symbols": 2,
      "total_connections": 1,
      "connections_by_color_type": {"process": 1}
    }
  },
  "processing_time": 3.21
}
```

## Docker Image Distribution

### Build Image
```bash
docker build -t ax-pid-analyzer-api:latest .
```

### Run Standalone Container
```bash
docker run -d \
  --name pid-analyzer-api \
  -p 5018:5018 \
  ax-pid-analyzer-api:latest
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PID_ANALYZER_PORT` | 5018 | API server port |
| `RULES_PATH` | /app/config/rules | Rules configuration path |
| `EASYOCR_LANG` | en | OCR language |

## Performance

| Metric | Value |
|--------|-------|
| Analysis (100 symbols) | ~3s |
| Valve List extraction | ~5s |
| Memory | ~2GB |

## Project Structure

```
pid-analyzer-api/
├── Dockerfile
├── README.md
├── api_server.py
├── services/
│   ├── analyzer_service.py
│   ├── bom_generator.py
│   ├── valve_list_extractor.py
│   └── region_extractor.py
├── models/
│   └── schemas.py
├── routers/
│   ├── analyze_router.py
│   ├── valve_signal_router.py
│   └── region_rules_router.py
├── config/
│   └── rules/
│       └── valve_signal_bwms.yaml
├── requirements.txt
└── results/
```

## Region Rule Schema

```yaml
id: valve_signal_bwms
name: Valve Signal List (BWMS)
description: BWMS valve signal extraction
enabled: true
category: bwms
region_criteria:
  line_styles: [dashed, dash_dot]
  min_area: 1000
region_text_patterns:
  - pattern: "SIGNAL FOR BWMS"
    case_insensitive: true
extraction_patterns:
  - type: valve_tag
    regex: "BWV-\\d+"
```

## Integration with AX PoC

This API is part of the **AX Drawing Analysis System**.

- **Main Project**: [ax-poc](https://github.com/your-org/ax-poc)
- **Inputs**: YOLO detections, Line Detector results
- **Outputs to**: Design Checker, Excel Export

### Pipeline Integration

```python
# Full P&ID analysis pipeline
yolo_result = yolo_api.detect(image, model_type="pid_class_aware")
line_result = line_detector_api.process(image)

analysis = pid_analyzer_api.analyze(
    symbols=yolo_result["detections"],
    lines=line_result["lines"],
    intersections=line_result["intersections"]
)

# Validate design
validation = design_checker_api.check(
    symbols=yolo_result["detections"],
    connections=analysis["connections"]
)
```

## License

Part of the AX Project (2025)

## Support

For issues or questions:
1. Check API documentation: http://localhost:5018/docs
2. Review logs: `docker logs pid-analyzer-api-standalone`
3. Contact: AX Project Team

---

**Version**: 1.0.0
**Last Updated**: 2025-12-31
**Maintained By**: AX Project Team
