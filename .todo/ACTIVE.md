# 진행 중인 작업

> **마지막 업데이트**: 2026-03-11
> **기준 커밋**: bbaff3b (feat: E05-S01 문서 표준화 완료)

---

## 현재 상태 요약

| 항목 | 값 |
|------|-----|
| **기술 스택** | FastAPI + React 19 + YOLO v11 + eDOCr2 + Docker |
| **API 서비스** | 21개 (전체 healthy) |
| **테스트** | 549개 통과 (gateway 364, web-ui 185) |
| **빌드 상태** | ✅ 정상 (tsc + build 에러 0) |
| **파일 크기** | 모두 600줄 이하 |
| **문서 사이트** | 15섹션 115페이지 (localhost:3001) — 100% 표준 준수 |

---

## Active Epic

### E05: Docs-Site Starlight 마이그레이션 + 문서 표준화

| Story | 상태 | 요약 |
|-------|------|------|
| S01 문서 구조 표준화 | ✅ Done | 115개 전체 100% (frontmatter, blockquote, 관련 문서) |
| S02 Starlight POC | ✅ Done (WT4) | Go 판정 (빌드 3.5초, Pagefind 내장, React Island 동작) |
| S03 콘텐츠 마이그레이션 | ⬜ Todo | Node 22 업그레이드 후 진행 |
| S04 TSX 컴포넌트 마이그레이션 | ⬜ Todo | FlowDiagram, SequenceDiagram 포팅 |
| S05 라우트 맵 문서화 | ✅ Done | 13개 라우트 100%, 6개 상세 페이지 |
| S06 문서 품질 검증 | ✅ Done | lint-docs.sh, onBrokenLinks: throw |

**상세**: [.todo/epics/e05-docs-starlight/EPIC.md](epics/e05-docs-starlight/EPIC.md)

### E01: 성과발표회 PPT 완성 (~03-06)

| Story | 상태 | 요약 |
|-------|------|------|
| [S01 내용 검증](epics/e01-presentation/S01-content-verification.md) | ✅ Done | PDF+코드 교차검증, 6개 불일치 수정 |
| [S02 디자인 보완](epics/e01-presentation/S02-design-polish.md) | ✅ Done | 메트릭 카드 11개 추가 (슬라이드 7,8,13) |
| [S03 대표자 검토](epics/e01-presentation/S03-ceo-review.md) | ⬜ Todo | 기타의견 작성 + 제출 |

**상세**: [.todo/epics/e01-presentation/EPIC.md](epics/e01-presentation/EPIC.md)

### E03: 동서기연 BOM 추출 자동화 (~03-21)

| Story | 상태 | 요약 |
|-------|------|------|
| [S01 소재 사이즈 추출](epics/e03-dsebearing/S01-material-size-extraction.md) | ✅ Done | 단품 3종 230개 치수 추출·검증 완료 |
| [S02 BOM 계층 구조](epics/e03-dsebearing/S02-bom-hierarchy.md) | ✅ Done | ASSY 7·SUB 16·PART 303 분류 완료 |
| [S03 결과 전달](epics/e03-dsebearing/S03-result-delivery.md) | 🔵 In Progress | 문서 완료, 고객 전달 대기 |

**Blueprint AI BOM 프로젝트**: `b97237fd` (BOM 326개 기존 임포트, 이름 변경)
**상세**: [.todo/epics/e03-dsebearing/EPIC.md](epics/e03-dsebearing/EPIC.md)

---

## 참조 문서

| 문서 | 위치 |
|------|------|
| 백로그 (Epic 인덱스) | `.todo/BACKLOG.md` |
| 완료 아카이브 | `.todo/COMPLETED.md` |
| Claude 전략 | `.todo/CLAUDE_CODE_STRATEGIES.md` |

---

*마지막 업데이트: 2026-03-11*
