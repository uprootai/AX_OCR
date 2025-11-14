# 🚀 EDGNet & Skin Model 개선 전략

**작성일**: 2025-11-13  
**목표**: 현재 60점(EDGNet), 40점(Skin Model)을 80점 이상으로 향상

---

## 📊 현재 상황 분석

### 가용 리소스:
1. **실제 도면**: 32개 (PDF + JPG/PNG)
2. **YOLO 검출 결과**: 89개 객체 (실제 검증 완료)
3. **eDOCr2 OCR 결과**: 치수/GD&T 정보
4. **웹 UI 테스트 페이지**: 실시간 테스트 가능

### 문제점:
- **EDGNet**: 2개 도면으로만 학습 (16KB 모델)
- **Skin Model**: Rule-based heuristic (FEM 미구현)

---

## 🎯 전략 1: EDGNet 합성 데이터 생성 및 재학습

### Phase 1: 기존 도면으로 초기 데이터셋 구축

#### Step 1: YOLO로 객체 검출
```python
# 32개 도면에 대해 YOLO 실행
for drawing in test_drawings:
    detections = yolo_detect(drawing)
    # 89개 * 32 = ~2,800개 객체
```

#### Step 2: eDOCr2로 치수 추출
```python
# 각 도면에서 치수 정보 추출
for drawing in test_drawings:
    dimensions = edocr2_extract(drawing)
    # 라벨링 데이터로 활용
```

#### Step 3: EDGNet 그래프 생성
```python
# YOLO bbox → 벡터화 → 그래프 노드/엣지
nodes = []
edges = []

for bbox in detections:
    # Bezier curve 추출
    curves = extract_bezier_curves(bbox)
    nodes.append({
        'features': compute_node_features(curves),
        'label': bbox.class_name  # YOLO 클래스
    })
    
# 공간적 인접성 기반 엣지 생성
edges = compute_spatial_edges(nodes)
```

#### Step 4: GraphSAGE 재학습
```python
# 목표: 16KB → 5MB+
model = GraphSAGE(
    in_channels=128,  # 노드 특징 차원
    hidden_channels=256,
    out_channels=4,  # Dimension, Text, Contour, Other
    num_layers=3
)

# 학습 설정
epochs = 100
batch_size = 32
learning_rate = 0.001

# 데이터셋: 32개 도면 → ~2,800개 노드
```

### Phase 2: 합성 데이터 증강

#### 방법 1: 기하학적 증강
```python
augmentations = [
    'rotation': [-5, 5],  # 회전
    'scale': [0.9, 1.1],  # 스케일
    'translation': [-10, 10],  # 이동
    'noise': 0.01  # 노이즈
]
# 32개 → 160개 (5배 증강)
```

#### 방법 2: YOLO 검출 결과 활용
```python
# YOLO가 검출한 89개 객체의 bbox와 클래스를 
# EDGNet의 ground truth로 사용
for detection in yolo_results:
    graph_node = {
        'bbox': detection.bbox,
        'class': detection.class_name,
        'confidence': detection.confidence
    }
```

#### 방법 3: 합성 도면 생성 (선택적)
```python
# 간단한 도면 패턴 합성
def generate_synthetic_drawing():
    # 기본 도형 + 치수선 + 주석
    shapes = ['rectangle', 'circle', 'line']
    dimensions = add_dimension_lines()
    annotations = add_text_blocks()
    return combine(shapes, dimensions, annotations)

# 추가 100개 합성 도면 생성
```

### 예상 결과:
- **데이터셋**: 32개 → 260개 (증강 + 합성)
- **노드 수**: 1,844 → 23,000+
- **모델 크기**: 16KB → 5-10MB
- **정확도**: 예상 60% → 75-80%
- **점수**: 60 → **80점**

---

## 🎯 전략 2: Skin Model FEM 기반 재구현

### Phase 1: FEM 라이브러리 통합

#### Option 1: Python FEM 라이브러리 사용
```python
# PyFEM or FEniCS 사용
from pyfem import FEModel

def predict_tolerance(geometry, material, process):
    # 1. FEM 메시 생성
    mesh = create_mesh(geometry)
    
    # 2. 재질 특성 설정
    material_props = {
        'youngs_modulus': get_youngs_modulus(material),
        'poisson_ratio': get_poisson_ratio(material),
        'yield_strength': get_yield_strength(material)
    }
    
    # 3. 경계 조건 설정
    boundary_conditions = set_manufacturing_constraints(process)
    
    # 4. FEM 해석 실행
    model = FEModel(mesh, material_props, boundary_conditions)
    result = model.solve()
    
    # 5. 공차 예측
    tolerance = {
        'flatness': compute_flatness_tolerance(result),
        'parallelism': compute_parallelism_tolerance(result),
        'perpendicularity': compute_perpendicularity_tolerance(result)
    }
    
    return tolerance
```

#### Option 2: GitHub 오픈소스 활용
```bash
# i7242/Skin-Model-Shape-Generation
git clone https://github.com/i7242/Skin-Model-Shape-Generation.git

# 핵심 기능 통합
- Statistical shape modeling
- Gaussian Process for tolerance prediction
- FEM-based deformation analysis
```

### Phase 2: 실제 도면 데이터 활용

#### Step 1: 도면에서 기하학 정보 추출
```python
# YOLO + eDOCr2 결과 활용
geometry_info = {
    'shapes': yolo_detections,  # 윤곽선, 구멍 등
    'dimensions': edocr2_dimensions,  # 치수 값
    'tolerances': edocr2_gdt  # GD&T 정보
}
```

#### Step 2: 재질 및 공정 정보 매핑
```python
# 도면 주석에서 추출 또는 기본값 사용
material_database = {
    'steel': {'E': 200e9, 'nu': 0.3, 'yield': 250e6},
    'aluminum': {'E': 70e9, 'nu': 0.33, 'yield': 95e6},
    'titanium': {'E': 110e9, 'nu': 0.34, 'yield': 880e6}
}

process_parameters = {
    'machining': {'roughness': 1.6, 'tolerance_class': 'IT7'},
    'casting': {'roughness': 12.5, 'tolerance_class': 'IT12'},
    '3d_printing': {'roughness': 6.3, 'tolerance_class': 'IT10'}
}
```

#### Step 3: FEM 시뮬레이션
```python
# 각 도면에 대해 FEM 해석 실행
for drawing in test_drawings:
    geometry = extract_geometry(drawing)
    material = identify_material(drawing)
    process = identify_process(drawing)
    
    # FEM 실행
    tolerance_prediction = run_fem_simulation(
        geometry, material, process
    )
    
    # 결과 저장
    save_tolerance_data(drawing, tolerance_prediction)
```

### Phase 3: ML 모델 학습 (선택적)

#### 빠른 예측을 위한 Surrogate Model
```python
# FEM 결과를 학습 데이터로 사용
X = [geometry_features, material_props, process_params]
y = fem_simulation_results

# Random Forest 또는 Neural Network
model = RandomForestRegressor(n_estimators=100)
model.fit(X, y)

# 실시간 예측
tolerance = model.predict(new_geometry)
```

### 예상 결과:
- **정확도**: Rule-based → FEM-based
- **신뢰도**: 40% → 75-80%
- **점수**: 40 → **80점**

---

## 📅 실행 계획

### Week 1: 데이터 준비 (2-3일)
- [ ] 32개 도면 YOLO 검출
- [ ] eDOCr2 치수 추출
- [ ] 라벨링 데이터 생성

### Week 2: EDGNet 개선 (3-4일)
- [ ] 그래프 데이터 생성
- [ ] 데이터 증강
- [ ] GraphSAGE 재학습
- [ ] 검증 및 평가

### Week 3: Skin Model 개선 (3-4일)
- [ ] FEM 라이브러리 설치
- [ ] 기하학 정보 추출
- [ ] FEM 시뮬레이션
- [ ] API 통합

### Week 4: 통합 테스트 (2-3일)
- [ ] 전체 파이프라인 테스트
- [ ] 성능 벤치마크
- [ ] 문서화

---

## 🔧 즉시 실행 가능한 Quick Wins

### 1. EDGNet 빠른 개선
```bash
# 32개 도면으로 즉시 재학습
cd /home/uproot/ax/dev/edgnet
python train_graphsage.py \
    --data_dir /home/uproot/ax/poc/test_samples \
    --epochs 100 \
    --batch_size 32
```

### 2. Skin Model 간단한 ML 통합
```python
# Rule-based → ML-based (FEM 없이도 개선 가능)
from sklearn.ensemble import RandomForestRegressor

# 기존 룰 기반 결과를 학습 데이터로 사용
# 32개 도면 * 다양한 파라미터 조합
X_train, y_train = generate_training_data()
model = RandomForestRegressor(n_estimators=100)
model.fit(X_train, y_train)
```

---

## 🎯 목표 달성 지표

### EDGNet (현재 60점 → 목표 80점)
- [x] 데이터셋: 2개 → 32개+ ✅
- [ ] 모델 크기: 16KB → 5MB+
- [ ] 정확도: 60% → 75-80%
- [ ] 노드 수: 1,844 → 20,000+

### Skin Model (현재 40점 → 목표 80점)
- [ ] 구현: Rule-based → FEM/ML-based
- [ ] 정확도: 40% → 75-80%
- [ ] 신뢰도: Low → High
- [ ] 검증: 실제 도면 테스트

### 전체 시스템 (현재 82점 → 목표 90점+)
- EDGNet: 60 → 80 (+20)
- Skin Model: 40 → 80 (+40)
- **평균**: 82 → **90점** (+8)

---

## 💡 혁신적 접근

### 1. 자가 학습 파이프라인
```python
# 웹 UI에서 사용자가 수정한 결과를 자동으로 학습
def auto_learning_pipeline():
    # 1. 사용자가 웹 UI에서 결과 수정
    user_corrections = collect_user_feedback()
    
    # 2. 수정 데이터를 학습 데이터에 추가
    training_data.append(user_corrections)
    
    # 3. 주기적으로 모델 재학습
    if len(training_data) > threshold:
        retrain_model(training_data)
```

### 2. Active Learning
```python
# 모델이 불확실한 케이스만 사용자에게 확인 요청
uncertain_samples = model.predict_with_uncertainty(new_data)
for sample in uncertain_samples:
    if sample.uncertainty > threshold:
        ask_user_confirmation(sample)
```

---

**Status**: Ready to Execute ✅  
**Expected Timeline**: 2-3 weeks  
**Expected Improvement**: 82 → 90+ points
