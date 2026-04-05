# Line Detector API Parameters

Line Detector API는 `POST /api/v1/process` 하나에 기능을 모아 두고, `profile`과 개별 파라미터 조합으로 동작을 바꾼다.

## Overview

| 항목 | 값 |
|------|-----|
| **Port** | 5016 |
| **Endpoint** | `POST /api/v1/process` |
| **Content-Type** | `multipart/form-data` |
| **Image field** | `file` |
| **Default profile** | `pid` |

## Exposed Parameters

| 파라미터 | 타입 | 기본값 | 설명 |
|------|------|------|------|
| `profile` | string | `pid` | 프로파일 기본값 선택 |
| `method` | string | `lsd` | `lsd`, `hough`, `combined` |
| `merge_lines` | boolean | `true` | 공선 라인 병합 |
| `classify_types` | boolean | `true` | 라인 유형 분류 |
| `classify_colors` | boolean | `true` | 색상 분류 |
| `classify_styles` | boolean | `true` | 스타일 분류 |
| `find_intersections` | boolean | `true` | 교차점 계산 |
| `detect_regions` | boolean | `false` | 점선 박스 영역 검출 |
| `region_line_styles` | string | `dashed,dash_dot` | 영역 검출 대상 스타일 목록 |
| `min_region_area` | integer | `5000` | 최소 영역 면적 |
| `visualize` | boolean | `true` | base64 PNG 시각화 생성 |
| `visualize_regions` | boolean | `true` | region overlay 포함 |
| `include_svg` | boolean | `false` | `svg_overlay` 응답 포함 |
| `min_length` | number | `0` | 최소 라인 길이. `0`이면 필터 없음 |
| `max_lines` | integer | `0` | 긴 라인 우선 상한. `0`이면 제한 없음 |

## Profiles

| 프로파일 | 목적 | 기본값 요약 |
|------|------|------|
| `pid` | 일반 P&ID 분석 | 분류/교차점/영역 검출 활성화 |
| `simple` | 선만 빠르게 검출 | 분류/교차점/영역 검출 비활성화 |
| `region_focus` | 점선 박스 중심 | 스타일 분류와 영역 검출 활성화 |
| `connectivity` | 연결성 분석 | 교차점 검출 활성화, 색상/스타일 분류 축소 |

## Important Notes

- 실제 업로드 필드명은 `image`가 아니라 `file`이다.
- `profile`은 시작값일 뿐이고, 같은 요청의 개별 파라미터가 최종 우선순위를 가진다.
- `detect_regions=true`를 써도 `classify_styles=false`면 region 검출은 실질적으로 동작하지 않는다.
- OpenCV LSD 세부값(`scale`, `sigma_scale`, `ang_th` 등)은 API에서 별도 노출하지 않는다. 현재 구현은 `cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD)` 기본값을 사용한다.
- 내부 병합 함수 `merge_collinear_lines()`는 코드상 `angle_threshold=5.0`, `distance_threshold=20.0`를 사용한다.

## Output Summary

- `lines`: 검출된 선분 목록
- `intersections`: 교차점 목록
- `regions`: 점선 박스 영역 목록
- `statistics`: 카운트 및 분포 통계
- `visualization`: base64 PNG
- `svg_overlay`: 선택적 SVG 오버레이
- `image_size`: `{width, height}`
- `options_used`: 실제 적용된 옵션
