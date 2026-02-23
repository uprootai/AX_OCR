---
sidebar_position: 1
title: Batch & Delivery
description: 대량 도면 일괄 분석 및 납품 패키지
---

# Batch Processing & Delivery

대량의 도면을 일괄 분석하고 납품 가능한 패키지로 내보내는 시스템입니다.

## Pipeline Overview

```mermaid
flowchart LR
    UPLOAD["폴더 업로드\nN개 도면"] --> QUEUE["처리 큐"]
    QUEUE --> PAR{"병렬 처리"}
    PAR --> S1["Session 1"]
    PAR --> S2["Session 2"]
    PAR --> SN["Session N"]
    S1 --> AGG["결과 집계"]
    S2 --> AGG
    SN --> AGG
    AGG --> BOM["통합 BOM"]
    BOM --> EXPORT["Export Package"]
```

## Key Capabilities

| Feature | Description |
|---------|-------------|
| **Batch Analysis** | 폴더 단위 도면 일괄 처리 |
| **Project Management** | 프로젝트 → 세션 계층 관리 |
| **Export Package** | JSON + Excel + PDF 납품 |
| **Self-contained Export** | 서버 없이 독립 실행 가능 |

## Real-World Example

**DSE Bearing Turbine Project:**
- 53 sessions (53개 도면)
- 2,710 dimensions extracted (평균 51.1/session)
- 7 assembly groups (T3~T8 + THRUST)
- 100% batch completion rate

## Project Hierarchy

```mermaid
erDiagram
    PROJECT ||--o{ SESSION : contains
    SESSION ||--o{ DETECTION : has
    SESSION ||--o{ DIMENSION : has
    SESSION ||--o{ BOM_ITEM : generates
    PROJECT ||--o{ QUOTATION : produces

    PROJECT {
        string id PK
        string name
        string client
        int session_count
    }
    SESSION {
        string id PK
        string project_id FK
        string image_path
        string status
    }
```

## Sub-pages

| Page | Description |
|------|-------------|
| [Batch Processing](./batch-processing) | 대량 도면 일괄 분석 상세 |
| [Project Management](./project-management) | 프로젝트 계층 관리 |
| [Export Package](./export-package) | 납품 패키지 생성 |
