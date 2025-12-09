# TrOCR API

> **Microsoft Transformer 기반 OCR - 손글씨 및 장면 텍스트 특화**

---

## 기본 정보

| 항목 | 값 |
|------|-----|
| **포트** | 5009 |
| **엔드포인트** | `POST /api/v1/ocr` |
| **GPU 권장** | ✅ (CPU 10배 느림) |
| **VRAM** | 2-6GB |

---

## 파라미터

### model_type (모델 선택)

| 값 | 용도 | VRAM |
|----|------|------|
| `printed` | 인쇄체 (기본) | ~3GB |
| `handwritten` | 손글씨 | ~3GB |
| `large-printed` | 대형 인쇄체 | ~6GB |
| `large-handwritten` | 대형 손글씨 | ~6GB |

- **타입**: select
- **기본값**: `printed`
- **팁**: 정확도가 중요하면 `large-*` 사용

### max_length (최대 출력 길이)

디코딩 시 생성할 최대 토큰 수입니다.

- **타입**: number (16 ~ 256)
- **기본값**: `64`
- **팁**: 긴 텍스트 라인은 128 이상 권장

### num_beams (빔 서치 빔 수)

Beam Search 알고리즘의 빔 수입니다.

- **타입**: number (1 ~ 10)
- **기본값**: `4`
- **팁**: 높을수록 정확하지만 느림

---

## 출력

| 필드 | 타입 | 설명 |
|------|------|------|
| `texts` | array | 인식된 텍스트 목록 |
| `full_text` | string | 전체 텍스트 |

### text 객체 구조

```json
{
  "text": "Hand-written note",
  "confidence": 0.92,
  "model": "handwritten"
}
```

---

## 사용 예시

### curl
```bash
curl -X POST http://localhost:5009/api/v1/ocr \
  -F "file=@handwriting.jpg" \
  -F "model_type=handwritten" \
  -F "num_beams=5"
```

### Python
```python
import requests

files = {"file": open("handwriting.jpg", "rb")}
data = {
    "model_type": "handwritten",
    "max_length": 128,
    "num_beams": 4
}

response = requests.post(
    "http://localhost:5009/api/v1/ocr",
    files=files,
    data=data
)
print(response.json())
```

---

## 특징

### 강점
- 손글씨 인식 정확도 우수
- Transformer 기반 문맥 이해
- 장면 텍스트 (간판, 표지판) 강함

### 약점
- 단일 텍스트 라인에 최적화
- 전체 페이지 처리에 부적합
- GPU 없이 매우 느림

---

## 권장 파이프라인

### 손글씨 인식
```
ImageInput → YOLO (text-region) → TrOCR (handwritten)
```

### OCR 앙상블 참여
```
ImageInput → OCR Ensemble (TrOCR 10% 가중치)
```

### 최적 워크플로우
```
YOLO로 텍스트 영역 검출 → 각 영역을 TrOCR로 개별 처리
```

---

## 리소스 요구사항

| 항목 | 최소 | 권장 |
|------|------|------|
| VRAM | 2.5GB | 6GB |
| RAM | 4GB | 6GB |
| CPU 코어 | 4 | 8 |
| CUDA | 11.8+ | 12.x |

### 파라미터별 리소스 영향

| 파라미터 | 영향 |
|----------|------|
| model_type | large 모델 → VRAM 2배 |
| num_beams | 빔 수 ↑ → 메모리/시간 증가 |

---

**마지막 업데이트**: 2025-12-09
