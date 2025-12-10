# EasyOCR API Parameters

80+ 언어 지원 OCR API - CPU 친화적

## Overview

| 항목 | 값 |
|------|-----|
| **Port** | 5015 |
| **Endpoint** | POST /api/v1/process |
| **Category** | OCR |

## Parameters

| 파라미터 | 타입 | 기본값 | 범위 | 설명 |
|---------|------|--------|------|------|
| `language` | select | ko | ko/en/ja/ch_sim | 인식 언어 |
| `min_confidence` | number | 0.5 | 0-1 | 최소 인식 신뢰도 |
| `paragraph` | boolean | true | - | 텍스트를 단락으로 분리 |

## Supported Languages

80개 이상의 언어 지원:
- 한국어 (ko)
- 영어 (en)
- 일본어 (ja)
- 중국어 간체 (ch_sim)
- 중국어 번체 (ch_tra)
- 기타 다수

## Resource Requirements

### GPU Mode
- **VRAM**: ~2GB
- **권장**: GTX 1060 이상

### CPU Mode
- **RAM**: ~3GB
- **참고**: CPU에서도 효율적으로 동작

## Output

- `text`: 인식된 텍스트
- `results`: 상세 인식 결과 (좌표, 신뢰도 포함)
- `paragraphs`: 단락별 텍스트 (paragraph=true 시)
