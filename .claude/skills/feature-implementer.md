---
name: feature-implementer
description: Executes feature implementation phase-by-phase based on plan documents using XML contracts, early-stop criteria, quality gates, and failure-context purification. Use when implementing planned features, executing development phases, or building according to structured roadmaps.
user-invocable: true
allowed-tools: [read, write, edit, glob, grep, bash]
---

# Feature Implementer Skill

**목적**: 계획 문서 기반 단계별 기능 구현 및 리스크 관리

---

## Execution Contract

구현을 시작하기 전에 현재 Phase 기준으로 계약을 먼저 채운다.

기본 템플릿:
- `/home/uproot/ax/poc/.claude/templates/claude-skill-system-prompt.xml`

최소 계약:

```xml
<contract>
  <goal>현재 Phase에서 완료할 단일 구현 목표</goal>
  <scope>수정 허용 파일, 서비스, 테스트 범위</scope>
  <success_definition>완료 조건 + 필수 검증</success_definition>
  <forbidden_actions>
    <item>계획 문서 밖 범위 확장 금지</item>
    <item>검증되지 않은 API, 파라미터, 파일명 추정 금지</item>
    <item>실패한 체크를 숨긴 채 진행 금지</item>
  </forbidden_actions>
  <tool_policy>
    <read_first>계획 문서, 관련 rule/skill, 대상 파일</read_first>
    <verify_with>phase에 맞는 최소 Quality Gate</verify_with>
  </tool_policy>
  <stop_conditions>
    <condition>안전한 구현 경로가 1개로 수렴하면 추가 탐색 중지</condition>
    <condition>핵심 정보가 없으면 추측 구현 대신 차단 질문 또는 보류</condition>
  </stop_conditions>
  <output_schema>
    <status/>
    <plan/>
    <edits/>
    <verification/>
    <risks/>
  </output_schema>
</contract>
```

원칙:
- 계약은 전체 기능이 아니라 `현재 Phase` 기준으로 좁게 유지
- Phase가 바뀌면 계약을 다시 작성
- 최종 응답에는 장문 사고 과정 대신 결정과 검증 결과만 노출

## Private Think Scratchpad

툴 호출 전 내부 메모는 짧게 유지한다.

```xml
<think_tool visibility="private">
  <task_class>scaffold | refactor | bugfix | integration</task_class>
  <unknowns/>
  <evidence_needed/>
  <tool_sequence/>
  <risk_checks/>
  <exit_test/>
</think_tool>
```

사용 규칙:
- 한 줄 체크리스트로만 작성
- `unknowns`가 안전한 구현을 막으면 바로 멈춘다
- scratchpad는 최종 출력에 그대로 노출하지 않는다

## Reasoning and Early Stop

- 기본 추론 노력은 `low`
- 다음 경우만 `medium`으로 상향:
  - 아키텍처 선택
  - 다중 서비스 연쇄 수정
  - High/Critical 리스크 변경
  - Quality Gate 2회 이상 실패
- `high`는 예외적 상황에서만 사용

조기 종료 규칙:
- 안전한 구현안 하나가 우세하면 대안 탐색을 멈춘다
- 동일 진단을 지지하는 독립 신호 2개가 있으면 원인 탐색을 멈춘다
- 추가 탐색이 결론을 바꾸지 못하면 바로 구현 또는 보고로 전환한다

---

## 🎯 스킬 개요

이 스킬은 다음을 수행합니다:
1. 계획 문서 파싱 및 진행 상태 추적
2. 단계별 실행 (Phase-by-Phase)
3. 각 단계 완료 후 사용자 승인 요청
4. Quality Gate 검증 (빌드, 테스트, 린트)
5. 리스크 평가 및 경고
6. 파괴적 작업 시 명시적 확인
7. Git 자동 커밋 생성
8. Dry-run 모드 지원

---

## 📋 실행 워크플로우

### Step 0: 계약 및 작업 패킷 생성

계획 문서를 읽기 전에 현재 작업 패킷을 확정한다.

필수 입력:
- 현재 Feature 또는 Epic 이름
- 이번 Phase의 목표
- 수정 가능 범위
- 필수 검증 명령

출력 형식:
```markdown
## Phase Contract
- Goal:
- Scope:
- Success:
- Stop if:
- Verify with:
```

이 단계에서 해야 할 일:
1. 계획 문서에서 이번 Phase만 분리
2. 관련 파일과 검증 명령만 좁게 수집
3. private think scratchpad 작성
4. 구현 전에 멈출 조건을 먼저 선언

### Step 1: 계획 문서 로드

```bash
# 계획 문서 위치
docs/plans/           # 기본 위치
.todos/               # 대안 위치
```

**계획 문서 구조 예시**:
```markdown
# Feature: 새로운 OCR API 추가

## Phase 1: API 스캐폴딩
- [ ] api_specs/new-ocr.yaml 생성
- [ ] models/new-ocr-api/api_server.py 생성
- [ ] docker-compose.yml에 서비스 추가

## Phase 2: Executor 구현
- [ ] blueprintflow/executors/new_ocr_executor.py 생성
- [ ] executor_registry.py에 등록
- [ ] services/new_ocr_service.py 생성

## Phase 3: 프론트엔드 통합
- [ ] Dashboard 설정 추가
- [ ] nodeDefinitions.ts 업데이트
```

### Step 2: Dry-Run 모드 (선택)

실제 변경 전에는 아래만 간단히 보여준다:
- 생성 파일
- 수정 파일
- 예상 리스크
- 진행 여부

### Step 3: 단계별 실행

#### A. Pre-Phase 체크
```markdown
## Phase 1: API 스캐폴딩

📋 Tasks:
1. [ ] api_specs/new-ocr.yaml 생성
2. [ ] models/new-ocr-api/api_server.py 생성
3. [ ] docker-compose.yml에 서비스 추가

🎯 Goal: 새 OCR API의 기본 구조 생성
⏱️ Estimated: 30분
⚠️ Risk: 🟢 Low

Ready to start Phase 1? (Y/n)
```

Pre-Phase 체크에는 아래 요약이 반드시 포함되어야 한다:

```markdown
### Contract Summary
- Scope: [이번 단계의 파일/서비스만]
- Success: [완료 기준]
- Stop if: [추가 정보 필요 / 위험 상향 / 검증 실패 반복]
```

#### B. 리스크 평가 기준

| 레벨 | 색상 | 조건 | 확인 필요 |
|------|------|------|----------|
| Low | 🟢 | 새 파일, 문서, 테스트 | 자동 진행 |
| Medium | 🟡 | 기존 코드 수정, 설정 변경 | 승인 요청 |
| High | 🟠 | DB 마이그레이션, API 변경, 의존성 추가 | 상세 설명 후 승인 |
| Critical | 🔴 | 파일 삭제, Breaking changes, 보안 수정 | 명시적 확인 |

#### C. 파괴적 작업 경고

- Git 추적 파일 삭제: 복구 가능하므로 일반 확인
- Git 미추적 파일/데이터 삭제: `DELETE` 같은 명시적 확인
- DB 파괴 작업: `I UNDERSTAND` 같은 강한 확인
- Breaking API 변경: 영향 범위 요약 후 확인

### Step 4: Quality Gate 검증

#### AX POC 프로젝트 기본 검증:

**백엔드**:
```bash
cd gateway-api
pytest tests/ -v                    # 테스트
python -c "import api_server"       # Import 검증
```

**프론트엔드**:
```bash
cd web-ui
npm run lint                        # ESLint
npm run build                       # TypeScript 빌드
npm run test:run                    # Vitest 테스트
```

**Docker**:
```bash
docker-compose config               # 설정 검증
docker-compose build <service>      # 빌드 테스트
```

#### 실패 시 재시도 프로토콜:

| 시도 | 동작 |
|------|------|
| 1회 | 오류 표시 → Reflector 요약 → 자동 수정 시도 → 재실행 |
| 2회 | 오류 표시 → Reflector 요약 → 재시도 여부 판단 |
| 3회 | 오류 분석 + Curator 패킷 생성 + 옵션 제시 |

재시도 전 private Reflector 형식:

```xml
<reflector>
  <failure_type/>
  <confirmed_facts/>
  <discarded_hypotheses/>
  <root_cause_candidate/>
  <next_probe/>
</reflector>
```

3회 실패 시 다음 턴 또는 Codex 검증으로 넘길 수 있도록 Curator 패킷을 남긴다:

```xml
<curator>
  <task_state/>
  <relevant_files/>
  <decisions/>
  <open_risks/>
  <next_action/>
</curator>
```

**3회 실패 시 옵션**:
```markdown
## Quality Gate Failed After 3 Attempts

### Failed Checks
- ❌ `npm run build` - TypeScript error in WorkflowPage.tsx

### Potential Problems Identified
1. Missing type definition for 'BOMSessionResponse'
2. Import path incorrect for 'analysisOptions'

### Suggested Actions
- Add type to src/types/index.ts
- Check import path

### Curated Context
- Task state:
- Relevant files:
- Open risks:
- Next action:

### Options
1. Continue anyway (skip quality gate) - NOT RECOMMENDED
2. Pause implementation to debug manually
3. Abort and restore to previous phase
4. Get detailed error context
5. Send curated packet to Codex for cross-check

Choice (1-5): _
```

### Step 5: 변경 요약 생성

Phase 완료 시 자동 생성 (`.todos/` 폴더에 저장):

```markdown
## Phase 1 Complete: API 스캐폴딩

Status:
Files Changed:
Risk:
Quality Gate Results:
Next Phase:
Curator Summary:
```

Phase 요약에는 긴 작업 로그 대신 다음 정보만 남긴다:
- 확정된 변경
- 통과/실패한 검증
- 다음 Phase의 차단 요소
- 재개에 필요한 Curator 요약

### Step 6: Git 통합

#### 자동 커밋 메시지:
```
Phase 1 complete: API 스캐폴딩

Tasks completed:
- api_specs/new-ocr.yaml 생성
- models/new-ocr-api/api_server.py 생성
- docker-compose.yml에 서비스 추가

Quality gates: All passed
Risk level: Low
Files changed: 3 created, 1 modified

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

#### 커밋 확인:
```
📝 Commit Preview

Branch: feature/new-ocr-api
Files to stage: 4 files
Commit message: [위 메시지]

Commit these changes? (Y/n)
Create tag 'phase-1-complete'? (Y/n)
```

### Step 7: 단계 간 승인

```markdown
## Implementation Progress

✅ Phase 1: API 스캐폴딩 (25분) - Complete
⏳ Phase 2: Executor 구현 (45분) - Next
⏳ Phase 3: 프론트엔드 통합 (30분)
⏳ Phase 4: 테스트 & 문서화 (20분)

Overall: 25% complete (1 of 4 phases)

Continue to Phase 2? (Y/n/pause)
```

- **Y**: 다음 단계 진행
- **n**: 구현 중단, Curator 패킷 저장
- **pause**: 나중에 재개 가능하도록 Curator 패킷 저장

### Step 8: 재개 기능

이전 세션에서 중단된 경우:
```
🔄 Resume Detection

Found incomplete implementation:
- Plan: .todos/new-ocr-api-plan.md
- Last Phase: Phase 2 (60% complete)
- Last Task: Executor 등록

Resume from Phase 2, Task 2.2? (Y/n)
```

재개 데이터는 전체 대화 기록이 아니라 아래만 포함해야 한다:
- 마지막 완료 Phase
- 현재 미완료 태스크
- 관련 파일
- 실패 원인 요약
- 다음 액션

---

## 🛠️ 자동 적용

이 스킬은 다음과 같은 요청 시 **자동으로 적용**됩니다:

- "새 기능 구현해줘"
- "이 계획대로 구현해줘"
- ".todos/에 있는 계획 실행해줘"
- "Phase별로 진행해줘"

Claude Code가 계획 문서를 감지하면 자동으로:
1. 계획 파싱
2. Phase 계약 생성
3. 리스크 평가
4. 단계별 실행
5. Quality Gate 검증
6. 실패 시 Reflector/Curator 정제
7. Git 커밋 생성

---

## 📁 AX POC 특화 설정

### 프로젝트 구조 인식
```
gateway-api/
├── api_specs/           # API 스펙 YAML
├── blueprintflow/
│   └── executors/       # 노드 실행기
├── routers/             # FastAPI 라우터
└── services/            # 서비스 레이어

models/
└── {api-id}-api/        # 개별 API 컨테이너

web-ui/
├── src/config/          # 노드 정의
├── src/pages/           # 페이지 컴포넌트
└── src/types/           # TypeScript 타입
```

### 기본 Quality Gate 명령어
```yaml
backend:
  - pytest gateway-api/tests/ -v
  - python -c "from gateway_api import api_server"

frontend:
  - npm run lint
  - npm run build
  - npm run test:run

docker:
  - docker-compose config
  - docker-compose build --dry-run {service}
```

### Codex 교차 검증 사용 시점

다음 상황에서만 단일 턴으로 Codex 교차 검증을 사용한다:
- High/Critical 리스크 변경
- Quality Gate 3회 실패
- 구현안 2개가 끝까지 팽팽한 경우

입력 패킷 기준:
- `/home/uproot/ax/poc/.claude/templates/codex-cross-check-system-prompt.xml`

Codex에 넘길 정보:
- task
- decision_request
- constraints
- relevant_files
- current_hypothesis
- diff_summary

### 리스크 자동 분류
| 파일 패턴 | 기본 리스크 |
|-----------|------------|
| `*.yaml`, `*.md` | 🟢 Low |
| `*_executor.py`, `*_service.py` | 🟢 Low |
| `docker-compose.yml` | 🟡 Medium |
| `*_router.py`, `api_server.py` | 🟡 Medium |
| `apiConfigStore.ts`, `workflowStore.ts` | 🟠 High |
| DELETE 작업 | 🔴 Critical |

---

## 📊 예상 효과

- ✅ 대규모 기능 구현 시 체계적 진행
- ✅ 리스크 사전 인지 및 관리
- ✅ Quality Gate로 버그 조기 발견
- ✅ 일관된 커밋 메시지 및 이력
- ✅ 중단 후 재개 가능
- ✅ Dry-run으로 사전 검토
