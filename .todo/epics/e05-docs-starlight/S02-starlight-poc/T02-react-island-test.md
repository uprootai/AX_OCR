# T02: React Island 테스트 (FlowDiagram)

> **Story**: S02-starlight-poc
> **상태**: 🔄 진행 중 (WT4)
> **핵심 검증**: Go/No-Go 판단의 가장 중요한 항목

## 작업 내용

1. `docs-site/src/components/diagrams/FlowDiagram.tsx` 복사
2. CSS 변수 매핑:
   - `--ifm-background-color` → `--sl-color-bg`
   - `--ifm-color-primary` → `--sl-color-accent`
3. 샘플 MDX에서 `<FlowDiagram client:load ... />` 테스트

## 검증

- [ ] FlowDiagram 빌드 에러 없음
- [ ] 브라우저에서 렌더링 확인 (노드, 엣지, 레이어)
- [ ] 다크모드 전환 시 색상 적용

## Go/No-Go

| 결과 | 판정 |
|------|------|
| `client:load` 정상 동작 | Go |
| 빌드 에러 또는 hydration 실패 | No-Go → Docusaurus 유지 |
