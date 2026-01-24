"""Workflow Session Schemas - BlueprintFlow에서 잠긴 세션 생성"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class LockLevel(str, Enum):
    """워크플로우 잠금 수준"""
    FULL = "full"  # 완전 잠금 - 이미지 업로드만 가능
    PARAMETERS = "parameters"  # 파라미터 수정 허용
    NONE = "none"  # 잠금 없음


class WorkflowNodeSchema(BaseModel):
    """워크플로우 노드 정의"""
    id: str
    type: str
    label: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    position: Optional[Dict[str, float]] = None


class WorkflowEdgeSchema(BaseModel):
    """워크플로우 엣지 정의"""
    id: str
    source: str
    target: str
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None
    condition: Optional[Dict[str, Any]] = None


class WorkflowDefinitionSchema(BaseModel):
    """워크플로우 정의"""
    name: str
    description: Optional[str] = None
    nodes: List[WorkflowNodeSchema]
    edges: List[WorkflowEdgeSchema]


class WorkflowSessionCreate(BaseModel):
    """BlueprintFlow 워크플로우로부터 세션 생성 요청"""
    name: str = Field(..., description="워크플로우 이름")
    description: Optional[str] = Field(None, description="워크플로우 설명")
    nodes: List[Dict[str, Any]] = Field(..., description="워크플로우 노드 정의")
    edges: List[Dict[str, Any]] = Field(..., description="워크플로우 엣지 정의")
    lock_level: LockLevel = Field(
        default=LockLevel.FULL,
        description="잠금 수준 (full: 완전 잠금, parameters: 파라미터 수정 허용)"
    )
    allowed_parameters: List[str] = Field(
        default_factory=list,
        description="수정 가능한 파라미터 목록 (lock_level이 parameters일 때)"
    )
    customer_name: Optional[str] = Field(None, description="고객명")
    expires_in_days: int = Field(default=30, description="만료 기간 (일)")


class WorkflowSessionResponse(BaseModel):
    """워크플로우 세션 생성 응답"""
    session_id: str = Field(..., description="세션 ID")
    share_url: str = Field(..., description="고객용 공유 URL")
    access_token: str = Field(..., description="접근 토큰")
    expires_at: datetime = Field(..., description="만료 시간")
    workflow_name: str = Field(..., description="워크플로우 이름")


class WorkflowSessionDetail(BaseModel):
    """워크플로우 세션 상세 정보"""
    session_id: str
    workflow_definition: Optional[Dict[str, Any]] = Field(
        None, description="워크플로우 정의 (nodes, edges)"
    )
    workflow_locked: bool = Field(default=False, description="워크플로우 잠금 여부")
    lock_level: LockLevel = Field(default=LockLevel.NONE, description="잠금 수준")
    allowed_parameters: List[str] = Field(
        default_factory=list,
        description="수정 가능한 파라미터 목록"
    )
    customer_name: Optional[str] = None
    access_token: Optional[str] = None
    expires_at: Optional[datetime] = None


class WorkflowExecuteRequest(BaseModel):
    """워크플로우 실행 요청"""
    image_ids: List[str] = Field(..., description="실행할 이미지 ID 목록")
    parameters: Optional[Dict[str, Any]] = Field(
        None, description="오버라이드할 파라미터 (lock_level이 parameters일 때만)"
    )


class WorkflowExecuteResponse(BaseModel):
    """워크플로우 실행 응답"""
    execution_id: str = Field(..., description="실행 ID")
    session_id: str = Field(..., description="세션 ID")
    status: str = Field(..., description="실행 상태")
    image_count: int = Field(..., description="처리된 이미지 수")
    message: str = Field(default="워크플로우 실행이 시작되었습니다")
