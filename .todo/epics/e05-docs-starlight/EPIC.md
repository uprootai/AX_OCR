# E05: Docs-Site Starlight 마이그레이션 + 문서 구조 표준화

> **소유자**: 개발팀
> **생성일**: 2026-03-11
> **기간**: 2026-Q2 (장기, 단계별 실행)
> **현 상태**: ✅ Phase 1+2 완료 (Starlight 마이그레이션 배포됨)

---

## 배경

현재 Docusaurus 3 기반 docs-site (15 카테고리, 100+ 페이지)를 **Astro Starlight**로 마이그레이션하고,
문서 작성 규칙을 표준화하여 장기적으로 유지보수 가능한 기술 문서 체계를 구축한다.

### 왜 Starlight인가

| 항목 | Docusaurus 3 | Starlight (Astro) |
|------|-------------|-------------------|
| 빌드 속도 | ~7초 (webpack) | ~1~2초 (Vite) |
| 번들 크기 | ~300KB+ (React) | ~50KB (제로 JS 기본) |
| React 컴포넌트 | 네이티브 | **Astro Island으로 재사용 가능** |
| 로컬 검색 | 외부 플러그인 | 내장 (Pagefind) |
| 다크모드 | 설정 필요 | 기본 내장 |
| 성능 (Lighthouse) | 70~85 | 95~100 |
| 마크다운 확장 | MDX | MDX (동일) |

### 마이그레이션 리스크

| 리스크 | 영향 | 대응 |
|--------|------|------|
| 기존 100+ 페이지 변환 | 높음 | S03에서 자동화 스크립트 작성 |
| FlowDiagram/SequenceDiagram TSX | 중간 | Astro Island으로 그대로 사용 가능 |
| Docusaurus 전용 기능 (admonitions) | 낮음 | Starlight 네이티브 지원 |
| 팀 학습 비용 | 낮음 | Astro는 프레임워크 무관 |

## 전략: 2단계 접근

### Phase 1: 문서 구조 표준화 (프레임워크 무관)
- 현재 Docusaurus에서 즉시 적용 가능
- S01 + S05 + S06 → 문서 품질 즉시 개선

### Phase 2: Starlight 마이그레이션
- Phase 1 완료 후 진행
- S02 → S03 → S04 순서

## Stories & Tasks

| ID | Story | Phase | Tasks | 상태 |
|----|-------|-------|-------|------|
| S01 | [문서 구조 규칙 표준화](S01-style-standards.md) | 1 | 4 Tasks | ✅ 완료 |
| S02 | [Starlight 파일럿 테스트](S02-starlight-poc.md) | 2 | 4 Tasks | ✅ 완료 (Go 판정) |
| S03 | [콘텐츠 마이그레이션](S03-content-migration.md) | 2 | 4 Tasks | ✅ 완료 |
| S04 | [TSX 컴포넌트 마이그레이션](S04-component-migration.md) | 2 | 3 Tasks | ✅ 완료 |
| S05 | [web-ui 라우트 맵 문서화](S05-route-documentation.md) | 1 | 8 Tasks | ✅ 완료 |
| S06 | [문서 품질 검증 체계](S06-quality-system.md) | 1 | 4 Tasks | ✅ 완료 |

### Task 상세 목록

**S01 (4 Tasks)** — ✅ 완료
- T01 표준 규칙 정의 → ✅ `.claude/rules/docs-site.md`
- T02 Customer Cases 적용 (7파일) → ✅
- T03 System Overview 적용 (6파일) → ✅
- T04 나머지 카테고리 적용 (96파일) → ✅ 6개 병렬 워크트리 처리

**S02 (4 Tasks)** — ✅ 완료 (Go 판정)
- T01 프로젝트 스캐폴딩 → ✅
- T02 React Island 테스트 → ✅ client:load 동작
- T03 샘플 콘텐츠 변환 → ✅
- T04 벤치마크 + Go/No-Go 판단 → ✅ Go (조건부: Node 22)

**S03 (4 Tasks)** — ✅ 완료
- T01 페이지 인벤토리 확정 → ✅ 115개
- T02 마이그레이션 스크립트 작성 → ✅ `scripts/migrate-content.mjs`
- T03 배치 변환 + 검증 (15 카테고리별) → ✅ 116 페이지 빌드 성공
- T04 사이드바 설정 완성 → ✅ `astro.config.mjs`

**S04 (3 Tasks)** — ✅ 완료
- T01 FlowDiagram TSX 포팅 → ✅ `src/components/diagrams/FlowDiagram.tsx`
- T02 SequenceDiagram TSX 포팅 → ✅ `src/components/diagrams/SequenceDiagram.tsx`
- T03 import 자동 삽입 스크립트 → ✅ 43개 파일 67개 사용처 client:load 적용

**S05 (8 Tasks)** — ✅ 완료
- T01 라우트 인벤토리 추출 → ✅
- T02 전체 라우트 맵 문서 → ✅ `frontend/route-map.mdx`
- T03 대시보드 상세 → ✅
- T04 프로젝트 상세 → ✅
- T05 BlueprintFlow 상세 → ✅
- T06 세션/분석 상세 → ✅
- T07 관리자 도구 복합 문서 (anchor) → ✅
- T08 sidebars.ts 업데이트 → ✅

**S06 (4 Tasks)** — ✅ 완료
- T01 onBrokenLinks 설정 변경 → ✅ `throw`
- T02 lint-docs.sh 스크립트 → ✅
- T03 package.json 업데이트 → ✅
- T04 품질 리포트 템플릿 → ✅

## 의존성 그래프

```
Phase 1 (즉시 시작 가능)          Phase 2 (Phase 1 완료 후)
┌─────┐                         ┌─────┐
│ S01 │──────────────────────────│ S02 │
│표준화│                         │ POC │
└──┬──┘                         └──┬──┘
   │                               ├──────────┐
   ├──────┐                    ┌───┴──┐   ┌───┴──┐
┌──┴──┐┌──┴──┐                │  S03 │   │  S04 │
│ S05 ││ S06 │                │콘텐츠│   │컴포넌트│
│라우트││품질 │                └──────┘   └──────┘
└─────┘└─────┘
```

## 성공 기준

| 기준 | 목표 |
|------|------|
| 빌드 속도 | < 3초 (현재 7초) |
| Lighthouse 성능 | > 95 |
| 문서 구조 일관성 | 100% (모든 페이지 표준 섹션 순서) |
| 라우트 문서화율 | 100% (web-ui 전체 라우트) |
| 링크 정합성 | 0개 깨진 링크 |
| React 컴포넌트 재사용 | FlowDiagram, SequenceDiagram 정상 동작 |

---

*작성: Claude Code | 2026-03-11*
