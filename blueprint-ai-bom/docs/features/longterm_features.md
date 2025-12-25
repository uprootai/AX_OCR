# 장기 로드맵 기능 (v9.0)

> **목적**: 도면 분석 고급 기능 - 영역 세분화, 노트 추출, 리비전 비교, VLM 자동 분류
> **상태**: ✅ 구현 완료 (2025-12-24)
> **버전**: v9.0

---

## 개요

장기 로드맵 기능은 Blueprint AI BOM의 고급 분석 기능으로, 도면의 세부 구조를 이해하고
메타데이터를 자동으로 추출하여 BOM 생성 품질을 향상시킵니다.

```
도면 업로드 → VLM 분류 → 영역 세분화 → 노트 추출 → 리비전 비교 → BOM 생성
```

---

## 1. 🗺️ 도면 영역 세분화 (`drawing_region_segmentation`)

### 목적
도면 내 각 뷰(정면도, 측면도, 단면도 등)를 자동으로 구분하여 영역별 분석을 가능하게 합니다.

### 세분화 대상

| 영역 타입 | 설명 | 처리 방식 |
|----------|------|----------|
| `FRONT_VIEW` | 정면도 | 주요 치수 추출 |
| `SIDE_VIEW` | 측면도 | 깊이/폭 치수 추출 |
| `TOP_VIEW` | 평면도 | 레이아웃 분석 |
| `SECTION_VIEW` | 단면도 | 내부 구조 분석 |
| `DETAIL_VIEW` | 상세도 | 고해상도 OCR |
| `TITLE_BLOCK` | 표제란 | 메타데이터 추출 |
| `BOM_TABLE` | BOM 테이블 | 부품 목록 파싱 |
| `NOTES_AREA` | 노트 영역 | 텍스트 추출 |

### API 엔드포인트

```http
POST /analysis/longterm/region-segmentation/{session_id}
Content-Type: application/json

{
  "min_region_size": 0.02,
  "merge_overlapping": true
}
```

**응답**:
```json
{
  "regions": [
    {
      "id": "region-001",
      "type": "FRONT_VIEW",
      "confidence": 0.92,
      "bbox": [100, 200, 500, 600],
      "verified": false
    }
  ],
  "total_regions": 6
}
```

### 관련 파일

| 파일 | 설명 |
|------|------|
| `backend/schemas/longterm.py` | `DrawingRegion`, `ViewType` 스키마 |
| `backend/services/region_segmenter.py` | 영역 분할 서비스 |
| `frontend/src/components/RegionEditor.tsx` | 영역 편집 UI |

---

## 2. 📋 주석/노트 추출 (`notes_extraction`)

### 목적
도면의 일반 노트 및 특수 지시사항을 추출하고 카테고리별로 분류합니다.

### 노트 카테고리

| 카테고리 | 설명 | 예시 |
|---------|------|------|
| `MATERIAL` | 재료 사양 | "재질: SUS304" |
| `HEAT_TREATMENT` | 열처리 | "열처리: HRC 58-62" |
| `SURFACE_FINISH` | 표면 처리 | "표면처리: 무전해 니켈도금" |
| `TOLERANCE` | 일반 공차 | "일반공차: KS B 0401-m" |
| `ASSEMBLY` | 조립 지시 | "접착제 도포 후 조립" |
| `INSPECTION` | 검사 요구 | "전수검사 필요" |
| `GENERAL` | 기타 일반 | 기타 노트 |

### API 엔드포인트

```http
POST /analysis/longterm/notes-extraction/{session_id}
Content-Type: application/json

{
  "include_general": true,
  "min_confidence": 0.7
}
```

**응답**:
```json
{
  "notes": [
    {
      "id": "note-001",
      "category": "MATERIAL",
      "text": "재질: SUS304",
      "confidence": 0.95,
      "bbox": [50, 800, 200, 830],
      "verified": false
    }
  ],
  "category_counts": {
    "MATERIAL": 2,
    "HEAT_TREATMENT": 1,
    "SURFACE_FINISH": 1
  }
}
```

### 관련 파일

| 파일 | 설명 |
|------|------|
| `backend/schemas/longterm.py` | `ExtractedNote`, `NoteCategory` 스키마 |
| `backend/services/notes_extractor.py` | 노트 추출 서비스 |

---

## 3. 🔄 리비전 비교 (`revision_comparison`)

### 목적
도면 버전 간 변경점을 자동으로 감지하고 하이라이트합니다.

### 변경 타입

| 타입 | 색상 | 설명 |
|------|------|------|
| `ADDED` | 🟢 녹색 | 새로 추가된 항목 |
| `DELETED` | 🔴 빨강 | 삭제된 항목 |
| `MODIFIED` | 🟡 노랑 | 수정된 항목 |
| `MOVED` | 🔵 파랑 | 위치 이동 |

### 변경 카테고리

| 카테고리 | 설명 |
|---------|------|
| `GEOMETRY` | 형상 변경 |
| `DIMENSION` | 치수 변경 |
| `NOTE` | 노트 변경 |
| `SYMBOL` | 심볼 변경 |
| `TITLE_BLOCK` | 표제란 변경 |

### API 엔드포인트

```http
POST /analysis/longterm/revision-compare
Content-Type: application/json

{
  "session_id_old": "abc-123",
  "session_id_new": "def-456",
  "comparison_method": "structural",
  "sensitivity": 0.8
}
```

**응답**:
```json
{
  "changes": [
    {
      "id": "change-001",
      "type": "MODIFIED",
      "category": "DIMENSION",
      "old_value": "100mm",
      "new_value": "105mm",
      "bbox_old": [200, 300, 250, 320],
      "bbox_new": [200, 300, 255, 320],
      "significance": "major"
    }
  ],
  "summary": {
    "total_changes": 5,
    "added": 1,
    "deleted": 0,
    "modified": 4
  }
}
```

### 관련 파일

| 파일 | 설명 |
|------|------|
| `backend/schemas/longterm.py` | `RevisionChange`, `ChangeType` 스키마 |
| `backend/services/revision_comparator.py` | 리비전 비교 서비스 |

---

## 4. 🤖 VLM 자동 분류 (`vlm_auto_classification`)

### 목적
Vision-Language Model을 사용하여 도면 타입, 산업 분야, 복잡도를 자동으로 분류합니다.

### 분류 항목

#### 도면 타입 (DrawingType)

| 타입 | 설명 |
|------|------|
| `MECHANICAL` | 기계 도면 |
| `ELECTRICAL` | 전기 도면 |
| `PID` | P&ID 도면 |
| `ARCHITECTURAL` | 건축 도면 |
| `PCB` | PCB 도면 |
| `OTHER` | 기타 |

#### 산업 분야 (IndustryDomain)

| 분야 | 설명 |
|------|------|
| `MANUFACTURING` | 제조업 |
| `ENERGY` | 에너지 |
| `CONSTRUCTION` | 건설 |
| `ELECTRONICS` | 전자 |
| `AUTOMOTIVE` | 자동차 |
| `OTHER` | 기타 |

#### 복잡도 (ComplexityLevel)

| 레벨 | 설명 | 예상 심볼 수 |
|------|------|-------------|
| `SIMPLE` | 단순 | < 10 |
| `MODERATE` | 보통 | 10-50 |
| `COMPLEX` | 복잡 | 50-100 |
| `VERY_COMPLEX` | 매우 복잡 | > 100 |

### API 엔드포인트

```http
POST /analysis/longterm/vlm-classification/{session_id}
Content-Type: application/json

{
  "vlm_provider": "local",
  "include_recommendations": true
}
```

**응답**:
```json
{
  "classification": {
    "drawing_type": "MECHANICAL",
    "industry_domain": "MANUFACTURING",
    "complexity_level": "MODERATE",
    "confidence": 0.89
  },
  "recommended_features": [
    "symbol_detection",
    "dimension_ocr",
    "gdt_parsing"
  ],
  "analysis_notes": "기계 가공 부품 도면으로 판단됨. GD&T 기호 다수 포함."
}
```

### 관련 파일

| 파일 | 설명 |
|------|------|
| `backend/schemas/longterm.py` | `VLMClassificationResult` 스키마 |
| `backend/services/vlm_classifier.py` | VLM 분류 서비스 |
| `frontend/src/pages/WorkflowPage.tsx` | VLM 분류 UI 섹션 |

---

## 프론트엔드 UI

### WorkflowPage 통합

각 장기 로드맵 기능은 WorkflowPage의 해당 섹션에서 사용할 수 있습니다:

1. **🗺️ 도면 영역 세분화** 섹션
   - 감지된 영역 시각화
   - 영역 타입 편집
   - 바운딩 박스 조정

2. **📋 주석/노트** 섹션
   - 추출된 노트 목록
   - 카테고리별 필터링
   - 텍스트 편집

3. **🔄 리비전 비교** 섹션
   - 변경점 오버레이
   - 변경 타입별 필터링
   - Before/After 비교 뷰

4. **🤖 VLM 분류** 섹션
   - 분류 결과 표시
   - 추천 기능 목록
   - 수동 분류 재정의

---

## 스키마 정의

### 주요 스키마 (`backend/schemas/longterm.py`)

```python
# 영역 세분화
class ViewType(str, Enum):
    FRONT_VIEW = "front_view"
    SIDE_VIEW = "side_view"
    TOP_VIEW = "top_view"
    SECTION_VIEW = "section_view"
    DETAIL_VIEW = "detail_view"
    TITLE_BLOCK = "title_block"
    BOM_TABLE = "bom_table"
    NOTES_AREA = "notes_area"

class DrawingRegion(BaseModel):
    id: str
    type: ViewType
    bbox: List[float]
    confidence: float
    verified: bool = False

# 노트 추출
class NoteCategory(str, Enum):
    MATERIAL = "material"
    HEAT_TREATMENT = "heat_treatment"
    SURFACE_FINISH = "surface_finish"
    TOLERANCE = "tolerance"
    ASSEMBLY = "assembly"
    INSPECTION = "inspection"
    GENERAL = "general"

class ExtractedNote(BaseModel):
    id: str
    category: NoteCategory
    text: str
    confidence: float
    bbox: List[float]
    verified: bool = False

# 리비전 비교
class ChangeType(str, Enum):
    ADDED = "added"
    DELETED = "deleted"
    MODIFIED = "modified"
    MOVED = "moved"

class RevisionChange(BaseModel):
    id: str
    type: ChangeType
    category: str
    old_value: Optional[str]
    new_value: Optional[str]
    bbox_old: Optional[List[float]]
    bbox_new: Optional[List[float]]

# VLM 분류
class DrawingClassification(str, Enum):
    MECHANICAL = "mechanical"
    ELECTRICAL = "electrical"
    PID = "pid"
    ARCHITECTURAL = "architectural"
    PCB = "pcb"
    OTHER = "other"

class VLMClassificationResult(BaseModel):
    drawing_type: DrawingClassification
    industry_domain: str
    complexity_level: str
    confidence: float
    recommended_features: List[str]
```

---

## 18개 기능 체크박스

ImageInput 노드에서 다음 18개 기능을 선택할 수 있습니다 (v8.1에서 툴팁 추가):

| # | 기능 ID | 기능명 | 설명 |
|---|---------|--------|------|
| 1 | `symbol_detection` | 심볼 검출 | YOLO 딥러닝 모델로 14가지 심볼 자동 검출 |
| 2 | `symbol_verification` | 심볼 검증 | Human-in-the-Loop 승인/거부/수정 |
| 3 | `dimension_ocr` | 치수 OCR | 치수값 텍스트 인식 및 단위 파싱 |
| 4 | `dimension_verification` | 치수 검증 | OCR 결과 검증 |
| 5 | `gdt_parsing` | GD&T 파싱 | 기하공차 기호 및 데이텀 파싱 |
| 6 | `relation_extraction` | 관계 추출 | 치수-심볼 연결 관계 분석 |
| 7 | `gt_comparison` | GT 비교 | Ground Truth 비교 (정밀도/재현율) |
| 8 | `bom_generation` | BOM 생성 | AI 기반 부품 목록 생성 |
| 9 | `title_block_ocr` | 표제란 OCR | 도면번호, 리비전, 작성자 추출 |
| 10 | `pid_connectivity` | P&ID 연결성 | 기기 간 연결 관계 분석 |
| 11 | `line_detection` | 선 검출 | 배관/전선 추적 |
| 12 | `welding_symbol` | 용접 기호 | 용접 사양 파싱 |
| 13 | `surface_roughness` | 표면 거칠기 | Ra/Rz 값 추출 |
| 14 | `quantity_extraction` | 수량 추출 | 부품 수량 자동 인식 |
| 15 | `drawing_region_segmentation` | 영역 세분화 | 도면 뷰 자동 구분 |
| 16 | `notes_extraction` | 노트 추출 | 일반 노트/지시사항 추출 |
| 17 | `revision_comparison` | 리비전 비교 | 버전 간 변경점 감지 |
| 18 | `vlm_auto_classification` | VLM 자동 분류 | 도면 타입/산업분야 AI 분류 |

---

## 성능 지표

| 기능 | 처리 시간 | 정확도 |
|------|----------|--------|
| 영역 세분화 | ~2초 | ~90% |
| 노트 추출 | ~1초 | ~85% |
| 리비전 비교 | ~3초 | ~92% |
| VLM 분류 | ~1초 (로컬) | ~88% |

---

## 환경 변수

```bash
# VLM 설정
VLM_PROVIDER=local  # local, openai, anthropic
VLM_MODEL=qwen2-vl-7b

# 영역 세분화
MIN_REGION_SIZE=0.02
MERGE_OVERLAPPING=true

# 리비전 비교
COMPARISON_SENSITIVITY=0.8
```

---

## 관련 문서

| 문서 | 설명 |
|------|------|
| [Active Learning](active_learning.md) | 검증 큐 시스템 |
| [Feedback Pipeline](feedback_pipeline.md) | YOLO 재학습 |
| [GD&T Parser](gdt_parser.md) | 기하공차 파싱 |
| [로드맵](../../../.todos/2025-12-24_blueprint_ai_bom_feature_roadmap.md) | 전체 기능 로드맵 |

---

**구현일**: 2025-12-24
**버전**: v9.0
