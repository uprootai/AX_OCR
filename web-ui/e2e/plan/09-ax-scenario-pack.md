# AX 핵심 시나리오 팩 (AX Scenario Pack)

> 기준일: 2026-03-23
> 목적: AX의 실제 업무 흐름을 Playwright 실행 표면과 1:1로 연결
> 관련 Story: `E08 / S04`

## 1. 시나리오 그룹

| 그룹 | 목적 | 실행 표면 | 우선순위 |
|------|------|-----------|----------|
| AX-SMOKE | dual-ui 진입, `/bom/*` redirect, 기본 shell 확인 | `npm run test:e2e:dual-ui` | P0 |
| AX-BOM-PROJECT | 프로젝트 상세에서 BOM 업로드/계층/도면 매칭/세션 생성 진입 | 신규/확장 Playwright spec | P0 |
| AX-WORKFLOW | Blueprint AI BOM workflow에서 업로드/검출/검토 큐 확인 | `blueprint-ai-bom*.spec.ts` | P1 |
| AX-DIMENSION | Dimension Lab 진입, 탭 렌더링, 배치/리더보드 확인 | 신규 Playwright spec | P1 |
| AX-OVERLAY | bbox/overlay 시각 신호 확인 | 기존 workflow/dimension 흐름 + screenshot 근거 | P1 |

## 2. 핵심 시나리오

### AX-001: web-ui → BOM frontend redirect smoke

- 시작점: `http://localhost:5174/dashboard`
- 액션: `/bom/workflow`로 이동
- 기대 결과:
  - URL이 `http://localhost:5021/bom/workflow`로 이동
  - workflow 화면에서 파일 입력 또는 세션/워크플로우 텍스트가 보임
- 실행: `cd web-ui && npm run test:e2e:dual-ui`
- artifact: `.gstack/reports/playwright/test-results/...`

### AX-002: 프로젝트 상세에서 BOM 워크플로우 진입

- 시작점: `web-ui/src/pages/project/ProjectDetailPage.tsx`
- 핵심 표면:
  - `data-testid="bom-workflow-section"`
  - `data-testid="bom-upload-button"`
  - `data-testid="bom-load-sample-button"`
  - `data-testid="bom-workflow-step-0..4"`
- 기대 결과:
  - BOM 섹션 렌더링
  - 샘플 BOM 또는 업로드 진입 버튼이 보임
  - BOM 데이터가 있으면 stepper가 현재 단계까지 활성화됨

### AX-003: 도면 매칭 테이블 확인

- 핵심 표면:
  - `data-testid="drawing-match-table"`
  - `data-testid="drawing-match-folder-input"`
  - `data-testid="drawing-match-start-button"`
  - `data-testid="drawing-match-summary"`
  - `data-testid="drawing-match-row-*"`
- 기대 결과:
  - 폴더 경로 입력 가능
  - 매칭 시작 버튼 enable/disable 상태가 폴더 입력과 일치
  - 결과가 있을 때 summary와 row가 표시됨

### AX-004: workflow 세션/검토 큐 확인

- 시작점: `http://localhost:5021/bom/workflow`
- 기대 결과:
  - 파일 업로드 입력 존재
  - workflow/세션 UI가 렌더링
  - 검출 후 검토 섹션 또는 결과 섹션으로 진입 가능
- 실행 후보:
  - `blueprint-ai-bom.spec.ts`
  - `blueprint-ai-bom-comprehensive.spec.ts`

### AX-005: Dimension Lab 진입과 탭 렌더링

- 시작점: `http://localhost:5021/bom/dimension-lab`
- 기대 결과:
  - 헤더 `Dimension Lab`
  - `개별 분석`, `배치 평가`, `리더보드` 탭 렌더링
  - 세션/배치 통계 카드 표시

### AX-006: overlay signal 확인

- 표면:
  - workflow 이미지 오버레이
  - `svgOverlay.ts` 기반 bbox/text/line overlay
  - Dimension Lab overlay
- 기대 결과:
  - SVG 또는 canvas overlay 노드가 렌더링
  - 실패 시 screenshot/trace를 남겨 시각 차이를 비교 가능

## 3. fixture / mock 전략

| 시나리오 | 전략 |
|----------|------|
| AX-SMOKE | 실제 dual-ui dev server 사용 |
| AX-BOM-PROJECT | 샘플 BOM 파일 또는 프로젝트 fixture 필요 |
| AX-WORKFLOW | `web-ui/e2e/fixtures/api-fixtures.ts` 재사용 |
| AX-DIMENSION | 실제 backend가 있으면 live, 없으면 render smoke 우선 |
| AX-OVERLAY | screenshot + DOM signal 중심, 픽셀 비교는 후순위 |

## 4. flaky 포인트

| 영역 | 리스크 | 대응 |
|------|--------|------|
| workflow API | backend/service 미기동 | blocked로 보고하고 수정 시도하지 않음 |
| upload | sample file 경로 의존 | fixture 경로 명시 + 없으면 skip reason 출력 |
| overlay | OCR/검출 결과 가변성 | DOM signal + screenshot evidence 조합 |
| redirect | env/port drift | `VITE_BLUEPRINT_AI_BOM_FRONTEND_URL`, `BOM_UI_ORIGIN`을 source로 사용 |

## 5. 재시도 정책

- Playwright 기본 재시도: local 1회, CI 2회
- `dual-ui-smoke`는 redirect/entry smoke로 유지하고 시나리오를 과적재하지 않는다
- flaky가 의심되면 screenshot/video/trace를 먼저 보고 selector 문제와 backend 문제를 분리한다

## 6. 다음 자동화 후보

1. 프로젝트 상세 페이지용 `project-bom-workflow.spec.ts`
2. Dimension Lab 진입 smoke
3. overlay DOM signal 전용 smoke
