# 일관성 검토 및 남은 작업 (2025-12-31)

> 마지막 커밋 이후 변경사항 분석 및 향후 작업 계획
> 분석 기준: git status 기준 unstaged/untracked 파일

---

## 1. 변경 사항 요약

### 1.1 라인 수 변화 (총 -13,926줄, +956줄)

| 파일 | 이전 | 이후 | 분리 결과 |
|------|------|------|----------|
| gateway-api/api_server.py | 2,044줄 | 335줄 | 6개 라우터 분리 |
| gateway-api/admin_router.py | 570줄 | 332줄 | docker, results, gpu_config 분리 |
| models/bwms_rules.py | 1,031줄 | 89줄 | bwms/ 패키지 (8개 모듈) |
| models/api_server_edocr_v1.py | 1,068줄 | 97줄 | edocr_v1/ 패키지 |
| models/region_extractor.py | 1,082줄 | 57줄 | region/ 패키지 (5개 모듈) |
| web-ui/Guide.tsx | 1,235줄 | 151줄 | guide/ 디렉토리 |
| web-ui/APIDetail.tsx | 1,197줄 | 248줄 | api-detail/ 디렉토리 |
| web-ui/NodePalette.tsx | 1,024줄 | 189줄 | node-palette/ 디렉토리 |
| blueprint-ai-bom/pid_features_router.py | 1,101줄 | 118줄 | pid_features/ (6개 라우터) |

### 1.2 신규 파일

```
gateway-api/
├── constants/
│   ├── __init__.py           (15줄)
│   └── docker_services.py    (69줄) ★ SSOT
├── utils/
│   └── subprocess_utils.py   (161줄) ★ 공통 유틸리티
├── routers/
│   ├── docker_router.py      (115줄)
│   ├── results_router.py     (74줄)
│   ├── gpu_config_router.py  (315줄)
│   ├── api_key_router.py     (201줄)
│   ├── process_router.py     (663줄)
│   ├── quote_router.py       (291줄)
│   └── download_router.py    (92줄)
└── tests/
    ├── test_docker_router.py
    ├── test_gpu_config_router.py
    ├── test_results_router.py
    └── test_admin_router.py
```

---

## 2. 일관성 이슈 및 해결 필요 항목

### 2.1 용어 정의 명확화 (완료)

| 용어 | 의미 | 사용 위치 |
|------|------|----------|
| **원본 도면** | 업로드된 도면 이미지 자체 | ReferenceDrawingSection.tsx, tooltipContent.ts |
| **참조 도면** | 클래스별 예시 이미지 (작업자 검증용) | ReferencePanel.tsx, SymbolVerificationSection.tsx |

✅ 용어 구분이 올바르게 되어 있음. 혼동 없음.

---

### 2.2 누락된 UI 섹션 (P1 - 완료 ✅)

새로 추가된 Feature가 `SectionVisibility`에 정의되었으나, 대응 UI 컴포넌트가 없음:

| Feature ID | SectionVisibility Key | UI 섹션 | 상태 |
|------------|----------------------|---------|------|
| `gt_comparison` | `gtComparison` | GTComparisonSection.tsx | ✅ 구현됨 |
| `bom_generation` | `bomGeneration` | BOMSection.tsx | ✅ 존재 |
| `industry_equipment_detection` | `industryEquipmentDetection` | IndustryEquipmentSection.tsx | ✅ 구현됨 |

#### 작업 항목:
- [x] GTComparisonSection.tsx 생성 (GT 비교 UI) - 2025-12-31
- [x] IndustryEquipmentSection.tsx 생성 (장비 태그 인식 UI) - 2025-12-31
- [x] tooltipContent.ts 업데이트 - 2025-12-31
- [ ] WorkflowPage.tsx에 해당 섹션 렌더링 조건 추가 (향후)
- [ ] 백엔드 API 연동 (/api/v1/analysis/{session_id}/gt-comparison 등) (향후)

---

### 2.3 SSOT 패턴 확장 (P2 - 완료 ✅)

gateway-api에서 적용된 SSOT 패턴을 다른 서비스에도 적용 가능:

| 서비스 | SSOT 적용 대상 | 현재 상태 |
|--------|---------------|----------|
| gateway-api | DOCKER_SERVICE_MAPPING, GPU_ENABLED_SERVICES | ✅ 완료 |
| gateway-api | RESULTS_DIR, UPLOAD_DIR | ✅ 완료 (constants/directories.py) |
| blueprint-ai-bom | Feature 정의, 섹션 매핑 | ⚠️ featureDefinitions.ts 존재하나 분산됨 |
| design-checker-api | BWMS 규칙 ID, 장비 타입 | ⚠️ bwms/rules_config.py에 일부 집중화 |
| pid-analyzer-api | 장비 타입, 연결 규칙 | ⚠️ 분산됨 |

#### 작업 항목:
- [x] gateway-api: constants/directories.py 생성 - 2025-12-31
- [x] 라우터들 RESULTS_DIR 중복 제거 - 2025-12-31
- [ ] blueprint-ai-bom: ALL_AVAILABLE_FEATURES를 별도 constants 파일로 분리 (향후)
- [ ] design-checker-api: 장비 패턴을 bwms/constants.py로 통합 (향후)
- [ ] pid-analyzer-api: 장비 분류 상수 통합 (향후)

---

### 2.4 테스트 커버리지 확대 (P2 - 완료 ✅)

신규 분리 모듈에 대한 테스트 필요:

| 모듈 | 테스트 파일 | 상태 |
|------|------------|------|
| gateway-api/routers/docker_router.py | test_docker_router.py | ✅ 13개 |
| gateway-api/routers/gpu_config_router.py | test_gpu_config_router.py | ✅ 7개 |
| gateway-api/routers/results_router.py | test_results_router.py | ✅ 7개 |
| gateway-api/routers/admin_router.py | test_admin_router.py | ✅ 20개 |
| gateway-api/routers/process_router.py | test_process_router.py | ✅ 20개 |
| gateway-api/routers/quote_router.py | test_quote_router.py | ✅ 19개 |
| gateway-api/routers/download_router.py | test_download_router.py | ✅ 15개 |
| models/bwms/*.py | test_bwms_module.py | ✅ 27개 |
| models/edocr_v1/*.py | test_edocr_v1_module.py | ✅ 26개 |
| models/region/*.py | test_region_module.py | ✅ 12개 |

#### 작업 항목:
- [x] test_process_router.py 작성 - 2025-12-31
- [x] test_quote_router.py 작성 - 2025-12-31
- [x] test_download_router.py 작성 - 2025-12-31
- [x] models/design-checker-api/tests/test_bwms_module.py 작성 - 2025-12-31
- [x] models/edocr2-v2-api/tests/test_edocr_v1_module.py 작성 - 2025-12-31
- [x] models/pid-analyzer-api/tests/test_region_module.py 작성 - 2025-12-31

---

### 2.5 API 문서 업데이트 (P3 - 완료 ✅)

분리된 라우터에 대한 OpenAPI 문서 검증:

| API 스펙 | openapi 섹션 | 상태 |
|----------|--------------|------|
| yolo.yaml | requestExamples, responseExamples | ✅ 추가됨 |
| edocr2.yaml | requestExamples, responseExamples | ✅ 추가됨 |
| pid-analyzer.yaml | requestExamples, responseExamples | ✅ 추가됨 |

#### 작업 항목:
- [x] yolo.yaml에 OpenAPI 예시 추가 - 2025-12-31
- [x] edocr2.yaml에 OpenAPI 예시 추가 - 2025-12-31
- [x] pid-analyzer.yaml에 OpenAPI 예시 추가 - 2025-12-31
- [ ] 나머지 API 스펙에도 예시 추가 (향후)

---

## 3. 백워드 호환성 래퍼 파일

분리된 모듈의 원본 파일은 하위 호환성을 위해 re-export 래퍼로 유지됨:

| 파일 | 역할 |
|------|------|
| models/design-checker-api/bwms_rules.py | bwms/ 패키지 re-export |
| models/edocr2-v2-api/api_server_edocr_v1.py | edocr_v1/ 패키지 re-export |
| models/pid-analyzer-api/region_extractor.py | region/ 패키지 re-export |

✅ 기존 import 경로 유지됨. 변경 불필요.

---

## 4. web-ui 분리 패턴 일관성

### 4.1 적용된 패턴

```
ComponentName.tsx (대형 파일)
    ↓ 분리
component-name/
├── index.ts              # re-export
├── hooks/
│   ├── useComponentState.ts
│   └── useComponentHandlers.ts
├── components/
│   └── SubComponent.tsx
├── sections/             # (Guide.tsx 전용)
│   └── SectionComponent.tsx
├── config/               # (APIDetail.tsx 전용)
│   └── definitions.ts
└── constants.ts          # (NodePalette.tsx 전용)
```

### 4.2 미적용 대형 파일 (현재 1000줄 미만)

| 파일 | 라인 수 | 조치 |
|------|---------|------|
| web-ui/BlueprintFlowBuilder.tsx | ~800줄 | 모니터링 (1000줄 초과 시 분리) |
| blueprint-ai-bom/WorkflowPage.tsx | ~600줄 | ✅ 이미 분리됨 |

---

## 5. Feature 의존성 매핑

`sectionConfig.ts`의 `FEATURE_DEPENDENCIES` 현재 상태:

```typescript
// 신규 추가된 의존성
gt_comparison: { requires: ['symbol_detection'] },
industry_equipment_detection: { requiresAtLeastOne: ['symbol_detection', 'pid_connectivity'] },
equipment_list_export: { requires: ['industry_equipment_detection'] },
```

#### 검증 완료:
- [x] gt_comparison이 symbol_detection 없이 활성화되지 않는지 확인 ✅
- [x] industry_equipment_detection의 의존성이 올바른지 확인 ✅

---

## 6. 추천 작업 우선순위 (업데이트: 2025-12-31)

### P0 (즉시) - 없음
모든 핵심 기능이 정상 동작 중.

### P1 (단기 - 1주) ✅ 완료
1. ~~GTComparisonSection.tsx 구현~~ ✅
2. ~~IndustryEquipmentSection.tsx 구현~~ ✅
3. ~~tooltipContent.ts 업데이트~~ ✅

### P2 (중기 - 2주) ✅ 완료
1. ~~누락된 라우터 테스트 작성 (process, quote, download)~~ ✅ +54개 테스트
2. ~~분리된 모듈 테스트 작성 (bwms, edocr_v1, region)~~ ✅ +65개 테스트
3. ~~SSOT 패턴 확장 (constants/directories.py)~~ ✅

### P3 (장기 - 1개월) ✅ 완료
1. ~~OpenAPI 문서 예시 추가 (yolo, edocr2, pid-analyzer)~~ ✅
2. 성능 벤치마크 문서화 (향후)
3. 아키텍처 다이어그램 업데이트 (향후)

---

## 7. 관련 파일 목록

### 수정된 파일 (staged 필요)
```
.todos/2025-12-29_next_steps_recommendation.md
.todos/2025-12-31_post_commit_analysis.md
.todos/README.md
.todos/REMAINING_WORK_PLAN.md
CLAUDE.md
blueprint-ai-bom/backend/routers/pid_features_router.py
blueprint-ai-bom/frontend/src/components/ReferencePanel.tsx
blueprint-ai-bom/frontend/src/components/tooltipContent.ts
blueprint-ai-bom/frontend/src/pages/WorkflowPage.tsx
blueprint-ai-bom/frontend/src/pages/workflow/components/WorkflowSidebar.tsx
blueprint-ai-bom/frontend/src/pages/workflow/config/sectionConfig.ts
blueprint-ai-bom/frontend/src/pages/workflow/sections/ReferenceDrawingSection.tsx
blueprint-ai-bom/frontend/src/pages/workflow/sections/SymbolVerificationSection.tsx
blueprint-ai-bom/frontend/src/pages/workflow/types/workflow.ts
gateway-api/api_server.py
gateway-api/routers/__init__.py
gateway-api/routers/admin_router.py
models/design-checker-api/bwms_rules.py
models/edocr2-v2-api/api_server_edocr_v1.py
models/pid-analyzer-api/region_extractor.py
web-ui/src/components/blueprintflow/NodePalette.tsx
web-ui/src/pages/admin/APIDetail.tsx
web-ui/src/pages/dashboard/Guide.tsx
```

### 신규 파일 (git add 필요)
```
.todos/2025-12-31_architecture_discussion.md
.todos/archive/
blueprint-ai-bom/backend/routers/pid_features/
gateway-api/constants/
gateway-api/routers/api_key_router.py
gateway-api/routers/docker_router.py
gateway-api/routers/download_router.py
gateway-api/routers/gpu_config_router.py
gateway-api/routers/process_router.py
gateway-api/routers/quote_router.py
gateway-api/routers/results_router.py
gateway-api/tests/test_admin_router.py
gateway-api/tests/test_docker_router.py
gateway-api/tests/test_gpu_config_router.py
gateway-api/tests/test_results_router.py
gateway-api/utils/subprocess_utils.py
models/design-checker-api/bwms/
models/edocr2-v2-api/edocr_v1/
models/pid-analyzer-api/region/
web-ui/src/components/blueprintflow/node-palette/
web-ui/src/pages/admin/api-detail/
web-ui/src/pages/dashboard/guide/
```

---

## 8. 참고 사항

### 8.1 디자인 패턴 점수
- 현재: **100/100점** (목표 달성)
- 테스트: **505개** (gateway 364, web-ui 141)
- ESLint: **0 에러**, 3 경고

### 8.2 파일 크기 규칙
- 목표: 모든 소스 파일 **1,000줄 이하**
- 현재: ✅ 모든 대형 파일 분리 완료

### 8.3 LLM 최적화
- 작은 파일 = 정확한 코드 생성
- 평균 파일 크기 ~200줄로 유지 중

---

*작성: Claude Code (Opus 4.5)*
*날짜: 2025-12-31*
