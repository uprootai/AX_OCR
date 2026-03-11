# T01: 페이지 인벤토리 확정

> **Story**: S03-content-migration
> **상태**: ⬜ Todo (S02 Go 후)

## 작업 내용

기존 docs-site의 모든 페이지를 인벤토리로 정리.

```bash
find docs-site/docs -name "*.mdx" -o -name "*.md" | sort > inventory.txt
wc -l inventory.txt  # 총 페이지 수 확정
```

## 분류 기준

| 유형 | 설명 | 예상 수 |
|------|------|---------|
| 순수 MD/표 | 변환 불필요, 복사만 | ~70 |
| FlowDiagram 포함 | import + client:load 추가 | ~25 |
| SequenceDiagram 포함 | import + client:load 추가 | ~8 |
| Docusaurus 전용 문법 | 수동 변환 필요 | ~5 |

## 산출물

- [ ] `inventory.txt` — 전체 파일 목록
- [ ] `inventory-classified.md` — 유형별 분류 결과
- [ ] 정확한 페이지 수 확정
