# Line Detector API

> **P&ID 라인(배관/신호선) 검출 및 연결성 분석**

---

## 기본 정보

| 항목 | 값 |
|------|-----|
| **포트** | 5016 |
| **엔드포인트** | `POST /api/v1/process` |
| **GPU 필요** | ❌ CPU 전용 (OpenCV) |
| **RAM** | ~2GB |

---

## 파라미터

### method (검출 방식)

| 값 | 설명 | 속도 | 정확도 |
|----|------|------|--------|
| `lsd` | Line Segment Detector (기본) | 빠름 | 높음 |
| `hough` | Hough Transform | 빠름 | 보통 |
| `combined` | LSD + Hough 결합 | 느림 | 최고 |

- **타입**: select
- **기본값**: `lsd`

### merge_lines (공선 라인 병합)

같은 직선 상의 분리된 라인 세그먼트를 병합합니다.

- **타입**: boolean
- **기본값**: `true`
- **팁**: 끊어진 라인을 연결하려면 활성화

### classify_types (라인 유형 분류)

배관/신호선/전기선 등 라인 유형을 자동 분류합니다.

- **타입**: boolean
- **기본값**: `true`

### find_intersections (교차점 검출)

라인 간 교차점을 검출합니다.

- **타입**: boolean
- **기본값**: `true`
- **팁**: PID Analyzer 입력에 필요

### visualize (시각화)

결과 이미지에 라인을 표시합니다.

- **타입**: boolean
- **기본값**: `true`

---

## 출력

| 필드 | 타입 | 설명 |
|------|------|------|
| `lines` | array | 검출된 라인 목록 |
| `intersections` | array | 교차점 목록 |
| `statistics` | object | 라인 통계 |
| `visualization` | string | 시각화 이미지 (base64) |

### line 객체 구조

```json
{
  "id": "L001",
  "start": [100, 200],
  "end": [300, 200],
  "type": "process_line",
  "length": 200,
  "angle": 0
}
```

### intersection 객체 구조

```json
{
  "id": "I001",
  "point": [200, 200],
  "lines": ["L001", "L002"],
  "type": "cross"
}
```

### 라인 유형

| type | 설명 |
|------|------|
| `process_line` | 프로세스 배관 (굵은 실선) |
| `signal_line` | 신호선 (점선) |
| `electric_line` | 전기선 |
| `pneumatic_line` | 공압선 |

---

## 사용 예시

### curl
```bash
curl -X POST http://localhost:5016/api/v1/process \
  -F "file=@pid_drawing.jpg" \
  -F "method=lsd" \
  -F "merge_lines=true" \
  -F "find_intersections=true"
```

### Python
```python
import requests

files = {"file": open("pid_drawing.jpg", "rb")}
data = {
    "method": "lsd",
    "merge_lines": True,
    "classify_types": True,
    "find_intersections": True,
    "visualize": True
}

response = requests.post(
    "http://localhost:5016/api/v1/process",
    files=files,
    data=data
)
print(response.json())
```

---

## 검출 방식 비교

| 방식 | 장점 | 단점 |
|------|------|------|
| LSD | 정확, 빠름 | 곡선 미지원 |
| Hough | 노이즈에 강함 | 파라미터 민감 |
| Combined | 최고 정확도 | 2배 처리 시간 |

---

## 권장 파이프라인

### P&ID 전체 분석
```
ImageInput → YOLO-PID → Line Detector → PID Analyzer → Design Checker
```

### 라인만 검출
```
ImageInput → Line Detector
```

---

## 리소스 요구사항

| 항목 | 최소 | 권장 |
|------|------|------|
| RAM | 1GB | 2GB |
| CPU 코어 | 2 | 4 |

### 파라미터별 리소스 영향

| 파라미터 | 영향 |
|----------|------|
| method | combined → 처리 시간 2배 |
| find_intersections | 추가 계산 필요 |

---

**마지막 업데이트**: 2025-12-09
