"""P&ID Features Routers Package

P&ID 분석 기능별 라우터 모듈

구성:
- valve_router: 밸브 검출
- equipment_router: 장비 검출
- checklist_router: 설계 체크리스트
- deviation_router: 편차 분석
- verification_router: 검증
- export_router: Excel 내보내기
"""

from fastapi import APIRouter

from .valve_router import router as valve_router, set_session_service as set_valve_service
from .equipment_router import router as equipment_router, set_session_service as set_equipment_service
from .checklist_router import router as checklist_router, set_session_service as set_checklist_service
from .deviation_router import router as deviation_router, set_session_service as set_deviation_service
from .verification_router import router as verification_router, set_session_service as set_verification_service
from .export_router import router as export_router, set_session_service as set_export_service


def create_pid_features_router() -> APIRouter:
    """통합 PID Features 라우터 생성"""
    router = APIRouter()

    # 서브 라우터 등록
    router.include_router(valve_router)
    router.include_router(equipment_router)
    router.include_router(checklist_router)
    router.include_router(deviation_router)
    router.include_router(verification_router)
    router.include_router(export_router)

    return router


def set_session_service(session_service):
    """모든 서브 라우터에 세션 서비스 주입"""
    set_valve_service(session_service)
    set_equipment_service(session_service)
    set_checklist_service(session_service)
    set_deviation_service(session_service)
    set_verification_service(session_service)
    set_export_service(session_service)


__all__ = [
    "valve_router",
    "equipment_router",
    "checklist_router",
    "deviation_router",
    "verification_router",
    "export_router",
    "create_pid_features_router",
    "set_session_service",
]
