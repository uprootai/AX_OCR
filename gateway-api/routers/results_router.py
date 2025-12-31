"""
Results Router - 파이프라인 결과 관리
- 결과 저장소 통계
- 최근 실행 결과 조회
- 오래된 결과 정리
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

results_router = APIRouter(prefix="/admin", tags=["Results"])


# =============================================================================
# API Endpoints
# =============================================================================

@results_router.get("/results/stats")
async def get_result_statistics() -> Dict[str, Any]:
    """
    파이프라인 결과 저장소 통계
    - 총 용량, 파일 수, 날짜별 통계
    """
    try:
        from utils.result_manager import get_result_manager
        manager = get_result_manager()
        stats = manager.get_statistics()
        return stats
    except ImportError:
        raise HTTPException(status_code=501, detail="Result manager not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@results_router.get("/results/recent")
async def get_recent_results(limit: int = 10) -> Dict[str, Any]:
    """
    최근 파이프라인 실행 결과 목록
    - limit: 조회할 개수 (기본 10)
    """
    try:
        from utils.result_manager import get_result_manager
        manager = get_result_manager()
        sessions = manager.list_recent_sessions(limit=limit)
        return {"sessions": sessions, "count": len(sessions)}
    except ImportError:
        raise HTTPException(status_code=501, detail="Result manager not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@results_router.post("/results/cleanup")
async def cleanup_old_results(
    max_age_days: int = 7,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    오래된 파이프라인 결과 정리
    - max_age_days: 보관 기간 (기본 7일)
    - dry_run: True면 실제 삭제 없이 목록만 반환
    """
    try:
        from utils.result_manager import get_result_manager
        manager = get_result_manager()
        result = manager.cleanup_old_results(max_age_days=max_age_days, dry_run=dry_run)
        return result
    except ImportError:
        raise HTTPException(status_code=501, detail="Result manager not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
