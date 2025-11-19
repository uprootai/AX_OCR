"""
EDGNet API Services
"""
from .inference import (
    EDGNetInferenceService,
    check_edgnet_availability,
    check_model_exists
)

__all__ = [
    "EDGNetInferenceService",
    "check_edgnet_availability",
    "check_model_exists"
]
