"""
Container Router - GPU stats operations
Route registration is handled by the package __init__.py (barrel).
"""
import logging

from .models import (
    GPUInfo,
    GPUStatsResponse,
    DOCKER_AVAILABLE,
    docker_client,
)

logger = logging.getLogger(__name__)


async def get_gpu_stats():
    """GPU 사용량 조회 (nvidia-smi)"""
    import subprocess

    def try_nvidia_smi():
        """Try to run nvidia-smi directly or via docker"""
        # 방법 1: 직접 nvidia-smi 실행 시도
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=index,name,memory.used,memory.total,utilization.gpu,temperature.gpu",
                    "--format=csv,noheader,nounits"
                ],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # 방법 2: GPU가 있는 다른 컨테이너를 통해 실행 시도
        if DOCKER_AVAILABLE:
            gpu_containers = ['yolo-api', 'edocr2-v2-api', 'esrgan-api', 'edgnet-api']
            for container_name in gpu_containers:
                try:
                    container = docker_client.containers.get(container_name)
                    if container.status == 'running':
                        exec_result = container.exec_run(
                            "nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu,temperature.gpu --format=csv,noheader,nounits",
                            demux=True
                        )
                        if exec_result.exit_code == 0 and exec_result.output[0]:
                            return exec_result.output[0].decode('utf-8')
                except Exception:
                    continue

        return None

    try:
        output = try_nvidia_smi()

        if output is None:
            return GPUStatsResponse(
                success=True,
                available=False,
                gpus=[],
                error="nvidia-smi not found (no NVIDIA GPU or no running GPU container)"
            )

        gpus = []
        for line in output.strip().split("\n"):
            if not line.strip():
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 5:
                mem_used = int(parts[2])
                mem_total = int(parts[3])
                gpus.append(GPUInfo(
                    index=int(parts[0]),
                    name=parts[1],
                    memory_used=mem_used,
                    memory_total=mem_total,
                    memory_percent=round((mem_used / mem_total) * 100, 1) if mem_total > 0 else 0,
                    utilization=float(parts[4]),
                    temperature=int(parts[5]) if len(parts) > 5 and parts[5].isdigit() else None
                ))

        return GPUStatsResponse(
            success=True,
            available=len(gpus) > 0,
            gpus=gpus
        )

    except Exception as e:
        logger.error(f"Failed to get GPU stats: {e}")
        return GPUStatsResponse(
            success=False,
            available=False,
            gpus=[],
            error=str(e)
        )
