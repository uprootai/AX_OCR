# PaddleOCR 3.0 API (PP-OCRv5)

Fast and accurate OCR service powered by PaddlePaddle's PP-OCRv5.

## Overview

- **Purpose**: General-purpose optical character recognition
- **Model**: PP-OCRv5 (13% accuracy improvement over v4)
- **Port**: 5006
- **GPU**: Recommended (CPU fallback available)
- **Languages**: 106 languages (English, Chinese, Korean, Japanese, Arabic, and more)

## What's New in 3.0.0

| Feature | PP-OCRv4 | PP-OCRv5 |
|---------|----------|----------|
| **Accuracy** | Baseline | +13% improvement |
| **Languages** | ~80 | 106 |
| **Vertical Text** | Limited | Excellent |
| **Handwriting** | Limited | Improved |
| **Model Size** | ~100MB | ~100MB |

## Quick Start (Standalone)

### Prerequisites
- Docker & Docker Compose
- NVIDIA GPU + CUDA (optional, for GPU acceleration)
- nvidia-docker2 (if using GPU)

### 1. Run the API

```bash
# With GPU
docker-compose -f docker-compose.single.yml up -d

# Without GPU (slower)
# Edit docker-compose.single.yml and comment out the 'deploy' section
docker-compose -f docker-compose.single.yml up -d
```

### 2. Check Health

```bash
curl http://localhost:5006/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "paddleocr-api",
  "version": "3.0.0",
  "ocr_version": "PP-OCRv5"
}
```

### 3. API Documentation

Open in browser: **http://localhost:5006/docs**

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
- file: image file (PNG, JPG, JPEG, TIFF, BMP)
- lang: language code (default: 'en')
- det_db_thresh: detection threshold (default: 0.3)
- det_db_box_thresh: box threshold (default: 0.6)
- use_textline_orientation: enable text line orientation (default: true)
- min_confidence: minimum confidence filter (default: 0.5)
- visualize: generate visualization image (default: false)
```

## Testing

```bash
# Test with a sample image
curl -X POST http://localhost:5006/api/v1/ocr \
  -F "file=@/path/to/image.jpg" \
  -F "lang=korean" \
  -F "min_confidence=0.5"
```

## Docker Image Distribution

### Build Image
```bash
docker build -t ax-paddleocr-api:3.0.0 .
```

### Save Image for Distribution
```bash
docker save ax-paddleocr-api:3.0.0 -o paddleocr-api.tar
```

### Load Image (on target machine)
```bash
docker load -i paddleocr-api.tar
```

### Run Standalone Container
```bash
docker run -d \
  --name paddleocr-api \
  -p 5006:5006 \
  --gpus all \
  -e USE_GPU=true \
  -e OCR_VERSION=PP-OCRv5 \
  -e OCR_LANG=en \
  ax-paddleocr-api:3.0.0
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PADDLEOCR_PORT` | 5006 | API server port |
| `USE_GPU` | false | Enable GPU acceleration |
| `OCR_VERSION` | PP-OCRv5 | OCR model version |
| `OCR_LANG` | en | OCR language |
| `DEVICE` | cpu | Inference device (cpu, gpu:0) |
| `USE_TEXTLINE_ORIENTATION` | true | Enable text line orientation |
| `USE_DOC_ORIENTATION` | false | Enable document orientation |
| `USE_DOC_UNWARPING` | false | Enable document unwarping |
| `TEXT_DET_THRESH` | 0.3 | Text detection threshold |
| `TEXT_DET_BOX_THRESH` | 0.6 | Box detection threshold |

### Supported Languages (106)

- `en` - English
- `ch` - Chinese (Simplified)
- `korean` - Korean
- `japan` - Japanese
- `fr` - French
- `de` - German
- `es` - Spanish
- `ru` - Russian
- `ar` - Arabic
- And 97 more...

Full list: https://paddlepaddle.github.io/PaddleOCR/v3.0.0/en/ppocr/blog/multi_languages.html

## Performance

| Metric | GPU (RTX 3080) | CPU (8 cores) |
|--------|----------------|---------------|
| Single image | ~0.5s | ~3-5s |
| Throughput | 120 img/min | 15 img/min |

## Integration with AX PoC

This API is part of the **AX Drawing Analysis System**.

- **Main Project**: [ax-poc](https://github.com/your-org/ax-poc)
- **Usage in Pipeline**: Multilingual OCR for engineering drawings
- **Gateway Integration**: Automatically called by Gateway API

## Project Structure

```
paddleocr-api/
├── Dockerfile                  # Docker build file
├── docker-compose.single.yml   # Standalone deployment
├── README.md                   # This file
├── api_server.py               # FastAPI application
├── models/
│   └── schemas.py              # Pydantic models
├── routers/
│   └── ocr_router.py           # OCR endpoints
├── services/
│   └── ocr.py                  # PaddleOCR 3.0 service
├── utils/
│   └── helpers.py              # Utility functions
├── requirements.txt            # Python dependencies
├── uploads/                    # Uploaded files (temporary)
└── results/                    # Processing results
```

## Troubleshooting

### GPU not detected
```bash
# Check NVIDIA driver
nvidia-smi

# Check Docker GPU access
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### Permission denied on uploads/
```bash
chmod 777 uploads/ results/
```

### Port 5006 already in use
```bash
# Change port in docker-compose.single.yml
ports:
  - "5007:5006"  # Host:Container
```

## License

Part of the AX Project (2025)

## Support

For issues or questions:
1. Check API documentation: http://localhost:5006/docs
2. Review logs: `docker logs paddleocr-api-standalone`
3. Contact: AX Project Team

---

**Version**: 3.0.0
**Last Updated**: 2025-12-31
**Maintained By**: AX Project Team
