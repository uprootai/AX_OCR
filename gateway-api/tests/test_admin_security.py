"""Protected admin route security tests."""

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient

from common.admin_security import (
    require_admin_token,
    is_docker_admin_routes_enabled,
    is_gpu_config_admin_routes_enabled,
)


def _build_secured_app() -> FastAPI:
    app = FastAPI()

    @app.get("/secured", dependencies=[Depends(require_admin_token)])
    async def secured_endpoint():
        return {"ok": True}

    return app


@pytest.mark.asyncio
async def test_require_admin_token_accepts_x_admin_token(monkeypatch):
    monkeypatch.setenv("GATEWAY_ADMIN_TOKEN", "secret-token")
    app = _build_secured_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/secured", headers={"X-Admin-Token": "secret-token"})

    assert response.status_code == 200
    assert response.json() == {"ok": True}


@pytest.mark.asyncio
async def test_require_admin_token_accepts_bearer_token(monkeypatch):
    monkeypatch.setenv("GATEWAY_ADMIN_TOKEN", "secret-token")
    app = _build_secured_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/secured", headers={"Authorization": "Bearer secret-token"})

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_require_admin_token_rejects_missing_token(monkeypatch):
    monkeypatch.setenv("GATEWAY_ADMIN_TOKEN", "secret-token")
    app = _build_secured_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/secured")

    assert response.status_code == 401
    assert response.json()["detail"] == "Admin authentication required"


@pytest.mark.asyncio
async def test_require_admin_token_rejects_unconfigured_route(monkeypatch):
    monkeypatch.delenv("GATEWAY_ADMIN_TOKEN", raising=False)
    app = _build_secured_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/secured", headers={"X-Admin-Token": "secret-token"})

    assert response.status_code == 503
    assert response.json()["detail"] == "Protected admin route is disabled"


def test_admin_route_flags_default_to_disabled(monkeypatch):
    monkeypatch.delenv("ENABLE_DOCKER_ADMIN_ROUTES", raising=False)
    monkeypatch.delenv("ENABLE_GPU_CONFIG_ADMIN_ROUTES", raising=False)

    assert is_docker_admin_routes_enabled() is False
    assert is_gpu_config_admin_routes_enabled() is False


def test_admin_route_flags_can_be_enabled(monkeypatch):
    monkeypatch.setenv("ENABLE_DOCKER_ADMIN_ROUTES", "true")
    monkeypatch.setenv("ENABLE_GPU_CONFIG_ADMIN_ROUTES", "1")

    assert is_docker_admin_routes_enabled() is True
    assert is_gpu_config_admin_routes_enabled() is True
