"""
Pydantic Models for Skin Model API
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    timestamp: str


class DimensionInput(BaseModel):
    """Dimension input data"""
    type: str = Field(..., description="치수 타입 (diameter, length, angle, etc.)")
    value: float = Field(..., description="치수 값")
    tolerance: Optional[float] = Field(None, description="공차 값")
    unit: str = Field("mm", description="단위")


class MaterialInput(BaseModel):
    """Material properties input"""
    name: str = Field("Steel", description="재질명")
    youngs_modulus: Optional[float] = Field(None, description="영계수 (GPa)")
    poisson_ratio: Optional[float] = Field(None, description="포아송 비")
    density: Optional[float] = Field(None, description="밀도 (kg/m³)")


class ToleranceRequest(BaseModel):
    """Tolerance prediction request"""
    dimensions: List[DimensionInput]
    material: MaterialInput | str = Field(..., description="재질 (MaterialInput object or string: aluminum/steel/stainless/titanium/plastic)")
    manufacturing_process: str = Field("machining", description="제조 공정 (machining, casting, 3d_printing, welding, sheet_metal)")
    correlation_length: float = Field(1.0, description="Random Field 상관 길이")
    task: Optional[str] = Field("tolerance", description="분석 작업 (tolerance, validate, manufacturability)")


class TolerancePrediction(BaseModel):
    """Predicted tolerance values"""
    flatness: float
    cylindricity: float
    position: float
    perpendicularity: Optional[float] = None


class ManufacturabilityScore(BaseModel):
    """Manufacturability assessment"""
    score: float = Field(..., ge=0, le=1, description="제조 가능성 점수 (0-1)")
    difficulty: str = Field(..., description="난이도 (Easy, Medium, Hard)")
    recommendations: List[str]


class AssemblabilityScore(BaseModel):
    """Assemblability assessment"""
    score: float = Field(..., ge=0, le=1)
    clearance: float
    interference_risk: str


class ToleranceResponse(BaseModel):
    """Tolerance prediction response"""
    status: str
    data: Dict[str, Any]
    processing_time: float


class GDTValidateRequest(BaseModel):
    """GD&T validation request"""
    dimensions: List[DimensionInput]
    gdt_specs: Dict[str, float] = Field(..., description="GD&T 요구사항")
    material: MaterialInput


class GDTValidateResponse(BaseModel):
    """GD&T validation response"""
    status: str
    data: Dict[str, Any]
    processing_time: float


class ParameterSchema(BaseModel):
    """파라미터 스키마"""
    name: str
    type: str  # 'number', 'string', 'boolean', 'select'
    default: Any
    description: str
    required: bool = False
    options: Optional[list] = None
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
    requires_image: bool = False
    inputs: list
    outputs: list
    parameters: list
    blueprintflow: BlueprintFlowMetadata
    output_mappings: Dict[str, str]
