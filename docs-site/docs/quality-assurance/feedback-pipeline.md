---
sidebar_position: 3
title: 피드백 파이프라인
description: 사용자 피드백 처리 파이프라인
---

# 피드백 파이프라인 (Feedback Pipeline)

## 개요

사용자 피드백을 수집하고 검증 완료된 데이터를 YOLO 재학습용 데이터셋으로 변환하여 모델을 지속적으로 개선합니다.

```mermaid
flowchart TD
    USER["사용자 검증"] --> TYPE{"피드백 유형"}
    TYPE -->|승인| APP["긍정 샘플"]
    TYPE -->|거부| REJ["부정 샘플"]
    TYPE -->|수정| MOD["수정된 정답 데이터"]

    APP --> STORE["세션 저장소"]
    REJ --> STORE
    MOD --> STORE
    STORE --> COLLECT["collect_verified_sessions()\n최소 승인율 >= 50%"]
    COLLECT --> EXPORT["export_yolo_dataset()"]
    EXPORT --> YOLO["YOLO 학습 데이터\nimages/ + labels/ + data.yaml"]
```

## 피드백 유형 (Feedback Types)

| 유형 | `verification_status` | 의미 | 재학습 활용 |
|------|----------------------|------|------------|
| **승인** | `approved` | 검출 정확함 | 원본 bbox + class를 긍정 샘플로 사용 |
| **거부** | `rejected` | 오검출 | 기본 제외 (`include_rejected=True` 로 포함 가능) |
| **수정** | `modified` | 수정 필요 | `modified_class_name`, `modified_bbox` 사용 |

수정된 항목은 원본 대신 수정된 값을 학습 데이터로 사용합니다:

```python
# class: modified_class_name or class_name
class_name = det.get("modified_class_name") or det.get("class_name")
# bbox: modified_bbox or bbox
bbox = det.get("modified_bbox") or det.get("bbox")
```

## 데이터 수집 (Data Collection)

`collect_verified_sessions()` 는 다음 조건으로 학습 가능한 세션을 필터링합니다:

| 필터 | 기본값 | 설명 |
|------|--------|------|
| `min_approved_rate` | `0.5` (50%) | 최소 승인율 |
| `days_back` | `None` (전체) | 최근 N일 내 세션만 |
| `pending == 0` | 필수 | 모든 항목 검증 완료 필수 |

## YOLO 데이터셋 내보내기 (YOLO Dataset Export)

`export_yolo_dataset()` 는 검증된 세션을 YOLO 형식으로 내보냅니다:

### 출력 구조

```
feedback_dataset_20260222_103000/
  images/          # 원본 이미지 복사
  labels/          # YOLO TXT 라벨 (session_id.txt)
  classes.txt      # 클래스 목록 (정렬순)
  data.yaml        # YOLO 학습 설정
  metadata.json    # 내보내기 메타데이터
```

### YOLO 라벨 형식

검출 bbox를 정규화된 YOLO 좌표로 변환합니다:

```python
x_center = ((x1 + x2) / 2) / image_width   # 0.0 ~ 1.0
y_center = ((y1 + y2) / 2) / image_height   # 0.0 ~ 1.0
width    = (x2 - x1) / image_width
height   = (y2 - y1) / image_height
# 유효성: 0 <= x_center <= 1, width > 0, height > 0
```

## API 엔드포인트

| 메서드 | 엔드포인트 | 설명 |
|--------|----------|------|
| `GET` | `/feedback/stats` | 피드백 통계 (승인/거부/수정 비율) |
| `GET` | `/feedback/sessions` | 검증 완료 세션 목록 |
| `POST` | `/feedback/export/yolo` | YOLO 데이터셋 내보내기 |
| `GET` | `/feedback/exports` | 이전 내보내기 목록 |
| `GET` | `/feedback/health` | 서비스 상태 |

### 내보내기 요청

```json
{
  "output_name": "my_dataset",
  "include_rejected": false,
  "min_approved_rate": 0.5,
  "days_back": 30
}
```

### 통계 응답

```json
{
  "total_sessions": 25,
  "total_detections": 450,
  "approved_count": 380,
  "rejected_count": 40,
  "modified_count": 30,
  "approval_rate": 0.844,
  "rejection_rate": 0.089,
  "modification_rate": 0.067
}
```

## 능동 학습과의 연동 (Integration with Active Learning)

피드백 파이프라인은 능동 학습(Active Learning) 서비스와 상호 보완적으로 동작합니다:

```mermaid
flowchart LR
    AL["능동 학습\n우선순위 큐"] --> REVIEW["사람/에이전트\n검토"]
    REVIEW --> LOG["검증 로그\n(JSONL, 항목별)"]
    REVIEW --> SESSION["세션 저장소\n(세션별)"]
    SESSION --> FP["피드백 파이프라인\n수집 + 내보내기"]
    FP --> YOLO["YOLO 데이터셋"]
    YOLO --> RETRAIN["모델 재학습"]
    RETRAIN --> BETTER["개선된 모델"]
    BETTER --> AL
```

- **능동 학습**: 항목 레벨 로그 (`VerificationLog` JSONL) - 개별 판단 기록
- **피드백 파이프라인**: 세션 레벨 수집 - 검증 완료된 전체 세션을 YOLO 데이터셋으로 변환

## 충돌 해결 (Conflict Resolution)

동일 세션에서 다수의 검토자가 있을 경우:

- 각 검출 결과의 `verification_status`는 마지막 검토 결과를 반영
- 세션 내 모든 항목이 `pending`이 아닐 때 수집 대상이 됨
- `min_approved_rate` 필터로 품질이 낮은 세션(거부 비율 높음)은 자동 제외
