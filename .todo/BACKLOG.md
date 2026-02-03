# 백로그 (향후 작업)

> 마지막 업데이트: 2026-02-03
> 미래 작업 및 참조 문서

---

## 현재 상태 요약

| 항목 | 값 |
|------|-----|
| **테스트** | 729개 (web-ui 304, gateway 425) |
| **빌드** | ✅ 정상 |
| **ESLint** | 0 errors |
| **노드 정의** | 29개 (Excel Export 제거) |
| **API 서비스** | 21개 |
| **DSE Bearing 템플릿** | 6개 (12→6 정리) |

---

## P1: 패턴 확산 작업 (2026-02-01 기준)

> 상세: `.todo/PENDING_PATTERN_PROPAGATION.md`

### P1-1. _safe_to_gray() 다른 OCR API 적용 [1-1]

**목표**: `cv2.cvtColor(img, COLOR_BGR2GRAY)` 직접 호출을 안전한 버전으로 교체

| # | 작업 | 파일 |
|---|------|------|
| 1 | 각 OCR API 소스에서 `cvtColor.*GRAY` 검색 | `models/*/services/*.py` |
| 2 | 해당 API에 `_safe_to_gray()` 함수 추가 | 각 API |
| 3 | 호출부 교체 및 테스트 | 각 API |

### P1-2. Excel Export 잔여 참조 정리 [0-1]

| # | 작업 |
|---|------|
| 1 | `grep -r "excelexport\|ExcelExport" --include="*.ts" --include="*.py"` 전체 검색 |
| 2 | CLAUDE.md 노드 목록에서 Excel Export 제거 |
| 3 | apiRegistry.ts에서 excelexport 항목 확인/제거 |

### ~~P1-3. Executor API 호출 메서드 분리~~ ✅ 완료 (2026-02-03)

| # | Executor | 상태 |
|---|----------|------|
| 1 | `bom_executor.py` | ✅ `_call_api()`, `_post_api()`, `_patch_api()` 분리 완료 |
| 2 | `pdfexport_executor.py` | ✅ `_post_api()` 분리 완료 |
| 3 | `pidfeatures_executor.py` | ✅ `_post_api()` 분리 완료 |

---

## P1: 기존 작업 (2026-01-30 이전)

### ~~P1-4. BOM 프론트엔드 세션 단가 표시~~ ✅ 완료 (2026-02-03)

| # | 작업 | 상태 |
|---|------|------|
| 1 | 세션 조회 시 `has_custom_pricing` 반환 | ✅ `session_router.py` |
| 2 | BOM 헤더에 "커스텀 단가" 배지 | ✅ `BOMSection.tsx` |
| 3 | types/index.ts에 필드 추가 | ✅ 완료 |

### ~~P1-5. DetectionResultsSection 클래스 하이라이트~~ ✅ 완료 (2026-02-03)

| # | 작업 | 상태 |
|---|------|------|
| 1 | `selectedClassName` state 추가 | ✅ 완료 |
| 2 | 클래스 목록 클릭 핸들러 (필터 UI) | ✅ 완료 |
| 3 | Canvas 렌더링에 선택 상태 반영 (opacity/lineWidth) | ✅ 완료 |

### P1-6. data.yaml 방식 표준화 검토 [C-1]

| # | 작업 | 파일 |
|---|------|------|
| 1 | model_registry.yaml 내 class_names 보유 모델 목록 확인 | `model_registry.yaml` |
| 2 | 학습 data.yaml이 존재하는 모델 식별 | `models/yolo-api/models/` |
| 3 | 해당 모델에 `data_yaml` 필드 추가 | `model_registry.yaml` |

### P1-7. Docker 빌드 panasia_data.yaml 확인 [C-3]

| # | 작업 |
|---|------|
| 1 | `models/yolo-api/Dockerfile` 확인 (COPY 범위) |
| 2 | `.dockerignore` 에 `.yaml` 제외 패턴 없는지 확인 |
| 3 | `docker compose build yolo-api` 후 컨테이너 내부 확인 |

---

## P2: 중기 작업

### P2-0. 치수 전용 워크플로우 일반 텍스트 OCR 강화 [신규]

**배경**: DSE Bearing 1-1 워크플로우에서 치수(숫자/기호)는 eDOCr2+PaddleOCR로 잘 잡히지만, 도면 내 한글/영어 텍스트는 전혀 인식되지 않음.

**현재 문제점**:
| 영역 | 못 잡는 것 | 원인 |
|------|----------|------|
| NOTES 영역 | 재료, 공차, 가공방법 등 영문 텍스트 전체 | 치수 OCR만 실행 |
| 표제란 | DOOSAN Enerbility, BEARING ASSY, 도면번호 등 | 표제란 OCR 미실행 (수동 버튼) |
| 뷰 라벨 | GEN SIDE, TBN SIDE, SECTION E-3, ISO VIEW | 인식 대상 아님 |
| 테이블 셀 | BEAAING→BEARING, 3ING→RING 등 OCR 오류 | Table Detector 내장 OCR 품질 낮음 |

**사용 가능한 OCR API (미활용)**:
| API | 포트 | 장점 | 적용 후보 |
|-----|------|------|----------|
| Tesseract | 5008 | 문서 OCR, 안정적 | 표제란, NOTES |
| EasyOCR | 5015 | 80+ 언어, 한글 강점 | 표제란, 테이블 셀 보정 |
| Surya OCR | 5013 | 90+ 언어, 최신 모델 | NOTES, 뷰 라벨 |
| DocTR | 5014 | 2단계 파이프라인 | 테이블 셀 보정 |
| TrOCR | 5009 | 필기체 | 수기 주석 |
| OCR Ensemble | 5011 | 4엔진 가중 투표 | 고정밀 텍스트 |

**검토 방향**:
1. **표제란 OCR 자동 실행**: `title_block_ocr` feature 있으면 분석 시 자동 실행 (현재 수동 버튼)
2. **NOTES 텍스트 추출**: `notes_extraction` feature에 범용 OCR 엔진 연결
3. **Table Detector OCR 후처리**: 테이블 셀 텍스트를 EasyOCR/Tesseract로 재인식
4. **뷰 라벨 인식**: 도면 영역 세분화 시 라벨 텍스트도 함께 추출
5. **BOM 품질 향상**: 테이블 OCR 보정 → `_generate_dimension_bom()` 부품명 정확도 개선

**우선순위**: 3번(테이블 셀 보정) > 1번(표제란 자동) > 2번(NOTES) > 4번(뷰 라벨)

---

### P2-1. 단가 API 확장 (GET/DELETE)

| 엔드포인트 | 동작 |
|-----------|------|
| `GET /bom/{session_id}/pricing` | 현재 적용된 단가 파일 내용 반환 |
| `DELETE /bom/{session_id}/pricing` | 세션 단가 제거, 글로벌 폴백 복원 |

### ~~P2-2. BOM 테이블 ↔ 도면 하이라이트 연동~~ ✅ 완료 (2026-02-03)

```
BOMSection.tsx → onClassSelect callback
  → WorkflowPage.tsx → bomHighlightClass state lift
  → FinalResultsSection.tsx → selectedClassName/onClassSelect props
```
양방향 연동: BOM 테이블 클릭 ↔ 도면 하이라이트 동기화

### P2-3. SAHI 모드 data.yaml class_names 호환

```
models/yolo-api/services/inference_service.py
  → SAHI AutoDetectionModel이 model.names를 상속하는지 확인
```

### P2-4. dimension_service 다른 OCR 엔진 통합

| 엔진 | 통합 가치 | 필요 작업 |
|------|----------|----------|
| Tesseract | 중간 | `_parse_tesseract_detection()` 추가 |
| TrOCR | 높음 | `_parse_trocr_detection()` 추가 |
| EasyOCR | 높음 | `_parse_easyocr_detection()` 추가 |

### P2-5. CLAUDE.md 노드/파라미터 목록 갱신

| 항목 | 변경 |
|------|------|
| 노드 수 | 30→29 (Excel Export 제거) |
| Table Detector 유효 파라미터 | `crop_regions`, `enable_quality_filter`, `max_empty_ratio` 추가 |
| BOM 유효 파라미터 | `drawing_type`, `features` 추가 |

---

## P3: 장기 작업

| 작업 | 설명 |
|------|------|
| Executor API 호출 재시도/타임아웃 표준화 | 공통 베이스 클래스에 retry 로직 |
| Docker GPU 자동 감지 | 컨테이너 시작 시 GPU 가용성 체크 |
| 크롭 영역 미리보기 도구 | 빌더에서 crop_regions 시각화 |
| 시각화 기능 확장 | 공차 히트맵, BOM 연결선 |
| 템플릿 버전 관리 | 히스토리 및 롤백 |
| 가중 투표 공통 라이브러리 | dimension_service + OCR Ensemble 통합 |

---

## 완료된 백로그 항목

| 작업 | 완료일 |
|------|--------|
| **P1-3 Executor API 호출 메서드 분리** (bom, pdfexport, pidfeatures) | 2026-02-03 |
| **P1-4 BOM 프론트엔드 세션 단가 표시** | 2026-02-03 |
| **P1-5 DetectionResultsSection 클래스 하이라이트** | 2026-02-03 |
| **P2-2 BOM ↔ 도면 하이라이트 연동** (양방향 동기화) | 2026-02-03 |
| **eDOCr2 5개 버그 수정** | 2026-02-01 |
| **BOM executor features 병합 + drawing_type 폴백** | 2026-02-01 |
| **Table Detector multi-crop + 품질 필터** | 2026-02-01 |
| **Excel Export 노드 완전 제거** | 2026-02-01 |
| **DSE Bearing 템플릿 정리 (12→6)** | 2026-02-01 |
| **DSE Bearing 6개 템플릿 aibom 파라미터 설정** | 2026-02-01 |
| **dimension_service 멀티 엔진 리팩토링** | 2026-02-01 |
| 빌더 단가 파일 업로드 | 2026-01-30 |
| YOLO data.yaml 방식 전환 | 2026-01-30 |
| FinalResults 클래스 하이라이트 | 2026-01-30 |
| DSE Bearing 100점 | 2026-01-22 |
| Blueprint AI BOM Phase 2 | 2026-01-24 |

---

## 참조 문서

| 문서 | 위치 |
|------|------|
| **패턴 확산 작업 상세** | `.todo/PENDING_PATTERN_PROPAGATION.md` |
| 새 API 추가 가이드 | `.claude/skills/api-creation-guide.md` |
| 모듈화 가이드 | `.claude/skills/modularization-guide.md` |
| Phase 2 아키텍처 | `.todo/archive/BLUEPRINT_ARCHITECTURE_V2.md` |
| DSE Bearing 계획 | `.todo/archive/DSE_BEARING_100_PLAN.md` |

---

*마지막 업데이트: 2026-02-03*
