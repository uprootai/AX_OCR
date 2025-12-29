"""
Knowledge API Global State Management

Manages global service instances for the Knowledge API.
"""
from typing import Optional

from services.neo4j_service import Neo4jService
from services.graphrag_service import GraphRAGService
from services.vectorrag_service import VectorRAGService
from services.standard_validator import StandardValidator

# Global service instances
_neo4j_service: Optional[Neo4jService] = None
_graphrag_service: Optional[GraphRAGService] = None
_vectorrag_service: Optional[VectorRAGService] = None
_standard_validator: Optional[StandardValidator] = None


def get_neo4j_service() -> Optional[Neo4jService]:
    """Get global Neo4j service instance"""
    return _neo4j_service


def get_graphrag_service() -> Optional[GraphRAGService]:
    """Get global GraphRAG service instance"""
    return _graphrag_service


def get_vectorrag_service() -> Optional[VectorRAGService]:
    """Get global VectorRAG service instance"""
    return _vectorrag_service


def get_standard_validator() -> Optional[StandardValidator]:
    """Get global Standard Validator instance"""
    return _standard_validator


def set_services(
    neo4j_service: Optional[Neo4jService],
    graphrag_service: Optional[GraphRAGService],
    vectorrag_service: Optional[VectorRAGService],
    standard_validator: Optional[StandardValidator]
):
    """Set global service instances (called from lifespan)"""
    global _neo4j_service, _graphrag_service, _vectorrag_service, _standard_validator
    _neo4j_service = neo4j_service
    _graphrag_service = graphrag_service
    _vectorrag_service = vectorrag_service
    _standard_validator = standard_validator
