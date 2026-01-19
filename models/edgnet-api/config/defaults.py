"""
EDGNet 기본 파라미터 설정

MODEL_DEFAULTS 패턴 적용
- 용도별 최적 파라미터 중앙 관리
- 코드 중복 제거
- 새 용도 추가 시 설정만 추가
"""

from typing import Dict, Any, Optional


# 모델별 설정
MODEL_CONFIGS: Dict[str, Dict[str, Any]] = {
    "graphsage": {
        "name": "GraphSAGE",
        "description": "그래프 신경망 기반 컴포넌트 분류 - 빠른 처리",
        "supports_num_classes": True,
        "supports_save_graph": True,
        "supports_vectorize": False,
        "recommended_for": ["도면 분류", "컴포넌트 추출"],
    },
    "unet": {
        "name": "UNet",
        "description": "픽셀 단위 세그멘테이션 - 정밀한 엣지 검출",
        "supports_num_classes": False,
        "supports_save_graph": False,
        "supports_vectorize": True,
        "supports_threshold": True,
        "recommended_for": ["엣지 검출", "윤곽선 추출", "마스크 생성"],
    },
}


# 용도별 기본 설정
DEFAULTS: Dict[str, Dict[str, Any]] = {
    "drawing_classification": {
        "name": "도면 컴포넌트 분류",
        "description": "Contour/Text/Dimension 3클래스 분류 (기본)",
        "model": "graphsage",
        "visualize": True,
        "num_classes": 3,
        "save_graph": False,
        "vectorize": False,
        "threshold": 0.5,
        "return_mask": False,
    },
    "text_detection": {
        "name": "텍스트 영역 검출",
        "description": "Text/Non-text 2클래스 분류",
        "model": "graphsage",
        "visualize": True,
        "num_classes": 2,
        "save_graph": False,
        "vectorize": False,
        "threshold": 0.5,
        "return_mask": False,
    },
    "edge_detection": {
        "name": "엣지 검출",
        "description": "UNet 기반 정밀 엣지 검출",
        "model": "unet",
        "visualize": True,
        "num_classes": 3,
        "save_graph": False,
        "vectorize": False,
        "threshold": 0.5,
        "return_mask": False,
    },
    "mask_extraction": {
        "name": "마스크 추출",
        "description": "세그멘테이션 마스크 추출 (후처리용)",
        "model": "unet",
        "visualize": False,
        "num_classes": 3,
        "save_graph": False,
        "vectorize": False,
        "threshold": 0.5,
        "return_mask": True,
    },
    "graph_analysis": {
        "name": "그래프 구조 분석",
        "description": "그래프 구조 JSON 저장 (연구용)",
        "model": "graphsage",
        "visualize": True,
        "num_classes": 3,
        "save_graph": True,
        "vectorize": False,
        "threshold": 0.5,
        "return_mask": False,
    },
    "fast": {
        "name": "빠른 처리",
        "description": "시각화 없이 빠른 분류만",
        "model": "graphsage",
        "visualize": False,
        "num_classes": 3,
        "save_graph": False,
        "vectorize": False,
        "threshold": 0.5,
        "return_mask": False,
    },
}


# 기본 프로파일
DEFAULT_PROFILE = "drawing_classification"


def get_defaults(profile: str = DEFAULT_PROFILE, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    프로파일에 맞는 기본 설정 반환

    Args:
        profile: 프로파일 이름
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


def list_profiles() -> Dict[str, str]:
    """
    사용 가능한 프로파일 목록과 설명 반환
    """
    return {
        profile: config.get("description", config.get("name", profile))
        for profile, config in DEFAULTS.items()
    }


def get_model_info(model: str) -> Dict[str, Any]:
    """
    모델 정보 반환
    """
    return MODEL_CONFIGS.get(model, MODEL_CONFIGS["graphsage"]).copy()


def get_profiles_by_model(model: str) -> Dict[str, Dict[str, Any]]:
    """
    특정 모델을 사용하는 프로파일 목록 반환
    """
    return {
        profile: config
        for profile, config in DEFAULTS.items()
        if config.get("model") == model
    }
