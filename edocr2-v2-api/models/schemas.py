"""
Pydantic Models for eDOCr2 API
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str


class OCRRequest(BaseModel):
    extract_dimensions: bool = Field(True, description="Extract dimension information")
    extract_gdt: bool = Field(True, description="Extract GD&T information")
    extract_text: bool = Field(True, description="Extract text information")
    use_vl_model: bool = Field(False, description="Use Vision Language model (GPT-4o/Qwen2-VL)")
    visualize: bool = Field(False, description="Generate visualization image")
    use_gpu_preprocessing: bool = Field(False, description="Use GPU preprocessing (CLAHE, denoising)")


class DimensionData(BaseModel):
    value: Any  # Can be float or str (for recognized text dimensions)
    unit: str
    type: str
    tolerance: Optional[str] = None
    location: Optional[Any] = None  # Can be dict or list


class GDTData(BaseModel):
    type: str
    value: float
    datum: Optional[str] = None
    location: Optional[Dict[str, float]] = None


class PossibleTextData(BaseModel):
    """Text annotations or labels found but not classified as dimensions"""
    text: str
    location: Optional[Any] = None


class TextData(BaseModel):
    drawing_number: Optional[str] = None
    revision: Optional[str] = None
    title: Optional[str] = None
    material: Optional[str] = None
    notes: Optional[List[str]] = None


class OCRResponse(BaseModel):
    status: str
    data: Dict[str, Any]
    processing_time: float
    file_id: str
