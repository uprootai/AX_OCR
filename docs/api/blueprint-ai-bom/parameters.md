# Blueprint AI BOM API

> **포트**: 5020 | **카테고리**: Analysis
> **버전**: v10.5 | **최종 업데이트**: 2026-01-17

---

## 개요

Blueprint AI BOM은 기계 도면을 분석하여 BOM(Bill of Materials)을 자동 생성하는
Human-in-the-Loop AI 시스템입니다.

```
도면 업로드 → AI 검출 → Human 검증 → BOM 생성 → 내보내기
```

---

## 엔드포인트

### 세션 관리

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/sessions/upload` | 이미지 업로드 및 세션 생성 |
| GET | `/sessions` | 세션 목록 조회 |
| GET | `/sessions/{session_id}` | 세션 상세 조회 |
| DELETE | `/sessions/{session_id}` | 세션 삭제 |

### 분석

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/analysis/detect/{session_id}` | YOLO 심볼 검출 |
| POST | `/analysis/ocr/{session_id}` | OCR 치수 인식 |
| POST | `/analysis/full/{session_id}` | 전체 분석 파이프라인 |

### 검증 (Active Learning)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/verification/queue/{session_id}` | 검증 큐 조회 |
| GET | `/verification/stats/{session_id}` | 검증 통계 |
| POST | `/verification/verify/{session_id}` | 단일 항목 검증 |
| POST | `/verification/auto-approve/{session_id}` | 자동 승인 (≥0.9) |
| POST | `/verification/bulk-approve/{session_id}` | 일괄 승인 |

### Feedback Loop

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/feedback/stats` | 피드백 통계 |
| GET | `/feedback/sessions` | 검증 완료 세션 목록 |
| POST | `/feedback/export/yolo` | YOLO 데이터셋 내보내기 |
| GET | `/feedback/exports` | 내보내기 목록 |

### BOM

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/bom/generate/{session_id}` | BOM 생성 |
| GET | `/bom/export/{session_id}/{format}` | 내보내기 (excel/csv/json/pdf) |

### 장기 로드맵 (v10.5 완료)

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/analysis/longterm/region-segmentation/{session_id}` | 영역 세분화 |
| POST | `/analysis/longterm/notes-extraction/{session_id}` | 노트 추출 |
| POST | `/analysis/longterm/revision-compare` | 리비전 비교 |
| POST | `/analysis/longterm/vlm-classification/{session_id}` | VLM 분류 |

---

## 파라미터

### 세션 업로드

```http
POST /sessions/upload
Content-Type: multipart/form-data
```

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `file` | File | ✅ | - | 도면 이미지 (PNG, JPG, PDF) |
| `features` | List[str] | ❌ | [] | 활성화할 기능 목록 |

**features 옵션** (18개):

| 기능 ID | 설명 |
|---------|------|
| `symbol_detection` | YOLO 심볼 검출 |
| `symbol_verification` | 심볼 검증 UI |
| `dimension_ocr` | 치수 OCR |
| `dimension_verification` | 치수 검증 UI |
| `gdt_parsing` | GD&T 파싱 |
| `relation_extraction` | 치수-심볼 관계 |
| `gt_comparison` | GT 비교 |
| `bom_generation` | BOM 생성 |
| `title_block_ocr` | 표제란 OCR |
| `pid_connectivity` | P&ID 연결성 |
| `line_detection` | 선 검출 |
| `welding_symbol` | 용접 기호 |
| `surface_roughness` | 표면 거칠기 |
| `quantity_extraction` | 수량 추출 |
| `drawing_region_segmentation` | 영역 세분화 |
| `notes_extraction` | 노트 추출 |
| `revision_comparison` | 리비전 비교 |
| `vlm_auto_classification` | VLM 자동 분류 |

### 검출 분석

```http
POST /analysis/detect/{session_id}
Content-Type: application/json
```

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `confidence_threshold` | float | ❌ | 0.4 | 최소 신뢰도 (0.0-1.0) |
| `iou_threshold` | float | ❌ | 0.5 | NMS IoU 임계값 |
| `max_detections` | int | ❌ | 100 | 최대 검출 수 |

### 검증 큐 조회

```http
GET /verification/queue/{session_id}?item_type=dimension
```

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `item_type` | str | ❌ | "dimension" | dimension, symbol |

### BOM 내보내기

```http
GET /bom/export/{session_id}/{format}
```

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `format` | str | ✅ | excel, csv, json, pdf |

---

## 응답 형식

### 성공 응답

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed"
}
```

### 에러 응답

```json
{
  "success": false,
  "error": "Error message",
  "detail": "Detailed error information"
}
```

---

## 검출 클래스 (27개)

| ID | 클래스명 | 한글명 |
|----|---------|--------|
| 0 | ARRESTER | 피뢰기 |
| 1 | BUS | 모선 |
| 2 | CT | 변류기 |
| 3 | DS | 단로기 |
| 4 | ES | 접지개폐기 |
| 5 | GCB | 가스차단기 |
| 6 | GPT | 접지형계기용변압기 |
| 7 | GS | 가스구간개폐기 |
| 8 | LBS | 부하개폐기 |
| 9 | MOF | 계기용변성기 |
| 10 | OCB | 유입차단기 |
| 11 | PT | 계기용변압기 |
| 12 | RECLOSER | 리클로저 |
| 13 | SC | 직렬콘덴서 |
| 14 | SHUNT_REACTOR | 분로리액터 |
| 15 | SS | 정류기 |
| 16 | TC | 탭절환기 |
| 17 | TR | 변압기 |
| 18 | TVSS | 서지흡수기 |
| 19 | VCB | 진공차단기 |
| 20 | 고장점표시기 | 고장점표시기 |
| 21 | 단로기_1P | 단로기(1P) |
| 22 | 부하개폐기_1P | 부하개폐기(1P) |
| 23 | 접지 | 접지 |
| 24 | 차단기 | 차단기 |
| 25 | 퓨즈 | 퓨즈 |
| 26 | 피뢰기 | 피뢰기 |

---

## 환경 변수

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| `YOLO_CONFIDENCE` | 0.4 | 검출 신뢰도 임계값 |
| `AUTO_APPROVE_THRESHOLD` | 0.9 | 자동 승인 임계값 |
| `CRITICAL_THRESHOLD` | 0.7 | Critical 우선순위 임계값 |
| `FEEDBACK_DATA_PATH` | /data/feedback | 피드백 저장 경로 |
| `YOLO_EXPORT_PATH` | /data/yolo_training | YOLO 내보내기 경로 |

---

## 관련 문서

| 문서 | 설명 |
|------|------|
| [메인 문서](../../../blueprint-ai-bom/docs/README.md) | Blueprint AI BOM 전체 문서 |
| [장기 로드맵](../../../blueprint-ai-bom/docs/features/longterm_features.md) | v10.5 기능 상세 (4/4 완료) |
| [Active Learning](../../../blueprint-ai-bom/docs/features/active_learning.md) | 검증 큐 시스템 |
| [Feedback Pipeline](../../../blueprint-ai-bom/docs/features/feedback_pipeline.md) | YOLO 재학습 |

---

**Swagger UI**: http://localhost:5020/docs
**ReDoc**: http://localhost:5020/redoc
