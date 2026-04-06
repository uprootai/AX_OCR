"""Protected admin route helpers for Docker and GPU controls."""

import logging
import os
import secrets
from typing import Optional

from fastapi import Header, HTTPException, status

logger = logging.getLogger(__name__)

ADMIN_TOKEN_ENV = "GATEWAY_ADMIN_TOKEN"
DOCKER_ADMIN_ROUTES_ENV = "ENABLE_DOCKER_ADMIN_ROUTES"
GPU_CONFIG_ADMIN_ROUTES_ENV = "ENABLE_GPU_CONFIG_ADMIN_ROUTES"


def _read_bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def is_docker_admin_routes_enabled() -> bool:
    """Docker 제어 라우터 활성화 여부."""
    return _read_bool_env(DOCKER_ADMIN_ROUTES_ENV, default=False)


def is_gpu_config_admin_routes_enabled() -> bool:
    """GPU 설정 라우터 활성화 여부."""
    return _read_bool_env(GPU_CONFIG_ADMIN_ROUTES_ENV, default=False)


def get_gateway_admin_token() -> str:
    """관리자 토큰 조회."""
    return os.getenv(ADMIN_TOKEN_ENV, "").strip()


def has_gateway_admin_token() -> bool:
    """관리자 토큰 설정 여부."""
    return bool(get_gateway_admin_token())


def _extract_bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None

    return token.strip() or None


async def require_admin_token(
    authorization: Optional[str] = Header(default=None),
    x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
) -> None:
    """관리자 토큰이 있는 경우에만 보호된 라우트 접근 허용."""
    expected_token = get_gateway_admin_token()
    if not expected_token:
        logger.error("%s is missing for a protected admin route", ADMIN_TOKEN_ENV)
        raise HTTPException(status_code=503, detail="Protected admin route is disabled")

    presented_token = x_admin_token or _extract_bearer_token(authorization)
    if not presented_token or not secrets.compare_digest(presented_token, expected_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
