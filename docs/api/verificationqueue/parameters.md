# Verification Queue API

> Human-in-the-Loop 검증 큐 관리
> **포트**: 5020 | **카테고리**: Analysis | **GPU**: 불필요

---

## 개요

Human-in-the-Loop 검증 큐를 관리합니다. 신뢰도가 낮은 항목을 검토하고 승인/거부/수정할 수 있습니다.

---

## 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/v1/pid-features/{session_id}/verify/queue` | 검증 큐 조회 |
| POST | `/api/v1/pid-features/{session_id}/verify` | 단일 항목 검증 |
| POST | `/api/v1/pid-features/{session_id}/verify/bulk` | 대량 검증 |
| GET | `/api/v1/pid-features/{session_id}/summary` | 검증 요약 |

---

## 파라미터

### 검증 큐 조회

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `session_id` | string | (필수) | 세션 ID |
| `item_type` | string | all | 필터 (all, valve, equipment, checklist) |

### 단일 항목 검증

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `item_id` | string | (필수) | 항목 ID |
| `item_type` | string | (필수) | 항목 타입 |
| `action` | string | (필수) | 액션 (verify, reject) |
| `notes` | string | - | 메모 |

---

## BlueprintFlow 파라미터

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `queue_filter` | select | all | 큐 필터 |
| `sort_by` | select | confidence_asc | 정렬 기준 |
| `batch_size` | number | 20 | 배치 크기 (5-100) |
| `auto_approve_threshold` | number | 0.95 | 자동 승인 임계값 (0.8-1.0) |

---

## 응답

```json
{
  "status": "success",
  "data": {
    "verified_items": [{"item_id": "V-001", "verification_status": "auto_verified"}],
    "rejected_items": [{"item_id": "E-005", "reason": "오검출"}],
    "pending_items": [{"item_id": "V-003", "confidence": 0.65}],
    "summary": {
      "total": 25,
      "verified": 15,
      "rejected": 2,
      "pending": 8,
      "progress_rate": 68.0
    }
  }
}
```

---

**최종 수정**: 2026-01-17
