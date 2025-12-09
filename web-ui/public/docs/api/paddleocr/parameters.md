# PaddleOCR API

> **PaddlePaddle 기반 다국어 범용 OCR**

---

## 기본 정보

| 항목 | 값 |
|------|-----|
| **포트** | 5006 |
| **엔드포인트** | `POST /api/v1/ocr` |
| **GPU 권장** | ✅ (CPU 5배 느림) |
| **VRAM** | ~2GB |

---

## 파라미터

### lang (인식 언어)

| 값 | 설명 |
|----|------|
| `en` | 영어 (기본) |
| `korean` | 한국어 |
| `ch` | 중국어 |
| `japan` | 일본어 |

- **타입**: select
- **기본값**: `en`
- **팁**: 한글 도면은 `korean` 사용

### det_db_thresh (검출 임계값)

텍스트 검출 신뢰도 임계값입니다.

- **타입**: number (0.0 ~ 1.0)
- **기본값**: `0.3`
- **팁**: 낮추면 더 많은 텍스트 검출

### det_db_box_thresh (박스 임계값)

바운딩 박스 생성 임계값입니다.

- **타입**: number (0.0 ~ 1.0)
- **기본값**: `0.5`

### use_angle_cls (회전 감지)

회전된 텍스트를 감지하고 정렬합니다.

- **타입**: boolean
- **기본값**: `true`
- **주의**: 처리 시간 50% 증가

### min_confidence (최소 신뢰도)

결과 필터링을 위한 최소 신뢰도입니다.

- **타입**: number (0.0 ~ 1.0)
- **기본값**: `0.5`

### visualize (시각화)

결과 이미지에 텍스트 영역을 표시합니다.

- **타입**: boolean
- **기본값**: `false`

---

## 출력

| 필드 | 타입 | 설명 |
|------|------|------|
| `detections` | array | 검출된 텍스트 목록 |
| `total_texts` | number | 총 검출 텍스트 수 |
| `visualized_image` | string | 시각화 이미지 (base64) |

### detection 객체 구조

```json
{
  "text": "도면 번호: DWG-001",
  "confidence": 0.94,
  "bbox": [[100, 50], [300, 50], [300, 80], [100, 80]]
}
```

---

## 사용 예시

### curl
```bash
curl -X POST http://localhost:5006/api/v1/ocr \
  -F "file=@drawing.jpg" \
  -F "lang=korean" \
  -F "det_db_thresh=0.3"
```

### Python
```python
import requests

files = {"file": open("drawing.jpg", "rb")}
data = {
    "lang": "korean",
    "det_db_thresh": 0.3,
    "det_db_box_thresh": 0.5,
    "use_angle_cls": True,
    "min_confidence": 0.5,
    "visualize": True
}

response = requests.post(
    "http://localhost:5006/api/v1/ocr",
    files=files,
    data=data
)
print(response.json())
```

---

## 특징

### 장점
- 80+ 언어 지원
- 한국어 인식 우수
- PP-OCRv3 최신 모델
- 빠른 처리 속도

### 단점
- GD&T 특수 기호에 약함
- 복잡한 레이아웃 처리 제한

---

## 권장 파이프라인

### 다국어 텍스트 추출
```
ImageInput → PaddleOCR
```

### OCR 앙상블 참여
```
ImageInput → OCR Ensemble (PaddleOCR 35% 가중치)
```

---

## 리소스 요구사항

| 항목 | 최소 | 권장 |
|------|------|------|
| VRAM | 1.5GB | 2GB |
| RAM | 2GB | 3GB |
| CPU 코어 | 4 | 8 |
| CUDA | 11.8+ | 12.x |

### 파라미터별 리소스 영향

| 파라미터 | 영향 |
|----------|------|
| use_angle_cls | 처리 시간 1.5배 증가 |

---

**마지막 업데이트**: 2025-12-09
