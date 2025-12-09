# YOLO Detection API

> **YOLOv11 기반 기계 도면 심볼 검출**

---

## 기본 정보

| 항목 | 값 |
|------|-----|
| **포트** | 5005 |
| **엔드포인트** | `POST /api/v1/detect` |
| **GPU 필수** | ✅ (CPU 10배 느림) |
| **VRAM** | 2-4GB |

---

## 파라미터

### model_type (모델 선택)

| 값 | 용도 | 검출 대상 |
|----|------|----------|
| `symbol-detector-v1` | 기계 심볼 | 용접, 베어링, 기어 등 |
| `dimension-detector-v1` | 치수 영역 | 치수선, 공차 표기 |
| `gdt-detector-v1` | GD&T | 기하공차 기호 |
| `text-region-detector-v1` | 텍스트 | 텍스트 블록 영역 |
| `yolo11n-general` | 범용 | 테스트용 |

- **타입**: select
- **기본값**: `symbol-detector-v1`

### confidence (신뢰도 임계값)

검출 결과를 필터링하는 신뢰도 기준입니다.

- **타입**: number (0.0 ~ 1.0)
- **기본값**: `0.5`
- **팁**: 작은 심볼이 많으면 `0.3`으로 낮추세요

### iou (NMS IoU 임계값)

중복 검출을 제거하는 기준입니다.

- **타입**: number (0.0 ~ 1.0)
- **기본값**: `0.45`
- **팁**: 중복이 많으면 `0.6`으로 올리세요

### imgsz (이미지 크기)

모델 입력 이미지 크기입니다.

- **타입**: number (320 ~ 1920)
- **기본값**: `1280`
- **옵션**: 640, 1280, 1920
- **팁**: 복잡한 도면은 `1920` 권장

| 크기 | VRAM | 처리 시간 |
|------|------|----------|
| 640 | 1.5GB | 빠름 |
| 1280 | 2.5GB | 보통 |
| 1920 | 4GB | 느림 (정확) |

### visualize (시각화)

결과 이미지에 바운딩 박스를 그릴지 여부입니다.

- **타입**: boolean
- **기본값**: `true`

### task (작업 유형)

| 값 | 설명 | VRAM |
|----|------|------|
| `detect` | 객체 검출 | 2GB |
| `segment` | 인스턴스 세그멘테이션 | 3GB |

- **타입**: select
- **기본값**: `detect`

---

## 출력

| 필드 | 타입 | 설명 |
|------|------|------|
| `detections` | array | 검출 결과 목록 |
| `total_detections` | number | 총 검출 개수 |
| `visualized_image` | base64 | 시각화 이미지 |
| `processing_time` | number | 처리 시간 (초) |

### detection 객체 구조

```json
{
  "class_name": "welding_symbol",
  "confidence": 0.92,
  "bbox": [100, 200, 150, 250],
  "extracted_text": "V"
}
```

---

## 검출 가능 심볼 (14종)

### 치수 (Dimensions)
- `diameter_dim` - 직경 치수 (⌀)
- `linear_dim` - 선형 치수
- `radius_dim` - 반경 치수 (R)
- `angular_dim` - 각도 치수 (°)
- `chamfer_dim` - 모따기 치수 (C)
- `tolerance_dim` - 공차 치수 (±)
- `reference_dim` - 참조 치수 (())

### GD&T
- `flatness` - 평면도 (⏥)
- `cylindricity` - 원통도 (⌭)
- `position` - 위치도 (⊕)
- `perpendicularity` - 수직도 (⊥)
- `parallelism` - 평행도 (∥)

### 기타
- `surface_roughness` - 표면 조도 (Ra)
- `text_block` - 텍스트 블록

---

## 사용 예시

### curl
```bash
curl -X POST http://localhost:5005/api/v1/detect \
  -F "file=@drawing.jpg" \
  -F "model_type=symbol-detector-v1" \
  -F "confidence=0.5" \
  -F "imgsz=1280"
```

### Python
```python
import requests

files = {"file": open("drawing.jpg", "rb")}
data = {
    "model_type": "symbol-detector-v1",
    "confidence": 0.5,
    "imgsz": 1280
}

response = requests.post(
    "http://localhost:5005/api/v1/detect",
    files=files,
    data=data
)
print(response.json())
```

---

## 리소스 요구사항

| 항목 | 최소 | 권장 |
|------|------|------|
| VRAM | 1.5GB | 4GB |
| RAM | 2GB | 3GB |
| CPU 코어 | 4 | 8 |
| CUDA | 11.8+ | 12.x |

---

**마지막 업데이트**: 2025-12-09
