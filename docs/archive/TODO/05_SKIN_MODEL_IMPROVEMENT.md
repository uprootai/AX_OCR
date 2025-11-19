# Skin Model 개선 계획

> 작성일: 2025-11-13
> 현재 상태: 🟡 규칙 기반 (Rule-based)
> 목표: ⭐ 머신러닝 기반으로 전환
> 우선순위: 🟢 Priority 3 (장기 과제)

---

## 📊 현재 상태 분석

### 현재 구현: 공학 휴리스틱

**파일**: `skin-model-api/api_server.py` (78-133줄)

```python
def predict_tolerance(material, mfg_process, dimensions, gdt_symbols, corr_length):
    """
    규칙 기반 공차 예측 (Rule-based)
    ❌ FEM 시뮬레이션 아님
    ❌ 머신러닝 아님
    ✅ 단순 룩업 테이블 + 선형 계산
    """

    # 1. 재질별 고정 계수
    material_factors = {
        "Steel": 1.0,
        "Aluminum": 0.8,
        "Titanium": 1.5,
        "Plastic": 0.6
    }

    # 2. 공정별 기본 공차
    process_tolerances = {
        "machining": {"flatness": 0.02, "cylindricity": 0.03, ...},
        "casting": {"flatness": 0.15, "cylindricity": 0.20, ...},
        "forging": {"flatness": 0.10, "cylindricity": 0.12, ...},
        "additive": {"flatness": 0.08, "cylindricity": 0.10, ...}
    }

    # 3. 선형 계산
    base_tolerance = process_tolerances.get(mfg_process, {...}).get(gdt_type, 0.05)
    material_factor = material_factors.get(material, 1.0)
    size_factor = max(dimensions) / 100.0
    correlation_factor = corr_length / 10.0

    predicted_tolerance = base_tolerance * material_factor * size_factor * correlation_factor

    # 4. 임계값 기반 점수 (단순 if-else)
    if predicted_tolerance < 0.05:
        feasibility_score = 0.65  # Hard
    elif predicted_tolerance < 0.10:
        feasibility_score = 0.80  # Medium
    else:
        feasibility_score = 0.92  # Easy

    return {
        "feasibility_score": feasibility_score,
        "predicted_tolerance": predicted_tolerance,
        ...
    }
```

### 왜 FEM이 아닌가?

| 특징 | 현재 구현 | 실제 FEM |
|------|----------|----------|
| 물리 시뮬레이션 | ❌ 없음 | ✅ 있음 (Stress, Strain) |
| 경계 조건 | ❌ 없음 | ✅ 있음 (Constraints, Loads) |
| 메쉬 생성 | ❌ 없음 | ✅ 있음 (Tetrahedral, Hexahedral) |
| 솔버 | ❌ 없음 | ✅ 있음 (Linear, Nonlinear) |
| 계산 복잡도 | O(1) (상수 시간) | O(n³) ~ O(n⁴) |
| 결과 | 단일 스칼라 값 | 3D 변형 필드 |

**결론**: 현재 구현은 **공학적 경험 법칙 (Engineering Heuristics)**

---

## 🎯 개선 목표

### 정확도 향상 목표

| 항목 | 현재 | 목표 | 개선 폭 |
|------|------|------|---------|
| **Feasibility Score 정확도** | ~70% | 85-90% | +15-20% |
| **Tolerance 예측 RMSE** | ? | < 0.03mm | - |
| **처리 속도** | <1ms | <50ms | - |

### 기술 목표

1. **규칙 기반 → 데이터 기반 전환**
2. **단순 if-else → 머신러닝 모델**
3. **고정 계수 → 학습된 가중치**
4. **단일 점수 → 신뢰 구간 제공**

---

## 🚀 개선 옵션

### Option 1: 머신러닝 회귀 모델 (추천)

#### 1.1 개요

**장점**:
- ✅ 빠른 구현 (2-3일)
- ✅ 빠른 추론 (<10ms)
- ✅ 해석 가능성 높음
- ✅ 적은 데이터로 학습 가능 (500-1000 샘플)

**단점**:
- ⚠️ 물리적 제약 보장 안 됨
- ⚠️ 외삽(extrapolation) 성능 제한적

#### 1.2 모델 선택지

**A. Gradient Boosting (XGBoost, LightGBM, CatBoost)**

```python
import xgboost as xgb
from sklearn.model_selection import train_test_split

# 특징 추출
features = [
    "material_id",  # Categorical: Steel=0, Aluminum=1, ...
    "process_id",  # Categorical: machining=0, casting=1, ...
    "max_dimension",  # Numeric
    "min_dimension",  # Numeric
    "avg_dimension",  # Numeric
    "num_gdt_symbols",  # Count
    "flatness_required",  # Binary
    "cylindricity_required",  # Binary
    "correlation_length",  # Numeric
    "surface_area",  # Numeric (estimated)
    "volume",  # Numeric (estimated)
]

# 타겟
targets = [
    "feasibility_score",  # Regression (0-1)
    "predicted_tolerance",  # Regression (mm)
]

# 모델 학습
model = xgb.XGBRegressor(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)

model.fit(X_train, y_train)

# 특징 중요도 분석
import matplotlib.pyplot as plt
xgb.plot_importance(model)
plt.show()
```

**예상 성능**:
- 정확도: 85-90% (실제 제조 결과 대비)
- 속도: 1-5ms
- 데이터 요구량: 500-1000 샘플

**B. Neural Network (MLP)**

```python
import torch
import torch.nn as nn

class TolerancePredictorNN(nn.Module):
    def __init__(self, input_dim, hidden_dims=[64, 32, 16]):
        super().__init__()
        layers = []

        prev_dim = input_dim
        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.ReLU(),
                nn.BatchNorm1d(hidden_dim),
                nn.Dropout(0.2)
            ])
            prev_dim = hidden_dim

        layers.append(nn.Linear(prev_dim, 2))  # 2 outputs: score, tolerance
        self.network = nn.Sequential(*layers)

    def forward(self, x):
        return self.network(x)

# 학습
model = TolerancePredictorNN(input_dim=11)
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
criterion = nn.MSELoss()

for epoch in range(100):
    optimizer.zero_grad()
    outputs = model(X_train)
    loss = criterion(outputs, y_train)
    loss.backward()
    optimizer.step()
```

**예상 성능**:
- 정확도: 80-85%
- 속도: 2-10ms
- 데이터 요구량: 1000-2000 샘플

#### 1.3 데이터 수집 방법

**A. 역사적 데이터 (Historical Data)**

```sql
-- 실제 제조 이력에서 데이터 추출
SELECT
    part_id,
    material,
    manufacturing_process,
    max_dimension,
    gdt_symbols,
    actual_tolerance_achieved,  -- 실제 측정값
    manufacturing_success,  -- 성공 여부
    manufacturing_difficulty  -- 난이도 (1-5)
FROM manufacturing_history
WHERE measurement_date > '2023-01-01'
```

**B. 시뮬레이션 데이터 (Synthetic)**

```python
# 규칙 기반 모델로 초기 데이터 생성
def generate_synthetic_data(n_samples=1000):
    data = []
    for _ in range(n_samples):
        material = random.choice(["Steel", "Aluminum", "Titanium", "Plastic"])
        process = random.choice(["machining", "casting", "forging", "additive"])
        dimensions = [random.uniform(10, 500) for _ in range(3)]

        # 현재 규칙 기반 모델로 라벨 생성
        result = predict_tolerance_rule_based(material, process, dimensions, ...)

        # 노이즈 추가 (현실성)
        result["feasibility_score"] += random.gauss(0, 0.05)
        result["predicted_tolerance"] += random.gauss(0, 0.01)

        data.append({**features, **result})

    return pd.DataFrame(data)
```

**C. 전문가 라벨링 (Expert Annotation)**

```python
# 도면 이미지 + 전문가 평가
annotations = [
    {
        "drawing_id": "DWG-001",
        "material": "Steel",
        "process": "machining",
        "dimensions": [100, 50, 20],
        "gdt_symbols": ["flatness", "parallelism"],
        "expert_feasibility": 0.85,  # 전문가 평가
        "expert_tolerance": 0.03,
        "expert_difficulty": "Medium"
    },
    # ... 100-200 샘플 (전문가 시간 필요)
]
```

#### 1.4 구현 단계

**Phase 1: 데이터 준비 (1일)**

1. 특징 설계 (Feature Engineering)
2. 데이터 수집 (Historical + Synthetic)
3. 데이터 정제 및 검증
4. Train/Val/Test 분할 (70/15/15)

**Phase 2: 모델 학습 (2일)**

1. Baseline 모델 학습 (Linear Regression)
2. XGBoost 모델 학습 및 튜닝
3. Neural Network 학습 (선택적)
4. 앙상블 (Ensemble) 시도

**Phase 3: 평가 및 배포 (1일)**

1. 테스트 세트 평가
2. 특징 중요도 분석
3. API 엔드포인트 업데이트
4. A/B 테스트 설정

**총 소요**: 4-5일

---

### Option 2: FEM API 통합 (고급)

#### 2.1 개요

**장점**:
- ✅ 물리적 정확도 매우 높음 (95%+)
- ✅ 응력/변형 상세 분석
- ✅ 복잡한 형상 처리 가능

**단점**:
- ⚠️ 매우 느림 (10초 ~ 10분)
- ⚠️ 복잡한 구현 (2-3주)
- ⚠️ 고비용 (상용 솔버 라이선스)
- ⚠️ 전문 지식 필요

#### 2.2 FEM 솔버 선택

**A. Open Source 솔버**

| 솔버 | 라이선스 | 언어 | 성능 | 학습 곡선 |
|------|----------|------|------|----------|
| **CalculiX** | GPL | Fortran | 중상 | 높음 |
| **FEniCS** | LGPL | Python | 중 | 중간 |
| **OpenSees** | BSD | C++ | 상 | 높음 |
| **Code_Aster** | GPL | Python | 중상 | 중간 |

**B. 상용 솔버 API**

| 솔버 | 비용 | API | 클라우드 | 정확도 |
|------|------|-----|---------|--------|
| **Ansys Cloud** | $$$$ | REST API | ✅ | 최상 |
| **Abaqus Cloud** | $$$$ | Python API | ✅ | 최상 |
| **SimScale** | $$$ | REST API | ✅ | 상 |
| **OnScale** | $$$ | REST API | ✅ | 상 |

#### 2.3 구현 예시 (FEniCS)

```python
from dolfin import *
import numpy as np

def fem_tolerance_prediction(geometry, material, process, boundary_conditions):
    """
    FEM 기반 공차 예측
    """

    # 1. 메쉬 생성
    mesh = generate_mesh_from_geometry(geometry)

    # 2. 함수 공간 정의
    V = VectorFunctionSpace(mesh, "CG", 1)  # Continuous Galerkin

    # 3. 재질 속성
    material_props = {
        "Steel": {"E": 200e9, "nu": 0.3},  # Young's modulus, Poisson's ratio
        "Aluminum": {"E": 70e9, "nu": 0.33},
        "Titanium": {"E": 110e9, "nu": 0.34}
    }

    E = material_props[material]["E"]
    nu = material_props[material]["nu"]

    # 4. 응력-변형 관계 (Hooke's law)
    mu = E / (2 * (1 + nu))
    lambda_ = E * nu / ((1 + nu) * (1 - 2 * nu))

    def sigma(u):
        return lambda_ * tr(sym(grad(u))) * Identity(3) + 2 * mu * sym(grad(u))

    # 5. 경계 조건
    bc_fixed = DirichletBC(V, Constant((0, 0, 0)), boundary_conditions["fixed"])
    bc_load = DirichletBC(V, boundary_conditions["load"], boundary_conditions["load_face"])

    # 6. 변분 문제 (Variational problem)
    u = TrialFunction(V)
    v = TestFunction(V)
    a = inner(sigma(u), sym(grad(v))) * dx
    L = dot(Constant((0, 0, 0)), v) * dx

    # 7. 솔버
    u_sol = Function(V)
    solve(a == L, u_sol, [bc_fixed, bc_load])

    # 8. 변형 계산
    displacement = u_sol.compute_vertex_values(mesh)
    max_displacement = np.max(np.abs(displacement))

    # 9. 공차 예측
    predicted_tolerance = max_displacement * process_factor(process)

    # 10. 제조 가능성 점수
    tolerance_threshold = get_process_capability(process)
    feasibility_score = min(1.0, tolerance_threshold / predicted_tolerance)

    return {
        "feasibility_score": feasibility_score,
        "predicted_tolerance": predicted_tolerance,
        "max_displacement": max_displacement,
        "stress_distribution": sigma(u_sol),  # 3D 응력 필드
        "processing_time": solve_time
    }
```

#### 2.4 클라우드 FEM API 예시 (SimScale)

```python
import requests

def simscale_fem_analysis(geometry_file, material, loads):
    """
    SimScale Cloud FEM API 사용
    """

    # 1. 프로젝트 생성
    project_response = requests.post(
        "https://api.simscale.com/v0/projects",
        headers={"X-API-KEY": SIMSCALE_API_KEY},
        json={"name": "Tolerance Analysis"}
    )
    project_id = project_response.json()["projectId"]

    # 2. 지오메트리 업로드
    with open(geometry_file, "rb") as f:
        geo_response = requests.post(
            f"https://api.simscale.com/v0/projects/{project_id}/geometries",
            headers={"X-API-KEY": SIMSCALE_API_KEY},
            files={"file": f}
        )
    geometry_id = geo_response.json()["geometryId"]

    # 3. 시뮬레이션 설정
    simulation = {
        "name": "Static Analysis",
        "type": "STATIC",
        "model": {
            "material": material,
            "loads": loads,
            "boundaryConditions": {...}
        }
    }

    sim_response = requests.post(
        f"https://api.simscale.com/v0/projects/{project_id}/simulations",
        headers={"X-API-KEY": SIMSCALE_API_KEY},
        json=simulation
    )
    simulation_id = sim_response.json()["simulationId"]

    # 4. 실행
    run_response = requests.post(
        f"https://api.simscale.com/v0/projects/{project_id}/simulations/{simulation_id}/runs",
        headers={"X-API-KEY": SIMSCALE_API_KEY}
    )
    run_id = run_response.json()["runId"]

    # 5. 결과 대기 (폴링)
    while True:
        status_response = requests.get(
            f"https://api.simscale.com/v0/projects/{project_id}/simulations/{simulation_id}/runs/{run_id}",
            headers={"X-API-KEY": SIMSCALE_API_KEY}
        )
        status = status_response.json()["status"]

        if status == "FINISHED":
            break
        elif status == "FAILED":
            raise Exception("Simulation failed")

        time.sleep(10)  # 10초 대기

    # 6. 결과 다운로드
    results_response = requests.get(
        f"https://api.simscale.com/v0/projects/{project_id}/simulations/{simulation_id}/runs/{run_id}/results",
        headers={"X-API-KEY": SIMSCALE_API_KEY}
    )

    return results_response.json()
```

**비용 예상**:
- SimScale: $0.50 - $2.00 per simulation
- 월 100회 실행 시: $50 - $200/month

---

### Option 3: ISO 표준 기반 룩업 테이블 (간단)

#### 3.1 개요

**장점**:
- ✅ 매우 빠른 구현 (1일)
- ✅ 표준 준수
- ✅ 해석 가능성 100%

**단점**:
- ⚠️ 정확도 중간 (~75%)
- ⚠️ 유연성 부족

#### 3.2 ISO 2768 - General Tolerances

```python
# ISO 2768-1: Linear dimensions (mm)
ISO_2768_LINEAR = {
    "f": {  # Fine
        (0.5, 3): 0.05,
        (3, 6): 0.05,
        (6, 30): 0.1,
        (30, 120): 0.15,
        (120, 400): 0.2,
        (400, 1000): 0.3,
        (1000, 2000): 0.5
    },
    "m": {  # Medium
        (0.5, 3): 0.1,
        (3, 6): 0.1,
        (6, 30): 0.2,
        (30, 120): 0.3,
        (120, 400): 0.5,
        (400, 1000): 0.8,
        (1000, 2000): 1.2
    },
    "c": {  # Coarse
        (0.5, 3): 0.2,
        (3, 6): 0.3,
        (6, 30): 0.5,
        (30, 120): 0.8,
        (120, 400): 1.2,
        (400, 1000): 2.0,
        (1000, 2000): 3.0
    }
}

# ISO 2768-2: Geometric tolerances
ISO_2768_GEOMETRIC = {
    "flatness": {
        "H": {(0, 10): 0.02, (10, 30): 0.05, (30, 100): 0.1, ...},
        "K": {(0, 10): 0.05, (10, 30): 0.1, (30, 100): 0.2, ...},
        "L": {(0, 10): 0.1, (10, 30): 0.2, (30, 100): 0.4, ...}
    },
    "cylindricity": {...},
    "parallelism": {...}
}

def iso_based_prediction(dimensions, gdt_symbols, tolerance_class="m"):
    """
    ISO 2768 표준 기반 예측
    """
    max_dim = max(dimensions)

    # 선형 치수 공차
    for (lower, upper), tolerance in ISO_2768_LINEAR[tolerance_class].items():
        if lower <= max_dim < upper:
            linear_tolerance = tolerance
            break

    # 기하 공차
    geometric_tolerances = {}
    for gdt in gdt_symbols:
        for (lower, upper), tolerance in ISO_2768_GEOMETRIC[gdt][tolerance_class].items():
            if lower <= max_dim < upper:
                geometric_tolerances[gdt] = tolerance
                break

    # 제조 가능성 점수 (표준 준수 시 높음)
    feasibility_score = 0.90 if tolerance_class in ["m", "c"] else 0.75

    return {
        "feasibility_score": feasibility_score,
        "predicted_tolerance": linear_tolerance,
        "geometric_tolerances": geometric_tolerances,
        "iso_standard": "ISO 2768-1:1989"
    }
```

---

## 📋 권장 로드맵

### 단계별 구현 (Progressive Enhancement)

#### Step 1: ISO 표준 기반 (1일) - 즉시 배포

- 현재 규칙 기반 → ISO 2768 기반으로 교체
- 정확도: 70% → 75% (+5%)
- 표준 준수 보장

#### Step 2: 머신러닝 모델 (1주일) - 메인 개선

- XGBoost 모델 학습
- 정확도: 75% → 85-90% (+10-15%)
- 특징 중요도 분석
- 신뢰 구간 제공

#### Step 3: 앙상블 (2일) - 추가 개선

- ISO + ML + 규칙 기반 앙상블
- 투표 또는 가중 평균
- 정확도: 90% → 92% (+2%)

#### Step 4: FEM API (선택적, 2-3주) - 고급 기능

- 클라우드 FEM API 통합 (SimScale)
- 복잡한 형상 처리
- 상세 응력 분석 제공
- "고급 분석" 옵션으로 제공

---

## 📊 비용-효과 분석

| 옵션 | 구현 시간 | 정확도 | 속도 | 비용 | 추천도 |
|------|----------|--------|------|------|--------|
| **ISO 표준** | 1일 | 75% | <1ms | $0 | ⭐⭐⭐ |
| **ML (XGBoost)** | 4-5일 | 85-90% | <10ms | $0 | ⭐⭐⭐⭐⭐ |
| **Neural Network** | 5-7일 | 80-85% | <10ms | $0 | ⭐⭐⭐⭐ |
| **FEM (Open)** | 2-3주 | 90-95% | 10s-10m | $0 | ⭐⭐ |
| **FEM (Cloud)** | 1-2주 | 95%+ | 1-5m | $50-200/m | ⭐⭐⭐ |

**최종 추천**: **Step 1 (ISO) + Step 2 (ML XGBoost)**

---

## 📝 구현 체크리스트

- [ ] **Phase 1: ISO 표준 구현 (1일)**
  - [ ] ISO 2768-1 룩업 테이블 작성
  - [ ] ISO 2768-2 기하 공차 추가
  - [ ] API 엔드포인트 업데이트
  - [ ] 단위 테스트 작성

- [ ] **Phase 2: 데이터 준비 (2일)**
  - [ ] 특징 설계
  - [ ] 역사적 데이터 수집
  - [ ] Synthetic 데이터 생성
  - [ ] 데이터 검증

- [ ] **Phase 3: ML 모델 학습 (2일)**
  - [ ] Baseline (Linear Regression)
  - [ ] XGBoost 학습 및 튜닝
  - [ ] 교차 검증
  - [ ] 모델 저장

- [ ] **Phase 4: 배포 (1일)**
  - [ ] API 통합
  - [ ] 성능 테스트
  - [ ] A/B 테스트 설정
  - [ ] 문서 업데이트

---

**총 예상 소요**: 6-7일 (ISO + ML)

**관련 문서**:
- `01_CURRENT_STATUS_OVERVIEW.md`: 전체 시스템 현황
- `08_LONG_TERM_IMPROVEMENTS.md`: 장기 개선 과제
