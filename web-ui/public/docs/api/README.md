# API Reference

> **AX 도면 분석 시스템 - 18개 API 완전 가이드**

---

## API 서비스 현황

### Detection (검출)

| API | 포트 | 용도 | 상태 | GPU |
|-----|------|------|------|-----|
| **YOLO** | 5005 | 통합 검출 (model_type으로 P&ID 지원) | ✅ 운영 | 필수 |

### OCR (문자 인식)

| API | 포트 | 용도 | 상태 | GPU |
|-----|------|------|------|-----|
| **eDOCr2** | 5002 | 기계 도면 치수 인식 (한국어 특화) | ✅ 운영 | 권장 |
| **PaddleOCR** | 5006 | 다국어 OCR (80+ 언어) | ✅ 운영 | 권장 |
| **Tesseract** | 5008 | 문서 OCR (오픈소스 표준) | ✅ 운영 | 불필요 |
| **TrOCR** | 5009 | 손글씨 OCR (Transformer 기반) | ✅ 운영 | 권장 |
| **Surya OCR** | 5013 | 다국어 OCR (90+ 언어, 레이아웃) | ✅ 운영 | 권장 |
| **DocTR** | 5014 | 문서 OCR (2단계 파이프라인) | ✅ 운영 | 권장 |
| **EasyOCR** | 5015 | 범용 OCR (80+ 언어, CPU 친화적) | ✅ 운영 | 선택 |
| **OCR Ensemble** | 5011 | 4엔진 가중 투표 앙상블 | ✅ 운영 | 권장 |

### Segmentation (세그멘테이션)

| API | 포트 | 용도 | 상태 | GPU |
|-----|------|------|------|-----|
| **EDGNet** | 5012 | 엣지 세그멘테이션 (GraphSAGE) | ✅ 운영 | 필수 |
| **Line Detector** | 5016 | P&ID 라인/연결 검출 | ✅ 운영 | 권장 |

### Preprocessing (전처리)

| API | 포트 | 용도 | 상태 | GPU |
|-----|------|------|------|-----|
| **ESRGAN** | 5010 | 이미지 업스케일링 (2x/4x) | ✅ 운영 | 필수 |

### Analysis (분석)

| API | 포트 | 용도 | 상태 | GPU |
|-----|------|------|------|-----|
| **SkinModel** | 5003 | 공차 분석 및 GD&T 검증 | ✅ 운영 | 권장 |
| **PID Analyzer** | 5018 | P&ID 연결 분석, BOM 생성 | ✅ 운영 | 불필요 |
| **Design Checker** | 5019 | P&ID 설계 규칙 검증 | ✅ 운영 | 불필요 |

### Knowledge (지식)

| API | 포트 | 용도 | 상태 | GPU |
|-----|------|------|------|-----|
| **Knowledge** | 5007 | Neo4j + GraphRAG 지식 엔진 | ✅ 운영 | 불필요 |

### AI (Vision-Language)

| API | 포트 | 용도 | 상태 | GPU |
|-----|------|------|------|-----|
| **VL** | 5004 | Vision-Language 모델 (Qwen2-VL) | ✅ 운영 | 필수 |

---

## 용도별 권장 파이프라인

### 기계 도면 치수 추출
```
ImageInput → YOLO → eDOCr2 → SkinModel
```

### P&ID 도면 분석
```
ImageInput → YOLO (model_type=pid_class_aware) → Line Detector → PID Analyzer → Design Checker
```

### 저해상도 도면 개선
```
ImageInput → ESRGAN(2x) → eDOCr2
```

### 고정밀 OCR (앙상블)
```
ImageInput → OCR Ensemble (eDOCr2 + PaddleOCR + Tesseract + TrOCR)
```

---

## 공통 API 규격

### Health Check
```bash
GET /health
GET /api/v1/health
```

### 기본 응답 형식
```json
{
  "status": "success",
  "data": { ... },
  "processing_time": 1.234
}
```

### 에러 응답
```json
{
  "status": "error",
  "detail": "Error message",
  "code": 400
}
```

---

## 리소스 요구사항 요약

| 카테고리 | 최소 VRAM | 권장 VRAM | CPU 대체 |
|----------|-----------|-----------|----------|
| Detection | 2GB | 4GB | 10x 느림 |
| OCR | 1GB | 2GB | 3-5x 느림 |
| Segmentation | 4GB | 6GB | 어려움 |
| Preprocessing | 4GB | 6GB | 20x 느림 |
| Analysis | N/A | N/A | CPU 전용 |

---

**총 API 수**: 18개
**총 파라미터 수**: 50+개
**마지막 업데이트**: 2025-12-28
