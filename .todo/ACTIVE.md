# 진행 중인 작업

> **마지막 업데이트**: 2026-02-04
> **기준 커밋**: 9c278b0 (feat: BOM HITL 치수 전용 워크플로우 완성, Executor 리팩토링, UI 하이라이트 연동)

---

## 미커밋 변경 요약 — DSE Bearing BOM 계층 워크플로우 (Phase 1 + Phase 2 + Phase 3)

> 동서기연 1차 미팅 결과 반영: BOM PDF → 계층 파싱 → 단품 세션 일괄 생성 → 프로젝트 견적 집계

### 변경 카테고리

| 영역 | 수정 | 신규 | 핵심 변경 |
|------|------|------|----------|
| **BOM Backend** | 5개 | 4개 | session metadata, BOM PDF parser, drawing matcher, quotation service |
| **BOM Frontend** | 2개 | 5개 | project API BOM 메서드, BOM 워크플로우 위저드 UI, MaterialBreakdown |
| **Gateway API** | 1개 | 0 | BOM executor project_id + metadata 전달 |
| **Web-UI** | 1개 | 0 | DSE 1-1 수정, 2-1/2-2/2-3 숨김, hidden 필터 |

---

## Phase 1 백엔드 변경 상세

### BOM PDF Parser (신규)
- **파일**: `services/bom_pdf_parser.py`
- RGB 색상 기반 레벨 감지 (PINK=ASSY, BLUE=SUB, WHITE=PART)
- PDF 테이블 파싱 → BOM 계층 구조 반환

### Drawing Matcher (신규)
- **파일**: `services/drawing_matcher.py`
- 파일명 ↔ 도면번호 매칭 (정규화 비교)
- 매칭 결과 + needs_quotation 필터링

### BOM Item Schema (신규)
- **파일**: `schemas/bom_item.py`
- BOMItem, BOMHierarchyResponse, DrawingMatchResult 등 데이터 모델

### Project/Session 확장 (수정 5개)
- project_router: 6개 BOM 엔드포인트 추가
- session_router: metadata 지원
- project_service: BOM 파싱/매칭/세션 생성
- session_service: metadata 전달, 일괄 생성

---

## Phase 2 프론트엔드 변경 상세

### 1. API 타입 내보내기 수정

**파일**: `lib/api/index.ts` (+4 타입)

BOMItem, BOMHierarchyResponse, DrawingMatchResult, SessionBatchCreateResponse 타입 re-export 추가

### 2. BOMHierarchyTree (신규, 247줄)

**파일**: `pages/project/components/BOMHierarchyTree.tsx`

- 재귀 TreeNode 컴포넌트로 BOM 계층 트리뷰 렌더링
- PINK(ASSY) / BLUE(SUB) / WHITE(PART) 색상 코딩
- 펼치기/접기 (개별 + 전체)
- 요약 통계 바 (전체/ASSY/SUB/PART 개수)

### 3. DrawingMatchTable (신규, 171줄)

**파일**: `pages/project/components/DrawingMatchTable.tsx`

- 도면 폴더 경로 입력 + 매칭 실행 버튼
- 매칭 결과 프로그레스 바 (매칭/미매칭 %)
- 견적 대상(needs_quotation) 항목만 테이블 표시
- 매칭/미매칭 상태 뱃지

### 4. QuotationDashboard (신규 → Phase 3에서 확장, 218줄)

**파일**: `pages/project/components/QuotationDashboard.tsx`

- 4개 통계 카드 (견적대상/세션생성/분석완료/견적완료)
- 필터 (전체/완료/진행중/미생성)
- BOM items ↔ sessions 조인 테이블
- 세션 링크 → /workflow?session= 이동

### 5. BOMWorkflowSection (신규, 377줄)

**파일**: `pages/project/components/BOMWorkflowSection.tsx`

- 5단계 위저드: BOM 업로드 → 계층 트리 → 도면 매칭 → 세션 생성 → 견적 현황
- 아이콘 스테퍼 UI (완료=green, 활성=blue, 비활성=gray)
- 자동 시작 위치 감지 (project 상태 기반)
- 단계별 조건 네비게이션

### 6. ProjectDetailPage 수정 (+8줄)

**파일**: `pages/project/ProjectDetailPage.tsx`

- BOMWorkflowSection import 추가
- 프로젝트 정보 grid와 세션 목록 사이에 BOMWorkflowSection 렌더링

---

## Phase 3 견적 집계 변경 상세

### Quotation Schema (신규)
- **파일**: `schemas/quotation.py`
- QuotationSummary, MaterialGroup, QuotationExportRequest 등

### Quotation Service (신규)
- **파일**: `services/quotation_service.py`
- 세션별 BOM 데이터 읽기 → 재질별 그룹핑
- PDF/Excel 내보내기 지원
- `_build_session_item()` → `session.json` → `bom_data.summary` 읽기

### MaterialBreakdown (신규)
- **파일**: `pages/project/components/MaterialBreakdown.tsx`
- 재질별 분류 테이블 (수량, 중량, 금액)
- 원형 차트 / 막대 그래프 시각화

### QuotationDashboard 확장
- 통계 카드에 MaterialBreakdown 연동
- 다운로드 버튼 (PDF/Excel)

---

## 프로젝트 상태

| 항목 | 결과 |
|------|------|
| **Python 문법** | ✅ 12/12 파일 정상 |
| **web-ui tsc** | ✅ 에러 0개 |
| **bom frontend tsc** | ✅ 에러 0개 |
| **bom frontend build** | ✅ 빌드 성공 |
| **데이터 흐름** | ✅ bom_service → session.json → quotation_service 통합 갭 없음 |

---

## 다음 단계

- [x] BOMHierarchyTree 프론트엔드 컴포넌트
- [x] DrawingMatchTable 프론트엔드 컴포넌트
- [x] QuotationDashboard 프론트엔드 컴포넌트
- [x] BOMWorkflowSection 위저드 컨트롤러
- [x] ProjectDetailPage 확장 (BOM 섹션 추가)
- [x] 견적 집계/출력 서비스

---

*마지막 업데이트: 2026-02-04*
