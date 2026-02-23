---
sidebar_position: 1
title: Batch Processing
description: 대량 도면 일괄 분석
---

# Batch Processing

## Overview

배치 처리는 폴더 단위로 여러 도면을 한 번에 분석하는 기능입니다.

```mermaid
sequenceDiagram
    participant U as User
    participant B as Batch Router
    participant Q as Processing Queue
    participant S as Session Service

    U->>B: Upload folder (N drawings)
    B->>B: Create project
    loop For each drawing
        B->>Q: Enqueue session
        Q->>S: Process drawing
        S->>S: Detect → OCR → Analyze
        S-->>Q: Session complete
    end
    Q-->>B: All sessions done
    B-->>U: Batch results summary
```

## API Endpoints

### Start Batch Analysis

```
POST /api/batch/analyze
Content-Type: multipart/form-data
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `files` | File[] | 도면 이미지 파일들 |
| `project_name` | string | 프로젝트 이름 |
| `features` | string[] | 활성화할 기능 목록 |

### Check Batch Status

```
GET /api/batch/status/{project_id}
```

Response:
```json
{
  "project_id": "a444211b",
  "total_sessions": 53,
  "completed": 53,
  "failed": 0,
  "progress_percent": 100.0
}
```

## Processing Pipeline Per Session

```mermaid
flowchart TD
    IMG["이미지 로드"] --> VLM["VLM 분류"]
    VLM --> DET["YOLO 검출"]
    DET --> OCR["eDOCr2 OCR"]
    OCR --> DIM["치수 파싱"]
    DIM --> VER["검증 큐"]
    VER --> BOM["BOM 생성"]
```

## Parallelization

- 세션 간 병렬 처리 (configurable concurrency)
- GPU 서비스 큐 관리로 메모리 초과 방지
- 실패 세션 자동 재시도 (최대 3회)

## Metrics

| Metric | Value (DSE Bearing) |
|--------|---------------------|
| Total sessions | 53 |
| Avg processing time | ~30s/session |
| Dimensions extracted | 2,710 total |
| Avg dimensions/session | 51.1 |
| Success rate | 100% |
