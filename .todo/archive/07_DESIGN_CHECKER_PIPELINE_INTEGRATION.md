# Design Checker Pipeline 통합 작업

> 생성일: 2026-01-05
> 관련 커밋: P3-1 YOLO 통합, P3-2 eDOCr2 통합

## 개요

Design Checker API에 YOLO + eDOCr2 통합 파이프라인이 추가되었습니다.
이 패턴은 다른 API들에도 적용될 수 있으며, 일관성을 위해 검토가 필요합니다.

---

## 1. 새로 추가된 파일들 (Untracked)

### 1.1 서비스 레이어 (`models/design-checker-api/services/`)

| 파일 | 설명 | 크기 |
|------|------|------|
| `__init__.py` | 서비스 모듈 내보내기 | 598B |
| `yolo_service.py` | YOLO API 연동 (httpx) | 10.6KB |
| `edocr2_service.py` | eDOCr2 API 연동 | 11.9KB |
| `ocr_service.py` | PaddleOCR API 연동 | 3.8KB |
| `tag_extractor.py` | 정규식 기반 태그 추출 | 13.9KB |
| `equipment_mapping.py` | 장비명 매핑 | 28.3KB |
| `excel_report.py` | Excel 리포트 생성 | 15.2KB |
| `pdf_report.py` | PDF 리포트 생성 | 17.4KB |

### 1.2 라우터 (`models/design-checker-api/routers/`)

| 파일 | 엔드포인트 | 설명 |
|------|------------|------|
| `pipeline_router.py` | `/api/v1/pipeline/*` | YOLO+OCR 통합 파이프라인 |
| `ocr_check_router.py` | `/api/v1/check/ocr/*` | OCR 기반 검증 |

### 1.3 규칙 설정 (`models/design-checker-api/config/`)

| 파일 | 설명 |
|------|------|
| `common/base_rules.yaml` | 공통 BWMS 규칙 |
| `ecs/ecs_rules.yaml` | ECS 제품 전용 규칙 |
| `hychlor/` | HYCHLOR 제품 전용 규칙 |

---

## 2. 수정된 파일들 (Modified)

### 2.1 `api_server.py`
```diff
- from routers import check_router, rules_router, checklist_router
+ from routers import check_router, rules_router, checklist_router, ocr_check_router, pipeline_router

+ app.include_router(ocr_check_router)
+ app.include_router(pipeline_router)

+ "ocr_sources": ["paddleocr", "edocr2", "both"],
```

**TODO:**
- [ ] 다른 API들도 `ocr_sources` 같은 메타데이터를 `/api/v1/info`에 추가할지 검토
- [ ] Gateway API의 `/specs` 엔드포인트에 새 엔드포인트 반영 확인

### 2.2 `routers/__init__.py`
```diff
+ from .ocr_check_router import router as ocr_check_router
+ from .pipeline_router import router as pipeline_router
```

**TODO:**
- [ ] 다른 API들도 `__all__` 명시적 export 패턴 적용 확인

### 2.3 `Dockerfile`
```diff
+ COPY services/ ./services/
```

**TODO:**
- [ ] 다른 API들도 services 폴더 구조가 있으면 Dockerfile에 COPY 추가

### 2.4 `requirements.txt`
```diff
+ httpx  # 외부 API 호출용
```

**TODO:**
- [ ] httpx가 필요한 다른 API들에도 추가

---

## 3. 다른 API들에 적용할 패턴

### 3.1 서비스 레이어 패턴

```python
# services/yolo_service.py 패턴
@dataclass
class YOLOResult:
    success: bool
    detections: list[Detection]
    error: Optional[str] = None

class YOLOService:
    async def detect_pid_symbols(self, image_data: bytes, ...) -> YOLOResult:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(...)
            ...

# 싱글톤 인스턴스
yolo_service = YOLOService()
```

**적용 대상:**
- [ ] `gateway-api/services/` - 기존 서비스들도 이 패턴으로 리팩토링
- [ ] `pid-analyzer-api/services/` - 외부 API 호출 시 적용
- [ ] `blueprint-ai-bom/backend/services/` - 일부 적용됨, 일관성 확인

### 3.2 Pipeline Router 패턴

```python
@router.post("/pipeline/validate")
async def validate_with_yolo(
    file: UploadFile = File(...),
    ocr_source: str = Form(default="edocr2"),  # 여러 소스 지원
):
    # Step 1: YOLO 검출
    yolo_result = await yolo_service.detect(...)

    # Step 2: OCR 추출 (소스 선택)
    if ocr_source in ["edocr2", "both"]:
        edocr2_result = await edocr2_service.extract(...)

    # Step 3: 결과 통합 및 검증
    ...
```

**적용 대상:**
- [ ] `pid-analyzer-api` - YOLO + Line Detector 통합 파이프라인
- [ ] `blueprint-ai-bom` - 이미 유사 패턴 있음, 일관성 확인

---

## 4. 테스트 추가 필요 ✅ 완료 (2026-01-16)

### 4.1 단위 테스트
- [x] `tests/test_yolo_service.py` - YOLO 서비스 테스트 (28개 테스트)
- [x] `tests/test_edocr2_service.py` - eDOCr2 서비스 테스트 (23개 테스트)
- [x] `tests/test_pipeline_router.py` - 파이프라인 라우터 테스트 (23개 테스트)

**총 74개 테스트 통과**

### 4.2 통합 테스트
- [x] `tests/test_pipeline_integration.py` - 통합 테스트 포함됨 (test_pipeline_router.py 내)

---

## 5. 문서화 TODO

- [ ] `gateway-api/api_specs/design-checker.yaml` 업데이트 (새 엔드포인트 추가)
- [ ] `docs/api/design-checker/pipeline.md` 생성 (파이프라인 사용법)
- [ ] CLAUDE.md 업데이트 (엔드포인트 목록)

---

## 6. 우선순위

| 순위 | 작업 | 영향도 | 상태 |
|------|------|--------|------|
| P0 | 테스트 추가 | 안정성 | ✅ 완료 (74개 테스트) |
| P1 | API 스펙 업데이트 | 일관성 | ✅ 완료 (design-checker.yaml) |
| P2 | 다른 API 패턴 적용 | 확장성 | 대기 |
| P3 | 문서화 | 유지보수 | 대기 |
