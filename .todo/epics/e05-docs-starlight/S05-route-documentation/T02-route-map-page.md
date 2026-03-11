# T02: 전체 라우트 맵 문서 작성

> **Story**: S05-route-documentation
> **상태**: 🔄 진행 중 (WT2)
> **생성 파일**: `docs-site/docs/frontend/route-map.mdx`

## 문서 구조

```markdown
---
title: 라우트 맵
description: web-ui 전체 라우트 목록
tags: [frontend, route, page]
---

# 라우트 맵

> web-ui의 전체 프론트엔드 라우트를 분류별로 정리한다.

## 사용자 페이지

| 경로 | 페이지 | 설명 | 가이드 |
|------|--------|------|--------|
| `/` | Dashboard | ... | [상세](./pages/dashboard) |

## 관리자 페이지
...

## 시스템 라우트
...

## 관련 문서
```

## 검증

- [ ] 모든 라우트가 표에 1:1 매핑
- [ ] redirect/wildcard 별도 구분
- [ ] 가이드 링크 대상 파일 존재
