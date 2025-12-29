# Design Checker API Parameters

P&ID 도면 설계 오류 검출 및 규정 검증 API

## Overview

| 항목 | 값 |
|------|-----|
| **Port** | 5019 |
| **Main Endpoint** | POST /api/v1/check |
| **BWMS Endpoint** | POST /api/v1/check/bwms |
| **Category** | Analysis |
| **Version** | 1.0.0 |

## Architecture (리팩토링 완료)

```
models/design-checker-api/
├── api_server.py       (167줄)  # FastAPI 앱, lifespan
├── schemas.py          (81줄)   # Pydantic 모델
├── constants.py        (219줄)  # 규칙 정의 (20개)
├── checker.py          (354줄)  # 설계 검증 로직
├── bwms_rules.py       (822줄)  # BWMS 규칙 (7+동적)
├── rule_loader.py      (260줄)  # YAML 기반 규칙 관리
├── excel_parser.py     (210줄)  # 체크리스트 Excel 파싱
└── routers/
    ├── check_router.py    (220줄)  # /api/v1/check, /process
    ├── rules_router.py    (295줄)  # /api/v1/rules/*
    └── checklist_router.py (311줄) # /api/v1/checklist/*
```

## Parameters

### /api/v1/check (설계 검증)

| 파라미터 | 타입 | 기본값 | 옵션 | 설명 |
|---------|------|--------|------|------|
| `symbols` | JSON | 필수 | - | YOLO 검출 결과 (model_type=pid_class_aware) |
| `connections` | JSON | [] | - | PID Analyzer 연결 분석 결과 |
| `lines` | JSON | [] | - | Line Detector 결과 |
| `texts` | JSON | [] | - | OCR 텍스트 (BWMS 검사용) |
| `categories` | string | "" | connectivity, symbol, labeling, specification, standard, safety, bwms | 검사할 카테고리 (쉼표 구분) |
| `severity_threshold` | select | info | error, warning, info | 보고할 최소 심각도 |
| `include_bwms` | boolean | true | - | BWMS 규칙 포함 여부 |

### /api/v1/check/bwms (BWMS 전용)

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `symbols` | JSON | 필수 | BWMS 장비 심볼 목록 |
| `connections` | JSON | [] | 장비 간 연결 정보 |
| `lines` | JSON | [] | 라인 정보 |
| `texts` | JSON | [] | OCR 텍스트 |
| `enabled_rules` | string | "" | 검사할 BWMS 규칙 ID (쉼표 구분) |

## Design Rules (20개)

| 카테고리 | 규칙 수 | 설명 |
|----------|--------|------|
| `connectivity` | 4개 | 연결 무결성 검증 |
| `symbol` | 4개 | 심볼 표준 준수 |
| `labeling` | 4개 | 라벨링 규칙 |
| `specification` | 3개 | 사양 검증 |
| `standard` | 3개 | 표준 규정 준수 |
| `safety` | 2개 | 안전 관련 검증 |

## BWMS Rules (7개 + 동적)

| 규칙 ID | 이름 | 심각도 | 자동검사 |
|---------|------|--------|----------|
| `BWMS-001` | G-2 Sampling Port 상류 위치 | warning | O |
| `BWMS-004` | FMU-ECU 순서 검증 | error | O |
| `BWMS-005` | GDS 위치 검증 | error | O |
| `BWMS-006` | TSU-APU 거리 제한 | warning | O |
| `BWMS-007` | Mixing Pump 용량 검증 | warning | X |
| `BWMS-008` | UV Reactor 사양 검증 | warning | X |
| `BWMS-009` | HYCHLOR 필터 위치 | warning | O |

## Output

```json
{
  "success": true,
  "data": {
    "violations": [
      {
        "rule_id": "CONN-001",
        "rule_name": "미연결 심볼 검사",
        "rule_name_en": "Unconnected Symbol Check",
        "category": "connectivity",
        "severity": "error",
        "standard": "ISO 10628",
        "description": "펌프 P-101이 연결되지 않았습니다",
        "location": {"x": 100, "y": 200, "width": 50, "height": 50},
        "affected_elements": ["P-101"],
        "suggestion": "파이프라인 연결을 확인하세요"
      }
    ],
    "summary": {
      "total": 3,
      "errors": 1,
      "warnings": 2,
      "info": 0,
      "compliance_score": 85.0
    },
    "rules_checked": 27,
    "checked_at": "2025-12-29T08:00:00"
  },
  "processing_time": 0.123
}
```

## Standards Supported

| 표준 | 설명 |
|------|------|
| **ISO 10628** | P&ID 표준 |
| **ISA 5.1** | 계기 심볼 표준 |
| **TECHCROSS BWMS** | 선박평형수처리시스템 규정 |

---

**See Also**:
- [endpoints.md](endpoints.md) - 전체 20개 엔드포인트
- [bwms-rules.md](bwms-rules.md) - BWMS 규칙 관리 가이드

**Last Updated**: 2025-12-29
