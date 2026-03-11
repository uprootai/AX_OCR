# T01: FlowDiagram TSX 포팅

> **Story**: S04-component-migration
> **상태**: ⬜ Todo (S02 Go 후)

## 작업 내용

1. `docs-site/src/components/diagrams/FlowDiagram.tsx` 복사
2. CSS 변수 매핑:

| Docusaurus | Starlight | 용도 |
|-----------|-----------|------|
| `--ifm-background-color` | `--sl-color-bg` | 배경색 |
| `--ifm-color-primary` | `--sl-color-accent` | 주색상 |
| `--ifm-font-size-base` | `--sl-text-base` | 폰트 |

3. 다크모드 `color-mix()` 수식 확인

## 테스트 케이스

| # | 레이아웃 | 테스트 페이지 |
|---|---------|-------------|
| 1 | LR (좌→우) | customer-cases/dsebearing |
| 2 | TD (위→아래) | analysis-pipeline |
| 3 | 다크모드 전환 | 아무 페이지 |
| 4 | 모바일 반응형 | 아무 페이지 |

## 검증

- [ ] 빌드 에러 없음
- [ ] 노드/엣지 렌더링 정상
- [ ] 다크모드 색상 정상
- [ ] 모바일 overflow 스크롤
