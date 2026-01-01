# 엣지 케이스 및 에러 처리 테스트 시나리오

> **총 테스트 수**: 30+
> **우선순위**: P2 (Medium)
> **목적**: 시스템 안정성 및 견고성 검증

---

## 목차

1. [입력 유효성 검증](#1-입력-유효성-검증)
2. [API 에러 처리](#2-api-에러-처리)
3. [네트워크 에러](#3-네트워크-에러)
4. [대용량 데이터](#4-대용량-데이터)
5. [동시성 처리](#5-동시성-처리)
6. [브라우저 호환성](#6-브라우저-호환성)
7. [보안 테스트](#7-보안-테스트)

---

## 1. 입력 유효성 검증

### 1.1 파일 업로드 검증 (10개)

#### EC-INP-001: 지원되지 않는 파일 형식
```gherkin
Feature: 파일 형식 검증
  Scenario Outline: 지원되지 않는 파일 형식 업로드 시도
    Given 세션 생성 화면에 있음
    When "<file_type>" 형식 파일 업로드 시도
    Then 에러 메시지 "지원되지 않는 파일 형식입니다" 표시됨
    And 파일이 업로드되지 않음

  Examples:
    | file_type | extension |
    | GIF       | .gif      |
    | BMP       | .bmp      |
    | WebP      | .webp     |
    | TIFF      | .tif      |
    | SVG       | .svg      |
    | EXE       | .exe      |
    | TXT       | .txt      |

  Supported Formats:
    - PNG, JPG/JPEG, PDF
```

#### EC-INP-002: 파일 크기 초과
```gherkin
Feature: 파일 크기 제한
  Scenario: 최대 크기 초과 파일 업로드
    Given 세션 생성 화면에 있음
    When 50MB 이상의 이미지 파일 업로드 시도
    Then 에러 메시지 "파일 크기가 50MB를 초과합니다" 표시됨
    And 업로드 진행률 바가 표시되지 않음

  Limit: 50MB
```

#### EC-INP-003: 빈 파일
```gherkin
Feature: 빈 파일 검증
  Scenario: 0바이트 파일 업로드
    Given 세션 생성 화면에 있음
    When 0바이트 이미지 파일 업로드 시도
    Then 에러 메시지 "빈 파일은 업로드할 수 없습니다" 표시됨
```

#### EC-INP-004: 손상된 이미지 파일
```gherkin
Feature: 손상된 파일 검증
  Scenario: 손상된 PNG 파일 업로드
    Given 세션 생성 화면에 있음
    When 손상된 PNG 파일 업로드 시도
    Then 에러 메시지 "이미지 파일을 읽을 수 없습니다" 표시됨
    And 파일 상세 정보에 "Invalid" 표시됨
```

#### EC-INP-005: 확장자 위조
```gherkin
Feature: 확장자 위조 검증
  Scenario: 잘못된 확장자로 위장된 파일
    Given 세션 생성 화면에 있음
    When TXT 파일을 .png 확장자로 변경하여 업로드
    Then 에러 메시지 "유효한 이미지 파일이 아닙니다" 표시됨
    And MIME 타입 검증 실패 표시됨

  Validation:
    - MIME type check
    - Magic number verification
```

#### EC-INP-006: 매우 작은 이미지
```gherkin
Feature: 최소 크기 검증
  Scenario: 너무 작은 이미지 업로드
    Given 세션 생성 화면에 있음
    When 10x10 픽셀 이미지 업로드
    Then 경고 메시지 "이미지가 너무 작아 검출 정확도가 낮을 수 있습니다" 표시됨
    And 업로드는 허용됨

  Minimum Recommended: 640x480
```

#### EC-INP-007: 매우 큰 이미지 해상도
```gherkin
Feature: 최대 해상도 처리
  Scenario: 초고해상도 이미지 업로드
    Given 세션 생성 화면에 있음
    When 10000x10000 픽셀 이미지 업로드
    Then 이미지가 자동으로 리사이징됨
    And 경고 메시지 "이미지가 최대 해상도로 조정되었습니다" 표시됨

  Maximum Processing Size: 8192x8192
```

### 1.2 입력 필드 검증 (6개)

#### EC-INP-008: 필수 필드 누락
```gherkin
Feature: 필수 필드 검증
  Scenario: 세션 이름 없이 생성 시도
    Given 새 세션 생성 다이얼로그가 열려있음
    When 세션 이름 필드를 비워둠
    And "생성" 버튼 클릭
    Then 에러 메시지 "세션 이름은 필수입니다" 표시됨
    And 세션 이름 필드가 빨간색 테두리로 강조됨
    And 다이얼로그가 닫히지 않음
```

#### EC-INP-009: 특수문자 입력
```gherkin
Feature: 특수문자 검증
  Scenario: 세션 이름에 특수문자 입력
    Given 새 세션 생성 다이얼로그가 열려있음
    When 세션 이름에 "<script>alert('xss')</script>" 입력
    And "생성" 버튼 클릭
    Then XSS 스크립트가 실행되지 않음
    And 입력이 이스케이프되어 저장됨
    Or 에러 메시지 "허용되지 않는 문자가 포함되어 있습니다" 표시됨
```

#### EC-INP-010: 최대 길이 초과
```gherkin
Feature: 입력 길이 제한
  Scenario: 세션 이름 최대 길이 초과
    Given 새 세션 생성 다이얼로그가 열려있음
    When 세션 이름에 300자 이상 입력 시도
    Then 입력이 255자에서 잘림
    Or 에러 메시지 "최대 255자까지 입력 가능합니다" 표시됨
```

#### EC-INP-011: 숫자 필드에 문자 입력
```gherkin
Feature: 숫자 필드 검증
  Scenario: confidence 필드에 문자 입력
    Given 검출 설정 패널이 열려있음
    When confidence 입력 필드에 "abc" 입력
    Then 입력이 거부됨
    Or 에러 메시지 "숫자만 입력 가능합니다" 표시됨
    And 값이 이전 값으로 유지됨
```

#### EC-INP-012: 음수 값 입력
```gherkin
Feature: 음수 값 검증
  Scenario: confidence에 음수 입력
    Given 검출 설정 패널이 열려있음
    When confidence 입력 필드에 "-0.5" 입력
    Then 에러 메시지 "0보다 큰 값을 입력하세요" 표시됨
    And 값이 이전 값으로 복원됨
```

#### EC-INP-013: 공백 문자열 입력
```gherkin
Feature: 공백 문자열 검증
  Scenario: 공백만 있는 입력
    Given 새 세션 생성 다이얼로그가 열려있음
    When 세션 이름에 "   " (공백만) 입력
    And "생성" 버튼 클릭
    Then 에러 메시지 "유효한 이름을 입력하세요" 표시됨
    And 공백이 trim되어 빈 문자열로 처리됨
```

---

## 2. API 에러 처리

### 2.1 HTTP 에러 응답 (8개)

#### EC-API-001: 400 Bad Request
```gherkin
Feature: 400 에러 처리
  Scenario: 잘못된 요청 파라미터
    Given 검출 API 호출 준비
    When confidence에 유효하지 않은 값 전송 (예: "invalid")
    Then API가 400 에러 반환
    And UI에 에러 메시지 "잘못된 요청입니다: confidence 값이 유효하지 않습니다" 표시됨
    And 요청 상세 정보가 콘솔에 로깅됨

  Response:
    {
      "detail": "Invalid value for confidence: expected float, got string"
    }
```

#### EC-API-002: 401 Unauthorized
```gherkin
Feature: 401 에러 처리
  Scenario: 인증 토큰 만료
    Given 사용자가 로그인된 상태
    When 인증 토큰이 만료된 후 API 호출
    Then API가 401 에러 반환
    And 로그인 페이지로 리다이렉트됨
    And 메시지 "세션이 만료되었습니다. 다시 로그인해주세요" 표시됨
```

#### EC-API-003: 403 Forbidden
```gherkin
Feature: 403 에러 처리
  Scenario: 권한 없는 리소스 접근
    Given 사용자가 다른 사용자의 세션에 접근 시도
    When GET /api/v1/sessions/{other_user_session_id} 호출
    Then API가 403 에러 반환
    And 메시지 "이 리소스에 접근할 권한이 없습니다" 표시됨
    And 세션 목록 페이지로 리다이렉트됨
```

#### EC-API-004: 404 Not Found
```gherkin
Feature: 404 에러 처리
  Scenario: 존재하지 않는 세션 접근
    Given 삭제된 세션 ID로 접근 시도
    When GET /api/v1/sessions/{deleted_session_id} 호출
    Then API가 404 에러 반환
    And 메시지 "요청한 리소스를 찾을 수 없습니다" 표시됨
    And "세션 목록으로 돌아가기" 버튼 표시됨
```

#### EC-API-005: 409 Conflict
```gherkin
Feature: 409 에러 처리
  Scenario: 중복 리소스 생성
    Given 동일한 이름의 세션이 이미 존재
    When 같은 이름으로 새 세션 생성 시도
    Then API가 409 에러 반환
    And 메시지 "동일한 이름의 세션이 이미 존재합니다" 표시됨
    And 다른 이름 입력을 유도하는 UI 표시됨
```

#### EC-API-006: 422 Unprocessable Entity
```gherkin
Feature: 422 에러 처리
  Scenario: 유효성 검증 실패
    Given 검출 API 호출 준비
    When confidence=0.5, iou_threshold=1.5 (범위 초과) 전송
    Then API가 422 에러 반환
    And 상세 유효성 검증 오류 메시지 표시됨

  Response:
    {
      "detail": [
        {
          "loc": ["body", "iou_threshold"],
          "msg": "ensure this value is less than or equal to 0.95",
          "type": "value_error.number.not_le"
        }
      ]
    }
```

#### EC-API-007: 500 Internal Server Error
```gherkin
Feature: 500 에러 처리
  Scenario: 서버 내부 오류
    Given 서버에서 예상치 못한 오류 발생
    When 검출 API 호출
    Then API가 500 에러 반환
    And 사용자에게 일반 에러 메시지 표시됨
    And "문제가 발생했습니다. 잠시 후 다시 시도해주세요" 표시됨
    And "오류 보고" 버튼 표시됨

  UI Behavior:
    - 상세 스택 트레이스는 사용자에게 노출되지 않음
    - 에러 ID가 제공됨 (지원 요청용)
```

#### EC-API-008: 503 Service Unavailable
```gherkin
Feature: 503 에러 처리
  Scenario: 서비스 일시 중단
    Given 백엔드 서비스가 유지보수 중
    When 모든 API 호출
    Then 503 에러 반환
    And 유지보수 안내 페이지 표시됨
    And "예상 복구 시간: 30분" 등 정보 표시됨
```

---

## 3. 네트워크 에러

### 3.1 연결 문제 (6개)

#### EC-NET-001: 네트워크 연결 끊김
```gherkin
Feature: 오프라인 상태 처리
  Scenario: 네트워크 연결 끊김
    Given 사용자가 작업 중
    When 네트워크 연결이 끊김
    Then 상단에 "오프라인 상태입니다" 배너 표시됨
    And 배너가 빨간색으로 강조됨
    And 네트워크 복구 시 자동으로 배너 사라짐
    And 저장되지 않은 변경사항 경고 표시됨

  UI Behavior:
    - navigator.onLine 감지
    - 재연결 시 자동 동기화 시도
```

#### EC-NET-002: 요청 타임아웃
```gherkin
Feature: 타임아웃 처리
  Scenario: API 응답 지연
    Given 검출 API 호출
    When 서버 응답이 30초 이상 지연됨
    Then 타임아웃 에러 발생
    And 메시지 "서버 응답 시간이 초과되었습니다" 표시됨
    And "다시 시도" 버튼 표시됨

  Timeout Settings:
    - Default: 30s
    - Detection: 120s
    - Export: 60s
```

#### EC-NET-003: 느린 네트워크 상태
```gherkin
Feature: 느린 네트워크 UX
  Scenario: 3G 네트워크 환경
    Given 느린 네트워크 환경 (3G 시뮬레이션)
    When 이미지 업로드 시도
    Then 업로드 진행률이 천천히 증가함
    And 예상 남은 시간이 표시됨
    And "업로드 취소" 버튼이 활성화됨
```

#### EC-NET-004: 간헐적 연결 끊김
```gherkin
Feature: 간헐적 연결 문제
  Scenario: 불안정한 연결
    Given 네트워크가 간헐적으로 끊김
    When 대용량 파일 업로드 중
    Then 업로드가 일시 중단됨
    And 연결 복구 시 자동 재시도됨
    And 재시도 횟수가 표시됨 (예: "재시도 2/3")
    And 최대 재시도 후 실패 메시지 표시됨
```

#### EC-NET-005: CORS 에러
```gherkin
Feature: CORS 에러 처리
  Scenario: CORS 정책 위반
    Given 잘못된 Origin에서 API 호출
    When 백엔드가 CORS 에러 반환
    Then 콘솔에 CORS 에러 로깅됨
    And 사용자에게 "서버 연결 오류" 일반 메시지 표시됨
    And 개발자 도구에서 상세 정보 확인 가능
```

#### EC-NET-006: DNS 해결 실패
```gherkin
Feature: DNS 에러 처리
  Scenario: DNS 해결 실패
    Given 백엔드 호스트명이 해결되지 않음
    When API 호출 시도
    Then "서버에 연결할 수 없습니다" 메시지 표시됨
    And 네트워크 상태 확인 권장 메시지 표시됨
```

---

## 4. 대용량 데이터

### 4.1 대량 검출 결과 (6개)

#### EC-BIG-001: 1000+ 검출 결과
```gherkin
Feature: 대량 검출 결과 처리
  Scenario: 1000개 이상 검출 결과
    Given 복잡한 P&ID 도면 업로드
    When 낮은 confidence (0.05)로 검출 실행
    And 1000개 이상 결과 반환됨
    Then 결과가 페이지네이션됨 (100개씩)
    And 테이블 렌더링이 3초 이내 완료됨
    And 가상 스크롤이 적용됨

  Performance Target:
    - Initial render: <3s
    - Scroll FPS: >30
```

#### EC-BIG-002: 대용량 이미지 (20MB+)
```gherkin
Feature: 대용량 이미지 처리
  Scenario: 20MB 고해상도 도면
    Given 20MB PNG 파일 업로드
    When 검출 실행
    Then 처리 진행률이 표시됨
    And 메모리 사용량이 안정적으로 유지됨
    And 타임아웃 없이 완료됨

  Expected Behavior:
    - 업로드: 청크 업로드 적용
    - 처리: 서버 측 리사이징
    - 표시: 썸네일 먼저 로드
```

#### EC-BIG-003: 긴 세션 목록 (1000+)
```gherkin
Feature: 긴 세션 목록 처리
  Scenario: 1000개 이상 세션 표시
    Given 사용자가 1000개 이상 세션 보유
    When 세션 목록 페이지 접속
    Then 가상 스크롤로 목록 렌더링
    And 검색/필터가 즉시 반응함
    And 스크롤이 부드럽게 동작함
```

#### EC-BIG-004: 복잡한 BOM (500+ 항목)
```gherkin
Feature: 대형 BOM 처리
  Scenario: 500개 이상 BOM 항목
    Given BOM에 500개 이상 항목 포함
    When BOM 테이블 표시
    Then 그룹화가 적용됨
    And 확장/축소가 빠르게 동작함
    And Excel 내보내기가 10초 이내 완료됨
```

#### EC-BIG-005: 대량 일괄 작업
```gherkin
Feature: 대량 일괄 처리
  Scenario: 100개 항목 일괄 승인
    Given BOM에 100개 미검증 항목 있음
    When "전체 선택" 후 "일괄 승인" 클릭
    Then 확인 다이얼로그에 "100개 항목" 표시됨
    When 확인 클릭
    Then 진행률 표시됨 (예: "50/100")
    And 전체 완료까지 10초 이내
    And 실패한 항목은 별도 표시됨
```

#### EC-BIG-006: 다중 페이지 PDF
```gherkin
Feature: 다중 페이지 PDF 처리
  Scenario: 50페이지 PDF 업로드
    Given 50페이지 PDF 파일 준비
    When PDF 업로드
    Then 각 페이지가 개별 이미지로 추출됨
    And 페이지 선택 UI 표시됨
    And 개별 또는 전체 페이지 처리 선택 가능

  Behavior:
    - PDF 파싱은 서버 측에서 수행
    - 페이지별 썸네일 제공
```

---

## 5. 동시성 처리

### 5.1 동시 요청 (4개)

#### EC-CON-001: 동시 검출 요청
```gherkin
Feature: 동시 검출 요청
  Scenario: 같은 세션에서 연속 검출 요청
    Given 세션에서 검출이 진행 중
    When 다시 "Run Detection" 클릭
    Then 경고 "검출이 이미 진행 중입니다" 표시됨
    And 두 번째 요청은 무시됨
    Or 이전 요청이 취소되고 새 요청 시작됨

  Behavior:
    - Debounce: 500ms
    - 버튼 비활성화 during processing
```

#### EC-CON-002: 다중 탭에서 같은 세션
```gherkin
Feature: 다중 탭 동기화
  Scenario: 두 개 탭에서 같은 세션 열기
    Given 브라우저 탭 A에서 세션 열림
    When 탭 B에서 같은 세션 열기
    And 탭 A에서 검출 실행
    Then 탭 B에서도 결과 자동 업데이트됨
    Or 탭 B에서 "새로고침 필요" 알림 표시됨

  Sync Strategy:
    - WebSocket 또는 polling (30초)
```

#### EC-CON-003: 동시 편집 충돌
```gherkin
Feature: 동시 편집 충돌
  Scenario: 두 사용자가 같은 BOM 항목 편집
    Given 사용자 A와 B가 같은 BOM 항목을 보고 있음
    When A가 항목을 "승인"으로 변경
    And B가 같은 항목을 "거부"로 변경 시도
    Then B에게 충돌 경고 표시됨
    And "최신 상태 확인" 옵션 제공됨
    And 강제 저장 또는 새로고침 선택 가능
```

#### EC-CON-004: Race Condition 방지
```gherkin
Feature: Race Condition 방지
  Scenario: 빠른 연속 업데이트
    Given BOM 테이블이 표시됨
    When 사용자가 3개 항목을 빠르게 연속 승인
    Then 각 요청이 순서대로 처리됨
    And 마지막 상태가 올바르게 반영됨
    And 중간 상태 플리커링 없음

  Implementation:
    - Request queue
    - Optimistic updates with rollback
```

---

## 6. 브라우저 호환성

### 6.1 브라우저별 테스트 (4개)

#### EC-BRW-001: Chrome 최신
```gherkin
Feature: Chrome 호환성
  Scenario: Chrome 120+ 테스트
    Given Chrome 최신 버전 사용
    When 전체 워크플로우 실행
    Then 모든 기능 정상 동작
    And UI가 올바르게 렌더링됨
    And DevTools 콘솔에 에러 없음
```

#### EC-BRW-002: Firefox 최신
```gherkin
Feature: Firefox 호환성
  Scenario: Firefox 120+ 테스트
    Given Firefox 최신 버전 사용
    When 전체 워크플로우 실행
    Then 모든 기능 정상 동작
    And CSS 렌더링이 Chrome과 동일함
```

#### EC-BRW-003: Safari 최신
```gherkin
Feature: Safari 호환성
  Scenario: Safari 17+ 테스트
    Given Safari 최신 버전 사용
    When 전체 워크플로우 실행
    Then 모든 기능 정상 동작
    And Date picker 등 네이티브 컨트롤 정상 동작
```

#### EC-BRW-004: Edge 최신
```gherkin
Feature: Edge 호환성
  Scenario: Edge 120+ 테스트
    Given Edge 최신 버전 사용
    When 전체 워크플로우 실행
    Then 모든 기능 정상 동작
    And Chromium 기반으로 Chrome과 동일
```

---

## 7. 보안 테스트

### 7.1 보안 취약점 (6개)

#### EC-SEC-001: XSS 방지
```gherkin
Feature: XSS 방지
  Scenario: 악성 스크립트 입력
    Given 세션 이름 입력 필드
    When "<script>alert('xss')</script>" 입력
    And 저장 후 다시 조회
    Then 스크립트가 실행되지 않음
    And 텍스트로 이스케이프되어 표시됨

  Validation:
    - React의 자동 이스케이프 활용
    - dangerouslySetInnerHTML 미사용
```

#### EC-SEC-002: SQL Injection 방지
```gherkin
Feature: SQL Injection 방지
  Scenario: 악성 쿼리 파라미터
    Given 검색 필드
    When "'; DROP TABLE sessions; --" 입력
    Then API가 정상적으로 처리됨
    And 데이터베이스에 영향 없음
    And 검색 결과만 표시됨

  Validation:
    - 파라미터화된 쿼리 사용
    - ORM 활용 (SQLAlchemy)
```

#### EC-SEC-003: Path Traversal 방지
```gherkin
Feature: Path Traversal 방지
  Scenario: 경로 조작 시도
    Given 파일 다운로드 API
    When 파일 경로에 "../../../etc/passwd" 전달
    Then 403 또는 404 에러 반환
    And 시스템 파일에 접근 불가

  Validation:
    - 경로 정규화
    - 허용된 디렉토리 외 접근 차단
```

#### EC-SEC-004: CSRF 방지
```gherkin
Feature: CSRF 방지
  Scenario: 외부 사이트에서 요청 위조
    Given 사용자가 로그인된 상태
    When 외부 사이트에서 POST /api/v1/sessions 요청
    Then 요청이 거부됨
    And CSRF 토큰 검증 실패 메시지 반환

  Validation:
    - CSRF 토큰 사용
    - SameSite 쿠키 설정
```

#### EC-SEC-005: 파일 업로드 보안
```gherkin
Feature: 파일 업로드 보안
  Scenario: 악성 파일 업로드 방지
    Given 이미지 업로드 기능
    When 실행 파일을 이미지 확장자로 위장하여 업로드
    Then 파일 시그니처 검증 실패
    And 업로드가 거부됨

  Validation:
    - MIME 타입 검증
    - 파일 시그니처 (magic number) 검증
    - 파일 확장자 화이트리스트
```

#### EC-SEC-006: Rate Limiting
```gherkin
Feature: Rate Limiting
  Scenario: 과도한 요청 차단
    Given API 엔드포인트
    When 1초에 100회 이상 요청
    Then 429 Too Many Requests 반환
    And "잠시 후 다시 시도해주세요" 메시지 표시됨
    And Retry-After 헤더 제공됨

  Limits:
    - 일반 API: 100 req/min
    - 검출 API: 10 req/min
    - 업로드 API: 20 req/min
```

---

## 8. 테스트 자동화 상태

| 카테고리 | 자동화 | 우선순위 |
|----------|--------|----------|
| 입력 유효성 | 30% | P1 |
| API 에러 | 40% | P0 |
| 네트워크 에러 | 10% | P2 |
| 대용량 데이터 | 20% | P2 |
| 동시성 | 10% | P3 |
| 브라우저 호환성 | 50% | P1 |
| 보안 | 20% | P0 |

---

## 9. 관련 문서

- [01-api-endpoints.md](./01-api-endpoints.md) - API 에러 응답 스키마
- [06-integration.md](./06-integration.md) - 통합 에러 시나리오
- [07-data-fixtures.md](./07-data-fixtures.md) - 테스트 데이터
