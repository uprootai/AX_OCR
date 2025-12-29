"""
Surya OCR API Schemas
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str
    gpu_available: Optional[bool] = None


class TextLine(BaseModel):
    text: str
    confidence: float
    bbox: List[float]


class LayoutElement(BaseModel):
    type: str
    bbox: List[float]
    confidence: float


class OCRResult(BaseModel):
    success: bool
    texts: List[TextLine]
    full_text: str
    layout: Optional[List[LayoutElement]] = None
    language: str
    processing_time: float
    error: Optional[str] = None


class ProcessResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    processing_time: float
    error: Optional[str] = None
