# ECS vs HYCHLOR 체크리스트 비교 분석

> **분석일**: 2026-01-05
> **분석 대상 파일**:
> - ECS: `(Ver.25.01) Check list_P&ID_ECS-B (2025.12.19.).xlsm`
> - HYCHLOR: `(Ver.25.01) Check list_P&ID_HYCHLOR 2.0 (2025.10.01).xlsm`

---

## 1. 핵심 수치 요약

| 구분 | ECS | HYCHLOR 2.0 | 차이 |
|------|-----|-------------|------|
| **총 체크 항목** | 80개 | 46개 | ECS +34개 |
| **카테고리 수** | 34개 | 23개 | ECS +11개 |
| **ECS 전용 카테고리** | 23개 | - | MIXING, ANU, CSU 등 |
| **HYCHLOR 전용 카테고리** | - | 12개 | HGU, DMU, CIP 등 |
| **공통 카테고리** | 11개 | 11개 | BALLAST PUMP, 선급 등 |

---

## 2. 시트(탭) 구조 비교

### ECS 시트 (5개)
1. `1. Check list` - 체크리스트 본문
2. `2. 배관 계산` - 배관 사이즈 계산
3. `3. ANU 선정표` - 중화제 주입기 선정
4. `4. PRU 발열량` - 정류기 발열량 계산
5. `5. Mixing pipe line` - 믹싱 배관 사이즈

### HYCHLOR 시트 (5개)
1. `1. Check list (25.01)` - 체크리스트 본문
2. `2. 배관 계산` - 배관 사이즈 계산
3. `3. 모델별 장비 사이즈_2` - 장비 사이즈 표
4. `a` - 보조 계산
5. `b` - 이전 버전 체크리스트 (Ver.24.00)

---

## 3. 카테고리 상세 비교

### 3.1 ECS에만 있는 카테고리 (23개)

| 카테고리 | 항목 수 | 설명 |
|----------|---------|------|
| MIXING | 13개 | 믹싱 시스템 (S.W.H.TK, 믹싱 펌프, PCU, VCU 등) |
| ANU | 3개 | 중화제 주입기 (Ammonia Neutralizing Unit) |
| PRU | 3개 | 정류기 (Power Rectifier Unit) |
| FMU | 4개 | 유량계 (Flow Meter Unit) |
| ECU | 1개 | 전기분해 챔버 (Electrolysis Chamber Unit) |
| CSU | 2개 | 염소 센서 (Chlorine Sensor Unit) |
| Ex-CSU | 1개 | 방폭 염소 센서 |
| DTS | 2개 | TRO 센서 (Dissolved TRO Sensor) |
| EX-DTS | 2개 | 방폭 TRO 센서 |
| VLS | 2개 | 밸브 신호 리스트 |
| T-STRAINER | 1개 | 스트레이너 |
| HEU | 1개 | 열교환기 (Heat Exchanger Unit) |
| FTS | 1개 | 유량 스위치 (Flow Transmitter Switch) |
| Ex-FTS | 1개 | 방폭 유량 스위치 |
| Ex-STS | 1개 | 방폭 온도 스위치 (삭제 대상) |
| GDS | 1개 | 가스 검출기 (Gas Detection System) |
| 삽입관 | 3개 | 샘플링 삽입관 |
| FCV (MAIN용) | 3개 | 메인 유량조절밸브 |
| GRAVITY 운전 | 1개 | 중력 밸러스팅 |
| DE-BALLAST시 FMU 미통과 | 1개 | 특수 케이스 |
| 선급 CRS | 1개 | CRS 선급 요구사항 |
| 선종 Tanker | 6개 | 탱커선 요구사항 |
| Ex-EWU | 1개 | 방폭 전기용접기 |

### 3.2 HYCHLOR에만 있는 카테고리 (12개)

| 카테고리 | 항목 수 | 설명 |
|----------|---------|------|
| HGU | 2개 | 염소 가스 발생기 (Hydrogen Gas Unit) |
| DMU | 2개 | 가스 분배 장치 (Distribution Manifold Unit) |
| NIU | 3개 | 중화제 주입기 (Neutralizing Injection Unit) |
| CIP | 3개 | 염소 주입점 (Chlorine Injection Point) |
| SWH | 2개 | 해수 가열기 (Sea Water Heater) |
| FMU (SIDE) | 4개 | 사이드 배관 유량계 |
| FMU (MAIN) | 2개 | 메인 배관 유량계 |
| (Ex-) DTS | 4개 | TRO 센서 (방폭/비방폭 통합) |
| SAMPLING DETAIL DRAWING | 2개 | 샘플링 상세 도면 |
| (If) GRAVITY 운전 | 1개 | 조건부 중력 밸러스팅 |
| (If) FCV (MAIN용) | 2개 | 조건부 유량조절밸브 |
| 선종 Tanker 안전구역 -> 위험구역 | 4개 | 탱커선 안전구역 요구사항 |

### 3.3 공통 카테고리 (11개)

| 카테고리 | ECS 항목 | HYCHLOR 항목 | 차이 |
|----------|----------|--------------|------|
| 기본 | 4개 | 4개 | 동일 |
| BALLAST PUMP | 4개 | 4개 | 동일 |
| EWU | 1개 | 2개 | HYCHLOR +1 |
| Retrofit Case 2 & 3 | 1개 | 1개 | 동일 |
| 선급 ABS | 4개 | 0개 | ECS만 상세 |
| 선급 DNV | 1개 | 0개 | ECS만 상세 |
| 선급 LR | 1개 | 0개 | ECS만 상세 |
| 선급 KR | 3개 | 0개 | ECS만 상세 |
| 선종 Bulker | 2개 | 1개 | ECS +1 |
| 선종 Barge | 3개 | 2개 | ECS +1 |
| 선종 LNG / LPG | 1개 | 1개 | 동일 |

---

## 4. 핵심 장비 매핑

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ECS (직접식 전기분해)           │ HYCHLOR 2.0 (간접식 전기분해)            │
├─────────────────────────────────┼───────────────────────────────────────────┤
│ ECU (전기분해 챔버)             │ HGU (염소 가스 발생기) - 유사 기능       │
│ PRU (정류기)                    │ DMU (가스 분배 장치) - 신규 장비         │
│ ANU (중화제 주입기)             │ NIU (중화제 주입기) - 유사 기능          │
│ DTS (TRO 센서)                  │ (Ex-)DTS (TRO 센서)                      │
│ FMU (유량계)                    │ FMU (SIDE) + FMU (MAIN) - 2종류로 분리   │
│ T-STRAINER (스트레이너)         │ - (없음)                                 │
│ CSU/Ex-CSU (염소센서)           │ - (없음)                                 │
│ HEU (열교환기)                  │ SWH (해수 가열기)                        │
│ FTS/Ex-FTS (유량 스위치)        │ - (없음)                                 │
│ GDS (가스 검출기)               │ - (없음)                                 │
│ VLS (밸브신호)                  │ - (없음, 간접식이라 불필요)              │
│ MIXING (믹싱 시스템)            │ - (없음)                                 │
│ 삽입관                          │ SAMPLING DETAIL DRAWING                  │
│ - (없음)                        │ CIP (염소 주입점)                        │
└─────────────────────────────────┴───────────────────────────────────────────┘
```

---

## 5. 기술적 핵심 차이점

### 5.1 전기분해 방식

| 구분 | ECS (직접식) | HYCHLOR 2.0 (간접식) |
|------|--------------|----------------------|
| **원리** | 해수를 직접 전기분해 | 소금물(Brine)을 전기분해 |
| **핵심 장비** | ECU (전기분해 챔버) | HGU (염소 가스 발생) → DMU (분배) |
| **처리 방식** | 처리수 직접 믹싱 | 염소 가스를 해수에 용해 |
| **주입점** | MIXING 시스템 | CIP (Chlorine Injection Point) |

### 5.2 안전 장비 구성

| 구분 | ECS | HYCHLOR 2.0 |
|------|-----|-------------|
| 염소 센서 | CSU (해수 내 염소 측정) | - |
| 가스 검출기 | GDS (공기 중 가스 측정) | - |
| 밸브 신호 | VLS (복잡한 밸브 신호 관리) | - (간접식이라 단순) |
| 스트레이너 | T-STRAINER 필수 | - (불필요) |

### 5.3 FMU (유량계) 구성

| 구분 | ECS | HYCHLOR 2.0 |
|------|-----|-------------|
| 구성 | FMU 단일 구성 | FMU (SIDE) + FMU (MAIN) |
| 체크 항목 | 4개 | 6개 (SIDE 4개 + MAIN 2개) |
| 위치 | ECU 후단 | HGU 후단 (SIDE), 메인 배관 (MAIN) |

### 5.4 보조 시트 차이

| ECS 시트 | HYCHLOR 시트 | 비고 |
|----------|--------------|------|
| ANU 선정표 | 모델별 장비 사이즈_2 | 다른 계산 목적 |
| PRU 발열량 | - | ECS 전용 |
| Mixing pipe line | - | ECS 전용 |

---

## 6. 체크리스트 항목 상세

### 6.1 ECS 주요 항목 (카테고리별)

#### 기본 (4개)
1. 도면 양식(51-Q-02-08) 최신 적용, 도번(TPDXX) 확인
2. ECS Components list 사양 확인 (ECU, FMU 등)
3. 장비 설치 위치 확인 (ENGINE RM, PUMP RM 등)
4. 재고 사용 가능 여부 확인 (FMU, T-STRAINER, FCV 등)

#### BALLAST PUMP (4개)
1. Ballast pump 용량 및 운전 조건 확인
2. Ballast pump 후단 Check valve, Manual valve 확인
3. Ballast pump Head 값 확인 (2바 이하 시 특별 조치)
4. A.P.Tank 주배수 펌프 확인

#### MIXING (13개)
1. S.W.H.TK 필요 CAPA 계산
2. Mixing pump 사양 선정 (Ballast pump capa 기준)
3. Mixing pipe line 사이즈 확인
4. Mixing pump Air ejector 위치
5. S.W.H.TK Main line By-pass valve 신호 구성
6. Mixing point 후단 CSU 위치
7. PCU 도면 표현
8. VCU 미적용 확인
9. FCV 메이커 HKC 적용
10. Mixing point와 FMU 설치 위치
11. Mixing pump 표준 외 사양 시 재확인
12. MIXING POINT와 CSU 거리 (MIN. 3M)
13. SUBMERSIBLE MIXING PUMP 시 PI 삭제

### 6.2 HYCHLOR 주요 항목 (카테고리별)

#### 기본 (4개)
1. 도번(TPDxxx) 해당 년도 정확히 기입
2. ECS COMPONENTS LIST 확인
3. 장비 설치 위치 확인
4. 재고 및 사용 가능 여부 확인 (FMU, FCV)

#### HGU (2개)
1. AC01V ↔ HGU ↔ DMU ↔ FMU 사이즈 및 PE CLASS 확인
2. HGU ↔ DMU "CLASS PIPING" 명기 (1급관)

#### DMU (2개)
1. DMU AIR VENT OUTLET 5M 표기
2. SPARK ARRESTOR 기입

#### CIP (3개)
1. CIP, ORIFICE 사이즈 기입
2. CIP 사이즈와 MAIN 배관 사이즈 형식승인 기준 확인
3. CIP와 DTS PORT 설치 위치 확인

---

## 7. 개발 시사점

### 7.1 체크리스트 템플릿 분리 필요

- **ECS용 템플릿**: 80개 항목, 34개 카테고리
- **HYCHLOR용 템플릿**: 46개 항목, 23개 카테고리
- **공통 템플릿**: 11개 카테고리 (기본, BALLAST PUMP, 선급, 선종 등)

### 7.2 장비 매핑 테이블 구축

P&ID 심볼 인식 시 제품군 자동 판별 가능:

| 심볼 감지 | 제품군 판별 |
|-----------|-------------|
| ECU, PRU, ANU | → ECS |
| HGU, DMU, NIU, CIP | → HYCHLOR |
| MIXING 관련 장비 | → ECS |

### 7.3 제품군별 검증 규칙

#### ECS 전용 규칙
- MIXING 시스템 검증 (S.W.H.TK, PCU, VCU 등)
- T-STRAINER 적용 여부 확인
- CSU/GDS 안전장비 검증
- VLS 밸브 신호 리스트 검증

#### HYCHLOR 전용 규칙
- CIP 위치 및 사이즈 검증
- DMU VENT 라인 검증 (5M 표기)
- HGU ↔ DMU CLASS PIPING 검증
- NIU INJECTION LINE 검증

### 7.4 공통 항목 우선 구현

1. **P0 (최우선)**
   - BALLAST PUMP 검증 (4개 항목)
   - 기본 항목 검증 (4개 항목)

2. **P1 (우선)**
   - 선급별 요구사항 (ABS, DNV, LR, KR)
   - 선종별 요구사항 (Bulker, Tanker, Barge, LNG/LPG)

3. **P2 (확장)**
   - ECS 전용 장비 검증 (MIXING, ANU, PRU 등)
   - HYCHLOR 전용 장비 검증 (HGU, DMU, CIP 등)

---

## 8. 참고 자료

### 8.1 파일 위치

```
/home/uproot/ax/poc/apply-company/techloss/
├── ECS 예시/
│   └── (Ver.25.01) Check list_P&ID_ECS-B (2025.12.19.).xlsm
├── 2차 기술 미팅 자료 모음/
│   ├── 하이클로 예시/
│   │   └── (Ver.25.01) Check list_P&ID_HYCHLOR 2.0 (2025.10.01).xlsm
│   └── ECS 예시/
│       └── (Ver.25.01) Check list_P&ID_ECS-B (2025.12.19.).xlsm
```

### 8.2 관련 문서

- `TECHLOSS_자료현황_2026-01-05.md` - TECHCROSS 자료 전체 현황
- Design Checker API: `/models/design-checker-api/` - P&ID 설계 검증 API

---

*Generated by Claude Code (Opus 4.5) - 2026-01-05*
