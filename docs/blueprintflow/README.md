# BlueprintFlow Documentation

**Visual Workflow Builder for Drawing Analysis**
> **최종 업데이트**: 2026-01-17 | **버전**: v23.1

---

## Contents

### Optimization & Usage Guides
1. [04_optimization/](04_optimization/) - Advanced optimization guides
   - [yolo_models.md](04_optimization/yolo_models.md) - YOLO model types
   - [pipeline_options.md](04_optimization/pipeline_options.md) - Post-processing pipelines
   - [optimization_guide.md](04_optimization/optimization_guide.md) - Implementation roadmap

### Additional Documentation
2. [아키텍처 설계](BLUEPRINTFLOW_ARCHITECTURE_COMPLETE_DESIGN.md) - Complete system design
3. [API 통합 가이드](BLUEPRINTFLOW_API_INTEGRATION_GUIDE.md) - How to integrate new APIs
4. **[Blueprint AI BOM](../../blueprint-ai-bom/docs/README.md)** - Human-in-the-Loop BOM 생성
5. **[시스템 아키텍처](../../web-ui/public/docs/architecture/system-architecture.md)** - v3.0 아키텍처

---

## Quick Start

**Access BlueprintFlow**:
```
http://localhost:5173/blueprintflow/builder
```

**Create First Workflow** (2 minutes):
1. Drag **YOLO** node to canvas
2. Drag **eDOCr2** node
3. Connect: YOLO output → eDOCr2 input
4. Click **Run**

---

## Current Status (2025-12-31)

| Feature | Status | Details |
|---------|--------|---------|
| **Frontend** | ✅ Complete | 28 nodes, templates, save/load |
| **Backend Engine** | ✅ Complete | Pipeline engine, DAG execution |
| **Control Flow** | ✅ Complete | IF, Loop, Merge nodes |
| **Dynamic API** | ✅ Complete | Runtime API registration |
| **API Services** | ✅ Complete | 20/20 healthy (100%) |
| **Blueprint AI BOM** | ✅ Complete | v10.5 TECHCROSS 통합 |
| **디자인 패턴** | ✅ Complete | 100/100점 달성 |
| **테스트** | ✅ Complete | 505개 통과 (gateway 364, web-ui 141) |

**Features**:
- ✅ Visual workflow builder with ReactFlow
- ✅ 28 node types (25 API + 3 control flow)
- ✅ Workflow save/load/share
- ✅ Real-time execution monitoring
- ✅ Template library
- ✅ 18개 기능 체크박스 + 툴팁
- ✅ TECHCROSS 1-1, 1-2, 1-3 완료
- ✅ 모듈화 완료 (NodePalette 분리)
- ✅ 5개 신규 노드 (GT Comparison, PDF/Excel Export, PID Features, Verification Queue)

---

## By Topic

### "I want to optimize my workflow"
→ Read [04_optimization/optimization_guide.md](04_optimization/optimization_guide.md)

### "Which YOLO model should I use?"
→ Read [04_optimization/yolo_models.md](04_optimization/yolo_models.md)

| model_type | Classes | Use Case |
|------------|---------|----------|
| engineering | 14 | 기계도면 치수/GD&T |
| pid_class_aware | 32 | P&ID 심볼 분류 |
| pid_class_agnostic | 1 | P&ID 위치만 |
| bom_detector | 27 | 전력 설비 |

### "What post-processing options exist?"
→ Read [04_optimization/pipeline_options.md](04_optimization/pipeline_options.md)

### "How does the system work?"
→ Read [BLUEPRINTFLOW_ARCHITECTURE_COMPLETE_DESIGN.md](BLUEPRINTFLOW_ARCHITECTURE_COMPLETE_DESIGN.md)

---

## API Services (20개)

| Category | Service | Port | GPU |
|----------|---------|------|-----|
| Orchestrator | Gateway | 8000 | - |
| Detection | YOLO | 5005 | ✓ |
| OCR | eDOCr2, PaddleOCR, TrOCR, EasyOCR | 5002-5015 | ✓ |
| OCR | Tesseract, Surya, DocTR, Ensemble | 5008-5014 | - |
| Segmentation | EDGNet, Line Detector | 5012, 5016 | ✓/- |
| Analysis | SkinModel, PID Analyzer, Design Checker | 5003-5019 | - |
| Analysis | Blueprint AI BOM | 5020 | - |
| AI | VL | 5004 | ✓ |
| Knowledge | Knowledge | 5007 | - |
| Preprocessing | ESRGAN | 5010 | ✓ |

---

## v23.0 Changes

- **ESLint 에러 0개 달성**: fast-refresh 규칙 준수
- **28개 노드**: 5개 신규 노드 추가
- **505개 테스트 통과**: Executor 단위 테스트 126개 추가
- **Feature Definition 동기화 자동화**: sync_feature_definitions.py
- **Executor 개발 가이드**: EXECUTOR_DEVELOPMENT_GUIDE.md

---

**Total Documentation**: ~800 lines (split across 12 files)
**Average File Size**: ~65 lines (LLM-friendly)

**Last Updated**: 2026-01-17
