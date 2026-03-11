# T04: 사이드바 설정 완성

> **Story**: S03-content-migration
> **상태**: ⬜ Todo (T03과 병렬)

## 작업 내용

Docusaurus `sidebars.ts`의 15개 카테고리를 `astro.config.mjs` sidebar 설정으로 변환.

## 매핑

| Docusaurus | Starlight |
|-----------|-----------|
| `type: 'category'` | `{ label, collapsed, items }` |
| `link: {type: 'doc', id: '...'}` | 카테고리 내 첫 항목 또는 `autogenerate` |
| `'doc-id'` 문자열 | `{ label, slug }` |
| `collapsed: true` | `collapsed: true` (동일) |

## 검증

- [ ] 15개 카테고리 모두 표시
- [ ] Customer Cases 하위 서브카테고리 (동서기연) 접기/펼치기
- [ ] 사이드바 순서 원본과 일치
