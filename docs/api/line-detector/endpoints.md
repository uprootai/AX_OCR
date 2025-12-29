# Line Detector API Endpoints

전체 4개 엔드포인트 가이드

---

## Health & Info (3개)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/health` | 헬스 체크 |
| GET | `/api/v1/health` | 헬스 체크 (v1) |
| GET | `/api/v1/info` | API 정보 및 BlueprintFlow 메타데이터 |

### GET /api/v1/info 응답 예시

```json
{
  "id": "line-detector",
  "name": "Line Detector",
  "version": "1.1.0",
  "description": "P&ID 라인(배관/신호선) 검출, 스타일 분류, 영역 검출 API",
  "blueprintflow": {
    "category": "segmentation",
    "color": "#8b5cf6",
    "icon": "GitCommitHorizontal"
  },
  "line_style_types": ["solid", "dashed", "dotted", "dash_dot", "double", "wavy"],
  "region_types": ["signal_group", "equipment_boundary", "note_box", "hazardous_area", "scope_boundary", "detail_area"]
}
```

---

## Process (1개)

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/process` | 라인 검출 및 분석 |

### 파라미터

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `file` | File | 필수 | P&ID 도면 이미지 |
| `method` | select | `lsd` | 검출 방식 (lsd/hough/combined) |
| `merge_lines` | boolean | `true` | 공선 라인 병합 |
| `classify_types` | boolean | `true` | 라인 유형 분류 (배관/신호선) |
| `classify_colors` | boolean | `true` | 색상 기반 분류 |
| `classify_styles` | boolean | `true` | 스타일 분류 (실선/점선 등) |
| `find_intersections` | boolean | `true` | 교차점 검출 |
| `detect_regions` | boolean | `false` | 점선 박스 영역 검출 |
| `region_line_styles` | string | `dashed,dash_dot` | 영역 검출에 사용할 스타일 |
| `min_region_area` | number | `5000` | 최소 영역 크기 (픽셀²) |
| `visualize` | boolean | `true` | 결과 시각화 |
| `min_length` | number | `0` | 최소 라인 길이 (0=필터링 안함) |
| `max_lines` | number | `0` | 최대 라인 수 (0=제한 없음) |

### curl 예시

```bash
# 기본 라인 검출
curl -X POST http://localhost:5016/api/v1/process \
  -F "file=@pid_image.png"

# 스타일 분류 + 영역 검출
curl -X POST http://localhost:5016/api/v1/process \
  -F "file=@pid_image.png" \
  -F "classify_styles=true" \
  -F "detect_regions=true" \
  -F "region_line_styles=dashed,dash_dot"

# 고해상도 처리 (최소 길이 필터)
curl -X POST http://localhost:5016/api/v1/process \
  -F "file=@large_pid.png" \
  -F "min_length=20" \
  -F "max_lines=500"
```

### 응답 구조

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
    "statistics": {
      "total_lines": 150,
      "pipe_lines": 100,
      "signal_lines": 40,
      "solid_lines": 120,
      "dashed_lines": 30,
      "total_regions": 3
    },
    "visualization": "base64_encoded_image..."
  },
  "processing_time": 1.234
}
```

---

## 라인 스타일 유형 (6종)

| 스타일 | 한국어 | 설명 |
|--------|--------|------|
| `solid` | 실선 | 일반 배관, 주요 프로세스 라인 |
| `dashed` | 점선 | 대안/비상 라인, 영역 표시 |
| `dotted` | 도트선 | 신호선, 제어선 |
| `dash_dot` | 일점쇄선 | 경계선, SIGNAL FOR 영역 |
| `double` | 이중선 | 고압/특수 배관 |
| `wavy` | 물결선 | 탄성/유연 연결 |

---

## 영역 유형 (6종)

| 유형 | 한국어 | 설명 |
|------|--------|------|
| `signal_group` | 신호 그룹 | SIGNAL FOR BWMS 등 |
| `equipment_boundary` | 장비 경계 | 장비 그룹 표시 |
| `note_box` | 노트 박스 | 도면 주석 영역 |
| `hazardous_area` | 위험 구역 | 안전 경고 영역 |
| `scope_boundary` | 공급 범위 | 공급자별 범위 표시 |
| `detail_area` | 상세 영역 | 확대/상세 도면 표시 |

---

**Last Updated**: 2025-12-29
