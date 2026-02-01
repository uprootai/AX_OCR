# 진행 중인 작업

> **마지막 업데이트**: 2026-02-01
> **기준 커밋**: ea3463f (feat: 빌더 단가 파일 업로드, BOM UX 개선, YOLO data.yaml 클래스명 방식 전환)

---

## 미커밋 변경 요약 (ea3463f 대비)

> 총 35개 파일 수정/삭제 + 7개 신규 파일 | +1,523줄 / -1,123줄

### 변경 카테고리

| 영역 | 수정 | 삭제 | 신규 | 핵심 변경 |
|------|------|------|------|----------|
| **Gateway API** | 4개 | 2개 | 0 | BOM executor features 병합, Table Detector multi-crop, Excel Export 제거 |
| **eDOCr2 API** | 3개 | 0 | 0 | _safe_to_gray, GPU→CPU 폴백, check_tolerances 방어, max_img_size 2048 |
| **Web-UI** | 11개 | 0 | 4 | 템플릿 정리(12→6), checkboxGroup, DSE 샘플 이미지, Excel Export 삭제 |
| **Blueprint AI BOM** | 13개 | 0 | 2 | dimension_service 대규모 리팩토링, DimensionOverlay, table_service |
| **기타** | 2개 | 0 | 1 | EasyOCR Dockerfile, docs, handoff |

---

## 핵심 변경 상세

### 1. BOM Executor: features 병합 + drawing_type 폴백

**파일**: `gateway-api/blueprintflow/executors/bom_executor.py`

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| **drawing_type** | `inputs.get("drawing_type", "auto")` (항상 auto) | `inputs or self.parameters` fallback (노드 파라미터 반영) |
| **features** | 택일 방식 (inputs만 또는 params만) | **병합** (inputs + params, 중복 제거, 순서 유지) |

**검증 완료**: 2-1 (`assembly`, 4개 merged), 2-3 (`assembly`, 5개 merged) - 게이트웨이 로그 확인

### 2. Table Detector: multi-crop + 품질 필터

**파일**: `gateway-api/blueprintflow/executors/tabledetector_executor.py` (+182줄)

| 항목 | 내용 |
|------|------|
| **도면 특화 프리셋** | `title_block`, `revision_table`, `parts_list_right` (3개 추가) |
| **multi-crop 루프** | `crop_regions` 리스트 순회, 각 영역 독립 API 호출 |
| **품질 필터** | `_is_quality_table()` - 빈 셀 70% 초과 테이블 자동 제거 |
| **_call_api()** | API 호출 로직을 별도 메서드로 추출 (재사용성) |
| **하위호환** | `crop_regions` 없으면 기존 `auto_crop` 폴백 |

### 3. eDOCr2: 5개 버그 수정

| Bug | 문제 | 수정 |
|-----|------|------|
| **1** | `cv2.cvtColor` 그레이스케일 입력 크래시 | `_safe_to_gray()` 함수 도입 (7곳 교체) |
| **2** | `dimensions.remove(o)` numpy 배열 비교 에러 | `is` identity 비교로 변경 |
| **3** | `check_tolerances()` top_line 미초기화 | `top_line = None` + 조기 반환 |
| **4** | `check_tolerances()` None/빈 이미지 크래시 | 입구 방어 코드 추가 |
| **5** | `fit()` 0차원 이미지 division-by-zero | 빈 이미지 반환 가드 |

**추가 개선**:
- GPU→CPU 전처리 폴백 (CLAHE + GaussianBlur)
- `max_img_size` 1048→2048 (고해상도 도면 정확도 향상)

### 4. Excel Export 완전 제거

| 삭제 파일 | 내용 |
|-----------|------|
| `gateway-api/blueprintflow/executors/excelexport_executor.py` | Executor 클래스 189줄 |
| `gateway-api/api_specs/excelexport.yaml` | API 스펙 90줄 |
| `__init__.py`에서 import 제거 | 레지스트리 등록 해제 |
| `test_executors_unit.py`에서 테스트 제거 | 4곳 parametrize 목록 |
| `analysisNodes.ts`에서 노드 정의 제거 | 프론트엔드 노드 |
| `locales/en.json`, `ko.json` 번역 제거 | i18n |
| `monitoring/constants.ts` 제거 | 모니터링 |
| `constants.ts` baseNodeTypes 제거 | 노드 타입 매핑 |

### 5. DSE Bearing 템플릿 정리 (12→6)

**삭제된 템플릿**: 2-4 (CV Cone Cover), 2-5 (GD&T), 2-6 (BOM 추출), 2-7 (Parts List), 3-1 (정밀 분석)
**갱신된 6개 템플릿**: 1-1, 2-1, 2-2, 2-3, 2-8, 3-2

| 갱신 항목 | 내용 |
|-----------|------|
| Table Detector 파라미터 | `mode: extract, ocr_engine: paddle, crop_regions: [3개]` |
| AI BOM 파라미터 | `drawing_type: assembly/dimension_bom`, features 명시 |
| Excel Export 노드 제거 | 모든 템플릿에서 excelexport 노드/엣지 삭제 |
| 샘플 이미지 추가 | 4개 DSE 도면 이미지 경로 설정 |

### 6. Blueprint AI BOM: dimension_service 대규모 리팩토링 (+872줄)

| 기능 | 내용 |
|------|------|
| **멀티 엔진 지원** | eDOCr2 + PaddleOCR 결합 |
| **가중 투표 병합** | `_merge_multi_engine()` - IoU 클러스터링 + 엔진별 가중치 |
| **PaddleOCR 파싱** | `_parse_paddle_detection()`, `_fix_diameter_symbol()` |
| **품질 필터** | `_is_valid_dimension()` - 깨진 텍스트/오탐 제거 |
| **bbox 유연 파싱** | dict/리스트/4점 좌표 모두 지원 |
| **서브 패턴 추출** | 긴 텍스트 블록에서 개별 치수 패턴 추출 |

---

## 프로젝트 상태

| 항목 | 결과 |
|------|------|
| **web-ui 빌드** | ✅ 정상 |
| **Python 문법** | ✅ 정상 |
| **2-1 실행 검증** | ✅ 6 success, 166371ms, 치수 52개 |
| **2-3 실행 검증** | ✅ 8 success, 135471ms, 치수 29개 |
| **drawing_type** | ✅ assembly (parameters에서 전달) |
| **features merge** | ✅ 정상 병합 + 중복 제거 |

---

*마지막 업데이트: 2026-02-01*
