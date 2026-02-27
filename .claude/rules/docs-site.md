---
paths:
  - "docs-site/**"
---

# 문서 사이트 규칙

## 코드 변경 시 문서 동기화 필수

| 변경 유형 | 업데이트 대상 |
|----------|-------------|
| 새 API 서비스 추가 | `docs-site/docs/system-overview/` + `devops/` |
| 새 노드 타입 추가 | `docs-site/docs/blueprintflow/node-catalog.md` |
| 파이프라인 흐름 변경 | `docs-site/docs/analysis-pipeline/` 다이어그램 |
| 새 검증 레벨 추가 | `docs-site/docs/agent-verification/` |
| Docker 서비스 변경 | `docs-site/docs/devops/docker-compose.md` |
| 프론트엔드 라우트 추가 | `docs-site/docs/frontend/routing.md` |

## 빌드 확인

```bash
cd docs-site && npm run build
```

## 다이어그램 전략 (IMPORTANT: Mermaid 사용 금지)

**Mermaid 대신 커스텀 React TSX 컴포넌트 사용** (번들 0, 다크모드 자동, 완전 제어)

| 컴포넌트 | 용도 | 파일 |
|----------|------|------|
| `<FlowDiagram>` | 플로우차트 (LR/TD), 상태 다이어그램 | `src/components/diagrams/FlowDiagram.tsx` |
| `<SequenceDiagram>` | 시퀀스 다이어그램 (API 흐름) | `src/components/diagrams/SequenceDiagram.tsx` |

- 글로벌 등록: `src/theme/MDXComponents.tsx` → import 불필요
- 다크모드: `color-mix(in srgb, color 55%, var(--ifm-background-color))` 자동 적용
- **새 다이어그램 추가 시**: Mermaid 블록 대신 TSX 컴포넌트 사용

**상세 가이드**: `.claude/skills/diagram-strategy.md`
