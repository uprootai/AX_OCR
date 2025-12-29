"""
Tesseract OCR API Schemas
"""
from typing import Optional, List
from pydantic import BaseModel


class OCRResult(BaseModel):
    text: str
    confidence: float
    bbox: Optional[List[int]] = None
    level: Optional[int] = None  # Tesseract output level


class OCRResponse(BaseModel):
    success: bool
    texts: List[OCRResult]
    full_text: str
    language: str
    processing_time_ms: float
    tesseract_version: Optional[str] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    tesseract_available: bool
    tesseract_version: Optional[str] = None
    timestamp: str
