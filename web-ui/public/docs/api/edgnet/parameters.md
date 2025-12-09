# EDGNet API

> **Graph Neural Network 기반 도면 세그멘테이션**

---

## 기본 정보

| 항목 | 값 |
|------|-----|
| **포트** | 5012 |
| **엔드포인트** | `POST /api/v1/segment` |
| **GPU 필수** | ✅ (CPU 5배 느림) |
| **VRAM** | 3-6GB |

---

## 파라미터

### model (세그멘테이션 모델)

| 값 | 설명 | VRAM | 속도 |
|----|------|------|------|
| `unet` | U-Net 기반 (기본) | ~3GB | 빠름 |
| `graphsage` | GraphSAGE 기반 | ~6GB | 정확 |

- **타입**: select
- **기본값**: `unet`

### num_classes (분류 클래스 수)

도면 요소를 분류할 클래스 수입니다.

- **타입**: number (2 ~ 20)
- **기본값**: `8`
- **팁**: 기본 8클래스 권장 (Contour, Text, Dimension, Symbol, Leader, Table, Title, Background)

### visualize (시각화)

세그멘테이션 결과를 컬러로 시각화합니다.

- **타입**: boolean
- **기본값**: `true`

### save_graph (그래프 저장)

그래프 구조를 JSON으로 저장합니다 (디버깅용).

- **타입**: boolean
- **기본값**: `false`

### vectorize (벡터화)

도면을 벡터 형식(DXF)으로 출력합니다.

- **타입**: boolean
- **기본값**: `false`

---

## 출력

| 필드 | 타입 | 설명 |
|------|------|------|
| `components` | array | 분류된 컴포넌트 목록 |
| `total_components` | number | 총 컴포넌트 수 |
| `visualized_image` | string | 시각화 이미지 (base64) |

### component 객체 구조

```json
{
  "id": "C001",
  "class": "dimension",
  "confidence": 0.94,
  "bbox": [100, 200, 300, 250],
  "mask": "base64_encoded_mask",
  "area": 15000
}
```

---

## 분류 클래스 (8종)

| 클래스 | 설명 | 색상 |
|--------|------|------|
| `contour` | 도면 윤곽선 | 파랑 |
| `text` | 일반 텍스트 | 초록 |
| `dimension` | 치수선 | 빨강 |
| `symbol` | 기호/심볼 | 노랑 |
| `leader` | 지시선 | 주황 |
| `table` | 테이블/표 | 보라 |
| `title` | 타이틀 블록 | 청록 |
| `background` | 배경 | 투명 |

---

## 사용 예시

### curl
```bash
curl -X POST http://localhost:5012/api/v1/segment \
  -F "file=@drawing.jpg" \
  -F "model=unet" \
  -F "num_classes=8" \
  -F "visualize=true"
```

### Python
```python
import requests

files = {"file": open("drawing.jpg", "rb")}
data = {
    "model": "unet",
    "num_classes": 8,
    "visualize": True,
    "save_graph": False,
    "vectorize": False
}

response = requests.post(
    "http://localhost:5012/api/v1/segment",
    files=files,
    data=data
)
print(response.json())
```

---

## 모델 비교

| 항목 | UNet | GraphSAGE |
|------|------|-----------|
| **속도** | 빠름 | 느림 |
| **정확도** | 보통 | 높음 |
| **VRAM** | 3GB | 6GB |
| **강점** | 일반 도면 | 복잡한 도면 |

---

## 권장 파이프라인

### 도면 구조 분석
```
ImageInput → EDGNet
```

### 전처리 후 분석
```
ImageInput → ESRGAN(2x) → EDGNet
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
| model | graphsage → VRAM 2배 |
| num_classes | 클래스 수 ↑ → 메모리 ↑ |

---

**마지막 업데이트**: 2025-12-09
