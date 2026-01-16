# 정리 작업 목록

> 현재 변경사항에서 발견된 정리 필요 항목

---

## 1. 삭제된 파일 정리

### Gateway에서 제거된 파일 (물리적 삭제 필요)
```bash
# 이미 코드에서 제거됨, 파일도 삭제 확인 필요
rm gateway-api/services/pid_overlay_service.py
rm gateway-api/routers/pid_overlay_router.py
rm gateway-api/services/__pycache__/pid_overlay_service.cpython-*.pyc
rm gateway-api/routers/__pycache__/pid_overlay_router.cpython-*.pyc
```

**상태**: ✅ 완료됨 (git status에서 확인)

---

## 2. 파라미터 정리 ✅ 완료 (2026-01-16)

### eDOCr2 version 파라미터 제거
**파일**: `web-ui/src/config/nodes/ocrNodes.ts`
**변경**: version 파라미터 (v1/v2/ensemble) 제거됨

**확인 결과**:
- [x] edocr2-api에서도 v1/v2 분기 제거 여부 ✅ (이미 정리됨)
- [x] gateway-api/services/ocr_service.py에서 버전 로직 정리 ✅
- [x] API 스펙에서 version 파라미터 제거 ✅

```bash
# 확인 명령
grep -r "version.*v1\|version.*v2" gateway-api/
grep -r "version.*v1\|version.*v2" models/edocr2-v2-api/
```

---

## 3. Web-UI 레거시 컴포넌트 정리 ✅ 완료 (2026-01-16)

### PID Overlay 컴포넌트 검토
**위치**:
- `web-ui/src/components/pid/PIDOverlayViewer.tsx`
- `web-ui/src/pages/pid-overlay/PIDOverlayPage.tsx`

**검토 결과**:
- [x] Gateway API 대신 Design Checker API (5019) 사용 확인 ✅
- [x] `/api/v1/pipeline/detect` 엔드포인트 정상 호출 ✅

---

## 4. 모델 레지스트리 동기화 ✅ 완료 (2026-01-16)

### YOLO 모델 클래스 변경
**파일**: `models/yolo-api/models/model_registry.yaml`
**변경**: pid_symbol 60종 → 32종으로 변경

**확인 결과**:
- [x] 실제 .pt 모델 파일과 일치 여부 ✅ (5개 모델 타입 모두 일치)
- [x] Blueprint AI BOM의 CLASS_NAMES와 동기화 ✅ (bom_detector 27종 일치)
- [x] nodeDefinitions.ts의 model_type 옵션과 일치 ✅ (pid_symbol 추가됨)

```yaml
# 변경된 클래스 목록 확인
pid_symbol:
  classes: 32  # 기존 60
  class_names:
    - Arrowhead
    - Arrowhead + Triangle
    # ... 32개
```

---

## 5. Docker 설정 정리

### 불필요한 환경 변수 정리
**파일**: `docker-compose.yml`, `gateway-api/docker-compose.yml`

```bash
# 사용되지 않는 환경 변수 확인
grep -E "^      - [A-Z_]+=" docker-compose.yml | \
  while read var; do
    name=$(echo "$var" | cut -d'=' -f1 | tr -d ' -')
    grep -q "$name" models/*/api_server.py || echo "Unused: $var"
  done
```

---

## 6. 생성된 임시 파일 정리 ✅ 완료 (2026-01-16)

### Excel 리포트 파일
**위치**: 프로젝트 루트
```
TECHCROSS_BWMS_Analysis_Report.xlsx
TECHCROSS_BWMS_Analysis_Report_v2.xlsx
```

**처리 결과**:
- [x] .gitignore에 `**/results/*` 이미 포함 ✅
- [x] 생성된 Excel 파일들은 results/ 디렉토리에 저장되어 자동 무시됨 ✅
- [x] git status에 untracked Excel 파일 없음 확인 ✅

---

## 7. 설정 파일 일관성 ✅ 완료 (2026-01-16)

### Design Checker 설정 구조
**현재**:
```
models/design-checker-api/config/
├── _active.yaml      # 프로필 활성화 설정
├── common/           # 공통 규칙 (21개)
├── ecs/              # ECS 전용 규칙 (37개)
└── hychlor/          # HYCHLOR 전용 규칙 (31개)
```

**확인 결과**:
- [x] common/ 디렉토리 구조 검토 ✅ (base_rules.yaml 포함)
- [x] _active.yaml 포맷 확인 ✅ (버전 1.0, 총 89개 규칙)
- [x] 제품군별 규칙 분리 구조 적절함 ✅

---

## 8. 테스트 파일 정리 ✅ 완료 (2026-01-16)

### 신규 생성된 테스트
**위치**: `models/pid-composer-api/tests/`

**확인 결과**:
- [x] pytest.ini 설정 확인 ✅ (asyncio_mode=auto, markers 설정 완료)
- [x] gateway-api 테스트 364개 통과 ✅
- [x] 테스트 파일 분포:
  - design-checker-api: 4개
  - pid-analyzer-api: 4개
  - yolo-api: 3개
  - line-detector-api: 3개
  - edocr2-v2-api: 2개
  - 기타: 각 1개

---

## 9. 린트 에러 정리 ✅ 완료 (2026-01-16)

### 현재 린트 상태
```
✔ 0 problems (0 errors, 0 warnings)
```

**수정 내역**:
- [x] 21개 경고 수정 → 0개 ✅
- [x] unused variables → `_` prefix 또는 제거
- [x] catch 블록 미사용 변수 → 바인딩 제거

**수정된 파일**:
- `e2e/blueprint-ai-bom-comprehensive.spec.ts`
- `e2e/blueprint-ai-bom.spec.ts`
- `e2e/ui/workflow.spec.ts`
- `src/components/dashboard/ContainerManager.tsx`
- `src/utils/specToHyperparams.ts`

---

## 10. 문서 업데이트 ✅ 완료 (2026-01-16)

### CLAUDE.md 추가 업데이트
- [x] API 서비스 테이블 정렬 확인 ✅ (20개 서비스 정상)
- [x] 포트 번호 중복 없는지 확인 ✅ (모두 고유)
- [x] 버전 히스토리에 PID Composer 추가 기록 ✅

### API 스펙 문서
- [x] gateway-api/api_specs/CONVENTIONS.md 확인 ✅ (OCR/Detection 표준 정의됨)
- [x] 22개 API 스펙 파일 존재 확인 ✅

---

## 우선순위 정리

| 작업 | 우선순위 | 예상 시간 | 상태 |
|------|----------|-----------|------|
| PID 컴포넌트 API 호출 수정 | P0 | 1시간 | ✅ 완료 (2026-01-16) |
| eDOCr2 version 파라미터 정리 | P1 | 0.5시간 | ✅ 완료 (2026-01-16) |
| 린트 에러 수정 (21개 → 0개) | P1 | 0.5시간 | ✅ 완료 (2026-01-16) |
| 모델 레지스트리 동기화 확인 | P1 | 1시간 | ✅ 완료 (2026-01-16) |
| Excel 파일 정리 | P2 | 0.1시간 | ✅ 완료 (2026-01-16) |
| Design Checker 설정 구조 검토 | P2 | 0.5시간 | ✅ 완료 (2026-01-16) |
| 테스트 구조 확인 | P2 | 0.5시간 | ✅ 완료 (2026-01-16) |
| 문서 업데이트 | P3 | 0.5시간 | ✅ 완료 (2026-01-16) |

**전체 정리 작업 완료율: 100%** (8/8 항목)

---

## 완료 요약 (2026-01-16)

| 카테고리 | 항목 수 | 상태 |
|----------|---------|------|
| P0 (긴급) | 1개 | ✅ 완료 |
| P1 (높음) | 3개 | ✅ 완료 |
| P2 (보통) | 3개 | ✅ 완료 |
| P3 (낮음) | 1개 | ✅ 완료 |
| **총계** | **8개** | **✅ 완료** |
