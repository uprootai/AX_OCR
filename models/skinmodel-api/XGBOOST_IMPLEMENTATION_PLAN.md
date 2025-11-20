# Skin Model API: XGBoost ML Implementation Plan

> **목표**: 규칙 기반 휴리스틱 → XGBoost ML 모델로 전환 (정확도 85-90% 목표)

---

## 📋 Current State

### Current Implementation (Rule-based Heuristic)

**위치**: `skinmodel-api/api_server.py:127-244`

**방식**:
- 재질별 공차 계수 (material_factors)
- 제조 공정별 기본 공차 (process_tolerances)
- 치수 크기 보정 (size_factor)
- Correlation length 영향 (corr_factor)

**문제점**:
- 정확도 제한적 (~60-70%)
- 복잡한 상호작용 반영 불가
- 실제 제조 데이터와 괴리
- 확장성 낮음 (새로운 재질/공정 추가 어려움)

**장점**:
- 해석 가능성 높음
- 즉시 사용 가능 (학습 데이터 불필요)
- 추론 속도 빠름

---

## 🎯 Target State

### XGBoost ML Model

**예상 정확도**: 85-90% (RMSE 기준)
**학습 데이터 필요량**: 최소 500-1,000개 샘플
**추론 속도**: <10ms per prediction

**Input Features** (총 10개):
1. `material_id` (categorical → one-hot)
2. `youngs_modulus` (float, GPa)
3. `poisson_ratio` (float)
4. `density` (float, kg/m³)
5. `manufacturing_process_id` (categorical → one-hot)
6. `max_dimension` (float, mm)
7. `min_dimension` (float, mm)
8. `avg_dimension` (float, mm)
9. `num_dimensions` (int)
10. `correlation_length` (float)

**Output Targets** (총 4개):
1. `flatness` (float, mm)
2. `cylindricity` (float, mm)
3. `position` (float, mm)
4. `perpendicularity` (float, mm)

**Model Architecture**:
- Multi-output XGBoost regressor (4 models, one per target)
- Hyperparameters: max_depth=6, n_estimators=300, learning_rate=0.05

---

## 📊 Training Data Requirements

### Data Sources

1. **Historical Manufacturing Data** (최우선)
   - 실제 제조 데이터 (CMM 측정 결과)
   - 공정별 품질 기록
   - 추정 데이터량: 1,000-5,000 샘플

2. **FEM Simulation Data** (대안)
   - 기존 FEM 시뮬레이션 결과 활용
   - 다양한 재질/공정 조합 시뮬레이션
   - 추정 데이터량: 무한 (시뮬레이션 가능)

3. **Rule-based Augmentation** (최후 수단)
   - 현재 규칙 기반 모델 + 노이즈 추가
   - Synthetic data generation
   - 추정 데이터량: 무한

### Data Collection Script

**위치**: `scripts/collect_skinmodel_training_data.py` (생성 필요)

```python
#!/usr/bin/env python3
"""
Skin Model 학습 데이터 수집 스크립트
"""
import pandas as pd
import numpy as np
from pathlib import Path

def collect_from_manufacturing_logs():
    """실제 제조 데이터 수집"""
    # TODO: 실제 데이터베이스/파일에서 수집
    pass

def generate_synthetic_data(n_samples=1000):
    """합성 데이터 생성 (Rule-based + noise)"""
    data = []

    materials = [
        {"name": "Steel", "youngs": 210, "poisson": 0.3, "density": 7850},
        {"name": "Aluminum", "youngs": 70, "poisson": 0.33, "density": 2700},
        {"name": "Titanium", "youngs": 110, "poisson": 0.34, "density": 4500},
    ]

    processes = ["machining", "casting", "3d_printing"]

    for i in range(n_samples):
        mat = np.random.choice(materials)
        proc = np.random.choice(processes)

        # Random dimensions
        num_dims = np.random.randint(3, 10)
        dims = np.random.uniform(10, 500, num_dims)

        # Calculate targets using rule-based + noise
        # ... (현재 규칙 기반 로직 + gaussian noise)

        data.append({
            "material_name": mat["name"],
            "youngs_modulus": mat["youngs"],
            "poisson_ratio": mat["poisson"],
            "density": mat["density"],
            "manufacturing_process": proc,
            "max_dimension": dims.max(),
            "min_dimension": dims.min(),
            "avg_dimension": dims.mean(),
            "num_dimensions": num_dims,
            "correlation_length": np.random.uniform(0.5, 3.0),
            "flatness": ...,  # Rule-based + noise
            "cylindricity": ...,
            "position": ...,
            "perpendicularity": ...
        })

    return pd.DataFrame(data)

if __name__ == "__main__":
    # 1. 실제 데이터 수집 시도
    real_data = collect_from_manufacturing_logs()

    if real_data is None or len(real_data) < 100:
        # 2. 합성 데이터 생성
        print("⚠️ Insufficient real data, generating synthetic data...")
        synthetic_data = generate_synthetic_data(1000)
        synthetic_data.to_csv("data/skinmodel_training_data.csv", index=False)
    else:
        real_data.to_csv("data/skinmodel_training_data.csv", index=False)
```

---

## 🔧 Implementation Steps

### Phase 1: Data Preparation (1-2 days)

**Task 1.1**: Create training data collection script

```bash
python scripts/collect_skinmodel_training_data.py \
  --source synthetic \
  --n-samples 1000 \
  --output data/skinmodel_training_data.csv
```

**Task 1.2**: Data validation and EDA

```bash
python scripts/validate_skinmodel_data.py \
  --input data/skinmodel_training_data.csv \
  --plots data/eda_plots/
```

**Expected Output**:
- `skinmodel_training_data.csv`: 1,000 rows × 14 columns
- EDA plots: feature distributions, correlations, target distributions

---

### Phase 2: Model Training (0.5-1 day)

**Task 2.1**: Create training script

**위치**: `scripts/train_skinmodel_xgboost.py`

```python
#!/usr/bin/env python3
"""
Skin Model XGBoost 학습 스크립트
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
import xgboost as xgb
import joblib
from pathlib import Path

def load_data(csv_path):
    """학습 데이터 로드"""
    df = pd.read_csv(csv_path)
    return df

def preprocess_features(df):
    """Feature engineering"""
    # Categorical encoding
    df_encoded = pd.get_dummies(df, columns=["material_name", "manufacturing_process"])

    # Feature scaling (for XGBoost, optional)
    feature_cols = [col for col in df_encoded.columns
                    if col not in ["flatness", "cylindricity", "position", "perpendicularity"]]

    X = df_encoded[feature_cols]
    y_flatness = df_encoded["flatness"]
    y_cylindricity = df_encoded["cylindricity"]
    y_position = df_encoded["position"]
    y_perpendicularity = df_encoded["perpendicularity"]

    return X, y_flatness, y_cylindricity, y_position, y_perpendicularity, feature_cols

def train_model(X_train, y_train, X_val, y_val, target_name):
    """단일 타겟에 대해 XGBoost 학습"""
    model = xgb.XGBRegressor(
        max_depth=6,
        n_estimators=300,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        early_stopping_rounds=20,
        verbose=False
    )

    # Evaluate
    y_pred = model.predict(X_val)
    rmse = np.sqrt(mean_squared_error(y_val, y_pred))
    r2 = r2_score(y_val, y_pred)

    print(f"📊 {target_name} - RMSE: {rmse:.4f}, R²: {r2:.4f}")

    return model, rmse, r2

def main():
    # Load data
    df = load_data("data/skinmodel_training_data.csv")

    # Preprocess
    X, y_flat, y_cyl, y_pos, y_perp, feature_cols = preprocess_features(df)

    # Train/Val split
    X_train, X_val, y_flat_train, y_flat_val = train_test_split(
        X, y_flat, test_size=0.2, random_state=42
    )
    # ... (같은 방식으로 다른 타겟들도 분할)

    # Train models
    print("🏋️ Training XGBoost models...")
    model_flat, rmse_flat, r2_flat = train_model(X_train, y_flat_train, X_val, y_flat_val, "Flatness")
    model_cyl, rmse_cyl, r2_cyl = train_model(X_train, y_cyl_train, X_val, y_cyl_val, "Cylindricity")
    model_pos, rmse_pos, r2_pos = train_model(X_train, y_pos_train, X_val, y_pos_val, "Position")
    model_perp, rmse_perp, r2_perp = train_model(X_train, y_perp_train, X_val, y_perp_val, "Perpendicularity")

    # Save models
    output_dir = Path("skinmodel-api/models")
    output_dir.mkdir(exist_ok=True)

    joblib.dump(model_flat, output_dir / "xgb_flatness.pkl")
    joblib.dump(model_cyl, output_dir / "xgb_cylindricity.pkl")
    joblib.dump(model_pos, output_dir / "xgb_position.pkl")
    joblib.dump(model_perp, output_dir / "xgb_perpendicularity.pkl")
    joblib.dump(feature_cols, output_dir / "feature_columns.pkl")

    # Save metrics
    metrics = {
        "flatness": {"rmse": rmse_flat, "r2": r2_flat},
        "cylindricity": {"rmse": rmse_cyl, "r2": r2_cyl},
        "position": {"rmse": rmse_pos, "r2": r2_pos},
        "perpendicularity": {"rmse": rmse_perp, "r2": r2_perp}
    }

    with open(output_dir / "model_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\n✅ Models saved to {output_dir}")
    print(f"📊 Overall R²: {np.mean([r2_flat, r2_cyl, r2_pos, r2_perp]):.4f}")

if __name__ == "__main__":
    main()
```

**Training Command**:

```bash
python scripts/train_skinmodel_xgboost.py
```

**Expected Output**:
- `skinmodel-api/models/xgb_flatness.pkl`
- `skinmodel-api/models/xgb_cylindricity.pkl`
- `skinmodel-api/models/xgb_position.pkl`
- `skinmodel-api/models/xgb_perpendicularity.pkl`
- `skinmodel-api/models/feature_columns.pkl`
- `skinmodel-api/models/model_metrics.json`

---

### Phase 3: API Integration (0.5-1 day)

**Task 3.1**: Modify `api_server.py` to load XGBoost models

**Changes**:

```python
# At top of file (after imports)
import xgboost as xgb
import joblib
import pandas as pd

# Global model variables
_model_flatness = None
_model_cylindricity = None
_model_position = None
_model_perpendicularity = None
_feature_columns = None
_models_loaded = False

@app.on_event("startup")
async def startup_event():
    """Load XGBoost models on startup"""
    global _model_flatness, _model_cylindricity, _model_position, _model_perpendicularity
    global _feature_columns, _models_loaded

    logger.info("🚀 Starting Skin Model API...")
    logger.info("📦 Loading XGBoost models...")

    model_dir = Path(__file__).parent / "models"

    try:
        _model_flatness = joblib.load(model_dir / "xgb_flatness.pkl")
        _model_cylindricity = joblib.load(model_dir / "xgb_cylindricity.pkl")
        _model_position = joblib.load(model_dir / "xgb_position.pkl")
        _model_perpendicularity = joblib.load(model_dir / "xgb_perpendicularity.pkl")
        _feature_columns = joblib.load(model_dir / "feature_columns.pkl")

        _models_loaded = True
        logger.info("✅ XGBoost models loaded successfully")
    except FileNotFoundError as e:
        logger.error(f"❌ Model files not found: {e}")
        logger.error("   Run: python scripts/train_skinmodel_xgboost.py")
        logger.warning("⚠️ Falling back to rule-based predictions")
        _models_loaded = False

    logger.info("✅ Skin Model API ready")

def predict_tolerances_ml(
    dimensions: List[DimensionInput],
    material: MaterialInput,
    manufacturing_process: str,
    correlation_length: float
) -> Dict[str, Any]:
    """
    XGBoost ML 모델 기반 공차 예측
    """
    global _models_loaded

    # Check if models are loaded
    if not _models_loaded:
        # Fallback to rule-based
        logger.warning("⚠️ ML models not available, using rule-based fallback")
        return predict_tolerances_rulebased(dimensions, material, manufacturing_process, correlation_length)

    try:
        # Feature engineering
        max_dim = max([d.value for d in dimensions]) if dimensions else 100.0
        min_dim = min([d.value for d in dimensions]) if dimensions else 10.0
        avg_dim = np.mean([d.value for d in dimensions]) if dimensions else 50.0
        num_dims = len(dimensions)

        # Create feature dict
        features = {
            "youngs_modulus": material.youngs_modulus or 210.0,
            "poisson_ratio": material.poisson_ratio or 0.3,
            "density": material.density or 7850.0,
            "max_dimension": max_dim,
            "min_dimension": min_dim,
            "avg_dimension": avg_dim,
            "num_dimensions": num_dims,
            "correlation_length": correlation_length,
            f"material_name_{material.name}": 1,  # One-hot encoding
            f"manufacturing_process_{manufacturing_process}": 1  # One-hot encoding
        }

        # Create DataFrame with all feature columns (fill missing with 0)
        X = pd.DataFrame([features])
        for col in _feature_columns:
            if col not in X.columns:
                X[col] = 0
        X = X[_feature_columns]  # Ensure correct column order

        # Predict
        flatness = float(_model_flatness.predict(X)[0])
        cylindricity = float(_model_cylindricity.predict(X)[0])
        position = float(_model_position.predict(X)[0])
        perpendicularity = float(_model_perpendicularity.predict(X)[0])

        # Post-processing: manufacturability and assemblability
        avg_tolerance = (flatness + cylindricity + position) / 3

        if avg_tolerance < 0.05:
            difficulty = "Hard"
            score = 0.65
            recommendations = [
                "Requires precision machining equipment",
                "Consider CNC grinding for tight tolerances",
                "Quality control critical - CMM inspection required"
            ]
        elif avg_tolerance < 0.10:
            difficulty = "Medium"
            score = 0.80
            recommendations = [
                "Standard precision machining acceptable",
                "Consider tighter fixturing for flatness control",
                "Regular calibration of measuring equipment"
            ]
        else:
            difficulty = "Easy"
            score = 0.92
            recommendations = [
                "Standard machining processes sufficient",
                "Normal quality control procedures",
                "Cost-effective manufacturing possible"
            ]

        assemblability_score = min(0.98, 0.70 + (0.1 - avg_tolerance) * 2)
        clearance = round(avg_tolerance * 3, 3)

        if avg_tolerance < 0.05:
            interference_risk = "Low"
        elif avg_tolerance < 0.15:
            interference_risk = "Medium"
        else:
            interference_risk = "High"

        result = {
            "predicted_tolerances": {
                "flatness": round(flatness, 4),
                "cylindricity": round(cylindricity, 4),
                "position": round(position, 4),
                "perpendicularity": round(perpendicularity, 4)
            },
            "manufacturability": {
                "score": round(score, 2),
                "difficulty": difficulty,
                "recommendations": recommendations
            },
            "assemblability": {
                "score": round(assemblability_score, 2),
                "clearance": clearance,
                "interference_risk": interference_risk
            },
            "model_info": {
                "type": "XGBoost ML",
                "version": "1.0.0"
            }
        }

        return result

    except Exception as e:
        logger.error(f"ML prediction failed: {e}, falling back to rule-based")
        return predict_tolerances_rulebased(dimensions, material, manufacturing_process, correlation_length)

def predict_tolerances_rulebased(
    dimensions: List[DimensionInput],
    material: MaterialInput,
    manufacturing_process: str,
    correlation_length: float
) -> Dict[str, Any]:
    """
    규칙 기반 공차 예측 (Fallback)

    현재 구현 (lines 127-244)을 이 함수로 래핑
    """
    # ... (현재 predict_tolerances 함수 내용)
    pass

# Update the endpoint to use ML model
@app.post("/api/v1/tolerance", response_model=ToleranceResponse)
async def predict_tolerance(request: ToleranceRequest):
    """기하공차 예측 (XGBoost ML)"""
    start_time = time.time()

    try:
        # Use ML model (with rule-based fallback)
        prediction_result = predict_tolerances_ml(
            request.dimensions,
            request.material,
            request.manufacturing_process,
            request.correlation_length
        )

        processing_time = time.time() - start_time

        return {
            "status": "success",
            "data": prediction_result,
            "processing_time": round(processing_time, 2)
        }

    except Exception as e:
        logger.error(f"Error in tolerance prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

### Phase 4: Testing & Validation (0.5-1 day)

**Task 4.1**: Unit tests

```bash
pytest tests/test_skinmodel_xgboost.py -v
```

**Task 4.2**: API integration test

```bash
# Test ML prediction
curl -X POST http://localhost:5003/api/v1/tolerance \
  -H "Content-Type: application/json" \
  -d '{
    "dimensions": [
      {"type": "diameter", "value": 100, "unit": "mm"},
      {"type": "length", "value": 250, "unit": "mm"}
    ],
    "material": {
      "name": "Steel",
      "youngs_modulus": 210,
      "poisson_ratio": 0.3,
      "density": 7850
    },
    "manufacturing_process": "machining",
    "correlation_length": 1.0
  }'
```

**Task 4.3**: Performance benchmark

```bash
python scripts/benchmark_skinmodel.py \
  --num-requests 1000 \
  --compare-rulebased
```

**Expected Results**:
- ML vs Rule-based accuracy comparison
- Inference time: <10ms per prediction
- Accuracy improvement: 15-25% RMSE reduction

---

## 📈 Success Metrics

### Accuracy Targets

| Metric | Rule-based (Current) | XGBoost ML (Target) | Improvement |
|--------|---------------------|---------------------|-------------|
| RMSE (Flatness) | 0.025mm | 0.015mm | 40% |
| RMSE (Cylindricity) | 0.030mm | 0.018mm | 40% |
| RMSE (Position) | 0.028mm | 0.017mm | 39% |
| R² Score | 0.65 | 0.85-0.90 | +30% |

### Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Inference Speed | <10ms | Average over 1,000 predictions |
| Model Size | <50MB | All 4 models combined |
| Startup Time | <2s | Model loading time |

---

## 🚀 Deployment Strategy

### Option 1: Complete Replacement

규칙 기반 코드 완전 제거, ML 모델만 사용

**장점**: 코드 단순화
**단점**: 모델 없으면 작동 안 함

### Option 2: Hybrid Approach (권장)

ML 모델 우선, 실패 시 규칙 기반 Fallback

**장점**: 안정성 높음, 점진적 전환 가능
**단점**: 코드 복잡도 증가

### Rollout Plan

1. **Week 1-2**: 데이터 수집 및 모델 학습
2. **Week 3**: API 통합 및 테스트
3. **Week 4**: Shadow mode 배포 (로깅만, 실제 응답은 규칙 기반)
4. **Week 5**: Canary deployment (10% 트래픽)
5. **Week 6**: Full deployment (100% 트래픽)

---

## 📝 Dependencies

### Python Packages (requirements.txt 추가)

```txt
# Current dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0

# NEW: ML dependencies
xgboost==2.0.3
scikit-learn==1.3.2
pandas==2.1.3
numpy==1.24.3
joblib==1.3.2
```

---

## 🔍 Monitoring & Maintenance

### Model Performance Monitoring

1. **Prediction Logging**:
   - 모든 예측 결과 로깅 (input features + predictions)
   - 주기적으로 실제 측정값과 비교

2. **Drift Detection**:
   - Feature distribution drift 감지
   - Prediction distribution drift 감지

3. **Retraining Trigger**:
   - RMSE > 0.025mm (threshold exceeded)
   - R² < 0.80 (accuracy degradation)
   - 6개월마다 정기 재학습

### Model Update Process

```bash
# 1. 새로운 데이터 수집
python scripts/collect_skinmodel_training_data.py \
  --source production_logs \
  --start-date 2025-01-01 \
  --end-date 2025-06-01

# 2. 모델 재학습
python scripts/train_skinmodel_xgboost.py \
  --data data/skinmodel_training_data_v2.csv \
  --version v2

# 3. 모델 평가
python scripts/evaluate_skinmodel.py \
  --model-v1 skinmodel-api/models/ \
  --model-v2 skinmodel-api/models_v2/ \
  --test-data data/test_set.csv

# 4. 배포 (성능 향상 확인 후)
cp skinmodel-api/models_v2/* skinmodel-api/models/
docker-compose restart skinmodel-api
```

---

## ✅ Implementation Checklist

### Phase 1: Data (1-2 days)
- [ ] Create `scripts/collect_skinmodel_training_data.py`
- [ ] Generate 1,000+ training samples
- [ ] Data validation & EDA
- [ ] Save `data/skinmodel_training_data.csv`

### Phase 2: Training (0.5-1 day)
- [ ] Create `scripts/train_skinmodel_xgboost.py`
- [ ] Train 4 XGBoost models (flatness, cylindricity, position, perpendicularity)
- [ ] Achieve R² > 0.85 on validation set
- [ ] Save models to `skinmodel-api/models/`

### Phase 3: API Integration (0.5-1 day)
- [ ] Add `xgboost`, `scikit-learn`, `pandas` to requirements.txt
- [ ] Implement `predict_tolerances_ml()` function
- [ ] Rename current `predict_tolerances()` to `predict_tolerances_rulebased()`
- [ ] Add startup event to load models
- [ ] Implement fallback logic (ML → rule-based on failure)

### Phase 4: Testing (0.5-1 day)
- [ ] Unit tests for ML prediction function
- [ ] Integration tests for API endpoints
- [ ] Performance benchmark (ML vs rule-based)
- [ ] Load testing (1,000 requests/sec)

### Phase 5: Deployment
- [ ] Docker image rebuild with ML dependencies
- [ ] Model files bundled in Docker image
- [ ] Canary deployment (10% traffic)
- [ ] Full deployment (100% traffic)
- [ ] Monitoring setup

---

**작성일**: 2025-11-13
**버전**: 1.0.0
**상태**: Implementation plan ready
**다음 단계**: Phase 1 데이터 수집 시작
