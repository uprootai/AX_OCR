"""
ESRGAN 기본 파라미터 설정

YOLO API의 MODEL_DEFAULTS 패턴 적용
- 용도별 최적 파라미터 중앙 관리
- 코드 중복 제거
- 새 용도 추가 시 설정만 추가

ESRGAN: 이미지 4x 업스케일링 (Real-ESRGAN)
"""

from typing import Dict, Any, Optional


# 용도별 기본 설정
DEFAULTS: Dict[str, Dict[str, Any]] = {
    "general": {
        "name": "일반",
        "description": "기본 4x 업스케일링",
        "scale": 4,
        "tile_size": 512,
        "tile_pad": 32,
        "denoise_strength": 0.5,
        "face_enhance": False,
    },
    "drawing": {
        "name": "도면용",
        "description": "도면 이미지 최적화 (선명한 선)",
        "scale": 4,
        "tile_size": 512,
        "tile_pad": 32,
        "denoise_strength": 0.3,
        "face_enhance": False,
    },
    "photo": {
        "name": "사진용",
        "description": "사진 이미지 최적화",
        "scale": 4,
        "tile_size": 512,
        "tile_pad": 32,
        "denoise_strength": 0.5,
        "face_enhance": True,
    },
    "fast": {
        "name": "빠른 처리",
        "description": "빠른 처리 (작은 타일)",
        "scale": 4,
        "tile_size": 256,
        "tile_pad": 16,
        "denoise_strength": 0.5,
        "face_enhance": False,
    },
    "quality": {
        "name": "고품질",
        "description": "고품질 처리 (큰 타일)",
        "scale": 4,
        "tile_size": 1024,
        "tile_pad": 64,
        "denoise_strength": 0.5,
        "face_enhance": False,
    },
    "debug": {
        "name": "디버그",
        "description": "디버그용",
        "scale": 4,
        "tile_size": 512,
        "tile_pad": 32,
        "denoise_strength": 0.5,
        "face_enhance": False,
    },
}

# 기본 프로파일
DEFAULT_PROFILE = "general"


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
