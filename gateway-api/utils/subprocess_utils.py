"""
Subprocess Utilities - 공통 subprocess 실행 패턴
보일러플레이트 제거를 위한 표준화된 함수들
"""

import subprocess
import logging
from typing import Optional, Tuple, List

logger = logging.getLogger(__name__)


def run_command(
    cmd: List[str],
    timeout: int = 30,
    capture: bool = True,
    cwd: Optional[str] = None
) -> Tuple[bool, str, str]:
    """
    공통 subprocess 실행 함수

    Args:
        cmd: 실행할 명령어 리스트
        timeout: 타임아웃 (초)
        capture: 출력 캡처 여부
        cwd: 작업 디렉토리

    Returns:
        (success, stdout, stderr) 튜플
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
            timeout=timeout,
            cwd=cwd
        )
        return (
            result.returncode == 0,
            result.stdout or "",
            result.stderr or ""
        )
    except subprocess.TimeoutExpired:
        return False, "", f"Timeout after {timeout}s"
    except Exception as e:
        logger.error(f"Command failed: {cmd}: {e}")
        return False, "", str(e)


def run_docker_command(
    action: str,
    container_name: str,
    timeout: int = 60
) -> Tuple[bool, str]:
    """
    Docker 컨테이너 제어 명령어 실행

    Args:
        action: start, stop, restart 중 하나
        container_name: 컨테이너 이름
        timeout: 타임아웃 (초)

    Returns:
        (success, message) 튜플
    """
    valid_actions = ["start", "stop", "restart"]
    if action not in valid_actions:
        return False, f"Invalid action: {action}. Must be one of {valid_actions}"

    success, stdout, stderr = run_command(
        ["docker", action, container_name],
        timeout=timeout
    )

    if success:
        return True, f"Successfully {action}ed {container_name}"
    else:
        return False, stderr or f"Failed to {action} {container_name}"


def get_docker_logs(
    container_name: str,
    lines: int = 200,
    timeout: int = 30
) -> str:
    """
    Docker 컨테이너 로그 조회

    Args:
        container_name: 컨테이너 이름
        lines: 조회할 줄 수
        timeout: 타임아웃 (초)

    Returns:
        로그 문자열
    """
    success, stdout, stderr = run_command(
        ["docker", "logs", "--tail", str(lines), container_name],
        timeout=timeout
    )

    logs = stdout + stderr
    return logs if logs else "No logs available"


def get_docker_containers() -> List[dict]:
    """
    실행 중인 Docker 컨테이너 목록 조회

    Returns:
        컨테이너 정보 리스트 [{"name": str, "status": str, "ports": str}]
    """
    success, stdout, _ = run_command(
        ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}\t{{.Ports}}"],
        timeout=10
    )

    containers = []
    if success and stdout:
        for line in stdout.strip().split("\n"):
            if line:
                parts = line.split("\t")
                if len(parts) >= 2:
                    containers.append({
                        "name": parts[0],
                        "status": parts[1],
                        "ports": parts[2] if len(parts) > 2 else ""
                    })

    return containers


def get_nvidia_gpu_info() -> Optional[dict]:
    """
    nvidia-smi를 통한 GPU 정보 조회

    Returns:
        GPU 정보 딕셔너리 또는 None
    """
    success, stdout, _ = run_command(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu",
            "--format=csv,noheader,nounits"
        ],
        timeout=5
    )

    if success and stdout:
        parts = stdout.strip().split(", ")
        if len(parts) >= 5:
            return {
                "device_name": parts[0],
                "total_memory": int(float(parts[1])),
                "used_memory": int(float(parts[2])),
                "free_memory": int(float(parts[3])),
                "utilization": int(float(parts[4]))
            }

    return None
