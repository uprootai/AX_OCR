"""
ML-based Tolerance Predictor
Rule-based 휴리스틱을 ML 모델로 교체
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np

logger = logging.getLogger(__name__)

# Lazy imports
joblib = None
pd = None


class MLTolerancePredictor:
    """ML 기반 공차 예측기"""

    def __init__(self, models_dir: str = "models"):
        """
        초기화

        Args:
            models_dir: 모델 파일이 저장된 디렉토리
        """
        self.models_dir = Path(models_dir)
        self.flatness_model = None
        self.cylindricity_model = None
        self.position_model = None
        self.process_encoder = None
        self.models_loaded = False

        # 재질별 속성 매핑
        self.material_properties = {
            "Steel": {"hardness": 200, "youngs_modulus": 200},
            "steel": {"hardness": 200, "youngs_modulus": 200},
            "Aluminum": {"hardness": 50, "youngs_modulus": 70},
            "aluminum": {"hardness": 50, "youngs_modulus": 70},
            "Plastic": {"hardness": 15, "youngs_modulus": 3},
            "plastic": {"hardness": 15, "youngs_modulus": 3},
            "Titanium": {"hardness": 275, "youngs_modulus": 110},
            "titanium": {"hardness": 275, "youngs_modulus": 110},
            "Brass": {"hardness": 100, "youngs_modulus": 100},
            "brass": {"hardness": 100, "youngs_modulus": 100},
        }

        # 모델 로드 시도
        self._load_models()

    def _load_models(self):
        """ML 모델 로드 (XGBoost 우선, RandomForest fallback)"""
        try:
            global joblib, pd
            import joblib
            import pandas as pd

            # XGBoost 모델 경로 (우선)
            flatness_xgb_path = self.models_dir / "flatness_predictor_xgboost.pkl"
            cylindricity_xgb_path = self.models_dir / "cylindricity_predictor_xgboost.pkl"
            position_xgb_path = self.models_dir / "position_predictor_xgboost.pkl"

            # RandomForest 모델 경로 (fallback)
            flatness_rf_path = self.models_dir / "flatness_predictor.pkl"
            cylindricity_rf_path = self.models_dir / "cylindricity_predictor.pkl"
            position_rf_path = self.models_dir / "position_predictor.pkl"

            encoder_path = self.models_dir / "process_encoder.pkl"

            # XGBoost 모델 우선 시도
            if all([p.exists() for p in [flatness_xgb_path, cylindricity_xgb_path, position_xgb_path, encoder_path]]):
                self.flatness_model = joblib.load(flatness_xgb_path)
                self.cylindricity_model = joblib.load(cylindricity_xgb_path)
                self.position_model = joblib.load(position_xgb_path)
                self.process_encoder = joblib.load(encoder_path)
                self.models_loaded = True
                logger.info("✅ XGBoost 모델 로드 성공")

            # RandomForest fallback
            elif all([p.exists() for p in [flatness_rf_path, cylindricity_rf_path, position_rf_path, encoder_path]]):
                self.flatness_model = joblib.load(flatness_rf_path)
                self.cylindricity_model = joblib.load(cylindricity_rf_path)
                self.position_model = joblib.load(position_rf_path)
                self.process_encoder = joblib.load(encoder_path)
                self.models_loaded = True
                logger.info("✅ RandomForest 모델 로드 성공 (XGBoost fallback)")

            else:
                logger.warning("⚠️  ML 모델 파일 없음 - Rule-based fallback 사용")
                self.models_loaded = False

        except Exception as e:
            logger.warning(f"⚠️  ML 모델 로드 실패: {e} - Rule-based fallback 사용")
            self.models_loaded = False

    def _extract_features(self, dimensions: List[Dict], material: Dict, process: str) -> np.ndarray:
        """
        입력 데이터에서 ML 모델용 특징 추출

        Args:
            dimensions: 치수 리스트
            material: 재질 정보
            process: 제조 공정

        Returns:
            특징 벡터 (7차원)
        """
        # 치수 정보 추출
        diameter = 0.0
        length = 0.0
        thickness = 0.0

        for dim in dimensions:
            dim_type = dim.get("type", "").lower()
            value = dim.get("value", 0.0)

            if "diameter" in dim_type or "dia" in dim_type:
                diameter = max(diameter, value)
            elif "length" in dim_type or "len" in dim_type:
                length = max(length, value)
            elif "thickness" in dim_type or "thick" in dim_type:
                thickness = max(thickness, value)
            else:
                # 일반 치수는 length로 간주
                length = max(length, value)

        # 치수가 없으면 기본값
        if diameter == 0.0 and length == 0.0:
            diameter = 50.0  # 기본값
            length = 100.0

        if thickness == 0.0:
            thickness = min(diameter, length) * 0.1  # 기본값: 10%

        # 재질 속성
        material_name = material.get("name", "Steel")
        props = self.material_properties.get(material_name, self.material_properties["Steel"])
        hardness = props["hardness"]
        youngs_modulus = material.get("youngs_modulus") or props["youngs_modulus"]

        # 공정 인코딩
        process_lower = process.lower()
        if process_lower not in ['machining', 'casting', '3d_printing', 'sheet_metal', 'forging']:
            process_lower = 'machining'  # 기본값

        try:
            process_encoded = self.process_encoder.transform([process_lower])[0]
        except:
            process_encoded = 0  # Fallback

        # Material encoding (간단히 매핑)
        material_map = {"steel": 0, "aluminum": 1, "plastic": 2, "titanium": 3, "brass": 4}
        material_encoded = material_map.get(material_name.lower(), 0)

        # 특징 벡터 생성 [diameter, length, thickness, hardness, youngs_modulus, process_encoded, material_encoded]
        features = np.array([
            diameter,
            length,
            thickness,
            hardness,
            youngs_modulus,
            process_encoded,
            material_encoded
        ]).reshape(1, -1)

        return features

    def predict(self, dimensions: List[Dict], material: Dict, process: str) -> Dict[str, float]:
        """
        ML 모델로 공차 예측

        Args:
            dimensions: 치수 정보 리스트
            material: 재질 정보
            process: 제조 공정

        Returns:
            예측된 공차 값들
        """
        if not self.models_loaded:
            logger.warning("ML 모델 미사용 - None 반환")
            return None

        try:
            # 특징 추출
            features = self._extract_features(dimensions, material, process)

            # 예측
            flatness = float(self.flatness_model.predict(features)[0])
            cylindricity = float(self.cylindricity_model.predict(features)[0])
            position = float(self.position_model.predict(features)[0])
            perpendicularity = flatness * 1.2  # 경험적 관계식

            logger.info(f"ML 예측 완료: flatness={flatness:.4f}, cylindricity={cylindricity:.4f}, position={position:.4f}")

            return {
                "flatness": round(flatness, 4),
                "cylindricity": round(cylindricity, 4),
                "position": round(position, 4),
                "perpendicularity": round(perpendicularity, 4)
            }

        except Exception as e:
            logger.error(f"ML 예측 실패: {e}")
            return None

    def is_available(self) -> bool:
        """ML 모델 사용 가능 여부"""
        return self.models_loaded


# Global predictor instance
_predictor = None


def get_ml_predictor() -> MLTolerancePredictor:
    """Global ML predictor 인스턴스 가져오기"""
    global _predictor
    if _predictor is None:
        _predictor = MLTolerancePredictor()
    return _predictor
