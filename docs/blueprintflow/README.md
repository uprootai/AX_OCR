# 🔮 BlueprintFlow Documentation

**Visual Workflow Builder for Drawing Analysis**
> **최종 업데이트**: 2025-12-24 | **버전**: v9.0

---

## 📚 Contents

### Optimization & Usage Guides
1. [04_optimization/](04_optimization/) - Advanced optimization guides
   - [yolo_models.md](04_optimization/yolo_models.md) - YOLO model diversification (97 lines)
   - [pipeline_options.md](04_optimization/pipeline_options.md) - 4 post-processing pipelines (99 lines)
   - [optimization_guide.md](04_optimization/optimization_guide.md) - Implementation roadmap (98 lines)

### Additional Documentation
2. [아키텍처 설계](BLUEPRINTFLOW_ARCHITECTURE_COMPLETE_DESIGN.md) - Complete system design
3. [API 통합 가이드](BLUEPRINTFLOW_API_INTEGRATION_GUIDE.md) - How to integrate new APIs
4. **[Blueprint AI BOM](../../blueprint-ai-bom/docs/README.md)** - 🆕 Human-in-the-Loop BOM 생성

---

## 🎯 Quick Start

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

## 📊 Current Status (2025-12-24)

| Feature | Status | Details |
|---------|--------|---------|
| **Frontend** | ✅ Complete | 21 nodes, templates, save/load |
| **Backend Engine** | ✅ Complete | Pipeline engine, DAG execution |
| **Control Flow** | ✅ Complete | IF, Loop, Merge nodes |
| **Dynamic API** | ✅ Complete | Runtime API registration |
| **API Services** | ✅ Complete | 18/18 healthy (100%) |
| **Blueprint AI BOM** | ✅ Complete | v9.0 장기 로드맵 완료 |

**Features**:
- ✅ Visual workflow builder with ReactFlow
- ✅ 21 node types (18 API + 3 control flow)
- ✅ Workflow save/load/share
- ✅ Real-time execution monitoring
- ✅ Template library
- ✅ **18개 기능 체크박스 + 툴팁** (v8.1)
- ✅ **장기 로드맵 4개 기능** (v9.0)

**See**: [04_optimization/](04_optimization/) for optimization guides

---

## 🔍 By Topic

### "I want to optimize my workflow"
→ Read [04_optimization/optimization_guide.md](04_optimization/optimization_guide.md)

### "Which YOLO model should I use?"
→ Read [04_optimization/yolo_models.md](04_optimization/yolo_models.md)

### "What post-processing options exist?"
→ Read [04_optimization/pipeline_options.md](04_optimization/pipeline_options.md)

### "How does the system work?"
→ Read [BLUEPRINTFLOW_ARCHITECTURE_COMPLETE_DESIGN.md](../BLUEPRINTFLOW_ARCHITECTURE_COMPLETE_DESIGN.md)

---

## 🆕 v9.0 장기 로드맵 기능

| 기능 | 설명 |
|------|------|
| 🗺️ 도면 영역 세분화 | 정면도/측면도/단면도 자동 구분 |
| 📋 주석/노트 추출 | 재료/열처리/표면처리 노트 추출 |
| 🔄 리비전 비교 | 도면 버전 간 변경점 감지 |
| 🤖 VLM 자동 분류 | 도면 타입/산업분야 AI 분류 |

**상세 문서**: [Blueprint AI BOM 장기 로드맵](../../blueprint-ai-bom/docs/features/longterm_features.md)

---

**Total Lines**: ~800 lines (split across 12 files)
**Average File Size**: ~65 lines (LLM-friendly)

**See**: [../00_INDEX.md](../00_INDEX.md) for complete documentation map

**Last Updated**: 2025-12-24
