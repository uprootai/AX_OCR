# Tesseract OCR API

Google Tesseract 기반 범용 OCR 엔진

## Overview

- **Purpose**: 범용 문서 OCR
- **Port**: 5008
- **GPU**: Not required (CPU only)
- **Engine**: Google Tesseract 5.x
- **License**: Apache 2.0

## Key Features

| Feature | Description |
|---------|-------------|
| **CPU Only** | GPU 불필요, 빠르고 가벼움 |
| **Multi-language** | 영어, 한국어, 일본어, 중국어 등 |
| **PSM Modes** | 다양한 페이지 분할 모드 |
| **Proven Engine** | 오랜 기간 검증된 OCR 엔진 |

## Page Segmentation Modes (PSM)

| Mode | Description |
|------|-------------|
| `0` | OSD (방향/스크립트 감지) |
| `1` | 자동 OSD 포함 |
| `3` | 자동 페이지 분할 (기본값) |
| `4` | 가변 크기 텍스트 단일 열 |
| `6` | 단일 균일 텍스트 블록 |
| `7` | 단일 텍스트 라인 |
| `11` | 희소 텍스트 |
| `12` | OSD 포함 희소 텍스트 |
| `13` | 원시 라인 |

## Quick Start (Standalone)

### Prerequisites
- Docker & Docker Compose

### 1. Run the API

```bash
cd models/tesseract-api
docker-compose -f docker-compose.single.yml up -d
docker logs tesseract-api-standalone -f
```

### 2. Check Health

```bash
curl http://localhost:5008/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "tesseract-api",
  "version": "1.0.0",
  "tesseract_version": "5.3.0"
}
```

### 3. API Documentation

Open in browser: **http://localhost:5008/docs**

## API Endpoints

### Health Check
```bash
GET /health
```

### OCR Processing
```bash
POST /api/v1/ocr
Content-Type: multipart/form-data

Parameters:
- file: image file (PNG, JPEG)
- lang: language code (eng, kor, jpn, chi_sim, eng+kor)
- psm: page segmentation mode (default: "3")
- output_type: output format (string, data, dict)
```

## Testing

```bash
curl -X POST http://localhost:5008/api/v1/ocr \
  -F "file=@document.png" \
  -F "lang=eng+kor" \
  -F "psm=6" \
  -F "output_type=data"
```

## Response Example

```json
{
  "status": "success",
  "data": {
    "texts": [
      {
        "text": "DRAWING TITLE",
        "confidence": 0.92,
        "bbox": [50, 100, 200, 130]
      },
      {
        "text": "REV. A",
        "confidence": 0.88,
        "bbox": [500, 100, 560, 130]
      }
    ],
    "full_text": "DRAWING TITLE\nREV. A\n..."
  },
  "processing_time": 0.45
}
```

## Supported Languages

| Code | Language |
|------|----------|
| `eng` | English |
| `kor` | Korean |
| `jpn` | Japanese |
| `chi_sim` | Chinese (Simplified) |
| `chi_tra` | Chinese (Traditional) |
| `eng+kor` | English + Korean |

## Docker Image Distribution

### Build Image
```bash
docker build -t ax-tesseract-api:latest .
```

### Run Standalone Container
```bash
docker run -d \
  --name tesseract-api \
  -p 5008:5008 \
  -e TESSERACT_LANG=eng \
  ax-tesseract-api:latest
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TESSERACT_PORT` | 5008 | API server port |
| `TESSERACT_LANG` | eng | Default language |
| `TESSERACT_PSM` | 3 | Default PSM mode |

## Performance

| Metric | Value |
|--------|-------|
| Single image | ~0.5s |
| Memory | ~1GB |
| CPU | 2 cores |

### Performance Tips

1. **Use PSM 6**: For single text blocks (faster)
2. **Language**: Use single language for speed
3. **Image Quality**: Higher resolution = better accuracy

## Project Structure

```
tesseract-api/
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
- **Usage in Pipeline**: Document OCR, fallback OCR
- **OCR Ensemble**: Integrated with 15% weight

### When to Use

| Scenario | Recommendation |
|----------|----------------|
| Engineering drawings | Use eDOCr2 instead |
| General documents | Good choice |
| Low resources | Good choice (CPU only) |
| OCR Ensemble | Use as part of ensemble |

## License

Part of the AX Project (2025)

## Support

For issues or questions:
1. Check API documentation: http://localhost:5008/docs
2. Review logs: `docker logs tesseract-api-standalone`
3. Contact: AX Project Team

---

**Version**: 1.0.0
**Last Updated**: 2025-12-31
**Maintained By**: AX Project Team
