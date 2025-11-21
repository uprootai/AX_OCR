# 🔮 BlueprintFlow Documentation

**Visual Workflow Builder for Drawing Analysis**

---

## 📚 Contents

### Optimization & Usage Guides
1. [04_optimization/](04_optimization/) - Advanced optimization guides
   - [yolo_models.md](04_optimization/yolo_models.md) - YOLO model diversification (97 lines)
   - [pipeline_options.md](04_optimization/pipeline_options.md) - 4 post-processing pipelines (99 lines)
   - [optimization_guide.md](04_optimization/optimization_guide.md) - Implementation roadmap (98 lines)

### Additional Documentation
2. [아키텍처 설계](../BLUEPRINTFLOW_ARCHITECTURE_COMPLETE_DESIGN.md) - Complete system design
3. [API 통합 가이드](../BLUEPRINTFLOW_API_INTEGRATION_GUIDE.md) - How to integrate new APIs

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

## 📊 Current Status (2025-11-21)

| Feature | Status | Details |
|---------|--------|---------|
| **Frontend** | ✅ Complete | 9 nodes, templates, save/load |
| **Backend Engine** | ✅ Complete | Pipeline engine, DAG execution |
| **Control Flow** | ✅ Complete | IF, Loop, Merge nodes |
| **Dynamic API** | ✅ Complete | Runtime API registration |

**Features**:
- ✅ Visual workflow builder with ReactFlow
- ✅ 9 node types (8 API + 3 control flow - 1 input)
- ✅ Workflow save/load/share
- ✅ Real-time execution monitoring
- ✅ Template library

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

**Total Lines**: ~800 lines (split across 12 files)
**Average File Size**: ~65 lines (LLM-friendly)

**See**: [../00_INDEX.md](../00_INDEX.md) for complete documentation map
