"""Analysis Router Package

analysis_router.py를 5개 모듈로 분할:
- core_router.py: 프리셋, 옵션, 분석 실행
- dimension_router.py: 치수 관리
- line_router.py: 선 검출, 연결성 분석
- region_router.py: 영역 분할 (Phase 5)
- gdt_router.py: GD&T 파싱, 표제란 OCR
"""
from .core_router import router as core_router
from .dimension_router import router as dimension_router
from .line_router import router as line_router
from .region_router import router as region_router
from .gdt_router import router as gdt_router

# 서비스 주입 함수들
from .core_router import (
    set_core_services,
    get_session_service,
    get_dimension_service,
    get_detection_service,
    get_relation_service,
    get_session_options,
)
from .line_router import (
    set_line_services,
    get_line_detector_service,
    get_connectivity_analyzer,
)
from .region_router import (
    set_region_services,
    get_region_segmenter,
)
from .gdt_router import (
    set_gdt_services,
    get_gdt_parser,
)

__all__ = [
    'core_router',
    'dimension_router',
    'line_router',
    'region_router',
    'gdt_router',
    # Core services
    'set_core_services',
    'get_session_service',
    'get_dimension_service',
    'get_detection_service',
    'get_relation_service',
    'get_session_options',
    # Line services
    'set_line_services',
    'get_line_detector_service',
    'get_connectivity_analyzer',
    # Region services
    'set_region_services',
    'get_region_segmenter',
    # GDT services
    'set_gdt_services',
    'get_gdt_parser',
]
