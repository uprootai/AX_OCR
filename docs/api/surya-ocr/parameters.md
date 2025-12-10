# Surya OCR API Parameters

90+ 언어 지원 다국어 OCR API - 레이아웃 분석 포함

## Overview

| 항목 | 값 |
|------|-----|
| **Port** | 5013 |
| **Endpoint** | POST /api/v1/process |
| **Category** | OCR |

## Parameters

| 파라미터 | 타입 | 기본값 | 옵션 | 설명 |
|---------|------|--------|------|------|
| `language` | select | ko | ko/en/ja/zh | 인식 언어 |
| `layout_analysis` | boolean | true | - | 문서 레이아웃 분석 활성화 |
| `visualize` | boolean | false | - | OCR 결과 시각화 이미지 생성 |

## Supported Languages

90개 이상의 언어 지원:
- 한국어 (ko)
- 영어 (en)
- 일본어 (ja)
- 중국어 (zh)
- 기타 다수

## Resource Requirements

### GPU Mode
- **VRAM**: ~4GB
- **권장**: RTX 3060 이상

### CPU Mode
- **RAM**: ~6GB
- **참고**: GPU 대비 5배 느림

## Output

- `text`: 인식된 텍스트
- `regions`: 텍스트 영역 정보
- `layout`: 레이아웃 분석 결과 (활성화 시)
