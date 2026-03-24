# 진행 중인 작업

> **마지막 업데이트**: 2026-03-23
> **기준 커밋**: E07 Operational Excellence

---

## 현재 상태 요약

| 항목 | 값 |
|------|-----|
| **기술 스택** | FastAPI + React 19 + YOLO v11 + eDOCr2 + Docker |
| **API 서비스** | 21개 (전체 healthy) |
| **테스트** | 800개 통과 (gateway 450, web-ui 350, model 6) |
| **빌드 상태** | ✅ 정상 (tsc + build 에러 0) |
| **파일 크기** | 모두 600줄 이하 |
| **문서 사이트** | 15섹션 117페이지 (localhost:3001) — 100% 표준 준수 |

---

## Active Epic

### E04: AX 테스트 컴플렉스 온보딩 (🔵 In Progress — S01~S03 Done)

| Story | 상태 | 요약 |
|-------|------|------|
| S01 납품 패키지 템플릿 | ✅ Done | generate-package.sh + 5 templates |
| S02 커스터마이징 파이프라인 | ✅ Done | create_customer_api.py + test_coverage.py |
| S03 사용자 교육 체계 | ✅ Done | quick-start + manual + FAQ (120p 빌드) |
| S04 기존 3개사 통합 | ✅ Done | STATUS.md + README 3사 + techcross 스캐폴딩 |
| S05 신규 7개사 온보딩 | ⬜ Blocked | 기업 모집 중 |

**상세**: [.todo/epics/e04-ax-testcomplex/EPIC.md](epics/e04-ax-testcomplex/EPIC.md)

### E09: OD/ID/W 검출 방법론 다양화 (🔵 In Progress)

| Story | 상태 | 요약 |
|-------|------|------|
| S01 화살촉 모폴로지 검출 | ✅ Done | Ø 우선 분류, K 보완 (W 검출 +17) |
| S02 Dimension-Text-First | ✅ Done | Ø 방향 무관 분류, K 보완 (OD 검출 +20) |
| S03 Randomized Hough | ✅ Done | 15K iter, vote≥3 → 8~20개 원 검출 |
| S04 Ellipse Decomposition | ✅ Done | r_min+arc_angle 필터 → 33~46개 원 검출 |
| **앙상블 v2** | ✅ Done | K+S01+S02+S06 투표 → **48%→71%** (87개 배치, 목표 달성) |
| **앙상블 v3 (검증)** | ✅ Done | K-priority 전략 → GT 정확도 50%→83%, 타당성 41%→56% |
| **앙상블 v5 (최적화)** | ✅ Done | _extract_num 파싱 수정 + fallback OCR + W radial 공식 + NM 필터 + soft filter → GT 2/2 (100%) |
| S05 CircleNet DL | ⏸️ 보류 | 0.5M U-Net 학습 성공, 반지름 회귀 실패 — dense label 필요 |
| S06 YOLOv11-OBB + VLM | ✅ Done | OCR bbox label → mAP50=0.301 달성 (87개 도면) |
| S07 Florence-2 Zero-Shot | ✅ Done | 형상 이해 OK, OCR 부족 — LoRA fine-tune 데이터 필요 |
| S08 Werk24 벤치마크 | ⬜ 제외 | 사용자 요청으로 제외 |

**성과**: v2 71% → v3 GT 83% → **v5 GT 100% (2/2)**. _extract_num 파싱, fallback OCR, W radial 우선, NM 필터, soft filter 적용. 22개 도면 값 변경, k_priority 40→44.
**상세**: [.todo/epics/e09-dimension-detection-methods/EPIC.md](epics/e09-dimension-detection-methods/EPIC.md)

### E08: Gstack 운영체계 최대 도입 (✅ Done)

| Story | 상태 | 요약 |
|-------|------|------|
| S01 기준점 + 채택 매트릭스 | ✅ Done | pin 고정 + 27개 스킬 AX 채택 매트릭스 + `.gstack` 정책 확정 |
| S02 이중 UI 브라우저 QA | ✅ Done | web-ui Playwright 다중 webServer + `/bom/*` redirect fix + dual-ui smoke 2개 통과 |
| S03 `.claude` 체계 재배치 | ✅ Done | /review, /investigate, /plan-eng-review, /qa-only 추가 + 역할 매트릭스/agent README 정리 |
| S04 QA 시나리오 재편 | ✅ Done | AX 5개 시나리오 그룹 문서화 + BOM/도면 매칭 test id 보강 |
| S05 기존 훅 체인 재설계 | ✅ Done | 차단형 Bash/Write 훅 + `.gstack/state` freeze 정책 + 회귀 테스트 6개 |
| S06 인증/아티팩트 정책 | ✅ Done | auth matrix + `.gstack/auth` 정책 + Playwright storage state env 지원 |
| S07 smoke/full 롤아웃 | ✅ Done | `frontend-smoke` CI job + rollout guide + verify/command 문서 반영 |

**상세**: [.todo/epics/e08-gstack-max-adoption/EPIC.md](epics/e08-gstack-max-adoption/EPIC.md)

### E07: Operational Excellence — WeekdayCode 4축 적용 (✅ Done)

| Story | 상태 | 요약 |
|-------|------|------|
| S01 Web-UI 컴포넌트 테스트 | ✅ Done | 4개 카드 컴포넌트 46개 테스트 |
| S02 OCR A/B 비교 실측 | ✅ Done | 3엔진 비교 프레임워크 + GT 데이터 |
| S03 분석 원가 지표 API | ✅ Done | GET /admin/cost-report 엔드포인트 |
| S04 업로드 TTL + 접근 로그 | ✅ Done | 24시간 TTL + 이벤트 로깅 |
| S05 모델 서비스 CI 통합 | ✅ Done | table-detector-api 테스트 + CI job |
| S06 OCR 교체 데모 문서 | ✅ Done | ocr-engine-swap.mdx 신규 |
| S07 전체 검증 + 문서 갱신 | ✅ Done | 450+349+6 테스트, 117p 빌드 |

**상세**: [.todo/epics/e07-operational-excellence/EPIC.md](epics/e07-operational-excellence/EPIC.md)

### E06: Docs 콘텐츠 스타일 규격 적용 (✅ Done)

| Story | 상태 | 요약 |
|-------|------|------|
| S01 스타일 규칙 정의 + 검증 스크립트 | ✅ Done | rules 파일 + lint-style.sh |
| S02 Frontmatter 일괄 표준화 | ✅ Done | tags 115/115 추가 |
| S03 H1 제목 + blockquote 표준화 | ✅ Done | 한글(English) 115/115 |
| S04 섹션 순서 재구성 | ✅ Done | 115개 검증, 1개 수정 |
| S05 관련 API 섹션 추가 | ✅ Done | 42개 파일 API 표 추가 |
| S06 라우트 문서 강화 | ✅ Done | 권한 컬럼, 재작성 |
| S07 표 형식 + anchor 통일 | ✅ Done | 표 9개 표준화, anchor 18개 |
| S08 최종 검증 + 배포 | ✅ Done | lint 0 violation, 116p 빌드, 배포 |

**상세**: [.todo/epics/e06-docs-style-rewrite/EPIC.md](epics/e06-docs-style-rewrite/EPIC.md)

### E05: Docs-Site Starlight 마이그레이션 + 문서 표준화 (✅ Done)

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

*마지막 업데이트: 2026-03-23*
