"""
DocTR API Schemas
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str
    gpu_available: Optional[bool] = None


class WordResult(BaseModel):
    text: str
    confidence: float
    bbox: List[float]


class LineResult(BaseModel):
    text: str
    words: List[WordResult]
    bbox: List[float]


class BlockResult(BaseModel):
    lines: List[LineResult]
    bbox: List[float]


class ProcessResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    processing_time: float
    error: Optional[str] = None
