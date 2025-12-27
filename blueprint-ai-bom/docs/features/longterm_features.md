# 장기 로드맵 기능 (v10.3) - 전체 완료

> **목적**: 도면 분석 고급 기능 - 영역 세분화, 노트 추출, 리비전 비교, VLM 자동 분류
> **상태**: ✅ 전체 구현 완료 (4/4 기능) - 2025-12-27
> **버전**: v10.3

---

## 개요

장기 로드맵 기능은 Blueprint AI BOM의 고급 분석 기능으로, 도면의 세부 구조를 이해하고
메타데이터를 자동으로 추출하여 BOM 생성 품질을 향상시킵니다.

```
도면 업로드 → VLM 분류 → 영역 세분화 → 노트 추출 → 리비전 비교 → BOM 생성
```

---

## 1. 🗺️ 도면 영역 세분화 (`drawing_region_segmentation`) ✅ 완전 구현

> **구현 상태**: ✅ 완전 구현 (2025-12-27)
> **방식**: 휴리스틱 + VLM 하이브리드

### 목적
도면 내 각 뷰(정면도, 측면도, 단면도 등)를 자동으로 구분하여 영역별 분석을 가능하게 합니다.

### 세분화 대상 (11개 영역 타입)

| 영역 타입 | 설명 | 처리 방식 |
|----------|------|----------|
| `TITLE_BLOCK` | 표제란 | 메타데이터 추출 |
| `MAIN_VIEW` | 메인 뷰 | 주요 치수 추출 |
| `BOM_TABLE` | BOM 테이블 | 부품 목록 파싱 |
| `NOTES` | 노트 영역 | 텍스트 추출 |
| `DETAIL_VIEW` | 상세도 | 고해상도 OCR |
| `SECTION_VIEW` | 단면도 | 내부 구조 분석 |
| `DIMENSION_AREA` | 치수 집중 영역 | 치수 OCR 집중 |
| `LEGEND` | 범례 | 심볼 매핑 |
| `REVISION_BLOCK` | 리비전 블록 | 변경 이력 |
| `PARTS_LIST` | 부품 목록 | BOM 파싱 |
| `UNKNOWN` | 미분류 | 일반 처리 |

### 검출 방식

#### 1. 휴리스틱 방식 (기본)
- **위치 기반 추정**: 표제란 (우하단), 노트 (좌하단), BOM (우측) 등
- **이미지 분석**: 엣지 검출, 텍스트 밀도 분석
- **규칙 기반**: 도면 표준 레이아웃 패턴 매칭

#### 2. VLM 방식 (선택)
- **지원 모델**: GPT-4o-mini, GPT-4o, Claude Vision, 로컬 VL API
- **정확도**: 휴리스틱 대비 10-15% 향상
- **비용**: API 호출당 약 $0.01 (gpt-4o-mini 기준)

### API 엔드포인트

```http
POST /analysis/longterm/region-segmentation/{session_id}
Content-Type: application/json

{
  "min_area_ratio": 0.02,
  "enable_vlm": true,
  "vlm_provider": "openai"
}
```

**요청 파라미터**:
| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `min_area_ratio` | float | `0.02` | 최소 영역 크기 비율 (2%) |
| `enable_vlm` | bool | `false` | VLM 하이브리드 모드 활성화 |
| `vlm_provider` | string | `"openai"` | VLM 제공자 (openai, anthropic, local) |

**응답 예시**:
```json
{
  "session_id": "abc-123",
  "regions": [
    {
      "id": "region-001",
      "type": "TITLE_BLOCK",
      "label": "표제란",
      "bbox": [0.7, 0.85, 1.0, 1.0],
      "confidence": 0.95,
      "processing_strategy": "title_block_ocr",
      "metadata": {"position": "bottom_right"}
    },
    {
      "id": "region-002",
      "type": "MAIN_VIEW",
      "label": "메인 뷰",
      "bbox": [0.05, 0.1, 0.65, 0.8],
      "confidence": 0.92,
      "processing_strategy": "dimension_extraction",
      "metadata": {}
    },
    {
      "id": "region-003",
      "type": "NOTES",
      "label": "노트 영역",
      "bbox": [0.02, 0.82, 0.35, 0.98],
      "confidence": 0.88,
      "processing_strategy": "text_extraction",
      "metadata": {}
    }
  ],
  "total_regions": 3,
  "detection_method": "heuristic",
  "processing_time_ms": 450.2
}
```

### 사용 예시

#### cURL
```bash
# 휴리스틱 방식
curl -X POST "http://localhost:5020/analysis/longterm/region-segmentation/your-session-id" \
  -H "Content-Type: application/json" \
  -d '{"min_area_ratio": 0.02}'

# VLM 하이브리드 방식
curl -X POST "http://localhost:5020/analysis/longterm/region-segmentation/your-session-id" \
  -H "Content-Type: application/json" \
  -d '{"enable_vlm": true, "vlm_provider": "openai"}'
```

#### Python
```python
import httpx

async def segment_regions(session_id: str, use_vlm: bool = False):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"http://localhost:5020/analysis/longterm/region-segmentation/{session_id}",
            json={"enable_vlm": use_vlm, "vlm_provider": "openai"}
        )
        return response.json()
```

### 관련 파일

| 파일 | 설명 |
|------|------|
| `backend/schemas/region.py` | `RegionType`, `DetectedRegion` 스키마 |
| `backend/services/region_segmenter.py` | 영역 분할 서비스 (휴리스틱 + VLM) |
| `backend/routers/longterm_router.py` | API 엔드포인트 |
| `frontend/src/config/features/featureDefinitions.ts` | 기능 정의 (SSOT) |

---

## 2. 📋 주석/노트 추출 (`notes_extraction`) ✅ 완전 구현

> **구현 상태**: ✅ 완전 구현 (2025-12-27)
> **지원 모델**: GPT-4o-mini (기본), GPT-4o, Claude Vision

### 목적
도면의 일반 노트 및 특수 지시사항을 추출하고 카테고리별로 분류합니다.

### 노트 카테고리

| 카테고리 | 설명 | 예시 |
|---------|------|------|
| `material` | 재료 사양 | "재질: SUS304" |
| `heat_treatment` | 열처리 | "열처리: HRC 58-62" |
| `surface_finish` | 표면 처리 | "표면처리: 무전해 니켈도금" |
| `tolerance` | 일반 공차 | "일반공차: KS B 0401-m" |
| `assembly` | 조립 지시 | "접착제 도포 후 조립" |
| `inspection` | 검사 요구 | "전수검사 필요" |
| `welding` | 용접 사양 | "TIG 용접" |
| `painting` | 도장 사양 | "분체도장 RAL 7035" |
| `standard` | 적용 규격 | "KS B ISO 286-1" |
| `general` | 기타 일반 | 기타 노트 |

### API 엔드포인트

```http
POST /analysis/notes/{session_id}/extract
Content-Type: application/json

{
  "provider": "openai",
  "use_ocr": true
}
```

**요청 파라미터**:
| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `provider` | string | `"openai"` | LLM 제공자 (openai, anthropic) |
| `use_ocr` | bool | `true` | 기존 OCR 결과 활용 여부 |

**응답 예시**:
```json
{
  "session_id": "abc-123",
  "notes": [
    {
      "id": "note_a1b2c3d4",
      "category": "material",
      "text": "재질: SUS304 (KS D 3698)",
      "confidence": 0.95,
      "bbox": [0.02, 0.85, 0.3, 0.88],
      "source": "llm",
      "verified": false
    },
    {
      "id": "note_e5f6g7h8",
      "category": "tolerance",
      "text": "일반공차: KS B 0401-m",
      "confidence": 0.92,
      "bbox": [0.02, 0.88, 0.25, 0.91],
      "source": "llm",
      "verified": false
    }
  ],
  "total_notes": 2,
  "by_category": {
    "material": 1,
    "tolerance": 1
  },
  "materials": [
    {
      "name": "SUS304",
      "standard": "KS D 3698",
      "grade": "304"
    }
  ],
  "standards": ["KS D 3698", "KS B 0401"],
  "tolerances": {
    "standard": "KS B 0401",
    "class": "m"
  },
  "heat_treatments": [],
  "surface_finishes": [],
  "extraction_provider": "openai",
  "llm_model": "gpt-4o-mini",
  "processing_time_ms": 1850.5
}
```

### 폴백 메커니즘

1. **LLM 실패 시**: 규칙 기반 추출 (정규식 패턴 매칭)
2. **이미지 없을 시**: 기존 OCR 결과에서만 추출

### 지원 패턴 (규칙 기반 폴백)

```python
# 재료 패턴
r'재질\s*[:：]\s*(.+)'
r'(SUS\d{3}[A-Z]?)'
r'(SM\d{2}C)'
r'(AISI\s*\d{4})'

# 열처리 패턴
r'열처리\s*[:：]\s*(.+)'
r'(HRC\s*\d+[-~]\d+)'
r'(침탄|담금질|뜨임|어닐링)'

# 표면처리 패턴
r'표면처리\s*[:：]\s*(.+)'
r'(무전해\s*니켈도금)'
r'(아노다이징|ANODIZING)'

# 공차 패턴
r'일반\s*공차\s*[:：]\s*(.+)'
r'(KS\s*B\s*0401[-\s]*[a-z])'
r'(ISO\s*2768[-\s]*[a-zA-Z]+)'

# 규격 패턴
r'(KS\s*[A-Z]\s*\d+)'
r'(JIS\s*[A-Z]\s*\d+)'
r'(ISO\s*\d+)'
r'(ASTM\s*[A-Z]\d+)'
```

### 관련 파일

| 파일 | 설명 |
|------|------|
| `backend/services/notes_extractor.py` | 노트 추출 서비스 (LLM + 정규식) |
| `backend/routers/longterm_router.py` | API 엔드포인트 |
| `frontend/src/config/features/featureDefinitions.ts` | 기능 정의 (SSOT) |

### 사용 예시

#### cURL
```bash
curl -X POST "http://localhost:5020/analysis/notes/your-session-id/extract" \
  -H "Content-Type: application/json" \
  -d '{"provider": "openai", "use_ocr": true}'
```

#### Python
```python
import httpx

async def extract_notes(session_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"http://localhost:5020/analysis/notes/{session_id}/extract",
            json={"provider": "openai", "use_ocr": True}
        )
        return response.json()
```

---

## 3. 🔄 리비전 비교 (`revision_comparison`) ✅ 완전 구현

> **구현 상태**: ✅ 완전 구현 (2025-12-27)
> **방식**: SSIM 이미지 비교 + 세션 데이터 비교 + VLM 지능형 비교

### 목적
도면 버전 간 변경점을 자동으로 감지하고 하이라이트합니다.

### 비교 방식

#### 1. SSIM 이미지 비교 (기본)
- **Structural Similarity Index**: 두 이미지의 구조적 유사도 측정
- **차이 이미지 생성**: 변경된 영역을 빨간색으로 하이라이트
- **OpenCV 기반**: cv2, scikit-image 활용

#### 2. 세션 데이터 비교 (항상 수행)
- **심볼 비교**: 추가/삭제/변경된 심볼 감지
- **치수 비교**: 변경된 치수값 추적
- **노트 비교**: 재료, 공차 등 노트 변경 감지

#### 3. VLM 지능형 비교 (선택)
- **GPT-4o-mini**: 두 이미지를 동시에 분석하여 변경점 설명
- **멀티 이미지 입력**: 이전/새 리비전 이미지 비교
- **자연어 설명**: 변경 내용의 상세 설명 생성

### 변경 타입

| 타입 | 중요도 | 설명 |
|------|--------|------|
| `added` | 🟢 | 새로 추가된 항목 |
| `removed` | 🔴 | 삭제된 항목 |
| `modified` | 🟡 | 수정된 항목 |
| `moved` | 🔵 | 위치 이동 |

### 변경 카테고리

| 카테고리 | 중요도 | 설명 |
|---------|--------|------|
| `dimension` | CRITICAL | 치수 변경 |
| `tolerance` | CRITICAL | 공차 변경 |
| `geometry` | CRITICAL | 형상 변경 |
| `symbol` | WARNING | 심볼 변경 |
| `note` | WARNING | 노트 변경 |
| `annotation` | INFO | 주석 변경 |
| `title_block` | INFO | 표제란 변경 |

### API 엔드포인트

```http
POST /analysis/revision/compare
Content-Type: application/json

{
  "session_id_old": "abc-123",
  "session_id_new": "def-456",
  "config": {
    "use_vlm": true,
    "compare_dimensions": true,
    "compare_symbols": true,
    "compare_notes": true
  }
}
```

**요청 파라미터**:
| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `session_id_old` | string | 필수 | 이전 리비전 세션 ID |
| `session_id_new` | string | 필수 | 새 리비전 세션 ID |
| `use_vlm` | bool | `false` | VLM 지능형 비교 사용 |
| `compare_dimensions` | bool | `true` | 치수 비교 활성화 |
| `compare_symbols` | bool | `true` | 심볼 비교 활성화 |
| `compare_notes` | bool | `true` | 노트 비교 활성화 |

**응답 예시**:
```json
{
  "comparison_id": "comp-abc123",
  "session_id_old": "session-old-123",
  "session_id_new": "session-new-456",
  "changes": [
    {
      "id": "dim_add_a1b2c3d4",
      "change_type": "added",
      "category": "dimension",
      "description": "치수 추가: 25mm",
      "old_value": null,
      "new_value": "25mm",
      "bbox_old": null,
      "bbox_new": [0.3, 0.4, 0.35, 0.45],
      "confidence": 0.85,
      "severity": "critical"
    },
    {
      "id": "sym_del_e5f6g7h8",
      "change_type": "removed",
      "category": "symbol",
      "description": "심볼 삭제: weld",
      "old_value": "weld",
      "new_value": null,
      "bbox_old": [0.5, 0.6, 0.55, 0.65],
      "bbox_new": null,
      "confidence": 0.9,
      "severity": "warning"
    }
  ],
  "total_changes": 2,
  "by_type": {"added": 1, "removed": 1},
  "by_category": {"dimension": 1, "symbol": 1},
  "added_count": 1,
  "removed_count": 1,
  "modified_count": 0,
  "similarity_score": 0.87,
  "alignment_score": 0.0,
  "diff_image_base64": "iVBORw0KGgo...",
  "comparison_provider": "opencv",
  "processing_time_ms": 1250.5
}
```

### 사용 예시

#### cURL
```bash
# 기본 비교 (SSIM + 데이터)
curl -X POST "http://localhost:5020/analysis/revision/compare" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id_old": "old-session-id",
    "session_id_new": "new-session-id"
  }'

# VLM 지능형 비교 포함
curl -X POST "http://localhost:5020/analysis/revision/compare" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id_old": "old-session-id",
    "session_id_new": "new-session-id",
    "config": {"use_vlm": true}
  }'
```

#### Python
```python
import httpx

async def compare_revisions(session_old: str, session_new: str, use_vlm: bool = False):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:5020/analysis/revision/compare",
            json={
                "session_id_old": session_old,
                "session_id_new": session_new,
                "config": {"use_vlm": use_vlm}
            }
        )
        return response.json()
```

### 관련 파일

| 파일 | 설명 |
|------|------|
| `backend/schemas/longterm.py` | `RevisionChange`, `ChangeType` 스키마 |
| `backend/services/revision_comparator.py` | 리비전 비교 서비스 (SSIM + 데이터 + VLM) |
| `backend/routers/longterm_router.py` | API 엔드포인트 |
| `frontend/src/config/features/featureDefinitions.ts` | 기능 정의 (SSOT) |

---

## 4. 🤖 VLM 자동 분류 (`vlm_auto_classification`) ✅ 완전 구현

> **구현 상태**: ✅ 완전 구현 (2025-12-27)
> **지원 모델**: GPT-4o-mini (기본), GPT-4o, GPT-4-turbo, 로컬 VL API, Claude Vision

### 목적
Vision-Language Model을 사용하여 도면 타입, 산업 분야, 복잡도를 자동으로 분류합니다.

### 지원 VLM 제공자

| Provider | 모델 | 비용 (1M 토큰) | 권장 용도 |
|----------|------|---------------|----------|
| `openai` | gpt-4o-mini | $0.15 / $0.60 | **테스트용 (기본값)** |
| `openai` | gpt-4o | $2.50 / $10.00 | 프로덕션용 |
| `openai` | gpt-4-turbo | $10.00 / $30.00 | 레거시 |
| `local` | BLIP-base | 무료 | 로컬 추론 |
| `anthropic` | Claude 3.5 Sonnet | $3.00 / $15.00 | 고품질 분석 |

### 분류 항목

#### 도면 타입 (DrawingType)

| 타입 | 설명 | 추천 프리셋 |
|------|------|-----------|
| `mechanical_part` | 기계 부품도 | dimension_extraction |
| `pid` | P&ID 배관계장도 | pid_analysis |
| `assembly` | 조립도 | assembly_analysis |
| `electrical` | 전기 회로도 | electrical_analysis |
| `architectural` | 건축 도면 | architectural_analysis |
| `unknown` | 분류 불가 | general |

#### 영역 검출 (RegionType)

| 영역 | 설명 |
|------|------|
| `title_block` | 표제란 (우하단) |
| `main_view` | 메인 도면 영역 |
| `bom_table` | BOM 테이블 |
| `notes` | 주석 영역 |
| `detail_view` | 상세도 |
| `section_view` | 단면도 |
| `dimension_area` | 치수 집중 영역 |

### 환경변수 설정 ⚠️ 중요

```bash
# .env 파일 또는 docker-compose.yml 환경변수

# 필수: OpenAI API 키
OPENAI_API_KEY=sk-your-api-key-here

# 선택: 사용할 모델 (기본값: gpt-4o-mini)
OPENAI_MODEL=gpt-4o-mini

# 선택: VL API URL (로컬 VLM 사용 시)
VL_API_URL=http://vl-api:5004

# 선택: Anthropic API 키 (Claude Vision 사용 시)
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### API 엔드포인트

```http
POST /analysis/vlm-classify/{session_id}
Content-Type: application/json

{
  "provider": "openai",
  "recommend_features": true
}
```

**요청 파라미터**:
| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `provider` | string | `"openai"` | VLM 제공자 (local, openai, anthropic) |
| `recommend_features` | bool | `true` | 기능 추천 포함 여부 |

**응답 예시**:
```json
{
  "session_id": "abc-123",
  "drawing_type": "mechanical_part",
  "drawing_type_confidence": 0.95,
  "industry_domain": "machinery",
  "industry_confidence": 0.76,
  "complexity": "moderate",
  "has_dimensions": true,
  "has_tolerances": true,
  "has_surface_finish": true,
  "has_welding_symbols": true,
  "has_gdt": true,
  "has_bom": false,
  "has_notes": true,
  "has_title_block": true,
  "regions": [
    {
      "region_type": "title_block",
      "bbox": [0.7, 0.85, 1.0, 1.0],
      "confidence": 0.9,
      "description": "표제란 - 도면번호, 품명 포함"
    },
    {
      "region_type": "main_view",
      "bbox": [0.05, 0.1, 0.85, 0.8],
      "confidence": 0.95,
      "description": "정면도 - 주요 치수 포함"
    }
  ],
  "recommended_features": [
    "symbol_detection",
    "dimension_ocr",
    "dimension_verification",
    "gdt_parsing",
    "surface_roughness_parsing",
    "welding_symbol_parsing",
    "bom_generation"
  ],
  "analysis_summary": "기계 부품 도면입니다. GD&T 기호와 다수의 치수 표기가 있습니다.",
  "vlm_provider": "openai",
  "vlm_model": "gpt-4o-mini",
  "processing_time_ms": 2340.5
}
```

### 프리셋 파이프라인 자동 설정

VLM 분류 결과에 따라 최적의 분석 파이프라인이 자동 추천됩니다:

| 도면 타입 | 추천 노드 | 주요 설정 |
|----------|----------|----------|
| mechanical_part | YOLO + eDOCr2 + SkinModel | tolerance_analysis 활성화 |
| pid | YOLO-PID + Line Detector + PID Analyzer | connectivity 활성화 |
| assembly | YOLO + eDOCr2 + VL | part_matching 활성화 |
| electrical | YOLO + OCR Ensemble | circuit_analysis 활성화 |
| architectural | EDGNet + OCR Ensemble | floor_plan_analysis 활성화 |

### 관련 파일

| 파일 | 설명 |
|------|------|
| `backend/services/vlm_classifier.py` | VLM 분류 서비스 (멀티 프로바이더) |
| `backend/routers/longterm_router.py` | API 엔드포인트 |
| `frontend/src/config/features/featureDefinitions.ts` | 기능 정의 (SSOT) |

### 사용 예시

#### cURL
```bash
# 세션 생성 후 VLM 분류 실행
curl -X POST "http://localhost:5020/analysis/vlm-classify/your-session-id" \
  -H "Content-Type: application/json" \
  -d '{"provider": "openai", "recommend_features": true}'
```

#### Python
```python
import httpx

async def classify_drawing(session_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"http://localhost:5020/analysis/vlm-classify/{session_id}",
            json={"provider": "openai", "recommend_features": True}
        )
        return response.json()
```

### 폴백 순서

VLM 분류 시 지정된 프로바이더가 실패하면 자동으로 다음 순서로 폴백됩니다:

1. **openai 지정 시**: openai → anthropic → local
2. **local 지정 시**: local → openai → anthropic
3. **anthropic 지정 시**: anthropic → openai → local

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
# ============================================================
# VLM 자동 분류 설정 (v10.0)
# ============================================================

# OpenAI API (필수 - VLM 분류 사용 시)
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o-mini    # gpt-4o-mini (기본), gpt-4o, gpt-4-turbo

# Anthropic API (선택 - Claude Vision 사용 시)
ANTHROPIC_API_KEY=sk-ant-your-key-here

# 로컬 VL API (선택 - 로컬 VLM 사용 시)
VL_API_URL=http://vl-api:5004

# ============================================================
# 기타 설정
# ============================================================

# 영역 세분화
MIN_REGION_SIZE=0.02
MERGE_OVERLAPPING=true

# 리비전 비교
COMPARISON_SENSITIVITY=0.8
```

### Docker Compose 예시

```yaml
# docker-compose.override.yml
services:
  blueprint-ai-bom:
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENAI_MODEL=gpt-4o-mini
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

**최초 구현일**: 2025-12-24 (API 스텁)
**VLM 완전 구현일**: 2025-12-27
**노트 추출 완전 구현일**: 2025-12-27
**영역 세분화 완전 구현일**: 2025-12-27
**리비전 비교 완전 구현일**: 2025-12-27
**버전**: v10.3 (전체 완료)
