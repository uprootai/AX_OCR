# S04: TSX 컴포넌트 마이그레이션

> **Phase**: 2 (S02 Go 판정 후, S03과 병렬 가능)
> **예상 소요**: 1일
> **의존성**: S02

---

## 목표

기존 Docusaurus용 React TSX 컴포넌트를 **Astro Island** 방식으로 마이그레이션한다.
코드 변경을 최소화하면서 Starlight 환경에서 정상 동작하게 한다.

## 대상 컴포넌트

| 컴포넌트 | 파일 | 사용 페이지 수 | 복잡도 |
|---------|------|-------------|--------|
| `FlowDiagram` | `src/components/diagrams/FlowDiagram.tsx` | ~25 | 중간 |
| `SequenceDiagram` | `src/components/diagrams/SequenceDiagram.tsx` | ~8 | 중간 |
| `MDXComponents` | `src/theme/MDXComponents.tsx` | 글로벌 | 삭제 대상 |

## Docusaurus vs Starlight 차이

### Docusaurus (현재)

```tsx
// src/theme/MDXComponents.tsx — 글로벌 등록
import MDXComponents from '@theme-original/MDXComponents';
import FlowDiagram from '@site/src/components/diagrams/FlowDiagram';

export default { ...MDXComponents, FlowDiagram, SequenceDiagram };
```

```mdx
<!-- 페이지에서 import 없이 바로 사용 -->
<FlowDiagram nodes={[...]} edges={[...]} />
```

### Starlight (마이그레이션 후)

```mdx
---
title: 분석 파이프라인
---
import FlowDiagram from '../../../components/diagrams/FlowDiagram';

{/* client:load로 React hydration */}
<FlowDiagram client:load
  direction="LR"
  nodes={[...]}
  edges={[...]}
/>
```

## 변경 사항

### FlowDiagram.tsx

| 항목 | 변경 필요 | 내용 |
|------|---------|------|
| React 코드 | ❌ 변경 없음 | 순수 React, DOM API 사용 |
| CSS | ⚠️ 확인 필요 | Docusaurus CSS 변수 → Starlight CSS 변수 |
| 다크모드 | ⚠️ 확인 필요 | `color-mix()` 사용 중 → 동작 확인 |
| Props 인터페이스 | ❌ 변경 없음 | |

### CSS 변수 매핑

| Docusaurus | Starlight | 용도 |
|-----------|-----------|------|
| `--ifm-background-color` | `--sl-color-bg` | 배경색 |
| `--ifm-color-primary` | `--sl-color-accent` | 주색상 |
| `--ifm-font-size-base` | `--sl-text-base` | 기본 폰트 |

### 다크모드 변환

```css
/* Docusaurus */
color-mix(in srgb, #e65100 55%, var(--ifm-background-color))

/* Starlight */
color-mix(in srgb, #e65100 55%, var(--sl-color-bg))
```

## MDXComponents 글로벌 등록 대안

Starlight에서는 글로벌 컴포넌트 등록이 없으므로 2가지 옵션:

### Option A: 각 페이지에서 import (권장)

```mdx
import FlowDiagram from '../../../components/diagrams/FlowDiagram';
```

- 장점: 명시적, 트리쉐이킹 가능
- 단점: 25+ 페이지에 import 추가 필요 (자동화 가능)

### Option B: Astro Layout에서 글로벌 주입

```astro
<!-- src/components/StarlightPage.astro -->
<script>
  import FlowDiagram from './diagrams/FlowDiagram';
  // window에 등록
</script>
```

- 장점: 기존과 유사한 사용 패턴
- 단점: 불필요한 번들 로드, Astro 철학에 반함

**결정**: Option A (명시적 import) 채택

## 테스트 케이스

| # | 테스트 | 페이지 | 확인 사항 |
|---|--------|--------|---------|
| 1 | FlowDiagram LR | customer-cases/dsebearing | 노드·엣지 렌더링 |
| 2 | FlowDiagram TD | analysis-pipeline | 세로 레이아웃 |
| 3 | SequenceDiagram | agent-verification | 시퀀스 화살표 |
| 4 | 다크모드 전환 | 아무 페이지 | 색상 mix 적용 |
| 5 | 모바일 반응형 | 아무 페이지 | overflow 스크롤 |

## 산출물

- [ ] `docs-site-starlight/src/components/diagrams/FlowDiagram.tsx` (CSS 변수만 수정)
- [ ] `docs-site-starlight/src/components/diagrams/SequenceDiagram.tsx` (CSS 변수만 수정)
- [ ] 자동 import 삽입 스크립트 (S03 스크립트에 포함)
- [ ] 5개 테스트 케이스 통과

---

*작성: Claude Code | 2026-03-11*
