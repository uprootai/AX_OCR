# T01: Starlight 프로젝트 스캐폴딩

> **Story**: S02-starlight-poc
> **상태**: 🔄 진행 중 (WT4)
> **수정 파일**: `docs-site-starlight/` (완전 신규)

## 작업 내용

1. `npm create astro@latest docs-site-starlight -- --template starlight --yes`
2. `npx astro add react --yes`
3. `astro.config.mjs` 기본 설정:
   - `base: '/docs/'`
   - `defaultLocale: 'ko'`
   - 2개 카테고리 사이드바 (System Overview, Customer Cases)

## 검증

- [ ] `npm run build` 성공
- [ ] 기본 페이지 렌더링 확인
- [ ] 사이드바 접기/펼치기 동작

## 위험 요소

- npm 버전 호환성
- astro/starlight 최신 버전 breaking change
