"""
services.customer_config — Barrel re-export

기존 `from services.customer_config import X` 임포트 경로 유지
"""

# Data models
from .models import CustomerSettings, OutputTemplate, ParsingProfile

# Service
from .service import CustomerConfigService

# Singleton factory
from .service import CustomerConfigService as _CustomerConfigService

# Model routing
from .model_routing import (
    CUSTOMER_TO_MODEL_MAP,
    DRAWING_TYPE_TO_MODEL_MAP,
    get_model_for_customer,
    list_available_models,
)

# Singleton instance (lazy)
_customer_config_instance = None


def get_customer_config(config_dir=None) -> CustomerConfigService:
    """고객 설정 서비스 인스턴스 반환"""
    global _customer_config_instance
    if _customer_config_instance is None:
        _customer_config_instance = _CustomerConfigService(config_dir)
    return _customer_config_instance


__all__ = [
    # models
    "ParsingProfile",
    "OutputTemplate",
    "CustomerSettings",
    # service
    "CustomerConfigService",
    # singleton
    "get_customer_config",
    # model routing
    "CUSTOMER_TO_MODEL_MAP",
    "DRAWING_TYPE_TO_MODEL_MAP",
    "get_model_for_customer",
    "list_available_models",
]
