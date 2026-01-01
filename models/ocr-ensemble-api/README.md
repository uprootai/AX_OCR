# OCR Ensemble API

4개 OCR 엔진 가중 투표 앙상블 시스템

## Overview

- **Purpose**: 다중 OCR 엔진 앙상블로 정확도 향상
- **Port**: 5011
- **GPU**: Recommended (4 engines run in parallel)
- **Engines**: eDOCr2 + PaddleOCR + Tesseract + TrOCR

## Key Features

| Feature | Description |
|---------|-------------|
| **4-Engine Ensemble** | 4개 OCR 엔진 병렬 실행 |
| **Weighted Voting** | 가중치 기반 투표 시스템 |
| **Confidence Boost** | 여러 엔진 동의 시 신뢰도 상승 |
| **Fallback** | 일부 엔진 실패 시에도 동작 |

## Engine Weights (Default)

| Engine | Weight | Specialty |
|--------|--------|-----------|
| **eDOCr2** | 40% | 기계 도면 치수 |
| **PaddleOCR** | 35% | 다국어 일반 텍스트 |
| **Tesseract** | 15% | 문서 텍스트 |
| **TrOCR** | 10% | 손글씨/장면 텍스트 |

## Quick Start (Standalone)

### Prerequisites
- Docker & Docker Compose
- NVIDIA GPU + CUDA 11.8+ (권장)
- 6GB+ GPU VRAM

### 1. Run the API

```bash
cd models/ocr-ensemble-api
docker-compose -f docker-compose.single.yml up -d
docker logs ocr-ensemble-api-standalone -f
```

### 2. Check Health

```bash
curl http://localhost:5011/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "ocr-ensemble-api",
  "version": "1.0.0",
  "engines": {
    "edocr2": "ready",
    "paddleocr": "ready",
    "tesseract": "ready",
    "trocr": "ready"
  }
}
```

### 3. API Documentation

Open in browser: **http://localhost:5011/docs**

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
- edocr2_weight: eDOCr2 weight (default: 0.40)
- paddleocr_weight: PaddleOCR weight (default: 0.35)
- tesseract_weight: Tesseract weight (default: 0.15)
- trocr_weight: TrOCR weight (default: 0.10)
- similarity_threshold: text similarity threshold (default: 0.7)
```

## Testing

```bash
curl -X POST http://localhost:5011/api/v1/ocr \
  -F "file=@engineering_drawing.png" \
  -F "edocr2_weight=0.40" \
  -F "paddleocr_weight=0.35" \
  -F "tesseract_weight=0.15" \
  -F "trocr_weight=0.10"
```

## Response Example

```json
{
  "status": "success",
  "data": {
    "results": [
      {
        "text": "Ø25 H7",
        "confidence": 0.96,
        "votes": 4,
        "bbox": [100, 150, 180, 175]
      },
      {
        "text": "MATERIAL: SUS304",
        "confidence": 0.92,
        "votes": 3,
        "bbox": [50, 400, 250, 425]
      }
    ],
    "full_text": "Ø25 H7\nMATERIAL: SUS304\n...",
    "engine_status": {
      "edocr2": "success",
      "paddleocr": "success",
      "tesseract": "success",
      "trocr": "success"
    }
  },
  "processing_time": 5.45
}
```

## Weight Presets

| Preset | Use Case | Weights |
|--------|----------|---------|
| **Mechanical** | 기계 도면 | eDOCr2:0.50, Paddle:0.30, Tess:0.10, TrOCR:0.10 |
| **Document** | 문서/계약서 | eDOCr2:0.20, Paddle:0.40, Tess:0.30, TrOCR:0.10 |
| **Multilingual** | 다국어 문서 | eDOCr2:0.25, Paddle:0.50, Tess:0.15, TrOCR:0.10 |
| **Handwritten** | 손글씨 포함 | eDOCr2:0.20, Paddle:0.30, Tess:0.10, TrOCR:0.40 |

## Docker Image Distribution

### Build Image
```bash
docker build -t ax-ocr-ensemble-api:latest .
```

### Run Standalone Container
```bash
docker run -d \
  --name ocr-ensemble-api \
  -p 5011:5011 \
  --gpus all \
  ax-ocr-ensemble-api:latest
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OCR_ENSEMBLE_PORT` | 5011 | API server port |
| `EDOCR2_URL` | http://edocr2-api:5002 | eDOCr2 API URL |
| `PADDLEOCR_URL` | http://paddleocr-api:5006 | PaddleOCR API URL |
| `TESSERACT_URL` | http://tesseract-api:5008 | Tesseract API URL |
| `TROCR_URL` | http://trocr-api:5009 | TrOCR API URL |

## Performance

| Metric | GPU (RTX 3080) | CPU (8 cores) |
|--------|----------------|---------------|
| Single image | ~5s | ~20s |
| Memory (GPU) | ~6GB | N/A |
| Memory (CPU) | N/A | ~12GB |

### Performance Notes

- All 4 engines run in parallel
- GPU strongly recommended
- CPU mode is very slow (not recommended)

## Project Structure

```
ocr-ensemble-api/
├── Dockerfile
├── README.md
├── api_server.py
├── services/
│   ├── ensemble_service.py
│   ├── voting.py
│   └── text_similarity.py
├── models/
│   └── schemas.py
├── requirements.txt
└── results/
```

## Integration with AX PoC

This API is part of the **AX Drawing Analysis System**.

- **Main Project**: [ax-poc](https://github.com/your-org/ax-poc)
- **Usage in Pipeline**: High-accuracy OCR for critical text
- **When to Use**: Complex drawings with mixed text types

### When to Use Ensemble

| Scenario | Recommendation |
|----------|----------------|
| Fast processing needed | Use single engine (eDOCr2) |
| Maximum accuracy needed | Use Ensemble |
| Mixed text types | Use Ensemble |
| Simple document | Use PaddleOCR alone |

## License

Part of the AX Project (2025)

## Support

For issues or questions:
1. Check API documentation: http://localhost:5011/docs
2. Review logs: `docker logs ocr-ensemble-api-standalone`
3. Contact: AX Project Team

---

**Version**: 1.0.0
**Last Updated**: 2025-12-31
**Maintained By**: AX Project Team
