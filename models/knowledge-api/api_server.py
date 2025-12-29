"""
Knowledge API Server
GraphRAG + VectorRAG based domain knowledge engine

Port: 5007
Features:
- Neo4j graph DB integration
- GraphRAG (similar parts/projects search)
- VectorRAG (FAISS-based similarity search)
- ISO/ASME standard validation
- Hybrid RAG
"""

import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from models.schemas import (
    HealthResponse,
    APIInfoResponse, ParameterSchema, IOSchema, BlueprintFlowMetadata
)
from services import (
    Neo4jService,
    GraphRAGService,
    VectorRAGService,
    StandardValidator,
    set_services,
    get_neo4j_service
)
from routers import graph_router, search_router, validation_router

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


# =====================
# Lifespan
# =====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup, cleanup on shutdown"""
    # Startup
    logger.info("=" * 70)
    logger.info("🚀 Knowledge API Server Starting...")
    logger.info("=" * 70)

    neo4j_service = None
    graphrag_service = None
    vectorrag_service = None
    standard_validator = None

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

    # Set global state
    set_services(neo4j_service, graphrag_service, vectorrag_service, standard_validator)

    logger.info("=" * 70)
    logger.info(f"✅ Knowledge API ready on port {KNOWLEDGE_API_PORT}")
    logger.info("=" * 70)

    yield

    # Shutdown
    logger.info("👋 Shutting down Knowledge API...")
    if neo4j_service:
        await neo4j_service.close()


# =====================
# FastAPI App
# =====================

app = FastAPI(
    title="Knowledge API",
    description="GraphRAG + VectorRAG based domain knowledge engine",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(graph_router)
app.include_router(search_router)
app.include_router(validation_router)


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
    neo4j_service = get_neo4j_service()
    neo4j_status = neo4j_service is not None and await neo4j_service.is_connected()

    from services.state import get_graphrag_service, get_vectorrag_service, get_standard_validator
    graphrag_status = get_graphrag_service() is not None
    vectorrag_status = get_vectorrag_service() is not None
    validator_status = get_standard_validator() is not None

    return {
        "status": "healthy" if neo4j_status else "degraded",
        "service": "knowledge-api",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "neo4j": "connected" if neo4j_status else "disconnected",
            "graphrag": "ready" if graphrag_status else "unavailable",
            "vectorrag": "ready" if vectorrag_status else "unavailable",
            "standard_validator": "ready" if validator_status else "unavailable"
        }
    }


@app.get("/api/v1/info", response_model=APIInfoResponse)
async def get_api_info():
    """BlueprintFlow API info"""
    return APIInfoResponse(
        name="Knowledge API",
        version="1.0.0",
        description="GraphRAG + VectorRAG based domain knowledge engine",
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
                description="Search type selection",
                required=False
            ),
            ParameterSchema(
                name="top_k",
                type="number",
                default=5,
                min=1,
                max=20,
                step=1,
                description="Number of results",
                required=False
            ),
            ParameterSchema(
                name="similarity_threshold",
                type="number",
                default=0.7,
                min=0.0,
                max=1.0,
                step=0.1,
                description="Similarity threshold",
                required=False
            )
        ],
        input_schema=IOSchema(
            type="object",
            format="json",
            description="Search query or part info",
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
            description="Search results and similar parts",
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
# Main
# =====================

if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=KNOWLEDGE_API_PORT,
        reload=True
    )
