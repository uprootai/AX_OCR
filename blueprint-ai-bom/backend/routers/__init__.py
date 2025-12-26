"""Blueprint AI BOM - Routers"""

from .session_router import router as session_router
from .detection_router import router as detection_router
from .bom_router import router as bom_router
from .verification_router import router as verification_router
from .classification_router import router as classification_router
from .relation_router import router as relation_router

# Analysis routers (분할된 모듈)
from .analysis import (
    core_router as analysis_core_router,
    dimension_router as analysis_dimension_router,
    line_router as analysis_line_router,
    region_router as analysis_region_router,
    gdt_router as analysis_gdt_router,
)

__all__ = [
    "session_router",
    "detection_router",
    "bom_router",
    "verification_router",
    "classification_router",
    "relation_router",
    # Analysis routers
    "analysis_core_router",
    "analysis_dimension_router",
    "analysis_line_router",
    "analysis_region_router",
    "analysis_gdt_router",
]
