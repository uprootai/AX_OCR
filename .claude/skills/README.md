# Claude Skills - AX POC 프로젝트

이 디렉토리에는 온디맨드로 로드되는 Claude Skills가 포함되어 있습니다.
**컨텍스트 효율화**: 필요할 때만 로드되어 토큰 사용량 최소화

---

## 사용 가능한 Skills (10개)

### 핵심 가이드 (5개) - 신규

| 스킬 | 용도 | 자동 트리거 |
|------|------|-------------|
| `context-engineering-guide` | 컨텍스트 관리, 60% 규칙, 토큰 최적화 | "컨텍스트", "토큰", "60%" |
| `modularization-guide` | 1000줄 제한, 분리 패턴, 리팩토링 전략 | "리팩토링", "분리", "모듈화" |
| `api-creation-guide` | 새 API 스캐폴딩, Dashboard 설정, GPU 설정 | "새 API", "/add-feature" |
| `project-reference` | R&D 논문 (35개), API 스펙, 문서 구조, CI/CD | "논문", "스펙", "R&D" |
| `version-history` | 버전 히스토리, Blueprint AI BOM, Design Checker | "버전", "BOM", "Design Checker" |

### 워크플로우 스킬 (5개)

| 스킬 | 용도 | 실행 방법 |
|------|------|----------|
| `feature-implementer` | 계획 문서 기반 단계별 기능 구현 | "새 기능 구현해줘" |
| `workflow-optimizer` | 도면 유형별 최적 파이프라인 추천 | `/skill workflow-optimizer` |
| `doc-updater` | 코드 변경 후 문서 자동 업데이트 | "문서 업데이트해줘" |
| `code-janitor` | 코드 스멜, 베스트 프랙티스 위반 탐지 | "코드 정리해줘" |
| `ux-enhancer` | UI/UX 베스트 프랙티스 적용 | "UI 개선해줘" |

---

## 온디맨드 로딩 원칙

블로그 권장사항 (sankalp.bearblog.dev) 기반:

1. **CLAUDE.md는 500줄 이하로 유지** → 핵심만 포함
2. **상세 가이드는 Skills로 분리** → 필요 시에만 로드
3. **컨텍스트 60% 규칙** → 초과 시 `/compact` 또는 `/handoff`

### 효과

| 항목 | Before | After |
|------|--------|-------|
| CLAUDE.md 크기 | 794줄 | **237줄** |
| 컨텍스트 효율 | 매번 전체 로드 | 온디맨드 로드 |
| 토큰 절약 | - | **~60%** |

---

## 스킬 호출 방식

### 자동 트리거
요청 내용에 따라 관련 스킬이 자동으로 적용됩니다:

| 요청 예시 | 적용되는 스킬 |
|-----------|--------------|
| "새 API 추가해줘" | api-creation-guide |
| "이 코드 리팩토링해줘" | modularization-guide |
| "버전 히스토리 보여줘" | version-history |
| "R&D 논문 확인해줘" | project-reference |

### 수동 호출
```
/skill workflow-optimizer
/skill code-janitor --auto-fix
```

---

## 권장 워크플로우

### 새 기능 구현 시
```
1. 계획 문서 작성 (.todo/BACKLOG.md에 추가)
2. "이 계획대로 구현해줘" → feature-implementer 자동 적용
3. 각 Phase 완료 후 Quality Gate 검증
4. 완료 시 ACTIVE.md 갱신, COMPLETED.md에 기록
```

### 새 API 추가 시
```
1. "새 API 추가해줘" → api-creation-guide 로드
2. 스캐폴딩 스크립트 실행
3. Dashboard 설정 추가
4. GPU 설정 (필요시)
```

### 배포 준비 시
```
1. "코드 품질 검사해줘" → code-janitor
2. "문서 업데이트해줘" → doc-updater
3. 커밋 & 푸시
```

---

## 리스크 레벨 가이드

| 레벨 | 아이콘 | 조건 | 요구 사항 |
|------|--------|------|----------|
| Low | 🟢 | 새 파일, 문서, 테스트 | 자동 진행 |
| Medium | 🟡 | 기존 코드 수정, 설정 변경 | 사용자 승인 |
| High | 🟠 | DB 변경, API 변경, 의존성 | 상세 검토 |
| Critical | 🔴 | 파일 삭제, Breaking changes | 명시적 확인 |

---

**마지막 업데이트**: 2026-01-16
**버전**: 3.0.0 (온디맨드 로딩 적용)
