# TECHCROSS 워크플로우 테스트 시나리오

> **총 테스트 수**: 50+
> **우선순위**: P1 (High)
> **관련 API**: PID Analyzer (5018), Design Checker (5019), Blueprint AI BOM (5020)

---

## 목차

1. [TECHCROSS 1-1: BWMS Checklist](#1-techcross-1-1-bwms-checklist)
2. [TECHCROSS 1-2: Valve Signal List](#2-techcross-1-2-valve-signal-list)
3. [TECHCROSS 1-3: Equipment List](#3-techcross-1-3-equipment-list)
4. [TECHCROSS 1-4: Deviation Analysis](#4-techcross-1-4-deviation-analysis)
5. [통합 워크플로우](#5-통합-워크플로우)

---

## 1. TECHCROSS 1-1: BWMS Checklist

### 1.1 체크리스트 항목 검증 (15개)

#### TC-1-1-001: 기본 체크리스트 실행
```gherkin
Feature: BWMS 체크리스트 기본 실행
  Scenario: 60개 체크리스트 항목 전체 검증
    Given 세션에 P&ID 도면이 업로드되어 있음
    And 심볼 검출이 완료됨
    When "BWMS Checklist" 탭 클릭
    And "Run Checklist" 버튼 클릭
    Then Design Checker API 호출됨
    And 60개 체크리스트 항목이 표시됨
    And 각 항목에 auto_status가 표시됨
    And 컴플라이언스율이 계산됨

  Expected Results:
    - API: POST /api/v1/sessions/{session_id}/checklist/check
    - Response: { items: [...], compliance_rate: number }
    - UI: 60개 행이 있는 테이블
    - 각 행: item_id, description, auto_status, final_status
```

#### TC-1-1-002: 규칙 프로파일 선택 - default
```gherkin
Feature: 규칙 프로파일 선택
  Scenario: default 프로파일 사용
    Given 체크리스트 화면에 있음
    When rule_profile 드롭다운에서 "default" 선택
    And "Run Checklist" 버튼 클릭
    Then 기본 20개 규칙이 적용됨
    And 일반적인 P&ID 검증 수행됨

  Parameters:
    rule_profile: "default"

  Expected Rules:
    - connectivity_check
    - symbol_validation
    - labeling_check
    - line_numbering
    - instrument_check
```

#### TC-1-1-003: 규칙 프로파일 선택 - bwms
```gherkin
Feature: 규칙 프로파일 선택
  Scenario: bwms 프로파일 사용
    Given 체크리스트 화면에 있음
    When rule_profile 드롭다운에서 "bwms" 선택
    And "Run Checklist" 버튼 클릭
    Then BWMS 전용 규칙이 적용됨
    And 선박평형수처리시스템 규정 검증됨

  Parameters:
    rule_profile: "bwms"

  Expected Rules (BWMS 전용):
    - bwms_ballast_tank_vent
    - bwms_treatment_system
    - bwms_sampling_point
    - bwms_bypass_valve
    - bwms_flow_measurement
    - bwms_control_system
    - bwms_power_supply
```

#### TC-1-1-004: 규칙 프로파일 선택 - chemical
```gherkin
Feature: 규칙 프로파일 선택
  Scenario: chemical 프로파일 사용
    Given 체크리스트 화면에 있음
    When rule_profile 드롭다운에서 "chemical" 선택
    And "Run Checklist" 버튼 클릭
    Then 화학 플랜트 규칙이 적용됨

  Parameters:
    rule_profile: "chemical"
```

#### TC-1-1-005: auto_status vs final_status 구분
```gherkin
Feature: 상태 구분
  Scenario: 자동 상태와 최종 상태 분리
    Given 체크리스트가 실행됨
    Then 각 항목에 두 개의 상태 컬럼이 있음
    And auto_status는 시스템이 자동 판정한 값
    And final_status는 사용자가 검증한 값
    And final_status가 null이면 auto_status를 따름

  Status Values:
    - Pass: 규칙 충족
    - Fail: 규칙 위반
    - N/A: 해당 없음
    - Pending: 검토 필요
    - Manual Required: 수동 검토 필수
```

#### TC-1-1-006: 개별 항목 검증 - 승인
```gherkin
Feature: 개별 항목 검증
  Scenario: 체크리스트 항목 승인
    Given 체크리스트에 Pending 상태 항목이 있음
    When 해당 항목의 "승인" 버튼 클릭
    Then final_status가 "Pass"로 변경됨
    And API 호출: POST /verify
    And 테이블 행 색상이 녹색으로 변경됨
    And 컴플라이언스율 재계산됨

  API Request:
    POST /api/v1/sessions/{session_id}/checklist/verify
    {
      "item_id": "CLK-001",
      "action": "approve",
      "comment": "확인 완료"
    }
```

#### TC-1-1-007: 개별 항목 검증 - 거부
```gherkin
Feature: 개별 항목 검증
  Scenario: 체크리스트 항목 거부
    Given 체크리스트에 Pass 상태 항목이 있음
    When 해당 항목의 "거부" 버튼 클릭
    Then 거부 사유 입력 모달이 표시됨
    When 사유 입력 후 "확인" 클릭
    Then final_status가 "Fail"로 변경됨
    And 사유가 comment 필드에 저장됨
    And 테이블 행 색상이 빨간색으로 변경됨
```

#### TC-1-1-008: 개별 항목 검증 - 수정
```gherkin
Feature: 개별 항목 검증
  Scenario: 체크리스트 항목 상태 수정
    Given 체크리스트에 항목이 있음
    When 해당 항목의 상태 드롭다운 클릭
    And "N/A" 선택
    Then final_status가 "N/A"로 변경됨
    And 해당 항목은 컴플라이언스율 계산에서 제외됨
```

#### TC-1-1-009: 일괄 승인
```gherkin
Feature: 일괄 검증
  Scenario: 다중 항목 일괄 승인
    Given 체크리스트에 5개 항목이 선택됨
    When "일괄 승인" 버튼 클릭
    Then 확인 다이얼로그 표시됨
    When "확인" 클릭
    Then 5개 항목 모두 final_status가 "Pass"로 변경됨
    And 단일 API 호출로 처리됨

  API Request:
    POST /api/v1/sessions/{session_id}/checklist/verify/bulk
    {
      "item_ids": ["CLK-001", "CLK-002", "CLK-003", "CLK-004", "CLK-005"],
      "action": "approve"
    }
```

#### TC-1-1-010: 컴플라이언스율 계산
```gherkin
Feature: 컴플라이언스율
  Scenario: 실시간 컴플라이언스율 계산
    Given 체크리스트에 60개 항목이 있음
    And 45개가 Pass, 10개가 Fail, 5개가 N/A
    Then 컴플라이언스율 = 45 / (60 - 5) * 100 = 81.8%
    And 헤더에 "컴플라이언스율: 81.8%" 표시됨
    And 진행률 바가 81.8% 채워짐

  Formula:
    compliance_rate = (pass_count / (total - na_count)) * 100
```

#### TC-1-1-011: 상태별 필터링
```gherkin
Feature: 상태 필터링
  Scenario Outline: 상태별 필터
    Given 체크리스트가 실행됨
    When 상태 필터에서 "<status>" 선택
    Then "<status>" 상태인 항목만 표시됨
    And 필터 칩에 선택된 상태가 표시됨

  Examples:
    | status          | expected_count |
    | All             | 60             |
    | Pass            | 45             |
    | Fail            | 10             |
    | Pending         | 3              |
    | Manual Required | 2              |
```

#### TC-1-1-012: 카테고리별 그룹화
```gherkin
Feature: 카테고리 그룹화
  Scenario: 규칙 카테고리별 그룹화
    Given 체크리스트가 실행됨
    When "카테고리별 그룹화" 토글 활성화
    Then 항목들이 카테고리별로 그룹화됨

  Categories:
    - Connectivity (연결성 검증)
    - Symbol (심볼 검증)
    - Labeling (라벨링 검증)
    - Instrument (계기 검증)
    - BWMS Specific (BWMS 전용)
```

#### TC-1-1-013: 체크리스트 Excel 내보내기
```gherkin
Feature: 체크리스트 내보내기
  Scenario: Excel 형식으로 내보내기
    Given 체크리스트가 실행됨
    And 일부 항목이 검증됨
    When "Excel 내보내기" 버튼 클릭
    Then Excel 파일 다운로드됨
    And 파일에 모든 항목 포함됨
    And auto_status와 final_status 모두 포함됨
    And 컴플라이언스율 요약 포함됨

  Excel Columns:
    - Item ID, Description, Category
    - Auto Status, Final Status
    - Comment, Verified By, Verified At
```

#### TC-1-1-014: 체크리스트 템플릿 업로드
```gherkin
Feature: 체크리스트 템플릿
  Scenario: 커스텀 체크리스트 업로드
    Given 체크리스트 화면에 있음
    When "템플릿 업로드" 버튼 클릭
    And 커스텀 Excel 파일 선택
    Then 파일 파싱됨
    And 커스텀 규칙이 추가됨
    And 다음 실행 시 커스텀 규칙 적용됨

  Template Format:
    | rule_id | description | category | severity |
```

#### TC-1-1-015: 제품 타입별 필터 (ECS/HYCHLOR)
```gherkin
Feature: 제품 타입 필터
  Scenario Outline: 제품별 규칙 필터링
    Given BWMS 체크리스트 화면에 있음
    When product_type 드롭다운에서 "<product>" 선택
    And "Run Checklist" 버튼 클릭
    Then "<product>" 제품 전용 규칙만 적용됨

  Examples:
    | product  | rules_count |
    | ALL      | 60          |
    | ECS      | 45          |
    | HYCHLOR  | 50          |
```

---

## 2. TECHCROSS 1-2: Valve Signal List

### 2.1 밸브 검출 및 분류 (12개)

#### TC-1-2-001: 밸브 신호 검출 실행
```gherkin
Feature: 밸브 신호 검출
  Scenario: P&ID에서 밸브 검출
    Given 세션에 P&ID 도면이 업로드되어 있음
    When "Valve Signal" 탭 클릭
    And "Detect Valves" 버튼 클릭
    Then PID Analyzer API 호출됨
    And 검출된 밸브 목록이 표시됨
    And 각 밸브에 신뢰도 점수가 표시됨

  API Request:
    POST /api/v1/sessions/{session_id}/valve-signal/detect

  Expected Response:
    {
      "valves": [
        {
          "id": "V-101",
          "type": "Control",
          "confidence": 0.95,
          "position": { "x": 100, "y": 200, "width": 50, "height": 50 },
          "attributes": { "actuator": "pneumatic", "size": "2inch" }
        }
      ],
      "total_count": 25
    }
```

#### TC-1-2-002: 밸브 카테고리 - Control Valve
```gherkin
Feature: 밸브 카테고리 분류
  Scenario: 제어 밸브 식별
    Given 밸브 검출이 완료됨
    When 카테고리 필터에서 "Control" 선택
    Then 제어 밸브만 표시됨
    And 심볼이 제어 밸브 패턴과 일치함

  Identification Patterns:
    - Symbol: 조절 밸브 심볼 (다이아몬드 + 삼각형)
    - Tag: CV-xxx, FCV-xxx, LCV-xxx, PCV-xxx
    - Actuator: 공압/전동 액추에이터 표시
```

#### TC-1-2-003: 밸브 카테고리 - Isolation Valve
```gherkin
Feature: 밸브 카테고리 분류
  Scenario: 격리 밸브 식별
    Given 밸브 검출이 완료됨
    When 카테고리 필터에서 "Isolation" 선택
    Then 격리 밸브만 표시됨

  Identification Patterns:
    - Symbol: 게이트/볼/플러그 밸브 심볼
    - Tag: IV-xxx, BV-xxx, GV-xxx
    - Function: 유체 차단용
```

#### TC-1-2-004: 밸브 카테고리 - Safety Valve
```gherkin
Feature: 밸브 카테고리 분류
  Scenario: 안전 밸브 식별
    Given 밸브 검출이 완료됨
    When 카테고리 필터에서 "Safety" 선택
    Then 안전 밸브만 표시됨

  Identification Patterns:
    - Symbol: 안전 밸브 심볼 (스프링 표시)
    - Tag: SV-xxx, PSV-xxx, RV-xxx
    - Function: 과압 방지용
```

#### TC-1-2-005: 밸브 카테고리 - Check Valve
```gherkin
Feature: 밸브 카테고리 분류
  Scenario: 체크 밸브 식별
    Given 밸브 검출이 완료됨
    When 카테고리 필터에서 "Check" 선택
    Then 체크 밸브만 표시됨

  Identification Patterns:
    - Symbol: 체크 밸브 심볼 (화살표 방향 표시)
    - Tag: CHK-xxx, CV-xxx (context 확인)
    - Function: 역류 방지용
```

#### TC-1-2-006: 밸브 카테고리 - Relief Valve
```gherkin
Feature: 밸브 카테고리 분류
  Scenario: 릴리프 밸브 식별
    Given 밸브 검출이 완료됨
    When 카테고리 필터에서 "Relief" 선택
    Then 릴리프 밸브만 표시됨

  Identification Patterns:
    - Symbol: 릴리프 밸브 심볼
    - Tag: RV-xxx, PRV-xxx
    - Function: 압력 해제용
```

#### TC-1-2-007: 밸브 ID 패턴 인식
```gherkin
Feature: 밸브 ID 인식
  Scenario: 다양한 밸브 ID 형식 인식
    Given 밸브 검출이 완료됨
    Then 다양한 ID 형식이 올바르게 파싱됨

  Supported Patterns:
    | Pattern      | Example     | Parsed As        |
    | V-xxx        | V-101       | Valve 101        |
    | XXV-xxx      | PCV-201     | Pressure CV 201  |
    | xxx-V-xxx    | 10-V-101    | Area 10, V 101   |
    | V-xxx-A/B    | V-101-A     | Valve 101 Train A|
```

#### TC-1-2-008: 밸브 신뢰도 색상 코딩
```gherkin
Feature: 신뢰도 시각화
  Scenario: 신뢰도에 따른 색상 코딩
    Given 밸브 검출이 완료됨
    Then 각 밸브 행에 신뢰도 색상이 적용됨

  Color Coding:
    | Confidence Range | Color  | Badge      |
    | 0.95 - 1.00      | Green  | High       |
    | 0.80 - 0.94      | Yellow | Medium     |
    | 0.60 - 0.79      | Orange | Low        |
    | 0.00 - 0.59      | Red    | Very Low   |
```

#### TC-1-2-009: 밸브 검증 워크플로우 - 승인
```gherkin
Feature: 밸브 검증
  Scenario: 검출된 밸브 승인
    Given 밸브 목록에 미검증 항목이 있음
    When 해당 밸브의 "승인" 버튼 클릭
    Then 밸브 상태가 "Verified"로 변경됨
    And 테이블에서 녹색 체크 아이콘 표시됨
    And Active Learning 데이터셋에 추가됨

  API Request:
    POST /api/v1/sessions/{session_id}/verify
    {
      "item_id": "V-101",
      "item_type": "valve",
      "action": "approve"
    }
```

#### TC-1-2-010: 밸브 검증 워크플로우 - 수정
```gherkin
Feature: 밸브 검증
  Scenario: 검출된 밸브 정보 수정
    Given 밸브 목록에 잘못 분류된 항목이 있음
    When 해당 밸브의 "수정" 버튼 클릭
    Then 수정 모달이 표시됨
    And 밸브 ID, 타입, 속성 수정 가능
    When 수정 후 "저장" 클릭
    Then 밸브 정보가 업데이트됨
    And 상태가 "Modified"로 변경됨

  Editable Fields:
    - valve_id (string)
    - valve_type (select: Control/Isolation/Safety/Check/Relief/Unknown)
    - actuator_type (select: Manual/Pneumatic/Electric/Hydraulic)
    - size (string)
    - material (string)
```

#### TC-1-2-011: 밸브 검증 워크플로우 - 거부
```gherkin
Feature: 밸브 검증
  Scenario: 잘못 검출된 밸브 거부
    Given 밸브 목록에 오검출 항목이 있음
    When 해당 밸브의 "거부" 버튼 클릭
    Then 거부 사유 선택 모달 표시됨
    When 사유 선택 후 "확인" 클릭
    Then 밸브가 목록에서 비활성화됨
    And 상태가 "Rejected"로 변경됨
    And Negative 학습 데이터로 표시됨

  Rejection Reasons:
    - false_positive: 밸브가 아님
    - wrong_classification: 잘못된 분류
    - duplicate: 중복 검출
    - partial_detection: 불완전한 검출
```

#### TC-1-2-012: 밸브 신호 목록 Excel 내보내기
```gherkin
Feature: 밸브 목록 내보내기
  Scenario: Valve Signal List Excel 내보내기
    Given 밸브 검출 및 검증이 완료됨
    When "Export Excel" 버튼 클릭
    Then TECHCROSS 양식의 Excel 파일 생성됨
    And 모든 밸브 정보 포함됨
    And 검증 상태 포함됨

  Excel Template (TECHCROSS 1-2):
    | No | Valve ID | Type | Actuator | Size | Location | Status |
```

---

## 3. TECHCROSS 1-3: Equipment List

### 3.1 장비 검출 및 분류 (12개)

#### TC-1-3-001: 장비 검출 실행
```gherkin
Feature: 장비 검출
  Scenario: P&ID에서 장비 검출
    Given 세션에 P&ID 도면이 업로드되어 있음
    When "Equipment" 탭 클릭
    And "Detect Equipment" 버튼 클릭
    Then PID Analyzer API 호출됨
    And 검출된 장비 목록이 표시됨

  API Request:
    POST /api/v1/sessions/{session_id}/equipment/detect

  Expected Response:
    {
      "equipment": [
        {
          "id": "ECU-001",
          "type": "ECU",
          "confidence": 0.92,
          "position": { "x": 200, "y": 300, "width": 100, "height": 80 },
          "attributes": { "manufacturer": "TECHCROSS", "model": "ECS-200" }
        }
      ],
      "total_count": 15
    }
```

#### TC-1-3-002: 장비 타입 - PUMP
```gherkin
Feature: 장비 타입 분류
  Scenario: 펌프 식별
    Given 장비 검출이 완료됨
    When 타입 필터에서 "PUMP" 선택
    Then 펌프만 표시됨

  Identification Patterns:
    - Symbol: 원형 펌프 심볼
    - Tag: P-xxx, PP-xxx
    - Subtypes: Centrifugal, Positive Displacement, Dosing
```

#### TC-1-3-003: 장비 타입 - VALVE (Automatic)
```gherkin
Feature: 장비 타입 분류
  Scenario: 자동 밸브 장비 식별
    Given 장비 검출이 완료됨
    When 타입 필터에서 "VALVE" 선택
    Then 자동 밸브 장비만 표시됨
    And 제어 밸브와 구분됨 (Signal List vs Equipment)
```

#### TC-1-3-004: 장비 타입 - TANK
```gherkin
Feature: 장비 타입 분류
  Scenario: 탱크 식별
    Given 장비 검출이 완료됨
    When 타입 필터에서 "TANK" 선택
    Then 탱크만 표시됨

  Identification Patterns:
    - Symbol: 원통형 탱크 심볼
    - Tag: T-xxx, TK-xxx
    - Subtypes: Storage, Process, Buffer
```

#### TC-1-3-005: 장비 타입 - HEAT_EXCHANGER
```gherkin
Feature: 장비 타입 분류
  Scenario: 열교환기 식별
    Given 장비 검출이 완료됨
    When 타입 필터에서 "HEAT_EXCHANGER" 선택
    Then 열교환기만 표시됨

  Identification Patterns:
    - Symbol: 열교환기 심볼 (Shell & Tube, Plate)
    - Tag: E-xxx, HX-xxx
```

#### TC-1-3-006: 장비 타입 - FILTER
```gherkin
Feature: 장비 타입 분류
  Scenario: 필터 식별
    Given 장비 검출이 완료됨
    When 타입 필터에서 "FILTER" 선택
    Then 필터만 표시됨

  Identification Patterns:
    - Symbol: 필터 심볼
    - Tag: F-xxx, FLT-xxx, STR-xxx
```

#### TC-1-3-007: BWMS 장비 태그 인식 - ECU/FMU/HGU
```gherkin
Feature: BWMS 장비 인식
  Scenario: TECHCROSS BWMS 전용 장비 인식
    Given 장비 검출이 완료됨
    Then BWMS 전용 장비 태그가 올바르게 인식됨

  BWMS Equipment Tags:
    | Tag   | Full Name                    | Function           |
    | ECU   | Electrochlorination Unit     | 전기분해 장치      |
    | FMU   | Filtration Module Unit       | 여과 모듈          |
    | HGU   | Hydrogen Gas Unit            | 수소 가스 처리     |
    | NMU   | Neutralization Module Unit   | 중화 모듈          |
    | TRO   | Total Residual Oxidant       | 잔류 산화제 측정   |
```

#### TC-1-3-008: 공급업체 표시
```gherkin
Feature: 공급업체 정보
  Scenario: 장비 공급업체 표시
    Given 장비 검출이 완료됨
    And 일부 장비에 공급업체 정보가 있음
    Then 공급업체 컬럼에 정보 표시됨
    And 공급업체 없으면 "-" 표시됨

  Supplier Info Sources:
    - 도면 내 텍스트 (OCR)
    - 장비 라벨
    - 범례 참조
```

#### TC-1-3-009: 장비 검증 워크플로우 - 승인
```gherkin
Feature: 장비 검증
  Scenario: 검출된 장비 승인
    Given 장비 목록에 미검증 항목이 있음
    When 해당 장비의 "승인" 버튼 클릭
    Then 장비 상태가 "Verified"로 변경됨
    And 녹색 체크 아이콘 표시됨

  API Request:
    POST /api/v1/sessions/{session_id}/verify
    {
      "item_id": "ECU-001",
      "item_type": "equipment",
      "action": "approve"
    }
```

#### TC-1-3-010: 장비 검증 워크플로우 - 수정
```gherkin
Feature: 장비 검증
  Scenario: 검출된 장비 정보 수정
    Given 장비 목록에 수정이 필요한 항목이 있음
    When 해당 장비의 "수정" 버튼 클릭
    Then 수정 모달이 표시됨
    And 장비 ID, 타입, 속성 수정 가능

  Editable Fields:
    - equipment_id (string)
    - equipment_type (select: PUMP/VALVE/TANK/...)
    - manufacturer (string)
    - model (string)
    - capacity (string)
    - material (string)
```

#### TC-1-3-011: 장비 검증 워크플로우 - 거부
```gherkin
Feature: 장비 검증
  Scenario: 잘못 검출된 장비 거부
    Given 장비 목록에 오검출 항목이 있음
    When 해당 장비의 "거부" 버튼 클릭
    Then 거부 사유 선택 모달 표시됨
    When 사유 선택 후 "확인" 클릭
    Then 장비가 목록에서 비활성화됨
```

#### TC-1-3-012: 장비 목록 Excel 내보내기
```gherkin
Feature: 장비 목록 내보내기
  Scenario: Equipment List Excel 내보내기
    Given 장비 검출 및 검증이 완료됨
    When "Export Excel" 버튼 클릭
    Then TECHCROSS 양식의 Excel 파일 생성됨

  Excel Template (TECHCROSS 1-3):
    | No | Tag | Equipment Name | Type | Manufacturer | Model | Qty | Remarks |
```

---

## 4. TECHCROSS 1-4: Deviation Analysis

### 4.1 편차 분석 (11개)

#### TC-1-4-001: 편차 분석 실행
```gherkin
Feature: 편차 분석
  Scenario: P&ID 편차 분석 실행
    Given 세션에 P&ID 도면이 업로드되어 있음
    And 심볼 검출이 완료됨
    When "Deviation Analysis" 탭 클릭
    And "Analyze Deviations" 버튼 클릭
    Then Design Checker API 호출됨
    And 검출된 편차 목록이 표시됨

  API Request:
    POST /api/v1/sessions/{session_id}/deviation/analyze

  Expected Response:
    {
      "deviations": [
        {
          "id": "DEV-001",
          "type": "missing_connection",
          "severity": "high",
          "description": "V-101에서 T-102로의 연결 누락",
          "position": { "x": 150, "y": 250 },
          "recommendation": "연결 라인 추가 권장"
        }
      ],
      "summary": {
        "critical": 2,
        "high": 5,
        "medium": 10,
        "low": 8,
        "info": 3
      }
    }
```

#### TC-1-4-002: 심각도 레벨 필터링 - Critical
```gherkin
Feature: 심각도 필터
  Scenario: Critical 편차만 표시
    Given 편차 분석이 완료됨
    When 심각도 필터에서 "Critical" 선택
    Then Critical 심각도 편차만 표시됨
    And 빨간색 배경으로 강조됨

  Critical Examples:
    - 안전 밸브 누락
    - 필수 계기 미설치
    - 중요 연결 단절
```

#### TC-1-4-003: 심각도 레벨 필터링 - High
```gherkin
Feature: 심각도 필터
  Scenario: High 편차 표시
    Given 편차 분석이 완료됨
    When 심각도 필터에서 "High" 선택
    Then High 심각도 편차만 표시됨

  High Examples:
    - 제어 밸브 위치 오류
    - 계기 연결 오류
    - 라인 번호 불일치
```

#### TC-1-4-004: 심각도 레벨 필터링 - Medium/Low/Info
```gherkin
Feature: 심각도 필터
  Scenario Outline: 다양한 심각도 필터
    Given 편차 분석이 완료됨
    When 심각도 필터에서 "<severity>" 선택
    Then "<severity>" 심각도 편차만 표시됨

  Examples:
    | severity | example                          |
    | Medium   | 라벨링 불일치                    |
    | Low      | 심볼 스타일 비표준               |
    | Info     | 권장 사항 (개선 제안)            |
```

#### TC-1-4-005: 분석 타입 선택 - connectivity
```gherkin
Feature: 분석 타입
  Scenario: 연결성 분석
    Given 편차 분석 화면에 있음
    When analysis_types에서 "connectivity" 선택
    And "Analyze" 버튼 클릭
    Then 연결성 관련 편차만 분석됨

  Connectivity Checks:
    - 연결 누락
    - 데드엔드 감지
    - 순환 경로 확인
    - 고립된 장비 감지
```

#### TC-1-4-006: 분석 타입 선택 - symbol_validation
```gherkin
Feature: 분석 타입
  Scenario: 심볼 검증 분석
    Given 편차 분석 화면에 있음
    When analysis_types에서 "symbol_validation" 선택
    And "Analyze" 버튼 클릭
    Then 심볼 관련 편차만 분석됨

  Symbol Checks:
    - 비표준 심볼 사용
    - 심볼 크기 불일치
    - 심볼 방향 오류
    - 누락된 심볼
```

#### TC-1-4-007: 표준 선택 - ISO 10628
```gherkin
Feature: 표준 선택
  Scenario: ISO 10628 표준 기반 분석
    Given 편차 분석 화면에 있음
    When standards에서 "ISO 10628" 선택
    And "Analyze" 버튼 클릭
    Then ISO 10628 규칙 기반 편차 분석됨

  ISO 10628 Rules:
    - 심볼 표기법
    - 라인 스타일
    - 라벨링 규칙
```

#### TC-1-4-008: 표준 선택 - ISA 5.1
```gherkin
Feature: 표준 선택
  Scenario: ISA 5.1 표준 기반 분석
    Given 편차 분석 화면에 있음
    When standards에서 "ISA 5.1" 선택
    And "Analyze" 버튼 클릭
    Then ISA 5.1 규칙 기반 편차 분석됨

  ISA 5.1 Rules:
    - 계기 태그 형식
    - 기능 문자 코드
    - 계기 심볼 표준
```

#### TC-1-4-009: 표준 선택 - BWMS
```gherkin
Feature: 표준 선택
  Scenario: BWMS 규정 기반 분석
    Given 편차 분석 화면에 있음
    When standards에서 "BWMS" 선택
    And "Analyze" 버튼 클릭
    Then BWMS 규정 기반 편차 분석됨

  BWMS Rules:
    - 밸러스트 탱크 벤트 연결
    - 처리 시스템 흐름
    - 샘플링 포인트 위치
    - 바이패스 밸브 설치
```

#### TC-1-4-010: 기준선 세션 비교
```gherkin
Feature: 기준선 비교
  Scenario: 이전 버전과 현재 버전 비교
    Given 현재 세션에 P&ID가 있음
    And 기준선 세션이 선택 가능함
    When "Compare with Baseline" 드롭다운에서 기준선 세션 선택
    And "Compare" 버튼 클릭
    Then 두 버전 간 차이점 분석됨
    And 추가/삭제/수정된 항목 표시됨

  Comparison Results:
    - Added: 새로 추가된 심볼/연결
    - Removed: 삭제된 심볼/연결
    - Modified: 변경된 심볼/연결
    - Unchanged: 동일한 항목
```

#### TC-1-4-011: 편차 목록 내보내기
```gherkin
Feature: 편차 목록 내보내기
  Scenario: Deviation List Excel 내보내기
    Given 편차 분석이 완료됨
    When "Export Excel" 버튼 클릭
    Then TECHCROSS 양식의 Excel 파일 생성됨

  Excel Template (TECHCROSS 1-4):
    | No | Deviation ID | Type | Severity | Description | Location | Recommendation | Status |
```

---

## 5. 통합 워크플로우

### 5.1 전체 TECHCROSS 워크플로우 (5개)

#### TC-INT-001: 전체 워크플로우 순차 실행
```gherkin
Feature: 전체 워크플로우
  Scenario: TECHCROSS 1-1 ~ 1-4 순차 실행
    Given 새 세션이 생성됨
    When P&ID 도면 업로드
    And 심볼 검출 실행
    And BWMS Checklist 실행 (1-1)
    And Valve Signal 검출 (1-2)
    And Equipment 검출 (1-3)
    And Deviation Analysis 실행 (1-4)
    Then 모든 워크플로우가 성공적으로 완료됨
    And 각 단계의 결과가 저장됨
```

#### TC-INT-002: 워크플로우 간 데이터 공유
```gherkin
Feature: 데이터 공유
  Scenario: 워크플로우 간 검출 결과 공유
    Given Valve Signal 검출이 완료됨 (1-2)
    When Equipment 검출 실행 (1-3)
    Then 이전 검출 결과가 참조됨
    And 중복 검출이 방지됨
    And 연관된 밸브-장비 관계가 표시됨
```

#### TC-INT-003: 통합 내보내기
```gherkin
Feature: 통합 내보내기
  Scenario: 전체 워크플로우 결과 일괄 내보내기
    Given 모든 워크플로우가 완료됨
    When "Export All" 버튼 클릭
    And 형식으로 "Excel (Combined)" 선택
    Then 단일 Excel 파일에 모든 결과 포함됨

  Combined Excel Sheets:
    - Summary (요약)
    - Checklist (1-1)
    - Valve Signal List (1-2)
    - Equipment List (1-3)
    - Deviation List (1-4)
```

#### TC-INT-004: 워크플로우 상태 추적
```gherkin
Feature: 상태 추적
  Scenario: 워크플로우 진행 상태 표시
    Given 세션이 열려있음
    Then 워크플로우 진행률 바가 표시됨
    And 각 단계의 완료 상태가 표시됨

  Status Indicators:
    - Not Started (회색)
    - In Progress (파란색)
    - Completed (녹색)
    - Error (빨간색)
    - Skipped (노란색)
```

#### TC-INT-005: 워크플로우 요약 대시보드
```gherkin
Feature: 요약 대시보드
  Scenario: 전체 워크플로우 요약 표시
    Given 워크플로우가 진행 중이거나 완료됨
    When "Summary" 탭 클릭
    Then 전체 요약 대시보드가 표시됨

  Summary Dashboard:
    - 체크리스트 컴플라이언스율
    - 검출된 밸브/장비 수
    - 검증 진행률
    - 편차 심각도 분포
    - 내보내기 버튼

  API:
    GET /api/v1/sessions/{session_id}/summary
```

---

## 6. 테스트 데이터 요구사항

### 6.1 필수 테스트 이미지

| 파일명 | 용도 | 요구사항 |
|--------|------|----------|
| `bwms_pid_001.png` | BWMS P&ID 기본 | ECU, FMU 포함 |
| `bwms_pid_002.png` | BWMS P&ID 복잡 | 30+ 밸브, 15+ 장비 |
| `pid_valve_test.png` | 밸브 테스트 | 6가지 카테고리 포함 |
| `pid_equipment_test.png` | 장비 테스트 | 9가지 타입 포함 |
| `pid_deviation_test.png` | 편차 테스트 | 의도적 오류 포함 |
| `pid_baseline_v1.png` | 기준선 v1 | 리비전 비교용 |
| `pid_baseline_v2.png` | 기준선 v2 | 리비전 비교용 |

### 6.2 기대 결과 데이터

각 테스트 이미지에 대한 기대 결과는 `07-data-fixtures.md`에 정의됩니다.

---

## 7. 자동화 상태

| 시나리오 | 자동화 | 우선순위 | 비고 |
|----------|--------|----------|------|
| TC-1-1-001 ~ 015 | 40% | P1 | 체크리스트 기본 |
| TC-1-2-001 ~ 012 | 33% | P1 | 밸브 신호 |
| TC-1-3-001 ~ 012 | 33% | P1 | 장비 목록 |
| TC-1-4-001 ~ 011 | 20% | P2 | 편차 분석 |
| TC-INT-001 ~ 005 | 20% | P1 | 통합 워크플로우 |

---

## 8. 관련 문서

- [01-api-endpoints.md](./01-api-endpoints.md) - API 엔드포인트 테스트
- [04-hyperparameters.md](./04-hyperparameters.md) - 하이퍼파라미터 테스트
- [06-integration.md](./06-integration.md) - 통합 테스트
- [TECHCROSS 요구사항 분석](/.todos/TECHCROSS_요구사항_분석_20251229.md)
