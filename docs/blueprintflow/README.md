# 🔮 BlueprintFlow Documentation

**Visual Workflow Builder for Drawing Analysis**

---

## 📚 Contents

### Core Documentation
1. [01_overview.md](01_overview.md) - What is BlueprintFlow? (60 lines)
2. [02_node_types.md](02_node_types.md) - 9 node types explained (90 lines)
3. [03_templates.md](03_templates.md) - 8 pre-built templates (80 lines)

### Optimization Strategy
4. [04_optimization/](04_optimization/) - Advanced optimization
   - [yolo_models.md](04_optimization/yolo_models.md) - YOLO model diversification (97 lines)
   - [pipeline_options.md](04_optimization/pipeline_options.md) - 4 post-processing pipelines (99 lines)
   - [optimization_guide.md](04_optimization/optimization_guide.md) - Implementation roadmap (98 lines)

### Implementation
5. [05_implementation/](05_implementation/) - Phase 4 roadmap
   - `phase_4a_nodedefs.md` - nodeDefinitions.ts overhaul
   - `phase_4b_models.md` - YOLO model training
   - `phase_4c_postproc.md` - Post-processing nodes
   - `phase_4d_templates.md` - Advanced templates

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
| **Backend Engine** | 🔄 In Progress | Phase 4 implementation |
| **Parameter Coverage** | ⚠️ 15.4% | Only 4/26 parameters exposed |

**Critical Issue**: All 6 API nodes are over-simplified
- eDOCr2: 0/6 parameters exposed
- SkinModel: 0/4 parameters exposed
- VL: 0/2 parameters exposed

**See**: [04_optimization/](04_optimization/) for detailed analysis

---

## 🔍 By Topic

### "I want to optimize my workflow"
→ Read [04_optimization/optimization_guide.md](04_optimization/optimization_guide.md)

### "Which YOLO model should I use?"
→ Read [04_optimization/yolo_models.md](04_optimization/yolo_models.md)

### "What post-processing options exist?"
→ Read [04_optimization/pipeline_options.md](04_optimization/pipeline_options.md)

### "How to implement Phase 4?"
→ Read [05_implementation/](05_implementation/)

---

**Total Lines**: ~800 lines (split across 12 files)
**Average File Size**: ~65 lines (LLM-friendly)

**See**: [../00_INDEX.md](../00_INDEX.md) for complete documentation map
