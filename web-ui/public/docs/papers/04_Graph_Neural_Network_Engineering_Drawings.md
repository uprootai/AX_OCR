# Graph Convolutional Networks를 사용한 공학 도면의 컴포넌트 세그멘테이션

## 논문 정보
- **제목**: Component Segmentation of Engineering Drawings Using Graph Convolutional Networks
- **저자**: Wentai Zhang, Joe Joseph, Yue Yin, Liuyue Xie, Tomotake Furuhata, Soji Yamakawa, Kenji Shimada, Levent Burak Kara
- **소속**: Carnegie Mellon University, Department of Mechanical Engineering
- **제출일**: 2023년 3월 15일
- **arXiv**: 2212.00290v2
- **게재 예정**: Computers in Industry

## 연구 배경

### 문제점
- **수동 작업의 필요성**: 제조 엔지니어들이 도면에서 위상학적 및 제조 요구사항을 수동으로 식별
- **비효율성**: 해석 프로세스가 노동집약적이고 시간 소모적
- **래스터 도면의 보편성**: 일본 제조업 조사에 따르면 84%가 PDF, 종이, 팩스 형태의 2D 래스터 도면 사용

### 기존 방법의 한계
1. **이미지 기반 방법의 문제**:
   - 공학 도면의 심각한 픽셀 희소성(sparse pixels)
   - 컴포넌트 타입이 맥락 정보에 의존적
   - 색상이나 텍스처 특징 부재
   - CNN의 장거리 맥락 정보 임베딩 한계

2. **기존 벡터화 방법의 한계**:
   - 직선 세그먼트만 사용 (원, 호, 곡선 부정확)
   - 위치 정보만 포함, 위상학적 특징 부재

## 제안 방법: EDGNet (Engineering Drawing Graph Network)

### 전체 워크플로우

```
Raster Drawing → Vectorization → Graph Construction → Graph Segmentation → Labeled Components
```

### 1. Drawing Vectorization (도면 벡터화)

#### 단계별 프로세스
1. **Thinning/Skeletonization (세선화)**
   - 4가지 알고리즘 테스트: Zhang & Suen, Lee et al., Medial Axis Transform, Datta & Parui
   - **선택**: Datta & Parui 방법 (가장 깨끗한 형태학적 결과)
   - 도면의 스트로크를 단일 픽셀 너비 궤적으로 변환

2. **Smoothing (평활화)**
   - 픽셀 노이즈 제거
   - 궤적 추적을 위한 전처리

3. **Trajectory Tracing (궤적 추적)**
   - Junction point, End point, Passing point 식별
   - 연결된 픽셀의 순서화된 리스트 생성
   - Junction 또는 endpoint에서 시작/종료

4. **Splitting (분할)**
   - Cosine angle 계산: θᵢ = cos⁻¹((ps - p₀) · (pe - p₀) / |ps - p₀| · |pe - p₀|)
   - 2차 미분으로 corner 감지
   - Local maxima에서 trace 분할

5. **Cleaning (정리)**
   - mⱼ < 4 픽셀 trace 제거
   - Junction point 병합
   - 그래프 edge-connectivity 보장

6. **Cubic Bezier Curve Fitting (3차 베지어 곡선 피팅)**
   - Least square method 사용
   - Bernstein polynomial: Bⱼᵢ,nord(t) = (nord choose i) tⁱ(1-t)^(nord-i)
   - 각 trace에 대해 제어점 계산
   - Terminal points를 first/last control points로 설정

### 2. Graph Construction (그래프 구성)

#### 그래프 정의
```
G(N, E)
N ∈ ℝ^(nN × (5n-1))  # Node features
E ∈ ℤ^(nE × 2)        # Edge indices
```

#### Node Features (n=4일 때, 총 19차원)

| Feature Type | Parameter | Dimension |
|--------------|-----------|-----------|
| **Shape** | n개 샘플링 포인트의 XY 좌표 | 2n (8) |
| **Length** | 연속 포인트 간 길이 | n-1 (3) |
|  | 총 길이 | 1 |
|  | first-to-last/total | 1 |
| **Angle** | 연속 선분 간 cos angle | n-2 (2) |
| **Curvature** | 각 샘플링 포인트의 곡률 | n (4) |

#### 특징
- **정규화**: 도면을 unit square에 맞춤 (크기 독립적)
- **맥락 정보**: Edge를 통한 컴포넌트 간 연결성 임베딩
- **토폴로지 정보**: 형상, 크기, 각도, 곡률 인코딩

#### Ground Truth Label 생성
1. DXF 렌더러(EZDXF) 수정
2. 각 컴포넌트 타입을 고유 색상으로 렌더링
   - Black: Contour (윤곽선)
   - Green: Text (텍스트)
   - Other colors: Dimension (치수)
3. 각 벡터의 샘플링 포인트 색상 확인
4. Majority voting으로 레이블 결정

### 3. Graph Segmentation (그래프 세그멘테이션)

#### 모델: GraphSAGE 기반

**모델 구조 (GS5 - 최종 선택)**:
```
5 GraphSAGE convolutional layers + 4 linear layers
Hidden layer nodes: [32, 64, 128, 256, 512, 256, 128, 32]
Activation: 8×ReLU + 1×Softmax
```

#### 학습 설정
- **Loss function**: Cross-entropy loss
- **Optimizer**: Adam (lr=1e-3, weight decay=5e-4)
- **Epochs**: 최대 10,000 (early stopping)
- **Batch size**: 16
- **학습 시간**: ~20시간 (GeForce RTX 2080 TI)
- **Hardware**: GPU (training), CPU (inference)

#### 비교 모델
1. **GCN** (Vanilla Graph Convolutional Network)
2. **MLP** (Multi-Layer Perceptron) - non-graph baseline
3. **PSPNet** - image-based baseline
4. **DeepLabV3** - image-based baseline
5. **Sketchgnn** - graph-based baseline

## 데이터셋

### 구성
- **총 도면 수**: 430개
- **출처**: 일본의 대형 전자상거래 시스템
- **도면 타입**:
  - Sheet metal parts (판금 부품)
  - Lathing parts (선삭 부품)
  - General machining parts (일반 가공 부품)
- **원본 형식**: DXF → Black-and-white raster images
- **컴포넌트 수**: 도면당 500~3,000개
- **분할**: Train 80% / Validation 20%

### 레이블 클래스
1. **2-class**: Text vs Non-text
2. **3-class**: Text vs Contour vs Dimension

## 실험 결과

### Experiment I: 모델 선택 (2-class)

| Model | Best Validation Accuracy |
|-------|--------------------------|
| **GS3 (Ours)** | **95.0%** |
| GCN | 93.5% |
| MLP | 85.5% |

**결론**:
- 그래프 기반 > Non-graph 기반 (>5% 향상)
- GraphSAGE > Vanilla GCN

### Experiment II: 모델 깊이 연구 (2-class)

| Model | Layers | Best Accuracy |
|-------|--------|---------------|
| GS3 | 3 conv + 2 linear | 95.0% |
| GS4 | 4 conv + 3 linear | 96.5% |
| **GS5** | **5 conv + 4 linear** | **97.8%** |

**최종 선택**: GS5 (깊이 증가에 따른 성능 향상이 5 layers에서 수렴)

### Experiment III: 3-class Segmentation

#### GS5 모델 성능 (Text/Contour/Dimension)

**Confusion Matrix**:
```
         Pred: Contour  Text  Dimension
Contour      4238       130      710
Text          105      9229      273
Dimension     761       352     9589
```

**평가 지표**:
- **Precision**: 83.03%, 95.04%, 90.70%
- **Recall**: 83.46%, 96.07%, 89.60%
- **Overall Accuracy**: 90.82%

#### 2-class Segmentation (Text/Non-text)

**GS5 모델 Confusion Matrix**:
```
         Pred: Text  Non-text
Text      21103      304
Non-text    345    13559
```

**평가 지표**:
- **Precision**: 98.38%
- **Recall**: 98.57%
- **Accuracy**: 98.48%

### Baseline 비교 (3가지 Task)

| Task | PSPNet | DeepLabV3 | Sketchgnn | **EDGNet (Ours)** |
|------|--------|-----------|-----------|-------------------|
| Text/Non-text | 96.62% | 96.87% | 94.76% | **98.48%** |
| Contour/Non-contour | 80.54% | 82.57% | 88.10% | **94.57%** |
| Text/Contour/Dimension | 79.54% | 81.64% | 84.37% | **90.82%** |

**주요 발견**:
- 모든 task에서 제안 방법이 최고 성능
- Contour vs Dimension 구분에서 그래프 기반 방법의 명확한 우위
- 그래프 기반 방법이 이미지 기반보다 안정적 (분산 낮음)

### 데이터셋 크기별 성능

- **50개 도면**: EDGNet 85%, Baseline 74-80%
- **340개 도면**: EDGNet 91%, Baseline 79-85%
- **결론**: EDGNet이 일관되게 5% 이상 우수, 안정성도 높음

## 기술적 세부사항

### Vectorization 알고리즘 비교

| Method | Junction Quality | Small Component | Branch Generation |
|--------|------------------|-----------------|-------------------|
| Medial Axis | Poor | Good | Many branches |
| Lee et al. | Good | **Poor** | Few |
| Zhang & Suen | **Poor** | Good | Few |
| **Datta & Parui** | **Good** | **Good** | **Minimal** |

### Parametric Study: n (샘플링 포인트 수)

- **테스트 범위**: n ∈ {4, 5, 6, 7, 8, 10, 12}
- **결과**: n=4와 n=12 간 유의미한 차이 없음
- **선택**: n=4 (계산 효율성, 안정성)
- **이유**: 대부분의 벡터가 직선 → 더 많은 포인트가 추가 정보 제공 안 함

### 알고리즘 복잡도

**Algorithm 1: EDGNet**
```
Input: Raster drawing Dr
Output: Labeled graph G(N, E), Y

1. Skeletonization & smoothing
2. Stroke tracing (nN strokes)
3. Bezier fitting (nN curves)
4. For each curve:
   - Sample n points
   - Calculate (5n-1) features
5. Construct graph G(N, E)
6. Predict labels: Y ← Fθ(G(N, E))
```

## 실패 사례 분석

### 주요 실패 유형

#### 1. 고립된 작은 컴포넌트
- **예시**: 파선, 지름 기호(∅), 관통 구멍 기호
- **원인**: 다른 컴포넌트와 연결되지 않음
- **결과**: 맥락 정보 없이 토폴로지 특징만으로 판단
- **해결 방안**: k-nearest neighbor edges 추가

#### 2. 다른 타입이 만나는 경계 영역
- **예시**: 윤곽선과 연장선의 연결부
- **원인**: Line-line connection vs Line-curve connection 구분 안 됨
- **해결 방안**: Edge features 추가
  - 연결 각도
  - 위치 이동
  - 곡률 변화

## 응용 분야

### 1. 자동화된 도면 해석
- 부품 형상 식별
- 치수 추출
- 제조 요구사항 파악

### 2. 견적 시스템
- 온라인 제조 플랫폼
- 자동 견적 생성
- 제조 가능성 평가

### 3. 도면 데이터베이스
- Content-based 검색
- 유사 도면 찾기
- 부품 인덱싱

### 4. CAD 통합
- 래스터 → 벡터 변환
- 파라메트릭 모델 생성
- 설계 정보 추출

## 연구의 장점

### 1. 방법론적 기여
- **새로운 벡터화 방법**: Skeletonizing + Tracing + Bezier fitting
- **그래프 표현**: 도메인 특화 nodal attributes + 맥락 정보
- **엔드투엔드 프레임워크**: 벡터화부터 분류까지 통합

### 2. 성능 우수성
- **이미지 기반 대비**: 5-11% 정확도 향상
- **안정성**: 다양한 데이터셋 크기에서 일관된 성능
- **확장성**: 다양한 AM 응용 가능

### 3. 실용성
- **산업 현장 적용 가능**: 실제 제조 도면 사용
- **자동화 효과**: 반복적이고 지루한 작업 감소
- **효율성 향상**: 검사 프로세스 간소화

## 한계점 및 향후 연구

### 현재 한계

1. **기호 인식 부재**
   - 제조 요구사항 기호
   - 기하공차 기호 (GD&T symbols)
   - 표면 거칠기 기호

2. **Edge Features 부족**
   - 연결 타입 정보 없음
   - 각도, 이동, 곡률 변화 미포함
   - True connection vs Intersection 구분 안 됨

3. **고립 컴포넌트 처리**
   - 맥락 정보 활용 불가
   - 토폴로지만으로 판단 → 낮은 정확도

4. **사용자 검증 필요**
   - 실제 사용자 테스트 미실시
   - 인터페이스 개발 필요

### 향후 연구 방향

#### 1. 기호 감지 알고리즘
- **단순 기호**: 휴리스틱 기반 방법
  - 표면 거칠기: 정삼각형 탐색
  - 관통 구멍: 일관된 형상 매칭
- **복잡한 기호**: 데이터 기반 방법
  - GD&T 기호: 텍스트 + 기호 + 박스 복합체
  - 제조 요구사항 기호

#### 2. 향상된 그래프 표현
- **Edge Features 추가**:
  - 연결 각도 (Connection angle)
  - 위치 이동 (Shift)
  - 곡률 변화 (Curvature change)
- **k-NN Edges**: 고립 컴포넌트 처리

#### 3. 고급 GNN 모델
- **Graph Attention Networks (GAT)**: Attention mechanism
- **Graph Transformers**: Self-attention
- **GINE Convolution**: Edge attributes 활용

#### 4. 사용자 인터페이스
- **기능**:
  - 도면 업로드
  - 자동 벡터화 및 예측
  - 오류 수정 인터페이스
- **장점**:
  - 검사 작업 효율화
  - 중요 정보 마킹
  - 사소한 오류만 수정

#### 5. 확장 응용
- 제조 방법 분류
- 치수 추정
- 유사도 검색
- 공정 계획

## 관련 연구 비교

### Content-based Methods
- **Hough line transform** (Mednonogov et al., 2000)
- **Pixel blocks** (Jiao et al., 2009)
- **Patch groups** (Liu et al., 2010)
- **한계**: 윤곽선만 처리, 치수/텍스트 미포함

### Graph-based Methods
- **Sketchgnn** (Yang et al., 2021): 스케치 세그멘테이션
- **OSSR-PID** (Paliwal et al., 2021): P&ID 기호 인식
- **Rica et al. (2023)**: Piping diagram zero-error digitization
- **Xie et al. (2022)**: 제조 방법 분류 (직선만 사용)

### Image-based Methods
- **PSPNet** (Zhao et al., 2017): Pyramid scene parsing
- **DeepLabV3** (Chen et al., 2017): Atrous convolution
- **한계**: 희소 픽셀, 맥락 정보 부족

## 핵심 알고리즘

### Bezier Curve Fitting
```python
# Trace의 포인트: p^j = [p_0^j, p_1^j, ..., p_{m_j-1}^j]^T
# Bernstein polynomial: B_{i,nord}^j(t) = C(nord,i) * t^i * (1-t)^(nord-i)
# Fitting: B^j * x^j = p^j
# Constraint: x_0^j = p_s^j, x_3^j = p_e^j
```

### Corner Detection
```python
θ_i = arccos((p_s - p_0) · (p_e - p_0) / |p_s - p_0| · |p_e - p_0|)
# 2nd derivative의 local maxima에서 분할
```

### Node Feature Calculation
```python
# n=4일 때
Features = [
    X0, Y0, X1, Y1, X2, Y2, X3, Y3,  # Shape (8)
    L01, L12, L23,                    # Length (3)
    L_total, L_first_last/L_total,    # Length (2)
    cos_θ1, cos_θ2,                   # Angle (2)
    κ0, κ1, κ2, κ3                    # Curvature (4)
]  # Total: 19 features
```

## 실험 환경

### 하드웨어
- **GPU**: GeForce RTX 2080 TI
- **Training**: GPU 사용
- **Inference**: CPU/GPU 모두 가능

### 소프트웨어
- **Framework**: PyTorch (PyTorch Geometric)
- **Renderer**: EZDXF (modified)
- **Language**: Python
- **Vectorization**: Custom implementation

## 주요 수식

### 그래프 표현
```
G(N, E)
N ∈ ℝ^(nN × (5n-1))
E ∈ ℤ^(nE × 2)
Y ∈ ℤ^nN
```

### 예측 함수
```
Y ← F_θ(G(N, E))
```
- θ: 학습 가능한 파라미터
- F: GraphSAGE 기반 모델

### Loss Function
```
L = CrossEntropy(Y, Y_gt)
```

## 결론

이 연구는 래스터 공학 도면 분석을 위한 새로운 프레임워크를 제시:

1. **혁신적 접근**:
   - 이미지 → 그래프 변환
   - 희소 픽셀 문제 해결
   - 맥락 정보 효과적 임베딩

2. **우수한 성능**:
   - 2-class: 98.48% 정확도
   - 3-class: 90.82% 정확도
   - Baseline 대비 5-11% 향상

3. **실용적 가치**:
   - 제조 현장 적용 가능
   - 자동화된 견적 시스템
   - 반복 작업 감소

4. **확장 가능성**:
   - 다른 도면 분석 task 적용 가능
   - 제조 방법 분류
   - 치수 추정
   - 유사도 검색

**핵심 메시지**: 그래프 기반 표현과 Graph Convolutional Networks를 활용하여 래스터 공학 도면의 자동 해석이 가능하며, 이는 제조 산업의 디지털화와 자동화에 크게 기여할 수 있습니다.
