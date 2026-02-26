# Claude Skills - AX POC 프로젝트

이 디렉토리에는 온디맨드로 로드되는 Claude Skills가 포함되어 있습니다.
**컨텍스트 효율화**: 필요할 때만 로드되어 토큰 사용량 최소화

---

## Progressive Disclosure 원칙

| 레벨 | 이름 | 위치 | 설명 |
|------|------|------|------|
| **L0** | Quick Ref | CLAUDE.md 스킬 테이블 | 핵심 수치/커맨드 1줄 (항상 로드) |
| **L1** | README | 이 파일 | 스킬 목록 + 용도 요약 (온디맨드) |
| **L2** | Full Guide | 각 스킬 `.md` 파일 | 상세 가이드 전체 (온디맨드) |

---

## 사용 가능한 Skills (15개)

### 핵심 가이드 (7개)

| 스킬 | 용도 | Quick Ref | 자동 트리거 |
|------|------|-----------|-------------|
| `context-engineering-guide` | 컨텍스트 관리, 60% 규칙 | 60% → `/compact` | "컨텍스트", "토큰" |
| `modularization-guide` | 1000줄 제한, 분리 패턴 | `wc -l` < 1000 | "리팩토링", "분리" |
| `api-creation-guide` | 새 API 스캐폴딩, GPU 설정 | `create_api.py --port` | "새 API", "/add-feature" |
| `project-reference` | R&D 논문 35개, API 스펙 | 논문 35개, API 21개 | "논문", "스펙", "R&D" |
| `version-history` | BOM v10.5, Design Checker | BOM v10.5, DC v1.0 | "버전", "BOM" |
| `devops-guide` | CI/CD, Docker, 배포 | `docker-compose up -d` | "CI", "배포", "Docker" |
| `docs-site-guide` | 문서 사이트 관리 | `:3001`, Docusaurus | "문서", "docs-site" |

### 전략 가이드 (1개)

| 스킬 | 용도 | Quick Ref | 자동 트리거 |
|------|------|-----------|-------------|
| `diagram-strategy` | 다이어그램 TSX 컴포넌트 | Mermaid 금지 → TSX | "다이어그램", "플로우" |

### 워크플로우 스킬 (5개)

| 스킬 | 용도 | Quick Ref | 실행 방법 |
|------|------|-----------|----------|
| `feature-implementer` | 계획 기반 단계별 구현 | Phase별 Quality Gate | "새 기능 구현해줘" |
| `workflow-optimizer` | 도면 유형별 파이프라인 추천 | 6개 프리셋 | `/skill workflow-optimizer` |
| `doc-updater` | 코드 변경 후 문서 업데이트 | 코드→문서 동기화 | "문서 업데이트해줘" |
| `code-janitor` | 코드 스멜, 베스트 프랙티스 | lint + 패턴 감사 | "코드 정리해줘" |
| `ux-enhancer` | UI/UX 베스트 프랙티스 | 접근성 + 반응형 | "UI 개선해줘" |

### 메타 파일 (2개)

| 파일 | 용도 |
|------|------|
| `SKILL.md` | 스킬 시스템 설명 (자동 로드) |
| `README.md` | 이 파일 (스킬 카탈로그) |

---

## 온디맨드 로딩 원칙

1. **CLAUDE.md는 550줄 이하로 유지** → 핵심만 포함
2. **상세 가이드는 Skills로 분리** → 필요 시에만 로드
3. **컨텍스트 60% 규칙** → 초과 시 `/compact` 또는 `/handoff`

### 효과

| 항목 | Before | After |
|------|--------|-------|
| CLAUDE.md 크기 | 794줄 | **~530줄** |
| 컨텍스트 효율 | 매번 전체 로드 | 온디맨드 로드 |
| 토큰 절약 | - | **~60%** |

---

## 스킬 호출 방식

### 자동 트리거
요청 내용에 따라 관련 스킬이 자동으로 적용됩니다.

### 수동 호출
```
/skill workflow-optimizer
/skill code-janitor --auto-fix
```

---

**마지막 업데이트**: 2026-02-26
**버전**: 4.0.0 (Progressive Disclosure + Quick Ref 적용)
