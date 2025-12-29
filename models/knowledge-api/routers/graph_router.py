"""
Graph Router - Neo4j GraphRAG Endpoints
"""
import logging

from fastapi import APIRouter, HTTPException

from models.schemas import (
    GraphQueryRequest, GraphQueryResponse,
    ComponentCreateRequest, ComponentResponse
)
from services.state import get_neo4j_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/graph", tags=["graph"])


@router.post("/query", response_model=GraphQueryResponse)
async def graph_query(request: GraphQueryRequest):
    """
    Execute Neo4j graph query

    Execute Cypher query or use predefined query templates
    """
    neo4j_service = get_neo4j_service()
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
            execution_time=0.0
        )
    except Exception as e:
        logger.error(f"Graph query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/component", response_model=ComponentResponse)
async def create_component(request: ComponentCreateRequest):
    """
    Save drawing component to graph DB

    Creates Component → Dimension → Tolerance → Process relationships
    """
    neo4j_service = get_neo4j_service()
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
