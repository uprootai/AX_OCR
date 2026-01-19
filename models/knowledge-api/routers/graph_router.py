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
        # dimensions, tolerances, processes를 dict 리스트로 변환
        dimensions = [d.model_dump() for d in request.dimensions] if request.dimensions else []
        tolerances = [t.model_dump() for t in request.tolerances] if request.tolerances else []
        processes = [p.model_dump() for p in request.processes] if request.processes else []

        component_id = await neo4j_service.create_component(
            name=request.name,
            part_id=request.part_id,
            part_number=request.part_number,
            category=request.category,
            material=request.material,
            manufacturer=request.manufacturer,
            unit_price=request.unit_price,
            specifications=request.specifications,
            dimensions=dimensions,
            tolerances=tolerances,
            processes=processes,
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
