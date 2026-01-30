# 진행 중인 작업

> **마지막 업데이트**: 2026-01-30
> **현재 활성화된 작업 목록**

---

## 📋 미커밋 변경 사항 (ecf6ba1 대비)

> 총 10개 파일 수정 + 1개 신규 파일 | +453줄

### 그룹 A: 빌더 단가 파일 업로드 + 첨부 파일 다운로드 (5개 파일)

**핵심**: 빌더에서 단가 JSON 첨부 → 세션별 단가 적용 → BOM 생성 시 세션 단가 우선, 미첨부 시 글로벌 폴백

| 파일 | 변경 내용 |
|------|----------|
| `web-ui/src/store/workflowStore.ts` | `uploadedPricingFile` 상태/액션 추가, `executeWorkflow`·`executeWorkflowStream` 양쪽 inputs에 `pricing_file` 포함, `clearWorkflow`에 초기화 |
| `web-ui/src/pages/blueprintflow/BlueprintFlowBuilder.tsx` | `DollarSign`, `Download` 아이콘 추가, 단가 업로드 UI (초록색, `.json`), 이미지/GT/단가 각각 다운로드 버튼 |
| `gateway-api/blueprintflow/executors/bom_executor.py` | `_upload_pricing_file()` 메서드 (GT 패턴 복제), execute에서 GT 다음 6번 단계로 호출 |
| `blueprint-ai-bom/backend/routers/bom_router.py` | `POST /{session_id}/pricing` 엔드포인트 (JSON 유효성 검사), `generate_bom` 호출 시 `session_pricing_path` 전달 |
| `blueprint-ai-bom/backend/services/bom_service.py` | `generate_bom()`에 `session_pricing_path` 파라미터, `load_pricing_db()` 세션 우선 로드 |

**파이프라인 흐름**:
```
빌더 단가 JSON 첨부
  → workflowStore.uploadedPricingFile 저장
  → executeWorkflow inputs.pricing_file에 포함
  → Gateway bom_executor._upload_pricing_file() → BOM API POST /bom/{session_id}/pricing
  → 세션 디렉토리에 pricing.json 저장
  → generate_bom 시 세션 pricing.json 우선 로드
  → 없으면 글로벌 classes_info_with_pricing.json 폴백
```

### 그룹 B: Blueprint AI BOM 프론트엔드 UX 개선 (2개 파일)

| 파일 | 변경 내용 |
|------|----------|
| `blueprint-ai-bom/frontend/src/components/ReferencePanel.tsx` | 드래그 리사이즈 (200~800px), 접기/펼치기, masonry 레이아웃 (CSS columns), 모두 펼침/접기 토글, `onClose` optional 변경 |
| `blueprint-ai-bom/frontend/src/pages/workflow/sections/FinalResultsSection.tsx` | BOM 심볼 리스트에서 클래스명 클릭 → 도면 위 해당 검출만 파란색 하이라이트 + 나머지 회색, 선택 해제 시 기존 상태별 색상 복원 |

### 그룹 C: YOLO 파나시아 data.yaml 방식 전환 (3+1개 파일)

**핵심**: `override_class_names: true` (라우터 후처리) → `data_yaml: panasia_data.yaml` (모델 로드 시 names 직접 교체)

| 파일 | 변경 내용 |
|------|----------|
| `models/yolo-api/models/model_registry.yaml` | panasia 모델: `override_class_names: true` → `data_yaml: panasia_data.yaml` |
| `models/yolo-api/routers/detection_router.py` | `override_class_names` 분기 제거 (isdigit/class_ 체크만 유지) |
| `models/yolo-api/services/registry.py` | 모델 로드 시 `data_yaml` 있으면 YAML 파싱 → `model.names` 직접 교체 |
| `models/yolo-api/models/panasia_data.yaml` | **(신규)** 파나시아 27종 클래스명 정의 (nc: 27) |

**장점**: 모델 학습 시 사용한 data.yaml과 동일 → 클래스명 불일치 방지, 라우터 후처리 불필요

---

## 🔍 확장 필요 분석 (다른 노드/컴포넌트 적용 검토)

### A-1. 단가 파일 → BOM 프론트엔드 연동 [P1]

**문제**: 빌더에서 단가 파일을 업로드하면 BOM 세션에 저장되지만, BOM 프론트엔드(WorkflowPage)에서는 "현재 세션에 커스텀 단가가 적용됨"을 인지하지 못함.

**필요 작업**:
- `blueprint-ai-bom/frontend`: 세션 정보에 pricing 파일 존재 여부 표시
- BOM 결과 테이블에 "세션 단가 적용됨" 표시
- BOM UI에서 직접 단가 파일 업로드/제거 기능 (빌더 없이 독립 사용 시)

**관련 파일**:
```
blueprint-ai-bom/frontend/src/pages/workflow/WorkflowPage.tsx
blueprint-ai-bom/frontend/src/pages/workflow/sections/BOMResultsSection.tsx
blueprint-ai-bom/backend/routers/bom_router.py (GET/DELETE pricing 추가)
```

### A-2. 단가 API 확장 (GET/DELETE) [P2]

**현재**: `POST /{session_id}/pricing` 만 존재
**필요**: 적용된 단가 조회/삭제 API

```python
# 추가 필요
GET  /bom/{session_id}/pricing   → 현재 적용된 단가 파일 내용 반환
DELETE /bom/{session_id}/pricing → 세션 단가 제거 → 글로벌 폴백 복원
```

### A-3. 템플릿 실행 경로에서 pricing_file 전달 확인 [P2]

**현재**: `executeWorkflow`, `executeWorkflowStream` 에는 pricing_file 포함
**확인 필요**: Gateway의 `execute-template`, `execute-template-stream` 엔드포인트도 동일하게 inputs를 그대로 전달하는지

```
gateway-api/routers/workflow_router.py
  → execute_template() / execute_template_stream()
  → inputs dict를 그대로 executor에 전달하므로 별도 작업 불필요할 수 있음
  → 다만 실제 테스트로 검증 필요
```

### B-1. 클래스 하이라이트 → DetectionResultsSection 확장 [P1]

**현재**: FinalResultsSection에서만 클래스명 클릭 → 하이라이트
**필요**: 검증 단계(DetectionResultsSection)에서도 동일 기능

**이유**: 검증 단계에서 특정 클래스만 골라보며 승인/수정할 때 유용

**관련 파일**:
```
blueprint-ai-bom/frontend/src/pages/workflow/sections/DetectionResultsSection.tsx
  → FinalResultsSection의 selectedClassName, handleClassClick 패턴 복제
  → Canvas 렌더링 로직에 선택 상태 반영
```

### B-2. BOM 테이블 ↔ 도면 연동 하이라이트 [P2]

**현재**: FinalResultsSection 내부에서만 연동
**필요**: BOMResultsSection 테이블에서 항목 클릭 → FinalResultsSection 도면에 해당 심볼 하이라이트

**구현 방식**:
```
BOMResultsSection.tsx → 클래스명 클릭 이벤트 → 상위 컴포넌트(WorkflowPage)로 전달
  → FinalResultsSection에 selectedClassName prop으로 전달
  → 기존 하이라이트 로직 재활용
```

### C-1. data.yaml 방식 → 다른 커스텀 모델 표준화 [P1]

**현재**: panasia만 data.yaml 방식
**향후**: 새로운 커스텀 모델 등록 시 data.yaml 방식을 표준으로 사용

**확인 필요**:
```yaml
# model_registry.yaml 내 다른 모델 중 class_names가 정의된 것들
pid:        class_names 33개 → data.yaml 전환 대상?
mechanical: class_names 27개 → data.yaml 전환 대상?
electrical: class_names 6개  → data.yaml 전환 대상?
```

**기준**: class_names 목록이 10개 이상이거나, 학습 data.yaml이 존재하는 모델은 data.yaml 방식으로 전환하는 것이 유지보수 용이

### C-2. SAHI 모드에서 data.yaml class_names 호환 [P2]

**현재**: registry.py에서 `service.model.model.names` 직접 교체
**확인**: SAHI 모드(`use_sahi=true`)일 때 sahi 라이브러리가 model.names를 참조하는지, 별도 경로를 사용하는지

```
models/yolo-api/services/inference_service.py
  → SAHI 추론 경로에서 model.names 사용 여부 확인
  → sahi.AutoDetectionModel이 model.names를 상속하는지 확인
```

### C-3. Docker 빌드 시 panasia_data.yaml 포함 확인 [P1]

```
models/yolo-api/Dockerfile
  → COPY models/ 또는 COPY . 범위에 models/panasia_data.yaml이 포함되는지 확인
  → 빌드 후 컨테이너 내 /app/models/panasia_data.yaml 존재 확인
```

---

## 📌 향후 작업 요약

| 우선순위 | ID | 작업 | 카테고리 | 관련 파일 |
|----------|-----|------|----------|----------|
| **P1** | A-1 | BOM 프론트엔드에 세션 단가 표시 | 단가 | bom-frontend |
| **P1** | B-1 | DetectionResultsSection 클래스 하이라이트 | UX | bom-frontend |
| **P1** | C-1 | data.yaml 방식 다른 모델 표준화 검토 | YOLO | yolo-api |
| **P1** | C-3 | Docker 빌드 panasia_data.yaml 포함 확인 | DevOps | yolo-api |
| **P2** | A-2 | GET/DELETE pricing API 추가 | 단가 | bom-backend |
| **P2** | A-3 | 템플릿 실행 pricing_file 전달 검증 | 단가 | gateway-api |
| **P2** | B-2 | BOM 테이블 ↔ 도면 하이라이트 연동 | UX | bom-frontend |
| **P2** | C-2 | SAHI 모드 data.yaml 호환 검증 | YOLO | yolo-api |

---

## 📊 프로젝트 상태

| 항목 | 결과 |
|------|------|
| **web-ui 빌드** | ✅ 정상 (15.04s) |
| **Python 문법** | ✅ 3개 파일 정상 |
| **미커밋 파일** | 10 modified + 1 new |

---

## 📂 TODO 파일 구조

```
.todo/
├── ACTIVE.md         # 현재 파일 (활성 작업)
├── BACKLOG.md        # 향후 작업 목록
├── SYNC_PATTERNS.md  # 패턴 동기화 추적
├── COMPLETED.md      # 완료 아카이브
└── archive/          # 상세 문서
    └── BLUEPRINT_ARCHITECTURE_V2.md
```

---

*마지막 업데이트: 2026-01-30*
