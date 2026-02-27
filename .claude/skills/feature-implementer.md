---
name: feature-implementer
description: Executes feature implementation phase-by-phase based on plan documents. Tracks progress, runs quality checks, provides risk assessments, and integrates with Git. Use when implementing planned features, executing development phases, or building according to structured roadmaps.
user-invocable: true
allowed-tools: [read, write, edit, glob, grep, bash]
---

# Feature Implementer Skill

**목적**: 계획 문서 기반 단계별 기능 구현 및 리스크 관리

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

실제 변경 전 프리뷰:

```
🔍 Dry-Run Preview

Phase 1: API 스캐폴딩

Would create:
  - gateway-api/api_specs/new-ocr.yaml (~80 lines)
  - models/new-ocr-api/api_server.py (~150 lines)
  - models/new-ocr-api/Dockerfile (~20 lines)

Would modify:
  - docker-compose.yml (+15 lines)

Risk Level: 🟢 Low (새 파일 생성만)

Proceed with actual implementation? (Y/n)
```

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

#### B. 리스크 평가 기준

| 레벨 | 색상 | 조건 | 확인 필요 |
|------|------|------|----------|
| Low | 🟢 | 새 파일, 문서, 테스트 | 자동 진행 |
| Medium | 🟡 | 기존 코드 수정, 설정 변경 | 승인 요청 |
| High | 🟠 | DB 마이그레이션, API 변경, 의존성 추가 | 상세 설명 후 승인 |
| Critical | 🔴 | 파일 삭제, Breaking changes, 보안 수정 | 명시적 확인 |

#### C. 파괴적 작업 경고

**Git 추적 파일 삭제** → 복구 가능, 일반 확인만:
```
ℹ️  File deletion: models/old-api/deprecated_handler.py
    (Git tracked - recoverable via git checkout)

Proceed? (Y/n): _
```

**Git 미추적 파일/데이터 삭제** → 복구 불가, 명시적 확인:
```
🔴 IRREVERSIBLE DELETION WARNING

About to DELETE: /tmp/uploaded_images/batch_001/
This is NOT tracked by git and CANNOT be recovered.

Type 'DELETE' to confirm: _
```

**DB 데이터 삭제** → 복구 불가, 명시적 확인:
```
🔴 CRITICAL: DATABASE OPERATION

About to: DROP TABLE sessions
This data CANNOT be recovered without backup.

Type 'I UNDERSTAND' to confirm: _
```

**Breaking API 변경 시**:
```
⚠️  BREAKING CHANGE WARNING

About to modify: gateway-api/routers/workflow_router.py
Change: Remove endpoint POST /api/v1/workflow/legacy

Impact analysis: Found 3 usages in codebase

Continue? (Y/n): _
```

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
| 1회 | 오류 표시 → 자동 수정 시도 → 재실행 |
| 2회 | 오류 표시 → 재시도? (Y/n) |
| 3회 | 오류 분석 + 옵션 제시 |

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

### Options
1. Continue anyway (skip quality gate) - NOT RECOMMENDED
2. Pause implementation to debug manually
3. Abort and restore to previous phase
4. Get detailed error context

Choice (1-4): _
```

### Step 5: 변경 요약 생성

Phase 완료 시 자동 생성 (`.todos/` 폴더에 저장):

```markdown
## Phase 1 Complete: API 스캐폴딩

**Duration**: 25분 (Estimated: 30분, Variance: -17%)
**Status**: ✅ Complete
**Date**: 2025-12-23 14:30

### Files Changed (4 files)

**Created** (3 files):
- ✅ `gateway-api/api_specs/new-ocr.yaml` (82 lines) - 🟢 Low
- ✅ `models/new-ocr-api/api_server.py` (145 lines) - 🟢 Low
- ✅ `models/new-ocr-api/Dockerfile` (18 lines) - 🟢 Low

**Modified** (1 file):
- ✅ `docker-compose.yml` (+12 lines) - 🟡 Medium

### Risk Assessment
**Overall Risk**: 🟡 Medium

**Destructive Changes**: None
**Breaking Changes**: None

### Quality Gate Results
✅ Python import check passed
✅ docker-compose config valid
✅ YAML syntax valid

### Next Phase Preview
- Phase 2: Executor 구현
- Estimated: 45분
- Risk: 🟢 Low
```

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
- **n**: 구현 중단, 진행 상황 저장
- **pause**: 나중에 재개 가능하도록 저장

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

---

## 🛠️ 자동 적용

이 스킬은 다음과 같은 요청 시 **자동으로 적용**됩니다:

- "새 기능 구현해줘"
- "이 계획대로 구현해줘"
- ".todos/에 있는 계획 실행해줘"
- "Phase별로 진행해줘"

Claude Code가 계획 문서를 감지하면 자동으로:
1. 계획 파싱
2. 리스크 평가
3. 단계별 실행
4. Quality Gate 검증
5. Git 커밋 생성

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
