"""
PID Analyzer 기본 파라미터 설정

YOLO API의 MODEL_DEFAULTS 패턴 적용
- 용도별 최적 파라미터 중앙 관리
- 코드 중복 제거
- 새 용도 추가 시 설정만 추가

PID Analyzer: P&ID 연결성 분석 및 BOM 추출
"""

from typing import Dict, Any, Optional


# 용도별 기본 설정
DEFAULTS: Dict[str, Dict[str, Any]] = {
    "general": {
        "name": "일반 분석",
        "description": "기본 연결성 분석 (모든 출력 포함)",
        "generate_bom": True,
        "generate_valve_list": True,
        "generate_equipment_list": True,
        "enable_ocr": True,
        "visualize": True,
    },
    "connectivity_only": {
        "name": "연결성만",
        "description": "연결 관계만 분석 (BOM 생성 안함)",
        "generate_bom": False,
        "generate_valve_list": False,
        "generate_equipment_list": False,
        "enable_ocr": False,
        "visualize": False,
    },
    "bom_export": {
        "name": "BOM 추출",
        "description": "BOM 및 장비 리스트 추출용",
        "generate_bom": True,
        "generate_valve_list": True,
        "generate_equipment_list": True,
        "enable_ocr": True,
        "visualize": False,
    },
    "bwms": {
        "name": "BWMS 분석",
        "description": "Ballast Water Management System 전용",
        "generate_bom": True,
        "generate_valve_list": True,
        "generate_equipment_list": True,
        "enable_ocr": True,
        "visualize": True,
    },
    "debug": {
        "name": "디버그",
        "description": "시각화 포함 디버그용",
        "generate_bom": True,
        "generate_valve_list": True,
        "generate_equipment_list": True,
        "enable_ocr": True,
        "visualize": True,
    },
}

# 기본 프로파일
DEFAULT_PROFILE = "general"


def get_defaults(profile: str = DEFAULT_PROFILE, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    프로파일에 맞는 기본 설정 반환

    Args:
        profile: 프로파일 이름 (general, connectivity_only, bom_export, bwms, debug)
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
