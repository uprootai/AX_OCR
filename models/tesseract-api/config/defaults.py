"""
Tesseract OCR 기본 파라미터 설정

YOLO API의 MODEL_DEFAULTS 패턴 적용
- 용도별 최적 파라미터 중앙 관리
- 코드 중복 제거
- 새 용도 추가 시 설정만 추가

PSM (Page Segmentation Mode):
  0 = OSD only
  1 = Auto page segmentation with OSD
  3 = Fully automatic page segmentation (default)
  6 = Assume a single uniform block of text
  7 = Treat the image as a single text line
  11 = Sparse text
  13 = Raw line

OEM (OCR Engine Mode):
  0 = Legacy only
  1 = Neural nets LSTM only
  2 = Legacy + LSTM
  3 = Default (auto)
"""

from typing import Dict, Any, Optional


# 용도별 기본 설정
DEFAULTS: Dict[str, Dict[str, Any]] = {
    "general": {
        "name": "일반 OCR",
        "description": "범용 텍스트 인식 (기본값)",
        "lang": "eng",
        "psm": "3",
        "oem": "3",
        "output_type": "data",
    },
    "korean": {
        "name": "한국어 OCR",
        "description": "한국어 문서 인식",
        "lang": "kor+eng",
        "psm": "6",
        "oem": "3",
        "output_type": "data",
    },
    "engineering": {
        "name": "도면 OCR",
        "description": "도면 텍스트 인식 (영숫자 중심)",
        "lang": "eng",
        "psm": "6",
        "oem": "1",
        "output_type": "data",
    },
    "single_line": {
        "name": "단일 라인",
        "description": "한 줄 텍스트만 인식",
        "lang": "eng",
        "psm": "7",
        "oem": "3",
        "output_type": "data",
    },
    "sparse": {
        "name": "희소 텍스트",
        "description": "흩어진 텍스트 인식 (라벨, 도면)",
        "lang": "eng",
        "psm": "11",
        "oem": "3",
        "output_type": "data",
    },
    "block": {
        "name": "텍스트 블록",
        "description": "단일 텍스트 블록 인식",
        "lang": "eng",
        "psm": "6",
        "oem": "3",
        "output_type": "data",
    },
    "raw": {
        "name": "원시 라인",
        "description": "원시 텍스트 라인 모드",
        "lang": "eng",
        "psm": "13",
        "oem": "1",
        "output_type": "data",
    },
}

# 기본 프로파일
DEFAULT_PROFILE = "general"


def get_defaults(profile: str = DEFAULT_PROFILE, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    프로파일에 맞는 기본 설정 반환

    Args:
        profile: 프로파일 이름 (general, korean, engineering, single_line, sparse, block, raw)
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


def get_psm_description(psm: str) -> str:
    """PSM 값에 대한 설명 반환"""
    psm_descriptions = {
        "0": "OSD only",
        "1": "Auto page segmentation with OSD",
        "3": "Fully automatic page segmentation (default)",
        "6": "Single uniform block of text",
        "7": "Single text line",
        "11": "Sparse text",
        "13": "Raw line",
    }
    return psm_descriptions.get(psm, "Unknown")


def list_profiles() -> Dict[str, str]:
    """
    사용 가능한 프로파일 목록과 설명 반환
    """
    return {
        profile: config.get("description", config.get("name", profile))
        for profile, config in DEFAULTS.items()
    }
