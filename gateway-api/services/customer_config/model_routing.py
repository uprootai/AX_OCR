"""
Customer Config — Model Routing

고객/도면 타입별 YOLO 모델 자동 선택 매핑
"""

from typing import Any, Dict, List, Optional


# ── 고객-모델 매핑 ─────────────────────────────────────────────────────────────
# model_registry.yaml의 모델 ID와 매핑

CUSTOMER_TO_MODEL_MAP: Dict[str, str] = {
    # BWMS/해양 - P&ID 심볼 모델
    "PANASIA": "pid_symbol",        # 파나시아 (BWMS 전문, P&ID 도면)
    "STX": "pid_symbol",            # STX조선해양 (선박 P&ID)
    "HANJIN": "pid_symbol",         # 한진중공업 (조선/해양)
    "HYUNDAI": "pid_symbol",        # 현대중공업 (조선/해양)

    # 전력 설비 - BOM 검출 모델
    "KEPCO": "bom_detector",        # 한국전력 (전력 설비 단선도)

    # 베어링/기계 - 기계도면 모델
    "DSE": "engineering",           # DSE Bearing (기계도면)
    "DOOSAN": "engineering",        # 두산에너빌리티 (발전설비 기계도면)

    # 해외 프로젝트 - 기본 모델
    "SAMSUNG": "engineering",       # 삼성물산 (기본)
}

# 도면 타입별 추천 모델
DRAWING_TYPE_TO_MODEL_MAP: Dict[str, str] = {
    "pid": "pid_symbol",            # P&ID 도면
    "pfd": "pid_symbol",            # 공정 흐름도
    "sld": "bom_detector",          # 전력 단선도
    "mechanical": "engineering",    # 기계도면
    "bearing": "engineering",       # 베어링 도면
    "mcp": "panasia",               # MCP 제어반
    "control_panel": "panasia",     # 제어반
}


def get_model_for_customer(
    customer_id: str,
    drawing_type: Optional[str] = None,
    default_model: str = "engineering"
) -> str:
    """
    고객 ID 또는 도면 타입에 따른 YOLO 모델 반환

    Args:
        customer_id: 고객 ID (DSE, PANASIA 등)
        drawing_type: 도면 타입 (pid, sld, mechanical 등)
        default_model: 매칭 실패 시 기본 모델

    Returns:
        YOLO 모델 ID (model_registry.yaml의 키)
    """
    # 1. 도면 타입으로 먼저 확인 (더 구체적)
    if drawing_type:
        drawing_type_lower = drawing_type.lower()
        if drawing_type_lower in DRAWING_TYPE_TO_MODEL_MAP:
            return DRAWING_TYPE_TO_MODEL_MAP[drawing_type_lower]

    # 2. 고객 ID로 확인
    customer_upper = customer_id.upper() if customer_id else ""
    if customer_upper in CUSTOMER_TO_MODEL_MAP:
        return CUSTOMER_TO_MODEL_MAP[customer_upper]

    # 3. 기본 모델 반환
    return default_model


def list_available_models() -> List[Dict[str, Any]]:
    """사용 가능한 모델 목록 반환"""
    return [
        {"model_id": "engineering", "name": "기계도면 심볼", "classes": 14},
        {"model_id": "pid_symbol", "name": "P&ID 심볼", "classes": 32},
        {"model_id": "pid_class_agnostic", "name": "P&ID 범용", "classes": 1},
        {"model_id": "pid_class_aware", "name": "P&ID 분류", "classes": 32},
        {"model_id": "bom_detector", "name": "전력 설비 단선도", "classes": 27},
        {"model_id": "panasia", "name": "파나시아 MCP Panel", "classes": 27},
    ]
