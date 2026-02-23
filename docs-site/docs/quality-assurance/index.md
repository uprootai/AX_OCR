---
sidebar_position: 1
title: 품질 보증
description: 품질 보증 체계 개요
---

# 품질 보증 (Quality Assurance)

ML 분석 결과의 품질을 보장하는 체계입니다.

## QA 생명주기

```mermaid
flowchart TD
    DET["검출 결과"] --> GT{"GT 데이터 존재?"}
    GT -->|예| COMP["GT 비교"]
    GT -->|아니오| AL["능동 학습 큐"]
    COMP --> METRICS["메트릭 계산\nmAP, P, R, F1"]
    METRICS --> REPORT["QA 보고서"]

    AL --> PRIORITY["우선순위 점수 산정"]
    PRIORITY --> REVIEW["사람 검토"]
    REVIEW --> FEEDBACK["피드백"]
    FEEDBACK --> RETRAIN["모델 업데이트"]
    RETRAIN --> DET
```

## 핵심 메트릭 (Key Metrics)

| 메트릭 | 설명 | 목표 |
|--------|------|------|
| **mAP@50** | 평균 정밀도 (Mean Average Precision) | > 0.85 |
| **Precision** | 정밀도 | > 0.90 |
| **Recall** | 재현율 | > 0.85 |
| **F1 Score** | 조화 평균 | > 0.87 |
| **CER** | 문자 오류율 (Character Error Rate, OCR) | < 5% |

## 세 가지 핵심 축

| 핵심 축 | 설명 |
|---------|------|
| [GT 비교](./gt-comparison) | 정답(Ground Truth) 데이터와 비교 분석 |
| [능동 학습](./active-learning) | 불확실 샘플 우선 학습 |
| [피드백 파이프라인](./feedback-pipeline) | 사용자 피드백 수집 및 처리 |
| [OCR 메트릭](./ocr-metrics) | OCR 성능 측정 |
