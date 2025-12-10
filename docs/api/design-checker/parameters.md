# Design Checker API Parameters

P&ID 설계 규칙 검증 API - 설계 표준 준수 여부 검사

## Overview

| 항목 | 값 |
|------|-----|
| **Port** | 5019 |
| **Endpoint** | POST /api/v1/process |
| **Category** | Analysis |

## Parameters

| 파라미터 | 타입 | 기본값 | 옵션 | 설명 |
|---------|------|--------|------|------|
| `ruleset` | select | standard | standard/strict/custom | 적용할 설계 규칙셋 |
| `include_warnings` | boolean | true | - | 경고 수준 이슈도 보고 |

## Ruleset Options

| 규칙셋 | 설명 |
|--------|------|
| `standard` | 일반적인 P&ID 설계 규칙 |
| `strict` | 엄격한 안전 규정 포함 |
| `custom` | 사용자 정의 규칙 |

## Output

- `violations`: 규칙 위반 목록
- `warnings`: 경고 목록
- `score`: 설계 품질 점수 (0-100)
- `report`: 상세 분석 리포트
