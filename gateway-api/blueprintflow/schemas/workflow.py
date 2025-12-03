"""
BlueprintFlow Workflow Schema Definitions
워크플로우 정의를 위한 Pydantic 모델
"""
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field, field_validator


class NodeParameter(BaseModel):
    """노드 파라미터 정의"""
    name: str
    value: Any
    type: Literal["string", "number", "boolean", "object", "array"]


class WorkflowNode(BaseModel):
    """워크플로우 노드 정의"""
    id: str = Field(..., description="노드 고유 ID")
    type: str = Field(..., description="노드 타입 (yolo, edocr2, if, merge, loop 등)")
    label: Optional[str] = Field(None, description="노드 표시 이름")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="노드 파라미터")
    position: Optional[Dict[str, float]] = Field(None, description="캔버스 상의 위치 (x, y)")


class WorkflowEdge(BaseModel):
    """워크플로우 엣지 (연결) 정의"""
    id: str = Field(..., description="엣지 고유 ID")
    source: str = Field(..., description="시작 노드 ID")
    target: str = Field(..., description="종료 노드 ID")
    sourceHandle: Optional[str] = Field(None, description="시작 핸들 ID")
    targetHandle: Optional[str] = Field(None, description="종료 핸들 ID")
    condition: Optional[Dict[str, Any]] = Field(None, description="조건부 실행 조건")


class WorkflowDefinition(BaseModel):
    """전체 워크플로우 정의"""
    name: str = Field(..., description="워크플로우 이름")
    description: Optional[str] = Field(None, description="워크플로우 설명")
    version: str = Field(default="1.0.0", description="워크플로우 버전")
    nodes: List[WorkflowNode] = Field(..., description="노드 목록")
    edges: List[WorkflowEdge] = Field(..., description="엣지 목록")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="추가 메타데이터")

    @field_validator('nodes')
    @classmethod
    def validate_nodes_not_empty(cls, v: List[WorkflowNode]) -> List[WorkflowNode]:
        if not v:
            raise ValueError("워크플로우는 최소 1개 이상의 노드가 필요합니다")
        return v

    @field_validator('nodes')
    @classmethod
    def validate_unique_node_ids(cls, v: List[WorkflowNode]) -> List[WorkflowNode]:
        ids = [node.id for node in v]
        if len(ids) != len(set(ids)):
            raise ValueError("노드 ID는 중복될 수 없습니다")
        return v


class WorkflowExecutionRequest(BaseModel):
    """워크플로우 실행 요청"""
    workflow: WorkflowDefinition
    inputs: Dict[str, Any] = Field(default_factory=dict, description="초기 입력 데이터")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="실행 설정")


class NodeExecutionStatus(BaseModel):
    """노드 실행 상태"""
    node_id: str
    status: Literal["pending", "running", "completed", "failed", "skipped"]
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    error: Optional[str] = None
    output: Optional[Dict[str, Any]] = None


class WorkflowExecutionResponse(BaseModel):
    """워크플로우 실행 응답"""
    execution_id: str
    status: Literal["running", "completed", "failed"]
    workflow_name: str
    node_statuses: List[NodeExecutionStatus]
    final_output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None
