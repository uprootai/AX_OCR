"""
API Key Service - 외부 AI API 키 관리 서비스

기능:
- API Key 암호화 저장 (Fernet 대칭키)
- Provider별 모델 선택
- 환경변수 Fallback
- 연결 테스트
"""

import os
import json
import base64
import logging
from pathlib import Path
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


class APIProvider(str, Enum):
    """지원하는 AI API Provider"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    LOCAL = "local"  # Local VL API (qwen-vl, llava 등)


@dataclass
class APIKeyConfig:
    """API Key 설정"""
    provider: str
    api_key: str  # 암호화된 키
    model: str
    enabled: bool = True
    last_tested: Optional[str] = None
    test_result: Optional[bool] = None


class APIKeyService:
    """API Key 관리 서비스"""

    # Provider별 지원 모델
    SUPPORTED_MODELS: Dict[APIProvider, List[Dict[str, Any]]] = {
        APIProvider.OPENAI: [
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "cost": "저렴", "recommended": True},
            {"id": "gpt-4o", "name": "GPT-4o", "cost": "중간", "recommended": False},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "cost": "높음", "recommended": False},
        ],
        APIProvider.ANTHROPIC: [
            {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "cost": "중간", "recommended": True},
            {"id": "claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku", "cost": "저렴", "recommended": False},
            {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "cost": "높음", "recommended": False},
        ],
        APIProvider.GOOGLE: [
            {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "cost": "저렴", "recommended": True},
            {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "cost": "중간", "recommended": False},
            {"id": "gemini-2.0-flash-exp", "name": "Gemini 2.0 Flash", "cost": "저렴", "recommended": False},
        ],
        APIProvider.LOCAL: [
            {"id": "qwen-vl", "name": "Qwen-VL (Local)", "cost": "무료", "recommended": True},
            {"id": "llava", "name": "LLaVA (Local)", "cost": "무료", "recommended": False},
        ],
    }

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Args:
            config_dir: 설정 파일 저장 경로 (기본: /data/config 또는 ./config)
        """
        if config_dir:
            self.config_dir = config_dir
        else:
            # Docker 환경 또는 로컬 환경
            if os.path.exists("/data"):
                self.config_dir = Path("/data/config")
            else:
                self.config_dir = Path(__file__).parent.parent / "config"

        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "api_keys.json"

        # 암호화 키 (환경변수 또는 생성)
        self._encryption_key = self._get_or_create_encryption_key()

        # 설정 로드
        self._configs: Dict[str, APIKeyConfig] = {}
        self._load_configs()

    def _get_or_create_encryption_key(self) -> bytes:
        """암호화 키 가져오기 또는 생성"""
        key_env = os.getenv("SECRET_KEY")
        if key_env:
            # 환경변수에서 키 사용
            return base64.urlsafe_b64encode(key_env.encode()[:32].ljust(32, b'\0'))

        # 키 파일에서 로드 또는 생성
        key_file = self.config_dir / ".encryption_key"
        if key_file.exists():
            return key_file.read_bytes()

        # 새 키 생성
        try:
            from cryptography.fernet import Fernet
            new_key = Fernet.generate_key()
        except ImportError:
            # cryptography 없으면 base64로 단순 인코딩
            import secrets
            new_key = base64.urlsafe_b64encode(secrets.token_bytes(32))

        key_file.write_bytes(new_key)
        key_file.chmod(0o600)  # 소유자만 읽기/쓰기
        return new_key

    def _encrypt(self, plaintext: str) -> str:
        """문자열 암호화"""
        try:
            from cryptography.fernet import Fernet
            f = Fernet(self._encryption_key)
            return f.encrypt(plaintext.encode()).decode()
        except ImportError:
            # Fallback: base64 인코딩 (보안 약함)
            return base64.urlsafe_b64encode(plaintext.encode()).decode()

    def _decrypt(self, ciphertext: str) -> str:
        """문자열 복호화"""
        try:
            from cryptography.fernet import Fernet
            f = Fernet(self._encryption_key)
            return f.decrypt(ciphertext.encode()).decode()
        except ImportError:
            # Fallback: base64 디코딩
            return base64.urlsafe_b64decode(ciphertext.encode()).decode()
        except Exception as e:
            logger.warning(f"Decryption failed: {e}")
            return ""

    def _load_configs(self):
        """설정 파일 로드"""
        if not self.config_file.exists():
            return

        try:
            data = json.loads(self.config_file.read_text())
            for provider, config_data in data.items():
                self._configs[provider] = APIKeyConfig(**config_data)
        except Exception as e:
            logger.error(f"Failed to load API key configs: {e}")

    def _save_configs(self):
        """설정 파일 저장"""
        try:
            data = {k: asdict(v) for k, v in self._configs.items()}
            self.config_file.write_text(json.dumps(data, indent=2))
            self.config_file.chmod(0o600)  # 소유자만 읽기/쓰기
        except Exception as e:
            logger.error(f"Failed to save API key configs: {e}")

    def set_api_key(self, provider: str, api_key: str, model: Optional[str] = None) -> bool:
        """
        API Key 설정

        Args:
            provider: API Provider (openai, anthropic, google, local)
            api_key: API Key
            model: 사용할 모델 (없으면 추천 모델)

        Returns:
            성공 여부
        """
        try:
            provider_enum = APIProvider(provider)
        except ValueError:
            logger.error(f"Unknown provider: {provider}")
            return False

        # 모델 기본값
        if not model:
            models = self.SUPPORTED_MODELS.get(provider_enum, [])
            recommended = next((m for m in models if m.get("recommended")), None)
            model = recommended["id"] if recommended else models[0]["id"] if models else ""

        # 암호화 및 저장
        encrypted_key = self._encrypt(api_key)
        self._configs[provider] = APIKeyConfig(
            provider=provider,
            api_key=encrypted_key,
            model=model,
            enabled=True
        )
        self._save_configs()
        logger.info(f"API Key set for provider: {provider}")
        return True

    def get_api_key(self, provider: str) -> Optional[str]:
        """
        API Key 조회 (복호화된 평문)
        환경변수 Fallback 지원

        Args:
            provider: API Provider

        Returns:
            복호화된 API Key 또는 None
        """
        # 1. 저장된 설정에서 조회
        config = self._configs.get(provider)
        if config and config.enabled and config.api_key:
            decrypted = self._decrypt(config.api_key)
            if decrypted:
                return decrypted

        # 2. 환경변수 Fallback
        env_mapping = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GOOGLE_API_KEY",
        }

        env_key = env_mapping.get(provider)
        if env_key:
            return os.getenv(env_key)

        return None

    def get_model(self, provider: str) -> Optional[str]:
        """
        선택된 모델 조회

        Args:
            provider: API Provider

        Returns:
            모델 ID 또는 None
        """
        config = self._configs.get(provider)
        if config:
            return config.model

        # 기본 모델 반환
        try:
            provider_enum = APIProvider(provider)
            models = self.SUPPORTED_MODELS.get(provider_enum, [])
            recommended = next((m for m in models if m.get("recommended")), None)
            return recommended["id"] if recommended else None
        except ValueError:
            return None

    def set_model(self, provider: str, model: str) -> bool:
        """
        모델 선택

        Args:
            provider: API Provider
            model: 모델 ID

        Returns:
            성공 여부
        """
        if provider not in self._configs:
            # 설정이 없으면 빈 설정 생성
            self._configs[provider] = APIKeyConfig(
                provider=provider,
                api_key="",
                model=model,
                enabled=True
            )
        else:
            self._configs[provider].model = model

        self._save_configs()
        return True

    def delete_api_key(self, provider: str) -> bool:
        """
        API Key 삭제

        Args:
            provider: API Provider

        Returns:
            성공 여부
        """
        if provider in self._configs:
            del self._configs[provider]
            self._save_configs()
            logger.info(f"API Key deleted for provider: {provider}")
            return True
        return False

    def get_all_settings(self) -> Dict[str, Any]:
        """
        모든 API Key 설정 조회 (키는 마스킹)

        Returns:
            Provider별 설정 (API Key 마스킹됨)
        """
        result = {}

        for provider_enum in APIProvider:
            provider = provider_enum.value
            config = self._configs.get(provider)

            # API Key 마스킹
            masked_key = None
            has_key = False
            source = None

            if config and config.api_key:
                decrypted = self._decrypt(config.api_key)
                if decrypted:
                    has_key = True
                    masked_key = f"****{decrypted[-4:]}" if len(decrypted) > 4 else "****"
                    source = "dashboard"

            # 환경변수 체크
            if not has_key:
                env_key = self.get_api_key(provider)
                if env_key:
                    has_key = True
                    masked_key = f"****{env_key[-4:]}" if len(env_key) > 4 else "****"
                    source = "environment"

            result[provider] = {
                "has_key": has_key,
                "masked_key": masked_key,
                "source": source,
                "model": config.model if config else self.get_model(provider),
                "models": self.SUPPORTED_MODELS.get(provider_enum, []),
                "enabled": config.enabled if config else True,
            }

        return result

    async def test_connection(self, provider: str, api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        API 연결 테스트

        Args:
            provider: API Provider
            api_key: 테스트할 API Key (없으면 저장된 키 사용)

        Returns:
            테스트 결과
        """
        import asyncio
        from datetime import datetime

        key_to_test = api_key or self.get_api_key(provider)

        if not key_to_test and provider != "local":
            return {
                "success": False,
                "error": "API Key가 설정되지 않았습니다",
                "provider": provider
            }

        try:
            if provider == "openai":
                result = await self._test_openai(key_to_test)
            elif provider == "anthropic":
                result = await self._test_anthropic(key_to_test)
            elif provider == "google":
                result = await self._test_google(key_to_test)
            elif provider == "local":
                result = await self._test_local()
            else:
                result = {"success": False, "error": f"Unknown provider: {provider}"}

            # 테스트 결과 저장
            if provider in self._configs:
                self._configs[provider].last_tested = datetime.now().isoformat()
                self._configs[provider].test_result = result.get("success", False)
                self._save_configs()

            return result

        except Exception as e:
            logger.error(f"Connection test failed for {provider}: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": provider
            }

    async def _test_openai(self, api_key: str) -> Dict[str, Any]:
        """OpenAI API 테스트"""
        import httpx

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"}
            )

            if response.status_code == 200:
                data = response.json()
                model_count = len(data.get("data", []))
                return {
                    "success": True,
                    "message": f"연결 성공 (사용 가능한 모델: {model_count}개)",
                    "provider": "openai"
                }
            elif response.status_code == 401:
                return {
                    "success": False,
                    "error": "잘못된 API Key입니다",
                    "provider": "openai"
                }
            else:
                return {
                    "success": False,
                    "error": f"API 오류: {response.status_code}",
                    "provider": "openai"
                }

    async def _test_anthropic(self, api_key: str) -> Dict[str, Any]:
        """Anthropic API 테스트"""
        import httpx

        async with httpx.AsyncClient(timeout=10.0) as client:
            # Anthropic은 messages endpoint로 테스트
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-3-5-haiku-20241022",
                    "max_tokens": 1,
                    "messages": [{"role": "user", "content": "Hi"}]
                }
            )

            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "연결 성공",
                    "provider": "anthropic"
                }
            elif response.status_code == 401:
                return {
                    "success": False,
                    "error": "잘못된 API Key입니다",
                    "provider": "anthropic"
                }
            else:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                return {
                    "success": False,
                    "error": error_data.get("error", {}).get("message", f"API 오류: {response.status_code}"),
                    "provider": "anthropic"
                }

    async def _test_google(self, api_key: str) -> Dict[str, Any]:
        """Google AI API 테스트"""
        import httpx

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"https://generativelanguage.googleapis.com/v1/models?key={api_key}"
            )

            if response.status_code == 200:
                data = response.json()
                model_count = len(data.get("models", []))
                return {
                    "success": True,
                    "message": f"연결 성공 (사용 가능한 모델: {model_count}개)",
                    "provider": "google"
                }
            elif response.status_code == 400 or response.status_code == 401:
                return {
                    "success": False,
                    "error": "잘못된 API Key입니다",
                    "provider": "google"
                }
            else:
                return {
                    "success": False,
                    "error": f"API 오류: {response.status_code}",
                    "provider": "google"
                }

    async def _test_local(self) -> Dict[str, Any]:
        """Local VL API 테스트"""
        import httpx

        vl_url = os.getenv("VL_API_URL", "http://vl-api:5004")

        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(f"{vl_url}/health")
                if response.status_code == 200:
                    return {
                        "success": True,
                        "message": "Local VL API 연결 성공",
                        "provider": "local"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"VL API 응답 오류: {response.status_code}",
                        "provider": "local"
                    }
            except httpx.ConnectError:
                return {
                    "success": False,
                    "error": "VL API에 연결할 수 없습니다",
                    "provider": "local"
                }


# Singleton instance
_api_key_service: Optional[APIKeyService] = None


def get_api_key_service() -> APIKeyService:
    """API Key 서비스 싱글톤 인스턴스 반환"""
    global _api_key_service
    if _api_key_service is None:
        _api_key_service = APIKeyService()
    return _api_key_service
