# 클로드 코드 13가지 전략 (보리스 체니)

> **출처**: 클로드 코드 창시자 보리스 체니 (Boris Cheney)
> **목표**: 주당 PR 100개 처리 가능한 생산성 극대화
> **작성일**: 2026-01-28

---

## 전략 목록 및 적용 현황

| # | 전략 | 적용 | 파일/설정 |
|---|------|------|-----------|
| 1 | 병렬 실행 | ⚠️ 수동 | 사용자가 여러 터미널 실행 |
| 2 | 백그라운드/웹 세션 | ⚠️ 수동 | `&` 또는 웹 세션 활용 |
| 3 | Opus + Thinking Mode | ✅ 적용 | claude-opus-4-5 사용 중 |
| 4 | CLAUDE.md 공유 | ✅ 적용 | `/CLAUDE.md` |
| 5 | PR 검증 + GitHub 통합 | ⚠️ 부분 | 수동 커밋 |
| 6 | Plan Mode | ✅ 적용 | Shift+Tab |
| 7 | 워크플로우 커맨드 | ✅ 적용 | `.claude/commands/` |
| 8 | 서브 에이전트 | ✅ 적용 | `/simplify`, `/verify` |
| 9 | Post-tool Hooks | ✅ 적용 | `.claude/hooks/post-edit-format.sh` |
| 10 | 권한 관리 | ✅ 적용 | `.claude/settings.json` |
| 11 | 외부 툴 권한 | ✅ 적용 | MCP (Playwright, Context7, Repomix) |
| 12 | 장기 작업 핸들링 | ✅ 적용 | `.claude/hooks/on-stop-verify.sh` |
| 13 | 자가 검증 | ✅ 적용 | `/verify` 커맨드 |

**적용률**: 11/13 (85%)

---

## 1. 병렬 실행 (Parallel Execution)

**전략**: 로컬에서 5개의 클로드를 동시에 실행

**현재 상태**: ⚠️ 수동
- 사용자가 여러 터미널 창에서 `claude` 실행 필요
- 시스템 알림 설정으로 입력 요청 시 즉시 반응

**적용 방법**:
```bash
# 터미널 1
claude

# 터미널 2
claude

# ...
```

---

## 2. 백그라운드 및 웹 세션 활용

**전략**: 로컬 5개 + 웹 10개 = 총 15개 세션

**현재 상태**: ⚠️ 수동
- `&` 명령어로 백그라운드 실행 가능
- 웹/모바일에서 직접 실행 가능

**적용 방법**:
```bash
# 백그라운드 실행
claude &

# 웹 세션
https://claude.ai
```

---

## 3. 최고 성능 모델 (Opus + Thinking Mode)

**전략**: "멍청한 모델은 쳐다보지도 않는다" - 항상 Opus 사용

**현재 상태**: ✅ 적용됨
- 모델: `claude-opus-4-5-20251101`
- Thinking Mode 활성화

**설정**:
```bash
# 모델 확인
claude --model opus
```

---

## 4. CLAUDE.md 적극 활용 및 공유

**전략**: Git에 커밋하여 팀원과 공유, 실수 기록

**현재 상태**: ✅ 적용됨
- 파일: `/CLAUDE.md`
- 내용:
  - 프로젝트 개요
  - 컨텍스트 관리 규칙
  - API 테스트 규칙
  - 자주 하는 실수 목록
  - 자가 검증 방법
  - 슬래시 커맨드 목록

**추가된 섹션**:
- "자주 하는 실수 (금지 목록)"
- "자가 검증 방법"
- "슬래시 커맨드"
- "Hooks 설정"

---

## 5. PR 검증 및 GitHub 통합

**전략**: 클로드 태그하여 CLAUDE.md 업데이트, GitHub 앱 설치

**현재 상태**: ⚠️ 부분 적용
- 수동 커밋으로 운영
- GitHub 앱 미설치

**향후 적용**:
```bash
# GitHub 앱 설치
/install
```

---

## 6. 플랜 모드 (Plan Mode)

**전략**: 대부분의 세션을 Plan Mode에서 시작

**현재 상태**: ✅ 적용됨
- `Shift+Tab`으로 Plan Mode 진입
- 읽기 전용으로 계획 수립 → Auto-Accept로 전환

**워크플로우**:
1. Plan Mode 진입 (Shift+Tab)
2. 읽기 전용으로 계획 검토
3. 계획 확정 후 Auto-Accept
4. 실행

---

## 7. 워크플로우 커맨드 저장

**전략**: 반복 프롬프트를 커맨드로 저장, Git 커밋

**현재 상태**: ✅ 적용됨
- 위치: `.claude/commands/`

**등록된 커맨드**:
| 커맨드 | 용도 |
|--------|------|
| `/verify` | 자가 검증 (빌드+린트+헬스체크) |
| `/simplify` | 코드 정리 |
| `/handoff` | 세션 핸드오프 |
| `/add-feature` | 새 기능 추가 |
| `/debug-issue` | 이슈 디버깅 |
| `/rebuild-service` | Docker 재빌드 |
| `/test-api` | API 테스트 |
| `/track-issue` | 이슈 추적 |

---

## 8. 서브 에이전트 (Sub-agents) 활용

**전략**: 특정 목적의 서브 에이전트 규칙적 사용

**현재 상태**: ✅ 적용됨

**등록된 서브 에이전트**:
| 에이전트 | 용도 | 파일 |
|----------|------|------|
| Code Simplifier | 코드 정리 | `/simplify` |
| Verify Agent | E2E 검증 | `/verify` |
| Explore Agent | 코드베이스 탐색 | Task 도구 |
| Plan Agent | 구현 계획 | Task 도구 |

---

## 9. Post-tool Hooks로 포매팅

**전략**: 코드 작성 직후 자동 포매팅

**현재 상태**: ✅ 적용됨
- 파일: `.claude/hooks/post-edit-format.sh`

**기능**:
- TypeScript/JavaScript: prettier + eslint --fix
- Python: ruff format + ruff check --fix

**효과**: 포매팅 문제 10% 자동 해결

---

## 10. 권한 관리 (No Dangerously Skip)

**전략**: Dangerously skip 대신 사전 승인

**현재 상태**: ✅ 적용됨
- 파일: `.claude/settings.json`

**사전 승인된 명령**:
```json
{
  "permissions": {
    "allow": [
      "Bash(git *)",
      "Bash(npm *)",
      "Bash(docker-compose *)",
      "Bash(curl -s *)",
      "Bash(ls *)",
      "Bash(cat *)",
      ...
    ]
  }
}
```

---

## 11. 모든 툴 권한 제공

**전략**: 외부 도구 자유롭게 사용

**현재 상태**: ✅ 적용됨

**연동된 MCP 서버**:
| MCP | 용도 |
|-----|------|
| Playwright | 브라우저 테스트, HTTP 요청 |
| Context7 | 라이브러리 문서 조회 |
| Repomix | 코드베이스 분석 |
| Sequential Thinking | 복잡한 추론 |

---

## 12. 장기 실행 작업 핸들링

**전략**: 백그라운드 검증, Stop Hook, 무한 반복 관리

**현재 상태**: ✅ 적용됨
- 파일: `.claude/hooks/on-stop-verify.sh`

**기능**:
- 작업 완료 시 자동 빌드 검증
- 변경 파일 분석 후 관련 프로젝트만 검증

---

## 13. 자가 검증 (Self-Verification)

**전략**: 정확한 검증 방법 제공

**현재 상태**: ✅ 적용됨
- 커맨드: `/verify`
- 문서: `CLAUDE.md` "자가 검증 방법" 섹션

**검증 항목**:
1. TypeScript 빌드 (web-ui, blueprint-ai-bom frontend)
2. Python 문법 검증 (gateway-api, BOM backend)
3. API 헬스체크 (5020, 8000)
4. Playwright E2E 테스트

---

## 파일 구조

```
.claude/
├── settings.json              # #10 권한 설정 (팀 공유)
├── settings.local.json        # 로컬 전용 설정
├── commands/                  # #7 워크플로우 커맨드
│   ├── verify.md              # #13 자가 검증
│   ├── simplify.md            # #8 Code Simplifier
│   ├── handoff.md
│   ├── add-feature.md
│   ├── debug-issue.md
│   ├── rebuild-service.md
│   ├── test-api.md
│   └── track-issue.md
├── hooks/                     # #9, #12 Hooks
│   ├── pre-edit-check.sh      # 1000줄 체크
│   ├── post-edit-format.sh    # 자동 포매팅
│   ├── post-bash-log.sh       # 실패 로깅
│   ├── on-stop.sh             # 완료 알림
│   └── on-stop-verify.sh      # 자동 검증
├── skills/                    # 온디맨드 가이드
│   ├── modularization-guide.md
│   ├── api-creation-guide.md
│   ├── devops-guide.md
│   └── ...
└── agents/                    # 에이전트 설정

CLAUDE.md                      # #4 프로젝트 가이드
```

---

## 미적용 항목 및 향후 계획

### 1. 병렬 실행 자동화
- 현재: 수동으로 여러 터미널 실행
- 계획: 스크립트로 자동화 가능

### 2. GitHub 앱 통합
- 현재: 수동 커밋
- 계획: `/install` 명령으로 GitHub 앱 설치

---

## 참고 자료

- **원문**: 보리스 체니 13가지 전략
- **관련 파일**:
  - `CLAUDE.md` - 프로젝트 가이드
  - `.claude/settings.json` - 권한 설정
  - `.claude/commands/` - 커맨드 목록
  - `.claude/hooks/` - Hook 스크립트

---

*마지막 업데이트: 2026-01-28*
*Managed By: Claude Code (Opus 4.5)*
