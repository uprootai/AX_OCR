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
