# S04: 섹션 순서 재구성

> **상태**: ⬜ Todo
> **선행**: S01 (3종 템플릿)
> **산출물**: ~35개 파일 섹션 순서 재배치

---

## 목표

문서 유형별 섹션 순서 템플릿을 정의하고,
비준수 파일 ~35개의 섹션을 재배치한다.

## 섹션 순서 템플릿 (3종)

### Type A: Overview (index.mdx)

```
---
frontmatter
---
# 제목 (Title)
> blockquote 요약

## 개요
(소개, 핵심 기능 요약)

## 아키텍처 / 구조
(FlowDiagram, 시스템 구성도)

## 하위 페이지
| 페이지 | 설명 |
|--------|------|

## 관련 API
| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|

## 관련 문서
- [링크](경로) — 설명
```

### Type B: Page (페이지 상세)

```
---
frontmatter
---
# 제목 (Title)
> blockquote 요약

## 접속 방법
| URL | 권한 | 설명 |
|-----|------|------|

## 페이지 구조 / 탭 구성
| 탭 | 설명 | 주요 동작 |
|----|------|----------|

## 상세 설명
(핵심 동작, 상태 전이, 필터, 검색 등)

## 관련 API
| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|

## 관련 문서
```

### Type C: API Reference

```
---
frontmatter
---
# 제목 (Title)
> blockquote 요약

## 기본 정보
| 항목 | 값 |
|------|-----|

## 파라미터
| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|

## 응답 형식
(JSON 구조, 필드 설명)

## 사용 예시
(curl, Python 코드)

## 리소스 요구사항
| 항목 | 값 |
|------|-----|

## 관련 문서
```

## Tasks

### T01 파일별 타입 분류

115개 파일을 3종 타입으로 분류:
- Type A (Overview): index.mdx 파일 (~16개)
- Type B (Page): frontend/pages/, deployment/ 등 (~30개)
- Type C (API): api-reference/ (~19개)
- 기타: research/ (자유 형식, 최소 규칙만)

### T02 배치 B1: system-overview + analysis-pipeline (12파일)

| 파일 | 타입 | 현재 순서 | 변경 필요 |
|------|------|----------|----------|
| system-overview/index.mdx | A | 개요→아키→서비스→기술→포트 | ⚠️ 관련 API 추가 |
| system-overview/architecture-map.mdx | B | 토폴로지→통신→포트 | ⚠️ 접속 방법 추가 |
| analysis-pipeline/index.mdx | A | 개요→단계→특성 | ⚠️ 관련 API 추가 |
| ... | ... | ... | ... |

각 파일의 H2 섹션을 템플릿 순서로 재배치.
**콘텐츠 삭제 없음** — 순서만 변경하고 누락 섹션 추가.

### T03 배치 B2: blueprintflow + agent-verification + bom-generation (15파일)
### T04 배치 B3: pid-analysis + batch-delivery + quality-assurance (16파일)
### T05 배치 B4: frontend + devops (17파일)
### T06 배치 B5+B6: api-reference + research + developer + deployment + customer-cases (55파일)

T02~T06은 **병렬 워크트리 에이전트**로 처리 가능.

## 완료 조건

- [ ] 115/115 파일이 해당 타입 템플릿 순서 준수
- [ ] 콘텐츠 누락 없음 (diff 확인)
- [ ] `## 관련 문서`가 항상 마지막 섹션
- [ ] Starlight 빌드 성공
