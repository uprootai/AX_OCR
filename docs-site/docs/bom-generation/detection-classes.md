---
sidebar_position: 1
title: 검출 클래스
description: BOM 생성 및 주석용 73개 검출 클래스 전체 목록
---

# 검출 클래스

시스템은 기계 도면에 특화된 YOLO v11 모델을 사용합니다. 전체 모델에 걸쳐 73개 이상의 클래스가 인식되며, BOM 관련 부품과 주석(Annotation) 요소로 구분됩니다.

## BOM 관련 클래스 (27개)

이 클래스들은 전기 단선도에서 검출되는 물리적 부품을 나타냅니다. 각 검출 결과는 수량 집계 및 단가 산출과 함께 BOM에 반영됩니다.

### 전기 장비 클래스

`bom_detector` 모델은 27개의 배전 장비 클래스를 검출합니다:

| 클래스 ID | 클래스명 | 표시명 | 카테고리 |
|----------|---------|-------|---------|
| 0 | ARRESTER | Arrester | 보호 |
| 1 | CB DS ASSY | CB DS Assembly | 개폐 |
| 2 | CT | Current Transformer | 계측 |
| 3 | CVT | Capacitive Voltage Transformer | 계측 |
| 4 | DS ASSY | Disconnector Assembly | 개폐 |
| 5 | ES / EST | Earth Switch | 접지 |
| 6 | GIS | Gas Insulated Switchgear | 개폐 |
| 7 | LA | Lightning Arrester | 보호 |
| 8 | LS | Line Switch | 개폐 |
| 9 | MOF | Metering Outfit | 계측 |
| 10 | NGR | Neutral Grounding Resistor | 접지 |
| 11 | P.Fuse | Power Fuse | 보호 |
| 12 | PI | Power Indicator | 계측 |
| 13 | PT | Potential Transformer | 계측 |
| 14 | SA | Surge Arrester | 보호 |
| 15 | SPD | Surge Protection Device | 보호 |
| 16 | T.C | Contactor | 개폐 |
| 17 | TR | Transformer | 전력 |
| 18 | VT | Voltage Transformer | 계측 |
| 19 | Branch (U-type) | U-type Branch | 배선 |
| 20 | Disconnector | Disconnector | 개폐 |
| 21 | Motor | Motor | 부하 |
| 22 | Power Fuse | Power Fuse | 보호 |
| 23 | Rectifier | Rectifier | 변환 |
| 24 | Circuit Breaker | Circuit Breaker | 보호 |
| 25 | Capacitor | Capacitor | 역률 |
| 26 | Arrester (alt) | Arrester | 보호 |

### 클래스 카테고리 요약

| 카테고리 | 개수 | 클래스 |
|---------|------|--------|
| **보호** | 7 | ARRESTER, LA, SA, SPD, P.Fuse, Power Fuse, Circuit Breaker |
| **개폐** | 6 | CB DS ASSY, DS ASSY, GIS, LS, T.C, Disconnector |
| **계측** | 6 | CT, CVT, MOF, PI, PT, VT |
| **전력** | 1 | TR |
| **접지** | 2 | ES/EST, NGR |
| **부하** | 1 | Motor |
| **변환** | 1 | Rectifier |
| **역률** | 1 | Capacitor |
| **배선** | 1 | Branch (U-type) |
| **기타** | 1 | Arrester (alt) |

## P&ID 심볼 클래스 (60개)

`pid_symbol` 모델은 공정 및 계장 다이어그램(P&ID)에 사용되는 심볼을 검출합니다:

### 밸브 유형

| 클래스 | 설명 |
|-------|------|
| Gate Valve | 표준 게이트 밸브 |
| Globe Valve | 글로브/제어 밸브 |
| Ball Valve | 볼 밸브 |
| Butterfly Valve | 버터플라이 밸브 |
| Check Valve | 역류 방지 밸브 |
| Relief Valve | 압력 릴리프 밸브 |
| Control Valve | 자동 제어 밸브 |
| Solenoid Valve | 전기 구동 밸브 |
| 3-Way Valve | 3방향 라우팅 밸브 |
| Needle Valve | 미세 유량 제어 밸브 |

### 장비

| 클래스 | 설명 |
|-------|------|
| Pump | 원심/용적식 펌프 |
| Compressor | 가스 압축기 |
| Heat Exchanger | 셸앤튜브 / 판형 열교환기 |
| Tank | 저장 용기 |
| Reactor | 화학 반응기 |
| Filter | 여과 장비 |
| Separator | 상분리 장치 |
| Column | 증류/흡수탑 |

### 계기류

| 클래스 | 설명 |
|-------|------|
| Pressure Indicator | 압력 지시계 (PI) |
| Temperature Indicator | 온도 지시계 (TI) |
| Flow Indicator | 유량 지시계 (FI) |
| Level Indicator | 레벨 지시계 (LI) |
| Pressure Transmitter | 압력 트랜스미터 (PT) |
| Temperature Transmitter | 온도 트랜스미터 (TT) |
| Flow Transmitter | 유량 트랜스미터 (FT) |
| Level Transmitter | 레벨 트랜스미터 (LT) |
| Controller | PID 제어기 |

### 배관 요소

| 클래스 | 설명 |
|-------|------|
| Reducer | 관경 축소 이음 |
| Tee | T형 분기관 |
| Elbow | 방향 전환 이음 |
| Flange | 배관 연결 플랜지 |
| Orifice | 유량 측정 오리피스 |
| Spectacle Blind | 차단용 블라인드 |

## 주석 클래스 (46개 이상)

주석 클래스는 모든 도면 유형에서 검출되며 부가 정보를 제공합니다. 이 클래스들은 BOM 수량에 직접 반영되지 않지만, 추출 데이터를 보강합니다.

### 치수 유형

| 유형 | 설명 | 예시 |
|------|------|------|
| Length | 선형 치수 | `45.2 mm` |
| Diameter | 원형 치수 | `OD 670 mm` |
| Radius | 호 치수 | `R 25` |
| Angle | 각도 치수 | `45.0 deg` |
| Thread | 나사 규격 | `M24x120L` |

### 공차 유형

| 유형 | 설명 | 예시 |
|------|------|------|
| Bilateral | 양방향 공차 | `45.2 +/- 0.1` |
| Unilateral | 단방향 공차 | `45.2 +0.05 / -0.00` |
| Limit | 최소/최대 범위 | `45.15 - 45.25` |

### GD&T(기하공차) 심볼

| 심볼 | 설명 |
|------|------|
| Straightness | 직진도 |
| Flatness | 평면도 |
| Circularity | 진원도 |
| Cylindricity | 원통도 |
| Perpendicularity | 직각도 |
| Parallelism | 평행도 |
| Position | 위치도 |
| Concentricity | 동심도 |
| Runout | 흔들림 |
| Total Runout | 전체 흔들림 |
| Profile of a Line | 선의 윤곽도 |
| Profile of a Surface | 면의 윤곽도 |

### 표면 거칠기

| 클래스 | 설명 |
|-------|------|
| Surface Roughness | Ra / Rz 값 |
| Machining Symbol | 가공 요구 기호 |
| Welding Symbol | 용접 유형 기호 |

## 모델 설정

각 검출 모델의 기본 파라미터는 다음과 같습니다:

| 모델 | 신뢰도 | IOU | 이미지 크기 | SAHI |
|------|--------|-----|-----------|------|
| `bom_detector` | 0.40 | 0.50 | 1024 | 꺼짐 |
| `pid_symbol` | 0.10 | 0.45 | 1024 | 켜짐 |
| `pid_class_aware` | 0.10 | 0.45 | 1024 | 켜짐 |
| `pid_class_agnostic` | 0.10 | 0.45 | 1024 | 켜짐 |
| `engineering` | 0.50 | 0.45 | 640 | 꺼짐 |
| `panasia` | 0.40 | 0.50 | 1024 | 꺼짐 |

**SAHI** (Slicing Aided Hyper Inference)는 P&ID 모델에서 활성화되어, 이미지를 25% 오버랩이 적용된 512x512 슬라이스로 분할 처리함으로써 작은 심볼의 검출 성능을 향상시킵니다.

## 마진 페널티

도면 마진 영역(표제란, 리비전 블록, 외곽 테두리)에서의 검출은 오검출을 줄이기 위해 50% 신뢰도 페널티가 적용됩니다:

| 영역 | 조건 | 페널티 |
|------|------|--------|
| 표제란 | x > 65% 이고 y > 85% | 0.5x |
| 리비전 블록 | x > 75% 이고 y < 15% | 0.5x |
| 상/하단 마진 | y < 3% 또는 y > 97% | 0.5x |
| 좌/우측 마진 | x < 3% 또는 x > 97% | 0.5x |
