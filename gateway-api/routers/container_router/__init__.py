"""
Container Router package — barrel re-export.

Existing imports (e.g. `from routers.container_router import router`) continue
to work unchanged.

Route map (prefix=/api/v1/containers):
  GET  ""                       → list_containers
  GET  "/status"                → list_container_status
  GET  "/gpu/stats"             → get_gpu_stats
  POST "/{name}/start"          → start_container
  POST "/{name}/stop"           → stop_container
  POST "/{name}/restart"        → restart_container
"""
from fastapi import APIRouter

from .container_ops import (
    list_containers,
    list_container_status,
    start_container,
    stop_container,
    restart_container,
)
from .gpu_ops import get_gpu_stats
from .models import ContainerListResponse, ContainerStatusResponse, ContainerActionResponse, GPUStatsResponse

router = APIRouter(prefix="/api/v1/containers", tags=["containers"])

# Root-level route (empty path avoids FastAPIError with include_router)
router.add_api_route("", list_containers, methods=["GET"], response_model=ContainerListResponse)
router.add_api_route("/status", list_container_status, methods=["GET"], response_model=ContainerStatusResponse)
router.add_api_route("/gpu/stats", get_gpu_stats, methods=["GET"], response_model=GPUStatsResponse)
router.add_api_route("/{container_name}/start", start_container, methods=["POST"], response_model=ContainerActionResponse)
router.add_api_route("/{container_name}/stop", stop_container, methods=["POST"], response_model=ContainerActionResponse)
router.add_api_route("/{container_name}/restart", restart_container, methods=["POST"], response_model=ContainerActionResponse)

__all__ = ["router"]
