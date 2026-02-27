---
description: Plan an Epic by breaking it into stories with specs and acceptance criteria
---

# /plan-epic — Epic 기획 커맨드

Plan Mode에서 다음을 수행합니다:

## 1. 요구사항 파악

사용자에게 질문:
- 무엇을 만드는가? (기능/산출물)
- 누구를 위한 것인가? (고객/내부)
- 언제까지? (기한)
- 성공 기준은? (측정 가능한 조건)

## 2. Epic 정의서 작성

`.todo/templates/EPIC_TEMPLATE.md`를 기반으로:
- `.todo/epics/{epic-id}/EPIC.md` 생성
- Epic ID는 BACKLOG.md의 마지막 번호 + 1

## 3. Story 분해

Epic을 3-7개의 Story로 분해:
- 각 Story는 **하나의 Claude 세션에서 완료 가능한 단위**
- `.todo/templates/STORY_TEMPLATE.md` 기반으로 생성
- 각 Story에 포함 필수:
  - 에이전트가 바로 실행 가능한 "설명" 섹션
  - 측정 가능한 "완료 조건"
  - 변경될 파일 목록 "변경 범위"
  - 복사-실행 가능한 "에이전트 지시"

## 4. Story 간 의존성 표시

```
S01 → S02 → S03  (순차)
S02 + S03         (병렬 가능)
```

## 5. 등록

- BACKLOG.md의 Epic 인덱스에 추가
- ACTIVE.md에 현재 진행 Epic으로 등록

## 6. 확인

```bash
ls .todo/epics/{epic-id}/
cat .todo/epics/{epic-id}/EPIC.md
```

## Story 크기 기준

| 크기 | 기준 | 예시 |
|------|------|------|
| 적정 | 1-3시간 | API 1개 추가, UI 컴포넌트 1개 |
| 너무 큼 | 4시간+ | 분해 필요 |
| 너무 작음 | 15분 이하 | 상위 Story에 병합 |
