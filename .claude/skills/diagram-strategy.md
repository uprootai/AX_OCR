---
name: diagram-strategy
description: 다이어그램/플로우차트/시퀀스/아키텍처 그림 작성 시 참조. Mermaid 금지 → FlowDiagram/SequenceDiagram TSX 컴포넌트. Triggers — diagram, flowchart, sequence, 구조도
user-invocable: false
allowed-tools: [Read, Grep, Glob]
skill-type: workflow
---

# Diagram Strategy (Mermaid → TSX)

## 원칙

**Mermaid 사용 금지** → 커스텀 React TSX 컴포넌트로 대체

| 항목 | Mermaid | TSX 컴포넌트 |
|------|---------|-------------|
| 번들 크기 | 158KB gzip | 0 |
| 다크모드 | 불완전 | 자동 (color-mix) |
| 스타일링 | 제한적 | 완전 제어 |
| Docusaurus 통합 | 플러그인 필요 | 네이티브 |

---

## 컴포넌트 API

### FlowDiagram (플로우차트)

```tsx
<FlowDiagram
  direction="LR"  // 'LR' | 'TD'
  title="검출 파이프라인"
  nodes={[
    { id: 'a', label: '입력', sub: '이미지', color: '#37474f', bg: '#eceff1' },
    { id: 'b', label: '검출', shape: 'diamond', color: '#e65100', bg: '#fff3e0' },
    { id: 'c', label: '결과', shape: 'stadium', color: '#1565c0', bg: '#e3f2fd' },
  ]}
  edges={[
    { from: 'a', to: 'b' },
    { from: 'b', to: 'c', label: '예' },
  ]}
  layers={[['a'], ['b'], ['c']]}
/>
```

**Props:**
- `nodes`: FlowNode[] - id, label, sub?, color?, bg?, shape? ('rect'|'diamond'|'rounded'|'stadium')
- `edges`: FlowEdge[] - from, to, label?, dashed?
- `layers`: string[][] - 노드 ID를 레이어별로 그룹핑 (레이아웃 결정)
- `direction`: 'LR' | 'TD' (기본: 'LR')
- `nodeWidth`, `nodeHeight`: 커스텀 크기 (기본: 130x56)

### SequenceDiagram (시퀀스)

```tsx
<SequenceDiagram
  title="API 흐름"
  participants={[
    { id: 'user', label: '사용자' },
    { id: 'gw', label: 'Gateway :8000', color: '#1565c0' },
    { id: 'api', label: 'YOLO :5005', color: '#e65100' },
  ]}
  messages={[
    { from: 'user', to: 'gw', label: 'POST /detect' },
    { from: 'gw', to: 'api', label: '이미지 전달' },
    { from: 'api', to: 'api', label: '추론', type: 'self' },
    { from: 'api', to: 'gw', label: '검출 결과', type: 'reply' },
    { from: 'gw', to: 'user', label: 'JSON 응답', type: 'reply' },
  ]}
  loops={[
    { label: '각 도면에 대해', start: 1, end: 3 },
  ]}
/>
```

**Props:**
- `participants`: Participant[] - id, label, color?
- `messages`: Message[] - from, to, label, type? ('sync'|'reply'|'self')
- `loops`: LoopBlock[] - label, start (메시지 인덱스), end (메시지 인덱스)

---

## 글로벌 등록

`docs-site/src/theme/MDXComponents.tsx`에서 글로벌 등록:
- `.md` 파일에서 `import` 없이 바로 `<FlowDiagram ... />` 사용 가능
- `docusaurus.config.ts`의 `markdown.format: 'mdx'` 설정으로 모든 .md 파일 MDX 지원

---

## 색상 팔레트 (카테고리별)

| 카테고리 | color | bg |
|----------|-------|-----|
| detection | #e65100 | #fff3e0 |
| ocr | #1b5e20 | #e8f5e9 |
| segmentation | #01579b | #e1f5fe |
| preprocessing | #4a148c | #f3e5f5 |
| analysis | #311b92 | #ede7f6 |
| knowledge | #880e4f | #fce4ec |
| ai | #1a237e | #e8eaf6 |
| gateway | #263238 | #eceff1 |
| neutral | #37474f | #eceff1 |
| success | #2e7d32 | #e8f5e9 |
| warning | #e65100 | #fff3e0 |
| error | #c62828 | #ffebee |
| info | #00838f | #e0f7fa |
| primary | #1565c0 | #e3f2fd |

---

## Mermaid → TSX 변환 규칙

### flowchart LR/TD
1. 각 노드를 `nodes` 배열의 객체로
2. 화살표(-->)를 `edges` 배열로
3. 조건 분기({})는 `shape: 'diamond'`
4. 노드를 레이어별로 `layers`에 배치
5. `direction` 설정

### sequenceDiagram
1. participant를 `participants` 배열로
2. 화살표(->>)를 `messages` 배열로
3. 점선(-->>)은 `type: 'reply'`
4. self-arrow는 `type: 'self'`
5. loop 블록은 `loops` 배열로

### 특수 다이어그램
- **stateDiagram**: FlowDiagram으로 변환 (states → nodes, transitions → edges)
- **mindmap**: 커스텀 JSX (트리 구조 flex 레이아웃)
- **erDiagram**: 커스텀 JSX (엔티티 카드 + 관계선)

---

## 파일 위치

```
docs-site/src/
├── components/diagrams/
│   ├── FlowDiagram.tsx       # 플로우차트 (LR/TD)
│   ├── SequenceDiagram.tsx   # 시퀀스 다이어그램
│   └── index.ts              # 배럴 export
└── theme/
    └── MDXComponents.tsx     # 글로벌 등록
```
