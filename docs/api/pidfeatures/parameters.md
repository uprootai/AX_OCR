# PID Features API

> TECHCROSS P&ID 통합 분석 (Valve/Equipment/Checklist)
> **포트**: 5020 | **카테고리**: Analysis | **GPU**: 불필요

---

## 개요

TECHCROSS P&ID 통합 분석 노드. Valve Signal List, Equipment List, Design Checklist를 한 번에 검출합니다. 신뢰도 기반 검증 큐를 자동 생성하여 Human-in-the-Loop 워크플로우를 지원합니다.

---

## 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/v1/pid-features/{session_id}/valve-signal/detect` | 밸브 검출 |
| POST | `/api/v1/pid-features/{session_id}/equipment/detect` | 장비 검출 |
| POST | `/api/v1/pid-features/{session_id}/checklist/check` | 체크리스트 검증 |
| GET | `/api/v1/pid-features/{session_id}/verify/queue` | 검증 큐 조회 |

---

## 파라미터

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `session_id` | string | (필수) | 세션 ID |
| `features` | array | [valve_signal, equipment, checklist] | 활성화할 기능 |
| `product_type` | string | ALL | 제품 타입 (ALL, ECS, HYCHLOR) |
| `confidence_threshold` | number | 0.7 | 신뢰도 임계값 (0.1-0.99) |
| `auto_verify_high_confidence` | boolean | true | 고신뢰도 자동 검증 |

### features 옵션

- `valve_signal`: Valve Signal List 추출
- `equipment`: Equipment List 추출
- `checklist`: Design Checklist 검증

### product_type 옵션

- `ALL`: 전체 제품
- `ECS`: ECS 전해조 전용
- `HYCHLOR`: HYCHLOR 전용

---

## 응답

```json
{
  "status": "success",
  "data": {
    "session_id": "flow_20260117_abc123",
    "valves": [{"valve_id": "V-001", "tag": "XV-101", "type": "Ball Valve"}],
    "equipment": [{"tag": "P-101", "type": "Centrifugal Pump"}],
    "checklist": [{"item_no": "1-1-001", "auto_status": "pass"}],
    "verification_queue": [{"item_id": "V-003", "confidence": 0.65}],
    "summary": {
      "valve_count": 12,
      "equipment_count": 5,
      "checklist_count": 60,
      "pending_verification": 8
    }
  }
}
```

---

**최종 수정**: 2026-01-17
