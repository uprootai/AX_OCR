# 📚 Documentation Index

**Last Updated**: 2025-11-21
**Purpose**: Complete documentation map for LLMs and developers

---

## 🎯 Quick Navigation

| Category | Location | Purpose | Files |
|----------|----------|---------|-------|
| **빠른 시작** | [quickstart/](quickstart/) | 5분 설치 및 첫 워크플로우 | 3 files |
| **아키텍처** | [architecture/](architecture/) | 시스템 구조 및 설계 | 4 files |
| **API 문서** | [api/](api/) | 6개 API 상세 설명 | 6 dirs |
| **BlueprintFlow** | [blueprintflow/](blueprintflow/) | 비주얼 워크플로우 빌더 | 5+ files |
| **작업 가이드** | [workflows/](workflows/) | 실무 작업 방법 | 5 files |
| **문제 해결** | [troubleshooting/](troubleshooting/) | 일반적인 문제 | 3 files |
| **레퍼런스** | [reference/](reference/) | 명령어, 환경변수 등 | 3 files |

---

## 📖 By Use Case

### "프로젝트 처음 시작하는데요?"
1. [quickstart/01_installation.md](quickstart/01_installation.md)
2. [quickstart/02_first_workflow.md](quickstart/02_first_workflow.md)
3. [architecture/01_system_overview.md](architecture/01_system_overview.md)

### "특정 API 사용 방법을 알고 싶어요"
1. [api/](api/) → 원하는 API 디렉토리
2. `overview.md` 읽기 (개요)
3. `parameters.md` 읽기 (파라미터 상세)

### "BlueprintFlow로 워크플로우 만들고 싶어요"
1. [blueprintflow/01_overview.md](blueprintflow/01_overview.md)
2. [blueprintflow/02_node_types.md](blueprintflow/02_node_types.md)
3. [blueprintflow/04_optimization/](blueprintflow/04_optimization/) (최적화)

### "기능 추가/수정하고 싶어요"
1. [workflows/01_add_feature.md](workflows/01_add_feature.md)
2. [workflows/02_modify_function.md](workflows/02_modify_function.md)

### "오류가 발생했어요"
1. [troubleshooting/common_issues.md](troubleshooting/common_issues.md)
2. [troubleshooting/api_errors.md](troubleshooting/api_errors.md)

---

## 🔍 By API

| API | Overview | Parameters | Special Topics |
|-----|----------|------------|----------------|
| **YOLO** | [api/yolo/overview.md](api/yolo/overview.md) | [parameters.md](api/yolo/parameters.md) | [models.md](api/yolo/models.md) (5개 특화 모델) |
| **eDOCr2** | [api/edocr2/overview.md](api/edocr2/overview.md) | [parameters.md](api/edocr2/parameters.md) | [v1_vs_v2.md](api/edocr2/v1_vs_v2.md), [ensemble.md](api/edocr2/ensemble.md) |
| **EDGNet** | [api/edgnet/overview.md](api/edgnet/overview.md) | [parameters.md](api/edgnet/parameters.md) | [graphsage_vs_unet.md](api/edgnet/graphsage_vs_unet.md) |
| **SkinModel** | [api/skinmodel/overview.md](api/skinmodel/overview.md) | [parameters.md](api/skinmodel/parameters.md) | [materials.md](api/skinmodel/materials.md) |
| **PaddleOCR** | [api/paddleocr/overview.md](api/paddleocr/overview.md) | [parameters.md](api/paddleocr/parameters.md) | [languages.md](api/paddleocr/languages.md) |
| **VL** | [api/vl/overview.md](api/vl/overview.md) | [parameters.md](api/vl/parameters.md) | [models.md](api/vl/models.md), [tasks.md](api/vl/tasks.md) |

---

## 📏 Documentation Standards

**All documents follow**:
- ✅ **< 100 lines per file** (quick reading for LLMs)
- ✅ **Single responsibility** (one topic per file)
- ✅ **Clear naming** (01_, 02_ for order)
- ✅ **README.md in each directory** (acts as index)

**File Naming Convention**:
- `overview.md` - High-level introduction
- `parameters.md` - Detailed parameter list
- `examples.md` - Usage examples
- `01_xxx.md` - Ordered documents (01, 02, 03...)

---

## 🆕 Recent Additions (2025-11-21)

- ✅ API parameter audit complete (26 total parameters documented)
- ✅ BlueprintFlow optimization strategy (5 scenarios)
- ✅ Micro-documentation structure implemented
- ✅ All APIs now have dedicated directories

---

**For LLMs**: Start with [quickstart/README.md](quickstart/README.md) or [api/README.md](api/README.md)
