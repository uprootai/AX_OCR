# Line Detector API

P&ID 라인 검출, 스타일 분류, 영역 검출 API

## Overview

- **Purpose**: P&ID 도면의 라인 검출 및 스타일 분류
- **Port**: 5016
- **GPU**: Not required (CPU only, OpenCV based)
- **Version**: 1.1.0

## Key Features

| Feature | Description |
|---------|-------------|
| **Line Detection** | LSD/Hough 기반 라인 검출 |
| **Style Classification** | 실선/점선/점점선/이중선/물결선 분류 |
| **Color Classification** | 공정선/냉각선/증기선/신호선 색상 분류 |
| **Region Detection** | 점선 박스 영역 검출 (SIGNAL FOR BWMS 등) |
| **Intersection Detection** | 라인 교차점 검출 |

## Line Style Types

| Style | Korean | Signal Type |
|-------|--------|-------------|
| `solid` | 실선 | 주요 공정 배관 |
| `dashed` | 점선 | 계장 신호선 |
| `dotted` | 점점선 | 보조/옵션 라인 |
| `dash_dot` | 일점쇄선 | 경계선/중심선 |
| `double` | 이중선 | 주요 배관/케이싱 |
| `wavy` | 물결선 | 플렉시블 호스 |

## Quick Start (Standalone)

### Prerequisites
- Docker & Docker Compose

### 1. Run the API

```bash
cd models/line-detector-api
docker-compose -f docker-compose.single.yml up -d
docker logs line-detector-api-standalone -f
```

### 2. Check Health

```bash
curl http://localhost:5016/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "line-detector-api",
  "version": "1.1.0"
}
```

### 3. API Documentation

Open in browser: **http://localhost:5016/docs**

## API Endpoints

### Health Check
```bash
GET /api/v1/health
```

### Line Detection
```bash
POST /api/v1/process
Content-Type: multipart/form-data

Parameters:
- file: image file (PNG, JPEG)
- method: detection method (lsd, hough, combined)
- merge_lines: merge collinear lines (default: true)
- classify_types: classify line types (default: true)
- classify_colors: classify by color (default: true)
- classify_styles: classify line styles (default: true)
- find_intersections: detect intersections (default: true)
- detect_regions: detect dashed box regions (default: false)
- min_length: minimum line length in pixels (default: 0)
- max_lines: maximum lines to return (default: 0 = unlimited)
- visualize: generate visualization (default: true)
```

## Testing

```bash
curl -X POST http://localhost:5016/api/v1/process \
  -F "file=@pid_drawing.png" \
  -F "method=lsd" \
  -F "classify_styles=true" \
  -F "classify_colors=true" \
  -F "detect_regions=true" \
  -F "visualize=true"
```

## Response Example

```json
{
  "status": "success",
  "data": {
    "lines": [
      {
        "id": 1,
        "start": [100, 200],
        "end": [400, 200],
        "style": "solid",
        "color": "black",
        "usage": "process"
      },
      {
        "id": 2,
        "start": [200, 100],
        "end": [200, 300],
        "style": "dashed",
        "color": "blue",
        "usage": "instrument"
      }
    ],
    "intersections": [
      {
        "point": [200, 200],
        "lines": [1, 2]
      }
    ],
    "regions": [
      {
        "id": 1,
        "type": "signal_group",
        "label": "SIGNAL FOR BWMS",
        "bbox": [500, 100, 800, 400],
        "lines_count": 12
      }
    ],
    "statistics": {
      "total_lines": 156,
      "by_style": {"solid": 120, "dashed": 28, "dash_dot": 8},
      "by_color": {"black": 140, "blue": 12, "red": 4},
      "regions_found": 3
    },
    "visualization": "data:image/png;base64,..."
  },
  "processing_time": 1.85
}
```

## Region Types

| Type | Korean | Description |
|------|--------|-------------|
| `signal_group` | 신호 그룹 | SIGNAL FOR BWMS 등 |
| `equipment_boundary` | 장비 경계 | 패키지/스키드 경계 |
| `note_box` | 노트 박스 | 주석/설명 영역 |
| `hazardous_area` | 위험 구역 | 위험 구역 표시 |
| `scope_boundary` | 공급 범위 | 공급자/구매자 범위 |
| `detail_area` | 상세도 영역 | 상세도 참조 영역 |

## Docker Image Distribution

### Build Image
```bash
docker build -t ax-line-detector-api:latest .
```

### Run Standalone Container
```bash
docker run -d \
  --name line-detector-api \
  -p 5016:5016 \
  ax-line-detector-api:latest
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LINE_DETECTOR_PORT` | 5016 | API server port |
| `DEFAULT_METHOD` | lsd | Default detection method |

## Performance

| Metric | Value |
|--------|-------|
| Single image (1080p) | ~1-2s |
| Memory | ~2GB |
| CPU | 2 cores recommended |

### Performance Tips

1. **Use min_length**: Filter short lines for faster processing
2. **Use max_lines**: Limit output for large images
3. **Disable unused features**: Turn off classify_colors if not needed

## Project Structure

```
line-detector-api/
├── Dockerfile
├── README.md
├── api_server.py
├── services/
│   ├── line_detector.py
│   ├── style_classifier.py
│   └── region_detector.py
├── models/
│   └── schemas.py
├── requirements.txt
└── results/
```

## Integration with AX PoC

This API is part of the **AX Drawing Analysis System**.

- **Main Project**: [ax-poc](https://github.com/your-org/ax-poc)
- **Usage in Pipeline**: Line detection for P&ID analysis
- **Outputs to**: PID Analyzer, Design Checker

### Pipeline Integration

```python
# Detect lines and regions
line_result = line_detector_api.process(
    image=pid_image,
    method="lsd",
    classify_styles=True,
    detect_regions=True
)

# Pass to PID Analyzer
pid_result = pid_analyzer_api.analyze(
    symbols=yolo_detections,
    lines=line_result["lines"],
    intersections=line_result["intersections"]
)
```

## License

Part of the AX Project (2025)

## Support

For issues or questions:
1. Check API documentation: http://localhost:5016/docs
2. Review logs: `docker logs line-detector-api-standalone`
3. Contact: AX Project Team

---

**Version**: 1.1.0
**Last Updated**: 2025-12-31
**Maintained By**: AX Project Team
