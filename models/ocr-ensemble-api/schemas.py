"""
OCR Ensemble Schemas
Pydantic models for API request/response
"""
from typing import Optional, List, Dict
from pydantic import BaseModel


class OCRResult(BaseModel):
    """Individual OCR result from a single engine"""
    text: str
    confidence: float
    bbox: Optional[List[int]] = None
    source: str  # Which OCR engine produced this result


class EnsembleResult(BaseModel):
    """Merged result from ensemble voting"""
    text: str
    confidence: float
    bbox: Optional[List[int]] = None
    votes: Dict[str, float]  # Weighted votes from each engine
    sources: List[str]  # Engines that returned this result


class EnsembleResponse(BaseModel):
    """API response for ensemble OCR"""
    success: bool
    results: List[EnsembleResult]
    full_text: str
    engine_results: Dict[str, List[OCRResult]]  # Raw results per engine
    engine_status: Dict[str, str]  # Status of each engine
    weights_used: Dict[str, float]
    processing_time_ms: float
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    engines: Dict[str, str]
    timestamp: str
