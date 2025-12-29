"""
TrOCR API Schemas
"""
from typing import Optional, List
from pydantic import BaseModel


class OCRResult(BaseModel):
    text: str
    confidence: float
    bbox: Optional[List[int]] = None


class OCRResponse(BaseModel):
    success: bool
    texts: List[OCRResult]
    full_text: str
    model: str
    device: str
    processing_time_ms: float
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    trocr_available: bool
    model_loaded: bool
    model_name: str
    device: str
    timestamp: str
