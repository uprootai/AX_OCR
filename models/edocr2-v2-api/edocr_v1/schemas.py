"""
eDOCr v1 Pydantic Schemas
OCR 요청/응답 모델 정의
"""

from typing import Optional, Dict, List
from pydantic import BaseModel, Field


class OCRRequest(BaseModel):
    """Standard OCR request parameters"""
    extract_dimensions: bool = Field(True, description="치수 정보 추출 여부")
    extract_gdt: bool = Field(True, description="GD&T 정보 추출 여부")
    extract_text: bool = Field(True, description="텍스트 정보 추출 여부")
    visualize: bool = Field(False, description="시각화 이미지 생성 여부")
    remove_watermark: bool = Field(False, description="워터마크 제거 여부")
    cluster_threshold: int = Field(20, description="치수 클러스터링 임계값 (px)")


class EnhancedOCRRequest(BaseModel):
    """Enhanced OCR with performance improvement strategies"""
    extract_dimensions: bool = Field(True, description="치수 정보 추출 여부")
    extract_gdt: bool = Field(True, description="GD&T 정보 추출 여부")
    extract_text: bool = Field(True, description="텍스트 정보 추출 여부")
    visualize: bool = Field(False, description="시각화 이미지 생성 여부")
    remove_watermark: bool = Field(False, description="워터마크 제거 여부")
    cluster_threshold: int = Field(20, description="치수 클러스터링 임계값 (px)")
    strategy: str = Field("edgnet", description="Enhancement strategy: basic, edgnet, vl, hybrid")
    vl_provider: str = Field("openai", description="VL provider: openai, anthropic")


class Dimension(BaseModel):
    """Dimension detection result"""
    type: str
    value: float
    unit: str
    tolerance: Optional[str] = None
    location: Dict[str, float]


class GDT(BaseModel):
    """GD&T (Geometric Dimensioning and Tolerancing) result"""
    type: str
    value: float
    datum: Optional[str] = None
    location: Dict[str, float]


class TextInfo(BaseModel):
    """Extracted text/infoblock information"""
    drawing_number: Optional[str] = None
    revision: Optional[str] = None
    title: Optional[str] = None
    material: Optional[str] = None
    notes: Optional[List[str]] = None
    total_blocks: int = 0


class OCRResult(BaseModel):
    """OCR processing result"""
    dimensions: List[Dimension]
    gdt: List[GDT]
    text: TextInfo
    visualization_url: Optional[str] = None


class OCRResponse(BaseModel):
    """Standard OCR API response"""
    status: str
    data: OCRResult
    processing_time: float
    file_id: str
