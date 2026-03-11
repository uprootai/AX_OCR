# T04: 벤치마크 비교 + Go/No-Go 판단

> **Story**: S02-starlight-poc
> **상태**: ✅ 완료 (WT4)

## 측정 결과

| 지표 | Docusaurus (현재) | Starlight (POC) | 목표 | 판정 |
|------|------------------|-----------------|------|------|
| 빌드 시간 | ~50초 (100+페이지) | **3.5초** (6페이지) | < 5초 | ✅ |
| dist/ 크기 | ~15MB | **800KB** (6페이지) | 현재의 50% | ✅ |
| React Island | N/A | **FlowDiagram 동작** | 동작 | ✅ |
| 사이드바 접기 | ✅ | ✅ | 동작 | ✅ |
| 로컬 검색 | ❌ (외부) | **Pagefind 내장** | 동작 | ✅ |

## Go/No-Go 판단: **Go (조건부)**

| 기준 | 결과 | 판정 |
|------|------|------|
| FlowDiagram 렌더링 | ✅ client:load 동작 | **Go** |
| 빌드 시간 < 5초 | ✅ 3.5초 | **Go** |
| 사이드바 동작 | ✅ 접기/펼치기 정상 | **Go** |
| 마이그레이션 자동화 | ⚠️ 가능하나 주의사항 있음 | **Go (조건부)** |

## 조건: Phase 2 착수 전 필요 사항

| # | 사항 | 이유 |
|---|------|------|
| 1 | Node.js 22로 업그레이드 | 최신 Astro 5 + Starlight 0.37+ 사용 가능 |
| 2 | `src/content/config.ts` 자동 생성 | 없으면 0 entries (무음 실패) |
| 3 | CSS 변수 매핑 스크립트 | `--ifm-*` → `--sl-color-*` |
| 4 | 사이드바 config 자동 변환 | `sidebars.ts` → `astro.config.mjs` |

## POC 산출물 위치

- 프로젝트: `.claude/worktrees/agent-a9fda838/docs-site-starlight/`
- 벤치마크: `docs-site-starlight/BENCHMARK.md`
- FlowDiagram: `docs-site-starlight/src/components/diagrams/FlowDiagram.tsx`
- 설정: `docs-site-starlight/astro.config.mjs`

---

*완료: 2026-03-11 | WT4*
