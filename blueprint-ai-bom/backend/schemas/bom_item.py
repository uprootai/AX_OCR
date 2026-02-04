"""BOM Item Schemas - BOM 계층 구조 스키마

BOM PDF 파싱 결과를 나타내는 스키마.
행 배경색으로 계층을 구분:
- PINK: Assembly (조립체)
- BLUE: Subassembly (하위 조립체)
- WHITE: Part (단품) → 견적 대상
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class BOMLevel(str, Enum):
    """BOM 계층 레벨 (PDF 행 배경색 기반)"""
    ASSEMBLY = "assembly"          # PINK 행
    SUBASSEMBLY = "subassembly"    # BLUE 행
    PART = "part"                  # WHITE 행


class BOMItemParsed(BaseModel):
    """BOM PDF에서 파싱된 개별 항목"""
    item_no: str = Field(..., description="품번 (BOM 테이블의 No.)")
    level: BOMLevel = Field(..., description="계층 레벨 (assembly/subassembly/part)")
    drawing_number: str = Field(..., description="도면번호 (예: TD0062017)")
    description: str = Field(default="", description="품명/설명")
    material: str = Field(default="", description="재질 (예: SF45A)")
    quantity: int = Field(default=1, description="수량")
    parent_item_no: Optional[str] = Field(None, description="부모 항목 품번")
    needs_quotation: bool = Field(
        default=False,
        description="견적 필요 여부 (WHITE 항목만 True)"
    )
    matched_file: Optional[str] = Field(None, description="매칭된 도면 파일 경로")
    session_id: Optional[str] = Field(None, description="생성된 BOM 세션 ID")


class BOMHierarchyResponse(BaseModel):
    """BOM 계층 트리 응답"""
    project_id: str
    bom_source: str = Field(default="", description="원본 BOM PDF 파일명")
    total_items: int = Field(default=0, description="전체 BOM 항목 수")
    assembly_count: int = Field(default=0, description="ASSEMBLY(PINK) 수")
    subassembly_count: int = Field(default=0, description="SUBASSEMBLY(BLUE) 수")
    part_count: int = Field(default=0, description="PART(WHITE) 수")
    items: List[BOMItemParsed] = Field(default_factory=list, description="전체 항목 (flat)")
    hierarchy: List[Dict[str, Any]] = Field(
        default_factory=list, description="계층 트리 구조"
    )


class DrawingMatchRequest(BaseModel):
    """도면 매칭 요청"""
    drawing_folder: str = Field(..., description="도면 폴더 경로 (예: /path/to/PJT/04_부품도면)")


class DrawingMatchResult(BaseModel):
    """도면 매칭 결과"""
    project_id: str
    total_items: int = 0
    matched_count: int = 0
    unmatched_count: int = 0
    items: List[BOMItemParsed] = Field(default_factory=list)


class SessionBatchCreateRequest(BaseModel):
    """세션 일괄 생성 요청"""
    template_name: Optional[str] = Field(
        "DSE Bearing 1-1",
        description="적용할 템플릿 이름"
    )
    only_matched: bool = Field(
        default=True,
        description="매칭된 도면만 세션 생성 (True 권장)"
    )


class SessionBatchCreateResponse(BaseModel):
    """세션 일괄 생성 응답"""
    project_id: str
    created_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    sessions: List[Dict[str, Any]] = Field(default_factory=list)
    message: str = ""
