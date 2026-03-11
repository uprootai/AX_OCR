# E06: Docs-Site 콘텐츠 스타일 규격 적용

> **소유자**: 개발팀
> **생성일**: 2026-03-11
> **기간**: 2026-Q2 (2~3일, 병렬 워크트리 활용)
> **현 상태**: ⬜ Planning

---

## 배경

E05에서 Docusaurus → Starlight 프레임워크 마이그레이션을 완료했으나,
**콘텐츠 자체는 기존 구조 그대로** 옮겨졌다. 사용자가 제시한 문서 스타일 규격 프롬프트를
116개 페이지 전체에 적용하여 일관된 기술 문서 체계를 구축한다.

### 현재 상태 (Gap 분석 결과)

| 규칙 | 현재 준수율 | 목표 | 영향 파일 |
|------|-----------|------|----------|
| `tags` frontmatter | 0% (0/115) | 100% | 전체 115개 |
| H1 한글+영어 제목 | 60% | 100% | ~46개 |
| blockquote 요약 | 95% | 100% | ~6개 |
| 섹션 순서 통일 | 70% | 100% | ~35개 |
| `## 관련 API` 섹션 | 4.3% (5/115) | 해당 파일 100% | ~50개 |
| 표 형식 통일 | 85% | 100% | ~17개 |
| 라우트 권한 구분 | 50% | 100% | route-map + 6개 페이지 상세 |
| anchor 기반 복합 문서 | 40% | 100% | ~10개 |
| 운영/개발 문체 | 90% | 100% | ~12개 |

### 전략: 카테고리별 배치 처리

115개 파일을 한번에 처리하지 않고, **16개 카테고리를 5개 배치로 묶어 병렬 처리**한다.
각 배치는 독립적이므로 워크트리 에이전트로 병렬 실행 가능하다.

| 배치 | 카테고리 | 파일 수 | 난이도 |
|------|---------|--------|--------|
| B1 | system-overview (6), analysis-pipeline (6) | 12 | 중 |
| B2 | blueprintflow (6), agent-verification (4), bom-generation (5) | 15 | 중 |
| B3 | pid-analysis (5), batch-delivery (5), quality-assurance (6) | 16 | 중 |
| B4 | frontend (12), devops (5) | 17 | 높 |
| B5 | api-reference (19), research (16) | 35 | 높 |
| B6 | developer (7), deployment (6), customer-cases (7) | 20 | 중 |

## Stories & Tasks

| ID | Story | Tasks | 상태 |
|----|-------|-------|------|
| S01 | [스타일 규칙 정의 + 검증 스크립트](S01-style-rules.md) | 4 Tasks | ⬜ Todo |
| S02 | [Frontmatter 일괄 표준화](S02-frontmatter-batch.md) | 3 Tasks | ⬜ Todo |
| S03 | [H1 제목 + blockquote 표준화](S03-title-blockquote.md) | 3 Tasks | ⬜ Todo |
| S04 | [섹션 순서 재구성](S04-section-reorder.md) | 6 Tasks | ⬜ Todo |
| S05 | [관련 API 섹션 추가](S05-api-sections.md) | 4 Tasks | ⬜ Todo |
| S06 | [라우트 문서 강화](S06-route-enhancement.md) | 3 Tasks | ⬜ Todo |
| S07 | [표 형식 + anchor 통일](S07-table-anchor.md) | 3 Tasks | ⬜ Todo |
| S08 | [최종 검증 + 배포](S08-final-verification.md) | 4 Tasks | ⬜ Todo |

### Task 상세 목록

**S01 (4 Tasks)** — ⬜ Todo
- T01 스타일 규칙 `.claude/rules/docs-content-style.md` 작성
- T02 lint-style.sh 검증 스크립트 작성 (tags, H1 패턴, 섹션 순서 검사)
- T03 카테고리별 현황 리포트 자동 생성
- T04 검증 기준 (pass/fail) 문서화

**S02 (3 Tasks)** — ⬜ Todo
- T01 tags 분류 체계 정의 (카테고리별 태그 매핑)
  ```
  system-overview → [시스템, 아키텍처, 인프라]
  analysis-pipeline → [파이프라인, ML, 분석]
  api-reference → [API, 마이크로서비스]
  frontend → [프론트엔드, React, UI]
  ...
  ```
- T02 115개 파일 frontmatter에 `tags` 필드 일괄 추가 (스크립트)
- T03 검증: 모든 파일에 description + tags 존재 확인

**S03 (3 Tasks)** — ⬜ Todo
- T01 H1 제목 매핑표 작성 (현재 → 목표)
  ```
  # 시스템 개요 → # 시스템 개요 (System Overview)
  # YOLO Detection API → # YOLO 검출 API (YOLO Detection)
  # Deployment → # 배포 가이드 (Deployment)
  ```
- T02 115개 파일 H1 제목 일괄 변환 (스크립트 + 수동 검토)
- T03 누락 blockquote 6개 파일 보완

**S04 (6 Tasks)** — ⬜ Todo (배치별 병렬 처리)
- T01 섹션 순서 템플릿 3종 정의
  ```
  [Overview 타입] 개요 → 아키텍처/구조 → 하위 페이지 → 관련 API → 관련 문서
  [Page 타입]    접속 방법 → 탭/구조 → 상세 설명 → 관련 API → 관련 문서
  [API 타입]     기본 정보 → 파라미터 → 응답 → 사용 예시 → 리소스 → 관련 문서
  ```
- T02 배치 B1 (system-overview + analysis-pipeline) 12파일 재구성
- T03 배치 B2 (blueprintflow + agent-verification + bom-generation) 15파일 재구성
- T04 배치 B3 (pid-analysis + batch-delivery + quality-assurance) 16파일 재구성
- T05 배치 B4 (frontend + devops) 17파일 재구성
- T06 배치 B5+B6 (api-reference + research + developer + deployment + customer-cases) 55파일 재구성

**S05 (4 Tasks)** — ⬜ Todo
- T01 `## 관련 API` 대상 파일 목록 확정 (~50개)
  - 파이프라인/분석 문서 → 해당 API 엔드포인트 매핑
  - Overview 문서 → Gateway 엔드포인트 매핑
  - Frontend 문서 → 호출하는 API 매핑
- T02 API 엔드포인트 목록 수집 (api_specs/*.yaml 기준)
- T03 50개 파일에 `## 관련 API` 섹션 추가 (메서드 | 엔드포인트 | 설명 표)
- T04 API ↔ 문서 양방향 링크 정합성 검증

**S06 (3 Tasks)** — ⬜ Todo
- T01 route-map.mdx 재작성
  - 라우트 표에 `권한` 컬럼 추가
  - 공개 / 사용자 / 관리자 / 시스템 4구분
  - redirect, wildcard, wrapper route 별도 섹션
  - 각 행 마지막에 `[상세](...)` 링크
- T02 6개 페이지 상세 문서 (dashboard, project, blueprintflow, session, admin, pages) 강화
  - `## 접속 방법` 표 추가
  - anchor 기반 세부 섹션
  - 같은 화면 다중 경로 명시
- T03 라우트 수 ↔ 문서 표 행 수 1:1 정합성 검증

**S07 (3 Tasks)** — ⬜ Todo
- T01 표 형식 4종 표준 정의 + 비준수 파일 목록 추출
  ```
  Type A: | URL | 권한 | 설명 |
  Type B: | 경로 | 페이지 | 설명 | 가이드 |
  Type C: | 탭 | 설명 | 주요 동작 |
  Type D: | 기능 | 설명 |
  ```
- T02 비준수 표 17개 파일 수정
- T03 복합 페이지 10개에 명시적 anchor (`<a id="..."></a>`) 추가

**S08 (4 Tasks)** — ⬜ Todo
- T01 lint-style.sh 전체 실행 → 0 violation 확인
- T02 Starlight 빌드 (116페이지, 0 에러)
- T03 컨테이너 배포 + Playwright 검증 (5개 대표 페이지 스크린샷)
- T04 ACTIVE.md, COMPLETED.md 업데이트 + 커밋

## 의존성 그래프

```
S01 (규칙 정의)
 ├── S02 (frontmatter) ─────────────────┐
 ├── S03 (H1 + blockquote) ─────────────┤
 ├── S04 (섹션 순서) ── T02~T06 병렬 ──┤
 ├── S05 (관련 API) ────────────────────┤
 ├── S06 (라우트 강화) ─────────────────┤
 └── S07 (표 + anchor) ────────────────┤
                                        │
                                   S08 (검증)
```

- S01 완료 후 S02~S07 **모두 병렬 가능** (파일 겹침 있으나 수정 영역 다름)
- S04 내부의 T02~T06도 배치별 병렬 가능
- S08은 모든 Story 완료 후 실행

## 성공 기준

| 기준 | 목표 |
|------|------|
| tags frontmatter | 115/115 (100%) |
| H1 한글+영어 패턴 | 115/115 (100%) |
| blockquote 요약 | 115/115 (100%) |
| 섹션 순서 준수 | 115/115 (100%) |
| `## 관련 API` 섹션 | 대상 50개 파일 100% |
| 라우트 권한 구분 | route-map + 6개 페이지 상세 |
| 표 형식 통일 | 비준수 0개 |
| anchor 복합 문서 | 대상 10개 파일 100% |
| lint-style.sh | 0 violation |
| 빌드 | 116페이지, 0 에러 |

## 추정 작업량

| Story | 자동화 가능 | 수동 검토 | 예상 에이전트 수 |
|-------|-----------|----------|----------------|
| S01 | 80% | 규칙 검토 | 1 |
| S02 | 95% (스크립트) | 태그 검토 | 1 |
| S03 | 70% (스크립트) | 제목 검토 | 1 |
| S04 | 30% | 섹션 재배치 수동 | 6 (배치별) |
| S05 | 50% | API 매핑 수동 | 2 |
| S06 | 20% | 라우트 분석 수동 | 1 |
| S07 | 60% | 표 구조 수동 | 2 |
| S08 | 90% | 스크린샷 확인 | 1 |

**S04가 가장 큰 작업** — 35개 파일의 섹션 순서를 수동으로 재배치해야 함.
병렬 에이전트 6개로 배치별 처리 시 효율적.

---

*작성: Claude Code | 2026-03-11*
