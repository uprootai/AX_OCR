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
