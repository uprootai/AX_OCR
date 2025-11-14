"""
API Authentication Middleware

간단한 API 키 기반 인증 시스템
"""

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from typing import Optional
import os
from pathlib import Path

# API 키 헤더
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# 설정 파일에서 API 키 로드
def load_api_keys():
    """Load API keys from environment or config file"""
    # 환경변수에서 로드
    env_key = os.getenv("API_KEY")
    if env_key:
        return {env_key: "default"}

    # security_config.yaml에서 로드 (있는 경우)
    config_path = Path("/home/uproot/ax/poc/security_config.yaml")
    if config_path.exists():
        try:
            import yaml
            with open(config_path) as f:
                config = yaml.safe_load(f)
                if config and "authentication" in config:
                    keys = config["authentication"].get("api_keys", [])
                    return {k["key"]: k.get("name", "unknown") for k in keys}
        except Exception as e:
            print(f"Warning: Failed to load security config: {e}")

    # 기본값: 인증 비활성화
    return {}

# 전역 API 키 저장소
VALID_API_KEYS = load_api_keys()

# 인증 활성화 여부
AUTHENTICATION_ENABLED = os.getenv("ENABLE_AUTH", "false").lower() == "true"


async def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """
    Verify API key from request header

    Args:
        api_key: API key from X-API-Key header

    Returns:
        Client name associated with the API key

    Raises:
        HTTPException: If authentication is enabled and key is invalid
    """
    # 인증 비활성화 시 통과
    if not AUTHENTICATION_ENABLED:
        return "unauthenticated"

    # API 키 없음
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Please provide X-API-Key header."
        )

    # API 키 검증
    if api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )

    return VALID_API_KEYS[api_key]


def require_auth():
    """
    Dependency to require authentication for an endpoint

    Usage:
        @app.get("/protected", dependencies=[Depends(require_auth())])
        async def protected_endpoint():
            return {"message": "You are authenticated"}
    """
    from fastapi import Depends
    return Depends(verify_api_key)
