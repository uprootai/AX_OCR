"""BOM Schemas"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ExportFormat(str, Enum):
    """내보내기 형식"""
    EXCEL = "excel"
    PDF = "pdf"
    JSON = "json"
    CSV = "csv"


class BOMItem(BaseModel):
    """BOM 항목"""
    item_no: int = Field(description="항목 번호")
    class_id: int = Field(description="클래스 ID")
    class_name: str = Field(description="부품명")
    model_name: Optional[str] = Field(default=None, description="모델명")
    quantity: int = Field(ge=1, description="수량")
    unit_price: float = Field(ge=0, description="단가")
    total_price: float = Field(ge=0, description="합계")
    avg_confidence: float = Field(ge=0, le=1, description="평균 신뢰도")
    detection_ids: List[str] = Field(default=[], description="검출 ID 목록")
    lead_time: Optional[str] = Field(default=None, description="납기")
    remarks: Optional[str] = Field(default=None, description="비고")
    dimensions: List[str] = Field(default=[], description="연결된 치수 정보")
    linked_dimension_ids: List[str] = Field(default=[], description="연결된 치수 ID 목록")


class BOMSummary(BaseModel):
    """BOM 요약"""
    total_items: int = Field(description="총 품목 수")
    total_quantity: int = Field(description="총 수량")
    subtotal: float = Field(description="소계")
    vat: float = Field(description="부가세 (10%)")
    total: float = Field(description="합계")


class BOMData(BaseModel):
    """BOM 데이터"""
    session_id: str
    created_at: datetime
    items: List[BOMItem]
    summary: BOMSummary

    # 메타데이터
    filename: Optional[str] = None
    model_id: Optional[str] = None
    detection_count: int = 0
    approved_count: int = 0


class BOMExportRequest(BaseModel):
    """BOM 내보내기 요청"""
    session_id: str
    format: ExportFormat = ExportFormat.EXCEL
    include_image: bool = False
    customer_name: Optional[str] = None
    customer_info: Optional[Dict[str, Any]] = None


class BOMExportResponse(BaseModel):
    """BOM 내보내기 응답"""
    session_id: str
    format: ExportFormat
    filename: str
    file_path: str
    file_size: int
    created_at: datetime
