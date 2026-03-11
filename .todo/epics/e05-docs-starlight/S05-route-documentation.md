# S05: web-ui 라우트 맵 문서화

> **Phase**: 1 (즉시 시작 가능)
> **예상 소요**: 1~2일
> **의존성**: S01

---

## 목표

web-ui의 **전체 라우트**를 1:1로 문서화한다.
현재 docs-site에 프론트엔드 라우트 맵이 **완전히 누락**되어 있다.

## 현황 분석

### 현재 docs-site의 Frontend 문서

| 문서 | 내용 | 라우트 커버리지 |
|------|------|---------------|
| `frontend/index.mdx` | 아키텍처 개요 | 라우트 언급 없음 |
| `frontend/routing.md` | 라우팅 구조 설명 | **개념만, 실제 라우트 목록 없음** |
| `frontend/state-management.md` | Zustand 스토어 | 라우트 무관 |
| `frontend/component-library.md` | 컴포넌트 목록 | 라우트 무관 |

### 문제점

- web-ui에 **52개+ 라우트**가 선언되어 있으나 문서화 0%
- 어떤 URL로 어떤 페이지에 접속하는지 문서가 없음
- 관리자/사용자/공개 페이지 구분이 없음

## 작업 내용

### 1단계: 라우트 인벤토리 추출

```bash
# web-ui 라우트 파일에서 실제 선언 추출
grep -rn "path:" web-ui/src/routes/ | sort
```

### 2단계: 라우트 분류

| 분류 | 설명 | 예시 |
|------|------|------|
| 공개 페이지 | 인증 없이 접근 | `/login`, `/` |
| 사용자 페이지 | 일반 사용자 | `/projects`, `/sessions` |
| 관리자 페이지 | 관리자 전용 | `/admin/*` |
| 시스템 라우트 | redirect, wildcard, wrapper | `/*`, 리다이렉트 |

### 3단계: 문서 작성

**생성할 문서**:

| 파일 | 내용 |
|------|------|
| `frontend/route-map.mdx` | **전체 라우트 맵** (마스터 표) |
| `frontend/pages/dashboard.mdx` | 대시보드 페이지 상세 |
| `frontend/pages/project.mdx` | 프로젝트 페이지 상세 |
| `frontend/pages/blueprintflow.mdx` | BlueprintFlow 페이지 상세 |
| `frontend/pages/admin.mdx` | 관리자 도구 상세 (anchor 기반) |
| `frontend/pages/session.mdx` | 세션/분석 페이지 상세 |

### 라우트 맵 표 형식

```markdown
## 사용자 페이지

| 경로 | 페이지 | 설명 | 가이드 |
|------|--------|------|--------|
| `/` | Dashboard | 프로젝트 목록, 최근 세션 | [상세](/docs/frontend/pages/dashboard) |
| `/projects/:id` | ProjectDetail | 프로젝트 상세, BOM, 세션 목록 | [상세](/docs/frontend/pages/project) |
| `/blueprintflow` | BlueprintFlow | 워크플로우 빌더 | [상세](/docs/frontend/pages/blueprintflow) |
```

### 관리자 복합 문서 (anchor 기반)

```markdown
# Admin Tools

## 데이터 관리 {#data-admin}
...

## 시스템 설정 {#system-settings}
...

## 사용자 관리 {#user-admin}
...
```

## 페이지별 상세 문서 구조

각 페이지 문서는 S01 표준을 따름:

```markdown
---
title: 대시보드
description: 프로젝트 목록 및 최근 세션 현황
tags: [frontend, dashboard, page]
---

# 대시보드

> 프로젝트 목록과 최근 분석 세션을 한눈에 확인하는 메인 페이지

## 접속 방법

| URL | 권한 | 설명 |
|-----|------|------|
| `/` | 인증 필요 | 메인 대시보드 |

## 탭 구성

| 탭 | 설명 | 주요 동작 |
|----|------|----------|
| 프로젝트 | 프로젝트 카드 목록 | 생성, 삭제, 상세 이동 |
| 최근 세션 | 최근 분석 세션 | 세션 상세 이동 |

## 상세 설명
...

## 관련 API

| 메서드 | 엔드포인트 | 설명 |
|--------|----------|------|
| GET | `/projects` | 프로젝트 목록 |
| POST | `/projects` | 프로젝트 생성 |

## 관련 문서

- [프로젝트 상세](/docs/frontend/pages/project)
- [BlueprintFlow](/docs/frontend/pages/blueprintflow)
```

## 산출물

- [ ] web-ui 전체 라우트 인벤토리 (라우트 수 확정)
- [ ] `frontend/route-map.mdx` (마스터 라우트 표)
- [ ] 5~6개 페이지별 상세 문서
- [ ] 라우트 수 vs 문서화 수 정합성 확인

## 완료 기준

- [ ] 모든 라우트가 route-map에 1:1 매핑
- [ ] redirect/wildcard 구분 표기
- [ ] 주요 페이지 5개 이상 상세 문서 작성
- [ ] 깨진 내부 링크 0개

---

*작성: Claude Code | 2026-03-11*
