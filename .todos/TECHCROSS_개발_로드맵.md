# TECHCROSS BWMS P&ID 분석 시스템 - 개발 로드맵

> 작성일: 2025-12-28
> 상태: 진행 중
> 목표: TECHCROSS BWMS(선박평형수처리장치) P&ID 도면 자동 분석 시스템

---

## 프로젝트 개요

### TECHCROSS란?
- 선박평형수처리장치(BWMS: Ballast Water Management System) 전문 기업
- P&ID 도면 검토 자동화 요청

### 최종 목표
P&ID 도면을 업로드하면 자동으로:
1. 장비(ECU, HGU, FMU 등) 인식 및 목록 생성
2. 밸브 신호 리스트 생성
3. 설계 규칙 60개 항목 자동 검증
4. 검토 결과 리포트(Excel/PDF) 출력

---

## 완료된 작업 (2025-12-28 기준)

| 작업 | 완료일 | 결과물 |
|------|--------|--------|
| Line Detector 스타일 분류 | 12/28 | 실선/점선/일점쇄선 등 6종 분류 |
| 점선 박스 영역 검출 | 12/28 | "SIGNAL FOR BWMS" 영역 자동 검출 |
| P&ID 심볼 검출 (일반) | 기존 | YOLO (model_type=pid_class_aware) |
| OCR 텍스트 인식 | 기존 | OCR Ensemble 4엔진 |
| 라인 연결 분석 | 기존 | PID Analyzer |
| 일반 설계 규칙 검증 | 기존 | Design Checker 17개 규칙 |

---

## Phase 1: 핵심 인프라 (MVP)

### 1-1. BWMS 장비 태그 패턴 인식
**파일**: `models/pid-analyzer-api/api_server.py` 확장

**무엇을 하는가?**
P&ID 도면에서 OCR로 읽은 텍스트 중에서 BWMS 전용 장비 태그를 자동 인식합니다.

**왜 필요한가?**
TECHCROSS BWMS 시스템에는 일반 P&ID에 없는 전용 장비들이 있습니다:
- ECU (Electrolyzer Cell Unit) - 전기분해 유닛
- HGU (Hydrogen Gas Unit) - 수소가스 처리 유닛
- FMU (Filter Module Unit) - 필터 모듈
- ANU (Active Neutralization Unit) - 중화 유닛
등 11종의 전용 장비

**어떻게 구현하는가?**
```python
BWMS_EQUIPMENT_PATTERNS = {
    'ECU': r'ECU[-_]?\d{3}',   # ECU-001, ECU001
    'HGU': r'HGU[-_]?\d{3}',
    'FMU': r'FMU[-_]?\d{3}',
    'ANU': r'ANU[-_]?\d{3}',
    'NIU': r'NIU[-_]?\d{3}',
    'TSU': r'TSU[-_]?\d{3}',
    'DTS': r'DTS[-_]?\d{3}',
    'GDS': r'GDS[-_]?\d{3}',
    'EWU': r'EWU[-_]?\d{3}',
    'APU': r'APU[-_]?\d{3}',
    'DMU': r'DMU[-_]?\d{3}',
}

def detect_bwms_equipment(ocr_texts):
    """OCR 결과에서 BWMS 장비 태그 추출"""
    equipment = []
    for text in ocr_texts:
        for equip_type, pattern in BWMS_EQUIPMENT_PATTERNS.items():
            if re.match(pattern, text, re.IGNORECASE):
                equipment.append({
                    'tag': text,
                    'type': equip_type,
                    'description': BWMS_DESCRIPTIONS[equip_type]
                })
    return equipment
```

**예상 작업 시간**: 2-3시간
**난이도**: ⭐⭐

---

### 1-2. Equipment List 자동 생성
**파일**: 신규 API 또는 PID Analyzer 확장

**무엇을 하는가?**
인식된 모든 장비를 Excel 파일로 출력합니다.

**출력 형식 예시**:
| No | Tag | Type | Description | Maker Supply |
|----|-----|------|-------------|--------------|
| 1 | ECU-001 | ECU | Electrolyzer Cell Unit | ✓ |
| 2 | FMU-001 | FMU | Filter Module Unit | |
| 3 | HGU-001 | HGU | Hydrogen Gas Unit | ✓ |

**왜 필요한가?**
- 도면에서 장비 목록을 수동으로 추출하는 작업이 매우 번거로움
- '*' 마크가 있는 장비는 MAKER SUPPLY (제조사 공급)으로 별도 관리 필요

**어떻게 구현하는가?**
```python
import openpyxl

def generate_equipment_list_excel(equipment_list, output_path):
    """장비 목록 Excel 파일 생성"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Equipment List"

    # 헤더
    headers = ['No', 'Tag', 'Type', 'Description', 'Maker Supply']
    ws.append(headers)

    # 데이터
    for i, equip in enumerate(equipment_list, 1):
        ws.append([
            i,
            equip['tag'],
            equip['type'],
            equip['description'],
            '✓' if equip.get('maker_supply') else ''
        ])

    wb.save(output_path)
```

**예상 작업 시간**: 3-4시간
**난이도**: ⭐⭐

---

## Phase 2: 핵심 기능

### 2-1. Valve Signal List 자동 생성
**파일**: 신규 API 또는 PID Analyzer 확장

**무엇을 하는가?**
"SIGNAL FOR BWMS" 영역 내의 밸브들을 추출하여 신호 리스트를 생성합니다.

**왜 필요한가?**
BWMS 시스템에서 제어해야 하는 밸브들의 목록이 필요합니다:
- Required: 필수 밸브 (시스템 작동에 반드시 필요)
- Alarm By-pass: 알람 우회 밸브
- PUMP: 펌프 관련 밸브
- ABNORMAL: 비정상 상태 대응 밸브

**출력 형식 예시**:
| No | Valve ID | Type | Signal Category | Description |
|----|----------|------|-----------------|-------------|
| 1 | XV-101 | Ball Valve | Required | Ballast inlet |
| 2 | XV-102 | Gate Valve | Alarm By-pass | Emergency bypass |

**구현 방법**:
1. Line Detector로 "SIGNAL FOR BWMS" 점선 영역 검출 (✅ 완료)
2. 해당 영역 내 밸브 심볼 추출
3. 밸브 ID OCR 인식
4. 카테고리 자동 분류
5. Excel 출력

**예상 작업 시간**: 4-5시간
**난이도**: ⭐⭐⭐

---

### 2-2. BWMS 설계 규칙 검증 (체크리스트 1-1)
**파일**: `models/design-checker-api/api_server.py` 확장

**무엇을 하는가?**
TECHCROSS BWMS 전용 설계 규칙 9개를 자동으로 검증합니다.

**구현할 규칙**:

| 규칙 ID | 규칙 내용 | 검증 방법 |
|---------|----------|----------|
| BWMS-001 | G-2 Sampling Port는 상류(upstream)에 위치 | 라인 흐름 방향 분석 |
| BWMS-002 | TSU와 APU 간 거리 ≥ 5m | 심볼 간 거리 계산 |
| BWMS-003 | ANU/NIU Injection Port 거리 ≥ 10m | 심볼 간 거리 계산 |
| BWMS-004 | FMU는 반드시 ECU 후단에 위치 | 연결 순서 분석 |
| BWMS-005 | GDS는 반드시 ECU/HGU 상부에 위치 | 위치 관계 분석 |
| BWMS-006 | 포트 간 최소 거리 MIN 5D | 파이프 직경 기반 계산 |
| BWMS-007 | Mixing Pump 용량 = 밸러스트 펌프 × 4.3% | 스펙 비교 |
| BWMS-008 | ECS 시스템 밸브 위치 검증 | 위치 규칙 검증 |
| BWMS-009 | HYCHLOR 필터 위치 검증 | 위치 규칙 검증 |

**구현 예시**:
```python
def check_fmu_after_ecu(connections, symbols):
    """BWMS-004: FMU가 ECU 다음에 위치하는지 검증"""
    ecu_list = [s for s in symbols if 'ECU' in s.get('tag', '')]
    fmu_list = [s for s in symbols if 'FMU' in s.get('tag', '')]

    violations = []
    for ecu in ecu_list:
        for fmu in fmu_list:
            if not is_downstream(connections, ecu, fmu):
                violations.append({
                    'rule': 'BWMS-004',
                    'message': f"{fmu['tag']}가 {ecu['tag']} 후단에 위치하지 않음",
                    'severity': 'critical'
                })
    return violations
```

**예상 작업 시간**: 1-2일
**난이도**: ⭐⭐⭐⭐

---

## Phase 3: 확장 기능

### 3-1. 체크리스트 UI (60개 항목)
**파일**: `web-ui/src/pages/` 신규 페이지

**무엇을 하는가?**
TECHCROSS 설계 검토 체크리스트 60개 항목을 웹 UI로 표시하고,
자동 검증 결과 + 수동 검토 입력을 지원합니다.

**UI 구성**:
```
┌─────────────────────────────────────────────────────┐
│ TECHCROSS BWMS 설계 검토 체크리스트                    │
├─────────────────────────────────────────────────────┤
│ 카테고리: 설계 검토                                    │
│ ┌─────────────────────────────────────────────────┐ │
│ │ □ ECU 용량이 선박 밸러스트 용량에 적합한가?      │ │
│ │   상태: [자동검증] ✅ 적합                        │ │
│ │   검토자 코멘트: ___________________________     │ │
│ ├─────────────────────────────────────────────────┤ │
│ │ □ FMU가 ECU 후단에 위치하는가?                   │ │
│ │   상태: [자동검증] ❌ 미충족 - FMU-001 위치 오류  │ │
│ │   검토자 코멘트: ___________________________     │ │
│ └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

**예상 작업 시간**: 2-3일
**난이도**: ⭐⭐⭐⭐

---

### 3-2. Deviation List (1-4)
**파일**: 신규 API

**무엇을 하는가?**
POR(구매 요청서) 대비 실제 설계의 편차 항목을 관리합니다.

**왜 필요한가?**
- 고객 요청사항(POR)과 실제 설계 간 차이점 추적
- 구매자 승인이 필요한 항목 관리

**출력 형식**:
| No | Item | POR Requirement | Actual Design | Deviation | Buyer Decision |
|----|------|-----------------|---------------|-----------|----------------|
| 1 | ECU 용량 | 500m³/h | 450m³/h | -10% | Approved |

**전제조건**: POR 원본 문서 확보 필요 (질문 14번 회신 대기)

**예상 작업 시간**: 1일
**난이도**: ⭐⭐⭐

---

### 3-3. PDF 리포트 생성
**파일**: 신규 API

**무엇을 하는가?**
모든 검토 결과를 종합한 PDF 리포트를 생성합니다.

**리포트 구성**:
1. 표지 (프로젝트 정보, 검토일, 검토자)
2. 요약 (Pass/Fail 통계)
3. Equipment List
4. Valve Signal List
5. 체크리스트 결과 (60개 항목)
6. Deviation List
7. 첨부: P&ID 이미지 + 검출 결과 오버레이

**예상 작업 시간**: 1-2일
**난이도**: ⭐⭐⭐

---

### 3-4. BWMS 전용 YOLO 모델 훈련
**파일**: `models/yolo-api/` 모델 추가 (model_type 파라미터로 전환)

**무엇을 하는가?**
BWMS 전용 장비 심볼을 이미지에서 직접 검출하는 YOLO 모델을 훈련합니다.

**왜 필요한가?**
현재는 OCR로 텍스트 태그만 인식하지만,
심볼 자체를 이미지에서 검출하면 더 정확한 위치 파악 가능

**훈련할 클래스 (11종)**:
- ECU, HGU, DMU, ANU, NIU, TSU, DTS, FMU, GDS, EWU, APU

**필요 데이터**:
- 최소 200-500장의 라벨링된 P&ID 이미지
- 각 클래스당 최소 50개 이상의 샘플

**전제조건**: 샘플 P&ID 도면 확보 및 라벨링 작업 필요

**예상 작업 시간**: 1-2주
**난이도**: ⭐⭐⭐⭐⭐

---

## 리스크 및 블로커

| 항목 | 리스크 | 대응 방안 |
|------|--------|----------|
| 체크리스트 xlsm 파일 손상 | 60개 항목 파악 불가 | 파일 재요청 (질문 1번) |
| BWMS 심볼 학습 데이터 부족 | YOLO 재학습 불가 | OCR 기반 우선 구현 |
| 거리 계산 (5m, 10m) | 스케일 정보 필요 | NOTE 영역 스케일 추출 또는 수동 입력 |
| Deviation POR 기준 | 원본 문서 없음 | 질문 14번 회신 대기 |

---

## MVP 데모 범위 (2주 내)

1. ✅ P&ID 업로드 → 심볼/텍스트 인식 (기존 기능)
2. ✅ "SIGNAL FOR BWMS" 영역 검출 (완료)
3. 🔄 BWMS 장비 태그 인식 (개발 필요)
4. 🔄 Equipment List Excel 출력 (개발 필요)
5. 🔄 Valve Signal List Excel 출력 (개발 필요)
6. 🔄 기본 설계 규칙 3개 검증 (개발 필요)

---

## 관련 문서

- [개발 우선순위](../apply-company/techloss/TECHCROSS_POC_개발_우선순위.md)
- [미구현 기능 평가](../apply-company/techloss/TECHLOSS_미구현기능_평가.md)
- [질문 목록](../apply-company/techloss/about-email-details/TECHCROSS_질문목록_이메일용.txt)

---

**작성자**: Claude AI (Opus 4.5)
**최종 업데이트**: 2025-12-28
