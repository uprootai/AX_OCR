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


class ParameterSchema(BaseModel):
    """파라미터 스키마"""
    name: str
    type: str  # 'number', 'string', 'boolean', 'select'
    default: Any
    description: str
    required: bool = False
    options: Optional[List[str]] = None
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None


class IOSchema(BaseModel):
    """입출력 스키마"""
    name: str
    type: str  # 'string', 'array', 'integer', 'float', 'boolean', 'object', 'file'
    description: str
    required: bool = True


class BlueprintFlowMetadata(BaseModel):
    """BlueprintFlow 노드 메타데이터"""
    icon: str
    color: str
    category: str


class APIInfoResponse(BaseModel):
    """API 메타데이터 응답"""
    id: str
    name: str
    display_name: str
    version: str
    description: str
    openapi_url: str
    base_url: str
    endpoint: str
    method: str = "POST"
    requires_image: bool = True
    inputs: List[IOSchema]
    outputs: List[IOSchema]
    parameters: List[ParameterSchema]
    blueprintflow: BlueprintFlowMetadata
    output_mappings: Dict[str, str]
