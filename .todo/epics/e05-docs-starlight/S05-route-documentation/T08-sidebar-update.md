# T08: sidebars.ts 업데이트

> **Story**: S05-route-documentation
> **상태**: 🔄 진행 중 (WT2)
> **수정 파일**: `docs-site/sidebars.ts`

## 변경 내용

Frontend 카테고리에 새 항목 추가:

```typescript
{
  type: 'category',
  label: '9. Frontend',
  items: [
    'frontend/routing',        // 기존
    'frontend/route-map',      // 신규
    {
      type: 'category',
      label: '페이지 상세',
      collapsed: true,
      items: [
        'frontend/pages/dashboard',
        'frontend/pages/project',
        'frontend/pages/blueprintflow',
        'frontend/pages/session',
        'frontend/pages/admin',
      ],
    },
    'frontend/state-management', // 기존
    'frontend/component-library', // 기존
    'frontend/bom-frontend',     // 기존
  ],
}
```

## 주의사항

- 기존 항목 순서/ID 유지
- 신규 항목만 추가
- 다른 카테고리 건드리지 않음
