# ESRGAN Upscaler API

Real-ESRGAN 기반 이미지 업스케일링 API

## Overview

- **Purpose**: 저해상도 이미지 4x 업스케일링
- **Port**: 5010
- **GPU**: Required for reasonable performance
- **Scale**: 2x or 4x upscaling

## Key Features

| Feature | Description |
|---------|-------------|
| **4x Upscaling** | 저해상도 이미지를 4배 확대 |
| **Noise Reduction** | 스캔 노이즈 제거 |
| **OCR Enhancement** | 업스케일링 후 OCR 정확도 향상 |
| **Quality Preservation** | 텍스트/라인 선명도 유지 |

## Quick Start (Standalone)

### Prerequisites
- Docker & Docker Compose
- NVIDIA GPU + CUDA 11.8+
- nvidia-docker2

### 1. Run the API

```bash
cd models/esrgan-api
docker-compose -f docker-compose.single.yml up -d
docker logs esrgan-api-standalone -f
```

### 2. Check Health

```bash
curl http://localhost:5010/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "esrgan-api",
  "version": "1.0.0",
  "model": "RealESRGAN_x4plus"
}
```

### 3. API Documentation

Open in browser: **http://localhost:5010/docs**

## API Endpoints

### Health Check
```bash
GET /health
```

### Upscale Image
```bash
POST /api/v1/upscale
Content-Type: multipart/form-data

Parameters:
- file: image file (PNG, JPG, JPEG)
- scale: upscale factor ("2" or "4", default: "4")
- denoise_strength: noise reduction (0-1, default: 0.5)
```

## Testing

```bash
curl -X POST http://localhost:5010/api/v1/upscale \
  -F "file=@low_res_drawing.png" \
  -F "scale=4" \
  -F "denoise_strength=0.5"
```

## Response Example

```json
{
  "status": "success",
  "data": {
    "image": "data:image/png;base64,...",
    "original_size": [640, 480],
    "upscaled_size": [2560, 1920],
    "scale_factor": 4
  },
  "processing_time": 3.25
}
```

## Use Cases

| Use Case | Description |
|----------|-------------|
| **Pre-OCR** | 저해상도 스캔 도면 개선 |
| **Detail Enhancement** | 작은 텍스트/치수 가독성 향상 |
| **Archive Recovery** | 오래된 스캔 도면 복원 |

## Docker Image Distribution

### Build Image
```bash
docker build -t ax-esrgan-api:latest .
```

### Save Image for Distribution
```bash
docker save ax-esrgan-api:latest -o esrgan-api.tar
```

### Run Standalone Container
```bash
docker run -d \
  --name esrgan-api \
  -p 5010:5010 \
  --gpus all \
  ax-esrgan-api:latest
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ESRGAN_PORT` | 5010 | API server port |
| `MODEL_NAME` | RealESRGAN_x4plus | Model to use |
| `DENOISE_STRENGTH` | 0.5 | Default noise reduction |

## Performance

| Metric | GPU (RTX 3080) | CPU (8 cores) |
|--------|----------------|---------------|
| 4x upscale (1080p) | ~3s | ~60s |
| Memory (GPU) | ~4GB | N/A |
| Memory (CPU) | N/A | ~8GB |

### Performance Tips

1. **Use GPU**: CPU is 20x slower - not recommended
2. **Start with 2x**: Use 2x first, then 4x if needed
3. **Denoise**: Increase for scanned images, decrease for digital

## Project Structure

```
esrgan-api/
├── Dockerfile
├── README.md
├── api_server.py
├── services/
│   └── upscale_service.py
├── models/
│   └── RealESRGAN_x4plus.pth
├── requirements.txt
└── results/
```

## Integration with AX PoC

This API is part of the **AX Drawing Analysis System**.

- **Main Project**: [ax-poc](https://github.com/your-org/ax-poc)
- **Usage in Pipeline**: Preprocessing before OCR
- **When to Use**: Low-resolution scanned drawings

### Pipeline Integration

```python
# Use ESRGAN before OCR for low-res images
if image_resolution < 1000:
    upscaled = esrgan_api.upscale(image, scale=4)
    ocr_result = edocr2_api.ocr(upscaled)
```

## Troubleshooting

### Out of memory (CUDA OOM)

Reduce image size or use 2x scale:
```bash
-F "scale=2"
```

### GPU not detected

```bash
nvidia-smi
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

## License

Part of the AX Project (2025)

## Support

For issues or questions:
1. Check API documentation: http://localhost:5010/docs
2. Review logs: `docker logs esrgan-api-standalone`
3. Contact: AX Project Team

---

**Version**: 1.0.0
**Last Updated**: 2025-12-31
**Maintained By**: AX Project Team
