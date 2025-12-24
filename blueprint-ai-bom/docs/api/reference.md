# API 레퍼런스

> **Blueprint AI BOM 백엔드 API 문서**
> **Base URL**: `http://localhost:5020`
> **최종 업데이트**: 2025-12-23

---

## 목차

1. [세션 관리](#세션-관리)
2. [분석](#분석)
3. [검증 (Active Learning)](#검증-active-learning)
4. [BOM](#bom)
5. [관계](#관계)
6. [분류](#분류)
7. [Feedback Loop](#feedback-loop)

---

## 세션 관리

### 이미지 업로드

```http
POST /sessions/upload
Content-Type: multipart/form-data
```

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `file` | File | ✅ | 이미지 파일 (jpg, png, bmp, tiff) |
| `drawing_type` | string | ❌ | 도면 타입 (auto, mechanical, pid, assembly) |

**응답** (200):
```json
{
  "session_id": "abc-123-def-456",
  "filename": "drawing.png",
  "status": "uploaded",
  "created_at": "2025-12-23T10:00:00",
  "drawing_type": "auto",
  "image_width": 2048,
  "image_height": 1536
}
```

### 세션 목록 조회

```http
GET /sessions?limit=50
```

**응답** (200):
```json
[
  {
    "session_id": "abc-123",
    "filename": "drawing.png",
    "status": "analyzed",
    "created_at": "2025-12-23T10:00:00"
  }
]
```

### 세션 상세 조회

```http
GET /sessions/{session_id}?include_image=false
```

**응답** (200):
```json
{
  "session_id": "abc-123",
  "filename": "drawing.png",
  "file_path": "/data/uploads/abc-123/original.png",
  "status": "analyzed",
  "drawing_type": "mechanical",
  "image_width": 2048,
  "image_height": 1536,
  "detections": [...],
  "dimensions": [...],
  "relations": [...]
}
```

### 세션 삭제

```http
DELETE /sessions/{session_id}
```

**응답** (200):
```json
{
  "status": "deleted",
  "session_id": "abc-123"
}
```

---

## 분석

### 전체 분석 실행

```http
POST /analysis/full/{session_id}
Content-Type: application/json
```

**요청 본문**:
```json
{
  "run_detection": true,
  "run_ocr": true,
  "run_gdt": true,
  "detection_confidence": 0.4,
  "ocr_languages": ["ko", "en"]
}
```

**응답** (200):
```json
{
  "session_id": "abc-123",
  "status": "analyzed",
  "detection_count": 15,
  "dimension_count": 42,
  "gdt_count": 8,
  "processing_time_ms": 3500
}
```

### YOLO 검출만 실행

```http
POST /analysis/detect/{session_id}
Content-Type: application/json
```

**요청 본문**:
```json
{
  "confidence": 0.4,
  "iou_threshold": 0.5,
  "imgsz": 1024
}
```

### OCR 인식만 실행

```http
POST /analysis/ocr/{session_id}
Content-Type: application/json
```

**요청 본문**:
```json
{
  "languages": ["ko", "en"],
  "parse_dimensions": true,
  "parse_gdt": true
}
```

---

## 검증 (Active Learning)

### 검증 큐 조회

```http
GET /verification/queue/{session_id}?item_type=dimension
```

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `item_type` | string | dimension | dimension 또는 symbol |

**응답** (200):
```json
{
  "session_id": "abc-123",
  "item_type": "dimension",
  "queue": [
    {
      "id": "dim-001",
      "item_type": "dimension",
      "priority": "critical",
      "confidence": 0.55,
      "has_relation": false,
      "reason": "낮은 신뢰도 (0.55)",
      "data": {...}
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
  },
  "thresholds": {
    "critical": 0.7,
    "auto_approve": 0.9
  }
}
```

### 검증 통계 조회

```http
GET /verification/stats/{session_id}?item_type=dimension
```

### 단일 항목 검증

```http
POST /verification/verify/{session_id}
Content-Type: application/json
```

**요청 본문**:
```json
{
  "item_id": "dim-001",
  "item_type": "dimension",
  "action": "approved",
  "modified_data": null,
  "review_time_seconds": 3.5
}
```

| action | 설명 |
|--------|------|
| `approved` | 승인 |
| `rejected` | 거부 |
| `modified` | 수정 (modified_data 필요) |

### 자동 승인 후보 조회

```http
GET /verification/auto-approve-candidates/{session_id}?item_type=dimension
```

### 자동 승인 실행

```http
POST /verification/auto-approve/{session_id}?item_type=dimension
```

신뢰도 ≥ 0.9인 모든 pending 항목 자동 승인

### 일괄 승인

```http
POST /verification/bulk-approve/{session_id}
Content-Type: application/json
```

**요청 본문**:
```json
{
  "item_ids": ["dim-001", "dim-002", "dim-003"],
  "item_type": "dimension"
}
```

### 검증 로그 조회

```http
GET /verification/logs/{session_id}?action_filter=modified
```

### 재학습 데이터 조회

```http
GET /verification/training-data?session_id=abc-123&action_filter=modified
```

### 임계값 조회

```http
GET /verification/thresholds
```

### 임계값 업데이트

```http
PUT /verification/thresholds
Content-Type: application/json
```

**요청 본문**:
```json
{
  "auto_approve_threshold": 0.9,
  "critical_threshold": 0.7
}
```

---

## BOM

### BOM 생성

```http
POST /bom/generate/{session_id}
```

**응답** (200):
```json
{
  "session_id": "abc-123",
  "filename": "drawing.png",
  "detection_count": 15,
  "approved_count": 14,
  "items": [
    {
      "item_no": 1,
      "class_name": "CT",
      "quantity": 3,
      "unit_price": 50000,
      "total_price": 150000,
      "detection_ids": ["det-001", "det-002", "det-003"],
      "avg_confidence": 0.92
    }
  ],
  "summary": {
    "total_items": 5,
    "total_quantity": 15,
    "subtotal": 850000,
    "vat": 85000,
    "total": 935000
  }
}
```

### BOM 내보내기

```http
GET /bom/export/{session_id}/{format}?customer_name=고객사
```

| format | Content-Type | 설명 |
|--------|--------------|------|
| `json` | application/json | JSON 형식 |
| `csv` | text/csv | CSV 형식 |
| `excel` | application/vnd.openxmlformats-... | Excel 파일 |
| `pdf` | application/pdf | PDF 보고서 |

---

## 관계

### 관계 목록 조회

```http
GET /relations/{session_id}
```

**응답** (200):
```json
{
  "session_id": "abc-123",
  "relations": [
    {
      "id": "rel-001",
      "dimension_id": "dim-001",
      "symbol_id": "det-001",
      "relation_type": "dimension_to_symbol",
      "confidence": 0.85
    }
  ]
}
```

### 관계 수동 추가

```http
POST /relations/{session_id}
Content-Type: application/json
```

**요청 본문**:
```json
{
  "dimension_id": "dim-001",
  "symbol_id": "det-001"
}
```

### 관계 삭제

```http
DELETE /relations/{session_id}/{relation_id}
```

---

## 분류

### 도면 타입 분류

```http
POST /classification/classify/{session_id}
```

**응답** (200):
```json
{
  "session_id": "abc-123",
  "drawing_type": "mechanical",
  "confidence": 0.92,
  "alternatives": [
    {"type": "assembly", "confidence": 0.05},
    {"type": "pid", "confidence": 0.03}
  ]
}
```

---

## Feedback Loop

### 피드백 통계 조회

```http
GET /feedback/stats?days_back=30
```

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `days_back` | int | ❌ | 최근 N일 내 데이터만 |

**응답** (200):
```json
{
  "total_sessions": 15,
  "total_detections": 450,
  "approved_count": 380,
  "rejected_count": 45,
  "modified_count": 25,
  "approval_rate": 0.844,
  "rejection_rate": 0.100,
  "modification_rate": 0.056
}
```

### 검증 완료 세션 목록

```http
GET /feedback/sessions?min_approved_rate=0.5&days_back=30
```

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `min_approved_rate` | float | 0.5 | 최소 승인율 |
| `days_back` | int | - | 최근 N일 내 세션 |

**응답** (200):
```json
{
  "sessions": [
    {
      "session_id": "abc-123",
      "filename": "drawing.png",
      "stats": {
        "total": 30,
        "approved": 28,
        "rejected": 2,
        "approval_rate": 0.933
      }
    }
  ],
  "count": 15
}
```

### YOLO 데이터셋 내보내기

```http
POST /feedback/export/yolo
Content-Type: application/json
```

**요청 본문**:
```json
{
  "output_name": "dataset_v1",
  "include_rejected": false,
  "min_approved_rate": 0.5,
  "days_back": 30
}
```

**응답** (200):
```json
{
  "success": true,
  "output_path": "/data/yolo_training/dataset_v1",
  "image_count": 150,
  "label_count": 4500,
  "class_distribution": {"CT": 850, "BUZZER": 320},
  "timestamp": "20251223_143000",
  "error": null
}
```

### 내보내기 목록 조회

```http
GET /feedback/exports
```

**응답** (200):
```json
{
  "exports": [
    {
      "name": "dataset_v1",
      "path": "/data/yolo_training/dataset_v1",
      "created_at": "20251223_143000",
      "image_count": 150,
      "label_count": 4500,
      "class_count": 14
    }
  ],
  "count": 1
}
```

### 서비스 상태 확인

```http
GET /feedback/health
```

**응답** (200):
```json
{
  "status": "healthy",
  "feedback_path": "/data/feedback",
  "yolo_export_path": "/data/yolo_training",
  "exports_count": 1
}
```

---

## 공통 응답 코드

| 코드 | 설명 |
|------|------|
| 200 | 성공 |
| 400 | 잘못된 요청 |
| 404 | 리소스 없음 |
| 500 | 서버 오류 |

---

## 에러 응답 형식

```json
{
  "detail": "세션을 찾을 수 없습니다"
}
```

---

**Swagger UI**: `http://localhost:5020/docs`
**ReDoc**: `http://localhost:5020/redoc`
