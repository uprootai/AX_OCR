"""
Pydantic Models for YOLO API
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Detection(BaseModel):
    """단일 검출 결과"""
    class_id: int = Field(..., description="클래스 ID (0-13)")
    class_name: str = Field(..., description="클래스 이름")
    confidence: float = Field(..., description="신뢰도 (0-1)")
    bbox: Dict[str, int] = Field(..., description="바운딩 박스 {x, y, width, height}")
    value: Optional[str] = Field(None, description="검출된 텍스트 값 (OCR 필요)")


class SVGOverlay(BaseModel):
    """SVG 오버레이 데이터"""
    svg: str = Field(..., description="인터랙티브 SVG 문자열 (라벨 포함)")
    svg_minimal: str = Field(..., description="최소 SVG 문자열 (박스만)")
    width: int = Field(..., description="이미지 너비")
    height: int = Field(..., description="이미지 높이")
    detection_count: int = Field(..., description="검출 개수")
    model_type: str = Field(..., description="모델 타입")


class DetectionResponse(BaseModel):
    """검출 API 응답"""
    status: str = Field(default="success")
    file_id: str = Field(..., description="파일 ID")
    detections: List[Detection] = Field(..., description="검출 목록")
    total_detections: int = Field(..., description="총 검출 개수")
    processing_time: float = Field(..., description="처리 시간 (초)")
    model_used: str = Field(..., description="사용된 모델")
    image_size: Dict[str, int] = Field(..., description="이미지 크기")
    visualized_image: Optional[str] = Field(None, description="Base64 encoded visualization image")
    svg_overlay: Optional[SVGOverlay] = Field(None, description="SVG 오버레이 데이터 (include_svg=True 시)")


class DimensionExtraction(BaseModel):
    """치수 추출 결과"""
    dimensions: List[Detection]
    gdt_symbols: List[Detection]
    surface_roughness: List[Detection]
    text_blocks: List[Detection]


class HealthResponse(BaseModel):
    """Health check 응답"""
    status: str = "healthy"
    model_loaded: bool
    model_path: str
    device: str
    gpu_available: bool
    gpu_name: Optional[str] = None


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
    type: str  # 'string', 'array', 'integer', 'float', 'boolean', 'object'
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
