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


class HealthResponse(BaseModel):
    """헬스체크 응답"""
    status: str = Field(default="healthy")
    service: str = Field(default="paddleocr-api")
    version: str = Field(default="1.0.0")
    gpu_available: bool = Field(..., description="GPU 사용 가능 여부")
    model_loaded: bool = Field(..., description="모델 로드 여부")
    lang: str = Field(..., description="OCR 언어 설정")
