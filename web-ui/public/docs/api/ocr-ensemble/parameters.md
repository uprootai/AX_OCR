# OCR Ensemble API

> **4개 OCR 엔진 가중 투표 앙상블**

---

## 기본 정보

| 항목 | 값 |
|------|-----|
| **포트** | 5011 |
| **엔드포인트** | `POST /api/v1/ocr` |
| **GPU 권장** | ✅ |
| **VRAM** | 4GB (4엔진 병렬) |

---

## 앙상블 구성

| 엔진 | 기본 가중치 | 특화 분야 |
|------|------------|----------|
| **eDOCr2** | 40% | 기계 도면 치수 |
| **PaddleOCR** | 35% | 다국어 범용 |
| **Tesseract** | 15% | 문서 텍스트 |
| **TrOCR** | 10% | 손글씨 |

---

## 파라미터

### engines (사용 엔진)

활성화할 OCR 엔진을 선택합니다.

- **타입**: array
- **기본값**: `["edocr2", "paddleocr", "tesseract", "trocr"]`
- **옵션**: edocr2, paddleocr, tesseract, trocr

### weights (엔진 가중치)

각 엔진의 투표 가중치입니다.

- **타입**: object
- **기본값**:
```json
{
  "edocr2": 0.40,
  "paddleocr": 0.35,
  "tesseract": 0.15,
  "trocr": 0.10
}
```

### voting_strategy (투표 전략)

| 값 | 설명 |
|----|------|
| `weighted` | 가중 투표 (기본) |
| `majority` | 다수결 |
| `confidence` | 신뢰도 기반 |

- **타입**: select
- **기본값**: `weighted`

### confidence_threshold (신뢰도 임계값)

최종 결과 필터링 신뢰도입니다.

- **타입**: number (0.0 ~ 1.0)
- **기본값**: `0.7`

### language (언어)

- **타입**: select
- **기본값**: `ko+en`
- **옵션**: ko, en, ko+en, ja, zh

### merge_duplicates (중복 병합)

유사 위치의 검출 결과를 병합합니다.

- **타입**: boolean
- **기본값**: `true`

### iou_threshold (중복 판단 IoU)

중복 병합 시 IoU 임계값입니다.

- **타입**: number (0.0 ~ 1.0)
- **기본값**: `0.5`

---

## 출력

| 필드 | 타입 | 설명 |
|------|------|------|
| `dimensions` | array | 앙상블 치수 결과 |
| `gdt` | array | GD&T 기호 |
| `text` | array | 텍스트 블록 |
| `engine_results` | object | 각 엔진별 원본 결과 |
| `voting_details` | array | 투표 상세 정보 |

### dimension 객체 (앙상블)

```json
{
  "value": "85.5",
  "unit": "mm",
  "confidence": 0.92,
  "votes": {
    "edocr2": { "value": "85.5", "confidence": 0.95 },
    "paddleocr": { "value": "85.5", "confidence": 0.90 },
    "tesseract": { "value": "855", "confidence": 0.60 },
    "trocr": { "value": "85.5", "confidence": 0.88 }
  },
  "agreement": 0.75
}
```

---

## 사용 예시

### curl
```bash
curl -X POST http://localhost:5011/api/v1/ocr \
  -F "file=@drawing.jpg" \
  -F 'engines=["edocr2","paddleocr","tesseract"]' \
  -F "confidence_threshold=0.7"
```

### Python
```python
import requests

files = {"file": open("drawing.jpg", "rb")}
data = {
    "engines": ["edocr2", "paddleocr", "tesseract", "trocr"],
    "voting_strategy": "weighted",
    "confidence_threshold": 0.7
}

response = requests.post(
    "http://localhost:5011/api/v1/ocr",
    files=files,
    data=data
)
print(response.json())
```

---

## 성능 비교

### 단일 엔진 vs 앙상블

| 방식 | 정확도 | 처리 시간 |
|------|--------|----------|
| eDOCr2 단독 | 85% | 10초 |
| PaddleOCR 단독 | 80% | 8초 |
| **앙상블 (4엔진)** | **92%** | 40초 |

---

## 권장 파이프라인

### 고정밀 OCR
```
ImageInput → ESRGAN(2x) → OCR Ensemble → 후처리
```

### 빠른 분석
```
ImageInput → eDOCr2 (단일)
```

---

## 리소스 요구사항

| 항목 | 최소 | 권장 |
|------|------|------|
| VRAM | 2GB | 4GB |
| RAM | 4GB | 8GB |
| 처리 시간 | 30초 | 60초 |

---

**마지막 업데이트**: 2025-12-09
