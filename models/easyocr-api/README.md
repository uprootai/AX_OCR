# EasyOCR API

80+ 언어 지원, CPU 친화적, 한국어 지원 OCR - Apache 2.0 라이선스

## Overview

- **Purpose**: 다국어 OCR (80+ 언어)
- **Port**: 5015
- **GPU**: Optional (CPU-friendly)
- **Languages**: 80+ languages including Korean, Japanese, Chinese
- **License**: Apache 2.0

## Key Features

| Feature | Description |
|---------|-------------|
| **80+ Languages** | 한국어, 일본어, 중국어 등 80개 이상 언어 지원 |
| **CPU-Friendly** | GPU 없이도 합리적인 속도 |
| **Korean Support** | 한국어 OCR 우수 성능 |
| **Paragraph Mode** | 문단 단위 텍스트 결합 |

## Quick Start (Standalone)

### Prerequisites
- Docker & Docker Compose
- NVIDIA GPU + CUDA (optional)

### 1. Run the API

```bash
cd models/easyocr-api
docker-compose -f docker-compose.single.yml up -d
docker logs easyocr-api-standalone -f
```

### 2. Check Health

```bash
curl http://localhost:5015/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "easyocr-api",
  "version": "1.0.0",
  "languages": ["ko", "en"]
}
```

### 3. API Documentation

Open in browser: **http://localhost:5015/docs**

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
- detail: include bbox details (default: true)
- paragraph: merge into paragraphs (default: false)
- batch_size: batch size (default: 1, max: 32)
- visualize: generate overlay image (default: true)
```

## Testing

```bash
curl -X POST http://localhost:5015/api/v1/ocr \
  -F "file=@korean_document.png" \
  -F "languages=ko,en" \
  -F "detail=true" \
  -F "visualize=true"
```

## Response Example

```json
{
  "status": "success",
  "data": {
    "texts": [
      {
        "text": "부품명",
        "confidence": 0.94,
        "bbox": [[100, 50], [180, 50], [180, 80], [100, 80]]
      },
      {
        "text": "Part Name",
        "confidence": 0.97,
        "bbox": [[200, 50], [320, 50], [320, 80], [200, 80]]
      }
    ],
    "full_text": "부품명 Part Name\n..."
  },
  "processing_time": 2.15
}
```

## Supported Languages

| Code | Language | Code | Language |
|------|----------|------|----------|
| `ko` | Korean | `en` | English |
| `ja` | Japanese | `zh` | Chinese (Simplified) |
| `de` | German | `fr` | French |
| `es` | Spanish | `ru` | Russian |

Full list: 80+ languages supported

## Docker Image Distribution

### Build Image
```bash
docker build -t ax-easyocr-api:latest .
```

### Run Standalone Container
```bash
docker run -d \
  --name easyocr-api \
  -p 5015:5015 \
  --gpus all \
  -e LANGUAGES="ko,en" \
  ax-easyocr-api:latest
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `EASYOCR_PORT` | 5015 | API server port |
| `LANGUAGES` | ko,en | Default languages |
| `USE_GPU` | false | Enable GPU |

## Performance

| Metric | GPU (RTX 3080) | CPU (8 cores) |
|--------|----------------|---------------|
| Single image | ~1s | ~3-5s |
| Memory (GPU) | ~2GB | N/A |
| Memory (CPU) | N/A | ~3GB |

## Project Structure

```
easyocr-api/
├── Dockerfile
├── README.md
├── api_server.py
├── services/
│   └── ocr_service.py
├── models/
│   └── schemas.py
├── requirements.txt
└── results/
```

## Integration with AX PoC

This API is part of the **AX Drawing Analysis System**.

- **Main Project**: [ax-poc](https://github.com/your-org/ax-poc)
- **Usage in Pipeline**: Multilingual OCR
- **OCR Ensemble**: Integrated with 10% weight

## License

Part of the AX Project (2025)

## Support

For issues or questions:
1. Check API documentation: http://localhost:5015/docs
2. Review logs: `docker logs easyocr-api-standalone`
3. Contact: AX Project Team

---

**Version**: 1.0.0
**Last Updated**: 2025-12-31
**Maintained By**: AX Project Team
