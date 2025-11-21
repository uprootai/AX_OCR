# 📘 Claude Code Project Guide

> **LLM-optimized navigation index**
> All documentation: <100 lines per file, modular structure, hierarchical organization

---

## 🎯 What Is This Project?

**Automated mechanical drawing analysis and manufacturing quote generation**

```
Drawing Image → YOLO Detection → OCR Extraction → Tolerance Analysis → Quote PDF
```

**Tech Stack**: FastAPI + React + YOLO v11 + eDOCr2 + Docker Compose
**Access**: http://localhost:5173

---

## 📚 Documentation Map

**Complete index**: [docs/00_INDEX.md](docs/00_INDEX.md)

| Category | Key Files | Lines |
|----------|-----------|-------|
| **Quick Start** | [QUICK_START.md](QUICK_START.md) | ~80 |
| **Architecture** | [ARCHITECTURE.md](ARCHITECTURE.md) | ~150 |
| **Workflows** | [WORKFLOWS.md](WORKFLOWS.md) | ~120 |
| **Issues** | [KNOWN_ISSUES.md](KNOWN_ISSUES.md) | ~100 |
| **Roadmap** | [ROADMAP.md](ROADMAP.md) | ~200 |
| **API Docs** | [docs/api/](docs/api/) | 6 APIs |
| **BlueprintFlow** | [docs/blueprintflow/](docs/blueprintflow/) | 12 files |

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
├── vl-api/           🤖 Vision LLMs (Port 5004)
└── web-ui/           🌐 React frontend (Port 5173)
```

**Modular API pattern**: api_server.py (endpoints) + services/ (logic) + models/ (schemas)

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

## 🎯 For LLMs: Navigation Guide

### By Task Type

| Task | Read First | Then Read |
|------|-----------|-----------|
| Quick overview | QUICK_START.md | ARCHITECTURE.md |
| Add/modify feature | WORKFLOWS.md | Relevant API docs |
| Debug issue | KNOWN_ISSUES.md | API error logs |
| BlueprintFlow dev | docs/blueprintflow/01_overview.md | 04_optimization/ |
| API parameter info | docs/api/{api}/parameters.md | - |

### LLM Best Practices

1. **Modular reading**: Each doc <100 lines for efficient context usage
2. **Single responsibility**: One topic per file
3. **Track feedback**: "안된다" → KNOWN_ISSUES.md, "잘된다" → RESOLVED
4. **Update roadmap**: Use checkboxes [ ] → [-] → [x] with timestamps
5. **BlueprintFlow isolation**: New routes only, never modify production code

---

## 🌐 Translation (i18n)

**Pattern**: Use `useTranslation()` hook, never hardcode text

```typescript
import { useTranslation } from 'react-i18next';

export default function MyComponent() {
  const { t } = useTranslation();
  return <h1>{t('page.title')}</h1>;
}
```

**Files**: `web-ui/src/locales/{ko,en}.json`
**Rule**: Every new UI component MUST have translations in both languages

**Translated pages**: Dashboard, Guide, Settings, Analyze, Monitor, BlueprintFlow (100%)

---

## 🔮 BlueprintFlow ✅ Phase 1-3 Complete

**Visual workflow builder for mechanical drawing analysis**

**Access**: http://localhost:5173/blueprintflow/builder
**Status**: Frontend complete (1,800 LOC), Backend in progress (Phase 4)

### Quick Facts
- **9 node types**: YOLO, eDOCr2, EDGNet, SkinModel, PaddleOCR, VL, IF, Loop, Merge
- **4 templates**: Basic, Advanced, Loop, Multi-model
- **Full i18n**: Korean/English translations complete
- **Drag-and-drop**: ReactFlow-based visual canvas

### Critical Issue: Over-Simplified Parameters ⚠️

**Problem**: Only 15.4% of actual API functionality exposed in BlueprintFlow (4/26 parameters)

| API | Actual Params | Exposed Params | Coverage |
|-----|--------------|----------------|----------|
| eDOCr2 | 6 | **0** ❌ | 0% |
| SkinModel | 4 | **0** ❌ | 0% |
| VL | 4 | **0** ❌ | 0% |
| YOLO | 6 | 2 | 33% |
| PaddleOCR | 4 | 1 | 25% |
| EDGNet | 4 | 1 | 25% |

**Solution**: Phase 4A - nodeDefinitions.ts complete overhaul (add 22 missing parameters)

### Documentation

**Complete guide**: [docs/blueprintflow/README.md](docs/blueprintflow/README.md)

| Topic | File | Lines |
|-------|------|-------|
| Overview | [01_overview.md](docs/blueprintflow/01_overview.md) | 60 |
| Node types | [02_node_types.md](docs/blueprintflow/02_node_types.md) | 90 |
| Templates | [03_templates.md](docs/blueprintflow/03_templates.md) | 80 |
| YOLO models | [04_optimization/yolo_models.md](docs/blueprintflow/04_optimization/yolo_models.md) | 97 |
| Pipeline options | [04_optimization/pipeline_options.md](docs/blueprintflow/04_optimization/pipeline_options.md) | 99 |
| Optimization guide | [04_optimization/optimization_guide.md](docs/blueprintflow/04_optimization/optimization_guide.md) | 98 |

### Implementation Phases

- [x] **Phase 1**: ReactFlow integration, Canvas setup ✅
- [x] **Phase 2**: 9 node types implementation ✅
- [x] **Phase 3**: Node metadata, Detail panel, i18n ✅
- [ ] **Phase 4**: Backend engine, Parameter overhaul 🔄 IN PROGRESS
- [ ] **Phase 5**: Testing & optimization ⏳

**Next steps**: Implement Phase 4A (add 22 missing parameters to nodeDefinitions.ts)

---

**Last Updated**: 2025-11-21
**Version**: 3.0 (Documentation restructured, micro-docs implemented)
**Managed By**: Claude Code (Sonnet 4.5)
