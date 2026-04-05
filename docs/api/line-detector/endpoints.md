# Line Detector API Endpoints

현재 구현 기준 엔드포인트는 5개다.

## Health and Info

| Method | Endpoint | 설명 |
|------|------|------|
| `GET` | `/health` | 헬스 체크 |
| `GET` | `/api/v1/health` | 헬스 체크 v1 경로 |
| `GET` | `/api/v1/info` | 서비스 메타데이터, 파라미터 정의 |
| `GET` | `/api/v1/profiles` | 프로파일 기본값 목록 |

### `GET /api/v1/info`

```json
{
  "id": "line-detector",
  "name": "Line Detector",
  "display_name": "P&ID Line Detector",
  "version": "1.1.0",
  "endpoint": "/api/v1/process",
  "method": "POST",
  "parameters": [
    {"name": "profile", "type": "select", "default": "pid"},
    {"name": "method", "type": "select", "default": "lsd"},
    {"name": "include_svg", "type": "boolean", "default": false}
  ]
}
```

### `GET /api/v1/profiles`

```json
{
  "profiles": {
    "pid": {
      "method": "lsd",
      "detect_regions": true,
      "visualize_regions": true
    },
    "simple": {
      "method": "lsd",
      "detect_regions": false,
      "visualize_regions": false
    },
    "region_focus": {
      "method": "lsd",
      "detect_regions": true,
      "visualize_regions": true
    },
    "connectivity": {
      "method": "lsd",
      "detect_regions": false,
      "visualize_regions": false
    }
  },
  "detection_methods": {
    "lsd": {"min_length": 20},
    "hough": {"min_length": 30},
    "combined": {"min_length": 15}
  },
  "default_profile": "pid",
  "available_profiles": {
    "pid": "P&ID 도면 배관/신호선 검출 최적화",
    "simple": "라인 검출만 수행 (분류 없음)",
    "region_focus": "점선 박스 영역 검출에 최적화",
    "connectivity": "라인 교차점 및 연결성 분석"
  }
}
```

## Process

| Method | Endpoint | 설명 |
|------|------|------|
| `POST` | `/api/v1/process` | 라인 검출 및 선택 기능 실행 |

### Request Parameters

| 파라미터 | 타입 | 기본값 | 설명 |
|------|------|------|------|
| `file` | File | 필수 | 입력 이미지 |
| `profile` | string | `pid` | 프로파일 기본값 |
| `method` | string | `lsd` | `lsd`, `hough`, `combined` |
| `merge_lines` | boolean | `true` | 공선 라인 병합 |
| `classify_types` | boolean | `true` | 라인 유형 분류 |
| `classify_colors` | boolean | `true` | 색상 분류 |
| `classify_styles` | boolean | `true` | 스타일 분류 |
| `find_intersections` | boolean | `true` | 교차점 계산 |
| `detect_regions` | boolean | `false` | 점선 박스 영역 검출 |
| `region_line_styles` | string | `dashed,dash_dot` | 영역 검출 대상 스타일 |
| `min_region_area` | integer | `5000` | 최소 영역 면적 |
| `visualize` | boolean | `true` | PNG 시각화 생성 |
| `visualize_regions` | boolean | `true` | region overlay 포함 |
| `include_svg` | boolean | `false` | SVG 오버레이 포함 |
| `min_length` | number | `0` | 최소 라인 길이 |
| `max_lines` | integer | `0` | 최대 라인 수 |

### curl Examples

```bash
curl -X POST http://localhost:5016/api/v1/process \
  -F "file=@pid_image.png" \
  -F "profile=simple" \
  -F "method=lsd" \
  -F "classify_colors=false" \
  -F "classify_styles=false" \
  -F "find_intersections=false" \
  -F "min_length=15" \
  -F "max_lines=5000"
```

```bash
curl -X POST http://localhost:5016/api/v1/process \
  -F "file=@pid_image.png" \
  -F "detect_regions=true" \
  -F "classify_styles=true" \
  -F "region_line_styles=dashed,dash_dot,dotted" \
  -F "include_svg=true"
```

### Response Shape

```json
{
  "success": true,
  "data": {
    "lines": [
      {
        "id": 0,
        "start_point": [100.0, 200.0],
        "end_point": [300.0, 200.0],
        "length": 200.0,
        "angle": 0.0,
        "line_type": "pipe",
        "line_style": "solid",
        "color": "black",
        "color_type": "process",
        "confidence": 0.85
      }
    ],
    "intersections": [
      {"id": 0, "point": [200.0, 200.0], "line_ids": [0, 1]}
    ],
    "regions": [
      {
        "id": 0,
        "bbox": [50, 100, 400, 350],
        "area": 87500,
        "region_type": "signal_group",
        "region_type_korean": "신호 그룹"
      }
    ],
    "svg_overlay": {"svg": "<svg>...</svg>"},
    "statistics": {
      "total_lines": 150,
      "intersection_count": 22,
      "by_line_style": {"solid": 120, "dashed": 30},
      "by_color_type": {"process": 140, "water": 10}
    },
    "visualization": "base64_png...",
    "method": "lsd",
    "image_size": {"width": 4096, "height": 3072},
    "options_used": {
      "profile": "simple",
      "method": "lsd",
      "classify_colors": false,
      "classify_styles": false,
      "min_length": 15,
      "max_lines": 5000
    }
  },
  "processing_time": 1.234,
  "error": null
}
```

## Notes

- `find_intersections`가 실제 요청 필드명이다. `find_intersections_flag`는 내부 변수명이지 공개 API 파라미터가 아니다.
- `/api/v1/process` 응답은 `data` 래퍼를 사용한다.
- `visualization`은 출력용 base64다. 입력은 반드시 multipart file 업로드를 사용한다.
