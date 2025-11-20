# 🎯 YOLOv11 API

High-performance object detection service specialized for engineering drawings.

## 📋 Overview

- **Purpose**: Detect and locate objects in technical drawings
- **Model**: YOLOv11 nano (custom-trained)
- **Port**: 5005
- **GPU**: Required (CUDA)
- **Classes**: 14 categories (dimensions, GD&T, text blocks, etc.)

## 🎨 Detection Classes

| Class | Description | Use Case |
|-------|-------------|----------|
| `dimension_line` | Dimension lines | Length measurements |
| `reference_dim` | Reference dimensions | Manufacturing specs |
| `tolerance_dim` | Toleranced dimensions | Quality control |
| `gdt_symbol` | GD&T symbols | Geometric tolerancing |
| `surface_roughness` | Surface finish symbols | Surface quality |
| `text_block` | Text annotations | Notes and labels |
| `title_block` | Title blocks | Drawing metadata |
| ... | (14 total) | Various |

## 🚀 Quick Start (Standalone)

### Prerequisites
- Docker & Docker Compose
- NVIDIA GPU + CUDA 11.8+
- nvidia-docker2

### 1. Run the API

```bash
# Navigate to API directory
cd models/yolo-api

# Start with docker-compose
docker-compose -f docker-compose.single.yml up -d

# Check logs
docker logs yolo-api-standalone -f
```

### 2. Check Health

```bash
curl http://localhost:5005/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "YOLOv11 API",
  "version": "1.0.0",
  "model": "yolo11n.pt"
}
```

### 3. API Documentation

Open in browser: **http://localhost:5005/docs**

## 📡 API Endpoints

### Health Check
```bash
GET /api/v1/health
```

### Object Detection
```bash
POST /api/v1/detect
Content-Type: multipart/form-data

Parameters:
- file: image file (PNG, JPG, JPEG, TIFF, BMP)
- conf_threshold: confidence threshold (default: 0.25)
- iou_threshold: IoU threshold for NMS (default: 0.7)
- imgsz: input image size (default: 1280)
- visualize: generate visualization (default: false)
```

## 🧪 Testing

### Basic Detection

```bash
curl -X POST http://localhost:5005/api/v1/detect \
  -F "file=@/path/to/drawing.jpg" \
  -F "conf_threshold=0.25" \
  -F "visualize=true"
```

### Response Example

```json
{
  "status": "success",
  "file_id": "abc123",
  "detections": [
    {
      "class_id": 0,
      "class_name": "dimension_line",
      "confidence": 0.92,
      "bbox": {
        "x": 100,
        "y": 200,
        "width": 300,
        "height": 50
      },
      "value": "100mm"
    }
  ],
  "detection_count": 42,
  "processing_time": 0.264,
  "model_info": {
    "model_name": "yolo11n",
    "version": "11.0.0",
    "device": "cuda:0"
  },
  "visualized_image": "base64_encoded_string..."
}
```

## 🐳 Docker Image Distribution

### Build Image
```bash
docker build -t ax-yolo-api:latest .
```

### Save Image for Distribution
```bash
docker save ax-yolo-api:latest -o yolo-api.tar
```

**Size**: ~8.2GB (includes PyTorch, CUDA libraries)

### Load Image (on target machine)
```bash
docker load -i yolo-api.tar
```

### Run Standalone Container
```bash
docker run -d \
  --name yolo-api \
  -p 5005:5005 \
  --gpus all \
  -e YOLO_API_PORT=5005 \
  -e YOLO_MODEL_PATH=/app/models/best.pt \
  ax-yolo-api:latest
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `YOLO_API_PORT` | 5005 | API server port |
| `YOLO_MODEL_PATH` | /app/models/best.pt | Model file path |
| `PYTHONUNBUFFERED` | 1 | Python output buffering |

### Model Files

- **Location**: `models/best.pt`
- **Type**: YOLOv11 nano (custom-trained)
- **Input Size**: 1280x1280 (configurable)
- **Classes**: 14

## 📊 Performance

| Metric | GPU (RTX 3080) | CPU (8 cores) |
|--------|----------------|---------------|
| Single image (1280px) | ~0.26s | ~2-3s |
| Throughput | 200+ img/min | 20 img/min |
| Memory (GPU) | ~2GB | N/A |
| Accuracy (mAP@0.5) | 0.89 | 0.89 |

### Performance Tips

1. **Batch Processing**: Process multiple images together
2. **Image Size**: Use `imgsz=640` for faster inference (lower accuracy)
3. **Confidence Threshold**: Increase to reduce false positives
4. **GPU**: Required for production use

## 🔗 Integration with AX PoC

This API is part of the **AX Drawing Analysis System**.

- **Main Project**: [ax-poc](https://github.com/your-org/ax-poc)
- **Usage in Pipeline**: Primary object detection stage
- **Gateway Integration**: Called first in Speed/Hybrid modes

### Pipeline Integration

```python
# Gateway calls YOLO API
response = requests.post(
    "http://yolo-api:5005/api/v1/detect",
    files={"file": image_bytes},
    data={
        "conf_threshold": 0.25,
        "iou_threshold": 0.7,
        "imgsz": 1280,
        "visualize": True
    }
)
```

## 📁 Project Structure

```
yolo-api/
├── Dockerfile                  # Docker build file
├── docker-compose.single.yml   # Standalone deployment
├── README.md                   # This file
├── api_server.py               # FastAPI application (324 lines)
├── models/
│   ├── schemas.py              # Pydantic models
│   └── best.pt                 # YOLOv11 model weights
├── services/
│   └── inference.py            # YOLO inference service
├── utils/
│   └── helpers.py              # Utility functions
├── requirements.txt            # Python dependencies
├── uploads/                    # Uploaded files (temporary)
└── results/                    # Detection results
```

## 🐛 Troubleshooting

### GPU not detected

```bash
# Check NVIDIA driver
nvidia-smi

# Check CUDA availability in container
docker run --rm --gpus all ax-yolo-api python -c "import torch; print(torch.cuda.is_available())"
```

### Out of memory (CUDA OOM)

Reduce image size:
```bash
curl -X POST http://localhost:5005/api/v1/detect \
  -F "file=@image.jpg" \
  -F "imgsz=640"  # Instead of 1280
```

### Model file not found

```bash
# Check model exists
docker exec yolo-api-standalone ls -lh /app/models/best.pt

# Mount model volume correctly
volumes:
  - ./models:/app/models:ro
```

### Low detection accuracy

1. **Adjust confidence threshold**:
   ```bash
   -F "conf_threshold=0.15"  # Lower for more detections
   ```

2. **Check image quality**: Ensure high resolution (1000+ pixels)

3. **Verify correct classes**: Check if your drawing matches training data

## 🎓 Model Training (Optional)

The YOLO model can be retrained with custom data.

### Training Data Format

```
datasets/
├── images/
│   ├── train/
│   └── val/
└── labels/
    ├── train/
    └── val/
```

### Training Command

```bash
# Inside container
yolo task=detect mode=train \
  model=yolo11n.pt \
  data=dataset.yaml \
  epochs=100 \
  imgsz=1280 \
  batch=16
```

**Note**: Training requires separate setup. See [YOLO Training Guide](../../docs/YOLO_TRAINING.md)

## 📄 License

Part of the AX Project (2025)

## 👥 Support

For issues or questions:
1. Check API documentation: http://localhost:5005/docs
2. Review logs: `docker logs yolo-api-standalone`
3. Test with sample images: `/datasets/test_samples/`
4. Contact: AX Project Team

---

**Version**: 1.0.0
**Model Version**: YOLOv11 nano (custom)
**Last Updated**: 2025-11-20
**Maintained By**: AX Project Team
