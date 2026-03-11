# S02: Starlight 파일럿 테스트

> **Phase**: 2 (S01 완료 후)
> **예상 소요**: 1~2일
> **의존성**: S01

---

## 목표

Astro Starlight로 docs-site를 새로 구성하고, 핵심 기능이 동작하는지 검증한다.
전체 마이그레이션 전에 **기술적 리스크를 제거**하는 것이 목적.

## 검증 항목

| # | 검증 대상 | 성공 기준 | 우선순위 |
|---|---------|---------|---------|
| 1 | 기본 구조 | Starlight 프로젝트 생성, 빌드 성공 | P0 |
| 2 | MDX 지원 | 기존 .mdx 파일 렌더링 | P0 |
| 3 | React Island | FlowDiagram TSX 컴포넌트 렌더링 | P0 |
| 4 | 사이드바 | 15개 카테고리, 접기/펼치기 | P0 |
| 5 | 다크모드 | 자동 전환, 다이어그램 색상 | P1 |
| 6 | 검색 | Pagefind 로컬 검색 동작 | P1 |
| 7 | i18n | 한국어 기본 로케일 | P1 |
| 8 | 빌드 성능 | < 3초 | P1 |
| 9 | Docker 배포 | nginx 정적 서빙 | P2 |
| 10 | ngrok-proxy 연동 | `/docs/` 경로 기반 라우팅 | P2 |

## 파일럿 구조

```
docs-site-starlight/          # 별도 디렉토리 (기존 docs-site 유지)
├── astro.config.mjs
├── package.json
├── src/
│   ├── content/
│   │   └── docs/              # 마크다운 파일 (기존 docs/ 복사)
│   │       ├── system-overview/
│   │       ├── customer-cases/
│   │       └── ...
│   └── components/
│       └── diagrams/          # 기존 TSX 컴포넌트 복사
│           ├── FlowDiagram.tsx
│           └── SequenceDiagram.tsx
├── public/
│   └── img/                   # 기존 static/img 복사
└── Dockerfile
```

## 핵심 기술 검증 코드

### 1. Astro 프로젝트 생성

```bash
npm create astro@latest docs-site-starlight -- --template starlight
cd docs-site-starlight
npx astro add react    # React Island 지원
```

### 2. astro.config.mjs

```javascript
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import react from '@astrojs/react';

export default defineConfig({
  base: '/docs/',
  integrations: [
    react(),
    starlight({
      title: 'AX POC',
      defaultLocale: 'ko',
      sidebar: [
        {
          label: '1. System Overview',
          collapsed: true,
          autogenerate: { directory: 'system-overview' },
        },
        // ... 15개 카테고리
      ],
      search: { provider: 'pagefind' },  // 로컬 검색 내장
    }),
  ],
});
```

### 3. React Island (FlowDiagram 재사용)

```mdx
---
title: 분석 파이프라인
---

import FlowDiagram from '../../components/diagrams/FlowDiagram';

<FlowDiagram client:load
  direction="LR"
  nodes={[...]}
  edges={[...]}
/>
```

- `client:load` 디렉티브로 React 컴포넌트를 클라이언트에서 hydrate
- 기존 TSX 코드 변경 없이 사용 가능

## 비교 벤치마크

파일럿 완료 후 측정:

| 지표 | Docusaurus (현재) | Starlight (파일럿) |
|------|------------------|-------------------|
| 빌드 시간 | 7초 | 목표 < 3초 |
| 번들 크기 | ? KB | 목표 < 100KB |
| Lighthouse 성능 | ? | 목표 > 95 |
| 첫 페이지 로드 | ? ms | 목표 < 500ms |
| React 컴포넌트 | 정상 | 정상 확인 필요 |

## Go/No-Go 판단 기준

| 기준 | Go | No-Go |
|------|-----|-------|
| FlowDiagram 렌더링 | ✅ React Island 동작 | ❌ Island 미지원 or 버그 |
| 빌드 시간 | < 5초 | > 7초 (현재보다 느림) |
| 사이드바 | 접기/펼치기 동작 | 구조적 제약 |
| 마이그레이션 난이도 | 자동화 가능 | 수작업 > 50% |

**No-Go 시**: Docusaurus 유지, S01/S05/S06 규칙만 적용

## 산출물

- [ ] `docs-site-starlight/` 디렉토리 (파일럿 프로젝트)
- [ ] 벤치마크 결과 표
- [ ] Go/No-Go 판단 보고
- [ ] 마이그레이션 자동화 가능성 평가

---

*작성: Claude Code | 2026-03-11*
