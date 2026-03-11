# T07: 관리자 도구 복합 문서 (anchor 기반)

> **Story**: S05-route-documentation
> **상태**: 🔄 진행 중 (WT2)
> **생성 파일**: `docs-site/docs/frontend/pages/admin.mdx`

## 구조 (anchor 기반 복합 문서)

```markdown
# Admin Tools

## 데이터 관리 {#data-admin}
...

## 시스템 설정 {#system-settings}
...

## 사용자 관리 {#user-admin}
...

## 모델 관리 {#model-admin}
...
```

## 작성 기준

- `web-ui/src/pages/admin/` 또는 관련 컴포넌트 기반
- 각 관리 기능별 anchor 생성
- route-map.mdx에서 `[상세](./pages/admin#data-admin)` 형태로 링크
