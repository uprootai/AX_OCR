"""Line Router - 선 검출 및 연결성 분석 API

선 검출 및 연결성 분석 기능:
- 선 검출 실행/조회
- 치수-심볼 연결
- 치수선 관계 분석
- 연결성 그래프 분석
"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
import logging

from schemas.analysis_options import AnalysisOptions

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["Lines & Connectivity"])

# 서비스 전역 변수
_line_detector_service = None
_connectivity_analyzer = None


def set_line_services(line_detector_service, connectivity_analyzer=None):
    """선 검출 및 연결성 서비스 설정"""
    global _line_detector_service, _connectivity_analyzer
    _line_detector_service = line_detector_service
    _connectivity_analyzer = connectivity_analyzer


def get_line_detector_service():
    if _line_detector_service is None:
        raise HTTPException(status_code=500, detail="Line detector service not initialized")
    return _line_detector_service


def get_connectivity_analyzer():
    if _connectivity_analyzer is None:
        raise HTTPException(status_code=500, detail="Connectivity analyzer not initialized")
    return _connectivity_analyzer


def get_session_service():
    """core_router에서 세션 서비스 가져오기"""
    from .core_router import get_session_service as _get_session_service
    return _get_session_service()


def get_session_options():
    """core_router에서 세션 옵션 가져오기"""
    from .core_router import get_session_options as _get_session_options
    return _get_session_options()


# ==================== 선 검출 API ====================

@router.post("/lines/{session_id}")
async def detect_lines(session_id: str) -> Dict[str, Any]:
    """선 검출 실행"""
    session_service = get_session_service()
    line_service = get_line_detector_service()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    image_path = session.get("file_path")
    if not image_path:
        raise HTTPException(status_code=400, detail="이미지 파일이 없습니다")

    _session_options = get_session_options()
    options = _session_options.get(session_id, AnalysisOptions())

    try:
        from schemas.line import LineDetectionConfig
        config = LineDetectionConfig(
            method="lsd",
            classify_types=True,
            classify_colors=True,
            find_intersections=True,
            visualize=True,
        )

        result = line_service.detect_lines(image_path, config)

        session_service.update_session(session_id, {
            "lines": result.get("lines", []),
            "intersections": result.get("intersections", []),
            "line_statistics": result.get("statistics", {}),
            "line_count": len(result.get("lines", [])),
        })

        logger.info(f"선 검출 완료: {len(result.get('lines', []))}개 선, {len(result.get('intersections', []))}개 교차점")

        return {
            "session_id": session_id,
            "lines": result.get("lines", []),
            "intersections": result.get("intersections", []),
            "statistics": result.get("statistics", {}),
            "processing_time_ms": result.get("processing_time_ms", 0),
            "visualization_base64": result.get("visualization_base64"),
        }

    except Exception as e:
        logger.error(f"선 검출 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"선 검출 실패: {str(e)}")


@router.get("/lines/{session_id}")
async def get_lines(session_id: str) -> Dict[str, Any]:
    """세션의 선 검출 결과 조회"""
    session_service = get_session_service()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    return {
        "session_id": session_id,
        "lines": session.get("lines", []),
        "intersections": session.get("intersections", []),
        "statistics": session.get("line_statistics", {}),
        "total": session.get("line_count", 0),
    }


@router.post("/lines/{session_id}/link-dimensions")
async def link_dimensions_to_symbols(session_id: str) -> Dict[str, Any]:
    """치수를 심볼에 연결"""
    session_service = get_session_service()
    line_service = get_line_detector_service()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    dimensions = session.get("dimensions", [])
    detections = session.get("detections", [])
    lines = session.get("lines", [])

    if not dimensions:
        return {
            "session_id": session_id,
            "links": [],
            "message": "치수가 없습니다"
        }

    if not detections:
        return {
            "session_id": session_id,
            "links": [],
            "message": "심볼이 없습니다"
        }

    from schemas.line import Line
    parsed_lines = [Line(**l) if isinstance(l, dict) else l for l in lines]
    links = line_service.link_dimensions_to_symbols(dimensions, detections, parsed_lines)

    link_data = [link.model_dump() for link in links]
    session_service.update_session(session_id, {
        "dimension_symbol_links": link_data,
    })

    link_map = {link.dimension_id: link.symbol_id for link in links if link.symbol_id}
    updated_dimensions = []
    for dim in dimensions:
        dim_copy = dict(dim)
        if dim.get("id") in link_map:
            dim_copy["linked_to"] = link_map[dim.get("id")]
        updated_dimensions.append(dim_copy)

    session_service.update_session(session_id, {"dimensions": updated_dimensions})

    return {
        "session_id": session_id,
        "links": link_data,
        "linked_count": sum(1 for link in links if link.symbol_id),
        "total_dimensions": len(dimensions),
    }


@router.post("/lines/{session_id}/find-dimension-relations")
async def find_dimension_relations(session_id: str) -> Dict[str, Any]:
    """치수선과 치수 간의 관계 분석"""
    session_service = get_session_service()
    line_service = get_line_detector_service()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    lines = session.get("lines", [])
    dimensions = session.get("dimensions", [])

    if not lines:
        return {
            "session_id": session_id,
            "relations": [],
            "message": "선 검출 결과가 없습니다. 먼저 선 검출을 실행하세요."
        }

    if not dimensions:
        return {
            "session_id": session_id,
            "relations": [],
            "message": "치수가 없습니다"
        }

    from schemas.line import Line
    parsed_lines = [Line(**l) if isinstance(l, dict) else l for l in lines]

    relations = line_service.find_dimension_lines(parsed_lines, dimensions)

    relation_data = [rel.model_dump() for rel in relations]
    session_service.update_session(session_id, {
        "dimension_line_relations": relation_data,
    })

    return {
        "session_id": session_id,
        "relations": relation_data,
        "total": len(relations),
    }


@router.get("/lines/health")
async def check_line_detector_health() -> Dict[str, Any]:
    """Line Detector API 상태 확인"""
    try:
        line_service = get_line_detector_service()
        is_healthy = line_service.health_check()
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "service": "line-detector",
        }
    except Exception as e:
        return {
            "status": "error",
            "service": "line-detector",
            "error": str(e),
        }


# ==================== 연결성 분석 API ====================

@router.post("/connectivity/{session_id}")
async def analyze_connectivity(session_id: str) -> Dict[str, Any]:
    """심볼 연결성 분석"""
    session_service = get_session_service()
    analyzer = get_connectivity_analyzer()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    detections = session.get("detections", [])
    if not detections:
        return {
            "session_id": session_id,
            "nodes": {},
            "connections": [],
            "statistics": {"total_symbols": 0},
            "message": "심볼이 없습니다. 먼저 심볼 검출을 실행하세요."
        }

    lines = session.get("lines", [])
    intersections = session.get("intersections", [])

    result = analyzer.analyze(
        symbols=detections,
        lines=lines if lines else None,
        intersections=intersections if intersections else None,
    )

    session_service.update_session(session_id, {
        "connectivity_graph": result,
        "connectivity_analyzed": True,
    })

    logger.info(
        f"연결성 분석 완료: {result['statistics']['total_symbols']}개 심볼, "
        f"{result['statistics']['total_connections']}개 연결"
    )

    return {
        "session_id": session_id,
        **result,
    }


@router.get("/connectivity/{session_id}")
async def get_connectivity(session_id: str) -> Dict[str, Any]:
    """세션의 연결성 분석 결과 조회"""
    session_service = get_session_service()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    graph = session.get("connectivity_graph", {})
    if not graph:
        return {
            "session_id": session_id,
            "analyzed": False,
            "message": "연결성 분석이 수행되지 않았습니다. POST /analysis/connectivity/{session_id}를 호출하세요."
        }

    return {
        "session_id": session_id,
        "analyzed": True,
        **graph,
    }


@router.get("/connectivity/{session_id}/path")
async def find_connection_path(
    session_id: str,
    source_id: str,
    target_id: str,
) -> Dict[str, Any]:
    """두 심볼 사이의 연결 경로 찾기"""
    session_service = get_session_service()
    analyzer = get_connectivity_analyzer()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    graph = session.get("connectivity_graph", {})
    if not graph:
        raise HTTPException(
            status_code=400,
            detail="연결성 분석이 수행되지 않았습니다"
        )

    path = analyzer.find_path(graph, source_id, target_id)

    if path is None:
        return {
            "session_id": session_id,
            "source_id": source_id,
            "target_id": target_id,
            "path": None,
            "connected": False,
            "message": "연결 경로를 찾을 수 없습니다"
        }

    return {
        "session_id": session_id,
        "source_id": source_id,
        "target_id": target_id,
        "path": path,
        "path_length": len(path),
        "connected": True,
    }


@router.get("/connectivity/{session_id}/component/{symbol_id}")
async def get_connected_component(
    session_id: str,
    symbol_id: str,
) -> Dict[str, Any]:
    """심볼이 속한 연결 컴포넌트 조회"""
    session_service = get_session_service()
    analyzer = get_connectivity_analyzer()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    graph = session.get("connectivity_graph", {})
    if not graph:
        raise HTTPException(
            status_code=400,
            detail="연결성 분석이 수행되지 않았습니다"
        )

    component = analyzer.get_connected_component(graph, symbol_id)

    return {
        "session_id": session_id,
        "symbol_id": symbol_id,
        "component": component,
        "size": len(component),
    }
