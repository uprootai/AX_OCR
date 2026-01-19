"""
Pydantic Models for PaddleOCR API
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class TextDetection(BaseModel):
    """텍스트 검출 결과"""
    text: str = Field(..., description="검출된 텍스트")
    confidence: float = Field(..., description="신뢰도 (0-1)")
    bbox: List[List[float]] = Field(..., description="바운딩 박스 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]")
    position: Dict[str, float] = Field(..., description="위치 정보 {x, y, width, height}")


class OCRResponse(BaseModel):
    """OCR 응답"""
    status: str = Field(default="success")
    processing_time: float = Field(..., description="처리 시간 (초)")
    total_texts: int = Field(..., description="검출된 텍스트 총 개수")
    detections: List[TextDetection] = Field(..., description="텍스트 검출 목록")
    metadata: Dict[str, Any] = Field(..., description="메타데이터")
    visualized_image: Optional[str] = Field(None, description="시각화 이미지 (base64)")
    svg_overlay: Optional[str] = Field(None, description="SVG 오버레이 (프론트엔드용)")
    svg_minimal: Optional[str] = Field(None, description="최소 SVG 오버레이 (라벨 없음)")


class HealthResponse(BaseModel):
    """헬스체크 응답"""
    status: str = Field(default="healthy")
    service: str = Field(default="paddleocr-api")
    version: str = Field(default="3.0.0")
    gpu_available: bool = Field(..., description="GPU 사용 가능 여부")
    model_loaded: bool = Field(..., description="모델 로드 여부")
    lang: str = Field(..., description="OCR 언어 설정")
    ocr_version: str = Field(default="PP-OCRv4", description="OCR 모델 버전")


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
