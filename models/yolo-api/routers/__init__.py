"""
YOLO API Routers
"""
from .detection_router import router as detection_router
from .models_router import router as models_router

__all__ = ['detection_router', 'models_router']
