"""Gateway API Routers"""
from .admin_router import admin_router
from .container_router import router as container_router
from .spec_router import router as spec_router
from .registry_router import router as registry_router
from .workflow_router import router as workflow_router
from .config_router import router as config_router

__all__ = [
    'admin_router',
    'container_router',
    'spec_router',
    'registry_router',
    'workflow_router',
    'config_router',
]
