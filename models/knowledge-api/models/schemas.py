"""
Knowledge API Pydantic Schemas
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# =====================
# Health & Info Schemas
# =====================

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str
    components: Optional[Dict[str, str]] = None


class ParameterSchema(BaseModel):
    name: str
    type: str
    options: Optional[List[str]] = None
    default: Any = None
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    description: str
    required: bool = False


class IOSchema(BaseModel):
    type: str
    format: str
    description: str
    example: Any = None


class BlueprintFlowMetadata(BaseModel):
    node_type: str
    category: str
    color: str
    icon: str
    inputs: List[str]
    outputs: List[str]


class APIInfoResponse(BaseModel):
    name: str
    version: str
    description: str
    endpoints: List[str]
    parameters: List[ParameterSchema]
    input_schema: IOSchema
    output_schema: IOSchema
    blueprintflow: BlueprintFlowMetadata


# =====================
# Graph Query Schemas
# =====================

class GraphQueryRequest(BaseModel):
    query: str = Field(..., description="Cypher 쿼리 또는 쿼리 템플릿 이름")
    parameters: Optional[Dict[str, Any]] = Field(default={}, description="쿼리 파라미터")


class GraphQueryResponse(BaseModel):
    status: str
    data: List[Dict[str, Any]]
    query: str
    execution_time: float


# =====================
# Component Schemas
# =====================

class DimensionInfo(BaseModel):
    value: str = Field(..., description="치수 값 (예: 50)")
    unit: str = Field(default="mm", description="단위")
    type: str = Field(default="linear", description="치수 유형 (linear, diameter, radius)")


class ToleranceInfo(BaseModel):
    type: str = Field(..., description="공차 유형 (예: H7, h6, ±0.1)")
    grade: Optional[str] = Field(None, description="ISO 공차 등급 (IT01-IT18)")
    upper: Optional[float] = Field(None, description="상한 공차")
    lower: Optional[float] = Field(None, description="하한 공차")


class ProcessInfo(BaseModel):
    name: str = Field(..., description="공정명 (예: MILLING, TURNING)")
    estimated_time: Optional[float] = Field(None, description="예상 가공 시간 (분)")
    estimated_cost: Optional[float] = Field(None, description="예상 비용")


class ComponentCreateRequest(BaseModel):
    name: str = Field(..., description="부품명")
    part_id: Optional[str] = Field(None, description="부품 ID (사용자 지정)")
    part_number: Optional[str] = Field(None, description="품번")
    category: Optional[str] = Field(None, description="카테고리 (예: transformer, circuit_breaker)")
    material: Optional[str] = Field(None, description="재질 (예: SUS304, AL6061)")
    manufacturer: Optional[str] = Field(None, description="제조사")
    unit_price: Optional[float] = Field(None, description="단가")
    specifications: Optional[Dict[str, Any]] = Field(default={}, description="사양 정보")
    dimensions: List[DimensionInfo] = Field(default=[], description="치수 정보")
    tolerances: List[ToleranceInfo] = Field(default=[], description="공차 정보")
    processes: List[ProcessInfo] = Field(default=[], description="필요 공정")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="추가 메타데이터")


class ComponentResponse(BaseModel):
    status: str
    component_id: str
    message: str


# =====================
# Vector Search Schemas
# =====================

class VectorSearchRequest(BaseModel):
    query: str = Field(..., description="검색 쿼리 텍스트")
    top_k: int = Field(default=5, ge=1, le=20, description="검색 결과 개수")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="유사도 임계값")


class VectorSearchResult(BaseModel):
    id: str
    text: str
    similarity: float
    metadata: Optional[Dict[str, Any]] = None


class VectorSearchResponse(BaseModel):
    status: str
    results: List[Dict[str, Any]]
    query: str
    total_found: int


# =====================
# Hybrid Search Schemas
# =====================

class HybridSearchRequest(BaseModel):
    query: str = Field(..., description="검색 쿼리")
    dimensions: Optional[List[str]] = Field(None, description="치수 정보")
    tolerance: Optional[str] = Field(None, description="공차 정보")
    material: Optional[str] = Field(None, description="재질")
    top_k: int = Field(default=5, ge=1, le=20, description="검색 결과 개수")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="유사도 임계값")
    use_graphrag: bool = Field(default=True, description="GraphRAG 사용 여부")
    use_vectorrag: bool = Field(default=True, description="VectorRAG 사용 여부")
    graph_weight: float = Field(default=0.6, ge=0.0, le=1.0, description="GraphRAG 가중치")
    vector_weight: float = Field(default=0.4, ge=0.0, le=1.0, description="VectorRAG 가중치")


class HybridSearchResponse(BaseModel):
    status: str
    results: List[Dict[str, Any]]
    query: str
    total_found: int
    sources_used: Dict[str, bool]


# =====================
# Similar Parts Schemas
# =====================

class SimilarPartRequest(BaseModel):
    dimensions: List[str] = Field(..., description="치수 값 리스트")
    tolerance: Optional[str] = Field(None, description="공차 (예: H7)")
    material: Optional[str] = Field(None, description="재질")
    top_k: int = Field(default=5, ge=1, le=20, description="검색 결과 개수")


class SimilarPart(BaseModel):
    part_id: str
    name: Optional[str] = None
    similarity: float
    dimensions: List[str]
    tolerance: Optional[str] = None
    material: Optional[str] = None
    past_cost: Optional[float] = None
    past_processes: Optional[List[str]] = None
    project_date: Optional[str] = None


class SimilarPartResponse(BaseModel):
    status: str
    similar_parts: List[Dict[str, Any]]
    query_info: Dict[str, Any]
    total_found: int


# =====================
# Standard Validation Schemas
# =====================

class StandardValidationRequest(BaseModel):
    dimension: Optional[str] = Field(None, description="치수 값")
    tolerance: Optional[str] = Field(None, description="공차 (예: H7, ±0.1)")
    gdt_symbol: Optional[str] = Field(None, description="GD&T 기호")
    surface_finish: Optional[str] = Field(None, description="표면조도 (예: Ra1.6)")
    thread_spec: Optional[str] = Field(None, description="나사 규격 (예: M10x1.5)")


class StandardValidationResponse(BaseModel):
    status: str
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    suggestions: List[str] = []
    matched_standards: List[str] = []
