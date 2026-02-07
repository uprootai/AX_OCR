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
    # 원가 내역 (Phase 4)
    material_cost: float = 0.0
    machining_cost: float = 0.0
    weight_kg: float = 0.0
    raw_dimensions: Optional[dict] = None
    cost_source: str = "none"           # "calculated" | "estimated" | "none"
    # 어셈블리 귀속 및 개정 추적
    assembly_drawing_number: Optional[str] = Field(
        None, description="소속 어셈블리 도면번호"
    )
    doc_revision: Optional[str] = Field(None, description="도면 개정번호")
    bom_revision: Optional[int] = Field(None, description="BOM 항목 개정번호")
    part_no: Optional[str] = Field(None, description="BOM Part No")
    size: Optional[str] = Field(None, description="BOM 규격/사이즈")
    remark: Optional[str] = Field(None, description="비고")


class MaterialGroup(BaseModel):
    """재질별 그룹"""
    material: str
    item_count: int = 0
    total_quantity: int = 0
    subtotal: float = 0.0
    total_weight: float = 0.0
    material_cost_sum: float = 0.0
    items: List[SessionQuotationItem] = Field(default_factory=list)


class AssemblyQuotationGroup(BaseModel):
    """어셈블리 단위 견적 그룹"""
    assembly_drawing_number: str
    assembly_description: str = ""
    bom_weight_kg: float = 0.0
    total_parts: int = 0
    quoted_parts: int = 0
    progress_percent: float = 0.0
    subtotal: float = 0.0
    vat: float = 0.0
    total: float = 0.0
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
    assembly_groups: List[AssemblyQuotationGroup] = Field(
        default_factory=list,
        description="어셈블리 단위 견적 그룹"
    )


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
