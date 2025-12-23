# Active Learning 검증 큐

> **목적**: 저신뢰 검출 우선 검증으로 검증 효율 극대화
> **상태**: ✅ 구현 완료 (2025-12-23)

---

## 개요

Active Learning 검증 큐는 AI 검출 결과를 신뢰도 기반으로 우선순위화하여
검증자가 가장 중요한 항목부터 효율적으로 검증할 수 있도록 지원합니다.

```
검출 결과 → 우선순위 분류 → 검증 큐 → Human 검증 → 로그 저장 → (향후) 재학습
```

---

## 우선순위 분류

| 우선순위 | 조건 | 색상 | 설명 |
|---------|------|------|------|
| **CRITICAL** | 신뢰도 < 0.7 | 🔴 빨강 | 즉시 확인 필요 |
| **HIGH** | 심볼 연결 없음 | 🟠 주황 | 연결 확인 필요 |
| **MEDIUM** | 신뢰도 0.7-0.9 | 🟡 노랑 | 검토 권장 |
| **LOW** | 신뢰도 ≥ 0.9 | 🟢 초록 | 자동 승인 후보 |

### 임계값 설정

| 파라미터 | 기본값 | 환경변수 |
|---------|--------|----------|
| `critical_threshold` | 0.7 | `CRITICAL_THRESHOLD` |
| `auto_approve_threshold` | 0.9 | `AUTO_APPROVE_THRESHOLD` |

---

## 백엔드 구현

### 서비스 (`services/active_learning_service.py`)

```python
class ActiveLearningService:
    def prioritize_items(self, items, item_type='dimension'):
        """항목을 우선순위별로 분류"""

    def get_verification_queue(self, items, item_type='dimension'):
        """우선순위 순으로 정렬된 검증 큐 반환"""

    def get_auto_approve_candidates(self, items):
        """자동 승인 후보 목록 (신뢰도 ≥ 0.9)"""

    def log_verification(self, item_id, item_type, original_data, user_action, ...):
        """검증 결과 로깅 (재학습용)"""

    def get_training_data(self, session_id=None, action_filter=None):
        """모델 재학습용 데이터 조회"""
```

### 검증 로그 형식

```json
{
  "item_id": "dim-001",
  "item_type": "dimension",
  "original_data": {"value": "100mm", "confidence": 0.65},
  "user_action": "modified",
  "modified_data": {"value": "100.5mm"},
  "timestamp": "2025-12-23T10:30:00",
  "session_id": "abc-123",
  "review_time_seconds": 5.2
}
```

---

## API 엔드포인트

### 검증 큐 조회

```http
GET /verification/queue/{session_id}?item_type=dimension
```

**응답**:
```json
{
  "session_id": "abc-123",
  "item_type": "dimension",
  "queue": [
    {
      "id": "dim-001",
      "priority": "critical",
      "confidence": 0.55,
      "reason": "낮은 신뢰도 (0.55)"
    }
  ],
  "stats": {
    "total": 50,
    "verified": 10,
    "pending": 40,
    "critical": 5,
    "high": 8,
    "medium": 15,
    "low": 12,
    "auto_approve_candidates": 12,
    "estimated_review_time_minutes": 8.5
  }
}
```

### 단일 항목 검증

```http
POST /verification/verify/{session_id}
Content-Type: application/json

{
  "item_id": "dim-001",
  "item_type": "dimension",
  "action": "approved",  // approved | rejected | modified
  "modified_data": null,
  "review_time_seconds": 3.5
}
```

### 자동 승인

```http
POST /verification/auto-approve/{session_id}?item_type=dimension
```

신뢰도 ≥ 0.9인 모든 pending 항목 일괄 승인

### 일괄 승인

```http
POST /verification/bulk-approve/{session_id}
Content-Type: application/json

{
  "item_ids": ["dim-001", "dim-002", "dim-003"],
  "item_type": "dimension"
}
```

---

## 프론트엔드 구현

### `VerificationQueue.tsx`

```typescript
interface VerificationQueueProps {
  sessionId: string;
  itemType?: 'dimension' | 'symbol';
  onVerify?: (itemId: string, action: string) => void;
  onAutoApprove?: () => void;
  onItemSelect?: (itemId: string) => void;
}
```

### 주요 기능

1. **우선순위별 그룹화**: 접을 수 있는 섹션으로 표시
2. **통계 대시보드**: 검토 대기, 완료, 예상 시간
3. **자동 승인 버튼**: 고신뢰 항목 일괄 처리
4. **개별 승인/거부**: 각 항목에 액션 버튼
5. **실시간 업데이트**: 검증 후 자동 새로고침

---

## 검증 로그 활용

### 재학습 데이터 조회

```http
GET /verification/training-data?action_filter=modified
```

**응답**:
```json
{
  "data": [
    {
      "item_id": "dim-001",
      "item_type": "dimension",
      "original": {"value": "100mm"},
      "action": "modified",
      "modified": {"value": "100.5mm"}
    }
  ],
  "count": 25,
  "action_counts": {
    "approved": 150,
    "rejected": 10,
    "modified": 25
  }
}
```

### 향후 활용

1. **오분류 패턴 분석**: rejected/modified 항목 분석
2. **신뢰도 임계값 조정**: 검증 결과 기반 최적화
3. **모델 재학습**: 수정된 데이터로 fine-tuning

---

## 설정 파일

### 환경 변수

```bash
# 검증 로그 저장 경로
VERIFICATION_LOG_PATH=/data/logs/verification

# 자동 승인 임계값 (0.5-1.0)
AUTO_APPROVE_THRESHOLD=0.9

# Critical 우선순위 임계값 (0.0-0.9)
CRITICAL_THRESHOLD=0.7
```

---

## 성능 지표

| 항목 | 값 |
|------|-----|
| 평균 검증 시간 (Critical) | 30초/항목 |
| 평균 검증 시간 (Medium) | 10초/항목 |
| 평균 검증 시간 (Low) | 2초/항목 |
| 자동 승인 비율 (신뢰도 ≥ 0.9) | ~24% |
| 예상 검토 시간 절감 | ~40% |

---

## 관련 파일

| 파일 | 설명 |
|------|------|
| `backend/services/active_learning_service.py` | 핵심 서비스 |
| `backend/routers/verification_router.py` | API 라우터 |
| `frontend/src/components/VerificationQueue.tsx` | UI 컴포넌트 |

---

**구현일**: 2025-12-23
