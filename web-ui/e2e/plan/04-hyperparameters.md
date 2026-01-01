# 하이퍼파라미터 테스트 시나리오

> **총 테스트 수**: 40+
> **우선순위**: P1 (High)
> **관련 컴포넌트**: 검출 설정, 분석 옵션, 내보내기 설정

---

## 목차

1. [Detection 파라미터](#1-detection-파라미터)
2. [OCR 파라미터](#2-ocr-파라미터)
3. [Analysis 파라미터](#3-analysis-파라미터)
4. [P&ID Features 파라미터](#4-pid-features-파라미터)
5. [Export 파라미터](#5-export-파라미터)
6. [파라미터 지속성](#6-파라미터-지속성)

---

## 1. Detection 파라미터

### 1.1 Confidence Threshold (12개)

#### HP-DET-001: confidence 기본값 검증
```gherkin
Feature: Confidence 기본값
  Scenario: 기본 confidence 값 확인
    Given 새 세션이 생성됨
    When 검출 설정 패널 열기
    Then confidence 슬라이더가 0.25로 설정됨
    And 입력 필드에 "0.25" 표시됨

  Default Value: 0.25
  Range: 0.05 ~ 1.00
  Step: 0.05
```

#### HP-DET-002: confidence 최솟값 경계
```gherkin
Feature: Confidence 경계값
  Scenario: 최솟값 0.05 검증
    Given 검출 설정 패널이 열려있음
    When confidence 슬라이더를 0.05로 설정
    And "Run Detection" 클릭
    Then API 호출 시 confidence=0.05 전달됨
    And 더 많은 검출 결과 표시됨 (낮은 신뢰도 포함)

  API Request:
    POST /api/v1/sessions/{session_id}/detect
    { "confidence": 0.05 }

  Behavior:
    - 노이즈 증가
    - 검출 수 증가 (3-5배)
    - False Positive 증가
```

#### HP-DET-003: confidence 최댓값 경계
```gherkin
Feature: Confidence 경계값
  Scenario: 최댓값 1.00 검증
    Given 검출 설정 패널이 열려있음
    When confidence 슬라이더를 1.00로 설정
    And "Run Detection" 클릭
    Then API 호출 시 confidence=1.0 전달됨
    And 매우 높은 신뢰도 검출만 표시됨

  Behavior:
    - 검출 수 감소 (0-5개)
    - False Positive 최소화
    - 일부 True Positive 누락 가능
```

#### HP-DET-004: confidence 슬라이더 드래그
```gherkin
Feature: Confidence 슬라이더
  Scenario: 슬라이더 드래그로 값 변경
    Given 검출 설정 패널이 열려있음
    When confidence 슬라이더를 0.5 위치로 드래그
    Then 입력 필드 값이 "0.50"으로 업데이트됨
    And 슬라이더 위치가 중간으로 이동됨

  UI Validation:
    - 실시간 값 업데이트
    - 0.05 단위로 스냅
```

#### HP-DET-005: confidence 직접 입력
```gherkin
Feature: Confidence 직접 입력
  Scenario: 입력 필드에 직접 값 입력
    Given 검출 설정 패널이 열려있음
    When confidence 입력 필드에 "0.75" 입력
    And Enter 키 누름
    Then 슬라이더가 0.75 위치로 이동됨
    And 값이 저장됨
```

#### HP-DET-006: confidence 범위 외 값 거부
```gherkin
Feature: Confidence 유효성 검사
  Scenario Outline: 범위 외 값 입력 시 거부
    Given 검출 설정 패널이 열려있음
    When confidence 입력 필드에 "<invalid_value>" 입력
    And Enter 키 누름
    Then 에러 메시지 "0.05 ~ 1.00 범위만 허용됩니다" 표시됨
    And 값이 이전 값으로 복원됨

  Examples:
    | invalid_value | description    |
    | 0.00          | 최솟값 미만    |
    | 0.03          | 스텝 미만      |
    | 1.50          | 최댓값 초과    |
    | -0.1          | 음수           |
    | abc           | 문자열         |
```

#### HP-DET-007: confidence 검출 결과 영향
```gherkin
Feature: Confidence 영향 분석
  Scenario: confidence 변경 시 검출 결과 변화
    Given 동일한 이미지로 검출 실행
    When confidence를 0.25, 0.50, 0.75로 각각 설정하여 검출
    Then 검출 수가 confidence에 반비례함

  Expected Pattern:
    | confidence | expected_range |
    | 0.25       | 50-100개       |
    | 0.50       | 20-50개        |
    | 0.75       | 5-20개         |
```

### 1.2 IOU Threshold (6개)

#### HP-DET-008: iou_threshold 기본값
```gherkin
Feature: IOU Threshold 기본값
  Scenario: 기본 iou_threshold 값 확인
    Given 검출 설정 패널이 열려있음
    Then iou_threshold 슬라이더가 0.45로 설정됨

  Default Value: 0.45
  Range: 0.10 ~ 0.95
  Step: 0.05
```

#### HP-DET-009: iou_threshold 낮은 값 (겹침 허용)
```gherkin
Feature: IOU Threshold 낮은 값
  Scenario: 겹치는 검출 허용
    Given 검출 설정 패널이 열려있음
    When iou_threshold를 0.10으로 설정
    And "Run Detection" 클릭
    Then 겹치는 바운딩 박스가 더 많이 표시됨
    And 동일 심볼에 여러 검출 가능

  Use Case: 밀집된 심볼 검출
```

#### HP-DET-010: iou_threshold 높은 값 (NMS 강화)
```gherkin
Feature: IOU Threshold 높은 값
  Scenario: 엄격한 중복 제거
    Given 검출 설정 패널이 열려있음
    When iou_threshold를 0.95로 설정
    And "Run Detection" 클릭
    Then 거의 모든 겹치는 박스가 제거됨
    And 명확히 구분된 심볼만 표시됨

  Use Case: 정밀한 개별 심볼 검출
```

#### HP-DET-011: iou_threshold와 confidence 조합
```gherkin
Feature: 파라미터 조합
  Scenario: confidence와 iou_threshold 조합 최적화
    Given 검출 설정 패널이 열려있음
    When confidence=0.3, iou_threshold=0.5 설정
    And "Run Detection" 클릭
    Then 균형 잡힌 검출 결과 표시됨

  Recommended Combinations:
    | Use Case       | confidence | iou_threshold |
    | 빠른 스캔      | 0.15       | 0.30          |
    | 균형           | 0.25       | 0.45          |
    | 정밀           | 0.50       | 0.60          |
    | 초정밀         | 0.75       | 0.80          |
```

### 1.3 Image Size (6개)

#### HP-DET-012: imgsz 기본값
```gherkin
Feature: Image Size 기본값
  Scenario: 기본 imgsz 값 확인
    Given 검출 설정 패널이 열려있음
    Then imgsz 드롭다운이 "1024"로 설정됨

  Default Value: 1024
  Options: 320, 480, 640, 800, 1024, 1280, 1536, 2048, 4096
```

#### HP-DET-013: imgsz 작은 값 (속도 우선)
```gherkin
Feature: Image Size 작은 값
  Scenario: 빠른 검출을 위한 작은 이미지
    Given 검출 설정 패널이 열려있음
    When imgsz 드롭다운에서 "320" 선택
    And "Run Detection" 클릭
    Then 검출이 빠르게 완료됨 (<1초)
    And 작은 심볼은 누락될 수 있음

  Trade-off:
    - 속도: 3-5배 빠름
    - 정확도: 10-20% 감소
    - 메모리: 50% 감소
```

#### HP-DET-014: imgsz 큰 값 (정확도 우선)
```gherkin
Feature: Image Size 큰 값
  Scenario: 정밀 검출을 위한 큰 이미지
    Given 검출 설정 패널이 열려있음
    When imgsz 드롭다운에서 "2048" 선택
    And "Run Detection" 클릭
    Then 작은 심볼도 검출됨
    And 처리 시간이 증가함 (5-10초)

  Trade-off:
    - 속도: 3-5배 느림
    - 정확도: 15-25% 증가
    - 메모리: 4배 증가
```

#### HP-DET-015: imgsz GPU 메모리 영향
```gherkin
Feature: Image Size 메모리 영향
  Scenario: imgsz에 따른 GPU 메모리 사용량
    Given GPU 모드로 검출 실행
    Then imgsz에 따른 메모리 사용량:

  Memory Usage (approximate):
    | imgsz | VRAM Usage |
    | 320   | ~0.5 GB    |
    | 640   | ~1.0 GB    |
    | 1024  | ~1.5 GB    |
    | 1280  | ~2.0 GB    |
    | 2048  | ~3.5 GB    |
    | 4096  | ~8.0 GB    |
```

### 1.4 Model Selection (4개)

#### HP-DET-016: model_type 선택
```gherkin
Feature: Model Type 선택
  Scenario Outline: 다양한 모델 타입 선택
    Given 검출 설정 패널이 열려있음
    When model_type 드롭다운에서 "<model>" 선택
    And "Run Detection" 클릭
    Then "<model>" 모델로 검출 수행됨
    And 해당 모델의 클래스가 검출됨

  Examples:
    | model          | classes     | use_case          |
    | engineering    | 27개        | 기계 도면         |
    | pid_class_aware| 50+개       | P&ID 도면         |
    | bom_detector   | 15개        | BOM 부품          |
    | yolov11n       | 80개        | 일반 객체         |
```

#### HP-DET-017: model_id 선택
```gherkin
Feature: Model ID 선택
  Scenario: 특정 모델 버전 선택
    Given 검출 설정 패널이 열려있음
    When model_id 드롭다운에서 "yolov11s" 선택
    Then 모델 크기가 변경됨

  Model Sizes:
    | model_id | parameters | speed  | accuracy |
    | yolov11n | 2.6M       | 빠름   | 보통     |
    | yolov11s | 9.4M       | 보통   | 좋음     |
    | yolov11m | 20.1M      | 느림   | 매우 좋음|
```

---

## 2. OCR 파라미터

### 2.1 OCR 엔진 선택 (6개)

#### HP-OCR-001: OCR 엔진 선택
```gherkin
Feature: OCR 엔진 선택
  Scenario Outline: 다양한 OCR 엔진 테스트
    Given OCR 설정 패널이 열려있음
    When ocr_engine 드롭다운에서 "<engine>" 선택
    And "Run OCR" 클릭
    Then "<engine>" 엔진으로 OCR 수행됨

  Examples:
    | engine     | port | specialty          |
    | edocr2     | 5002 | 한국어 치수        |
    | paddleocr  | 5006 | 다국어             |
    | tesseract  | 5008 | 문서 텍스트        |
    | trocr      | 5009 | 필기체             |
    | ensemble   | 5011 | 4엔진 가중 투표    |
    | surya      | 5013 | 90+ 언어           |
    | doctr      | 5014 | 2단계 파이프라인   |
    | easyocr    | 5015 | 80+ 언어           |
```

#### HP-OCR-002: language 파라미터
```gherkin
Feature: OCR 언어 설정
  Scenario: 언어 파라미터 설정
    Given OCR 설정 패널이 열려있음
    When language 드롭다운에서 "ko+en" 선택
    And "Run OCR" 클릭
    Then 한국어와 영어 혼합 인식 수행됨

  Language Options:
    - ko: 한국어만
    - en: 영어만
    - ko+en: 한국어 + 영어
    - ja: 일본어
    - zh: 중국어
```

#### HP-OCR-003: detect_rotation 토글
```gherkin
Feature: 회전 감지
  Scenario: 회전된 텍스트 감지 활성화
    Given OCR 설정 패널이 열려있음
    When detect_rotation 토글 활성화
    And "Run OCR" 클릭
    Then 회전된 텍스트도 인식됨
    And 각도 정보가 결과에 포함됨

  API Request:
    { "detect_rotation": true }
```

### 2.2 eDOCr2 전용 파라미터 (4개)

#### HP-OCR-004: dimension_mode
```gherkin
Feature: eDOCr2 Dimension Mode
  Scenario: 치수 인식 모드 선택
    Given eDOCr2 OCR 설정 패널이 열려있음
    When dimension_mode 드롭다운에서 "detailed" 선택
    Then 상세 치수 파싱 활성화됨

  Modes:
    - basic: 기본 치수만
    - detailed: 공차, 단위 포함
    - gdt: GD&T 심볼 포함
```

#### HP-OCR-005: tolerance_parsing
```gherkin
Feature: 공차 파싱
  Scenario: 공차 정보 파싱 활성화
    Given eDOCr2 OCR 설정 패널이 열려있음
    When tolerance_parsing 토글 활성화
    And "Run OCR" 클릭
    Then 공차 정보가 별도 필드로 파싱됨

  Example Output:
    {
      "value": "50.00",
      "tolerance_upper": "+0.05",
      "tolerance_lower": "-0.02",
      "unit": "mm"
    }
```

---

## 3. Analysis 파라미터

### 3.1 GD&T 파싱 (4개)

#### HP-ANA-001: parse_gdt 활성화
```gherkin
Feature: GD&T 파싱
  Scenario: GD&T 심볼 파싱 활성화
    Given 분석 설정 패널이 열려있음
    When parse_gdt 토글 활성화
    And "Run Analysis" 클릭
    Then GD&T 심볼이 파싱됨
    And 기하공차 정보가 추출됨

  GD&T Symbols:
    - 평면도 (Flatness): ⏥
    - 직진도 (Straightness): ⏤
    - 진원도 (Circularity): ○
    - 원통도 (Cylindricity): ⌭
    - 위치도 (Position): ⌖
    - 동심도 (Concentricity): ⊚
```

#### HP-ANA-002: gdt_standard 선택
```gherkin
Feature: GD&T 표준 선택
  Scenario: GD&T 표준 규격 선택
    Given GD&T 파싱이 활성화됨
    When gdt_standard 드롭다운에서 "ASME Y14.5" 선택
    Then ASME 표준에 따른 파싱 수행됨

  Standards:
    - ASME Y14.5 (2018)
    - ISO 1101 (2017)
    - JIS B 0021
```

### 3.2 VLM 분류 (4개)

#### HP-ANA-003: vlm_provider 선택
```gherkin
Feature: VLM 프로바이더
  Scenario: VLM 프로바이더 선택
    Given VLM 분류 설정 패널이 열려있음
    When vlm_provider 드롭다운에서 "openai" 선택
    Then OpenAI API 사용하여 분류 수행됨

  Providers:
    - openai: GPT-4o-mini
    - anthropic: Claude 3 Haiku
    - local: 로컬 VL 모델 (5004)
```

#### HP-ANA-004: vlm_temperature
```gherkin
Feature: VLM Temperature
  Scenario: VLM Temperature 설정
    Given VLM 분류 설정 패널이 열려있음
    When temperature 슬라이더를 0.2로 설정
    Then 결정적 응답 생성 (낮은 다양성)

  Range: 0.0 ~ 1.0
  Default: 0.3

  Effect:
    - 0.0: 완전 결정적
    - 0.3: 약간 다양
    - 0.7: 창의적
    - 1.0: 매우 다양
```

---

## 4. P&ID Features 파라미터

### 4.1 Rule Profile (4개)

#### HP-PID-001: rule_profile 선택
```gherkin
Feature: Rule Profile 선택
  Scenario Outline: 다양한 규칙 프로파일 테스트
    Given P&ID 설정 패널이 열려있음
    When rule_profile 드롭다운에서 "<profile>" 선택
    And "Run Check" 클릭
    Then "<profile>" 프로파일의 규칙이 적용됨

  Examples:
    | profile   | rules_count | specialty          |
    | default   | 20          | 일반 P&ID          |
    | bwms      | 60          | 선박평형수처리     |
    | chemical  | 35          | 화학 플랜트        |
    | oil_gas   | 45          | 석유/가스          |
```

### 4.2 Severity Threshold (4개)

#### HP-PID-002: severity_threshold 선택
```gherkin
Feature: Severity Threshold
  Scenario Outline: 심각도 임계값 필터링
    Given P&ID 편차 분석 화면에 있음
    When severity_threshold 드롭다운에서 "<threshold>" 선택
    And "Analyze" 클릭
    Then "<threshold>" 이상 심각도만 표시됨

  Examples:
    | threshold | shows                    |
    | info      | info, low, medium, high, critical |
    | low       | low, medium, high, critical       |
    | medium    | medium, high, critical            |
    | high      | high, critical                    |
    | critical  | critical                          |
```

### 4.3 Analysis Types (4개)

#### HP-PID-003: analysis_types 다중 선택
```gherkin
Feature: Analysis Types 다중 선택
  Scenario: 여러 분석 타입 동시 선택
    Given P&ID 편차 분석 화면에 있음
    When analysis_types에서 다음 선택:
      - connectivity
      - symbol_validation
      - labeling
    And "Analyze" 클릭
    Then 선택된 3가지 타입의 분석 수행됨

  Available Types:
    - connectivity: 연결성 검증
    - symbol_validation: 심볼 검증
    - labeling: 라벨링 검증
    - line_numbering: 라인 번호 검증
    - instrument_check: 계기 검증
    - bwms_specific: BWMS 전용 검증
```

### 4.4 Standards (4개)

#### HP-PID-004: standards 다중 선택
```gherkin
Feature: Standards 다중 선택
  Scenario: 여러 표준 동시 적용
    Given P&ID 편차 분석 화면에 있음
    When standards에서 다음 선택:
      - ISO 10628
      - ISA 5.1
    And "Analyze" 클릭
    Then 두 표준 모두 적용하여 분석됨

  Available Standards:
    - ISO 10628: P&ID 표준
    - ISA 5.1: 계기 심볼 표준
    - ANSI/ISA S5.1: 미국 계기 표준
    - BS 5070: 영국 표준
    - DIN 28004: 독일 표준
    - BWMS: TECHCROSS BWMS 규정
```

---

## 5. Export 파라미터

### 5.1 Export Format (6개)

#### HP-EXP-001: export_type Excel
```gherkin
Feature: Excel 내보내기
  Scenario: Excel 형식으로 내보내기
    Given BOM 또는 워크플로우 결과가 있음
    When export_type 드롭다운에서 "excel" 선택
    And "Export" 클릭
    Then .xlsx 파일 다운로드됨
    And 서식이 적용됨

  Excel Features:
    - 헤더 스타일링
    - 열 너비 자동 조정
    - 필터 활성화
    - 색상 코딩
```

#### HP-EXP-002: export_type CSV
```gherkin
Feature: CSV 내보내기
  Scenario: CSV 형식으로 내보내기
    Given BOM 결과가 있음
    When export_type 드롭다운에서 "csv" 선택
    And "Export" 클릭
    Then .csv 파일 다운로드됨
    And UTF-8 인코딩 적용됨
```

#### HP-EXP-003: export_type JSON
```gherkin
Feature: JSON 내보내기
  Scenario: JSON 형식으로 내보내기
    Given BOM 결과가 있음
    When export_type 드롭다운에서 "json" 선택
    And "Export" 클릭
    Then .json 파일 다운로드됨
    And 구조화된 데이터 포함됨
```

#### HP-EXP-004: export_type PDF
```gherkin
Feature: PDF 내보내기
  Scenario: PDF 형식으로 내보내기
    Given BOM 결과가 있음
    When export_type 드롭다운에서 "pdf" 선택
    And "Export" 클릭
    Then .pdf 파일 다운로드됨
    And 보고서 형식으로 포맷됨

  PDF Features:
    - 회사 로고
    - 페이지 번호
    - 테이블 서식
    - 차트/이미지 포함
```

### 5.2 Export Options (4개)

#### HP-EXP-005: include_rejected 옵션
```gherkin
Feature: 거부 항목 포함
  Scenario: 거부된 항목도 내보내기에 포함
    Given BOM 결과에 거부된 항목이 있음
    When include_rejected 체크박스 활성화
    And "Export" 클릭
    Then 거부된 항목도 파일에 포함됨
    And "Rejected" 상태로 표시됨

  Default: false
```

#### HP-EXP-006: include_low_confidence 옵션
```gherkin
Feature: 낮은 신뢰도 포함
  Scenario: 낮은 신뢰도 항목 내보내기 포함
    Given BOM 결과에 낮은 신뢰도 항목이 있음
    When include_low_confidence 체크박스 활성화
    And confidence_threshold를 0.3으로 설정
    And "Export" 클릭
    Then 0.3 이하 신뢰도 항목도 포함됨

  Default: false
```

#### HP-EXP-007: project_metadata 설정
```gherkin
Feature: 프로젝트 메타데이터
  Scenario: 내보내기에 메타데이터 포함
    Given BOM 결과가 있음
    When project_metadata 섹션 확장
    And 다음 정보 입력:
      - project_name: "BWMS Project A"
      - drawing_number: "PID-001-R3"
      - revision: "3"
      - engineer: "홍길동"
    And "Export" 클릭
    Then 내보내기 파일에 메타데이터 포함됨
```

---

## 6. 파라미터 지속성

### 6.1 세션 간 지속성 (4개)

#### HP-PER-001: 파라미터 자동 저장
```gherkin
Feature: 파라미터 자동 저장
  Scenario: 변경된 파라미터 자동 저장
    Given 검출 설정 패널이 열려있음
    When confidence를 0.5로 변경
    And imgsz를 2048로 변경
    And 다른 페이지로 이동
    And 다시 검출 설정 패널 열기
    Then confidence가 0.5로 유지됨
    And imgsz가 2048로 유지됨

  Storage: localStorage
```

#### HP-PER-002: 세션별 파라미터 저장
```gherkin
Feature: 세션별 파라미터
  Scenario: 세션에 파라미터 저장
    Given 세션 A에서 confidence=0.3 설정
    And 세션 B에서 confidence=0.7 설정
    When 세션 A 다시 열기
    Then confidence가 0.3으로 표시됨
    When 세션 B 다시 열기
    Then confidence가 0.7으로 표시됨

  Storage: API - session.settings
```

#### HP-PER-003: 기본값으로 재설정
```gherkin
Feature: 기본값 재설정
  Scenario: 파라미터 기본값 복원
    Given 여러 파라미터가 변경된 상태
    When "Reset to Defaults" 버튼 클릭
    Then 확인 다이얼로그 표시됨
    When "확인" 클릭
    Then 모든 파라미터가 기본값으로 복원됨

  Default Values:
    - confidence: 0.25
    - iou_threshold: 0.45
    - imgsz: 1024
    - model_type: engineering
```

#### HP-PER-004: 프리셋 저장/로드
```gherkin
Feature: 파라미터 프리셋
  Scenario: 파라미터 프리셋 저장 및 로드
    Given 파라미터가 최적화된 상태
    When "Save as Preset" 클릭
    And 프리셋 이름 "High Precision" 입력
    And "저장" 클릭
    Then 프리셋이 저장됨
    When 다음에 프리셋 드롭다운에서 "High Precision" 선택
    Then 저장된 파라미터가 모두 로드됨
```

---

## 7. 파라미터 조합 테스트

### 7.1 최적 조합 (4개)

#### HP-COMBO-001: 빠른 스캔 조합
```gherkin
Feature: 빠른 스캔 최적화
  Scenario: 빠른 검출을 위한 파라미터 조합
    Given 검출 설정 패널이 열려있음
    When 다음 파라미터 설정:
      - confidence: 0.15
      - iou_threshold: 0.30
      - imgsz: 640
      - model_id: yolov11n
    And "Run Detection" 클릭
    Then 검출이 1초 이내 완료됨

  Use Case: 빠른 미리보기
```

#### HP-COMBO-002: 균형 조합
```gherkin
Feature: 균형 최적화
  Scenario: 속도와 정확도 균형 파라미터
    Given 검출 설정 패널이 열려있음
    When 다음 파라미터 설정:
      - confidence: 0.25
      - iou_threshold: 0.45
      - imgsz: 1024
      - model_id: yolov11s
    And "Run Detection" 클릭
    Then 검출이 3초 이내 완료됨
    And 적절한 정확도 달성됨

  Use Case: 일반 사용
```

#### HP-COMBO-003: 정밀 조합
```gherkin
Feature: 정밀 최적화
  Scenario: 높은 정확도를 위한 파라미터
    Given 검출 설정 패널이 열려있음
    When 다음 파라미터 설정:
      - confidence: 0.50
      - iou_threshold: 0.60
      - imgsz: 2048
      - model_id: yolov11m
    And "Run Detection" 클릭
    Then 작은 심볼도 정확히 검출됨
    And 오검출이 최소화됨

  Use Case: 최종 검증
```

#### HP-COMBO-004: BWMS 전용 조합
```gherkin
Feature: BWMS 최적화
  Scenario: BWMS P&ID 분석 최적 파라미터
    Given P&ID 설정 패널이 열려있음
    When 다음 파라미터 설정:
      - model_type: pid_class_aware
      - confidence: 0.20
      - rule_profile: bwms
      - standards: BWMS
      - analysis_types: all
    And "Run Full Analysis" 클릭
    Then BWMS 전용 심볼이 검출됨
    And BWMS 규칙 기반 검증 수행됨

  Use Case: TECHCROSS 워크플로우
```

---

## 8. 테스트 자동화 상태

| 시나리오 그룹 | 자동화 | 우선순위 |
|--------------|--------|----------|
| Detection 파라미터 | 50% | P0 |
| OCR 파라미터 | 30% | P1 |
| Analysis 파라미터 | 20% | P1 |
| P&ID 파라미터 | 40% | P1 |
| Export 파라미터 | 50% | P1 |
| 파라미터 지속성 | 25% | P2 |
| 조합 테스트 | 10% | P2 |

---

## 9. 관련 문서

- [01-api-endpoints.md](./01-api-endpoints.md) - API 파라미터 스키마
- [02-ui-interactions.md](./02-ui-interactions.md) - UI 컨트롤 테스트
- [06-integration.md](./06-integration.md) - 파라미터 통합 테스트
