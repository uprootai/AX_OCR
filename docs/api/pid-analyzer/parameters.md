# PID Analyzer API Parameters

P&ID 연결 분석 API - 심볼과 라인 연결 분석, BOM 생성

## Overview

| 항목 | 값 |
|------|-----|
| **Port** | 5018 |
| **Endpoint** | POST /api/v1/process |
| **Category** | Analysis |

## Parameters

| 파라미터 | 타입 | 기본값 | 범위 | 설명 |
|---------|------|--------|------|------|
| `connection_distance` | number | 30 | 10-100 | 심볼-라인 연결 거리 임계값 (px) |
| `generate_bom` | boolean | true | - | Bill of Materials 생성 |
| `visualize` | boolean | true | - | 연결 분석 시각화 |

## Input Requirements

이 API는 다음 데이터가 필요합니다:
- YOLO 심볼 검출 결과 (`detections`) - model_type=pid_class_aware 사용
- Line Detector 라인 검출 결과 (`lines`)

## Output

- `connections`: 심볼 간 연결 정보
- `bom`: Bill of Materials (장비 목록)
- `graph`: 연결 그래프 데이터
- `visualization`: 연결 시각화 이미지

## Resource Requirements

### CPU Mode
- **RAM**: ~1GB
- **참고**: 순수 알고리즘 처리로 GPU 불필요
