"""
VL API Schemas
Pydantic 모델 정의
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str
    available_models: List[str]


class InfoBlockRequest(BaseModel):
    query_fields: List[str] = Field(
        default=["name", "part number", "material", "scale", "weight"],
        description="추출할 정보 필드 목록"
    )
    model: str = Field(default="claude-3-5-sonnet-20241022", description="사용할 VL 모델")


class InfoBlockResponse(BaseModel):
    status: str
    data: Dict[str, str]
    processing_time: float
    model_used: str


class DimensionExtractionRequest(BaseModel):
    model: str = Field(default="claude-3-5-sonnet-20241022", description="사용할 VL 모델")


class DimensionExtractionResponse(BaseModel):
    status: str
    data: List[str]
    processing_time: float
    model_used: str


class ManufacturingProcessRequest(BaseModel):
    model: str = Field(default="gpt-4o", description="사용할 VL 모델")


class ManufacturingProcessResponse(BaseModel):
    status: str
    data: Dict[str, str]
    processing_time: float
    model_used: str


class QCChecklistRequest(BaseModel):
    model: str = Field(default="gpt-4o", description="사용할 VL 모델")


class QCChecklistResponse(BaseModel):
    status: str
    data: List[str]
    processing_time: float
    model_used: str


class AnalyzeRequest(BaseModel):
    """범용 VQA (Visual Question Answering) 요청"""
    model: str = Field(default="claude-3-5-sonnet-20241022", description="사용할 VL 모델")
    temperature: float = Field(default=0.0, ge=0.0, le=1.0, description="생성 temperature")


class AnalyzeResponse(BaseModel):
    """범용 VQA 응답"""
    status: str
    mode: str = Field(description="분석 모드: 'vqa' (질문-답변) 또는 'captioning' (일반 설명)")
    answer: Optional[str] = Field(None, description="질문에 대한 답변 (VQA 모드)")
    caption: Optional[str] = Field(None, description="이미지 설명 (캡셔닝 모드)")
    question: Optional[str] = Field(None, description="사용자 질문 (VQA 모드)")
    confidence: float = Field(default=1.0, description="답변 신뢰도")
    processing_time: float
    model_used: str
