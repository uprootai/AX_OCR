"""Template Schemas - 워크플로우 템플릿 스키마

Phase 2: 빌더에서 생성한 워크플로우를 템플릿으로 저장
- 노드/엣지 구조 저장
- 파라미터 설정 저장
- 프로젝트에 연결하여 재사용
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class TemplateNode(BaseModel):
    """워크플로우 노드"""
    id: str = Field(..., description="노드 ID")
    type: str = Field(..., description="노드 타입", example="yolo")
    position: Dict[str, float] = Field(
        ...,
        description="노드 위치",
        example={"x": 100, "y": 200}
    )
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="노드 데이터 (파라미터 포함)"
    )


class TemplateEdge(BaseModel):
    """워크플로우 엣지"""
    id: str = Field(..., description="엣지 ID")
    source: str = Field(..., description="소스 노드 ID")
    target: str = Field(..., description="타겟 노드 ID")
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None


class TemplateCreate(BaseModel):
    """템플릿 생성 요청 (빌더에서 저장)"""
    name: str = Field(..., description="템플릿명", example="P&ID 심볼검출 템플릿")
    description: Optional[str] = Field(None, description="템플릿 설명")

    # 검출 설정
    model_type: str = Field(
        ...,
        description="YOLO 모델 타입",
        example="pid_symbol"
    )

    # 검출 파라미터
    detection_params: Dict[str, Any] = Field(
        default_factory=lambda: {
            "confidence": 0.1,
            "iou": 0.45,
            "imgsz": 1024,
            "use_sahi": True
        },
        description="검출 파라미터"
    )

    # 활성화된 기능
    features: List[str] = Field(
        default_factory=list,
        description="활성화된 기능 목록",
        example=["symbol_detection", "gt_comparison", "dimension_ocr"]
    )

    # 도면 타입
    drawing_type: str = Field(
        "auto",
        description="도면 타입",
        example="pid"
    )

    # 워크플로우 정의 (빌더에서 생성)
    nodes: List[TemplateNode] = Field(default_factory=list)
    edges: List[TemplateEdge] = Field(default_factory=list)


class TemplateUpdate(BaseModel):
    """템플릿 수정 요청"""
    name: Optional[str] = None
    description: Optional[str] = None
    model_type: Optional[str] = None
    detection_params: Optional[Dict[str, Any]] = None
    features: Optional[List[str]] = None
    drawing_type: Optional[str] = None
    nodes: Optional[List[TemplateNode]] = None
    edges: Optional[List[TemplateEdge]] = None


class TemplateResponse(BaseModel):
    """템플릿 응답"""
    model_config = ConfigDict(from_attributes=True)

    template_id: str
    name: str
    description: Optional[str] = None

    # 검출 설정
    model_type: str
    detection_params: Dict[str, Any] = Field(default_factory=dict)
    features: List[str] = Field(default_factory=list)
    drawing_type: str = "auto"

    # 워크플로우 요약
    node_count: int = 0
    edge_count: int = 0
    node_types: List[str] = Field(default_factory=list)  # 사용된 노드 타입들

    # 사용 통계
    usage_count: int = 0  # 이 템플릿으로 생성된 세션 수

    # 메타
    created_at: datetime
    updated_at: datetime


class TemplateDetail(TemplateResponse):
    """템플릿 상세 (워크플로우 포함)"""
    nodes: List[TemplateNode] = Field(default_factory=list)
    edges: List[TemplateEdge] = Field(default_factory=list)


class TemplateListResponse(BaseModel):
    """템플릿 목록 응답"""
    templates: List[TemplateResponse]
    total: int


# ============ 버전 관리 스키마 ============

class TemplateVersion(BaseModel):
    """템플릿 버전 정보"""
    version: int = Field(..., description="버전 번호")
    template_id: str = Field(..., description="템플릿 ID")
    name: str = Field(..., description="템플릿명")
    description: Optional[str] = None
    model_type: str
    detection_params: Dict[str, Any] = Field(default_factory=dict)
    features: List[str] = Field(default_factory=list)
    drawing_type: str = "auto"
    nodes: List[TemplateNode] = Field(default_factory=list)
    edges: List[TemplateEdge] = Field(default_factory=list)
    node_count: int = 0
    edge_count: int = 0
    change_summary: str = Field(
        default="",
        description="변경 요약",
        example="YOLO confidence 0.3→0.4, 노드 2개 추가"
    )
    created_at: datetime
    created_by: Optional[str] = Field(None, description="변경자")


class TemplateVersionResponse(BaseModel):
    """버전 응답"""
    model_config = ConfigDict(from_attributes=True)

    version: int
    change_summary: str
    node_count: int
    edge_count: int
    created_at: datetime
    created_by: Optional[str] = None


class TemplateVersionListResponse(BaseModel):
    """버전 목록 응답"""
    template_id: str
    template_name: str
    current_version: int
    versions: List[TemplateVersionResponse]
    total: int


class TemplateRollbackRequest(BaseModel):
    """롤백 요청"""
    target_version: int = Field(..., description="롤백할 버전 번호")
