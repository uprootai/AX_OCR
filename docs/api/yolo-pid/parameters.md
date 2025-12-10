# YOLO-PID API Parameters

P&ID 심볼 검출 API - SAHI 기반 대형 이미지 고해상도 검출

## Overview

| 항목 | 값 |
|------|-----|
| **Port** | 5017 |
| **Endpoint** | POST /api/v1/process |
| **Category** | Detection |
| **Version** | 2.0.0 |

## Parameters

| 파라미터 | 타입 | 기본값 | 범위 | 설명 |
|---------|------|--------|------|------|
| `confidence` | number | 0.10 | 0.05-1.0 | 신뢰도 임계값 (낮을수록 더 많은 심볼 검출) |
| `slice_height` | select | 512 | 256/512/768/1024 | SAHI 슬라이스 높이 |
| `slice_width` | select | 512 | 256/512/768/1024 | SAHI 슬라이스 너비 |
| `overlap_ratio` | number | 0.25 | 0.1-0.5 | 슬라이스 오버랩 비율 |
| `class_agnostic` | boolean | false | - | Class-agnostic 모드 |
| `visualize` | boolean | true | - | 결과 시각화 |

## Resource Requirements

### GPU Mode
- **VRAM**: ~3GB
- **최소 VRAM**: 2000MB
- **권장**: RTX 3060 이상
- **CUDA**: 11.8+

### CPU Mode
- **RAM**: ~6GB
- **최소 RAM**: 4096MB
- **참고**: GPU 대비 8배 느림

## Parameter Impact

| 파라미터 | 영향 | 예시 |
|---------|------|------|
| `slice_height` | 슬라이스 크기↓ → 검출 정밀도↑, 처리시간↑ | 256:최정밀, 512:균형, 1024:빠름 |
| `confidence` | 신뢰도↓ → 검출 수↑, 오탐 가능성↑ | 0.05:최대검출, 0.15:균형, 0.30:고신뢰 |

## Detected Classes (32)

Valve, Pump, Tank, Instrument, Heat Exchanger, Compressor, Filter, Mixer, Reactor, Column 등
