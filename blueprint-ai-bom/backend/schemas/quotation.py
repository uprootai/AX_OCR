"""Quotation Schemas - 견적 집계 스키마

Phase 3: 프로젝트 내 모든 세션 BOM → 재질별 그룹 집계 → PDF/Excel 견적서 내보내기
"""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class SessionQuotationItem(BaseModel):
    """세션별 견적 항목"""
    session_id: str
    drawing_number: str = ""
    bom_item_no: str = ""
    description: str = ""
    material: str = ""
    bom_quantity: int = 1
    quote_status: str = "pending"       # pending | quoted
    bom_item_count: int = 0             # 세션 내 BOM 품목 수
    subtotal: float = 0.0               # session.bom_data.summary.subtotal
    vat: float = 0.0
    total: float = 0.0
    session_status: str = "uploaded"
    bom_generated: bool = False


class MaterialGroup(BaseModel):
    """재질별 그룹"""
    material: str
    item_count: int = 0
    total_quantity: int = 0
    subtotal: float = 0.0
    items: List[SessionQuotationItem] = Field(default_factory=list)


class QuotationSummary(BaseModel):
    """견적 요약 통계"""
    total_sessions: int = 0
    completed_sessions: int = 0         # bom_generated == True
    pending_sessions: int = 0
    quoted_sessions: int = 0            # quote_status == "quoted"
    total_items: int = 0
    subtotal: float = 0.0
    vat: float = 0.0                    # subtotal × 0.1
    total: float = 0.0                  # subtotal + vat
    progress_percent: float = 0.0


class ProjectQuotationResponse(BaseModel):
    """프로젝트 견적 집계 응답"""
    project_id: str
    project_name: str = ""
    customer: str = ""
    created_at: str
    summary: QuotationSummary
    items: List[SessionQuotationItem] = Field(default_factory=list)
    material_groups: List[MaterialGroup] = Field(default_factory=list)


class QuotationExportFormat(str, Enum):
    """견적서 내보내기 형식"""
    PDF = "pdf"
    EXCEL = "excel"


class QuotationExportRequest(BaseModel):
    """견적서 내보내기 요청"""
    format: QuotationExportFormat = QuotationExportFormat.PDF
    customer_name: Optional[str] = None
    include_material_breakdown: bool = True
    notes: Optional[str] = None


class QuotationExportResponse(BaseModel):
    """견적서 내보내기 응답"""
    project_id: str
    format: QuotationExportFormat
    filename: str
    file_path: str
    file_size: int
    created_at: str
