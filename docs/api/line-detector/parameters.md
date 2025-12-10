# Line Detector API Parameters

P&ID 라인 검출 API - Hough Transform 기반 배관 라인 검출

## Overview

| 항목 | 값 |
|------|-----|
| **Port** | 5016 |
| **Endpoint** | POST /api/v1/process |
| **Category** | Segmentation |

## Parameters

| 파라미터 | 타입 | 기본값 | 범위 | 설명 |
|---------|------|--------|------|------|
| `min_line_length` | number | 50 | 10-200 | 최소 라인 픽셀 길이 |
| `detection_threshold` | number | 0.5 | 0.1-1.0 | 라인 검출 감도 |
| `visualize` | boolean | true | - | 라인 시각화 이미지 생성 |

## Resource Requirements

### GPU Mode
- **VRAM**: ~1GB
- **권장**: GTX 1060 이상

### CPU Mode
- **RAM**: ~2GB
- **참고**: CPU에서도 빠른 처리 가능

## Output

- `lines`: 검출된 라인 좌표 목록
- `visualization`: 라인 시각화 이미지 (base64)
