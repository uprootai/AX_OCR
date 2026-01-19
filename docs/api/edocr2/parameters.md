# eDOCr2 API

> 기계 도면 특화 OCR - 치수, GD&T, 텍스트 추출
> **포트**: 5002 | **카테고리**: OCR | **GPU**: 권장 (GTX 1060+)

---

## 개요

기계 도면에서 치수, GD&T 기호, 텍스트를 자동 추출합니다. 한국어+영어 혼합 도면을 지원하며, YOLO와 함께 사용하면 정확도가 향상됩니다.

---

## 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/v1/ocr` | 이미지에서 OCR 수행 |
| GET | `/api/v2/health` | 헬스체크 |

---

## 파라미터

### 기본 파라미터

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `language` | select | ko+en | OCR 언어 |

**language 옵션:**
- `ko`: 한국어
- `en`: 영어
- `ko+en`: 한국어+영어 (권장)
- `ja`: 일본어
- `zh`: 중국어

### 추출 옵션

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `extract_dimensions` | boolean | true | 치수 정보 추출 (φ476, 10±0.5, R20 등) |
| `extract_gdt` | boolean | true | GD&T 기호 추출 (평행도, 직각도, 위치도 등) |
| `extract_text` | boolean | true | 일반 텍스트 추출 (도면 번호, 재질, 주석 등) |
| `extract_tables` | boolean | false | 테이블 추출 (BOM 등) |

### 고급 파라미터

| 파라미터 | 타입 | 기본값 | 범위 | 설명 |
|---------|------|--------|------|------|
| `cluster_threshold` | number | 50 | 10-200 | 텍스트 클러스터링 임계값 |
| `visualize` | boolean | true | - | 결과 시각화 이미지 생성 |

---

## 프로파일

미리 정의된 설정으로 빠르게 사용할 수 있습니다.

| 프로파일 | 설명 | 설정 |
|---------|------|------|
| `full` | 전체 추출 | dimensions + gdt + text |
| `dimension_only` | 치수만 | dimensions만 활성화 |
| `gdt_only` | GD&T만 | gdt만 활성화 |
| `text_only` | 텍스트만 | text만 활성화 |
| `accurate` | 정확도 우선 | 모든 기능 + VL 모델 |
| `fast` | 속도 우선 | dimensions만, 시각화 없음 |
| `debug` | 디버그 | 모든 기능 + 시각화 |

---

## 응답

```json
{
  "status": "success",
  "data": {
    "dimensions": [
      {
        "value": "50.0",
        "tolerance": "±0.1",
        "unit": "mm",
        "bbox": [100, 200, 200, 230],
        "type": "linear"
      },
      {
        "value": "Ø25",
        "tolerance": "H7",
        "unit": "mm",
        "bbox": [300, 150, 380, 180],
        "type": "diameter"
      }
    ],
    "gdt_symbols": [
      {
        "symbol": "⌖",
        "type": "position",
        "tolerance": "0.05",
        "datum": ["A", "B"],
        "bbox": [400, 300, 500, 350]
      }
    ],
    "text_blocks": [
      {
        "text": "PART NAME",
        "bbox": [50, 50, 200, 80],
        "confidence": 0.95
      }
    ],
    "tables": [],
    "drawing_number": "DWG-001",
    "material": "SUS304",
    "visualized_image": "data:image/jpeg;base64,..."
  },
  "processing_time": 2.45
}
```

---

## 사용 예시

```bash
# 기본 치수 추출
curl -X POST http://localhost:5002/api/v1/ocr \
  -F "file=@drawing.png" \
  -F "language=ko+en" \
  -F "extract_dimensions=true" \
  -F "extract_gdt=true"

# 테이블 포함 (BOM 도면)
curl -X POST http://localhost:5002/api/v1/ocr \
  -F "file=@bom_drawing.png" \
  -F "extract_tables=true"
```

---

## 리소스 요구사항

| 환경 | VRAM/RAM | 처리 속도 |
|------|----------|----------|
| GPU (권장) | ~2GB VRAM | 2-3초 |
| CPU | ~4GB RAM | 6-9초 |

**참고:** `extract_tables=true` 사용 시 메모리 2배 증가

---

## 권장 워크플로우

```
YOLO (영역 검출) → eDOCr2 (OCR) → SkinModel (공차 분석)
```

YOLO로 치수 영역을 먼저 검출한 후 eDOCr2로 OCR하면 정확도가 향상됩니다.

---

**최종 수정**: 2026-01-17
