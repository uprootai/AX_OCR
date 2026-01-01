# DocTR API

2단계 파이프라인 OCR (Detection + Recognition) - Apache 2.0 라이선스

## Overview

- **Purpose**: 2단계 파이프라인 기반 문서 OCR
- **Port**: 5014
- **GPU**: Recommended (CPU fallback available)
- **License**: Apache 2.0

## Key Features

| Feature | Description |
|---------|-------------|
| **2-Stage Pipeline** | Detection → Recognition 분리 |
| **Multiple Models** | ResNet, MobileNet, LinkNet 지원 |
| **Page Straightening** | 기울어진 문서 자동 정렬 |
| **PDF Support** | PDF 파일 직접 처리 |

## Quick Start (Standalone)

### Prerequisites
- Docker & Docker Compose
- NVIDIA GPU + CUDA (optional)

### 1. Run the API

```bash
cd models/doctr-api
docker-compose -f docker-compose.single.yml up -d
docker logs doctr-api-standalone -f
```

### 2. Check Health

```bash
curl http://localhost:5014/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "doctr-api",
  "version": "1.0.0",
  "det_model": "db_resnet50",
  "reco_model": "crnn_vgg16_bn"
}
```

### 3. API Documentation

Open in browser: **http://localhost:5014/docs**

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
- file: image file (PNG, JPEG, PDF)
- det_arch: detection model (db_resnet50, db_mobilenet_v3_large, linknet_resnet18)
- reco_arch: recognition model (crnn_vgg16_bn, crnn_mobilenet_v3_small, master)
- straighten_pages: enable page alignment (default: false)
- export_as_xml: export as XML (default: false)
- visualize: generate overlay image (default: true)
```

## Testing

```bash
curl -X POST http://localhost:5014/api/v1/ocr \
  -F "file=@document.png" \
  -F "det_arch=db_resnet50" \
  -F "reco_arch=crnn_vgg16_bn" \
  -F "visualize=true"
```

## Response Example

```json
{
  "status": "success",
  "data": {
    "texts": [
      {
        "text": "SPECIFICATION",
        "confidence": 0.96,
        "bbox": [[50, 100], [200, 100], [200, 130], [50, 130]]
      }
    ],
    "full_text": "SPECIFICATION\nDRAWING NO: DWG-001\n...",
    "pages": [
      {
        "page_idx": 0,
        "dimensions": [1200, 800],
        "blocks": 15
      }
    ]
  },
  "processing_time": 1.85
}
```

## Model Options

### Detection Models

| Model | Speed | Accuracy | VRAM |
|-------|-------|----------|------|
| `db_resnet50` | Medium | High | ~2.5GB |
| `db_mobilenet_v3_large` | Fast | Medium | ~1.5GB |
| `linknet_resnet18` | Fast | Medium | ~1.5GB |

### Recognition Models

| Model | Speed | Accuracy | VRAM |
|-------|-------|----------|------|
| `crnn_vgg16_bn` | Medium | High | ~1GB |
| `crnn_mobilenet_v3_small` | Fast | Medium | ~0.5GB |
| `master` | Slow | Very High | ~2GB |

## Docker Image Distribution

### Build Image
```bash
docker build -t ax-doctr-api:latest .
```

### Run Standalone Container
```bash
docker run -d \
  --name doctr-api \
  -p 5014:5014 \
  --gpus all \
  ax-doctr-api:latest
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DOCTR_PORT` | 5014 | API server port |
| `DET_ARCH` | db_resnet50 | Detection model |
| `RECO_ARCH` | crnn_vgg16_bn | Recognition model |
| `USE_GPU` | true | Enable GPU |

## Performance

| Metric | GPU (RTX 3080) | CPU (8 cores) |
|--------|----------------|---------------|
| Single image | ~1.5s | ~6s |
| Memory (GPU) | ~2GB | N/A |
| Memory (CPU) | N/A | ~4GB |

## Project Structure

```
doctr-api/
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
- **Usage in Pipeline**: Document OCR with layout analysis
- **Gateway Integration**: Called via Gateway API

## License

Part of the AX Project (2025)

## Support

For issues or questions:
1. Check API documentation: http://localhost:5014/docs
2. Review logs: `docker logs doctr-api-standalone`
3. Contact: AX Project Team

---

**Version**: 1.0.0
**Last Updated**: 2025-12-31
**Maintained By**: AX Project Team
