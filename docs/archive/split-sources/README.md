# Archived: Split Source Files

**Date**: 2025-11-21
**Reason**: These large files have been split into micro-documents (<100 lines each) for better LLM readability

---

## Files Archived

### 1. ALL_MODELS_DETAILED_ANALYSIS.md (538 lines)
**Original purpose**: Complete analysis of all 6 API parameters

**Split into 6 micro-docs** (docs/api/):
- `yolo/parameters.md` (90 lines) - YOLO API parameters
- `edocr2/parameters.md` (94 lines) - eDOCr2 API parameters
- `edgnet/parameters.md` (91 lines) - EDGNet API parameters
- `skinmodel/parameters.md` (84 lines) - SkinModel API parameters
- `paddleocr/parameters.md` (99 lines) - PaddleOCR API parameters
- `vl/parameters.md` (94 lines) - VL API parameters

**Total**: 538 lines → 552 lines across 6 files (~92 lines each)
**Benefit**: LLM can read only relevant API docs instead of all 538 lines

---

### 2. BLUEPRINTFLOW_OPTIMIZATION_STRATEGY.md (226 lines)
**Original purpose**: YOLO model diversification and pipeline optimization strategy

**Split into 3 micro-docs** (docs/blueprintflow/04_optimization/):
- `yolo_models.md` (97 lines) - YOLO model selection strategy
- `pipeline_options.md` (99 lines) - 4 post-processing pipeline options
- `optimization_guide.md` (98 lines) - Implementation roadmap and expected results

**Total**: 226 lines → 294 lines across 3 files (~98 lines each)
**Benefit**: Focused reading - model selection vs pipeline options vs implementation

---

## Migration Summary

**Before restructuring**:
- 2 large files: 764 lines total
- Mixed topics in single files
- Difficult for LLMs to find specific information

**After restructuring**:
- 9 micro-docs: 846 lines total
- Single topic per file
- Hierarchical directory structure
- LLM-friendly navigation

**Philosophy**: "마이크로하게 보관하고 그걸 잘 디렉토리 구조화된 상태로 관리"

---

## How to Use New Structure

**Instead of reading all 538 lines of ALL_MODELS_DETAILED_ANALYSIS.md**:
```bash
# Only read relevant API parameters
docs/api/yolo/parameters.md        # If working with YOLO
docs/api/edocr2/parameters.md      # If working with eDOCr2
```

**Instead of reading all 226 lines of BLUEPRINTFLOW_OPTIMIZATION_STRATEGY.md**:
```bash
# Read by purpose
docs/blueprintflow/04_optimization/yolo_models.md         # Model selection
docs/blueprintflow/04_optimization/pipeline_options.md    # Post-processing
docs/blueprintflow/04_optimization/optimization_guide.md  # Implementation
```

---

**See**: [docs/00_INDEX.md](../../00_INDEX.md) for complete documentation map
