# 진행 중인 작업

> **마지막 업데이트**: 2026-02-27
> **기준 커밋**: 2070e1a (feat: BMAD-Lite 워크플로 도입 + PPT S02 디자인 보완)

---

## 현재 상태 요약

| 항목 | 값 |
|------|-----|
| **기술 스택** | FastAPI + React 19 + YOLO v11 + eDOCr2 + Docker |
| **API 서비스** | 21개 (전체 healthy) |
| **테스트** | 549개 통과 (gateway 364, web-ui 185) |
| **빌드 상태** | ✅ 정상 (tsc + build 에러 0) |
| **파일 크기** | 모두 600줄 이하 |
| **문서 사이트** | 14섹션 101페이지 (localhost:3001) |

---

## Active Epic

### E01: 성과발표회 PPT 완성 (~03-06)

| Story | 상태 | 요약 |
|-------|------|------|
| [S01 내용 검증](epics/e01-presentation/S01-content-verification.md) | ✅ Done | PDF+코드 교차검증, 6개 불일치 수정 |
| [S02 디자인 보완](epics/e01-presentation/S02-design-polish.md) | ✅ Done | 메트릭 카드 11개 추가 (슬라이드 7,8,13) |
| [S03 대표자 검토](epics/e01-presentation/S03-ceo-review.md) | ⬜ Todo | 기타의견 작성 + 제출 |

**상세**: [.todo/epics/e01-presentation/EPIC.md](epics/e01-presentation/EPIC.md)

### E02: 테크로스 P&ID 자동 설계 검증 (~03-21)

| Story | 상태 | 요약 |
|-------|------|------|
| [S01 파이프라인 테스트](epics/e02-techcross/S01-pipeline-test.md) | ✅ Done | YOLO 257건, OCR 141건, BWMS API 60-70% 기구현 |
| [S02 BWMS 태그 인식](epics/e02-techcross/S02-bwms-tag-recognition.md) | ✅ Done | 6/10 장비 검출 (NoneType+bbox+OCR 3건 수정) |
| [S03 Excel 출력](epics/e02-techcross/S03-excel-export.md) | ✅ Done | 버그 3건 수정, Excel 2종 출력 성공 |
| [S04 BWMS 규칙](epics/e02-techcross/S04-bwms-rules.md) | ⬜ Todo | Design Checker 규칙 5개 |
| [S05 프리셋 템플릿](epics/e02-techcross/S05-blueprintflow-preset.md) | ⬜ Todo | BlueprintFlow 테크로스 전용 |
| [S06 E2E 검증](epics/e02-techcross/S06-e2e-validation.md) | ⬜ Todo | 통합 테스트 + 체크리스트 매핑 |

**상세**: [.todo/epics/e02-techcross/EPIC.md](epics/e02-techcross/EPIC.md)

---

## 참조 문서

| 문서 | 위치 |
|------|------|
| 백로그 (Epic 인덱스) | `.todo/BACKLOG.md` |
| 완료 아카이브 | `.todo/COMPLETED.md` |
| Claude 전략 | `.todo/CLAUDE_CODE_STRATEGIES.md` |

---

*마지막 업데이트: 2026-02-27*
