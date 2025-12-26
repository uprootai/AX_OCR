# TECHCROSS P&ID 도면 검토 AI - AX POC 개발 계획

> **작성일**: 2025.12.25
> **목적**: TECHCROSS 기본설계팀 요구사항을 AX POC BlueprintFlow로 구현하기 위한 개발 계획

---

## 1. P&ID 이미지 특성 분석

### 1.1 도면 구조 (공통)

```
P&ID 도면 구성
├── Components List (장비 목록 + 연결 사이즈)
├── Symbol Legend (심볼 범례)
├── History (개정 이력)
├── NOTE OF P&ID (설계 노트/규정)
├── P&ID 본문 (운전 모드별 다이어그램)
│   ├── Ballasting Operation
│   ├── De-Ballasting Operation
│   ├── Mixing Operation
│   └── Stripping Operation
└── Sampling Detail Drawing (상세도)
```

### 1.2 ECS 시스템 특성

| 항목 | 내용 |
|------|------|
| **방식** | 직접 전기분해 (필터 없음) |
| **복잡도** | 중간 |
| **주요 장비** | ECU, PRU, ANU, TSU-S, APU, FMU, CSU, GDS, EWU, T-STR, PCU, FCV |
| **심볼 수** | 약 40종 |
| **라인 유형** | Ballast Water, TSU Sampling, ANU Dosing |
| **특수 표시** | SIGNAL FOR BWMS, N.O, N.C, *(Maker Supply), H(Hydraulic) |

### 1.3 HYCHLOR 2.0 시스템 특성

| 항목 | 내용 |
|------|------|
| **방식** | 간접 전기분해 + 필터 (Side Stream) |
| **복잡도** | 높음 |
| **주요 장비** | MCP, MPC, MCC, HGU, PRM, DMU, FP, IFP, NIU, DTS, DTU, CIP, CPP, SWH, AC01V/AC02V + ECS 장비 |
| **심볼 수** | 약 50종 (추가: PT, CI, FS, GS, AV, Blower, Hopper, CPVC/PE Coating) |
| **라인 유형** | + PE Coating, CPVC Pipe, Degas 라인 |
| **특수 표시** | + Hazardous Area (3m/5m), Class Piping |

### 1.4 검출 대상 심볼 목록

#### 밸브류 (Valves)
| 심볼 | 명칭 | 검출 우선순위 |
|------|------|:------------:|
| ◁▷ | Butterfly Valve | ⭐⭐⭐ |
| ⊠◁▷ | Remote Butterfly Valve | ⭐⭐⭐ |
| ⊳| | Globe Valve | ⭐⭐⭐ |
| ⊳◇ | Check Valve | ⭐⭐⭐ |
| ⊠ | Ball Valve | ⭐⭐ |
| ◁|▷ | Diaphragm Valve | ⭐⭐ |
| ⌐▷ | Angle Valve | ⭐⭐ |
| ⊗◁▷ | Solenoid Valve | ⭐⭐⭐ |
| ⊳|▷ | Throttling Valve | ⭐⭐ |
| ⊠3 | 3-Way Cock Valve | ⭐⭐ |

#### 계기류 (Instruments)
| 심볼 | 명칭 | 검출 우선순위 |
|------|------|:------------:|
| [PI] | Pressure Indicator | ⭐⭐⭐ |
| [PS] | Pressure Switch | ⭐⭐⭐ |
| [PT] | Pressure Transmitter | ⭐⭐ |
| [TI] | Temperature Indicator | ⭐⭐⭐ |
| [TS] | Temperature Switch | ⭐⭐⭐ |
| [LS] | Level Switch | ⭐⭐ |
| [ZS] | Limit Switch | ⭐⭐⭐ |
| [FS] | Flow Switch | ⭐⭐ |
| [GS] | Gas Sensor | ⭐⭐ |
| [CI] | Compound Indicator | ⭐ |

#### 장비류 (Equipment)
| 심볼 | 명칭 | 검출 우선순위 |
|------|------|:------------:|
| ⊙M | Pump (Motor) | ⭐⭐⭐ |
| ⊠⊠ | Strainer | ⭐⭐⭐ |
| ⊠Y | Y-Strainer | ⭐⭐ |
| ⊙F | Filter | ⭐⭐ |
| ⊳⊲ | Eductor | ⭐⭐ |
| ★ | Maker (TECHCROSS) Supply | ⭐⭐⭐ |
| ⊙B | Blower | ⭐ |

#### 배관 요소 (Piping)
| 심볼 | 명칭 | 검출 우선순위 |
|------|------|:------------:|
| —|— | Closed Pipe Connection | ⭐⭐ |
| —⊕— | Branch Pipes | ⭐⭐ |
| —+— | Crossing Connected | ⭐⭐ |
| —⌒— | Crossing Not Connected | ⭐⭐ |
| ▷◁ | Reducer | ⭐⭐ |
| ⊗ | Blind Flange | ⭐ |

### 1.5 텍스트 정보 유형

| 유형 | 예시 | OCR 난이도 |
|------|------|:----------:|
| **장비 태그** | BAV1, BWV2, ECU 1000B | 중 |
| **배관 사이즈** | Ø273x9.5, 5K-350A, 10K-15A | 중 |
| **플랜지 규격** | JIS 5K, JIS 10K, JIS 16K | 중 |
| **유량/압력** | 500m³/h x 3.5bar, 2800m³/h x 35mTH | 중 |
| **상태 표시** | N.O, N.C, SIGNAL FOR BWMS | 하 |
| **거리/높이** | MIN.5D, WITHIN 600mm, 3M AROUND | 중 |
| **재질** | SUS316L, PE COATING, CPVC | 하 |
| **튜브 사이즈** | Ø6, Ø10, Ø12 | 하 |

---

## 2. AX 노드 ↔ TECHCROSS 요구사항 매핑

### 2.1 핵심 파이프라인

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    TECHCROSS P&ID 분석 파이프라인                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────┐    ┌─────────────┐    ┌──────────────┐                   │
│  │ PDF/DWG  │───▶│   ESRGAN    │───▶│    YOLO      │                   │
│  │  입력    │    │  (선택적)    │    │ (pid_symbol) │                   │
│  └──────────┘    └─────────────┘    └──────┬───────┘                   │
│                                            │                            │
│                                            ▼                            │
│  ┌──────────────┐    ┌─────────────────────────────────┐               │
│  │ Line Detector │───▶│        PID Analyzer             │               │
│  │  (배관/신호)  │    │  • Valve Signal List 생성       │               │
│  └──────────────┘    │  • Equipment List 생성          │               │
│                      │  • 연결성 분석 (Graph)          │               │
│                      └─────────────┬───────────────────┘               │
│                                    │                                    │
│                                    ▼                                    │
│  ┌──────────────┐    ┌─────────────────────────────────┐               │
│  │ OCR Ensemble │───▶│      Design Checker             │               │
│  │ (태그/사이즈) │    │  • 체크리스트 자동 검토         │               │
│  └──────────────┘    │  • Deviation List 생성          │               │
│                      │  • 규정 위반 사항 식별          │               │
│                      └─────────────────────────────────┘               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 요구사항별 노드 매핑

| TECHCROSS 요구사항 | AX 노드 | 현재 상태 | 필요 작업 |
|-------------------|---------|:--------:|----------|
| **P&ID 인식** | YOLO (pid_symbol) | ✅ 60종 | BWMS 전용 심볼 추가 학습 |
| **형상 기반 심볼 검출** | YOLO + SAHI | ✅ 구현됨 | 고해상도 도면 최적화 |
| **장비 위치 파악** | PID Analyzer | ✅ 구현됨 | 상대 위치 규칙 추가 |
| **Valve Signal List** | PID Analyzer | ✅ 구현됨 | SIGNAL FOR BWMS 필터 추가 |
| **Equipment List** | PID Analyzer | ✅ 구현됨 | *(Maker Supply) 필터 추가 |
| **Deviation List** | Design Checker | 🔄 개발중 | TECHCROSS 표준 규칙 추가 |
| **체크리스트 검토** | Design Checker | 🔄 개발중 | BWMS 체크리스트 룰 구현 |
| **배관 라인 검출** | Line Detector | ✅ 구현됨 | 색상별 분류 개선 |
| **텍스트 추출** | OCR Ensemble | ✅ 구현됨 | 도면 특화 후처리 |
| **멀티모달 질의응답** | VL Model | ✅ 구현됨 | P&ID 전용 프롬프트 |

### 2.3 신규 개발 필요 항목

#### 2.3.1 YOLO 모델 확장 (pid_symbol)
```yaml
추가 학습 클래스:
  # BWMS 전용 장비
  - ECU (Electro Chamber Unit)
  - HGU (Hypochlorite Generation Unit)
  - DMU (Degas Module Unit)
  - ANU/NIU (Neutralization Unit)
  - TSU/DTS (TRO Sensor Unit)
  - FMU (Flow Meter Unit)
  - GDS (Gas Detection Sensor)
  - EWU (EM Washing Unit)

  # 특수 표시
  - SIGNAL_FOR_BWMS (신호 밸브 표시)
  - MAKER_SUPPLY (★ 표시)
  - N.O_N.C (상시 열림/닫힘)
```

#### 2.3.2 Design Checker 규칙 추가
```yaml
TECHCROSS 설계 규칙:
  # G-2 Sampling Port
  - rule: G2_SAMPLING_POSITION
    condition: "G-2 Sampling Port must be upstream of vertical pipe"
    severity: error

  # TSU/DTS 위치
  - rule: TSU_APU_DISTANCE
    condition: "TSU와 APU 사이 거리 5m 이내, 높이 2m 이내"
    severity: warning

  # ANU/NIU 위치
  - rule: ANU_INJECTION_DISTANCE
    condition: "ANU/NIU Injection Port 10m 이내"
    severity: warning

  # 거리 규정
  - rule: MIN_5D_DISTANCE
    condition: "TSU Port와 ANU Port 간 최소 5D 거리"
    severity: error

  # FMU 위치
  - rule: FMU_ECU_POSITION
    condition: "FMU가 ECU 후단에 위치"
    severity: error

  # GDS 위치
  - rule: GDS_ABOVE_ECU
    condition: "GDS가 ECU/HGU 상부에 위치"
    severity: error
```

---

## 3. 개발 로드맵

### Phase 1: POC 기반 구축 (1-2주)

```
목표: 기본 파이프라인 동작 확인
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[ ] YOLO pid_symbol 모델로 샘플 P&ID 테스트
[ ] Line Detector로 배관 라인 검출 테스트
[ ] PID Analyzer 연결성 분석 테스트
[ ] OCR Ensemble로 태그/사이즈 추출 테스트
[ ] BlueprintFlow 세션 구성 및 저장
```

#### 테스트 대상 파일
- `[PNID] REV.0 YZJ2023-1584_1585_NK_ECS1000Bx1_MIX.pdf` (ECS)
- `[PNID] Rev.0 H1993A_4A_5A_6A_7A_8A_HYCHLOR 2.0-3000 2SETS_LR.pdf` (HYCHLOR)

### Phase 2: BWMS 전용 모델 학습 (3-4주)

```
목표: TECHCROSS P&ID 특화 모델 개발
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[ ] BWMS 장비 심볼 라벨링 (ECU, HGU, DMU 등)
[ ] YOLO 추가 학습 데이터셋 구축
[ ] 모델 재학습 및 평가
[ ] SIGNAL FOR BWMS 밸브 검출 로직 추가
[ ] *(Maker Supply) 장비 필터링 로직 추가
```

### Phase 3: 체크리스트 자동화 (2-3주)

```
목표: 설계 검토 자동화
━━━━━━━━━━━━━━━━━━━━━━

[ ] TECHCROSS 체크리스트 Excel 분석
[ ] Design Checker에 BWMS 규칙 구현
[ ] 규칙 위반 시 시각화 (바운딩 박스 + 설명)
[ ] Deviation List 자동 생성 로직
[ ] 체크리스트 결과 리포트 출력 (Excel/PDF)
```

### Phase 4: 출력물 생성 (2주)

```
목표: 실무 활용 가능한 결과물
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[ ] Valve Signal List Excel 자동 생성
[ ] Equipment List Excel 자동 생성
[ ] 체크리스트 검토 결과 Excel 자동 생성
[ ] Deviation List Excel 자동 생성
[ ] 검토 결과 시각화 PDF 생성
```

### Phase 5: 통합 및 납품 (1-2주)

```
목표: BlueprintFlow 세션 패키징
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[ ] TECHCROSS 전용 BlueprintFlow 세션 구성
[ ] 세션 내보내기/가져오기 기능 확인
[ ] 사용자 매뉴얼 작성
[ ] 테스트 및 피드백 반영
[ ] 최종 납품 패키지 구성
```

---

## 4. BlueprintFlow 세션 구성 (예상)

### 4.1 P&ID 검토 세션

```
┌─────────────────────────────────────────────────────────────┐
│                  TECHCROSS P&ID 검토 세션                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [ImageInput] ──┬──▶ [YOLO pid_symbol] ──┐                 │
│                 │                         │                 │
│                 └──▶ [Line Detector] ────┼──▶ [PID         │
│                                          │    Analyzer]    │
│  [TextInput] ────▶ [OCR Ensemble] ───────┘       │         │
│  (프로젝트 정보)                                  │         │
│                                                   ▼         │
│                                          [Design Checker]   │
│                                                   │         │
│                                                   ▼         │
│                                           [결과 출력]       │
│                                           • 체크리스트     │
│                                           • Valve List     │
│                                           • Equipment List │
│                                           • Deviation List │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 노드 파라미터 권장값

| 노드 | 파라미터 | 권장값 | 비고 |
|------|----------|--------|------|
| YOLO | model_type | `pid_symbol` | P&ID 전용 |
| YOLO | confidence | `0.1` | 소형 심볼 검출 |
| YOLO | use_sahi | `true` | 대형 도면 필수 |
| YOLO | slice_height | `1024` | 고해상도 |
| Line Detector | method | `lsd` | 빠른 검출 |
| Line Detector | classify_colors | `true` | 라인 유형 분류 |
| OCR Ensemble | edocr2_weight | `0.5` | 한국어 도면 |
| PID Analyzer | generate_valve_list | `true` | 밸브 목록 |
| PID Analyzer | generate_equipment_list | `true` | 장비 목록 |
| Design Checker | severity_threshold | `warning` | 경고 이상 표시 |

---

## 5. 리스크 및 대응 방안

### 5.1 기술적 리스크

| 리스크 | 영향도 | 대응 방안 |
|--------|:------:|----------|
| 심볼 검출 정확도 부족 | 높음 | BWMS 전용 데이터셋 구축 및 재학습 |
| 고해상도 도면 처리 속도 | 중간 | SAHI 슬라이싱 + GPU 가속 |
| OCR 텍스트 인식 오류 | 중간 | OCR Ensemble + 후처리 교정 |
| 연결성 분석 오류 | 중간 | Human-in-the-Loop 검증 단계 추가 |
| DWG 파일 지원 | 낮음 | PDF 변환 후 처리 (LibreCAD/ODA) |

### 5.2 일정 리스크

| 리스크 | 영향도 | 대응 방안 |
|--------|:------:|----------|
| 라벨링 작업 지연 | 중간 | 우선순위 심볼만 1차 학습 |
| 체크리스트 규칙 복잡도 | 중간 | 핵심 규칙만 1차 구현 |
| 클라이언트 피드백 지연 | 낮음 | 주간 데모 및 피드백 수집 |

---

## 6. 필요 리소스

### 6.1 하드웨어

| 항목 | 최소 사양 | 권장 사양 |
|------|----------|----------|
| GPU | RTX 3060 (12GB) | RTX 4070 (12GB) 이상 |
| RAM | 32GB | 64GB |
| Storage | SSD 256GB | SSD 512GB |

### 6.2 데이터

| 항목 | 수량 | 용도 |
|------|:----:|------|
| ECS P&ID 도면 | 10+ | 학습 데이터 |
| HYCHLOR P&ID 도면 | 10+ | 학습 데이터 |
| 체크리스트 Excel | 2+ | 규칙 추출 |
| Valve Signal List | 2+ | 출력 형식 참고 |
| Equipment List | 2+ | 출력 형식 참고 |

---

## 7. 성공 기준

### 7.1 정량적 목표

| 항목 | 목표 | 측정 방법 |
|------|:----:|----------|
| 심볼 검출율 | ≥90% | 수동 검증 대비 |
| 텍스트 인식률 | ≥95% | 태그/사이즈 정확도 |
| 체크리스트 검토율 | ≥80% | 자동화 항목 비율 |
| Valve List 정확도 | ≥90% | SIGNAL FOR BWMS 밸브 |
| Equipment List 정확도 | ≥95% | Maker Supply 장비 |
| 처리 시간 | <3분 | P&ID 1장 기준 |

### 7.2 정성적 목표

- [ ] 설계자가 체크리스트 검토 시간 50% 단축
- [ ] Human Error 발생률 감소
- [ ] Deviation 사항 누락 방지
- [ ] 신입 설계자 학습 시간 단축

---

## 8. 참고 문서

| 문서 | 경로 |
|------|------|
| TECHCROSS 자료 정리 | `TECHLOSS_자료_정리.md` |
| AX POC 가이드 | `/home/uproot/ax/poc/CLAUDE.md` |
| YOLO API 스펙 | `gateway-api/api_specs/yolo.yaml` |
| PID Analyzer 스펙 | `gateway-api/api_specs/pid-analyzer.yaml` |
| Design Checker 스펙 | `gateway-api/api_specs/design-checker.yaml` |
| Line Detector 스펙 | `gateway-api/api_specs/line-detector.yaml` |
| OCR Ensemble 스펙 | `gateway-api/api_specs/ocr-ensemble.yaml` |

---

*문서 작성: Claude Code (Opus 4.5)*
*AX POC 시스템 버전: 12.0*
