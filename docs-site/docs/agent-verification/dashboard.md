---
sidebar_position: 3
title: 대시보드
description: 실시간 검증 대시보드의 지표 및 분석
---

# 대시보드

검증 대시보드는 세션 및 프로젝트 수준에서 검증 진행 상황, 정확도 지표, 성능 분석에 대한 실시간 인사이트를 제공합니다.

## 세션 대시보드

**엔드포인트**: `GET /verification/agent/dashboard/{session_id}`

세션 대시보드는 단일 도면 분석 세션의 검증 상태를 항목 유형(심볼 및 치수)별로 분류하여 보여줍니다.

### 검증 상태 분포

대시보드는 검증 작업의 분포를 추적합니다:

| 상태 | 설명 | 표시 색상 |
|------|------|----------|
| **승인 (Approved)** | 올바름이 확인됨 | 녹색 |
| **수정 (Modified)** | 검토자에 의해 수정됨 | 노란색 |
| **거부 (Rejected)** | 오탐이 제거됨 | 빨간색 |
| **대기 (Pending)** | 검토 대기 중 | 회색 |

### 유형별 작업 분포

각 항목 유형(심볼, 치수)에 대해 대시보드는 다음을 제공합니다:

```json
{
  "session_id": "abc-123",
  "filename": "drawing-001.png",
  "drawing_type": "electrical",
  "symbol": {
    "total": 27,
    "verified": 25,
    "pending": 2,
    "actions": {
      "approved": 22,
      "modified": 2,
      "rejected": 1,
      "pending": 2
    },
    "verified_by": {
      "agent": 18,
      "human": 7
    },
    "reject_reasons": {
      "not_symbol": 1
    },
    "avg_confidence_by_action": {
      "approved": 0.912,
      "modified": 0.743,
      "rejected": 0.385
    }
  },
  "dimension": {
    "total": 54,
    "verified": 50,
    "pending": 4,
    "actions": { "approved": 45, "modified": 4, "rejected": 1, "pending": 4 },
    "verified_by": { "agent": 38, "human": 12 }
  }
}
```

### 주요 지표

| 지표 | 공식 | 설명 |
|------|------|------|
| **완료율 (Completion Rate)** | `(total - pending) / total * 100` | 검증된 항목의 백분율 |
| **에이전트 비율 (Agent Rate)** | `agent_count / total * 100` | AI 에이전트가 처리한 백분율 |
| **승인율 (Approval Rate)** | `approved / verified * 100` | ML 검출의 정확도 |
| **수정율 (Modification Rate)** | `modified / verified * 100` | 수정이 필요한 비율 |
| **거부율 (Rejection Rate)** | `rejected / verified * 100` | 오탐율 (False positive rate) |

### 작업별 평균 신뢰도

이 지표는 다양한 검증 결과에 걸친 신뢰도 분포를 보여줍니다:

- **승인된 항목**: 일반적으로 신뢰도 > 0.85 (모델이 올바름)
- **수정된 항목**: 일반적으로 신뢰도 0.6-0.85 (모델이 근접했지만 수정이 필요)
- **거부된 항목**: 일반적으로 신뢰도 < 0.5 (오탐)

이 통계는 향후 배포를 위한 최적 임계값 결정에 도움이 됩니다.

## 프로젝트 대시보드

**엔드포인트**: `GET /verification/agent/dashboard/project/{project_id}`

프로젝트 대시보드는 프로젝트 내 모든 세션의 검증 결과를 집계하여 검증 효율성에 대한 전체적인 뷰를 제공합니다.

### 집계 지표

```json
{
  "project_id": "project-001",
  "session_count": 12,
  "aggregate": {
    "symbol": {
      "total": 324,
      "approved": 285,
      "rejected": 12,
      "modified": 18,
      "pending": 9,
      "agent": 242,
      "human": 73,
      "completion_rate": 97.2,
      "agent_rate": 74.7
    },
    "dimension": {
      "total": 648,
      "approved": 590,
      "rejected": 8,
      "modified": 35,
      "pending": 15,
      "agent": 502,
      "human": 131,
      "completion_rate": 97.7,
      "agent_rate": 77.5
    }
  },
  "sessions": [
    {
      "session_id": "abc-123",
      "filename": "drawing-001.png",
      "status": "completed",
      "symbol": { "total": 27, "approved": 25, "agent": 18 },
      "dimension": { "total": 54, "approved": 50, "agent": 38 }
    }
  ]
}
```

## 정확도 지표

### 정밀도 (Precision)

승인된 항목 중 실제로 올바른 항목의 비율을 측정합니다 (정답 데이터와의 비교가 필요):

```
Precision = True Positives / (True Positives + False Positives)
```

GT 비교 기능 (`/gt/compare/{session_id}`)을 통해 추적되며, 검출된 항목을 수동으로 레이블링된 정답 데이터(Ground Truth)와 비교합니다.

### 재현율 (Recall)

실제 항목 중 얼마나 많이 검출되었는지를 측정합니다:

```
Recall = True Positives / (True Positives + False Negatives)
```

### F1 점수 (F1 Score)

정밀도와 재현율의 조화 평균:

```
F1 = 2 * (Precision * Recall) / (Precision + Recall)
```

## 처리 속도

대시보드는 검증 처리량을 추적합니다:

| 지표 | 설명 | 목표 |
|------|------|------|
| **분당 항목 수 (Items per minute)** | 평균 검증 처리량 | > 10 항목/분 |
| **예상 검토 시간 (Estimated review time)** | 남은 대기 항목 완료까지의 시간 | 분 단위로 표시 |
| **에이전트 응답 시간 (Agent response time)** | LLM 에이전트 결정 지연 시간 | < 5초/항목 |

### 예상 검토 시간 계산

시스템은 우선순위 분포를 기반으로 남은 검토 시간을 추정합니다:

| 우선순위 | 항목당 예상 시간 |
|---------|----------------|
| CRITICAL | 30초 |
| HIGH | 20초 |
| MEDIUM | 10초 |
| LOW | 2초 (자동 승인) |

## 거부 사유 분석

항목이 거부되면 대시보드가 사유를 분류합니다:

| 사유 | 설명 |
|------|------|
| `not_dimension` | OCR이 치수가 아닌 텍스트를 추출함 |
| `not_symbol` | 오탐 검출 |
| `garbage` | 노이즈 또는 아티팩트 |
| `duplicate` | 동일 항목이 여러 번 검출됨 |
| `unspecified` | 사유가 제공되지 않음 |

이 분석은 ML 파이프라인의 체계적인 문제를 식별하고 모델 개선 방향을 안내하는 데 도움이 됩니다.

## 수정 추적

수정된 항목에 대해 대시보드는 변경 내용을 추적합니다:

- **심볼 수정**: 클래스 레이블 변경 (예: "CT" -> "PT")
- **치수 수정**: 값 수정, 단위 변경, 유형 재분류, 공차 업데이트

```json
{
  "modifications": [
    { "id": "det-001", "class": "CT -> PT" },
    { "id": "dim-042", "value": "45.2 -> 45.5", "unit": "mm" }
  ]
}
```

이러한 수정 사항은 모델이 근접했지만 정확하지 않았던 사례를 나타내므로, 모델 개선을 위한 높은 가치의 학습 예제를 제공합니다.
