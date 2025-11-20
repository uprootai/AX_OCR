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
    material: MaterialInput
    manufacturing_process: str = Field("machining", description="제조 공정 (machining, casting, 3d_printing)")
    correlation_length: float = Field(1.0, description="Random Field 상관 길이")


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
