# T02: SequenceDiagram TSX 포팅

> **Story**: S04-component-migration
> **상태**: ⬜ Todo (T01과 병렬)

## 작업 내용

1. `docs-site/src/components/diagrams/SequenceDiagram.tsx` 복사
2. CSS 변수 동일 매핑 (T01과 동일)
3. 다크모드 확인

## 테스트 케이스

| # | 테스트 | 페이지 |
|---|--------|--------|
| 1 | 시퀀스 화살표 렌더링 | agent-verification |
| 2 | 참가자 박스 | api-reference |
| 3 | 다크모드 | 아무 페이지 |

## 검증

- [ ] 빌드 에러 없음
- [ ] 시퀀스 화살표 정상
- [ ] 다크모드 색상 정상
