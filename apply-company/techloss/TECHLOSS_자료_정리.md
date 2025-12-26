# TECHCROSS 기본설계팀 도면 검토 AI 프로젝트 자료 정리

## 1. 프로젝트 개요

### 1.1 회사 정보
- **회사명**: TECHCROSS (테크로스)
- **담당팀**: 기본설계팀
- **프로젝트 목적**: AI를 활용한 P&ID(Piping and Instrumentation Diagram) 도면 검토 자동화

### 1.2 프로젝트 배경
- 현재 GPT(LLM)는 텍스트 기반으로 이미지/도면 인식 능력이 부족하여 도면 검토에 한계가 있음
- **멀티모달 AI** 개발을 통해 이미지를 사람처럼 이해하고 처리하는 시스템 구축 예정

### 1.3 핵심 목적
> **'Drawn → Reviewed → Approved'** 의 도면 검토 과정을
> **'AI 검토 → Approved'** 으로 변환하여 검토 시수 절감 및 Human Error 방지

---

## 2. 개발 로드맵

| 단계 | 기간 | 주요 내용 |
|------|------|----------|
| **Phase 1** | 26년 1-2분기 | POC 수행 및 업체 계약 (기술/기능 실현 가능 여부 테스트) |
| **Phase 2** | 26년 3-4분기 | AI 컨셉 확정, User Interface 구현, 개발 업체와 피드백 교환 |
| **Phase 3** | 27년 1-2분기 | 프로토타입 완성, PDF/CAD 파일 인식 AI 알고리즘 완성 |
| **Phase 4** | 27년 3-4분기 | 유지보수 및 시운영, 팀원 교육 및 AI 검토 체계 운영 |

---

## 3. 주요 기능 (1차)

### 3.1 P&ID 인식 및 체크리스트 검토
- 단순 텍스트가 아닌 **형상(Shape)** 기반으로 P&ID 인식 (PDF/DWG 파일)
- P&ID 내 장비 간 **상대적 위치** 파악
- 기본적 계산 및 적정 사양 적용 여부 검증
  - 예: 배관 내 해수 유속 3m/s 기준 사이즈 선정 확인
  - 예: Mixing pump 용량이 Ballast pump 용량의 4.3%인지 확인

#### 체크리스트 검토 항목 예시:
| No | 체크 항목 | 판정 | 비고 |
|----|----------|------|------|
| 1 | T-STR 미적용 조선소임을 확인하였는가 | N/A | Retrofit 건으로 적용 |
| 2 | FMU가 ECU 후단에 위치하였는가 | 충족 | - |
| 3 | FMU에 Down sizing 적용하였는가 | 미충족 | 메인 배관과 SIZE 동일 |
| 4 | ANU 적정 용량 적용하였는가 | 충족 | De-Ballasting 유량 700m³/h로 5T 모델 적정 |

### 3.2 Valve Signal List 작성
- 도면 상 **'SIGNAL FOR BWMS'** 문구가 적용된 밸브 자동 추출
- Signal List에 밸브들의 역할과 함께 기입
- 당사 표준에 따라 밸브 간 알람 조건 기입
- 누락된 알람 조건 발견 시 사용자에게 알림

### 3.3 Equipment List 작성
- P&ID상 **당사(TECHCROSS) 공급으로 표시된 장비** 자동 인식
- Equipment List 자동 작성
- 장비별 수량 및 사양 정리

### 3.4 Deviation List 작성
- 조선소 POS(Purchase Order Specification) 중 **당사 표준과 상이한 부분** 식별
- 영업팀 협의가 필요한 부분을 Deviation 사항으로 기입

---

## 4. 향후 추가 기능 (2차)

### 4.1 P&ID 자동 작성
- 설계 조건 입력(ECS 모델, 조선소, 선급) 후
- 미리 학습한 모듈들을 선정 및 조합하여 P&ID 자동 작성
- 조선소 POS 및 선급 RULE에 부합하도록 작성

### 4.2 Flow Diagram 작성
- 시스템 이해를 바탕으로 Flow Diagram 자동 작성

### 4.3 사내 ERP 접근 및 검색
- 사내 ERP에 접근하여 도면 및 이력 검색
- 프로젝트 정보 요청 시 검색 결과 정리하여 제공

---

## 5. 와이어프레임 (UI/UX 설계)

### 5.1 메인 화면 구성

| 영역 | 기능 |
|------|------|
| **나의 프로젝트** | 내가 진행중인 프로젝트 열람, P&ID 검토, 문서 작성, 코멘트 답변 회신 |
| **전체 프로젝트 검색** | Database로 팀원 전체 프로젝트 열람 (열람만 가능, 수정 불가) |
| **지침 열람** | 체크리스트, 조선소별 특이사항, 선급룰 열람 (관리자 계정 시 수정 가능) |

### 5.2 프로젝트 화면 구조
```
프로젝트 선택
├── TP (Technical Proposal)
├── 승인도
│   ├── Rev.A, Rev.B, ...
│   └── 조선소 코멘트 / Rev. 개정
├── 선급 승인
├── Manual
├── Signal List
└── 최근 대화 (자연어 문답)
```

### 5.3 승인도 관리 기능
1. **신규 Revision 추가**: 조선소 요청사항/P&ID 수정 경위 입력
2. **체크리스트 작성/보기**: AI가 P&ID 분석 후 체크리스트 자동 생성
3. **재검토**: 미처리 항목 표시 (노란색: 확인 필요, 빨간색: 미충족)
4. **상신하기**: 결재 프로세스 진행

### 5.4 자연어 대화 기능
- 프로젝트별 자유로운 질의응답
- 출처: 전체 프로젝트 내용, 사전 입력된 당사 장비 정보, 지침 내용
- 개인 대화 내용은 다른 사용자에게 비공개

---

## 6. BWMS(Ballast Water Management System) 제품 라인업

### 6.1 ECS (Electro Cleen System) - 전기분해 방식
**특징**: 직접 전기분해 방식, 필터 없음

#### 주요 구성품:
| 약어 | 장비명 | 설명 |
|------|--------|------|
| CPC | Control PC | 제어 PC |
| PDE | Power Distributor Equipment | 전력 분배 장비 |
| ECU | Electro Chamber Unit | 전해조 유닛 |
| PRU | Power Rectifier Unit | 전원 정류기 유닛 |
| EPJ | ECU Power Junction Box | ECU 전원 접속함 |
| ESJ | ECU Signal Junction Box | ECU 신호 접속함 |
| ANU | Auto Neutralization Unit | 자동 중화 장치 |
| TSU-S | TRO Sensor Unit & Control Unit | TRO 센서 및 제어 유닛 |
| APU | Air Pump Unit | 공기 펌프 유닛 |
| FMU | Flow Meter Unit | 유량계 유닛 |
| FTS | F.W Temperature Sensor | 담수 온도 센서 |
| CSU | Conductivity Sensor Unit | 전도도 센서 유닛 |
| GDS | Gas Detection Sensor | 가스 감지 센서 |
| EWU | EM Washing Unit | 전극 세척 유닛 |
| T-STR | T-Strainer | T형 스트레이너 |
| PCU | Pump Control Unit | 펌프 제어 유닛 |
| FCV | Flow Control Valve | 유량 제어 밸브 |

### 6.2 HYCHLOR 2.0 - 간접 전기분해 방식
**특징**: Side stream 전기분해 방식, 필터 포함

#### 추가 구성품:
| 약어 | 장비명 | 설명 |
|------|--------|------|
| MCP | Main Control PC | 메인 제어 PC |
| MPC | Main Power Cabinet | 메인 전원 캐비닛 |
| MCC | Main Control Cabinet | 메인 제어 캐비닛 |
| HGU | Hypochlorite Generation Unit | 차아염소산염 생성 장치 |
| PRM | Power Rectifier Module | 전원 정류 모듈 |
| DMU | Degas Module Unit | 탈기 모듈 유닛 |
| CIP | Chemical Injection Pipe | 약품 주입 배관 |
| NIU | Neutralization Injection Unit | 중화제 주입 유닛 |
| DTS | DPD TRO Sensor | DPD TRO 센서 |
| DTU | Drain Tank Unit | 드레인 탱크 유닛 |
| FP | Feeder Pump | 피더 펌프 |
| IFP | Inverter For Feeder Pump | 피더 펌프용 인버터 |
| ST | Strainer | 스트레이너 |
| CPP | Conductivity & Pressure pipe assy | 전도도 및 압력 배관 조립체 |
| AC01V/AC02V | Safety Fail Closed Valve | 안전 실패 시 닫힘 밸브 |
| SWH | Sea Water Heater | 해수 히터 |

---

## 7. P&ID 도면 주요 설계 기준

### 7.1 공통 설계 노트

#### G-2 Sampling Port
- IMO 규정 준수 필수
- 수평 또는 수직 메인 밸러스트 배관의 **상류(up-stream)**에 설치
- 하류(down-stream)에 설치 금지

#### TSU/DTS (TRO Sensor)
- APU와 최대한 가깝게 배치 (5m 이내, 높이 2m 이내)
- Sampling Port와 ANU/NIU Port 간 최소 **5D** 거리 유지
- Bypass 배관은 TRO 센서 장비보다 높게 배치
- 배관 및 밸브 재질: **SUS316L**

#### ANU/NIU (중화 유닛)
- Injection Port와 유닛 간 최대한 가깝게 배치 (10m 이내)
- 10m 이상 시 HMI의 "PREPARATION" 버튼으로 중화제 충전 필요
- 배관 및 밸브 재질: **SUS316L**
- 담수 최소 온도 **20°C** 확보 필요

#### ECU (전해조)
- ECU 출구 배관은 ECU보다 높게 배치 (내부 물 유지를 위해)
- PS&PI, TS&TI는 Maker 공급, 설치는 Yard 수행

#### EWU (전극 세척)
- 담수 공급 라인 및 드레인 연결 라인은 ECU/HGU 주변 **3m 이내** 배치
- 세척수는 EWU 탱크에 저장 후 **12해리 이상, 수심 25m 이상**에서 배출

### 7.2 Mixing Operation (저염도 지역 운전)
- 해수 저장 탱크 용량: 총 밸러스팅 용량의 **최소 4.3%** (ECS) / **1%** (HYCHLOR)
- 계산: S.W.(34.7 PSU) 4.3% + F.W.(0 PSU) 95.7% = Mixing(1.5 PSU)
- Mixing Pump 흡입 중심은 A.P.TK 바닥면보다 낮게 위치

### 7.3 냉각수 조건 (PRU용)
- 냉각 해수 온도 (입구): +32°C
- 냉각 담수 온도 (입구): +36°C
- 냉각 담수 압력 강하: 0.5BAR
- 유량: 0.45m³/h (PRU당)

### 7.4 해수 히터 적용 조건
- 해수 온도 **3°C 미만** 시 Sea Water Heater 적용
- BWMS에서 해수 온도 모니터링 필요

---

## 8. 예시 프로젝트 정보

### 8.1 ECS 예시 - YZJ2023-1584/1585
| 항목 | 내용 |
|------|------|
| 조선소 | YZJ (Yangzijiang Shipbuilding) |
| Hull No. | YZJ2023-1584/1585 |
| 선급 | NK (Nippon Kaiji Kyokai) |
| 모델 | ECS1000B 1.1 x 1 |
| Ballast Pump | 500m³/h x 3.5bar |
| Strip Eductor | 50m³/h x 2.5bar |
| Mixing S.W. Pump | 45m³/h x 40mTH |
| 냉각수 조건 | Max. 36°C, Min. 3.6m³/h |

### 8.2 HYCHLOR 예시 - H1993A/4A/5A/6A/7A/8A
| 항목 | 내용 |
|------|------|
| 조선소 | HUDONG-ZHONGHUA (沪东中华) |
| Hull No. | H1993A-98A |
| 선종 | 174,000M³ LNG Carrier |
| 선급 | LR (Lloyd's Register) |
| 모델 | ECS-HYCHLOR 2.0-3000+3000 (2 Sets) |
| 처리 용량 | 5,600 m³/h 이상 |
| Ballast Pump | 2,800m³/h x 35mTH (3대, 1대 예비) |
| Strip Eductor | 350m³/h (2대) |
| Feeder Pump | 30m³/h x 60mTH |
| 전원 | 3-phase AC440V (60Hz) |

---

## 9. 주요 문서 목록

### 9.1 기획 문서
| 파일명 | 내용 |
|--------|------|
| 기본설계팀 AI 활용한 도면 검토 계획 (25.12.10.).pdf | 프로젝트 로드맵 및 기능 정의 |
| 기본설계팀 AI 에이전트 와이어프레임.pdf | UI/UX 설계 문서 |

### 9.2 ECS 예시 자료
| 파일명 | 내용 |
|--------|------|
| [PNID] REV.0 YZJ2023-1584_1585_NK_ECS1000Bx1_MIX | P&ID 도면 (PDF/DWG) |
| (Ver.25.01) Check list_P&ID_ECS-B | P&ID 체크리스트 (XLSM) |
| BWMS Valve signal & Operation mode | 밸브 신호 및 운전 모드 (XLSX) |
| TP_ECS Equipment list | 장비 목록 (XLSX) |
| (DEVIATION LIST) | 편차 목록 (XLSX) |
| 48K LPGC - General requirements of TA | 기술 요구사항 (DOC) |
| Ballast Water Treatment Plant | 밸러스트 처리 사양 (DOCX) |

### 9.3 HYCHLOR 예시 자료
| 파일명 | 내용 |
|--------|------|
| [PNID] Rev.0 H1993A_4A_5A_6A_7A_8A_HYCHLOR 2.0-3000 2SETS_LR | P&ID 도면 |
| (Ver.25.01) Check list_P&ID_HYCHLOR 2.0 | P&ID 체크리스트 |
| (Ver.25.01) BWMS Valve signal | 밸브 신호 목록 |
| TP_Equipment list | 장비 목록 |
| Counter flange List | 카운터 플랜지 목록 |
| Ballast water treatment order specification | 조선소 발주 사양서 |
| Deviation list of Ballast water treatment | 편차 목록 |
| Order specification for general requirement | 일반 요구사항 |
| hull and electrical General technical requirement | 선체/전기 기술 요구사항 |

---

## 10. AI 시스템 개발 시 고려사항

### 10.1 입력 데이터
1. **P&ID 도면** (PDF, DWG)
2. **조선소 POS** (Purchase Order Specification)
3. **선급 RULE** 문서
4. **당사 표준 체크리스트**
5. **과거 프로젝트 데이터** (ERP 연동)

### 10.2 출력 데이터
1. **체크리스트 검토 결과** (충족/미충족/N/A)
2. **Valve Signal List** (자동 추출)
3. **Equipment List** (자동 작성)
4. **Deviation List** (자동 식별)
5. **Flow Diagram** (향후 기능)

### 10.3 기술적 도전 과제
1. P&ID 도면의 **심볼/형상 인식** 정확도
2. **텍스트 + 이미지** 멀티모달 처리
3. 장비 간 **연결 관계** 파악
4. 선급별/조선소별 **표준 규정** 학습
5. **계산 로직** 적용 (유속, 용량 등)

### 10.4 품질 검증 항목
- 도면 양식 (51-Q-02-08) 최신 적용 여부
- ECS Components list 사양 확인 (ECU, FMU, T-STR, MIXING PUMP, FCV pipe size)
- 장비 설치 위치 확인 (비방폭 장비가 방폭구역에 설치되지 않도록)
- 재고 사용 가능 여부 (특히 FMU/T-STR/FCV/PUMP)
- Ballast pump 용량/운전조건 확인
- Ballast pump 후단 Check valve & Manual valve 확인

---

## 11. 용어 정리

| 용어 | 설명 |
|------|------|
| BWMS | Ballast Water Management System (밸러스트수 관리 시스템) |
| BWTS | Ballast Water Treatment System (밸러스트수 처리 시스템) |
| P&ID | Piping and Instrumentation Diagram (배관계장도) |
| POS | Purchase Order Specification (발주 사양서) |
| TP | Technical Proposal (기술 제안서) |
| TRO | Total Residual Oxidant (총잔류산화물) |
| PSU | Practical Salinity Unit (실용염분단위) |
| ECU | Electro Chamber Unit (전해조 유닛) |
| HGU | Hypochlorite Generation Unit (차아염소산염 생성 장치) |
| FMU | Flow Meter Unit (유량계 유닛) |
| ANU/NIU | Auto/Neutralization Injection Unit (중화제 주입 장치) |
| N.O | Normally Open (평상시 열림) |
| N.C | Normally Closed (평상시 닫힘) |
| IMO | International Maritime Organization (국제해사기구) |
| USCG | United States Coast Guard (미국 해안경비대) |
| LR | Lloyd's Register (영국 선급) |
| NK | Nippon Kaiji Kyokai (일본 선급) |
| DNV | Det Norske Veritas (노르웨이 선급) |

---

*문서 작성일: 2025.12.25*
*작성 목적: TECHCROSS 기본설계팀 AI 도면 검토 시스템 POC 참고자료*
