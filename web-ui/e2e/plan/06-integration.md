# 통합 테스트 시나리오

> **총 테스트 수**: 30+
> **우선순위**: P1 (High)
> **목적**: End-to-End 워크플로우 검증

---

## 목차

1. [전체 워크플로우](#1-전체-워크플로우)
2. [프론트엔드-백엔드 통합](#2-프론트엔드-백엔드-통합)
3. [외부 서비스 통합](#3-외부-서비스-통합)
4. [데이터 일관성](#4-데이터-일관성)
5. [상태 전이](#5-상태-전이)
6. [성능 통합 테스트](#6-성능-통합-테스트)

---

## 1. 전체 워크플로우

### 1.1 기본 워크플로우 (6개)

#### INT-WF-001: 새 사용자 온보딩 플로우
```gherkin
Feature: 새 사용자 온보딩
  Scenario: 처음 사용자 전체 플로우
    Given 새 사용자가 시스템에 접속
    When 첫 세션 생성
    And 도면 이미지 업로드
    And 검출 실행
    And 결과 검토
    And BOM 생성
    And Excel 내보내기
    Then 전체 플로우가 5분 이내 완료됨
    And 각 단계에 적절한 안내 표시됨

  Steps:
    1. 홈페이지 접속
    2. "새 세션 만들기" 클릭
    3. 세션 이름 입력 + 이미지 업로드
    4. "검출 실행" 클릭
    5. 검출 결과 확인 + 필요시 수정
    6. "BOM 생성" 클릭
    7. BOM 검토 + 검증
    8. "Excel 내보내기" 클릭

  Expected Duration: <5 min
  Success Criteria: 모든 단계 완료, 에러 없음
```

#### INT-WF-002: 검출-검증-내보내기 전체 플로우
```gherkin
Feature: 검출-검증-내보내기 통합
  Scenario: 완전한 BOM 생성 워크플로우
    Given 세션에 이미지가 업로드됨
    When 다음 단계 순차 실행:
      | Step | Action              | Expected Result      |
      | 1    | Run Detection       | 50+ detections       |
      | 2    | Run OCR             | Dimensions extracted |
      | 3    | Generate BOM        | BOM items created    |
      | 4    | Verify 10 items     | Status updated       |
      | 5    | Bulk approve rest   | All verified         |
      | 6    | Export to Excel     | File downloaded      |
    Then 각 단계의 결과가 다음 단계에 반영됨
    And 최종 Excel에 모든 검증 상태 포함됨

  API Call Sequence:
    1. POST /sessions/{id}/detect
    2. POST /sessions/{id}/ocr
    3. POST /sessions/{id}/bom/generate
    4. POST /sessions/{id}/verify (x10)
    5. POST /sessions/{id}/verify/bulk
    6. POST /sessions/{id}/export
```

#### INT-WF-003: TECHCROSS 전체 워크플로우
```gherkin
Feature: TECHCROSS 1-1 ~ 1-4 통합
  Scenario: TECHCROSS 전체 요구사항 수행
    Given BWMS P&ID 도면이 업로드됨
    When 다음 워크플로우 순차 실행:
      | Step | Workflow           | Key Validation          |
      | 1    | Symbol Detection   | ECU, FMU detected       |
      | 2    | 1-1 Checklist      | 60 items checked        |
      | 3    | 1-2 Valve Signal   | 25 valves classified    |
      | 4    | 1-3 Equipment      | 15 equipment listed     |
      | 5    | 1-4 Deviation      | 10 deviations found     |
      | 6    | Verify All         | 80%+ compliance         |
      | 7    | Export Combined    | Single Excel generated  |
    Then TECHCROSS 요구사항 문서와 일치하는 결과 생성됨

  Total Duration: <15 min
```

#### INT-WF-004: Active Learning 피드백 루프
```gherkin
Feature: Active Learning 통합
  Scenario: 검증 데이터가 학습에 반영되는 플로우
    Given 검출 결과에 오검출이 포함됨
    When 사용자가 10개 항목을 거부 (오검출 표시)
    And 15개 항목을 승인
    And 5개 항목을 수정
    Then 검증 데이터가 Feedback 데이터셋에 추가됨
    And "Export Training Data" 가능해짐
    When Training Data 내보내기
    Then YOLO 형식 학습 데이터 생성됨

  Feedback Data Format:
    - images/: 원본 이미지
    - labels/: YOLO 형식 라벨
    - annotations.json: 상세 어노테이션
```

#### INT-WF-005: 리비전 비교 플로우
```gherkin
Feature: 리비전 비교 통합
  Scenario: 두 버전 도면 비교 워크플로우
    Given 기준선 세션 (v1.0)이 완료됨
    And 새 버전 세션 (v1.1)이 생성됨
    When "Compare with Baseline" 실행
    Then 다음 비교 결과 표시됨:
      | Category  | Count | Description       |
      | Added     | 5     | 새로 추가된 심볼  |
      | Removed   | 2     | 삭제된 심볼       |
      | Modified  | 8     | 변경된 심볼       |
      | Unchanged | 50    | 동일한 심볼       |
    And 시각적 diff 오버레이 제공됨
    And 변경 요약 리포트 생성 가능

  Comparison Methods:
    - Visual: SSIM 이미지 비교
    - Data: 심볼/연결 비교
    - VLM: AI 기반 차이점 분석
```

#### INT-WF-006: 오류 복구 플로우
```gherkin
Feature: 오류 복구 통합
  Scenario: 중간 단계 실패 후 복구
    Given 검출까지 완료된 세션
    When OCR 실행 중 API 오류 발생
    Then 에러 메시지와 함께 상태 저장됨
    And 검출 결과는 유지됨
    When 사용자가 "재시도" 클릭
    Then OCR이 다시 실행됨
    And 이전 상태에서 이어서 진행됨

  Recovery Points:
    - 각 단계 완료 시 자동 저장
    - 실패 지점부터 재시작 가능
    - 전체 워크플로우 리셋 옵션
```

---

## 2. 프론트엔드-백엔드 통합

### 2.1 상태 동기화 (6개)

#### INT-FE-001: 세션 상태 동기화
```gherkin
Feature: 세션 상태 동기화
  Scenario: 백엔드 변경이 프론트엔드에 반영
    Given 세션 상세 페이지가 열려있음
    When 백엔드에서 세션 상태가 "processing" → "completed"로 변경됨
    Then 프론트엔드에서 상태가 자동 업데이트됨
    And 로딩 스피너가 사라지고 결과 표시됨
    And 토스트 알림 "처리 완료" 표시됨

  Sync Mechanism:
    - Polling: 5초 간격
    - Or WebSocket (실시간)
```

#### INT-FE-002: 검출 결과 실시간 반영
```gherkin
Feature: 검출 결과 반영
  Scenario: 검출 API 응답이 UI에 반영
    Given 검출이 진행 중
    When API가 검출 결과 반환
    Then 이미지 위에 바운딩 박스 오버레이됨
    And 결과 테이블에 항목 추가됨
    And 통계 (총 검출 수, 클래스별 분포) 업데이트됨

  UI Updates:
    1. Canvas overlay rendering
    2. DataGrid row insertion
    3. Statistics charts update
```

#### INT-FE-003: 폼 제출 → API → UI 갱신
```gherkin
Feature: 폼-API-UI 통합
  Scenario: 하이퍼파라미터 변경 후 재검출
    Given 검출 설정 패널이 열려있음
    When confidence를 0.5로 변경
    And "Apply & Run" 클릭
    Then POST /detect API가 confidence=0.5로 호출됨
    And 새로운 검출 결과가 UI에 표시됨
    And 이전 결과와 비교 가능
```

#### INT-FE-004: 파일 업로드 진행률
```gherkin
Feature: 업로드 진행률 통합
  Scenario: 대용량 파일 업로드 진행률 표시
    Given 15MB 이미지 파일 선택됨
    When "업로드" 클릭
    Then 업로드 진행률 바가 표시됨
    And 진행률이 실시간 업데이트됨 (10%, 30%, 50%...)
    And 업로드 완료 시 "100%" 표시 후 처리 시작

  Implementation:
    - XMLHttpRequest.upload.onprogress
    - Or fetch with ReadableStream
```

#### INT-FE-005: 에러 응답 UI 표시
```gherkin
Feature: 에러 응답 통합
  Scenario: API 에러가 UI에 적절히 표시
    Given 유효하지 않은 파라미터로 API 호출
    When API가 422 에러 반환
    Then UI에 상세 에러 메시지 표시됨
    And 에러 필드가 강조됨
    And 수정 안내 메시지 제공됨

  Error Display:
    - Toast notification for transient errors
    - Inline error for validation errors
    - Modal for critical errors
```

#### INT-FE-006: Optimistic Update + Rollback
```gherkin
Feature: Optimistic Update 통합
  Scenario: 빠른 UI 반응을 위한 Optimistic Update
    Given BOM 항목 목록이 표시됨
    When 항목 "승인" 클릭
    Then UI가 즉시 "승인됨" 상태로 변경됨 (Optimistic)
    And 백그라운드에서 API 호출
    If API 성공
      Then 상태 유지
    If API 실패
      Then 상태 롤백됨
      And 에러 메시지 표시됨
```

---

## 3. 외부 서비스 통합

### 3.1 다중 API 연동 (8개)

#### INT-EXT-001: YOLO → eDOCr2 파이프라인
```gherkin
Feature: 검출-OCR 파이프라인
  Scenario: YOLO 검출 후 eDOCr2 OCR
    Given 이미지가 업로드됨
    When 검출 실행 (YOLO API - 5005)
    Then 심볼 검출 결과 반환 (27 클래스)
    When OCR 실행 (eDOCr2 API - 5002)
    Then 검출된 영역에서 치수 추출됨
    And 심볼-치수 매핑이 생성됨

  Integration:
    YOLO → Symbol positions
    eDOCr2 → Dimension texts
    Mapping → Symbol + Dimension pairs
```

#### INT-EXT-002: PID Analyzer → Design Checker
```gherkin
Feature: P&ID 분석 체인
  Scenario: PID Analyzer 후 Design Checker
    Given P&ID 도면이 업로드됨
    When PID Analyzer 실행 (5018)
    Then 연결 그래프 생성됨
    When Design Checker 실행 (5019)
    Then 설계 규칙 검증됨
    And 두 결과가 통합 뷰에 표시됨

  Data Flow:
    PID Analyzer → connectivity.json
    Design Checker → validation_results.json
    Combined View → integrated_analysis.json
```

#### INT-EXT-003: VLM 분류 통합
```gherkin
Feature: VLM 분류 통합
  Scenario: 도면 타입 자동 분류
    Given 이미지가 업로드됨
    When VLM 분류 API 호출 (OpenAI)
    Then 도면 타입이 분류됨
      | Type          | Confidence |
      | P&ID          | 0.92       |
      | Electrical    | 0.05       |
      | Mechanical    | 0.03       |
    And 분류 결과에 따라 적절한 모델 추천됨

  VLM Providers:
    - Primary: OpenAI GPT-4o-mini
    - Fallback: Local VL (5004)
```

#### INT-EXT-004: OCR Ensemble 통합
```gherkin
Feature: OCR Ensemble 통합
  Scenario: 다중 OCR 엔진 가중 투표
    Given 복잡한 도면이 업로드됨
    When OCR Ensemble 실행 (5011)
    Then 4개 엔진이 병렬 실행됨:
      | Engine     | Weight |
      | eDOCr2     | 0.35   |
      | PaddleOCR  | 0.30   |
      | Tesseract  | 0.20   |
      | TrOCR      | 0.15   |
    And 가중 투표로 최종 결과 생성됨
    And 신뢰도 점수가 개별 엔진보다 높음
```

#### INT-EXT-005: Line Detector → PID Analyzer
```gherkin
Feature: 라인 검출 통합
  Scenario: 라인 검출 결과가 P&ID 분석에 사용
    Given P&ID 도면이 업로드됨
    When Line Detector 실행 (5016)
    Then 라인 세그먼트 및 스타일 검출됨
      | Line Type   | Count |
      | Solid       | 45    |
      | Dashed      | 12    |
      | Dash-Dot    | 8     |
    When PID Analyzer 실행
    Then 라인 정보가 연결 분석에 활용됨
    And 라인 타입별 의미 해석됨 (프로세스 라인, 계기 라인 등)
```

#### INT-EXT-006: ESRGAN 전처리 통합
```gherkin
Feature: 업스케일 전처리
  Scenario: 저해상도 이미지 업스케일
    Given 저해상도 (640x480) 이미지 업로드됨
    When ESRGAN 전처리 실행 (5010)
    Then 4x 업스케일된 이미지 생성됨 (2560x1920)
    When 업스케일된 이미지로 검출 실행
    Then 검출 정확도가 향상됨
    And 원본 vs 업스케일 비교 가능

  Performance:
    - 업스케일 시간: ~10초
    - 정확도 향상: +15-25%
```

#### INT-EXT-007: Blueprint AI BOM 전체 통합
```gherkin
Feature: Blueprint AI BOM 통합
  Scenario: 완전한 BOM 생성 파이프라인
    Given 기계 도면이 업로드됨
    When Blueprint AI BOM 워크플로우 실행 (5020)
    Then 다음 단계가 자동 실행됨:
      1. VLM 도면 타입 분류
      2. YOLO 심볼 검출
      3. eDOCr2 치수 OCR
      4. GD&T 파싱
      5. BOM 항목 생성
      6. Human-in-the-Loop 검증 큐
    And 모든 결과가 단일 인터페이스에 통합됨

  Total APIs Used: 6+
```

#### INT-EXT-008: 외부 API 장애 대응
```gherkin
Feature: 외부 API 장애 대응
  Scenario: 외부 API 일시 장애 시 폴백
    Given YOLO API (5005)가 응답 불가
    When 검출 요청
    Then 폴백 메커니즘 활성화됨:
      | Strategy      | Action                     |
      | Retry         | 3회 재시도 (exponential)   |
      | Fallback API  | 대체 API 시도 (있는 경우)  |
      | Graceful Fail | 에러 메시지 + 수동 입력 옵션|
    And 장애 상황이 로깅됨
    And 관리자에게 알림 발송됨
```

---

## 4. 데이터 일관성

### 4.1 트랜잭션 일관성 (4개)

#### INT-DATA-001: 세션 생성 원자성
```gherkin
Feature: 세션 생성 원자성
  Scenario: 세션 생성 중 일부 실패 시 롤백
    Given 세션 생성 요청
    When 이미지 저장은 성공
    And 데이터베이스 저장 실패
    Then 전체 트랜잭션 롤백됨
    And 저장된 이미지 파일 삭제됨
    And 일관된 에러 메시지 반환됨
```

#### INT-DATA-002: 검출 결과 저장 일관성
```gherkin
Feature: 검출 결과 일관성
  Scenario: 검출 결과와 이미지 매핑 일관성
    Given 검출이 완료됨
    Then 각 검출 결과에 올바른 image_id 연결됨
    And 검출 좌표가 이미지 크기 범위 내
    And 검출 클래스가 유효한 클래스 목록에 있음
    And 중복 detection_id 없음
```

#### INT-DATA-003: BOM 버전 관리
```gherkin
Feature: BOM 버전 일관성
  Scenario: BOM 편집 시 버전 관리
    Given BOM v1.0이 저장됨
    When 사용자가 5개 항목 수정
    And "저장" 클릭
    Then BOM v1.1이 생성됨
    And v1.0은 히스토리에 보존됨
    And 언제든 v1.0으로 롤백 가능
```

#### INT-DATA-004: 검증 상태 동기화
```gherkin
Feature: 검증 상태 일관성
  Scenario: 여러 소스에서 검증 상태 일관성
    Given 항목이 API로 "승인"됨
    Then 다음 위치 모두에서 상태 일치:
      | Location       | Status    |
      | Database       | approved  |
      | API Response   | approved  |
      | UI Table       | 승인됨    |
      | Export Excel   | Approved  |
```

---

## 5. 상태 전이

### 5.1 세션 상태 전이 (4개)

#### INT-STATE-001: 세션 상태 머신
```gherkin
Feature: 세션 상태 전이
  Scenario: 유효한 상태 전이만 허용
    Given 세션이 "created" 상태
    Then 다음 전이만 유효:

  State Machine:
    created → processing (검출 시작)
    created → deleted (삭제)
    processing → completed (검출 완료)
    processing → failed (검출 실패)
    completed → verified (검증 완료)
    completed → archived (보관)
    failed → processing (재시도)
    verified → exported (내보내기)
    * → deleted (언제든 삭제 가능)

  Invalid Transitions (should fail):
    created → completed (검출 단계 스킵 불가)
    processing → exported (검증 단계 스킵 불가)
    deleted → * (삭제된 세션 복구 불가)
```

#### INT-STATE-002: 검출 항목 상태 전이
```gherkin
Feature: 검출 항목 상태 전이
  Scenario: 검출 항목 검증 상태 전이
    Given 검출 항목이 "pending" 상태
    Then 다음 전이만 유효:

  State Machine:
    pending → approved (승인)
    pending → rejected (거부)
    pending → modified (수정)
    approved → rejected (승인 취소)
    approved → modified (승인 후 수정)
    rejected → approved (거부 취소)
    rejected → modified (거부 후 수정)
    modified → approved (수정 후 승인)
    modified → rejected (수정 후 거부)
```

#### INT-STATE-003: 워크플로우 단계 전이
```gherkin
Feature: 워크플로우 단계 전이
  Scenario: 워크플로우 단계별 진행
    Given 워크플로우가 "upload" 단계
    Then 다음 순서로 진행:

  Workflow Steps:
    1. upload → detection (이미지 업로드 완료)
    2. detection → ocr (검출 완료)
    3. ocr → analysis (OCR 완료)
    4. analysis → verification (분석 완료)
    5. verification → export (검증 완료)

  Skip Rules:
    - OCR은 스킵 가능 (치수 없는 도면)
    - Analysis는 스킵 가능 (단순 BOM)
    - Verification은 스킵 가능 (auto-approve)
```

#### INT-STATE-004: 배치 상태 전이
```gherkin
Feature: 배치 상태 전이
  Scenario: 일괄 승인 시 상태 전이
    Given 100개 항목이 "pending" 상태
    When "전체 승인" 실행
    Then 트랜잭션으로 100개 모두 전이됨
    And 중간 실패 시 전체 롤백됨
    And 최종 상태가 일관됨
```

---

## 6. 성능 통합 테스트

### 6.1 로드 테스트 (4개)

#### INT-PERF-001: 동시 사용자 처리
```gherkin
Feature: 동시 사용자 처리
  Scenario: 10명 동시 접속 시 성능
    Given 10명의 사용자가 동시 접속
    When 각 사용자가 검출 실행
    Then 모든 요청이 30초 이내 완료됨
    And 응답 시간 편차가 ±5초 이내
    And 에러 없음

  Performance Target:
    - Concurrent users: 10
    - Max response time: 30s
    - Error rate: 0%
```

#### INT-PERF-002: API 응답 시간
```gherkin
Feature: API 응답 시간
  Scenario: 주요 API 응답 시간 검증
    Given 시스템이 정상 상태
    When 각 API를 10회 호출
    Then 평균 응답 시간이 목표 이내:

  Response Time Targets:
    | API              | Target (avg) | Max    |
    | GET /sessions    | <500ms       | <1s    |
    | POST /detect     | <10s         | <30s   |
    | POST /ocr        | <5s          | <15s   |
    | POST /export     | <3s          | <10s   |
    | GET /bom         | <1s          | <3s    |
```

#### INT-PERF-003: 메모리 사용량
```gherkin
Feature: 메모리 사용량
  Scenario: 장시간 사용 시 메모리 안정성
    Given 시스템이 시작됨
    When 1시간 동안 지속적인 작업 수행
    Then 메모리 사용량이 안정적으로 유지됨
    And 메모리 누수 없음
    And GC 후 메모리 정상 회복

  Memory Targets:
    - Frontend: <500MB
    - Backend per request: <1GB
```

#### INT-PERF-004: 대용량 파이프라인
```gherkin
Feature: 대용량 파이프라인
  Scenario: 100개 이미지 배치 처리
    Given 100개 P&ID 이미지 준비
    When 배치 처리 실행
    Then 전체 처리가 30분 이내 완료됨
    And 개별 이미지 결과가 올바름
    And 진행률이 실시간 표시됨

  Performance Target:
    - 100 images in 30 min
    - ~18s per image average
```

---

## 7. 테스트 자동화 상태

| 카테고리 | 자동화 | 우선순위 |
|----------|--------|----------|
| 전체 워크플로우 | 30% | P0 |
| FE-BE 통합 | 40% | P0 |
| 외부 서비스 통합 | 20% | P1 |
| 데이터 일관성 | 30% | P1 |
| 상태 전이 | 25% | P1 |
| 성능 통합 | 10% | P2 |

---

## 8. 관련 문서

- [01-api-endpoints.md](./01-api-endpoints.md) - API 명세
- [03-techcross-workflow.md](./03-techcross-workflow.md) - TECHCROSS 워크플로우
- [05-edge-cases.md](./05-edge-cases.md) - 에러 시나리오
- [07-data-fixtures.md](./07-data-fixtures.md) - 테스트 데이터
