"""
Search Router - VectorRAG, HybridRAG, Similar Parts Endpoints
"""
import logging
from typing import List, Dict

from fastapi import APIRouter, HTTPException

from models.schemas import (
    VectorSearchRequest, VectorSearchResponse,
    HybridSearchRequest, HybridSearchResponse,
    SimilarPartRequest, SimilarPartResponse
)
from services.state import get_graphrag_service, get_vectorrag_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["search"])


@router.post("/vector/search", response_model=VectorSearchResponse)
async def vector_search(request: VectorSearchRequest):
    """
    FAISS-based vector similarity search

    Search similar drawings/parts using text embeddings
    """
    vectorrag_service = get_vectorrag_service()
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


@router.post("/hybrid/search", response_model=HybridSearchResponse)
async def hybrid_search(request: HybridSearchRequest):
    """
    Hybrid RAG search (GraphRAG + VectorRAG)

    Combines graph traversal with vector similarity
    """
    graphrag_service = get_graphrag_service()
    vectorrag_service = get_vectorrag_service()
    results = []

    # GraphRAG search
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

    # VectorRAG search
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

    # Merge and deduplicate results
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


@router.post("/similar-parts", response_model=SimilarPartResponse)
async def find_similar_parts(request: SimilarPartRequest):
    """
    Find similar parts (Step 2 of PPT 6-step cost estimation)

    Use GraphRAG to search past projects with similar size, tolerance, and material
    """
    graphrag_service = get_graphrag_service()
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


def _merge_search_results(
    results: List[Dict],
    graph_weight: float = 0.6,
    vector_weight: float = 0.4
) -> List[Dict]:
    """Merge search results with weighted scoring"""
    merged = {}

    for r in results:
        key = r.get("part_id") or r.get("id") or str(r)
        if key not in merged:
            merged[key] = r.copy()
            merged[key]["combined_score"] = 0.0

        # Apply weight
        source = r.get("source", "unknown")
        score = r.get("similarity", r.get("score", 0.5))

        if source == "graphrag":
            merged[key]["combined_score"] += score * graph_weight
        elif source == "vectorrag":
            merged[key]["combined_score"] += score * vector_weight
        else:
            merged[key]["combined_score"] += score * 0.5

    # Sort by score
    sorted_results = sorted(
        merged.values(),
        key=lambda x: x.get("combined_score", 0),
        reverse=True
    )

    return sorted_results
