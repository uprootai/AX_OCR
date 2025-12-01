"""
Knowledge API Server
GraphRAG + VectorRAG 기반 도메인 지식 엔진

포트: 5007
기능:
- Neo4j 그래프 DB 연동
- GraphRAG (유사 부품/프로젝트 검색)
- VectorRAG (FAISS 기반 유사도 검색)
- ISO/ASME 규격 검증
- 하이브리드 RAG
"""

import os
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from models.schemas import (
    HealthResponse,
    GraphQueryRequest, GraphQueryResponse,
    VectorSearchRequest, VectorSearchResponse,
    HybridSearchRequest, HybridSearchResponse,
    ComponentCreateRequest, ComponentResponse,
    SimilarPartRequest, SimilarPartResponse,
    StandardValidationRequest, StandardValidationResponse,
    APIInfoResponse, ParameterSchema, IOSchema, BlueprintFlowMetadata
)
from services.neo4j_service import Neo4jService
from services.graphrag_service import GraphRAGService
from services.vectorrag_service import VectorRAGService
from services.standard_validator import StandardValidator

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
KNOWLEDGE_API_PORT = int(os.getenv("KNOWLEDGE_API_PORT", "5007"))
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "ax_poc_2024")

# Initialize FastAPI
app = FastAPI(
    title="Knowledge API",
    description="GraphRAG + VectorRAG 기반 도메인 지식 엔진",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global services
neo4j_service: Optional[Neo4jService] = None
graphrag_service: Optional[GraphRAGService] = None
vectorrag_service: Optional[VectorRAGService] = None
standard_validator: Optional[StandardValidator] = None


# =====================
# Startup/Shutdown Events
# =====================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global neo4j_service, graphrag_service, vectorrag_service, standard_validator

    logger.info("=" * 70)
    logger.info("🚀 Knowledge API Server Starting...")
    logger.info("=" * 70)

    # Initialize Neo4j
    try:
        neo4j_service = Neo4jService(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        await neo4j_service.connect()
        await neo4j_service.init_schema()
        logger.info("✅ Neo4j connected")
    except Exception as e:
        logger.warning(f"⚠️ Neo4j connection failed: {e}")
        neo4j_service = None

    # Initialize GraphRAG
    try:
        graphrag_service = GraphRAGService(neo4j_service)
        logger.info("✅ GraphRAG initialized")
    except Exception as e:
        logger.warning(f"⚠️ GraphRAG initialization failed: {e}")
        graphrag_service = None

    # Initialize VectorRAG
    try:
        vectorrag_service = VectorRAGService()
        await vectorrag_service.load_index()
        logger.info("✅ VectorRAG initialized")
    except Exception as e:
        logger.warning(f"⚠️ VectorRAG initialization failed: {e}")
        vectorrag_service = None

    # Initialize Standard Validator
    try:
        standard_validator = StandardValidator()
        logger.info("✅ Standard Validator initialized")
    except Exception as e:
        logger.warning(f"⚠️ Standard Validator initialization failed: {e}")
        standard_validator = None

    logger.info("=" * 70)
    logger.info(f"✅ Knowledge API ready on port {KNOWLEDGE_API_PORT}")
    logger.info("=" * 70)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global neo4j_service

    logger.info("👋 Shutting down Knowledge API...")

    if neo4j_service:
        await neo4j_service.close()


# =====================
# Health & Info Endpoints
# =====================

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint"""
    return {
        "status": "online",
        "service": "Knowledge API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health", response_model=HealthResponse)
@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    neo4j_status = neo4j_service is not None and await neo4j_service.is_connected()
    graphrag_status = graphrag_service is not None
    vectorrag_status = vectorrag_service is not None

    return {
        "status": "healthy" if neo4j_status else "degraded",
        "service": "knowledge-api",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "neo4j": "connected" if neo4j_status else "disconnected",
            "graphrag": "ready" if graphrag_status else "unavailable",
            "vectorrag": "ready" if vectorrag_status else "unavailable",
            "standard_validator": "ready" if standard_validator else "unavailable"
        }
    }


@app.get("/api/v1/info", response_model=APIInfoResponse)
async def get_api_info():
    """BlueprintFlow용 API 정보"""
    return APIInfoResponse(
        name="Knowledge API",
        version="1.0.0",
        description="GraphRAG + VectorRAG 기반 도메인 지식 엔진",
        endpoints=[
            "/api/v1/graph/query",
            "/api/v1/graph/component",
            "/api/v1/vector/search",
            "/api/v1/hybrid/search",
            "/api/v1/similar-parts",
            "/api/v1/validate/standard"
        ],
        parameters=[
            ParameterSchema(
                name="search_type",
                type="select",
                options=["graphrag", "vectorrag", "hybrid"],
                default="hybrid",
                description="검색 유형 선택",
                required=False
            ),
            ParameterSchema(
                name="top_k",
                type="number",
                default=5,
                min=1,
                max=20,
                step=1,
                description="검색 결과 개수",
                required=False
            ),
            ParameterSchema(
                name="similarity_threshold",
                type="number",
                default=0.7,
                min=0.0,
                max=1.0,
                step=0.1,
                description="유사도 임계값",
                required=False
            )
        ],
        input_schema=IOSchema(
            type="object",
            format="json",
            description="검색 쿼리 또는 부품 정보",
            example={
                "query": "SUS304 Ø50 H7",
                "dimensions": ["50", "30", "10"],
                "tolerance": "H7",
                "material": "SUS304"
            }
        ),
        output_schema=IOSchema(
            type="object",
            format="json",
            description="검색 결과 및 유사 부품 정보",
            example={
                "results": [
                    {
                        "part_id": "PART-001",
                        "similarity": 0.95,
                        "dimensions": ["50", "30", "10"],
                        "past_cost": 84205
                    }
                ]
            }
        ),
        blueprintflow=BlueprintFlowMetadata(
            node_type="knowledge",
            category="KNOWLEDGE",
            color="#9333ea",
            icon="database",
            inputs=["query", "component_data"],
            outputs=["search_results", "similar_parts", "validation_result"]
        )
    )


# =====================
# GraphRAG Endpoints
# =====================

@app.post("/api/v1/graph/query", response_model=GraphQueryResponse)
async def graph_query(request: GraphQueryRequest):
    """
    Neo4j 그래프 쿼리 실행

    Cypher 쿼리를 실행하거나 사전 정의된 쿼리 템플릿 사용
    """
    if not neo4j_service:
        raise HTTPException(status_code=503, detail="Neo4j service unavailable")

    try:
        result = await neo4j_service.execute_query(
            request.query,
            request.parameters
        )
        return GraphQueryResponse(
            status="success",
            data=result,
            query=request.query,
            execution_time=0.0  # TODO: measure actual time
        )
    except Exception as e:
        logger.error(f"Graph query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/graph/component", response_model=ComponentResponse)
async def create_component(request: ComponentCreateRequest):
    """
    도면 컴포넌트를 그래프 DB에 저장

    Component → Dimension → Tolerance → Process 관계 생성
    """
    if not neo4j_service:
        raise HTTPException(status_code=503, detail="Neo4j service unavailable")

    try:
        component_id = await neo4j_service.create_component(
            name=request.name,
            part_number=request.part_number,
            material=request.material,
            dimensions=request.dimensions,
            tolerances=request.tolerances,
            processes=request.processes,
            metadata=request.metadata
        )
        return ComponentResponse(
            status="success",
            component_id=component_id,
            message=f"Component {request.name} created successfully"
        )
    except Exception as e:
        logger.error(f"Component creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================
# VectorRAG Endpoints
# =====================

@app.post("/api/v1/vector/search", response_model=VectorSearchResponse)
async def vector_search(request: VectorSearchRequest):
    """
    FAISS 기반 벡터 유사도 검색

    텍스트 임베딩으로 유사한 도면/부품 검색
    """
    if not vectorrag_service:
        raise HTTPException(status_code=503, detail="VectorRAG service unavailable")

    try:
        results = await vectorrag_service.search(
            query=request.query,
            top_k=request.top_k,
            threshold=request.similarity_threshold
        )
        return VectorSearchResponse(
            status="success",
            results=results,
            query=request.query,
            total_found=len(results)
        )
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================
# Hybrid RAG Endpoints
# =====================

@app.post("/api/v1/hybrid/search", response_model=HybridSearchResponse)
async def hybrid_search(request: HybridSearchRequest):
    """
    하이브리드 RAG 검색 (GraphRAG + VectorRAG)

    그래프 탐색과 벡터 유사도를 결합한 검색
    """
    results = []

    # GraphRAG 검색
    if graphrag_service and request.use_graphrag:
        try:
            graph_results = await graphrag_service.search(
                query=request.query,
                dimensions=request.dimensions,
                tolerance=request.tolerance,
                material=request.material,
                top_k=request.top_k
            )
            results.extend([{**r, "source": "graphrag"} for r in graph_results])
        except Exception as e:
            logger.warning(f"GraphRAG search failed: {e}")

    # VectorRAG 검색
    if vectorrag_service and request.use_vectorrag:
        try:
            vector_results = await vectorrag_service.search(
                query=request.query,
                top_k=request.top_k,
                threshold=request.similarity_threshold
            )
            results.extend([{**r, "source": "vectorrag"} for r in vector_results])
        except Exception as e:
            logger.warning(f"VectorRAG search failed: {e}")

    # 결과 병합 및 중복 제거
    merged_results = _merge_search_results(
        results,
        graph_weight=request.graph_weight,
        vector_weight=request.vector_weight
    )

    return HybridSearchResponse(
        status="success",
        results=merged_results[:request.top_k],
        query=request.query,
        total_found=len(merged_results),
        sources_used={
            "graphrag": request.use_graphrag,
            "vectorrag": request.use_vectorrag
        }
    )


# =====================
# Similar Parts Endpoint
# =====================

@app.post("/api/v1/similar-parts", response_model=SimilarPartResponse)
async def find_similar_parts(request: SimilarPartRequest):
    """
    유사 부품 검색 (PPT 6단계 비용 산정의 2단계)

    GraphRAG로 비슷한 크기, 공차, 재질의 과거 프로젝트 검색
    """
    if not graphrag_service:
        raise HTTPException(status_code=503, detail="GraphRAG service unavailable")

    try:
        similar_parts = await graphrag_service.find_similar_parts(
            dimensions=request.dimensions,
            tolerance=request.tolerance,
            material=request.material,
            top_k=request.top_k
        )

        return SimilarPartResponse(
            status="success",
            similar_parts=similar_parts,
            query_info={
                "dimensions": request.dimensions,
                "tolerance": request.tolerance,
                "material": request.material
            },
            total_found=len(similar_parts)
        )
    except Exception as e:
        logger.error(f"Similar parts search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================
# Standard Validation Endpoint
# =====================

@app.post("/api/v1/validate/standard", response_model=StandardValidationResponse)
async def validate_standard(request: StandardValidationRequest):
    """
    ISO/ASME 규격 검증

    - ISO 1101 GD&T 규격 검증
    - ASME Y14.5 규격 검증
    - 나사 규격 검증
    - 표면조도 규격 검증
    """
    if not standard_validator:
        raise HTTPException(status_code=503, detail="Standard validator unavailable")

    try:
        validation_result = await standard_validator.validate(
            dimension=request.dimension,
            tolerance=request.tolerance,
            gdt_symbol=request.gdt_symbol,
            surface_finish=request.surface_finish,
            thread_spec=request.thread_spec
        )

        return StandardValidationResponse(
            status="success",
            is_valid=validation_result["is_valid"],
            errors=validation_result.get("errors", []),
            warnings=validation_result.get("warnings", []),
            suggestions=validation_result.get("suggestions", []),
            matched_standards=validation_result.get("matched_standards", [])
        )
    except Exception as e:
        logger.error(f"Standard validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================
# Helper Functions
# =====================

def _merge_search_results(
    results: List[Dict],
    graph_weight: float = 0.6,
    vector_weight: float = 0.4
) -> List[Dict]:
    """검색 결과 병합 및 가중치 적용"""
    merged = {}

    for r in results:
        key = r.get("part_id") or r.get("id") or str(r)
        if key not in merged:
            merged[key] = r.copy()
            merged[key]["combined_score"] = 0.0

        # 가중치 적용
        source = r.get("source", "unknown")
        score = r.get("similarity", r.get("score", 0.5))

        if source == "graphrag":
            merged[key]["combined_score"] += score * graph_weight
        elif source == "vectorrag":
            merged[key]["combined_score"] += score * vector_weight
        else:
            merged[key]["combined_score"] += score * 0.5

    # 점수 기준 정렬
    sorted_results = sorted(
        merged.values(),
        key=lambda x: x.get("combined_score", 0),
        reverse=True
    )

    return sorted_results


# =====================
# Main
# =====================

if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=KNOWLEDGE_API_PORT,
        reload=True
    )
