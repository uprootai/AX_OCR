"""
OCR Ensemble 기본 파라미터 설정

YOLO API의 MODEL_DEFAULTS 패턴 적용
- 용도별 최적 파라미터 중앙 관리
- 코드 중복 제거
- 새 용도 추가 시 설정만 추가

OCR Ensemble: 4개 OCR 엔진 가중 투표 (eDOCr2, PaddleOCR, Tesseract, TrOCR)
"""

from typing import Dict, Any, Optional


# 용도별 기본 설정
DEFAULTS: Dict[str, Dict[str, Any]] = {
    "general": {
        "name": "일반 앙상블",
        "description": "범용 가중 투표 (기본값)",
        "edocr2_weight": 0.40,
        "paddleocr_weight": 0.35,
        "tesseract_weight": 0.15,
        "trocr_weight": 0.10,
        "similarity_threshold": 0.7,
        "engines": "all",
    },
    "dimension": {
        "name": "치수 인식",
        "description": "치수/숫자 인식에 최적화 (eDOCr2 강조)",
        "edocr2_weight": 0.55,
        "paddleocr_weight": 0.25,
        "tesseract_weight": 0.15,
        "trocr_weight": 0.05,
        "similarity_threshold": 0.6,
        "engines": "all",
    },
    "korean": {
        "name": "한국어 인식",
        "description": "한국어 문서 인식 (PaddleOCR 강조)",
        "edocr2_weight": 0.30,
        "paddleocr_weight": 0.50,
        "tesseract_weight": 0.10,
        "trocr_weight": 0.10,
        "similarity_threshold": 0.7,
        "engines": "all",
    },
    "engineering": {
        "name": "도면 인식",
        "description": "기계/전기 도면 텍스트 인식",
        "edocr2_weight": 0.45,
        "paddleocr_weight": 0.30,
        "tesseract_weight": 0.20,
        "trocr_weight": 0.05,
        "similarity_threshold": 0.65,
        "engines": "all",
    },
    "accurate": {
        "name": "정확도 우선",
        "description": "높은 유사도 임계값으로 정확도 우선",
        "edocr2_weight": 0.35,
        "paddleocr_weight": 0.35,
        "tesseract_weight": 0.20,
        "trocr_weight": 0.10,
        "similarity_threshold": 0.85,
        "engines": "all",
    },
    "fast": {
        "name": "속도 우선",
        "description": "주요 엔진만 사용 (eDOCr2 + PaddleOCR)",
        "edocr2_weight": 0.50,
        "paddleocr_weight": 0.50,
        "tesseract_weight": 0.0,
        "trocr_weight": 0.0,
        "similarity_threshold": 0.7,
        "engines": "edocr2,paddleocr",
    },
    "handwritten": {
        "name": "필기체 인식",
        "description": "필기체 텍스트 인식 (TrOCR 강조)",
        "edocr2_weight": 0.20,
        "paddleocr_weight": 0.25,
        "tesseract_weight": 0.15,
        "trocr_weight": 0.40,
        "similarity_threshold": 0.6,
        "engines": "all",
    },
}

# 기본 프로파일
DEFAULT_PROFILE = "general"


def get_defaults(profile: str = DEFAULT_PROFILE, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    프로파일에 맞는 기본 설정 반환

    Args:
        profile: 프로파일 이름 (general, dimension, korean, engineering, accurate, fast, handwritten)
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


def get_weight_config(profile: str = DEFAULT_PROFILE) -> Dict[str, float]:
    """
    엔진별 가중치 설정 반환

    Args:
        profile: 프로파일 이름

    Returns:
        가중치 설정 딕셔너리
    """
    config = DEFAULTS.get(profile, DEFAULTS[DEFAULT_PROFILE])

    return {
        "edocr2": config.get("edocr2_weight", 0.40),
        "paddleocr": config.get("paddleocr_weight", 0.35),
        "tesseract": config.get("tesseract_weight", 0.15),
        "trocr": config.get("trocr_weight", 0.10),
    }


def get_active_engines(profile: str = DEFAULT_PROFILE) -> list:
    """
    활성화된 엔진 목록 반환

    Args:
        profile: 프로파일 이름

    Returns:
        활성 엔진 목록
    """
    config = DEFAULTS.get(profile, DEFAULTS[DEFAULT_PROFILE])
    engines_str = config.get("engines", "all")

    if engines_str == "all":
        return ["edocr2", "paddleocr", "tesseract", "trocr"]

    return [e.strip() for e in engines_str.split(",") if e.strip()]


def list_profiles() -> Dict[str, str]:
    """
    사용 가능한 프로파일 목록과 설명 반환
    """
    return {
        profile: config.get("description", config.get("name", profile))
        for profile, config in DEFAULTS.items()
    }
