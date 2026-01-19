# API Documentation

**Complete guide for all 20 APIs**
> **최종 업데이트**: 2026-01-17 | **상태**: 20/20 healthy (100%)

---

## Available APIs

### Detection

| API | Port | Purpose | Status | Docs |
|-----|------|---------|--------|------|
| **YOLO** | 5005 | 통합 객체 검출 (engineering, pid_class_aware, pid_class_agnostic, bom_detector) | ✅ | [yolo/](yolo/) |

### OCR

| API | Port | Purpose | Status | Docs |
|-----|------|---------|--------|------|
| **eDOCr2** | 5002 | 한국어 치수/GD&T OCR | ✅ | [edocr2/](edocr2/) |
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
| **Design Checker** | 5019 | P&ID design validation + BWMS rules | ✅ | [design-checker/](design-checker/) |
| **Blueprint AI BOM** | 5020 | Human-in-the-Loop BOM (v10.5) | ✅ | [blueprint-ai-bom/](blueprint-ai-bom/) |
| **PID Features** | 5020 | TECHCROSS P&ID 통합 분석 | ✅ | [pidfeatures/](pidfeatures/) |
| **GT Comparison** | 5020 | Ground Truth 비교 분석 | ✅ | [gtcomparison/](gtcomparison/) |
| **Verification Queue** | 5020 | Human-in-the-Loop 검증 큐 | ✅ | [verificationqueue/](verificationqueue/) |

### Export

| API | Port | Purpose | Status | Docs |
|-----|------|---------|--------|------|
| **Excel Export** | 5020 | 분석 결과 Excel 내보내기 | ✅ | [excelexport/](excelexport/) |
| **PDF Export** | 5020 | 분석 결과 PDF 리포트 | ✅ | [pdfexport/](pdfexport/) |

### Visualization

| API | Port | Purpose | Status | Docs |
|-----|------|---------|--------|------|
| **PID Composer** | 5021 | P&ID 레이어 합성 및 SVG 오버레이 | ✅ | [pid-composer/](pid-composer/) |

### Knowledge & AI

| API | Port | Purpose | Status | Docs |
|-----|------|---------|--------|------|
| **Knowledge** | 5007 | Neo4j + GraphRAG | ✅ | [knowledge/](knowledge/) |
| **VL** | 5004 | Vision Language Models | ✅ | [vl/](vl/) |

---

## How to Read API Docs

Each API directory contains:

1. **parameters.md** - 파라미터 상세 설명
2. **overview.md** - API 개요 (일부)
3. **examples.md** - 사용 예시 (일부)

---

## Quick Links

### Most Used
- [YOLO 4가지 모델](yolo/parameters.md) - engineering, pid_class_aware, pid_class_agnostic, bom_detector
- [eDOCr2 파라미터](edocr2/parameters.md) - 치수, GD&T, 텍스트 추출
- [VL 4 tasks](vl/tasks.md) - Info Block, Dimensions, Manufacturing, QC

### Common Questions
- "Which OCR for Korean?" → [edocr2/parameters.md](edocr2/parameters.md)
- "Which OCR for English?" → [paddleocr/parameters.md](paddleocr/parameters.md)
- "How to analyze tolerance?" → [skinmodel/overview.md](skinmodel/overview.md)
- "How to segment drawings?" → [edgnet/overview.md](edgnet/overview.md)

---

## By Use Case

### Scenario A: 기계도면 치수 추출
```
YOLO (engineering, confidence=0.25)
  → eDOCr2 (extract_dimensions=true)
  → SkinModel (tolerance analysis)
```

### Scenario B: P&ID 심볼 분석
```
YOLO (pid_class_aware, use_sahi=true)
  → Line Detector (라인 검출)
  → PID Analyzer (연결성 분석)
  → Design Checker (설계 검증)
```

### Scenario C: TECHCROSS BWMS 분석
```
PID Features (Valve/Equipment/Checklist 검출)
  → Verification Queue (Human-in-the-Loop)
  → Excel Export / PDF Export (결과 내보내기)
```

### Scenario D: 전력 설비 BOM 생성
```
YOLO (bom_detector, confidence=0.4)
  → eDOCr2 (extract_text=true)
  → Blueprint AI BOM (BOM 생성)
```

---

## Blueprint AI BOM (v10.5)

**Human-in-the-Loop 도면 BOM 생성 시스템**

| 기능 | 설명 |
|------|------|
| 심볼 검출 | YOLO v11 기반 27개 클래스 |
| 치수 OCR | eDOCr2 한국어 치수 인식 |
| GD&T 파싱 | 기하공차/데이텀 파싱 |
| 영역 세분화 | 정면도/측면도/단면도 자동 구분 |
| 노트 추출 | 재료/열처리/표면처리 추출 |
| 리비전 비교 | 버전 간 변경점 감지 |
| VLM 분류 | 도면 타입/산업분야 AI 분류 |

**상세 문서**: [blueprint-ai-bom/parameters.md](blueprint-ai-bom/parameters.md)

---

## Design Checker API (v1.0)

**P&ID 도면 설계 오류 검출 및 규정 검증 API**

| 기능 | 설명 |
|------|------|
| 설계 규칙 | 20개 내장 규칙 (ISO 10628, ISA 5.1) |
| BWMS 규칙 | 7개 내장 + 동적 규칙 (TECHCROSS 전용) |
| 규칙 관리 | Excel 업로드, YAML 저장, 프로필 관리 |
| 제품 필터 | ALL / ECS / HYCHLOR 타입별 규칙 |

**상세 문서**: [design-checker/parameters.md](design-checker/parameters.md)

---

## PID Features (신규)

**TECHCROSS P&ID 통합 분석 시스템**

| 기능 | 설명 |
|------|------|
| Valve Signal List | 밸브 태그/타입/신호 추출 |
| Equipment List | 장비 태그/타입 추출 |
| Design Checklist | 60개 체크리스트 자동 검증 |
| Verification Queue | 신뢰도 기반 검토 큐 |

**관련 문서**:
- [pidfeatures/parameters.md](pidfeatures/parameters.md)
- [verificationqueue/parameters.md](verificationqueue/parameters.md)
- [gtcomparison/parameters.md](gtcomparison/parameters.md)

---

**Total APIs**: 20 (all healthy)
**Total Parameters Across All APIs**: 70+ parameters

**See**: [../00_INDEX.md](../00_INDEX.md) for complete documentation map

**Last Updated**: 2026-01-17
