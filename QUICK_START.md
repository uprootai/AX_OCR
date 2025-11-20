# ⚡ Quick Start Guide

**5분 안에 프로젝트 파악하기**

---

## 🎯 What Is This?

**도면 OCR 및 제조 견적 자동화 시스템**

```
도면 이미지 → YOLO 검출 → OCR 추출 → 공차 분석 → 자동 견적서
```

---

## 🏗️ Architecture (30초 이해)

```
Web UI (React) → Gateway API → [ YOLO | eDOCr2 | EDGNet | Skin Model ]
                                   ↓       ↓        ↓         ↓
                              객체검출   OCR    세그멘테이션  공차예측
```

**All APIs**: Refactored modular structure
```
api_server.py (200-350 lines) + models/ + services/ + utils/
```

---

## 📁 Project Structure

```
/home/uproot/ax/poc/
├── gateway-api/           ⭐ Main orchestrator (Port 8000)
├── web-ui/                🌐 React frontend (Port 5173)
└── models/                🆕 All inference APIs (standalone ready)
    ├── yolo-api/          🎯 Object detection (Port 5005)
    ├── edocr2-v2-api/     📝 OCR service (Port 5002)
    ├── edgnet-api/        🎨 Segmentation (Port 5012)
    ├── skinmodel-api/     📐 Tolerance (Port 5003)
    ├── paddleocr-api/     📄 Aux OCR (Port 5006)
    └── vl-api/            🔑 Vision-Language (Port 5004)
```

---

## 🚀 Common Tasks

### Start Services
```bash
cd /home/uproot/ax/poc
docker-compose up -d
```

### Check Health
```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:5005/api/v1/health
```

### Test Pipeline
```bash
curl -X POST -F "file=@test.jpg" \
  -F "pipeline_mode=speed" \
  -F "use_ocr=true" \
  http://localhost:8000/api/v1/process
```

### View Logs
```bash
docker logs gateway-api --tail 50
docker logs yolo-api -f  # Note: Container names remain the same
```

### Run Individual API
```bash
# Standalone execution
cd models/yolo-api
docker-compose -f docker-compose.single.yml up -d

# Check API docs
http://localhost:5005/docs
```

---

## 📚 Learn More

- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Workflows**: [WORKFLOWS.md](WORKFLOWS.md)
- **Issues**: [KNOWN_ISSUES.md](KNOWN_ISSUES.md)
- **Roadmap**: [ROADMAP.md](ROADMAP.md)
- **LLM Guide**: [LLM_USABILITY_GUIDE.md](LLM_USABILITY_GUIDE.md)

---

## 🐛 Having Issues?

1. Check [KNOWN_ISSUES.md](KNOWN_ISSUES.md)
2. Check logs: `docker logs <service-name>`
3. Restart service: `docker-compose restart <service-name>`

---

**Updated**: 2025-11-19
