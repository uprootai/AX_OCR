---
sidebar_position: 3
title: 내보내기 형식
description: BOM 및 견적 내보내기 형식 - Excel, JSON, PDF
---

# 내보내기 형식 (Export Formats)

BOM 시스템은 다양한 용도에 맞는 여러 내보내기 형식을 지원합니다. 각 형식에는 검출 결과, 치수, 단가 및 검증 상태를 포함한 전체 BOM 데이터가 담겨 있습니다.

## 형식 비교

| 기능 | Excel (.xlsx) | JSON (.json) | PDF (.pdf) |
|------|:------------:|:------------:|:----------:|
| 구조화된 BOM 테이블 | 예 | 예 | 예 |
| 단가 내역 | 예 | 예 | 예 |
| 도면 이미지 | 아니오 | 아니오 | 예 |
| 검출 오버레이 | 아니오 | 아니오 | 예 |
| 기계 판독 가능 | 부분적 | 예 | 아니오 |
| 사람 판독 가능 | 예 | 부분적 | 예 |
| 편집 가능 | 예 | 예 | 아니오 |
| 자체 완결형 | 예 | 예 | 예 |
| 일반적 파일 크기 | 50-200 KB | 20-100 KB | 500 KB - 2 MB |
| 주요 용도 | 구매/조달 | API 연동 | 고객용 견적서 |

## Excel 내보내기

Excel 내보내기는 구매 및 제조 워크플로에 맞게 구성된 BOM 데이터 워크북을 생성합니다.

### 시트 구조

**시트 1: BOM**

| 컬럼 | 설명 | 예시 |
|------|------|------|
| No. | 항목 번호 | 1 |
| Part Number | 도면 품번 | T1-001 |
| Description | 부품명 | T1 BEARING ASSY |
| Material | 재질 사양 | SCM440+QT |
| Size | 치수 사양 | OD670XID440X29.5T |
| Quantity | 수량 | 2 |
| Unit | 단위 | EA |
| Unit Price | 단가 | 485,000 |
| Total Price | 수량 x 단가 | 970,000 |
| Verification | 검증 상태 | Approved |

**시트 2: 원가 내역 (단가 포함 시)**

| 컬럼 | 설명 |
|------|------|
| Description | 부품명 |
| Weight (kg) | 계산된 중량 |
| Material Cost | 원재료비 |
| Machining Cost | 가공비 |
| Treatment Cost | 열처리/표면 처리비 |
| Setup Cost | 셋업/공구비 |
| Inspection Cost | 품질 검사비 |
| Transport Cost | 물류비 |
| Subtotal | 항목 합계 |
| Cost Source | calculated / estimated / catalog |

### 내보내기 엔드포인트

```
GET /export/excel/{session_id}
```

## JSON 내보내기

JSON 형식은 API 연동 및 프로그래밍 방식 처리를 위한 전체 BOM 데이터 구조를 제공합니다.

### 응답 구조

```json
{
  "session_id": "abc-123",
  "filename": "drawing-001.png",
  "drawing_type": "electrical",
  "created_at": "2026-02-22T10:30:00Z",
  "bom": {
    "items": [
      {
        "id": "item-001",
        "part_number": "T1-001",
        "description": "T1 BEARING ASSY",
        "material": "SCM440+QT",
        "size": "OD670XID440X29.5T",
        "quantity": 2,
        "unit": "EA",
        "class_name": "BEARING",
        "confidence": 0.92,
        "verification_status": "approved",
        "pricing": {
          "unit_price": 485000,
          "total_price": 970000,
          "cost_breakdown": {
            "weight_kg": 45.2,
            "material_cost": 356400,
            "machining_cost": 120000,
            "treatment_cost": 36160,
            "setup_cost": 0,
            "inspection_cost": 25630,
            "transport_cost": 4520,
            "subtotal": 970000,
            "cost_source": "calculated"
          }
        },
        "dimensions": {
          "od": 670,
          "id": 440,
          "length": 29.5
        },
        "bbox": { "x1": 100, "y1": 200, "x2": 300, "y2": 350 }
      }
    ],
    "summary": {
      "total_items": 15,
      "total_cost": 8500000,
      "currency": "KRW"
    }
  },
  "detections": [...],
  "dimensions": [...]
}
```

### 내보내기 엔드포인트

```
GET /export/json/{session_id}
```

## PDF 내보내기

PDF 형식은 고객에게 전달할 수 있는 포맷된 견적서를 생성합니다. 상세 레이아웃 정보는 [PDF 보고서](./pdf-report.md)를 참조하세요.

### 내보내기 엔드포인트

```
GET /export/pdf/{session_id}
POST /quotation/generate/{session_id}
```

## 자체 완결형 내보내기 패키지

보관 및 오프라인 검토를 위해 시스템은 자체 완결형 내보내기 패키지를 생성할 수 있습니다:

```
export-package/
  ├── bom.xlsx           # BOM 스프레드시트
  ├── bom.json           # 기계 판독용 BOM
  ├── quotation.pdf      # 포맷된 견적서
  ├── drawing.png        # 원본 도면 이미지
  ├── detection.png      # 검출 오버레이가 포함된 도면
  └── metadata.json      # 세션 및 분석 메타데이터
```

### 패키지 내보내기 엔드포인트

```
POST /export/package/{session_id}
```

모든 내보내기 파일이 포함된 ZIP 아카이브를 반환합니다.

## 세션 입출력

내보내기 외에도, 시스템은 백업 및 이관을 위한 세션 가져오기/내보내기를 지원합니다:

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/session/export/{session_id}` | GET | 전체 세션 상태 내보내기 |
| `/session/import` | POST | 내보낸 데이터에서 세션 가져오기 |
| `/project/export/{project_id}` | GET | 프로젝트 내 모든 세션 내보내기 |
| `/project/import` | POST | 모든 세션 포함 프로젝트 가져오기 |
