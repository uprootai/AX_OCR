# Surya OCR API

90+ 언어 지원, 레이아웃 분석 OCR - GPL-3.0 라이선스

## Overview

- **Purpose**: 다국어 OCR (90+ 언어) + 레이아웃 분석
- **Port**: 5013
- **GPU**: Recommended
- **Languages**: 90+ languages
- **License**: GPL-3.0

## Key Features

| Feature | Description |
|---------|-------------|
| **90+ Languages** | 90개 이상 언어 지원 |
| **Layout Analysis** | 문서 레이아웃 분석 |
| **Text Regions** | 텍스트 영역 감지 |
| **Figure Detection** | 그림/도표 영역 감지 |

## Quick Start (Standalone)

### Prerequisites
- Docker & Docker Compose
- NVIDIA GPU + CUDA (recommended)

### 1. Run the API

```bash
cd models/surya-ocr-api
docker-compose -f docker-compose.single.yml up -d
docker logs surya-ocr-api-standalone -f
```

### 2. Check Health

```bash
curl http://localhost:5013/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "surya-ocr-api",
  "version": "1.0.0",
  "languages": 90
}
```

### 3. API Documentation

Open in browser: **http://localhost:5013/docs**

## API Endpoints

### Health Check
```bash
GET /api/v1/health
```

### OCR Processing
```bash
POST /api/v1/ocr
Content-Type: multipart/form-data

Parameters:
- file: image file (PNG, JPEG)
- languages: comma-separated language codes (default: "ko,en")
- detect_layout: enable layout analysis (default: false)
- visualize: generate overlay image (default: true)
```

## Testing

```bash
curl -X POST http://localhost:5013/api/v1/ocr \
  -F "file=@document.png" \
  -F "languages=ko,en" \
  -F "detect_layout=true" \
  -F "visualize=true"
```

## Response Example

```json
{
  "status": "success",
  "data": {
    "texts": [
      {
        "text": "Technical Drawing",
        "confidence": 0.95,
        "bbox": [50, 30, 250, 60]
      }
    ],
    "full_text": "Technical Drawing\nScale: 1:10\n...",
    "layout": {
      "text_regions": 12,
      "figure_regions": 3,
      "table_regions": 1
    }
  },
  "processing_time": 2.45
}
```

## Layout Analysis Output

When `detect_layout=true`:

| Region Type | Description |
|-------------|-------------|
| `text_regions` | 텍스트 영역 |
| `figure_regions` | 그림/도표 영역 |
| `table_regions` | 테이블 영역 |

## Docker Image Distribution

### Build Image
```bash
docker build -t ax-surya-ocr-api:latest .
```

### Run Standalone Container
```bash
docker run -d \
  --name surya-ocr-api \
  -p 5013:5013 \
  --gpus all \
  -e LANGUAGES="ko,en" \
  ax-surya-ocr-api:latest
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SURYA_PORT` | 5013 | API server port |
| `LANGUAGES` | ko,en | Default languages |
| `DETECT_LAYOUT` | false | Enable layout by default |

## Performance

| Metric | GPU (RTX 3080) | CPU (8 cores) |
|--------|----------------|---------------|
| OCR only | ~2s | ~10s |
| With layout | ~4s | ~20s |
| Memory (GPU) | ~3GB | N/A |
| Memory (CPU) | N/A | ~6GB |

## Project Structure

```
surya-ocr-api/
├── Dockerfile
├── README.md
├── api_server.py
├── services/
│   ├── ocr_service.py
│   └── layout_service.py
├── models/
│   └── schemas.py
├── requirements.txt
└── results/
```

## License Note

Surya OCR is licensed under **GPL-3.0**.
Commercial use may require separate licensing arrangements.

## Integration with AX PoC

This API is part of the **AX Drawing Analysis System**.

- **Main Project**: [ax-poc](https://github.com/your-org/ax-poc)
- **Usage in Pipeline**: Multilingual OCR with layout analysis
- **When to Use**: Complex documents with mixed layouts

## Support

For issues or questions:
1. Check API documentation: http://localhost:5013/docs
2. Review logs: `docker logs surya-ocr-api-standalone`
3. Contact: AX Project Team

---

**Version**: 1.0.0
**Last Updated**: 2025-12-31
**Maintained By**: AX Project Team
