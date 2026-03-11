# T03: package.json에 lint 스크립트 추가

> **Story**: S06-quality-system
> **상태**: 🔄 진행 중 (WT3)
> **수정 파일**: `docs-site/package.json` (scripts 1줄만)

## 변경 내용

```json
{
  "scripts": {
    "lint:docs": "bash scripts/lint-docs.sh"
  }
}
```

## 주의사항

- `prebuild`에는 추가하지 않음 (다른 워크트리 작업과 충돌 방지)
- 기존 scripts 항목 유지, `lint:docs`만 추가

## 검증

- [ ] `npm run lint:docs` 실행 성공
