"""
Pydantic Models for EDGNet API
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    timestamp: str


class SegmentRequest(BaseModel):
    """Segmentation request parameters"""
    visualize: bool = Field(True, description="시각화 이미지 생성 여부")
    num_classes: int = Field(3, description="분류 클래스 수 (2 or 3)")
    save_graph: bool = Field(False, description="그래프 데이터 저장 여부")


class ClassificationStats(BaseModel):
    """Classification statistics"""
    contour: int = Field(0, description="윤곽선 컴포넌트 수")
    text: int = Field(0, description="텍스트 컴포넌트 수")
    dimension: int = Field(0, description="치수 컴포넌트 수")


class GraphStats(BaseModel):
    """Graph statistics"""
    nodes: int
    edges: int
    avg_degree: float


class SegmentResponse(BaseModel):
    """Segmentation response"""
    status: str
    data: Dict[str, Any]
    processing_time: float
    file_id: str


class VectorizeRequest(BaseModel):
    """Vectorization request parameters"""
    save_bezier: bool = Field(True, description="Bezier 곡선 저장 여부")


class VectorizeResponse(BaseModel):
    """Vectorization response"""
    status: str
    data: Dict[str, Any]
    processing_time: float
    file_id: str


class UNetSegmentRequest(BaseModel):
    """UNet 세그멘테이션 요청 파라미터"""
    threshold: float = Field(0.5, description="세그멘테이션 임계값 (0.0~1.0)", ge=0.0, le=1.0)
    visualize: bool = Field(True, description="세그멘테이션 결과 시각화 생성 여부")
    return_mask: bool = Field(False, description="세그멘테이션 마스크 반환 여부 (base64)")


class UNetSegmentResponse(BaseModel):
    """UNet 세그멘테이션 응답"""
    status: str = Field(..., description="처리 상태 (success/error)")
    data: Dict[str, Any] = Field(..., description="세그멘테이션 결과 데이터")
    processing_time: float = Field(..., description="처리 시간 (초)")
    file_id: str = Field(..., description="업로드된 파일 ID")


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
    requires_image: bool = True
    inputs: list
    outputs: list
    parameters: list
    blueprintflow: BlueprintFlowMetadata
    output_mappings: Dict[str, str]
