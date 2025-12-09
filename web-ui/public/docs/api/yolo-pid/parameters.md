# YOLO-PID API

> **P&ID 도면 심볼 검출 (밸브, 펌프, 계기 등 50+ 클래스)**

---

## 기본 정보

| 항목 | 값 |
|------|-----|
| **포트** | 5017 |
| **엔드포인트** | `POST /api/v1/process` |
| **GPU 필수** | ✅ (CPU 8배 느림) |
| **VRAM** | 1-4GB |

---

## 파라미터

### confidence (신뢰도 임계값)

검출 결과를 필터링하는 신뢰도 기준입니다.

- **타입**: number (0.1 ~ 1.0)
- **기본값**: `0.25`
- **팁**: P&ID 심볼은 작아서 낮은 값 권장

### iou (NMS IoU 임계값)

중복 검출을 제거하는 기준입니다.

- **타입**: number (0.1 ~ 1.0)
- **기본값**: `0.45`

### imgsz (이미지 크기)

모델 입력 이미지 크기입니다.

| 크기 | VRAM | 처리 시간 | 정확도 |
|------|------|----------|--------|
| 320 | ~1GB | 빠름 | 낮음 |
| 640 | ~2GB | 보통 | 보통 |
| 1280 | ~4GB | 느림 | 높음 |

- **타입**: select
- **기본값**: `640`
- **팁**: 복잡한 P&ID는 `1280` 권장

### visualize (시각화)

결과 이미지에 바운딩 박스를 그릴지 여부입니다.

- **타입**: boolean
- **기본값**: `true`

---

## 출력

| 필드 | 타입 | 설명 |
|------|------|------|
| `detections` | array | 검출된 P&ID 심볼 목록 |
| `statistics` | object | 카테고리별 통계 |
| `visualization` | string | 시각화 이미지 (base64) |

### detection 객체 구조

```json
{
  "class_name": "gate_valve",
  "class_id": 12,
  "confidence": 0.87,
  "bbox": [100, 200, 150, 250],
  "category": "valve"
}
```

---

## 검출 가능 심볼 (50+ 클래스)

### 밸브 (Valves)
| 클래스 | 설명 |
|--------|------|
| `gate_valve` | 게이트 밸브 |
| `globe_valve` | 글로브 밸브 |
| `ball_valve` | 볼 밸브 |
| `butterfly_valve` | 버터플라이 밸브 |
| `check_valve` | 체크 밸브 |
| `control_valve` | 컨트롤 밸브 |
| `relief_valve` | 릴리프 밸브 |
| `solenoid_valve` | 솔레노이드 밸브 |

### 펌프 (Pumps)
| 클래스 | 설명 |
|--------|------|
| `centrifugal_pump` | 원심 펌프 |
| `positive_displacement_pump` | 용적형 펌프 |
| `vacuum_pump` | 진공 펌프 |

### 계기 (Instruments)
| 클래스 | 설명 |
|--------|------|
| `pressure_indicator` | 압력계 (PI) |
| `temperature_indicator` | 온도계 (TI) |
| `flow_indicator` | 유량계 (FI) |
| `level_indicator` | 레벨계 (LI) |
| `pressure_transmitter` | 압력 트랜스미터 (PT) |
| `temperature_transmitter` | 온도 트랜스미터 (TT) |

### 장비 (Equipment)
| 클래스 | 설명 |
|--------|------|
| `vessel` | 용기 |
| `tank` | 탱크 |
| `heat_exchanger` | 열교환기 |
| `filter` | 필터 |
| `compressor` | 압축기 |

### 기타
| 클래스 | 설명 |
|--------|------|
| `reducer` | 리듀서 |
| `tee` | 티 |
| `elbow` | 엘보 |
| `flange` | 플랜지 |

---

## 사용 예시

### curl
```bash
curl -X POST http://localhost:5017/api/v1/process \
  -F "file=@pid_drawing.jpg" \
  -F "confidence=0.25" \
  -F "imgsz=640"
```

### Python
```python
import requests

files = {"file": open("pid_drawing.jpg", "rb")}
data = {
    "confidence": 0.25,
    "iou": 0.45,
    "imgsz": 640,
    "visualize": True
}

response = requests.post(
    "http://localhost:5017/api/v1/process",
    files=files,
    data=data
)
print(response.json())
```

---

## 권장 파이프라인

### P&ID 전체 분석
```
ImageInput → YOLO-PID → Line Detector → PID Analyzer → Design Checker
```

### 심볼만 검출
```
ImageInput → YOLO-PID
```

---

## 리소스 요구사항

| 항목 | 최소 | 권장 |
|------|------|------|
| VRAM | 2GB | 4GB |
| RAM | 3GB | 4GB |
| CPU 코어 | 4 | 8 |
| CUDA | 11.8+ | 12.x |

### 파라미터별 리소스 영향

| 파라미터 | 영향 |
|----------|------|
| imgsz | 320→1GB, 640→2GB, 1280→4GB |

---

**마지막 업데이트**: 2025-12-09
