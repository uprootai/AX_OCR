"""Gateway API Constants - SSOT for all constant values"""

from .docker_services import (
    DOCKER_SERVICE_MAPPING,
    GPU_ENABLED_SERVICES,
    get_container_name,
    is_gpu_enabled_service,
)

from .directories import (
    GATEWAY_BASE_DIR,
    UPLOAD_DIR,
    RESULTS_DIR,
    init_directories,
    get_upload_dir,
    get_results_dir,
    get_project_dir,
)

__all__ = [
    # Docker services
    'DOCKER_SERVICE_MAPPING',
    'GPU_ENABLED_SERVICES',
    'get_container_name',
    'is_gpu_enabled_service',
    # Directories
    'GATEWAY_BASE_DIR',
    'UPLOAD_DIR',
    'RESULTS_DIR',
    'init_directories',
    'get_upload_dir',
    'get_results_dir',
    'get_project_dir',
]
