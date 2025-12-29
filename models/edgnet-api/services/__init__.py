"""
EDGNet API Services
"""
from .inference import (
    EDGNetInferenceService,
    check_edgnet_availability,
    check_model_exists
)
from .unet_inference import (
    UNetInferenceService,
    check_unet_model_exists
)
from .state import (
    get_edgnet_service,
    get_unet_service,
    set_services
)

__all__ = [
    "EDGNetInferenceService",
    "check_edgnet_availability",
    "check_model_exists",
    "UNetInferenceService",
    "check_unet_model_exists",
    "get_edgnet_service",
    "get_unet_service",
    "set_services",
]
