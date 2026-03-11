# T03: 샘플 콘텐츠 변환 테스트

> **Story**: S02-starlight-poc
> **상태**: 🔄 진행 중 (WT4)

## 작업 내용

기존 docs-site에서 대표 페이지 3~4개 복사 후 Starlight 구조로 변환:

| 원본 | 변환 대상 | 난이도 |
|------|---------|--------|
| `system-overview/index.mdx` | 순수 MD + 표 | 낮음 |
| `customer-cases/panasia.mdx` | FlowDiagram 포함 | 중간 |
| `analysis-pipeline/index.mdx` | FlowDiagram + 표 | 중간 |

## 변환 규칙 확인

| Docusaurus | Starlight | 자동화 가능 |
|-----------|-----------|-----------|
| `sidebar_position` | 제거 (config에서 관리) | ✅ |
| `:::tip` | `:::tip` (동일) | - |
| `:::warning` | `:::caution` | ✅ sed |
| `:::danger` | `:::danger` (동일) | - |
| 글로벌 FlowDiagram | `import` + `client:load` | ✅ 스크립트 |

## 검증

- [ ] 3~4개 페이지 빌드 성공
- [ ] admonition 렌더링 확인
- [ ] 표 렌더링 확인
