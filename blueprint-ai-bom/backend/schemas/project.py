"""Project Schemas - 프로젝트(고객사) 관리 스키마

Phase 2: 프로젝트 기반 도면 관리
- 고객사별 프로젝트 단위 관리
- 프로젝트별 기본 템플릿 설정
- GT/참조도면 폴더 관리
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict


class ProjectCreate(BaseModel):
    """프로젝트 생성 요청"""
    name: str = Field(..., description="프로젝트명", example="파나시아 BWMS")
    customer: str = Field(..., description="고객사명", example="파나시아")
    description: Optional[str] = Field(None, description="프로젝트 설명")
    project_type: Optional[Literal["bom_quotation", "pid_detection", "general"]] = Field(
        "general",
        description="프로젝트 타입 (선택사항)"
    )
    default_template_id: Optional[str] = Field(None, description="기본 템플릿 ID")

    # 기본 설정 (템플릿 없이 사용 시)
    default_model_type: Optional[str] = Field(
        None,
        description="기본 YOLO 모델",
        example="pid_symbol"
    )
    default_features: List[str] = Field(
        default_factory=list,
        description="기본 활성화 기능",
        example=["symbol_detection", "gt_comparison"]
    )

    # BOM 프로젝트 확장
    bom_source: Optional[str] = Field(None, description="BOM PDF 파일명")
    drawing_folder: Optional[str] = Field(None, description="도면 폴더 경로")


class ProjectUpdate(BaseModel):
    """프로젝트 수정 요청"""
    name: Optional[str] = None
    customer: Optional[str] = None
    project_type: Optional[Literal["bom_quotation", "pid_detection", "general"]] = None
    description: Optional[str] = None
    default_template_id: Optional[str] = None
    default_model_type: Optional[str] = None
    default_features: Optional[List[str]] = None
    gt_folder: Optional[str] = None
    reference_folder: Optional[str] = None
    bom_source: Optional[str] = None
    drawing_folder: Optional[str] = None


class ProjectResponse(BaseModel):
    """프로젝트 응답"""
    model_config = ConfigDict(from_attributes=True)

    project_id: str
    name: str
    customer: str
    description: Optional[str] = None
    project_type: str = Field(default="general", description="프로젝트 타입")

    # 템플릿 연결
    default_template_id: Optional[str] = None
    default_template_name: Optional[str] = None  # 조인된 템플릿명

    # 기본 설정
    default_model_type: Optional[str] = None
    default_features: List[str] = Field(default_factory=list)

    # 폴더 경로
    gt_folder: Optional[str] = None
    reference_folder: Optional[str] = None

    # BOM 프로젝트 확장
    bom_source: Optional[str] = Field(None, description="BOM PDF 파일명")
    drawing_folder: Optional[str] = Field(None, description="도면 폴더 경로")

    # 통계
    session_count: int = 0
    completed_count: int = 0
    pending_count: int = 0

    # BOM 견적 통계
    bom_item_count: int = Field(default=0, description="전체 BOM 항목 수")
    quotation_item_count: int = Field(default=0, description="견적 대상 (WHITE) 수")
    quoted_count: int = Field(default=0, description="견적 완료 수")
    total_quotation: float = Field(default=0.0, description="총 견적가")

    # 메타
    created_at: datetime
    updated_at: datetime


class ProjectDetail(ProjectResponse):
    """프로젝트 상세 (세션 목록 포함)"""
    sessions: List[Dict[str, Any]] = Field(default_factory=list)
    template: Optional[Dict[str, Any]] = None


class ProjectListResponse(BaseModel):
    """프로젝트 목록 응답"""
    projects: List[ProjectResponse]
    total: int


class ProjectBatchUploadRequest(BaseModel):
    """도면 일괄 업로드 요청"""
    template_id: Optional[str] = Field(
        None,
        description="사용할 템플릿 ID (없으면 프로젝트 기본 템플릿)"
    )
    auto_detect: bool = Field(
        True,
        description="업로드 후 자동 검출 실행"
    )


class ProjectBatchUploadResponse(BaseModel):
    """도면 일괄 업로드 응답"""
    project_id: str
    uploaded_count: int
    session_ids: List[str]
    failed_files: List[str] = Field(default_factory=list)
    message: str
