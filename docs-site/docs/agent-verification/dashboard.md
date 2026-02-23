---
sidebar_position: 3
title: Dashboard
description: Real-time verification dashboard with metrics and analytics
---

# Dashboard

The verification dashboard provides real-time insights into verification progress, accuracy metrics, and performance analytics at both session and project levels.

## Session Dashboard

**Endpoint**: `GET /verification/agent/dashboard/{session_id}`

The session dashboard shows verification status for a single drawing analysis session, broken down by item type (symbol and dimension).

### Verification Status Distribution

The dashboard tracks the distribution of verification actions:

| Status | Description | Indicator |
|--------|-------------|-----------|
| **Approved** | Confirmed correct | Green |
| **Modified** | Corrected by reviewer | Yellow |
| **Rejected** | False positive removed | Red |
| **Pending** | Awaiting review | Gray |

### Action Distribution by Type

For each item type (symbol, dimension), the dashboard provides:

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

### Key Metrics

| Metric | Formula | Description |
|--------|---------|-------------|
| **Completion Rate** | `(total - pending) / total * 100` | Percentage of items verified |
| **Agent Rate** | `agent_count / total * 100` | Percentage handled by AI agent |
| **Approval Rate** | `approved / verified * 100` | Accuracy of ML detections |
| **Modification Rate** | `modified / verified * 100` | Rate of corrections needed |
| **Rejection Rate** | `rejected / verified * 100` | False positive rate |

### Average Confidence by Action

This metric reveals the confidence distribution across different verification outcomes:

- **Approved items**: Typically confidence > 0.85 (model was correct)
- **Modified items**: Typically confidence 0.6-0.85 (model was close but needed correction)
- **Rejected items**: Typically confidence < 0.5 (false positives)

These statistics help identify optimal threshold values for future deployments.

## Project Dashboard

**Endpoint**: `GET /verification/agent/dashboard/project/{project_id}`

The project dashboard aggregates verification results across all sessions in a project, providing a bird's-eye view of verification efficiency.

### Aggregated Metrics

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

## Accuracy Metrics

### Precision

Measures how many approved items are actually correct (requires ground truth comparison):

```
Precision = True Positives / (True Positives + False Positives)
```

Tracked through the GT Comparison feature (`/gt/compare/{session_id}`), which compares detected items against manually labeled ground truth.

### Recall

Measures how many real items were detected:

```
Recall = True Positives / (True Positives + False Negatives)
```

### F1 Score

Harmonic mean of precision and recall:

```
F1 = 2 * (Precision * Recall) / (Precision + Recall)
```

## Processing Speed

The dashboard tracks verification throughput:

| Metric | Description | Target |
|--------|-------------|--------|
| **Items per minute** | Average verification throughput | > 10 items/min |
| **Estimated review time** | Time to complete remaining pending items | Displayed in minutes |
| **Agent response time** | LLM agent decision latency | < 5 sec/item |

### Estimated Review Time Calculation

The system estimates remaining review time based on priority distribution:

| Priority | Estimated Time per Item |
|----------|------------------------|
| CRITICAL | 30 seconds |
| HIGH | 20 seconds |
| MEDIUM | 10 seconds |
| LOW | 2 seconds (auto-approve) |

## Reject Reason Analysis

When items are rejected, the dashboard categorizes the reasons:

| Reason | Description |
|--------|-------------|
| `not_dimension` | OCR extracted text that is not a dimension |
| `not_symbol` | False positive detection |
| `garbage` | Noise or artifact |
| `duplicate` | Same item detected multiple times |
| `unspecified` | No reason provided |

This analysis helps identify systematic issues in the ML pipeline and guides model improvement efforts.

## Modification Tracking

For modified items, the dashboard tracks what was changed:

- **Symbol modifications**: Class label changes (e.g., "CT" -> "PT")
- **Dimension modifications**: Value corrections, unit changes, type reclassification, tolerance updates

```json
{
  "modifications": [
    { "id": "det-001", "class": "CT -> PT" },
    { "id": "dim-042", "value": "45.2 -> 45.5", "unit": "mm" }
  ]
}
```

These modifications provide high-value training examples for model improvement, as they represent cases where the model was close but not quite correct.
