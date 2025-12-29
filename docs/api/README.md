# 🔌 API Documentation

**Complete guide for all 18 APIs**
> **최종 업데이트**: 2025-12-29 | **상태**: 18/18 healthy (100%)

---

## 📚 Available APIs

### Detection
| API | Port | Purpose | Status | Docs |
|-----|------|---------|--------|------|
| **YOLO** | 5005 | Object detection (model_type으로 P&ID 지원) | ✅ | [yolo/](yolo/) |

### OCR
| API | Port | Purpose | Status | Docs |
|-----|------|---------|--------|------|
| **eDOCr2** | 5002 | Korean dimension OCR | ✅ | [edocr2/](edocr2/) |
| **PaddleOCR** | 5006 | Multi-language OCR (en, ch, kr) | ✅ | [paddleocr/](paddleocr/) |
| **Tesseract** | 5008 | Document OCR | ✅ | [tesseract/](tesseract/) |
| **TrOCR** | 5009 | Handwriting OCR | ✅ | [trocr/](trocr/) |
| **OCR Ensemble** | 5011 | 4-engine weighted voting | ✅ | [ocr-ensemble/](ocr-ensemble/) |
| **Surya OCR** | 5013 | 90+ languages, layout analysis | ✅ | [surya-ocr/](surya-ocr/) |
| **DocTR** | 5014 | 2-stage OCR pipeline | ✅ | [doctr/](doctr/) |
| **EasyOCR** | 5015 | 80+ languages, CPU-friendly | ✅ | [easyocr/](easyocr/) |

### Segmentation
| API | Port | Purpose | Status | Docs |
|-----|------|---------|--------|------|
| **EDGNet** | 5012 | Edge segmentation (GraphSAGE, UNet) | ✅ | [edgnet/](edgnet/) |
| **Line Detector** | 5016 | P&ID line detection | ✅ | [line-detector/](line-detector/) |

### Preprocessing
| API | Port | Purpose | Status | Docs |
|-----|------|---------|--------|------|
| **ESRGAN** | 5010 | 4x super resolution | ✅ | [esrgan/](esrgan/) |

### Analysis
| API | Port | Purpose | Status | Docs |
|-----|------|---------|--------|------|
| **SkinModel** | 5003 | Tolerance analysis & GD&T validation | ✅ | [skinmodel/](skinmodel/) |
| **PID Analyzer** | 5018 | P&ID connectivity & BOM | ✅ | [pid-analyzer/](pid-analyzer/) |
| **Design Checker** | 5019 | P&ID design validation + BWMS rules (v1.0) | ✅ | [design-checker/](design-checker/) |
| **Blueprint AI BOM** | 5020 | Human-in-the-Loop BOM (v10.3) | ✅ | [blueprint-ai-bom/](blueprint-ai-bom/) |

### Knowledge & AI
| API | Port | Purpose | Status | Docs |
|-----|------|---------|--------|------|
| **Knowledge** | 5007 | Neo4j + GraphRAG | ✅ | [knowledge/](knowledge/) |
| **VL** | 5004 | Vision Language Models | ✅ | [vl/](vl/) |

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

## 🆕 Blueprint AI BOM (v9.0)

**Human-in-the-Loop 도면 BOM 생성 시스템**

| 기능 | 설명 |
|------|------|
| 🎯 심볼 검출 | YOLO v11 기반 27개 클래스 |
| 📏 치수 OCR | eDOCr2 한국어 치수 인식 |
| 📐 GD&T 파싱 | 기하공차/데이텀 파싱 |
| 🗺️ 영역 세분화 | 정면도/측면도/단면도 자동 구분 |
| 📋 노트 추출 | 재료/열처리/표면처리 추출 |
| 🔄 리비전 비교 | 버전 간 변경점 감지 |
| 🤖 VLM 분류 | 도면 타입/산업분야 AI 분류 |

**상세 문서**: [blueprint-ai-bom/parameters.md](blueprint-ai-bom/parameters.md)

---

## 🛡️ Design Checker API (v1.0)

**P&ID 도면 설계 오류 검출 및 규정 검증 API**

| 기능 | 설명 |
|------|------|
| 📋 설계 규칙 | 20개 내장 규칙 (ISO 10628, ISA 5.1) |
| ⚓ BWMS 규칙 | 7개 내장 + 동적 규칙 (TECHCROSS 전용) |
| 📁 규칙 관리 | Excel 업로드, YAML 저장, 프로필 관리 |
| 🔧 제품 필터 | ALL / ECS / HYCHLOR 타입별 규칙 |

### 주요 엔드포인트

| 엔드포인트 | 설명 |
|-----------|------|
| `POST /api/v1/check` | 통합 설계 검증 |
| `POST /api/v1/check/bwms` | BWMS 전용 검증 |
| `POST /api/v1/rules/disable` | 규칙 비활성화 |
| `POST /api/v1/checklist/upload` | Excel 체크리스트 업로드 |

**상세 문서**: [design-checker/parameters.md](design-checker/parameters.md)

---

**Total APIs**: 18 (all healthy)
**Total Parameters Across All APIs**: 50+ parameters
**Average Parameters Per API**: 4-6 parameters

**See**: [../00_INDEX.md](../00_INDEX.md) for complete documentation map

**Last Updated**: 2025-12-29
