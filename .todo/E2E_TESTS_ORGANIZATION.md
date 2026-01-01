# E2E 테스트 구조 및 조직

> 작성일: 2026-01-01
> 상태: 신규 추가됨 (미커밋)
> 총 테스트 코드: ~5,500줄

---

## 1. 새로 추가된 파일 구조

```
web-ui/e2e/
├── api/                    # API 테스트 (13개 파일, 4,740줄)
│   ├── analysis.spec.ts    # 659줄 - 분석 API
│   ├── bom.spec.ts         # 271줄 - BOM 생성 API
│   ├── classification.spec.ts # 272줄 - 분류 API
│   ├── config.spec.ts      # 225줄 - 설정 API
│   ├── detection.spec.ts   # 447줄 - 검출 API
│   ├── edge-cases.spec.ts  # 521줄 - 엣지 케이스
│   ├── feedback.spec.ts    # 238줄 - 피드백 API
│   ├── performance.spec.ts # 444줄 - 성능 테스트
│   ├── relations.spec.ts   # 226줄 - 관계 분석 API
│   ├── sessions.spec.ts    # 321줄 - 세션 관리 API
│   ├── settings.spec.ts    # 206줄 - 설정 API
│   ├── techcross.spec.ts   # 500줄 - TECHCROSS 워크플로우
│   └── verification.spec.ts # 410줄 - 검증 API
├── fixtures/               # 테스트 픽스처 (242줄)
│   ├── api-fixtures.ts     # Worker-scoped 테스트 픽스처
│   └── images/             # 테스트 이미지 디렉토리
├── plan/                   # 테스트 계획 문서 (9개)
│   ├── README.md           # 테스트 계획 개요
│   ├── 01-api-endpoints.md # API 엔드포인트 테스트 계획
│   ├── 02-ui-interactions.md # UI 상호작용 테스트 계획
│   ├── 03-techcross-workflow.md # TECHCROSS 워크플로우 계획
│   ├── 04-hyperparameters.md # 하이퍼파라미터 테스트 계획
│   ├── 05-edge-cases.md    # 엣지 케이스 테스트 계획
│   ├── 06-integration.md   # 통합 테스트 계획
│   ├── 07-data-fixtures.md # 테스트 데이터 픽스처 계획
│   └── 08-test-matrix.md   # 테스트 매트릭스
├── ui/                     # UI 테스트 (1개 파일, 503줄)
│   └── workflow.spec.ts    # 워크플로우 UI 테스트
├── blueprint-ai-bom.spec.ts # BOM 테스트
└── blueprint-ai-bom-comprehensive.spec.ts # BOM 종합 테스트
```

---

## 2. API 테스트 상세 (13개 파일)

### 2.1 테스트 대상별 분류

| 파일명 | 테스트 대상 | 라인 수 | 테스트 케이스 |
|--------|------------|---------|--------------|
| `analysis.spec.ts` | 분석 API (치수, 연결성, 경로) | 659 | 분석 결과, 치수 추출, 연결성 분석 |
| `bom.spec.ts` | BOM 생성 API | 271 | BOM 생성, 형식 변환 |
| `classification.spec.ts` | 분류 API | 272 | 분류, 신뢰도 필터링 |
| `config.spec.ts` | 설정 API | 225 | 설정 CRUD |
| `detection.spec.ts` | 검출 API | 447 | YOLO 검출, 필터링, 페이지네이션 |
| `edge-cases.spec.ts` | 엣지 케이스 | 521 | 빈 입력, 특수 문자, XSS 방지 |
| `feedback.spec.ts` | 피드백 API | 238 | 피드백 제출, 조회 |
| `performance.spec.ts` | 성능 테스트 | 444 | 응답 시간, 동시 요청, 메모리 |
| `relations.spec.ts` | 관계 분석 API | 226 | 심볼 관계, 연결 분석 |
| `sessions.spec.ts` | 세션 관리 API | 321 | 세션 CRUD, 만료 |
| `settings.spec.ts` | 설정 API | 206 | 사용자 설정 |
| `techcross.spec.ts` | TECHCROSS 워크플로우 | 500 | Valve Signal, Equipment, Checklist |
| `verification.spec.ts` | 검증 API | 410 | Human-in-the-Loop 검증 큐 |

### 2.2 테스트 픽스처 (api-fixtures.ts)

```typescript
// Worker-scoped 픽스처 (242줄)
- testSession: 테스트 세션 자동 생성/정리
- testImage: 테스트 이미지 Base64
- apiClient: Axios 인스턴스 (타임아웃 설정)
- cleanupSession: 세션 정리 함수
```

---

## 3. 테스트 계획 문서 (plan/)

| 파일명 | 내용 | 라인 수 |
|--------|------|---------|
| `README.md` | 테스트 계획 개요 및 인덱스 | ~200 |
| `01-api-endpoints.md` | API 엔드포인트별 테스트 케이스 | ~500 |
| `02-ui-interactions.md` | UI 상호작용 시나리오 | ~500 |
| `03-techcross-workflow.md` | TECHCROSS 요구사항 검증 | ~700 |
| `04-hyperparameters.md` | 하이퍼파라미터 변경 테스트 | ~500 |
| `05-edge-cases.md` | 엣지 케이스 및 에러 처리 | ~500 |
| `06-integration.md` | 통합 테스트 시나리오 | ~400 |
| `07-data-fixtures.md` | 테스트 데이터 픽스처 정의 | ~400 |
| `08-test-matrix.md` | 테스트 매트릭스 및 커버리지 | ~300 |

---

## 4. UI 테스트 (ui/)

| 파일명 | 테스트 대상 | 라인 수 |
|--------|------------|---------|
| `workflow.spec.ts` | 워크플로우 UI | 503 |

**테스트 케이스**:
- 세션 생성/선택
- 이미지 업로드
- 검출 실행
- 결과 확인
- BOM 생성
- 검증 워크플로우

---

## 5. 기존 E2E 테스트 파일 (루트)

| 파일명 | 테스트 대상 |
|--------|------------|
| `dashboard.spec.ts` | 대시보드 기능 |
| `dashboard-api-add.spec.ts` | API 추가 기능 |
| `dashboard-stop-all.spec.ts` | 전체 중지 기능 |
| `navigation.spec.ts` | 내비게이션 |
| `blueprintflow.spec.ts` | BlueprintFlow 기본 |
| `hyperparameter-changes.spec.ts` | 하이퍼파라미터 변경 |
| `hyperparameter-integration.spec.ts` | 하이퍼파라미터 통합 |
| `node-comprehensive.spec.ts` | 노드 종합 테스트 |
| `pid-analysis.spec.ts` | P&ID 분석 |
| `template-comprehensive.spec.ts` | 템플릿 종합 |
| `template-execution.spec.ts` | 템플릿 실행 |
| `templates.spec.ts` | 템플릿 기본 |
| `image-persist-debug.spec.ts` | 이미지 지속성 디버그 |
| `blueprint-ai-bom.spec.ts` | BOM 기본 |
| `blueprint-ai-bom-comprehensive.spec.ts` | BOM 종합 |

---

## 6. 결정 필요 사항

### 6.1 커밋 여부

- [ ] 새 E2E 테스트 파일들을 커밋할 것인가?
- [ ] `plan/` 디렉토리는 테스트 계획 문서 (커밋 권장)
- [ ] `playwright-report/trace/` 는 `.gitignore`에 추가해야 함

### 6.2 테스트 실행 확인

```bash
# API 테스트만 실행
cd web-ui
npx playwright test e2e/api/ --reporter=list

# UI 테스트만 실행
npx playwright test e2e/ui/ --reporter=list

# 전체 테스트
npx playwright test

# 특정 테스트 파일 실행
npx playwright test e2e/api/techcross.spec.ts
```

### 6.3 CI/CD 통합

- [ ] GitHub Actions에 새 테스트 디렉토리 포함 여부
- [ ] 테스트 타임아웃 설정 확인 (API 테스트는 더 긴 타임아웃 필요)
- [ ] 병렬 실행 설정 (Worker 수 조정)

---

## 7. 파일 구조 권장사항 (최종)

```
web-ui/e2e/
├── api/                    # API 테스트 (백엔드 API 직접 호출)
│   ├── analysis.spec.ts
│   ├── bom.spec.ts
│   └── ...
├── ui/                     # UI 테스트 (브라우저 상호작용)
│   ├── workflow.spec.ts
│   ├── dashboard.spec.ts   # 기존 파일 이동 권장
│   └── ...
├── integration/            # 통합 테스트 (API + UI)
│   └── ...
├── fixtures/               # 공통 픽스처
│   ├── api-fixtures.ts
│   ├── ui-fixtures.ts      # 필요시 추가
│   └── images/
├── plan/                   # 테스트 계획 문서
│   └── ...
└── utils/                  # 테스트 유틸리티
    └── helpers.ts
```

---

## 8. .gitignore 업데이트 필요

```gitignore
# Playwright
web-ui/playwright-report/trace/
web-ui/test-results/
```

---

## 9. 관련 작업

- [ ] 기존 루트 테스트 파일들을 `ui/` 디렉토리로 이동
- [ ] 테스트 파일명 컨벤션 통일 (`*.spec.ts`)
- [ ] README 또는 TESTING.md 문서 작성
- [ ] CI 파이프라인에 E2E 테스트 단계 추가
- [ ] Playwright 설정 파일 업데이트 (projects, timeout)

---

## 10. 테스트 실행 결과 (최신)

```
# 마지막 테스트 실행
- 전체 테스트: 160 passed
- 실패: 0
- 스킵: 0
```

---

**작성자**: Claude Code
**마지막 업데이트**: 2026-01-01
