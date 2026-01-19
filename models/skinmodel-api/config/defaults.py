"""
SkinModel 기본 파라미터 설정

YOLO API의 MODEL_DEFAULTS 패턴 적용
- 용도별 최적 파라미터 중앙 관리
- 코드 중복 제거
- 새 용도 추가 시 설정만 추가

SkinModel: FEM 기반 공차 예측 및 제조성 분석
"""

from typing import Dict, Any, Optional


# 재료 프리셋
MATERIAL_PRESETS: Dict[str, Dict[str, Any]] = {
    "aluminum": {
        "name": "Aluminum",
        "youngs_modulus": 69.0,
        "poisson_ratio": 0.33,
        "density": 2700.0
    },
    "steel": {
        "name": "Steel",
        "youngs_modulus": 200.0,
        "poisson_ratio": 0.30,
        "density": 7850.0
    },
    "stainless": {
        "name": "Stainless Steel",
        "youngs_modulus": 193.0,
        "poisson_ratio": 0.31,
        "density": 8000.0
    },
    "titanium": {
        "name": "Titanium",
        "youngs_modulus": 110.0,
        "poisson_ratio": 0.34,
        "density": 4500.0
    },
    "plastic": {
        "name": "Plastic",
        "youngs_modulus": 2.5,
        "poisson_ratio": 0.40,
        "density": 1200.0
    },
}


# 용도별 기본 설정
DEFAULTS: Dict[str, Dict[str, Any]] = {
    "general": {
        "name": "일반 분석",
        "description": "기본 공차 분석 (Steel 기준)",
        "default_material": "steel",
        "include_fem_analysis": True,
        "include_manufacturability": True,
        "tolerance_class": "medium",
        "visualize": False,
    },
    "precision": {
        "name": "정밀 부품",
        "description": "정밀 가공 부품용 (엄격한 공차)",
        "default_material": "steel",
        "include_fem_analysis": True,
        "include_manufacturability": True,
        "tolerance_class": "fine",
        "visualize": False,
    },
    "lightweight": {
        "name": "경량 부품",
        "description": "경량화 부품용 (알루미늄/티타늄)",
        "default_material": "aluminum",
        "include_fem_analysis": True,
        "include_manufacturability": True,
        "tolerance_class": "medium",
        "visualize": False,
    },
    "marine": {
        "name": "선박용",
        "description": "선박/해양 부품용 (스테인리스)",
        "default_material": "stainless",
        "include_fem_analysis": True,
        "include_manufacturability": True,
        "tolerance_class": "medium",
        "visualize": False,
    },
    "debug": {
        "name": "디버그",
        "description": "시각화 포함 디버그용",
        "default_material": "steel",
        "include_fem_analysis": True,
        "include_manufacturability": True,
        "tolerance_class": "medium",
        "visualize": True,
    },
}

# 기본 프로파일
DEFAULT_PROFILE = "general"


def get_defaults(profile: str = DEFAULT_PROFILE, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    프로파일에 맞는 기본 설정 반환

    Args:
        profile: 프로파일 이름 (general, precision, lightweight, marine, debug)
        overrides: 덮어쓸 파라미터

    Returns:
        설정 딕셔너리
    """
    base_config = DEFAULTS.get(profile, DEFAULTS[DEFAULT_PROFILE]).copy()

    if overrides:
        for key, value in overrides.items():
            if value is not None:
                base_config[key] = value

    return base_config


def get_material(material_name: str) -> Dict[str, Any]:
    """
    재료 프리셋 반환

    Args:
        material_name: 재료 이름 (aluminum, steel, stainless, titanium, plastic)

    Returns:
        재료 속성 딕셔너리
    """
    return MATERIAL_PRESETS.get(material_name.lower(), MATERIAL_PRESETS["steel"]).copy()


def list_profiles() -> Dict[str, str]:
    """
    사용 가능한 프로파일 목록과 설명 반환
    """
    return {
        profile: config.get("description", config.get("name", profile))
        for profile, config in DEFAULTS.items()
    }
