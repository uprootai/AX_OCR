---
sidebar_position: 11
title: "Line Detector API"
description: "P&ID 도면의 배관/신호선 검출 및 연결성 분석 API의 파라미터와 출력 구조를 정리한다."
tags: [API, 마이크로서비스, 라인검출]
---

# Line Detector API (라인 검출)

> P&ID 라인(배관/신호선) 검출 및 연결성 분석 (포트 5016, CPU 전용).

---

## 기본 정보

| 항목 | 값 |
|------|-----|
| **포트** | 5016 |
| **주요 엔드포인트** | `POST /api/v1/process` |
| **보조 엔드포인트** | `GET /health`, `GET /api/v1/health`, `GET /api/v1/info`, `GET /api/v1/profiles` |
| **GPU 필요** | ❌ CPU 전용 (OpenCV) |
| **RAM** | ~2GB |
| **기본 프로파일** | `pid` |

---

## 엔드포인트

| Method | Endpoint | 설명 |
|------|------|------|
| `GET` | `/health` | 헬스 체크 |
| `GET` | `/api/v1/health` | 헬스 체크 v1 경로 |
| `GET` | `/api/v1/info` | 서비스 메타데이터, 파라미터 정의, 스타일/영역 타입 |
| `GET` | `/api/v1/profiles` | 프로파일 기본값 (`pid`, `simple`, `region_focus`, `connectivity`) |
| `POST` | `/api/v1/process` | 라인 검출 및 선택 기능 실행 |

---

## 요청 파라미터

### 주요 파라미터

| 파라미터 | 타입 | 기본값 | 설명 |
|------|------|------|------|
| `profile` | string | `pid` | 프로파일 기본값 선택. 이후 개별 파라미터가 우선 적용됨 |
| `method` | string | `lsd` | `lsd`, `hough`, `combined` 중 선택 |
| `merge_lines` | boolean | `true` | 공선 세그먼트 병합 |
| `classify_types` | boolean | `true` | 라인 용도 분류 |
| `classify_colors` | boolean | `true` | 색상 분류 |
| `classify_styles` | boolean | `true` | 스타일 분류 |
| `find_intersections` | boolean | `true` | 교차점 계산 |
| `detect_regions` | boolean | `false` | 점선 박스 영역 검출 |
| `region_line_styles` | string | `dashed,dash_dot` | 영역 검출에 사용할 스타일 목록 |
| `min_region_area` | integer | `5000` | 영역 최소 면적 |
| `visualize` | boolean | `true` | PNG 시각화 base64 생성 |
| `visualize_regions` | boolean | `true` | 영역 시각화를 visualization에 포함 |
| `include_svg` | boolean | `false` | SVG 오버레이 구조를 `svg_overlay`로 포함 |
| `min_length` | number | `0` | 최소 라인 길이. `0`이면 필터 없음 |
| `max_lines` | integer | `0` | 반환 라인 수 상한. `0`이면 제한 없음 |

### 프로파일 기본값

| 프로파일 | 목적 | 핵심 기본값 |
|------|------|------|
| `pid` | P&ID 일반 분석 | 분류/교차점/영역 검출 활성화 |
| `simple` | 선만 빠르게 검출 | 분류/교차점/영역 검출 비활성화 |
| `region_focus` | 점선 박스 중심 | `classify_styles=true`, `detect_regions=true` |
| `connectivity` | 연결성 분석 | `find_intersections=true`, `classify_colors=false` |

### 내부 알고리즘 파라미터

현재 API가 외부에 노출하는 튜닝 파라미터는 위 표가 전부다. `detect_lines_lsd()`는 `cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD)`를 사용하며, `scale`, `sigma_scale`, `ang_th` 같은 OpenCV LSD 세부값은 코드에서 별도 override 하지 않는다. `merge_collinear_lines()`는 내부적으로 `angle_threshold=5.0`, `distance_threshold=20.0`을 사용한다.

---

## 응답 구조

상위 응답은 항상 아래 형태다.

```json
{
  "success": true,
  "data": {},
  "processing_time": 1.234,
  "error": null
}
```

### `data` 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| `lines` | array | 검출된 라인 목록 |
| `intersections` | array | 교차점 목록 |
| `regions` | array | 검출된 점선 박스 영역 |
| `svg_overlay` | object | `include_svg=true`일 때 포함되는 SVG 구조 |
| `statistics` | object | 라인/색상/스타일/영역 통계 |
| `visualization` | string | base64 PNG |
| `method` | string | 실제 사용된 검출 방식 |
| `image_size` | object | `{width, height}` |
| `options_used` | object | 실제 적용된 옵션 값 |

### line 객체 예시

```json
{
  "id": 0,
  "start_point": [100.0, 200.0],
  "end_point": [300.0, 200.0],
  "waypoints": [[100.0, 200.0], [300.0, 200.0]],
  "length": 200.0,
  "angle": 0.0,
  "line_type": "pipe",
  "line_style": "solid",
  "color": "black",
  "color_type": "process",
  "confidence": 0.85
}
```

### intersection 객체 예시

```json
{
  "id": 0,
  "point": [200.0, 200.0],
  "line_ids": [0, 1],
  "type": "cross"
}
```

### region 객체 예시

```json
{
  "id": 0,
  "bbox": [50, 100, 400, 350],
  "area": 87500,
  "region_type": "signal_group",
  "region_type_korean": "신호 그룹"
}
```

### 스타일/영역 타입

| 분류 | 값 | 설명 |
|------|------|------|
| line style | `solid`, `dashed`, `dotted`, `dash_dot`, `double`, `wavy`, `unknown` | 스타일 분류 결과 |
| region type | `signal_group`, `equipment_boundary`, `note_box`, `hazardous_area`, `scope_boundary`, `detail_area`, `unknown` | 점선 박스 영역 분류 결과 |

---

## 사용 예시

### curl
```bash
curl -X POST http://localhost:5016/api/v1/process \
  -F "file=@pid_drawing.png" \
  -F "profile=simple" \
  -F "method=lsd" \
  -F "merge_lines=true" \
  -F "find_intersections=false" \
  -F "classify_colors=false" \
  -F "classify_styles=false" \
  -F "min_length=15" \
  -F "max_lines=5000"
```

### Python
```python
import requests

files = {"file": open("pid_drawing.png", "rb")}
data = {
    "profile": "simple",
    "method": "lsd",
    "merge_lines": "true",
    "classify_types": "false",
    "classify_colors": "false",
    "classify_styles": "false",
    "find_intersections": "false",
    "visualize": "false",
    "include_svg": "true",
    "min_length": "15",
    "max_lines": "5000",
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
| `lsd` | 직선 세그먼트 정밀도 높음 | 곡선에는 약함 |
| `hough` | 노이즈에 상대적으로 강함 | 짧은 세그먼트 정밀도 낮을 수 있음 |
| `combined` | 누락 보완에 유리 | 결과 수와 처리 시간 증가 |

---

## 권장 파이프라인

### P&ID 전체 분석
```
ImageInput → YOLO (model_type=pid_class_aware) → Line Detector → PID Analyzer → Design Checker
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
| `method=combined` | LSD + Hough를 모두 실행하므로 처리 시간 증가 |
| `find_intersections=true` | 교차점 계산 추가 |
| `detect_regions=true` | 스타일 분류와 영역 탐색 추가 |
| `max_lines` 작게 설정 | 후속 처리량 감소 |

---

## 관련 문서

- [PID Analyzer API](/docs/api-reference/pid-analyzer) -- Line Detector 결과를 입력으로 연결 분석
- [YOLO Detection API](/docs/api-reference/yolo) -- P&ID 심볼 검출 (model_type=pid_class_aware)
- [Design Checker API](/docs/api-reference/design-checker) -- P&ID 설계 규칙 검증
