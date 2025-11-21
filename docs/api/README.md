# 🔌 API Documentation

**Complete guide for all 6 APIs**

---

## 📚 Available APIs

| API | Port | Purpose | Status | Docs |
|-----|------|---------|--------|------|
| **YOLO** | 5005 | Object detection (symbols, dimensions) | ✅ | [yolo/](yolo/) |
| **eDOCr2** | 5001 (v1)<br>5002 (v2) | Korean OCR specialist | ✅ | [edocr2/](edocr2/) |
| **EDGNet** | 5012 | Edge segmentation (GraphSAGE, UNet) | ✅ | [edgnet/](edgnet/) |
| **SkinModel** | 5003 | Tolerance analysis & GD&T validation | ✅ | [skinmodel/](skinmodel/) |
| **PaddleOCR** | 5006 | Multi-language OCR (en, ch, kr) | ✅ | [paddleocr/](paddleocr/) |
| **VL** | 5004 | Vision Language Models (Claude, GPT-4o) | ✅ | [vl/](vl/) |

---

## 📖 How to Read API Docs

Each API directory contains:

1. **overview.md** - What it does, when to use (< 50 lines)
2. **parameters.md** - All parameters explained (< 90 lines)
3. **examples.md** - Usage examples with curl/Python (< 60 lines)
4. **Special topics** - API-specific advanced features

---

## 🔍 Quick Links

### Most Used
- [eDOCr2 v1 vs v2](edocr2/v1_vs_v2.md) - Which version to use?
- [YOLO 5 specialized models](yolo/models.md) - Symbol vs Dimension detector
- [VL 4 tasks](vl/tasks.md) - Info Block, Dimensions, Manufacturing, QC

### Common Questions
- "Which OCR for Korean?" → [edocr2/overview.md](edocr2/overview.md)
- "Which OCR for English?" → [paddleocr/overview.md](paddleocr/overview.md)
- "How to analyze tolerance?" → [skinmodel/overview.md](skinmodel/overview.md)
- "How to segment drawings?" → [edgnet/overview.md](edgnet/overview.md)

---

## 🎯 By Use Case

### Scenario A: Extract dimensions from mechanical drawing
1. YOLO (dimension-detector-v1)
2. eDOCr2 (extract_dimensions=true)
3. SkinModel (tolerance analysis)

### Scenario B: Recognize welding symbols
1. YOLO (symbol-detector-v1)
2. eDOCr2 (extract_text=true)

### Scenario C: English drawing OCR
1. YOLO (text-region-detector-v1)
2. PaddleOCR (lang=en)
3. VL (extract_info_block)

---

**Total Parameters Across All APIs**: 26 parameters
**Average Parameters Per API**: 4-6 parameters

**See**: [../00_INDEX.md](../00_INDEX.md) for complete documentation map
