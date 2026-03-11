# T03: import 자동 삽입 스크립트

> **Story**: S04-component-migration
> **상태**: ⬜ Todo (T01/T02 완료 후)

## 문제

Docusaurus는 `MDXComponents.tsx`로 글로벌 등록 → import 불필요.
Starlight은 각 MDX 파일에서 명시적 import 필요.

## 스크립트 로직

```bash
# FlowDiagram 사용 파일 찾기
grep -rl '<FlowDiagram' src/content/docs/ | while read f; do
  # frontmatter 뒤에 import 삽입
  # <FlowDiagram → <FlowDiagram client:load 변환
done

# SequenceDiagram 동일 처리
grep -rl '<SequenceDiagram' src/content/docs/ | while read f; do
  ...
done
```

## import 경로 계산

파일 깊이에 따라 상대 경로 자동 계산:
- `docs/index.mdx` → `../../components/diagrams/FlowDiagram`
- `docs/customer-cases/dsebearing/index.mdx` → `../../../../components/diagrams/FlowDiagram`

## 검증

- [ ] 모든 FlowDiagram 사용 파일에 import 삽입됨
- [ ] 모든 SequenceDiagram 사용 파일에 import 삽입됨
- [ ] `client:load` 디렉티브 추가됨
- [ ] 빌드 성공
