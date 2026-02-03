# 치수 전용 워크플로우 — 일반 텍스트 OCR 강화 실험 계획

> 날짜: 2026-02-03
> 목표: DSE Bearing 워크플로우에서 치수 외 일반 텍스트(한글/영어) 인식률 개선

---

## 1. 현재 상태 분석

### 1.1 문제점

DSE Bearing 1-1 워크플로우에서 **치수(숫자/기호)는 eDOCr2+PaddleOCR로 잘 인식**되지만, 도면 내 **일반 텍스트는 전혀 인식되지 않음**.

| 영역 | 못 잡는 것 | 원인 |
|------|----------|------|
| NOTES 영역 | 재료, 공차, 가공방법 등 영문 텍스트 | 치수 OCR만 실행 |
| 표제란 (Title Block) | DOOSAN Enerbility, BEARING ASSY, 도면번호 | 표제란 OCR 미실행 (수동 버튼) |
| 뷰 라벨 | GEN SIDE, TBN SIDE, SECTION E-3, ISO VIEW | 인식 대상 아님 |
| 테이블 셀 | BEAAING→BEARING, 3ING→RING 등 OCR 오류 | Table Detector 내장 OCR 품질 낮음 |

### 1.2 DSE Bearing 6개 템플릿 현황

| # | 템플릿 | 노드 구성 | 현재 사용 OCR | 일반 텍스트 처리 |
|---|--------|----------|-------------|----------------|
| 1-1 | 도면 분석 + AI BOM | ImageInput → TableDetector → eDOCr2 → AI BOM → SkinModel | eDOCr2 + PaddleOCR(tiled) | Table Detector가 paddle로 테이블 셀 OCR |
| 2-1 | Ring ASSY | ESRGAN → TableDetector → eDOCr2 → AI BOM → SkinModel | eDOCr2 + PaddleOCR | ESRGAN 업스케일 후 테이블 OCR |
| 2-2 | Casing ASSY | ESRGAN → TableDetector → eDOCr2 → AI BOM → SkinModel | eDOCr2 + PaddleOCR | 동일 |
| 2-3 | Thrust Bearing | ESRGAN → VL → TableDetector → eDOCr2 → AI BOM → SkinModel → Merge | eDOCr2 + PaddleOCR + VLM | VLM이 구조 분석 텍스트 보완 |
| 2-8 | YOLO Parts List | YOLO → TableDetector → AI BOM | PaddleOCR (TableDetector 내장) | YOLO로 text_block 영역 검출 |
| 3-2 | 완전 자동 견적 | TitleBlock → PartsList → eDOCr2 → DimensionParser → AI BOM → BOMMatcher → QuoteGenerator | eDOCr2 + PaddleOCR | TitleBlock/PartsList 전용 노드 (미구현) |

### 1.3 사용 가능한 OCR API (9개)

| API | 포트 | 강점 | 일반 텍스트 품질 | 한국어 | 속도 |
|-----|------|------|----------------|--------|------|
| **eDOCr2** | 5002 | 치수/GD&T 특화 | 낮음 (치수 전용) | ko+en | 보통 |
| **PaddleOCR** | 5006 | 범용, v5 | **높음** | ✓✓ | 빠름 |
| **Tesseract** | 5008 | 문서 OCR | 중간 | ✓ | 매우 빠름 |
| **TrOCR** | 5009 | 필기체 | 중간 (인쇄체도 가능) | △ | 느림 |
| **EasyOCR** | 5015 | 80+ 언어 | **높음** | ✓✓✓ | 보통 |
| **Surya OCR** | 5013 | 90+ 언어, 레이아웃 | 높음 | ✓✓ | 느림 |
| **DocTR** | 5014 | 2단계 파이프라인 | 높음 | ✓ | 보통 |
| **OCR Ensemble** | 5011 | 4엔진 투표 | **매우 높음** | ✓✓ | 느림 |
| **Table Detector** | 5022 | 테이블 구조 추출 | 중간 (내장 OCR 의존) | ✓ | 보통 |

---

## 2. 실험 설계

### 실험 우선순위

| 순위 | 실험 | 영향도 | 난이도 | 변경 파일 |
|------|------|--------|--------|----------|
| **E1** | Table Detector OCR 엔진 교체/보정 | **높음** | 낮음 | table_service.py, core_router.py |
| **E2** | 표제란 OCR 자동 실행 | 중간 | 중간 | core_router.py, session_router.py |
| **E3** | NOTES 텍스트 추출 | 중간 | 중간 | table_service.py |
| **E4** | 뷰 라벨 인식 | 낮음 | 높음 | 신규 서비스 필요 |

---

### E1: Table Detector OCR 품질 개선

**현재**: Table Detector가 `ocr_engine: 'paddle'`로 테이블 셀 텍스트를 인식하지만 오류 있음:
- `BEAAING` → `BEARING` (A/R 혼동)
- `3ING` → `RING` (3/R 혼동)
- `SF440A` → `SF4404` (A/4 혼동)

**실험 방법**:

#### E1-A: EasyOCR 엔진으로 교체
```
table_service.py → _call_api() → ocr_engine='easyocr'
```
- EasyOCR은 한글/영어 혼합에 강함
- Table Detector API가 이미 `easyocr` 옵션 지원

#### E1-B: 다중 엔진 후처리
```
1. Table Detector로 테이블 구조 추출 (셀 bbox 확보)
2. 각 셀 이미지를 EasyOCR/PaddleOCR/Tesseract 3개로 재OCR
3. 다수결 투표로 최종 텍스트 결정
```

#### E1-C: Table Detector 파라미터 튜닝
```
confidence_threshold: 0.5 → 0.3 (더 많은 셀 검출)
min_confidence: 50 → 30 (저신뢰도 텍스트도 캡처)
```

**측정**: DSE Bearing ASSY 도면의 Parts List 테이블에서:
- 인식 정확도 (글자 단위)
- 부품명 정확도 (항목 단위)
- 처리 시간

**구현 파일**:
- `blueprint-ai-bom/backend/services/table_service.py` — OCR 엔진 파라미터 변경
- `blueprint-ai-bom/backend/routers/analysis/core_router.py` — 텍스트 추출 시 엔진 선택

---

### E2: 표제란 OCR 자동 실행

**현재**: `title_block_ocr` feature가 있어도 수동 버튼으로만 실행 가능

**실험 방법**:

#### E2-A: 분석 파이프라인에 표제란 OCR 추가
```python
# core_router.py → run_analysis()
if options.enable_text_extraction:
    # 기존: table_service.extract_tables()만 실행
    # 추가: 표제란 영역을 별도 OCR로 처리
    title_block_region = _crop_title_block(image_path)  # (55%, 65%) ~ (100%, 100%)
    title_text = await _ocr_region(title_block_region, engine='paddleocr')
```

#### E2-B: Table Detector 크롭 영역에 이미 포함
현재 `table_service.py`가 이미 `title_block` 영역을 크롭하여 Table Detector에 보냄.
→ Table Detector가 테이블이 아닌 텍스트도 반환하는지 확인
→ 반환하지 않으면 별도 OCR 파이프라인 추가

**구현 파일**:
- `blueprint-ai-bom/backend/services/table_service.py` — 표제란 텍스트 추출 메서드 추가
- `blueprint-ai-bom/backend/routers/analysis/core_router.py` — 자동 실행 로직
- `blueprint-ai-bom/backend/schemas/session.py` — title_block_text 필드

---

### E3: NOTES 텍스트 추출

**현재**: NOTES 영역 (보통 좌하단 또는 우하단)의 텍스트가 전혀 추출되지 않음

**실험 방법**:

#### E3-A: NOTES 영역 크롭 + 범용 OCR
```python
# table_service.py에 NOTES 크롭 영역 추가
_CROP_REGIONS = {
    "title_block":      (0.55, 0.65, 1.0, 1.0),
    "revision_table":   (0.55, 0.0, 1.0, 0.20),
    "parts_list_right": (0.60, 0.20, 1.0, 0.65),
    "notes_area":       (0.0, 0.65, 0.55, 1.0),    # 좌하단 NOTES 영역 (신규)
}
```
- PaddleOCR 또는 EasyOCR로 텍스트 블록 추출
- 테이블이 아닌 자유 텍스트 → 텍스트 라인 추출 모드 사용

#### E3-B: Surya OCR 레이아웃 분석
```
Surya OCR의 detect_layout=true 옵션으로 NOTES 영역 자동 감지
→ 감지된 텍스트 영역만 OCR 실행
```

**구현 파일**:
- `blueprint-ai-bom/backend/services/table_service.py` — NOTES 크롭 영역 및 OCR
- `blueprint-ai-bom/backend/routers/analysis/core_router.py` — 결과 세션 저장

---

### E4: 뷰 라벨 인식

**현재**: GEN SIDE, TBN SIDE, SECTION E-3 등 뷰 라벨이 인식되지 않음

**실험 방법**: 뷰 라벨은 도면 전체에 분산되어 있어 영역 크롭이 어려움
→ YOLO text_block 검출 + OCR 조합 또는 전체 이미지 OCR에서 필터링

**우선순위 낮음** — E1~E3 완료 후 검토

---

## 3. 구현 계획

### Phase 1: E1 — Table Detector OCR 개선 (즉시 실행)

#### Step 1: table_service.py에 OCR 엔진 선택 옵션 추가
```python
# extract_tables() 시그니처에 ocr_engine 파라미터 추가
async def extract_tables(self, image_path, mode='extract',
                         ocr_engine='paddle',  # 기존
                         enable_cell_reocr=False,  # 신규: 셀 재OCR
                         ...):
```

#### Step 2: 셀 재OCR 파이프라인 추가
Table Detector가 반환한 테이블의 각 셀 텍스트를 EasyOCR로 재인식:
```python
async def _reocr_table_cells(self, table_data, image_path):
    """Table Detector 결과의 셀 텍스트를 EasyOCR로 재인식"""
    for row in table_data['data']:
        for i, cell_text in enumerate(row):
            if cell_text and len(cell_text) > 1:
                # EasyOCR로 재인식
                reocr_text = await self._ocr_cell(cell_bbox, image_path, engine='easyocr')
                if reocr_text and confidence > 0.8:
                    row[i] = reocr_text
```

#### Step 3: core_router.py에서 세션 features 기반 엔진 선택
```python
# features에 table_extraction이 있으면
if 'table_extraction' in features:
    result = await table_service.extract_tables(
        image_path,
        ocr_engine='paddle',
        enable_cell_reocr=True,  # 셀 재OCR 활성화
    )
```

#### Step 4: 검증
- DSE Bearing ASSY 도면으로 테스트
- Parts List 테이블 셀 텍스트 정확도 비교 (before/after)

### Phase 2: E2 — 표제란 자동 OCR (E1 완료 후)

#### Step 1: table_service.py에 표제란 텍스트 추출 메서드 추가
```python
async def extract_title_block_text(self, image_path) -> dict:
    """표제란 영역의 텍스트 추출 (비테이블)"""
    crop = self._crop_region(image_path, "title_block")
    # PaddleOCR로 텍스트 추출 (테이블 아닌 일반 텍스트)
    result = await self._call_paddleocr(crop)
    return {
        "drawing_number": ...,
        "title": ...,
        "company": ...,
        "raw_text": result
    }
```

#### Step 2: core_router.py에서 자동 실행
```python
if options.enable_text_extraction:
    # 기존 테이블 추출
    table_result = await table_service.extract_tables(...)
    # 신규: 표제란 텍스트 추출
    title_block_text = await table_service.extract_title_block_text(image_path)
    session_service.update_session(session_id, title_block_text=title_block_text)
```

### Phase 3: E3 — NOTES 텍스트 (E2 완료 후)

기존 `_CROP_REGIONS`에 `notes_area` 추가하여 OCR 실행.

---

## 4. 측정 기준

| 메트릭 | 현재 | 목표 |
|--------|------|------|
| 테이블 셀 텍스트 정확도 | ~85% | >95% |
| 표제란 텍스트 인식 | 0% (미실행) | >90% |
| NOTES 텍스트 인식 | 0% (미실행) | >80% |
| 처리 시간 증가 | 기준 | <30% 증가 |

---

## 5. 리스크 및 제약

| 리스크 | 완화 방안 |
|--------|----------|
| EasyOCR API 미기동 | healthcheck 후 fallback to paddle |
| 셀 재OCR로 처리 시간 증가 | 셀 단위 병렬 처리, confidence > 0.9 셀은 스킵 |
| 크롭 영역이 도면마다 다름 | 다수 DSE Bearing 도면으로 검증, 영역 비율 조정 가능 |
| GPU 메모리 부족 | EasyOCR은 CPU도 가능, 순차 실행으로 메모리 절감 |

---

*작성: 2026-02-03*
*관련 백로그: `.todo/BACKLOG.md` P2-0*
