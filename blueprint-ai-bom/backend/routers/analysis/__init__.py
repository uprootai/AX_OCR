"""Analysis Router Package

analysis_router.py를 5개 모듈로 분할:
- core_router.py: 프리셋, 옵션, 분석 실행
- dimension_router.py: 치수 관리
- line_router.py: 선 검출, 연결성 분석
- region_router.py: 영역 분할 (Phase 5)
- gdt_router.py: GD&T 파싱, 표제란 OCR

longterm_router.py에서 분리된 5개 모듈:
- drawing_region_router.py: 도면 영역 세분화
- notes_router.py: 노트/주석 추출
- revision_router.py: 리비전 비교
- vlm_router.py: VLM 자동 분류
- viewlabels_router.py: 뷰 라벨 인식
"""
from .core_router import router as core_router
from .dimension_router import router as dimension_router
from .line_router import router as line_router
from .region_router import router as region_router
from .gdt_router import router as gdt_router
from .batch_router import router as batch_router

# Long-term 기능 라우터 (longterm_router.py에서 분리)
from .drawing_region_router import router as drawing_region_router
from .notes_router import router as notes_router
from .revision_router import router as revision_router
from .vlm_router import router as vlm_router
from .viewlabels_router import router as viewlabels_router

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
# Long-term 서비스 주입 함수들
from .drawing_region_router import set_drawing_region_services
from .notes_router import set_notes_services
from .revision_router import set_revision_services
from .vlm_router import set_vlm_services
from .viewlabels_router import set_viewlabels_services

__all__ = [
    'core_router',
    'dimension_router',
    'line_router',
    'region_router',
    'gdt_router',
    'batch_router',
    # Long-term routers (from longterm_router.py)
    'drawing_region_router',
    'notes_router',
    'revision_router',
    'vlm_router',
    'viewlabels_router',
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
    # Long-term services
    'set_drawing_region_services',
    'set_notes_services',
    'set_revision_services',
    'set_vlm_services',
    'set_viewlabels_services',
]
