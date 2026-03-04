# AX POC - Claude Code Project Guide

> 기계 도면 자동 분석 및 제조 견적 시스템 | FastAPI + React 19 + YOLO v11 + eDOCr2 + Docker
> 경로별 상세 규칙: `.claude/rules/` | 온디맨드 스킬: `.claude/skills/`

---

## 컨텍스트 관리

### 60% 규칙
- **60% 초과 시** → `/compact` 또는 `/handoff` 실행

### 탐색 패턴

| 상황 | 도구 |
|------|------|
| 대규모 코드베이스 검색 | `Explore` 에이전트 |
| 특정 파일/클래스 검색 | `Glob` / `Read` 도구 |

---

## 작업 추적 (.todo/) — BMAD-Lite

```
.todo/
├── ACTIVE.md          # 현재 Epic/Story (세션 시작 시 반드시 읽기)
├── BACKLOG.md         # Epic 인덱스
├── COMPLETED.md       # 완료 아카이브
└── epics/{id}/        # EPIC.md + S01~S0N.md
```

| 시점 | 행동 |
|------|------|
| **세션 시작** | `ACTIVE.md` 읽고 현재 Epic/Story 파악 |
| **작업 완료** | Story ✅, `ACTIVE.md` 갱신, 필요시 `COMPLETED.md` 기록 |
| **새 작업** | `BACKLOG.md`에 Epic 추가 또는 기존 Epic에 Story 추가 |

---

## IMPORTANT: API 테스트 규칙

### 핵심: Multipart 필수 (base64 금지)

```bash
# ❌ 금지 — 쉘 인자 제한, +33% 용량
curl -d '{"image": "base64..."}'

# ✅ 필수
curl -F "file=@image.png" http://localhost:5005/api/v1/detect
```

| 금지 | 대안 |
|------|------|
| base64 이미지 전송 | multipart/form-data |
| `curl`로 ML API 직접 호출 | Playwright HTTP (`playwright_post`) |
| 백그라운드 테스트 (`nohup`, `&`) | 사용자 직접 실행 |

### 예외: 빠른 헬스체크 (< 1초)

```bash
curl -s http://localhost:5005/health
```

## IMPORTANT: 테스트 실행 정책 (Gateway API)

- 상세 실행 규칙은 `.claude/rules/development.md`를 단일 기준(SSOT)으로 따른다.
- `/verify` 실행 절차는 `.claude/commands/verify.md`를 따른다.
- Test Runner 동작은 `.claude/agents/test-runner.md`를 따른다.

---

## 온디맨드 스킬

| 스킬 | 용도 | Quick Ref | 트리거 |
|------|------|-----------|--------|
| `modularization-guide` | 1000줄 제한, 분리 패턴 | `wc -l` < 1000 | "리팩토링", "분리" |
| `api-creation-guide` | 새 API 스캐폴딩 가이드 | `create_api.py --port` | "새 API" |
| `project-reference` | R&D 논문, API 스펙 | 논문 35개, API 21개 | "논문", "스펙" |
| `version-history` | BOM, Design Checker 버전 | BOM v10.5, DC v1.0 | "버전", "BOM" |
| `devops-guide` | CI/CD, Docker, 배포 | `docker-compose up -d` | "배포", "Docker" |
| `docs-site-guide` | 문서 사이트 관리 | `:3001`, Docusaurus | "문서", "docs-site" |
| `diagram-strategy` | 다이어그램 TSX 컴포넌트 | Mermaid 금지 → TSX | "다이어그램" |
| `presentation-guide` | PPT/PDF 산출물 생성 | 메트릭 카드, 3중 검증 | "PPT", "발표자료" |

**위치**: `.claude/skills/` (전체 16개 중 핵심 8개)

---

## 서브에이전트 모델 배정

| 모델 | 용도 | Task 파라미터 |
|------|------|--------------|
| **haiku** | 빠른 탐색, 파일 검색 | `model: "haiku"` |
| **sonnet** | 계획 수립, 중간 복잡도 | `model: "sonnet"` |
| **opus** | 기본값, 복잡한 구현 | 생략 (기본) |

---

## 코드 주석 태그 (AX Tag)

| 태그 | 용도 | 예시 |
|------|------|------|
| `@AX:ANCHOR` | 핵심 진입점, 변경 시 영향 큼 | `// @AX:ANCHOR — 노드 타입 정의` |
| `@AX:WARN` | 주의 필요, 함정/부작용 있음 | `# @AX:WARN — confidence 기본값 0.4` |
| `@AX:TODO` | 향후 개선 필요 | `// @AX:TODO — 캐시 레이어 추가` |

---

## 파일 크기 규칙

| 라인 수 | 조치 |
|---------|------|
| < 500줄 | ✅ 유지 |
| 500-1000줄 | ⚠️ 리팩토링 고려 |
| > 1000줄 | **즉시 분리** (`.claude/skills/modularization-guide.md`) |

---

## IMPORTANT: 절대 금지

| 실수 | 대안 |
|------|------|
| base64 이미지 전송 | multipart/form-data |
| `curl`로 ML API 직접 호출 | Playwright HTTP |
| 1000줄 이상 파일 생성 | 즉시 분리 |
| 존재하지 않는 파라미터 사용 | `api_specs/*.yaml` 확인 |
| 커밋 전 빌드 미확인 | `/verify` 실행 |
| Mermaid 다이어그램 사용 | TSX 컴포넌트 (`FlowDiagram`, `SequenceDiagram`) |

---

## 슬래시 커맨드

| 커맨드 | 용도 |
|--------|------|
| `/verify` | 자가 검증 (빌드+린트+헬스체크) |
| `/simplify` | 코드 정리 (중복 제거, 단순화) |
| `/handoff` | 세션 핸드오프 (컨텍스트 60% 초과 시) |
| `/plan-epic` | Epic 기획 → Story 분해 (BMAD-Lite) |
| `/add-feature` | 새 기능 추가 가이드 |
| `/debug-issue` | 이슈 디버깅 워크플로우 |
| `/rebuild-service` | Docker 서비스 재빌드 |
| `/test-api` | API 엔드포인트 테스트 |

---

## Hooks (8개)

| Hook | 이벤트 | 기능 |
|------|--------|------|
| `session-start.sh` | SessionStart | 세션 인사 (git 상태, .todo 리마인더) |
| `pre-edit-check.sh` | PreToolUse | 1000줄 이상 파일 경고 |
| `post-edit-format.sh` | PostToolUse | 자동 포매팅 (prettier, ruff) |
| `post-edit-quality.sh` | PostToolUse | Quality Gate (console.log, 시크릿) |
| `post-bash-log.sh` | PostToolUse | 실패 명령 로깅 |
| `pre-compact.sh` | PreCompact | 컨텍스트 압축 전 진행 중 작업 보존 |
| `on-stop.sh` | Stop | 작업 완료 알림 |
| `on-stop-verify.sh` | Stop | 자동 검증 (빌드, Python 구문) |

---

**Managed By**: Claude Code (Opus 4.6)
