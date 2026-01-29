"""
YOLO 모델별 기본 파라미터 설정

Blueprint AI BOM의 MODEL_CONFIGS 패턴 적용
- 모델별 최적 파라미터 중앙 관리
- 코드 중복 제거
- 새 모델 추가 시 설정만 추가
"""

from typing import Dict, Any, Optional

# 모델별 기본 파라미터 설정
MODEL_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "engineering": {
        "name": "기계도면 심볼",
        "confidence": 0.50,
        "iou": 0.45,
        "imgsz": 640,
        "use_sahi": False,
        "augment": False,
        "description": "치수선, 중심선, 용접기호 등 14종 검출",
    },
    "pid_symbol": {
        "name": "P&ID 심볼 (32종)",
        "confidence": 0.10,  # P&ID는 낮은 신뢰도 권장 (작은 심볼 검출)
        "iou": 0.45,
        "imgsz": 1024,
        "use_sahi": True,  # SAHI 자동 활성화 (대형 이미지용)
        "slice_size": 512,
        "overlap_ratio": 0.25,
        "augment": False,
        "description": "밸브, 계기, 플랜지 등 32종 P&ID 심볼 검출",
    },
    "pid_class_aware": {
        "name": "P&ID 분류 (32종)",
        "confidence": 0.10,
        "iou": 0.45,
        "imgsz": 1024,
        "use_sahi": True,
        "slice_size": 512,
        "overlap_ratio": 0.25,
        "augment": False,
        "description": "32종 주요 P&ID 심볼 분류",
    },
    "pid_class_agnostic": {
        "name": "P&ID 범용",
        "confidence": 0.10,
        "iou": 0.45,
        "imgsz": 1024,
        "use_sahi": True,
        "slice_size": 512,
        "overlap_ratio": 0.25,
        "augment": False,
        "description": "클래스 구분 없이 모든 심볼 검출",
    },
    "bom_detector": {
        "name": "전력 설비 단선도 (27종)",
        "confidence": 0.40,
        "iou": 0.50,
        "imgsz": 1024,
        "use_sahi": False,  # 단선도는 SAHI 불필요
        "augment": False,
        "description": "차단기, 변압기, CT, PT 등 27종 검출",
    },
    "panasia": {
        "name": "파나시아 MCP Panel (27종)",
        "confidence": 0.40,  # bom_detector.pt 최적값
        "iou": 0.50,
        "imgsz": 1024,  # bom_detector.pt는 1024 최적
        "use_sahi": False,
        "augment": False,  # bom_detector.pt는 TTA 불필요
        "description": "파나시아 MCP Panel 전기 제어반 27종 심볼 검출 (F1 98%)",
    },
}

# 기본 모델 (설정이 없을 때 사용)
DEFAULT_MODEL_TYPE = "engineering"


def get_model_config(model_type: str, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    모델 타입에 맞는 설정을 반환

    Args:
        model_type: 모델 타입 (engineering, pid_symbol, bom_detector 등)
        overrides: 덮어쓸 파라미터 (None이 아닌 값만 적용)

    Returns:
        모델 설정 딕셔너리
    """
    # 기본 설정 가져오기 (없으면 engineering 사용)
    base_config = MODEL_DEFAULTS.get(model_type, MODEL_DEFAULTS[DEFAULT_MODEL_TYPE]).copy()

    # 오버라이드 적용 (None이 아닌 값만)
    if overrides:
        for key, value in overrides.items():
            if value is not None:
                base_config[key] = value

    return base_config


def get_sahi_config(model_type: str) -> Dict[str, Any]:
    """
    SAHI 슬라이싱 설정 반환

    Args:
        model_type: 모델 타입

    Returns:
        SAHI 설정 딕셔너리 (use_sahi, slice_size, overlap_ratio)
    """
    config = MODEL_DEFAULTS.get(model_type, MODEL_DEFAULTS[DEFAULT_MODEL_TYPE])

    return {
        "use_sahi": config.get("use_sahi", False),
        "slice_size": config.get("slice_size", 640),
        "overlap_ratio": config.get("overlap_ratio", 0.2),
    }


def list_available_models() -> Dict[str, str]:
    """
    사용 가능한 모델 목록과 설명 반환

    Returns:
        모델 타입 -> 설명 딕셔너리
    """
    return {
        model_type: config.get("description", config.get("name", model_type))
        for model_type, config in MODEL_DEFAULTS.items()
    }
