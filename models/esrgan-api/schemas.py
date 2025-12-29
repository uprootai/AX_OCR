"""
ESRGAN Schemas
Pydantic models for API request/response
"""
from typing import Optional
from pydantic import BaseModel


class UpscaleResponse(BaseModel):
    """Response for upscale endpoints"""
    success: bool
    original_size: dict
    upscaled_size: dict
    scale: int
    model: str
    device: str
    processing_time_ms: float
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    realesrgan_available: bool
    model_loaded: bool
    device: str
    timestamp: str
