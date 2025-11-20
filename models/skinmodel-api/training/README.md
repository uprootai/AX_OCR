# Skin Model Training

기하공차 예측 ML 모델 학습 자료

## 📁 디렉토리 구조

```
training/
├── scripts/
│   ├── implement_skinmodel_ml.py
│   └── upgrade_skinmodel_xgboost.py
└── README.md
```

## 🚀 학습 방법

### 1. 기본 ML 모델 학습

```bash
python training/scripts/implement_skinmodel_ml.py
```

### 2. XGBoost로 업그레이드

```bash
python training/scripts/upgrade_skinmodel_xgboost.py
```

### 3. 학습된 모델 배치

학습 완료 후 `.pkl` 파일들이 `models/` 디렉토리에 생성되어 API에서 사용됩니다.

## 📊 모델 정보

- **Flatness Predictor**: 평탄도 예측
- **Cylindricity Predictor**: 원통도 예측
- **Position Predictor**: 위치 공차 예측

## 🔧 알고리즘

- Random Forest (기본)
- XGBoost (업그레이드)
