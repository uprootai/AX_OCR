# TECHCROSS BWMS P&ID 분석 - 미구현 기능 평가

> 작성일: 2025-12-25
> 목적: AX POC 시스템에서 TECHCROSS 요구사항 대비 미구현 기능 상세 분석

---

## 1. 평가 개요

### 분석 대상 파일
| 컴포넌트 | 파일 경로 | 분석 결과 |
|----------|----------|----------|
| PID Analyzer | `models/pid-analyzer-api/api_server.py` (1033줄) | 일반 기능 구현됨 |
| Design Checker | `models/design-checker-api/api_server.py` (824줄) | **BWMS 규칙 없음** |
| Line Detector | `models/line-detector-api/api_server.py` (1007줄) | 완전 구현됨 |
| YOLO-PID | `models/yolo-pid-api/api_server.py` (555줄) | 30개 일반 클래스 |
| OCR Ensemble | `models/ocr-ensemble-api/api_server.py` (649줄) | 완전 구현됨 |
| YOLO 모델 | `models/yolo-api/models/model_registry.yaml` | **BWMS 장비 없음** |

---

## 2. 핵심 미구현 기능 (Critical Gap)

### 2.1 BWMS 전용 장비 심볼 인식 - **미구현**

**현재 상태:**
```yaml
# pid_symbol 모델 클래스 (30종)
- Agitator, Ball valve, Centrifugal pump
- Control valve, Exchanger, Gate Valve
- Globe Valve, Pump, Separator, Valve...
```

**TECHCROSS 필수 장비 (미인식):**
| 장비 코드 | 장비명 | 기능 | 인식 여부 |
|-----------|--------|------|----------|
| ECU | Electrolyzer Cell Unit | 전기분해 유닛 | ❌ |
| HGU | Hydrogen Gas Unit | 수소가스 처리 | ❌ |
| DMU | Direct Mix Unit | 직접 혼합 유닛 | ❌ |
| ANU | Active Neutralization Unit | 중화 유닛 | ❌ |
| NIU | Neutralization Injection Unit | 중화 주입 유닛 | ❌ |
| TSU | Total residual Solution Unit | 잔류 용액 유닛 | ❌ |
| DTS | Dosing TRO Station | TRO 투여 스테이션 | ❌ |
| FMU | Filter Module Unit | 필터 모듈 | ❌ |
| GDS | Gas Dilution System | 가스 희석 시스템 | ❌ |
| EWU | Electrolyte Washing Unit | 전해질 세척 유닛 | ❌ |
| APU | Automatic Purge Unit | 자동 퍼지 유닛 | ❌ |

**개발 필요사항:**
1. BWMS 전용 심볼 데이터셋 구축 (샘플 P&ID에서 추출)
2. YOLO 모델 클래스 확장 또는 별도 모델 훈련
3. 장비 태그 패턴 인식 (예: `ECU-001`, `HGU-002`)

---

### 2.2 TECHCROSS 설계 규칙 검증 - **미구현**

**현재 Design Checker 규칙 (17개):**
```python
DESIGN_RULES = {
    "CONN-001": "끊어진 라인 검출",
    "CONN-002": "미연결 심볼",
    "SYM-002": "심볼 중첩",
    "LBL-001": "태그번호 누락",
    "SAF-001": "안전밸브 누락",
    # ... 일반 P&ID 규칙만 있음
}
```

**TECHCROSS 필수 규칙 (미구현):**

| 규칙 ID | 규칙 내용 | 우선순위 | 구현 난이도 |
|---------|----------|----------|------------|
| BWMS-001 | G-2 Sampling Port는 반드시 상류(upstream)에 위치 | 🔴 Critical | 중 |
| BWMS-002 | TSU와 APU 간 거리 ≥ 5m, 높이차 ≥ 2m | 🔴 Critical | 상 |
| BWMS-003 | ANU/NIU Injection Port 거리 ≥ 10m | 🔴 Critical | 상 |
| BWMS-004 | FMU는 반드시 ECU 후단에 위치 | 🔴 Critical | 중 |
| BWMS-005 | GDS는 반드시 ECU/HGU 상부에 위치 | 🔴 Critical | 중 |
| BWMS-006 | 포트 간 최소 거리 MIN 5D (파이프 직경의 5배) | 🔴 Critical | 상 |
| BWMS-007 | Mixing Pump 용량 = 밸러스트 펌프 용량 × 4.3% | 🟡 Important | 상 |
| BWMS-008 | 직접전기분해(ECS) 시스템 밸브 위치 검증 | 🟡 Important | 중 |
| BWMS-009 | 간접전기분해(HYCHLOR) 필터 위치 검증 | 🟡 Important | 중 |

**개발 필요사항:**
1. 심볼 위치 관계 분석 로직 (upstream/downstream 판단)
2. 거리 계산 알고리즘 (P&ID 스케일 고려)
3. 규칙 엔진 프레임워크 확장

---

### 2.3 라인 번호/파이프 스펙 추출 - **부분 구현**

**현재 상태:**
- Line Detector: 라인 검출 ✅, 색상 분류 ✅, 스타일 분류 ✅
- OCR: 텍스트 인식 ✅

**미구현 기능:**
| 기능 | 설명 | 구현 상태 |
|------|------|----------|
| 라인 번호 패턴 파싱 | `2"-PSA-1001-E-L-1A` 형식 분해 | ❌ |
| 파이프 재질 추출 | SS316L, CPVC, PE 등 | ❌ |
| 압력/온도 등급 | Class 150, PN10 등 | ❌ |
| 라인과 텍스트 연결 | 인접 OCR 결과를 라인에 매핑 | ❌ |

**라인 번호 패턴 예시:**
```
2"-PSA-1001-E-L-1A
│  │    │   │ │ │
│  │    │   │ │ └── 시퀀스
│  │    │   │ └──── 라인 타입 (L=Liquid)
│  │    │   └────── 재질 (E=?)
│  │    └────────── 라인 번호
│  └─────────────── 서비스 코드 (PSA=Process Sea water A)
└────────────────── 파이프 사이즈 (2인치)
```

---

### 2.4 BWMS 체크리스트 자동화 - **미구현**

**TECHCROSS 체크리스트 항목 (60여개):**
```
Category: 설계 검토
□ ECU 용량이 선박 밸러스트 용량에 적합한가?
□ HGU가 올바른 위치에 설치되어 있는가?
□ 모든 안전 밸브가 표시되어 있는가?
□ 비상 차단 밸브 위치가 적절한가?
...

Category: 배관 검토
□ G-2 샘플링 포트가 상류에 있는가?
□ 최소 5D 거리가 확보되었는가?
□ 라인 재질이 해수에 적합한가?
...
```

**개발 필요사항:**
1. 체크리스트 항목 → 검증 규칙 매핑
2. 자동 검증 결과 → 체크리스트 UI 연동
3. 수동 검토 항목 플래그 처리

---

## 3. 기존 구현 기능 상태

### 3.1 완전 구현됨 (사용 가능)

| 기능 | 컴포넌트 | 상태 | TECHCROSS 활용 |
|------|----------|------|---------------|
| P&ID 심볼 검출 | YOLO-PID | ✅ | 일반 심볼 검출 가능 |
| 라인 검출 | Line Detector | ✅ | 배관 경로 추출 가능 |
| OCR | OCR Ensemble | ✅ | 텍스트 인식 가능 |
| 심볼 연결 분석 | PID Analyzer | ✅ | 연결 관계 파악 가능 |
| 일반 설계 규칙 | Design Checker | ✅ | 기본 검증 가능 |

### 3.2 부분 구현 (확장 필요)

| 기능 | 현재 상태 | 필요한 확장 |
|------|----------|------------|
| BOM 생성 | 일반 BOM ✅ | BWMS 장비 카테고리 추가 |
| 밸브 리스트 | 일반 밸브 ✅ | BWMS 밸브 태그 패턴 |
| 장비 리스트 | 일반 장비 ✅ | BWMS 장비 분류 (ECU/HGU 등) |
| 계기 검출 | OCR 기반 ✅ | BWMS 계기 패턴 (TI, FI, LI) |

---

## 4. 개발 우선순위 제안

### Phase 1: 필수 기능 (1-2주)
1. **BWMS 장비 태그 패턴 인식**
   - OCR 결과에서 ECU/HGU/DMU 등 태그 추출
   - 정규식 기반 패턴 매칭
   - 난이도: ⭐⭐

2. **기본 위치 규칙 검증**
   - upstream/downstream 관계 판단
   - 심볼 간 상대 위치 계산
   - 난이도: ⭐⭐⭐

### Phase 2: 핵심 기능 (2-3주)
3. **TECHCROSS 설계 규칙 구현**
   - BWMS-001 ~ BWMS-005 규칙 구현
   - Design Checker 규칙 엔진 확장
   - 난이도: ⭐⭐⭐⭐

4. **라인 번호 파싱**
   - 라인 번호 → 속성 분해
   - 라인-심볼 연결
   - 난이도: ⭐⭐⭐

### Phase 3: 고급 기능 (3-4주)
5. **거리 계산 알고리즘**
   - P&ID 스케일 자동 감지
   - 심볼 간 실제 거리 계산
   - 난이도: ⭐⭐⭐⭐⭐

6. **BWMS 전용 YOLO 모델**
   - 샘플 P&ID에서 학습 데이터 추출
   - 모델 훈련 (최소 200-500장)
   - 난이도: ⭐⭐⭐⭐⭐

---

## 5. 기술적 구현 방안

### 5.1 BWMS 장비 인식 (OCR 기반)

```python
# PID Analyzer에 추가할 BWMS 장비 패턴
BWMS_EQUIPMENT_PATTERNS = {
    'ECU': r'ECU[-_]?\d{3}',      # ECU-001, ECU001
    'HGU': r'HGU[-_]?\d{3}',
    'DMU': r'DMU[-_]?\d{3}',
    'ANU': r'ANU[-_]?\d{3}',
    'NIU': r'NIU[-_]?\d{3}',
    'TSU': r'TSU[-_]?\d{3}',
    'DTS': r'DTS[-_]?\d{3}',
    'FMU': r'FMU[-_]?\d{3}',
    'GDS': r'GDS[-_]?\d{3}',
    'EWU': r'EWU[-_]?\d{3}',
    'APU': r'APU[-_]?\d{3}',
}

def detect_bwms_equipment(ocr_texts: List[str]) -> List[Dict]:
    """BWMS 장비 태그 검출"""
    equipment = []
    for text in ocr_texts:
        for equip_type, pattern in BWMS_EQUIPMENT_PATTERNS.items():
            if re.match(pattern, text, re.IGNORECASE):
                equipment.append({
                    'tag': text,
                    'type': equip_type,
                    'description': BWMS_EQUIPMENT_DESC[equip_type]
                })
    return equipment
```

### 5.2 설계 규칙 검증 프레임워크

```python
# Design Checker에 추가할 BWMS 규칙
BWMS_DESIGN_RULES = {
    "BWMS-001": {
        "name": "G-2 Sampling Port Upstream",
        "description": "G-2 Sampling Port는 반드시 상류에 위치해야 함",
        "severity": "critical",
        "checker": check_g2_upstream,
    },
    "BWMS-004": {
        "name": "FMU After ECU",
        "description": "FMU는 반드시 ECU 후단에 위치해야 함",
        "severity": "critical",
        "checker": check_fmu_after_ecu,
    },
    # ...
}

def check_fmu_after_ecu(connections: Dict, symbols: List) -> Dict:
    """FMU가 ECU 다음에 위치하는지 검증"""
    ecu_symbols = [s for s in symbols if 'ECU' in s.get('tag', '')]
    fmu_symbols = [s for s in symbols if 'FMU' in s.get('tag', '')]

    for ecu in ecu_symbols:
        for fmu in fmu_symbols:
            # 연결 경로에서 ECU → FMU 순서 확인
            if not is_downstream(connections, ecu, fmu):
                return {
                    "passed": False,
                    "message": f"{fmu['tag']}가 {ecu['tag']} 후단에 위치하지 않음"
                }
    return {"passed": True}
```

---

## 6. 샘플 P&ID 테스트 계획

### 사용 가능한 테스트 파일
| 파일명 | 시스템 | 용도 |
|--------|--------|------|
| `[PNID] REV.0 YZJ2023-1584_1585_NK_ECS1000Bx1_MIX.pdf` | ECS (직접전기분해) | 장비 인식 테스트 |
| `[PNID] Rev.0 H1993A...HYCHLOR 2.0-3000 2SETS_LR.pdf` | HYCHLOR (간접전기분해) | 필터 위치 테스트 |

### 테스트 시나리오
1. **심볼 검출 테스트**: 현재 YOLO로 검출 가능한 심볼 확인
2. **OCR 테스트**: ECU/HGU 등 태그 인식 가능 여부
3. **라인 검출 테스트**: 배관 경로 추출
4. **연결 분석 테스트**: 심볼 간 연결 관계 파악

---

## 7. 결론

### 핵심 Gap 요약

| 영역 | 현재 상태 | 필요 개발 | 영향도 |
|------|----------|----------|--------|
| BWMS 장비 인식 | ❌ 없음 | YOLO 확장 또는 OCR 패턴 | 🔴 High |
| TECHCROSS 규칙 | ❌ 없음 | 9개 규칙 구현 | 🔴 High |
| 라인 번호 파싱 | ❌ 없음 | 정규식 파서 | 🟡 Medium |
| 체크리스트 자동화 | ❌ 없음 | UI 연동 | 🟡 Medium |
| 거리 계산 | ❌ 없음 | 스케일 알고리즘 | 🟡 Medium |

### 즉시 시작 가능한 작업
1. OCR 결과에서 BWMS 장비 태그 패턴 추출 (정규식)
2. Design Checker에 기본 BWMS 규칙 프레임워크 추가
3. 샘플 P&ID로 현재 시스템 테스트

### 중장기 개발 필요
1. BWMS 전용 YOLO 모델 훈련 (데이터셋 구축 필요)
2. P&ID 스케일 기반 거리 계산 알고리즘
3. 60여개 체크리스트 자동화 시스템

---

**문서 작성자**: Claude AI
**최종 업데이트**: 2025-12-25
