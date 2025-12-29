"""
EDGNet Global State Management

Manages global service instances for the EDGNet API.
"""
from typing import Optional

from services.inference import EDGNetInferenceService
from services.unet_inference import UNetInferenceService

# Global inference services
_edgnet_service: Optional[EDGNetInferenceService] = None
_unet_service: Optional[UNetInferenceService] = None


def get_edgnet_service() -> Optional[EDGNetInferenceService]:
    """Get global EDGNet (GraphSAGE) service instance"""
    return _edgnet_service


def get_unet_service() -> Optional[UNetInferenceService]:
    """Get global UNet service instance"""
    return _unet_service


def set_services(
    edgnet_service: Optional[EDGNetInferenceService],
    unet_service: Optional[UNetInferenceService]
):
    """Set global service instances (called from lifespan)"""
    global _edgnet_service, _unet_service
    _edgnet_service = edgnet_service
    _unet_service = unet_service
