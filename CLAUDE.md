# 📘 Claude Code Project Guide

> **Quick index for LLM-optimized project navigation**
>
> All documentation follows best practices: <100 lines per file, modular structure

---

## 🎯 What Is This Project?

**Automated mechanical drawing analysis and manufacturing quote generation**

```
Drawing Image → YOLO Detection → OCR Extraction → Tolerance Analysis → Quote PDF
```

**Tech Stack**: FastAPI + React + YOLO v11 + eDOCr2 + Docker Compose

---

## 📚 Documentation Map

### 🚀 Getting Started
- **[QUICK_START.md](QUICK_START.md)** - 5-minute project overview
  - What is this?
  - Architecture diagram
  - Common commands
  - Health checks

### 🏗️ Understanding the System
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed system design
  - Microservices map
  - Modular code structure
  - Data flow (Speed/Hybrid modes)
  - Design patterns
  - Performance characteristics

### 🔧 Working with Code
- **[WORKFLOWS.md](WORKFLOWS.md)** - Step-by-step task guides
  - Add new feature to API
  - Modify existing function
  - Delete deprecated feature
  - Debug common errors
  - Test individual APIs
  - Docker workflows

### 🐛 Tracking Issues
- **[KNOWN_ISSUES.md](KNOWN_ISSUES.md)** - Problem tracker
  - User feedback tracking ("안된다" / "잘된다")
  - Issue resolution workflow
  - Common problems & quick fixes

### 🗺️ Project Planning
- **[ROADMAP.md](ROADMAP.md)** - Project tracking system
  - Phase progress with checkboxes
  - Next sprint priorities
  - Metrics & KPIs
  - Decision log

---

## 📁 Project Structure

```
/home/uproot/ax/poc/
├── gateway-api/      ⭐ Main orchestrator (Port 8000)
├── yolo-api/         🎯 Object detection (Port 5005)
├── edocr2-v2-api/    📝 OCR service (Port 5002)
├── edgnet-api/       🎨 Segmentation (Port 5012)
├── skinmodel-api/    📐 Tolerance (Port 5003)
├── paddleocr-api/    📄 Aux OCR (Port 5006)
└── web-ui/           🌐 React frontend (Port 5173)
```

**All APIs follow modular pattern**:
```
{api-name}/
├── api_server.py (200-350 lines) ← Endpoints only
├── models/schemas.py ← Pydantic models
├── services/{service}.py ← Business logic
└── utils/helpers.py ← Utility functions
```

---

## ⚡ Quick Commands

```bash
# Start all services
docker-compose up -d

# Check health
curl http://localhost:8000/api/v1/health

# View logs
docker logs gateway-api -f

# Test pipeline
curl -X POST -F "file=@test.jpg" \
  -F "pipeline_mode=speed" \
  http://localhost:8000/api/v1/process
```

---

## 🎯 For LLMs: Best Practices

1. **Read documentation by purpose**:
   - Quick task? → WORKFLOWS.md
   - Understanding system? → ARCHITECTURE.md
   - Debugging? → KNOWN_ISSUES.md

2. **Follow modular structure**:
   - Files are <200 lines for efficient context usage
   - Each module has single responsibility

3. **Track user feedback**:
   - User says "안된다" → Add to KNOWN_ISSUES.md
   - User says "잘된다" → Mark issue as RESOLVED

4. **Update roadmap**:
   - Use checkboxes: [ ] → [-] → [x]
   - Add timestamps on completion

---

**Last Updated**: 2025-11-19
**Version**: 2.0 (Post-refactoring)
**Managed By**: Claude Code (Sonnet 4.5)
