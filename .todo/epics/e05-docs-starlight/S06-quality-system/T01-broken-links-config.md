# T01: 깨진 링크 빌드 실패 설정

> **Story**: S06-quality-system
> **상태**: 🔄 진행 중 (WT3)
> **수정 파일**: `docs-site/docusaurus.config.ts` (2줄만)

## 변경 내용

```typescript
// 변경 전
onBrokenLinks: 'warn',
onBrokenMarkdownLinks: 'warn',

// 변경 후
onBrokenLinks: 'throw',
onBrokenMarkdownLinks: 'throw',
```

## 주의사항

- 이 2줄 외에 docusaurus.config.ts의 **다른 어떤 줄도 수정하지 않음**
- 기존에 깨진 링크가 있으면 빌드 실패할 수 있음
  - 이 경우 `'warn'`으로 유지하고 TODO 기록

## 검증

- [ ] 빌드 성공 (throw 적용 시)
- [ ] 또는 깨진 링크 목록 리포트 (warn 유지 시)
