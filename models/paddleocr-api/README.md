# 🔤 PaddleOCR API

Fast and accurate OCR service powered by PaddlePaddle's PaddleOCR.

## 📋 Overview

- **Purpose**: General-purpose optical character recognition
- **Model**: PaddleOCR (multi-language support)
- **Port**: 5006
- **GPU**: Recommended (CPU fallback available)
- **Languages**: English, Chinese, Korean, Japanese, and 80+ more

## 🚀 Quick Start (Standalone)

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
  "service": "PaddleOCR API",
  "version": "1.0.0"
}
```

### 3. API Documentation

Open in browser: **http://localhost:5006/docs**

## 📡 API Endpoints

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
- use_gpu: true/false (default: true)
- use_angle_cls: true/false (default: true)
- lang: language code (default: 'en')
```

## 🧪 Testing

```bash
# Test with a sample image
curl -X POST http://localhost:5006/api/v1/ocr \
  -F "file=@/path/to/image.jpg" \
  -F "use_gpu=true" \
  -F "lang=en"
```

## 🐳 Docker Image Distribution

### Build Image
```bash
docker build -t ax-paddleocr-api:latest .
```

### Save Image for Distribution
```bash
docker save ax-paddleocr-api:latest -o paddleocr-api.tar
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
  -e USE_ANGLE_CLS=true \
  -e OCR_LANG=en \
  ax-paddleocr-api:latest
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PADDLEOCR_PORT` | 5006 | API server port |
| `USE_GPU` | true | Enable GPU acceleration |
| `USE_ANGLE_CLS` | true | Enable text angle classification |
| `OCR_LANG` | en | OCR language (en, ch, korean, japan, etc.) |
| `PYTHONUNBUFFERED` | 1 | Python output buffering |

### Supported Languages

- `en` - English
- `ch` - Chinese (Simplified)
- `korean` - Korean
- `japan` - Japanese
- `french` - French
- `german` - German
- And 80+ more...

Full list: https://github.com/PaddlePaddle/PaddleOCR/blob/release/2.6/doc/doc_en/multi_languages_en.md

## 📊 Performance

| Metric | GPU (RTX 3080) | CPU (8 cores) |
|--------|----------------|---------------|
| Single image | ~0.5s | ~3-5s |
| Throughput | 120 img/min | 15 img/min |

## 🔗 Integration with AX PoC

This API is part of the **AX Drawing Analysis System**.

- **Main Project**: [ax-poc](https://github.com/your-org/ax-poc)
- **Usage in Pipeline**: Auxiliary OCR for YOLO crop regions
- **Gateway Integration**: Automatically called by Gateway API

## 📁 Project Structure

```
paddleocr-api/
├── Dockerfile                  # Docker build file
├── docker-compose.single.yml   # Standalone deployment
├── README.md                   # This file
├── api_server.py               # FastAPI application (203 lines)
├── models/
│   └── schemas.py              # Pydantic models
├── services/
│   └── ocr.py                  # PaddleOCR service wrapper
├── utils/
│   └── helpers.py              # Utility functions
├── requirements.txt            # Python dependencies
├── uploads/                    # Uploaded files (temporary)
└── results/                    # Processing results
```

## 🐛 Troubleshooting

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

## 📄 License

Part of the AX Project (2025)

## 👥 Support

For issues or questions:
1. Check API documentation: http://localhost:5006/docs
2. Review logs: `docker logs paddleocr-api-standalone`
3. Contact: AX Project Team

---

**Version**: 1.0.0
**Last Updated**: 2025-11-20
**Maintained By**: AX Project Team
