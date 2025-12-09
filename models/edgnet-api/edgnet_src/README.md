# EDGNet: Engineering Drawing Graph Network

## 개요
Carnegie Mellon University 논문 "Component Segmentation of Engineering Drawings Using Graph Convolutional Networks" 구현

## 논문 정보
- **저자**: Wentai Zhang et al., Carnegie Mellon University
- **arXiv**: 2212.00290v2
- **성능**: 2-class (text/non-text) 98.48%, 3-class 90.82%

## 시스템 구조

```
Raster Drawing → Vectorization → Graph Construction → GraphSAGE → Labeled Components
```

### 1. Vectorization (벡터화)
- **Thinning**: Datta & Parui 알고리즘
- **Tracing**: Junction/endpoint 기반 궤적 추적
- **Bezier Fitting**: 3차 베지어 곡선으로 피팅

### 2. Graph Construction (그래프 구성)
- **Nodes**: 각 컴포넌트의 19차원 특징 벡터
  - Shape (8): XY 좌표
  - Length (5): 길이 정보
  - Angle (2): 각도 정보
  - Curvature (4): 곡률 정보
- **Edges**: 컴포넌트 간 연결성

### 3. GraphSAGE Classification
- 노드 분류: Contour / Text / Dimension
- 90.82% 정확도 달성 (3-class)

## 설치

```bash
cd /home/uproot/ax/dev/edgnet
pip install -r requirements.txt
```

## 사용법

```bash
# 도면 벡터화
python vectorize.py --input drawing.png --output vectors.json

# 그래프 구축
python build_graph.py --input vectors.json --output graph.pkl

# 분류
python classify.py --input graph.pkl --output results.json
```

## 프로젝트 구조

```
edgnet/
├── vectorization/      # 벡터화 모듈
│   ├── thinning.py    # 세선화 알고리즘
│   ├── tracing.py     # 궤적 추적
│   └── bezier.py      # 베지어 피팅
├── graph/             # 그래프 구성
│   ├── features.py    # 특징 추출
│   └── builder.py     # 그래프 빌더
├── models/            # 딥러닝 모델
│   └── graphsage.py   # GraphSAGE 구현
└── utils/             # 유틸리티
    └── visualize.py   # 시각화
```

## 목표
업루트 AX 프로젝트의 도면 세그멘테이션 기능 제공
- MaP 0.88, Accuracy 0.9 달성 (4차년도)
- eDOCr2와 통합하여 엔드투엔드 파이프라인 구축
