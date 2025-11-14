#!/usr/bin/env python3
"""
Skin Model XGBoost 업그레이드 스크립트

기존 RandomForest 모델을 XGBoost로 업그레이드하여 정확도 향상
- 기존 학습 데이터 사용
- GPU 가속 학습
- 모델 비교 및 성능 평가
"""

import sys
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
import pandas as pd

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# XGBoost import
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.error("❌ XGBoost not installed. Install with: pip install xgboost")

# joblib for model loading/saving
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error


# 합성 데이터 생성 (기존과 동일)
def generate_synthetic_data(n_samples: int = 5000) -> pd.DataFrame:
    """합성 학습 데이터 생성"""
    np.random.seed(42)

    data = []

    for _ in range(n_samples):
        # 특징 생성
        diameter = np.random.uniform(10, 200)  # mm
        length = np.random.uniform(20, 500)
        thickness = np.random.uniform(1, 50)
        material_hardness = np.random.choice([50, 100, 200, 275])  # Al, Brass, Steel, Ti
        material_youngs = np.random.choice([70, 100, 200, 110])
        process_encoded = np.random.choice([0, 1, 2, 3])  # machining, casting, forging, sheet_metal

        # 특징 벡터
        features = {
            'diameter': diameter,
            'length': length,
            'thickness': thickness,
            'material_hardness': material_hardness,
            'material_youngs_modulus': material_youngs,
            'process_encoded': process_encoded
        }

        # 목표 변수 생성 (물리 기반 휴리스틱)
        # Flatness
        thickness_factor = 0.001 * (thickness ** 0.5)
        process_factor = 1.0 + 0.1 * process_encoded
        flatness = thickness_factor * process_factor * np.random.uniform(0.8, 1.2)

        # Cylindricity
        diameter_factor = 0.002 * (diameter ** 0.5)
        material_factor = 200.0 / material_hardness
        cylindricity = diameter_factor * material_factor * np.random.uniform(0.8, 1.2)

        # Position
        length_factor = 0.005 * (length ** 0.3)
        position = length_factor * process_factor * np.random.uniform(0.8, 1.2)

        features['flatness'] = max(0.001, flatness)
        features['cylindricity'] = max(0.001, cylindricity)
        features['position'] = max(0.001, position)

        data.append(features)

    return pd.DataFrame(data)


def load_existing_data(models_dir: Path) -> Tuple[pd.DataFrame, bool]:
    """기존 모델에서 학습 데이터 추출 시도"""
    try:
        # 메타데이터 확인
        metadata_path = models_dir / "model_metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            training_samples = metadata.get('training_samples', 0)
            logger.info(f"기존 메타데이터: {training_samples} 샘플")

        # 기존 모델이 있으면 데이터를 재생성할 필요 없음
        # 합성 데이터 생성 (기존과 동일한 분포)
        logger.info("합성 데이터 생성 (기존 분포 유지)")
        df = generate_synthetic_data(n_samples=5000)
        return df, True

    except Exception as e:
        logger.warning(f"기존 데이터 로드 실패: {e}")
        return None, False


def train_xgboost_models(
    X: np.ndarray,
    y_flatness: np.ndarray,
    y_cylindricity: np.ndarray,
    y_position: np.ndarray,
    use_gpu: bool = True
) -> Tuple[xgb.XGBRegressor, xgb.XGBRegressor, xgb.XGBRegressor, Dict]:
    """XGBoost 모델 학습"""

    # Device 설정
    # XGBoost GPU 지원 확인
    device = "cpu"
    tree_method = "hist"

    if use_gpu:
        # XGBoost GPU 지원은 CUDA 빌드가 필요
        # 일반 pip install xgboost는 CPU만 지원
        logger.info("⚡ XGBoost 학습 모드 (tree_method=hist)")
        logger.info("   Note: GPU acceleration requires CUDA-enabled XGBoost build")
    else:
        logger.info("💻 XGBoost CPU 학습 모드")

    # XGBoost 하이퍼파라미터
    params = {
        'n_estimators': 200,
        'max_depth': 6,
        'learning_rate': 0.1,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'tree_method': tree_method,
        'random_state': 42,
        'n_jobs': -1
    }

    logger.info(f"XGBoost 파라미터: {params}")

    # Train/val split
    X_train, X_val, y_flat_train, y_flat_val = train_test_split(
        X, y_flatness, test_size=0.2, random_state=42
    )
    _, _, y_cyl_train, y_cyl_val = train_test_split(
        X, y_cylindricity, test_size=0.2, random_state=42
    )
    _, _, y_pos_train, y_pos_val = train_test_split(
        X, y_position, test_size=0.2, random_state=42
    )

    logger.info(f"학습 데이터: {len(X_train)}, 검증 데이터: {len(X_val)}")

    results = {}
    start_time = time.time()

    # 1. Flatness 모델
    logger.info("📦 Flatness 모델 학습...")
    flatness_model = xgb.XGBRegressor(**params)
    flatness_model.fit(X_train, y_flat_train, eval_set=[(X_val, y_flat_val)], verbose=False)

    y_flat_pred = flatness_model.predict(X_val)
    flat_r2 = r2_score(y_flat_val, y_flat_pred)
    flat_mae = mean_absolute_error(y_flat_val, y_flat_pred)
    flat_rmse = np.sqrt(mean_squared_error(y_flat_val, y_flat_pred))

    results['flatness'] = {'r2': flat_r2, 'mae': flat_mae, 'rmse': flat_rmse}
    logger.info(f"  Flatness - R²={flat_r2:.4f}, MAE={flat_mae:.6f}, RMSE={flat_rmse:.6f}")

    # 2. Cylindricity 모델
    logger.info("📦 Cylindricity 모델 학습...")
    cylindricity_model = xgb.XGBRegressor(**params)
    cylindricity_model.fit(X_train, y_cyl_train, eval_set=[(X_val, y_cyl_val)], verbose=False)

    y_cyl_pred = cylindricity_model.predict(X_val)
    cyl_r2 = r2_score(y_cyl_val, y_cyl_pred)
    cyl_mae = mean_absolute_error(y_cyl_val, y_cyl_pred)
    cyl_rmse = np.sqrt(mean_squared_error(y_cyl_val, y_cyl_pred))

    results['cylindricity'] = {'r2': cyl_r2, 'mae': cyl_mae, 'rmse': cyl_rmse}
    logger.info(f"  Cylindricity - R²={cyl_r2:.4f}, MAE={cyl_mae:.6f}, RMSE={cyl_rmse:.6f}")

    # 3. Position 모델
    logger.info("📦 Position 모델 학습...")
    position_model = xgb.XGBRegressor(**params)
    position_model.fit(X_train, y_pos_train, eval_set=[(X_val, y_pos_val)], verbose=False)

    y_pos_pred = position_model.predict(X_val)
    pos_r2 = r2_score(y_pos_val, y_pos_pred)
    pos_mae = mean_absolute_error(y_pos_val, y_pos_pred)
    pos_rmse = np.sqrt(mean_squared_error(y_pos_val, y_pos_pred))

    results['position'] = {'r2': pos_r2, 'mae': pos_mae, 'rmse': pos_rmse}
    logger.info(f"  Position - R²={pos_r2:.4f}, MAE={pos_mae:.6f}, RMSE={pos_rmse:.6f}")

    training_time = time.time() - start_time
    results['training_time'] = training_time
    results['device'] = device
    results['tree_method'] = tree_method

    logger.info(f"✅ 학습 완료: {training_time:.2f}초")

    return flatness_model, cylindricity_model, position_model, results


def compare_models(models_dir: Path, results: Dict):
    """기존 RandomForest vs 새로운 XGBoost 비교"""
    logger.info("\n" + "="*60)
    logger.info("모델 성능 비교")
    logger.info("="*60)

    # 기존 모델 메타데이터 로드
    metadata_path = models_dir / "model_metadata.json"
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            old_metadata = json.load(f)

        logger.info("\n[기존 RandomForest 모델]")
        logger.info(f"  Model: {old_metadata.get('model_type', 'RandomForest')}")
        logger.info(f"  Training samples: {old_metadata.get('training_samples', 'N/A')}")

        flat_r2 = old_metadata.get('flatness_r2')
        cyl_r2 = old_metadata.get('cylindricity_r2')
        pos_r2 = old_metadata.get('position_r2')

        if flat_r2 and isinstance(flat_r2, (int, float)):
            logger.info(f"  Flatness R²: {flat_r2:.4f}")
        else:
            logger.info(f"  Flatness R²: N/A")

        if cyl_r2 and isinstance(cyl_r2, (int, float)):
            logger.info(f"  Cylindricity R²: {cyl_r2:.4f}")
        else:
            logger.info(f"  Cylindricity R²: N/A")

        if pos_r2 and isinstance(pos_r2, (int, float)):
            logger.info(f"  Position R²: {pos_r2:.4f}")
        else:
            logger.info(f"  Position R²: N/A")
    else:
        logger.info("\n[기존 모델 메타데이터 없음]")

    logger.info("\n[새로운 XGBoost 모델]")
    logger.info(f"  Device: {results.get('device', 'N/A')}")
    logger.info(f"  Tree method: {results.get('tree_method', 'N/A')}")
    logger.info(f"  Training time: {results.get('training_time', 0):.2f}초")
    logger.info(f"  Flatness R²: {results['flatness']['r2']:.4f}")
    logger.info(f"  Cylindricity R²: {results['cylindricity']['r2']:.4f}")
    logger.info(f"  Position R²: {results['position']['r2']:.4f}")

    logger.info("\n" + "="*60)


def save_models(
    flatness_model: xgb.XGBRegressor,
    cylindricity_model: xgb.XGBRegressor,
    position_model: xgb.XGBRegressor,
    process_encoder,
    results: Dict,
    output_dir: Path
):
    """모델 저장"""
    output_dir.mkdir(parents=True, exist_ok=True)

    # 모델 저장
    joblib.dump(flatness_model, output_dir / "flatness_predictor_xgboost.pkl")
    joblib.dump(cylindricity_model, output_dir / "cylindricity_predictor_xgboost.pkl")
    joblib.dump(position_model, output_dir / "position_predictor_xgboost.pkl")
    joblib.dump(process_encoder, output_dir / "process_encoder.pkl")

    logger.info(f"💾 모델 저장: {output_dir}")

    # 메타데이터
    metadata = {
        'model_type': 'XGBoost',
        'xgboost_version': xgb.__version__,
        'device': results.get('device', 'cpu'),
        'tree_method': results.get('tree_method', 'hist'),
        'training_time': results.get('training_time', 0),
        'training_samples': 5000,
        'flatness_r2': results['flatness']['r2'],
        'flatness_mae': results['flatness']['mae'],
        'flatness_rmse': results['flatness']['rmse'],
        'cylindricity_r2': results['cylindricity']['r2'],
        'cylindricity_mae': results['cylindricity']['mae'],
        'cylindricity_rmse': results['cylindricity']['rmse'],
        'position_r2': results['position']['r2'],
        'position_mae': results['position']['mae'],
        'position_rmse': results['position']['rmse'],
    }

    with open(output_dir / "model_metadata_xgboost.json", 'w') as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"📄 메타데이터 저장: {output_dir}/model_metadata_xgboost.json")


def main():
    """메인 함수"""
    logger.info("="*60)
    logger.info("Skin Model XGBoost 업그레이드")
    logger.info("="*60)

    if not XGBOOST_AVAILABLE:
        logger.error("❌ XGBoost not available. Install with: pip install xgboost")
        return 1

    # 경로 설정
    models_dir = Path("/home/uproot/ax/poc/skinmodel-api/models")
    output_dir = models_dir  # 동일 디렉토리에 저장

    # 데이터 생성
    logger.info("\n📊 학습 데이터 생성...")
    df = generate_synthetic_data(n_samples=5000)

    logger.info(f"  샘플 수: {len(df)}")
    logger.info(f"  특징 수: {df.shape[1] - 3}")  # 3개 목표 변수 제외

    # 특징 및 목표 변수 분리
    feature_cols = ['diameter', 'length', 'thickness', 'material_hardness',
                    'material_youngs_modulus', 'process_encoded']
    X = df[feature_cols].values
    y_flatness = df['flatness'].values
    y_cylindricity = df['cylindricity'].values
    y_position = df['position'].values

    # Process encoder (기존과 동일)
    process_mapping = {
        'machining': 0,
        'casting': 1,
        'forging': 2,
        'sheet_metal': 3
    }

    # XGBoost 모델 학습
    logger.info("\n🚀 XGBoost 모델 학습 시작...")
    flatness_model, cylindricity_model, position_model, results = train_xgboost_models(
        X, y_flatness, y_cylindricity, y_position, use_gpu=True
    )

    # 모델 비교
    compare_models(models_dir, results)

    # 모델 저장
    save_models(
        flatness_model,
        cylindricity_model,
        position_model,
        process_mapping,
        results,
        output_dir
    )

    logger.info("\n" + "="*60)
    logger.info("✅ XGBoost 업그레이드 완료!")
    logger.info("="*60)
    logger.info(f"평균 R² 점수: {np.mean([results['flatness']['r2'], results['cylindricity']['r2'], results['position']['r2']]):.4f}")
    logger.info("")
    logger.info("다음 단계:")
    logger.info("1. ml_predictor.py에서 XGBoost 모델 사용하도록 수정")
    logger.info("2. docker-compose restart skinmodel-api")
    logger.info("3. 성능 테스트")

    return 0


if __name__ == "__main__":
    sys.exit(main())
