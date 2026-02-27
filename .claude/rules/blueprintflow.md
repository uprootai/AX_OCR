---
paths:
  - "web-ui/src/pages/blueprintflow/**"
  - "web-ui/src/config/nodeDefinitions.ts"
  - "web-ui/src/pages/blueprintflow/templates/**"
  - "gateway-api/blueprintflow/**"
---

# BlueprintFlow 규칙

## 노드 타입 (29개)

| 카테고리 | 노드 |
|----------|------|
| Input | ImageInput, TextInput |
| Detection | YOLO, Table Detector |
| OCR | eDOCr2, PaddleOCR, Tesseract, TrOCR, OCR Ensemble, SuryaOCR, DocTR, EasyOCR |
| Segmentation | EDGNet, Line Detector |
| Preprocessing | ESRGAN |
| Analysis | SkinModel, PID Analyzer, Design Checker |
| Analysis (신규) | GT Comparison, PDF Export, PID Features, Verification Queue, Dimension Updater |
| BOM | Blueprint AI BOM |
| Knowledge | Knowledge |
| AI | VL |
| Control | IF, Loop, Merge |

총 70개+ 파라미터가 `nodeDefinitions.ts`에 정의됨

## 카테고리 타입

```typescript
type NodeCategory =
  | 'input' | 'detection' | 'ocr' | 'segmentation'
  | 'preprocessing' | 'analysis' | 'knowledge' | 'ai' | 'control';
```

**주의**: `'api'` 타입은 사용하지 않음

## 템플릿 작성 규칙

**필수 준수사항:**
1. **API 스펙 동기화**: 템플릿 파라미터는 반드시 `gateway-api/api_specs/*.yaml`에 정의된 파라미터만 사용
2. **유효 파라미터만 사용**: 추측이나 희망사항으로 파라미터 추가 금지

**주요 API 유효 파라미터:**

| API | 유효 파라미터 |
|-----|--------------|
| **eDOCr2** | `language`, `extract_dimensions`, `extract_gdt`, `extract_text`, `extract_tables`, `cluster_threshold`, `visualize`, `enable_crop_upscale`, `crop_preset`, `upscale_scale`, `upscale_denoise` |
| **SkinModel** | `material_type`, `manufacturing_process`, `correlation_length`, `task` |
| **YOLO** | `model_type`, `confidence`, `iou`, `imgsz`, `use_sahi`, `slice_height`, `slice_width`, `overlap_ratio`, `visualize`, `task` |
| **Table Detector** | `mode`, `ocr_engine`, `borderless`, `confidence_threshold`, `min_confidence`, `output_format` |
| **Blueprint AI BOM** | `features` (array: `verification`, `gt_comparison`, `bom_generation`, `dimension_extraction`) |

**금지 파라미터 예시 (API 스펙에 없음):**
- `extract_tolerances`, `extract_bom`, `extract_title_block`, `extract_part_number`
- `analyze_gdt`, `tolerance_stack`, `analyze_clearance`, `machining_difficulty`

**검증 방법:**
```bash
cat gateway-api/api_specs/edocr2.yaml | grep -A 100 "parameters:"
```
