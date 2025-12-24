# 금속 적층 제조의 기하공차 및 제조 조립 가능성 추정

## 논문 정보
- **제목**: Geometric tolerance and manufacturing assemblability estimation of metal additive manufacturing (AM) processes
- **저자**: Baltej Singh Rupal, Nabil Anwer, Marc Secanell, Ahmed Jawad Qureshi
- **소속**:
  - University of Alberta (캐나다)
  - Université Paris-Saclay, ENS Paris-Saclay, LURPA (프랑스)
- **게재**: Materials and Design 194 (2020) 108842
- **게재일**: 2020년 6월 6일
- **DOI**: 10.1016/j.matdes.2020.108842

## 연구 배경
- 금속 적층 제조(AM)는 복잡한 금속 부품 제조의 주요 공정으로 자리잡음
- 그러나 금속 AM 인쇄 부품 및 조립품의 기하공차 제어 연구는 부족
- **조립 가능성(Assemblability)**: 부품이 맞춤 부품과 조립되어 지정된 기능을 수행하는 능력
  - 맞춤 부품의 기하공차에 크게 의존
  - 크기뿐만 아니라 형상(shape)과 방향(orientation) 관점에서도 제어 필요

## 연구 목적
금속 AM 부품의 기하공차를 추정하고 조립 가능성을 보장하는 방법론 제시:
- 공정 모델링과 수치 시뮬레이션 활용
- 광범위한 실험 작업 없이 예측 가능
- 열물리학적 공정 효과 고려

## 방법론: Skin Model Shapes 기반 공차 분석

### Skin Model이란?
- **정의**: "작업물과 환경 사이의 물리적 인터페이스 모델"
- 부품의 명목 형상과 다양한 소스의 기하 편차 고려
- 3D 포인트 클라우드로 표현
- 각 점은 표면 법선 벡터 방향으로 편차 적용

### 2단계 생성 과정

#### 1. Prediction Stage (예측 단계)
- **시기**: 초기 설계 단계
- **방법**:
  - 체계적 편차: In-plane shrinkage factor 사용
  - 랜덤 편차: Random field theory 기반
  - Squared exponential correlation function 사용
- **수식**:
  - In-plane shrinkage: Xs = Sp × X
  - Correlation: Mcr = exp(-d²ij / l²cr)
- **파라미터 조정**:
  - Shrinkage factor: 0.98 (0.90-0.99 범위 테스트)
  - Standard deviation: 0.02mm

#### 2. Observation Stage (관찰 단계)
- **시기**: 후기 설계 단계
- **방법**:
  - 열-기계적 유한 요소 시뮬레이션 사용
  - 실제 제조 공정 시뮬레이션 결과 반영
- **구현**: Autodesk Netfabb Ultimate Academic 2019

## Assembly Benchmark Test Artifact (ABTA) 설계

### 설계 기준 (12가지)
1. AM 공정의 인쇄 크기 제약 준수
2. 기본 조립 연결부 포함 (회전, 프리즘, 구형 조인트)
3. 토폴로지 최적화 특징 포함 (unit-cells, 유기적 형상)
4. 공정 파라미터 기반 특징 선택 (최소 층 두께, 분말 입자 크기)
5. GD&T 정량화기로 공차 대역 제공
6. 국제 표준 준수 (ISO 1101, ASME Y14.5, ISO 17296-3, ASME Y14.46)
7. 실제 조립 구성요소와 관련성
8. 정밀 측정 장비로 측정 가능 (CMM, 레이저 스캐너)
9. 체계적 및 랜덤 편차 모드 추출 가능
10. 정적/동적 조립 기능 테스트
11. 조립 설계와 AM 설계의 연결 고려
12. 조립 특징에 서포트 구조 회피

### ABTA 구조
- **구성요소**: Pin-ABTA와 Hole-ABTA
- **크기**: 50 × 25 × 20 mm (L × B × H)
- **조립 조인트**: 회전 조인트(Revolute Joint) 2개 + 평면 조인트(Planer Joint)
- **맞춤 방식**: H11/c11 간극 맞춤
  - Pin 직경: 14.840mm (공칭)
  - Hole 직경: 15.055mm (공칭)

### Lattice 구조
- **타입**: Simple cubic lattice
- **목적**: 토폴로지 최적화 및 중량 감소
- **파라미터**:
  - Shell 두께: 1.5mm
  - Infill 비율: 37.7%
  - Unit cell 길이: 5mm
  - Beam 두께: 1mm
- **측정 방법**: Total Supplemental Surface (TSS) 개념 사용 (ASME Y14.46)

## GD&T 특성

### Pin-ABTA
- Datum A 평면의 평탄도(Flatness)
- Datum A, B, C에 대한 핀 축의 수직도(Perpendicularity)
- 핀의 원통도(Cylindricity)
- Datum A, B, C에 대한 핀의 위치 공차(Position Tolerance)

### Hole-ABTA
- Datum A 평면의 평탄도
- Datum A, B, C에 대한 홀 축의 수직도
- 홀의 원통도
- Datum A, B, C에 대한 홀의 위치 공차

## 열-기계적 시뮬레이션

### 지배 방정식

#### 1. 열 전도 방정식 (순차 결합 해석)
```
Q(x,t) - ∇·q(x,t) = ρCp(dT/dt)
```
- q = -k∇T (Fourier's law)
- Goldak's 3D Gaussian ellipsoidal distribution 사용

#### 2. 열 손실
- 대류: qconv = h(Ts - Ta)
- 복사: qrad = εσ(T⁴s - T⁴a)

#### 3. 기계적 응답 (선형 탄성 방정식)
```
∇·σ = 0
σ = Cεe (Hooke's law)
ε = εe + εp + εt (총 변형률)
```
- 열 변형률: εt = α(T(x,y,z,t) - Tref)
- von-Mises 항복 기준 및 Prandtl-Reuss 유동 법칙 사용

### 시뮬레이션 파라미터 (LPBF)
- **재료**: Inconel 718
- **레이저 출력**: 200W
- **열원 흡수 효율**: 35%
- **레이저 빔 직경**: 0.063mm
- **이동 속도**: 1800mm/s
- **층 두께**: 0.04mm
- **Hatch spacing**: 0.05mm
- **층간 회전 각도**: 225°
- **베이스 플레이트**: 100 × 100 × 20mm (중앙 고정)
- **계산 시간**:
  - Pin-ABTA: 5시간 25분
  - Hole-ABTA: 1시간 53분

### 변동성 캡처
- 20개 시뮬레이션 실행 (훈련 세트)
- 공정 파라미터 체계적 변경:
  - 층 두께: 30-70μm
  - Hatch spacing: 100-200μm
  - 레이저 출력: 200-300W
  - 스캔 속도: 500-1000mm/s

### Principal Component Analysis (PCA)
- 편차 STL에서 PCA 수행
- 주요 변동 모드 및 PCA 점수 추출
- Inverse transform sampling으로 샘플 생성

## 실험 검증

### 제작 조건
- **시스템**: AddUp FormUp 350 LPBF 프린터
- **플랫폼**: 원형, 직경 100mm
- **재료**: Inconel 718 (Aubert & Duval Pearl Micro Ni718)
- **분말 크기**: 10-53μm
- **층 두께**: 40μm
- **샘플 수**: 3개 (각각 별도 빌드 플레이트)
- **제거 방법**: Wire-EDM

### 측정 장비
- **장비**: SEIV Renault CMM (프랑스 Guyancourt)
- **센서**:
  - Kreon Aquilon KA50 레이저 센서
  - Renishaw TP2 touch probe
- **반복성 (2σ)**: 0.35μm (단방향)
- **해상도**: 0.2μm
- **측정 횟수**: 각 정량화기당 3회 (표준 오차 계산)
- **측정점**:
  - 평탄도: 최소 15점
  - 원통도: 최소 10점

## 실험 결과

### 1. 직경 값
| 구성요소 | Nominal | Prediction | Observation | Experimental | 오차 |
|---------|---------|------------|-------------|--------------|------|
| **Hole D1** | 15.055mm | 15.03mm | 15.05mm | 14.89mm | 0.75% |
| **Hole D2** | 15.055mm | 15.02mm | 15.05mm | 14.95mm | - |
| **Pin d1** | 14.840mm | 14.83mm | 14.93mm | 14.77mm | 0.62% |
| **Pin d2** | 14.840mm | 14.90mm | 14.93mm | 14.77mm | - |

- Observation phase가 prediction phase보다 평균 0.090-0.110mm 높게 추정
- 두 단계 모두 조립 가능성 사양 충족

### 2. 원통도 (Cylindricity)
| Phase | 평균 값 | 표준편차 |
|-------|---------|----------|
| Prediction | 0.056mm | 0.014mm |
| Observation | 0.070mm | - |
| Experimental | 0.054mm | 0.008mm |

- Prediction phase가 실험 값과 0.010mm 이내로 근접

### 3. 평탄도 (Flatness)
| Phase | 평균 값 | 표준편차 |
|-------|---------|----------|
| Prediction | 0.120mm | 0.019mm |
| Observation | 0.110mm | 0.016mm |
| Experimental | 0.120mm | 0.016mm |

- Hole 구성요소의 XY 평면(Datum A)에서 두 단계 모두 과소 예측
- 원인: Lattice 구조 효과가 시뮬레이션에서 정확히 캡처되지 않음

### 4. 수직도 (Perpendicularity)
| Phase | 평균 값 |
|-------|---------|
| Prediction | 0.043mm |
| Observation | 0.045mm |
| Experimental | 0.037mm |

- 대부분 0.020mm 범위 내 (1개 이상치 제외)

### 5. True Position (위치 공차)
- **복합 공차**: 평탄도 + 축 위치에 의존
- Hole 구성요소: 실험 결과가 observation phase와 0.050mm 이내
- Pin 구성요소: 실험 결과가 두 단계보다 0.250mm 이상 높음
- 모든 결과가 조립 가능성 조건 충족

### 6. 조립 가능성 검증
- **결과**: 100% 간극 맞춤 달성 (3개 샘플 모두)
- 후처리 작업 없이 조립 성공

## 주요 기여

1. **새로운 분할 기술**: 휴리스틱 기반 분할로 텍스트 감지 및 정밀도 향상
2. **Skin model shapes 기법**: 금속 AM 공정에 최초 적용
3. **하이브리드 접근법**:
   - 전통적 OCR (In-plane shrinkage)
   - 물리 기반 시뮬레이션 (FEM)
   - 통계적 방법 (Random field theory)
4. **GD&T 표준 준수**: ISO 1101, ASME Y14.5 정량화기 사용
5. **실험 검증**: CMM 측정 및 실제 조립으로 방법론 검증
6. **확장성**: 다른 AM 공정 및 재료에 적용 가능

## 연구의 한계

### 현재 한계
1. **계산 시간**: FEM 시뮬레이션이 오래 걸림 (최대 5시간)
2. **FEM 정확도**: 시뮬레이션 자체가 실험 대비 최소 10% 오차
3. **체계적 편차 모델**: 균일한 in-plane shrinkage 사용
   - 형상 기반 및 층 기반 편차 미반영
4. **예측 단계 업데이트**: Trial-and-error 기반
   - 자동화된 최적화 필요
5. **이상치(Outliers)**: 균일 수축 계수 사용으로 인한 예측 오차
6. **Lattice 구조**: 복잡한 격자 구조의 편차가 정확히 예측되지 않음

### 고려사항
- 표면 거칠기는 고려하지 않음
  - LPBF Inconel 718 평균 표면 거칠기: 0.0165mm
  - 형상 및 방향 편차(평균 0.100mm)보다 훨씬 작음
  - 웨이브니스(waviness)는 형상 공차 측정에 포함됨

## 향후 연구 방향

1. **개선된 체계적 편차 모델**
   - 형상 기반 및 층 기반 편차 모델 개발
   - 더 정확한 예측 단계 결과

2. **자동화된 최적화**
   - 변수 업데이트를 위한 기계 학습 모델 탐색
   - 시뮬레이션 또는 실험 데이터로부터 자동 샘플 생성

3. **표면 기반 방법**
   - 기하공차뿐만 아니라 표면 분석 추가

4. **다양한 공정/재료**
   - 다른 금속 AM 공정에 적용
   - 다양한 재료 및 공정 파라미터로 모델 훈련

5. **복잡한 격자 구조**
   - 유기적 형상 및 minimal surface unit cells
   - 신뢰할 수 있는 측정 알고리즘 개발

## 응용 분야

1. **품질 관리 자동화**
   - 인쇄 전 공차 및 조립 가능성 예측
   - 재료 낭비 감소

2. **정밀 제조**
   - 높은 기하학적 정확도가 필요한 응용 분야
   - 항공우주, 의료 기기 등

3. **공정 최적화**
   - 공정 파라미터 선택 지원
   - 잔류 응력 관리

4. **설계 검증**
   - 제조 전 가상 조립 테스트
   - 설계 변경 영향 평가

## 기술적 세부사항

### 하드웨어
- CPU: Intel i7-6700 (4 Cores@3.4GHz)
- RAM: 16.0GB
- GPU: Nvidia A4000 (언급됨, 다른 연구용)

### 소프트웨어
- **CAD**: ANSYS SpaceClaim Direct Modeler 19.2
- **FEM 시뮬레이션**: Autodesk Netfabb Ultimate Academic 2019
- **데이터 분석**: MATLAB (stlread 등)
- **GD&T 추출**: MATLAB 루틴 (ISO 1101 정의 기반)

### 샘플 생성
- Prediction phase: 1,000,000 샘플
- Observation phase: 1,000,000 샘플
- 훈련 세트: 20개 시뮬레이션

## 결론

이 연구는 금속 AM 부품의 기하공차와 조립 가능성을 예측하는 체계적인 방법론을 제시:

1. **높은 정확도**:
   - 대부분의 GD&T 특성에서 ±0.010mm 표준편차
   - 실험 결과와 근접한 예측

2. **조립 가능성 검증**:
   - 가상 분석과 실제 조립 모두 성공
   - 100% 간극 맞춤 달성

3. **실용적 접근**:
   - 광범위한 실험 없이 예측 가능
   - 다양한 AM 공정에 확장 가능

4. **표준 준수**:
   - GD&T 국제 표준 따름
   - 산업 적용 가능한 방법론

**핵심 메시지**: Skin model shapes와 물리 기반 시뮬레이션을 결합하여 금속 AM의 기하학적 품질과 조립 가능성을 제조 전에 신뢰성 있게 예측할 수 있으며, 이는 정밀 제조 분야에서 금속 AM의 적용을 확대하는 데 기여할 것입니다.
