# TrOCR API

Microsoft TrOCR Transformer 기반 OCR - 손글씨/장면 텍스트 특화

## Overview

- **Purpose**: Transformer 기반 OCR (손글씨/장면 텍스트)
- **Port**: 5009
- **GPU**: Recommended
- **Model**: Microsoft TrOCR (Transformer)
- **License**: MIT

## Key Features

| Feature | Description |
|---------|-------------|
| **Transformer-based** | 최신 Transformer 아키텍처 |
| **Handwriting** | 손글씨 텍스트 인식 |
| **Scene Text** | 장면 텍스트 인식 |
| **Line-level** | 텍스트 라인 단위 처리 |

## Model Types

| Model | Use Case | VRAM |
|-------|----------|------|
| `printed` | 인쇄 텍스트 | ~3GB |
| `handwritten` | 손글씨 | ~3GB |
| `large-printed` | 고정밀 인쇄 | ~6GB |
| `large-handwritten` | 고정밀 손글씨 | ~6GB |

## Quick Start (Standalone)

### Prerequisites
- Docker & Docker Compose
- NVIDIA GPU + CUDA (recommended)

### 1. Run the API

```bash
cd models/trocr-api
docker-compose -f docker-compose.single.yml up -d
docker logs trocr-api-standalone -f
```

### 2. Check Health

```bash
curl http://localhost:5009/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "trocr-api",
  "version": "1.0.0",
  "model_type": "printed"
}
```

### 3. API Documentation

Open in browser: **http://localhost:5009/docs**

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
- file: image file (cropped text line recommended)
- model_type: model type (printed, handwritten, large-printed, large-handwritten)
- max_length: maximum output length (default: 64)
- num_beams: beam search beams (default: 4)
```

## Testing

```bash
# For printed text
curl -X POST http://localhost:5009/api/v1/ocr \
  -F "file=@text_line.png" \
  -F "model_type=printed" \
  -F "max_length=64"

# For handwritten text
curl -X POST http://localhost:5009/api/v1/ocr \
  -F "file=@handwritten.png" \
  -F "model_type=handwritten" \
  -F "max_length=128"
```

## Response Example

```json
{
  "status": "success",
  "data": {
    "texts": [
      {
        "text": "Tolerance ±0.05",
        "confidence": 0.94
      }
    ],
    "full_text": "Tolerance ±0.05"
  },
  "processing_time": 0.85
}
```

## Best Practices

### Input Image

| Aspect | Recommendation |
|--------|----------------|
| **Cropping** | Crop to single text line |
| **Resolution** | 32-64px height optimal |
| **Contrast** | High contrast preferred |
| **Background** | Clean background preferred |

### Pipeline Usage

TrOCR works best with pre-cropped text regions:

```python
# Detect text regions with YOLO
yolo_result = yolo_api.detect(image, model_type="engineering")

# Process each text region with TrOCR
for detection in yolo_result["detections"]:
    if detection["class_name"] == "text":
        cropped = crop_image(image, detection["bbox"])
        text = trocr_api.ocr(cropped, model_type="printed")
```

## Docker Image Distribution

### Build Image
```bash
docker build -t ax-trocr-api:latest .
```

### Run Standalone Container
```bash
docker run -d \
  --name trocr-api \
  -p 5009:5009 \
  --gpus all \
  -e MODEL_TYPE=printed \
  ax-trocr-api:latest
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TROCR_PORT` | 5009 | API server port |
| `MODEL_TYPE` | printed | Default model type |
| `MAX_LENGTH` | 64 | Maximum output length |
| `NUM_BEAMS` | 4 | Beam search beams |

## Performance

| Metric | GPU (RTX 3080) | CPU (8 cores) |
|--------|----------------|---------------|
| Single line | ~0.5s | ~5s |
| Memory (GPU) | ~3GB | N/A |
| Memory (CPU) | N/A | ~6GB |

### Performance Tips

1. **Batch Processing**: Process multiple lines together
2. **GPU Required**: CPU is 10x slower
3. **Model Size**: Use base models unless high accuracy needed

## Project Structure

```
trocr-api/
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
- **Usage in Pipeline**: Single-line text recognition
- **OCR Ensemble**: Integrated with 10% weight

### When to Use

| Scenario | Recommendation |
|----------|----------------|
| Full page OCR | Use eDOCr2 or PaddleOCR |
| Single text lines | Good choice |
| Handwritten notes | Best choice |
| OCR Ensemble | Use as part of ensemble |

## License

Part of the AX Project (2025)

## Support

For issues or questions:
1. Check API documentation: http://localhost:5009/docs
2. Review logs: `docker logs trocr-api-standalone`
3. Contact: AX Project Team

---

**Version**: 1.0.0
**Last Updated**: 2025-12-31
**Maintained By**: AX Project Team
