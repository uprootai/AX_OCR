"""Export Docker Handler - Docker 이미지 및 docker-compose 관리

self_contained_export_service.py에서 추출된 모듈:
- get_docker_image_size(): Docker 이미지 크기 조회
- export_docker_images(): Docker 이미지를 tar 파일로 저장
- generate_docker_compose(): docker-compose.yml 생성
"""

import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Set

import yaml

from schemas.export import DockerImageInfo

logger = logging.getLogger(__name__)


def get_docker_image_size(
    service_name: str,
    source_prefix: str = "",
) -> float:
    """Docker 이미지 크기 조회 (MB)

    Args:
        service_name: 서비스 이름 (예: yolo-api)
        source_prefix: 소스 이미지 접두사 (예: poc_, poc-)
    """
    # 여러 이미지 이름 형식 시도 (prefix 변형 + prefix 없는 것)
    # Docker Compose는 '_'를, docker compose v2는 '-'를 사용
    alt_prefix = source_prefix.replace("_", "-") if "_" in source_prefix else source_prefix.replace("-", "_")
    image_names_to_try = [
        f"{source_prefix}{service_name}:latest",
        f"{alt_prefix}{service_name}:latest",
        f"{service_name}:latest",
    ]

    for image_name in image_names_to_try:
        try:
            result = subprocess.run(
                ["docker", "image", "inspect", image_name,
                 "--format", "{{.Size}}"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                size_bytes = int(result.stdout.strip())
                return round(size_bytes / (1024 * 1024), 2)
        except Exception as e:
            logger.debug(f"Image not found: {image_name}")
            continue

    logger.warning(f"Failed to get image size for {service_name}")
    return 0.0


def export_docker_images(
    services: List[str],
    output_dir: Path,
    compress: bool,
    port_offset: int,
    service_port_map: Dict[str, int],
    source_prefix: str = "",
) -> Dict[str, DockerImageInfo]:
    """Docker 이미지를 tar 파일로 저장

    Args:
        services: 서비스 목록
        output_dir: 출력 디렉토리
        compress: gzip 압축 여부
        port_offset: 포트 오프셋
        service_port_map: 서비스 포트 매핑
        source_prefix: 소스 이미지 접두사 (예: poc_, poc-)
    """
    results = {}
    output_dir.mkdir(parents=True, exist_ok=True)

    for service in services:
        # 여러 이미지 이름 형식 시도 (prefix 변형 + prefix 없는 것)
        alt_prefix = source_prefix.replace("_", "-") if "_" in source_prefix else source_prefix.replace("-", "_")
        image_names_to_try = [
            f"{source_prefix}{service}:latest",
            f"{alt_prefix}{service}:latest",
            f"{service}:latest",
        ]

        found_image = None
        for img_name in image_names_to_try:
            # 이미지 존재 확인
            check_result = subprocess.run(
                ["docker", "image", "inspect", img_name],
                capture_output=True, text=True
            )
            if check_result.returncode == 0:
                found_image = img_name
                break

        if not found_image:
            logger.warning(f"Docker image not found for {service}, skipping...")
            continue

        # 출력 파일은 항상 표준 이름 사용 (prefix 없이)
        target_image_name = f"{service}:latest"
        file_ext = ".tar.gz" if compress else ".tar"
        output_file = output_dir / f"{service}{file_ext}"

        try:
            # 소스 이미지를 표준 이름으로 태그 (import 시 일관성 위해)
            if found_image != target_image_name:
                subprocess.run(
                    ["docker", "tag", found_image, target_image_name],
                    check=True, timeout=30
                )
                logger.info(f"[Export] Tagged {found_image} as {target_image_name}")

            # 이미지 저장
            if compress:
                cmd = f"docker save {target_image_name} | gzip > {output_file}"
                subprocess.run(cmd, shell=True, check=True, timeout=600)
            else:
                subprocess.run(
                    ["docker", "save", target_image_name, "-o", str(output_file)],
                    check=True, timeout=600
                )

            size_mb = round(output_file.stat().st_size / (1024 * 1024), 2)
            original_port = service_port_map.get(service, 5000)
            mapped_port = original_port + port_offset

            results[service] = DockerImageInfo(
                service_name=service,
                image_name=target_image_name,
                file_name=output_file.name,
                size_mb=size_mb,
                original_port=original_port,
                mapped_port=mapped_port
            )
            logger.info(f"[Export] Docker image saved: {service} ({size_mb} MB)")

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to export Docker image {service}: {e}")
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout exporting Docker image {service}")

    return results


def generate_docker_compose(
    services: List[str],
    output_path: Path,
    port_offset: int,
    container_prefix: str,
    service_port_map: Dict[str, int],
    frontend_services: Set[str],
    backend_to_frontend_map: Dict[str, str],
) -> str:
    """docker-compose.yml 생성 (포트 오프셋 및 컨테이너 접두사 적용)"""
    compose_content = {
        "version": "3.8",
        "services": {},
        "networks": {
            "imported_network": {
                "name": f"{container_prefix}_network",
                "driver": "bridge"
            }
        }
    }

    for service in services:
        original_port = service_port_map.get(service, 5000)
        mapped_port = original_port + port_offset
        container_name = f"{container_prefix}-{service}"

        # 환경변수에서 내부 URL도 오프셋 적용
        env_vars = ["PYTHONUNBUFFERED=1"]

        if service == "gateway-api":
            env_vars.extend([
                f"GATEWAY_PORT={original_port}",
                "GATEWAY_WORKERS=1",
            ])
            # Gateway가 다른 서비스 호출 시 오프셋 적용된 URL 사용
            for svc in services:
                if svc != "gateway-api":
                    svc_port = service_port_map.get(svc, 5000)
                    svc_name = f"{container_prefix}-{svc}"
                    env_key = svc.upper().replace("-", "_") + "_URL"
                    env_vars.append(f"{env_key}=http://{svc_name}:{svc_port}")

        elif service == "yolo-api":
            env_vars.append(f"YOLO_API_PORT={original_port}")
        elif service == "edocr2-v2-api":
            env_vars.append(f"EDOCR2_PORT={original_port}")
        elif service == "paddleocr-api":
            env_vars.extend([f"PADDLEOCR_PORT={original_port}", "USE_GPU=false"])
        elif service == "blueprint-ai-bom-backend":
            yolo_container = f"{container_prefix}-yolo-api"
            env_vars.extend([
                f"BOM_PORT={original_port}",
                f"YOLO_API_URL=http://{yolo_container}:5005"
            ])
        elif service == "blueprint-ai-bom-frontend":
            # 프론트엔드는 특별 처리 (아래에서 별도 생성)
            pass
        else:
            # 기본 포트 환경변수
            port_env_key = service.upper().replace("-", "_") + "_PORT"
            env_vars.append(f"{port_env_key}={original_port}")

        # 프론트엔드 서비스는 별도 처리
        if service in frontend_services:
            backend_service = None
            # 해당 프론트엔드의 백엔드 찾기
            for backend, frontend in backend_to_frontend_map.items():
                if frontend == service:
                    backend_service = backend
                    break

            backend_container = f"{container_prefix}-{backend_service}" if backend_service else None

            compose_content["services"][service] = {
                "image": f"{service}:latest",
                "container_name": container_name,
                "ports": [f"{mapped_port}:80"],  # nginx는 80 포트
                "environment": [
                    # nginx가 백엔드로 프록시할 수 있도록 설정
                    f"BACKEND_URL=http://{backend_container}:5020" if backend_container else "",
                ],
                "depends_on": [backend_service] if backend_service and backend_service in services else [],
                "networks": ["imported_network"],
                "restart": "unless-stopped"
            }
            # 빈 환경변수 제거
            compose_content["services"][service]["environment"] = [
                e for e in compose_content["services"][service]["environment"] if e
            ]
            continue  # 다음 서비스로

        compose_content["services"][service] = {
            "image": f"{service}:latest",
            "container_name": container_name,
            "ports": [f"{mapped_port}:{original_port}"],
            "environment": env_vars,
            "networks": ["imported_network"],
            "restart": "unless-stopped"
        }

    with open(output_path, "w") as f:
        yaml.dump(compose_content, f, default_flow_style=False, sort_keys=False)

    return str(output_path)
