# 진행 중인 작업

> **마지막 업데이트**: 2026-03-30
> **기준 커밋**: E12 Dimension Lab 고도화

---

## 🔴 현재 진행 중

### E12: Dimension Lab — OD/ID/W 고도화 (🔵 In Progress — Phase 2)

| Phase | 상태 | 요약 |
|-------|------|------|
| Phase 1: GT 확보 + Baseline | ✅ Done | GT 7건 확보, K geometry 0/7 → 세션힌트 1/7 |
| Phase 2: SECTION 감지 | 🔵 In Progress | **세로스캔+위치+힌트 = OD 5/7, ID 6/7** |
| Phase 3: DL 모델 | ⬜ Todo | CircleNet / Florence-2 LoRA |
| Phase 4: 앙상블 v7 | ⬜ Todo | 전략 통합 + 견적 자동화 |
| Phase 5: 고객 납품 | ⬜ Todo | BMT 프로젝트 연계 |

**앙상블 v6 결과**: OD 5/7(71%), ID 5/7(71%), W 5/7(71%) — 전체 15/21(71%)
**v5 대비**: OD +3, ID +2, W +3 개선
**핵심 기법**: SEC-priority 전략 (ASSY→SEC 우선, Part→K 우선) + 세로 텍스트 슬라이딩 스캔
**상세**: `.todo/epics/E12_DIMENSION_LAB_ADVANCEMENT/EPIC.md`
**실험 문서**: docs-site `customer-cases/dsebearing/e12-section-detection`

---

### E10: BMT GAR 배치도 TAG 추출 OCR 실험 (✅ Done — S01~S06 전체 완료)

| Story | 상태 | 요약 |
|-------|------|------|
| S01 OCR 엔진별 벤치마크 | ✅ Done | PaddleOCR 41.7% 1위, 7개 엔진 비교 |
| S02 뷰별 레이아웃 분리 | ✅ Done | 5개 뷰 크롭 → **41.7%→95.8%** (+54%p) |
| S03 TAG vs 치수 필터링 | ✅ Done | 39개→24개 TAG, 노이즈 15개 제거 |
| S04 Part List/BOM 자동 매칭 | ✅ Done | 19건 매칭 + **3건 불일치 자동 검출** |
| S05 멀티모달 VLM 실험 | ✅ Done | Claude Vision GT 24개 TAG 확립 |
| S06 BlueprintFlow 템플릿 | ✅ Done | BMT 카테고리 + 7노드 파이프라인 등록 |

**성과**: GAR 이미지→OCR(95.8%)→필터(100%)→BOM 매칭 → 불일치 3건 자동 검출 + BlueprintFlow 템플릿 등록
**상세**: [.todo/epics/e10-bmt-gar-ocr/EPIC.md](epics/e10-bmt-gar-ocr/EPIC.md)

### E12: BMT 세션 UI — Human-in-the-Loop 도면 검증 (✅ Done — S01~S07 전체 완료)

| Story | 상태 | 요약 |
|-------|------|------|
| S01 크롭 이미지 API | ✅ Done | 백엔드: bmt_router.py 9개 엔드포인트 + Docker 배포 |
| S02 크롭 뷰어 | ✅ Done | 프론트: 9개 크롭 카드 + TAG 배지 + 클릭 이동 |
| S03 TAG 확인/수정 | ✅ Done | 프론트: 크롭 OCR 이미지 + TAG 승인/삭제 HITL |
| S04 BOM 매칭 판정 | ✅ Done | 프론트: 불일치 판정 (실제 오류/정상 차이) + 필터 테이블 |
| S05 파이프라인 실행 | ✅ Done | 백엔드: 비동기 실행 + 폴링 / 프론트: 6단계 진행 바 |
| S06 리포트 | ✅ Done | 백엔드: FileResponse Excel 다운로드 / 프론트: 다운로드 버튼 |
| S07 통합 | ✅ Done | 4단계 탭 UI + S05/S06 연동 완료 |

**전체 완료** | 접근: `:3000/bom/workflow?session=2e6bae64`
**상세**: [.todo/epics/e12-bmt-session-ui/EPIC.md](epics/e12-bmt-session-ui/EPIC.md)

### E11: BMT 뷰 자동 분리 + executor 구현 (✅ Done — S01~S06 전체 완료)

| Story | 상태 | 요약 |
|-------|------|------|
| S01 뷰 라벨 OCR 검출 | ✅ Done | 6개 뷰 라벨 자동 검출 (BOTTOM/FRONT/TOP/RIGHT/A VIEW) |
| S02 경계선 섹션 범위 | ✅ Done | 라벨 중심점 → 2행3열 그리드 경계 자동 계산 |
| S03 자동 분리 (하드코딩 0) | ✅ Done | **Min-Content 경계**: 인접 VIEW 사이 콘텐츠 최소점 = 경계 |
| S04 OCR 앙상블 | ✅ Done | PaddleOCR 23/24 + Tesseract B03 보완 = **24/24 = 100%** |
| S05 executor 4개 구현 | ✅ Done | view_splitter + tag_filter + excel_lookup + bom_check |
| S06 End-to-End 파이프라인 | ✅ Done | `bmt_e2e_pipeline.py` 150줄, 1줄 실행 → Excel 리포트 |

**E2E 결과**: 이미지1장 → 25 TAG → 19 매칭 + **3건 불일치 자동 검출** (V06/PI02/B02)
**최종 알고리즘**: VIEW 라벨 OCR → Min-Content 경계 → PaddleOCR+Tesseract → Part List → ERP BOM → Excel 리포트
**상세**: [.todo/epics/e11-bmt-auto-view/EPIC.md](epics/e11-bmt-auto-view/EPIC.md)

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
