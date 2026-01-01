# Blueprint AI BOM E2E Test Plan

> **Version**: 1.0.0
> **Last Updated**: 2026-01-01
> **Total Test Scenarios**: 500+
> **API Endpoints**: 119개
> **UI Components**: 48개

---

## 1. 개요 (Overview)

### 1.1 테스트 목적

Blueprint AI BOM 시스템의 전체 기능을 검증하기 위한 포괄적인 E2E 테스트 계획입니다.

- **기능 검증**: 모든 API 엔드포인트와 UI 컴포넌트가 올바르게 동작하는지 확인
- **통합 검증**: 프론트엔드-백엔드 간 통합이 정상적으로 이루어지는지 확인
- **워크플로우 검증**: TECHCROSS 1-1~1-4 요구사항이 충족되는지 확인
- **파라미터 검증**: 모든 하이퍼파라미터와 설정이 올바르게 적용되는지 확인
- **에러 처리 검증**: 에지 케이스와 에러 상황에서 시스템이 안정적으로 동작하는지 확인

### 1.2 테스트 범위

| 영역 | 테스트 수 | 설명 |
|------|----------|------|
| API 엔드포인트 | 200+ | 119개 엔드포인트 × 정상/에러 케이스 |
| UI 인터랙션 | 150+ | 48개 컴포넌트 × 사용자 액션 |
| TECHCROSS 워크플로우 | 50+ | 1-1~1-4 상세 시나리오 |
| 하이퍼파라미터 | 40+ | 검출/분석/내보내기 파라미터 |
| 에지 케이스 | 30+ | 빈 데이터, 타임아웃, 대용량 등 |
| 통합 테스트 | 30+ | End-to-End 워크플로우 |
| **총계** | **500+** | |

### 1.3 테스트 환경

```yaml
Frontend:
  URL: http://localhost:3000
  Framework: React 18 + TypeScript
  Test Runner: Playwright

Backend:
  URL: http://localhost:5020
  Framework: FastAPI
  Version: 10.6.0

External Services:
  - PID Analyzer: http://localhost:5018
  - Design Checker: http://localhost:5019
  - YOLO API: http://localhost:5005
  - eDOCr2 API: http://localhost:5002
```

---

## 2. 테스트 문서 구조 (Document Structure)

```
e2e/plan/
├── README.md                    # 전체 개요 (현재 문서)
├── 01-api-endpoints.md          # API 엔드포인트 테스트 (200+ 시나리오)
├── 02-ui-interactions.md        # UI 인터랙션 테스트 (150+ 시나리오)
├── 03-techcross-workflow.md     # TECHCROSS 워크플로우 테스트 (50+ 시나리오)
├── 04-hyperparameters.md        # 하이퍼파라미터 테스트 (40+ 시나리오)
├── 05-edge-cases.md             # 에지 케이스 테스트 (30+ 시나리오)
├── 06-integration.md            # 통합 테스트 (30+ 시나리오)
├── 07-data-fixtures.md          # 테스트 데이터 픽스처
└── 08-test-matrix.md            # 테스트 매트릭스 (우선순위, 자동화 상태)
```

---

## 3. 테스트 우선순위 (Priority Levels)

| 레벨 | 설명 | 예시 |
|------|------|------|
| **P0 (Critical)** | 핵심 기능, 반드시 통과 | 이미지 업로드, 검출, BOM 생성 |
| **P1 (High)** | 중요 기능, 릴리즈 전 필수 | 검증 워크플로우, 내보내기 |
| **P2 (Medium)** | 부가 기능, 릴리즈 후 가능 | VLM 분류, GD&T 파싱 |
| **P3 (Low)** | 개선 사항, 선택적 | UI 스타일링, 성능 최적화 |

---

## 4. 테스트 카테고리 (Test Categories)

### 4.1 기능 테스트 (Functional Tests)

#### 세션 관리 (15개)
- 이미지 업로드 (다양한 형식: PNG, JPG, PDF)
- 세션 생성/조회/수정/삭제
- 세션 목록 페이지네이션
- 세션 상태 전환

#### 검출 (Detection) (25개)
- YOLO 검출 실행
- 하이퍼파라미터 적용 (confidence, iou_threshold, imgsz)
- 모델 선택 (nano, small, medium)
- 검출 결과 조회
- 수동 검출 추가
- 검출 삭제

#### 검증 (Verification) (30개)
- 개별 항목 승인/거부/수정
- 일괄 승인/거부
- Active Learning 큐
- 검증 통계
- 검증 상태 필터링

#### BOM 생성 (20개)
- BOM 자동 생성
- BOM 항목 수정
- 내보내기 (Excel, CSV, JSON, PDF)
- 가격 계산

### 4.2 TECHCROSS 워크플로우 (50개)

#### 1-1: BWMS Checklist (15개)
- 60개 체크리스트 항목 검증
- auto_status vs final_status 구분
- 규칙 프로파일 선택 (default, bwms, chemical)
- 컴플라이언스율 계산

#### 1-2: Valve Signal List (12개)
- 6가지 밸브 카테고리 분류
- 밸브 ID 패턴 인식
- 검증 워크플로우
- 신뢰도 색상 코딩

#### 1-3: Equipment List (12개)
- 9가지 장비 타입 분류
- BWMS 장비 태그 인식 (ECU, FMU, HGU 등)
- 공급업체 표시
- 검증 워크플로우

#### 1-4: Deviation Analysis (11개)
- 심각도 레벨 필터링 (critical~info)
- 분석 타입 선택
- 표준 선택 (ISO 10628, ISA 5.1, BWMS)
- 기준선 세션 비교

### 4.3 UI 인터랙션 (150개)

#### 페이지 네비게이션 (10개)
- 라우팅
- 브라우저 뒤로/앞으로
- 딥링크

#### 폼 인터랙션 (40개)
- 입력 필드 유효성 검사
- 드롭다운 선택
- 슬라이더 조정
- 체크박스/라디오 버튼

#### 테이블 인터랙션 (30개)
- 정렬
- 필터링
- 페이지네이션
- 행 선택

#### 이미지 인터랙션 (20개)
- 이미지 확대/축소
- 바운딩 박스 오버레이
- 드래그로 박스 그리기
- 클릭 이벤트

#### 모달/다이얼로그 (20개)
- 모달 열기/닫기
- 확인 다이얼로그
- 경고/에러 메시지
- 토스트 알림

#### 상태 관리 (30개)
- 로딩 상태
- 에러 상태
- 빈 상태
- 성공 상태

### 4.4 하이퍼파라미터 (40개)

#### Detection 파라미터 (12개)
- confidence: 0.05~1.0
- iou_threshold: 0.1~0.95
- imgsz: 320~4096
- model_id 선택

#### Analysis 파라미터 (10개)
- OCR 엔진 선택
- 분석 옵션 토글
- 프리셋 적용

#### Export 파라미터 (8개)
- export_type 선택
- include_rejected 옵션
- 프로젝트 메타데이터

#### P&ID 파라미터 (10개)
- rule_profile 선택
- severity_threshold 선택
- analysis_types 선택
- standards 선택

### 4.5 에지 케이스 (30개)

#### 입력 검증 (10개)
- 빈 입력
- 잘못된 형식
- 경계값
- 특수 문자

#### 에러 처리 (10개)
- API 오류
- 타임아웃
- 네트워크 오류
- 인증 오류

#### 대용량 처리 (10개)
- 대용량 이미지
- 많은 검출 결과
- 긴 세션 목록
- 동시 요청

---

## 5. 테스트 실행 가이드 (Execution Guide)

### 5.1 사전 조건

```bash
# 1. 서비스 시작
cd /home/uproot/ax/poc
docker-compose up -d

# 2. Blueprint AI BOM 시작
cd blueprint-ai-bom
docker-compose up -d

# 3. 헬스 체크
curl http://localhost:5020/health
curl http://localhost:3000
```

### 5.2 테스트 실행

```bash
# 전체 테스트
cd web-ui
npx playwright test e2e/blueprint-ai-bom*.spec.ts

# 특정 카테고리
npx playwright test e2e/blueprint-ai-bom.spec.ts --grep "TECHCROSS"

# 헤드리스 모드 비활성화 (디버깅)
npx playwright test --headed

# 특정 브라우저
npx playwright test --project=chromium
```

### 5.3 테스트 보고서

```bash
# HTML 보고서 생성
npx playwright test --reporter=html

# 보고서 열기
npx playwright show-report
```

---

## 6. 테스트 데이터 (Test Data)

### 6.1 샘플 이미지

| 파일 | 용도 | 위치 |
|------|------|------|
| `page_1.png` | P&ID 도면 (TECHCROSS) | `/apply-company/techloss/test_output/` |
| `test_drawing.jpg` | 기계 부품도 | `/samples/` |
| `electrical_panel.png` | 전기 패널도 | `/samples/` |

### 6.2 기대 결과 (Expected Results)

각 테스트 시나리오에 대한 기대 결과는 개별 문서에 정의됩니다.

---

## 7. 자동화 상태 (Automation Status)

| 카테고리 | 전체 | 자동화됨 | 수동 | 비율 |
|----------|------|---------|------|------|
| API 엔드포인트 | 200 | 50 | 150 | 25% |
| UI 인터랙션 | 150 | 41 | 109 | 27% |
| TECHCROSS | 50 | 20 | 30 | 40% |
| 하이퍼파라미터 | 40 | 15 | 25 | 38% |
| 에지 케이스 | 30 | 5 | 25 | 17% |
| 통합 테스트 | 30 | 10 | 20 | 33% |
| **총계** | **500** | **141** | **359** | **28%** |

### 현재 자동화된 테스트 파일

| 파일 | 테스트 수 | 설명 |
|------|----------|------|
| `blueprint-ai-bom.spec.ts` | 20 | 기본 워크플로우 |
| `blueprint-ai-bom-comprehensive.spec.ts` | 41 | 상세 파라미터 |
| `hyperparameter-changes.spec.ts` | 10 | 하이퍼파라미터 저장 |
| 기타 | 70+ | 템플릿, 노드, API 설정 등 |

---

## 8. 다음 단계 (Next Steps)

### Phase 1: 핵심 워크플로우 자동화 (P0)
- [ ] 세션 관리 전체 자동화
- [ ] 검출 파이프라인 자동화
- [ ] BOM 생성 자동화

### Phase 2: TECHCROSS 워크플로우 자동화 (P1)
- [ ] 1-1 Checklist 전체 자동화
- [ ] 1-2 Valve Signal 전체 자동화
- [ ] 1-3 Equipment 전체 자동화

### Phase 3: 에지 케이스 자동화 (P2)
- [ ] 입력 검증 자동화
- [ ] 에러 처리 자동화
- [ ] 대용량 처리 자동화

### Phase 4: 성능 테스트 추가 (P3)
- [ ] 로드 테스트
- [ ] 스트레스 테스트
- [ ] 메모리 누수 테스트

---

## 9. 참고 문서 (References)

- [Blueprint AI BOM API 문서](/home/uproot/ax/poc/blueprint-ai-bom/docs/README.md)
- [CLAUDE.md 프로젝트 가이드](/home/uproot/ax/poc/CLAUDE.md)
- [Playwright 공식 문서](https://playwright.dev/docs/intro)
- [TECHCROSS 요구사항 분석](/.todos/TECHCROSS_요구사항_분석_20251229.md)
