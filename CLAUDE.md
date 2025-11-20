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

## 🌐 Translation (i18n) Guidelines

**IMPORTANT**: This project supports bilingual UI (Korean/English). When adding or modifying user-facing text:

### 1. **Translation Files Location**
```
web-ui/src/locales/
├── ko.json  ← Korean translations
└── en.json  ← English translations
```

### 2. **When to Add Translations**
Add translation keys whenever you:
- Create new UI components with user-facing text
- Add new pages or routes
- Modify existing text in components
- Add error messages, tooltips, or labels

### 3. **Translation Pattern**
```typescript
// ❌ BAD: Hardcoded text
<h1>도면 분석</h1>

// ✅ GOOD: Use translation keys
import { useTranslation } from 'react-i18next';

export default function MyComponent() {
  const { t } = useTranslation();
  return <h1>{t('analyze.title')}</h1>;
}
```

### 4. **Translation Key Structure**
```json
{
  "pageName": {
    "title": "Page Title",
    "subtitle": "Page description",
    "sectionName": "Section text",
    "buttonLabel": "Button text"
  }
}
```

### 5. **Checklist for Adding Features**
When creating new UI components:
1. ✅ Write the component code
2. ✅ Add Korean translations to `ko.json`
3. ✅ Add English translations to `en.json`
4. ✅ Import and use `useTranslation()` hook
5. ✅ Replace all hardcoded text with `t('key')`
6. ✅ Test language toggle (🌐 icon in header)

### 6. **Existing Translated Pages**
- ✅ Header (navigation)
- ✅ Sidebar (menu)
- ✅ Dashboard
- ✅ Guide
- ✅ Settings
- ✅ Analyze
- ✅ Monitor
- ✅ **BlueprintFlow (완전 번역 완료)** ⭐ NEW
  - Builder, List, Templates, NodePalette, NodeDetailPanel
- ⚠️ Docs, Test pages (partially translated)

**If you add new UI text without translations, the feature is incomplete.**

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

### 🔮 BlueprintFlow ✅ PHASE 1-3 COMPLETE (2025-11-20)
- **[BLUEPRINTFLOW_ARCHITECTURE_COMPLETE_DESIGN.md](docs/BLUEPRINTFLOW_ARCHITECTURE_COMPLETE_DESIGN.md)** - Complete design document
  - Visual workflow builder architecture ✅ IMPLEMENTED
  - Pipeline engine implementation ⏳ IN PROGRESS
  - Node types and data flow ✅ IMPLEMENTED (9 nodes)
  - 5-phase implementation roadmap ✅ Phase 1-3 완료
- **[BLUEPRINTFLOW_ARCHITECTURE_EVALUATION.md](docs/BLUEPRINTFLOW_ARCHITECTURE_EVALUATION.md)** - Current vs BlueprintFlow comparison
  - Feature comparison matrix
  - Pros and cons analysis
  - Use case coverage
- **[HYBRID_VS_FULL_BLUEPRINTFLOW_COMPARISON.md](docs/HYBRID_VS_FULL_BLUEPRINTFLOW_COMPARISON.md)** - Implementation approach comparison
  - Hybrid approach (1-2 weeks, 500 lines)
  - Full BlueprintFlow (5 weeks, 7,500 lines)
  - ROI analysis

**Current Status**: Frontend 100% complete, Backend engine in progress

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
   - BlueprintFlow implementation? → BLUEPRINTFLOW_ARCHITECTURE_COMPLETE_DESIGN.md

2. **Follow modular structure**:
   - Files are <200 lines for efficient context usage
   - Each module has single responsibility
   - BlueprintFlow code goes in separate `/blueprintflow` directory

3. **Track user feedback**:
   - User says "안된다" → Add to KNOWN_ISSUES.md
   - User says "잘된다" → Mark issue as RESOLVED

4. **Update roadmap**:
   - Use checkboxes: [ ] → [-] → [x]
   - Add timestamps on completion

5. **BlueprintFlow development**:
   - **NEVER modify existing production code** (gateway-api, web-ui main routes)
   - Create new routes under `/blueprintflow` or `/workflow`
   - Use feature flags to enable/disable BlueprintFlow features
   - Test in isolation before integration
   - Follow 5-phase roadmap in BLUEPRINTFLOW_ARCHITECTURE_COMPLETE_DESIGN.md

---

## 🔮 BlueprintFlow: Visual Workflow Builder ✅ PHASE 1-3 COMPLETE

### What is BlueprintFlow?

**BlueprintFlow** is a visual workflow builder for mechanical drawing analysis, allowing users to compose API pipelines like Lego blocks.

**Status**: ✅ **Frontend Complete** (Phase 1-3 완료, 2025-11-20)

**Key Concepts**:
- **Blueprint**: Mechanical drawing domain (용접, 베어링, 기어 등 14개 심볼)
- **Flow**: Visual workflow composition (drag-and-drop nodes)
- **Nodes**: 9 types - YOLO, eDOCr2, EDGNet, SkinModel, PaddleOCR, VL, IF, Loop, Merge
- **Canvas**: ReactFlow-based visual editor
- **Access**: http://localhost:5173/blueprintflow/builder

### Implementation Status: Frontend ✅ Complete

| Feature | Status | Details |
|---------|--------|---------|
| **Visual Canvas** | ✅ Complete | ReactFlow drag-and-drop, grid background, minimap |
| **9 Node Types** | ✅ Complete | API (6) + Control (3) fully implemented |
| **Node Metadata** | ✅ Complete | 265 lines - nodeDefinitions.ts |
| **Detail Panel** | ✅ Complete | 270 lines - NodeDetailPanel.tsx |
| **Real-time Parameter Editing** | ✅ Complete | Sliders, dropdowns, text inputs, checkboxes |
| **Workflow Save/Load** | ✅ Complete | localStorage with JSON format |
| **4 Templates** | ✅ Complete | Basic, Advanced, Loop, Multi-model |
| **i18n Support** | ✅ Complete | Korean/English full translation |
| **Node Selection Feedback** | ✅ Complete | Border glow on selection |
| **Individual Delete** | ✅ Complete | Delete key support |
| **Node Palette** | ✅ Complete | Drag-and-drop node library |
| **Workflow List** | ✅ Complete | Saved workflow management |
| **Backend Engine** | 🔄 In Progress | Pipeline execution engine (Phase 4) |
| **Workflow Execution** | 🔄 In Progress | API orchestration (Phase 4) |

### Safe Development Strategy

1. **Separate Section**: Create `/blueprintflow` route in web-ui
2. **Independent Backend**: New endpoints `/api/v1/workflow/*`
3. **Feature Flag**: `ENABLE_BLUEPRINTFLOW` environment variable
4. **No Impact**: Existing `/analyze` page remains unchanged
5. **Gradual Rollout**: Test → Beta → Production

### File Structure for BlueprintFlow ✅ IMPLEMENTED

```
web-ui/src/
├── pages/
│   ├── analyze/                  ← Production (unchanged)
│   └── blueprintflow/            ✅ NEW: BlueprintFlow section
│       ├── BlueprintFlowBuilder.tsx  ✅ Canvas editor (300 lines)
│       ├── WorkflowList.tsx          ✅ Workflow management (150 lines)
│       └── WorkflowTemplates.tsx     ✅ Template gallery (200 lines)
├── components/
│   └── blueprintflow/            ✅ NEW: BlueprintFlow components
│       ├── NodePalette.tsx           ✅ Node library (150 lines)
│       ├── NodeDetailPanel.tsx       ✅ Detail panel (270 lines)
│       └── nodes/                    ✅ 9 node types
│           ├── ApiNodes.tsx          ✅ 6 API nodes (200 lines)
│           ├── ControlNodes.tsx      ✅ 3 control nodes (170 lines)
│           └── BaseNode.tsx          ✅ Base component (85 lines)
├── config/
│   └── nodeDefinitions.ts        ✅ Node metadata (265 lines)
├── store/
│   └── workflowStore.ts          ✅ Zustand state (150 lines)
├── locales/
│   ├── ko.json                   ✅ Korean translations
│   └── en.json                   ✅ English translations
└── i18n.ts                       ✅ i18n setup

gateway-api/
├── api_server.py                 ← Add new routes (Phase 4)
├── blueprintflow/                ⏳ TODO: Backend engine
│   ├── pipeline_engine.py        ⏳ TODO: Dynamic pipeline
│   └── workflow_manager.py       ⏳ TODO: Workflow CRUD
```

**Lines of Code**:
- Frontend: ~1,800 lines (fully implemented)
- Backend: ~0 lines (Phase 4 - in progress)

### LLM Development Workflow

When implementing BlueprintFlow:

1. **Read the design first**:
   ```bash
   # Always start here
   docs/BLUEPRINTFLOW_ARCHITECTURE_COMPLETE_DESIGN.md
   ```

2. **Check current phase**:
   - Phase 1: ✅ COMPLETE - ReactFlow integration, Canvas setup
   - Phase 2: ✅ COMPLETE - 9 node types implementation
   - Phase 3: ✅ COMPLETE - Node metadata, Detail panel, i18n
   - Phase 4: 🔄 IN PROGRESS - Backend pipeline engine, Workflow execution
   - Phase 5: ⏳ TODO - Testing & optimization

3. **Create isolated code**:
   - New files only (no edits to existing production code)
   - Use separate routes (`/blueprintflow`, not `/analyze`)
   - Test independently

4. **Incremental testing**:
   - Each phase should be testable via web UI
   - User should see progress in real-time
   - Provide demo workflows

5. **Documentation updates**:
   - Update ROADMAP.md with checkbox progress
   - Add screenshots to docs/images/
   - Document API endpoints in WORKFLOWS.md

---

**Last Updated**: 2025-11-20
**Version**: 2.2 (BlueprintFlow Phase 1-3 완료)
**Managed By**: Claude Code (Sonnet 4.5)

## 📊 BlueprintFlow Implementation Summary

**Total Development Time**: ~6 hours (2025-11-20)
**Total Lines of Code**: ~1,800 lines (frontend only)
**Files Created**: 15 new files
**Dependencies Added**: reactflow, zustand, react-i18next, i18next

**Key Achievements**:
1. ✅ Complete visual workflow builder with drag-and-drop
2. ✅ 9 node types with full metadata system
3. ✅ Real-time parameter editing with rich UI controls
4. ✅ Comprehensive help system (NodeDetailPanel)
5. ✅ Full Korean/English internationalization
6. ✅ Workflow save/load with localStorage
7. ✅ 4 production-ready templates
8. ✅ Professional UX (selection feedback, keyboard shortcuts)

**Next Steps** (Phase 4):
- Backend pipeline execution engine
- Workflow API endpoints (CRUD)
- Real-time execution progress tracking
- Result visualization integration
