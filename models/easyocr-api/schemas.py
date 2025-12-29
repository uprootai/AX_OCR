"""
EasyOCR API Schemas
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str
    gpu_available: Optional[bool] = None
    gpu_enabled: Optional[bool] = None


class TextResult(BaseModel):
    text: str
    confidence: float
    bbox: List[List[int]]


class ProcessResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    processing_time: float
    error: Optional[str] = None
