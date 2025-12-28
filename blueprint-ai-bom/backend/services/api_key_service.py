"""API Key 관리 서비스

API 키를 안전하게 저장, 조회, 검증하는 서비스입니다.

보안 고려사항:
- API 키는 Fernet 대칭 암호화로 저장
- 마스터 키는 환경변수 또는 자동 생성
- 키 조회 시 마스킹 처리 (앞 8자 + ****)
- 파일 권한 제한 (600)

지원 프로바이더:
- OpenAI (GPT-4o, GPT-4o-mini)
- Anthropic (Claude 3.5 Sonnet)
- Local VL API
- Google (Gemini) - 향후 지원
"""

import os
import json
import logging
import base64
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

# 암호화 라이브러리 (없으면 base64 인코딩 사용)
try:
    from cryptography.fernet import Fernet
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

logger = logging.getLogger(__name__)


class APIProvider(str, Enum):
    """지원하는 API 프로바이더"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    GOOGLE = "google"


class APIKeyService:
    """API Key 관리 서비스

    기능:
    - API 키 저장 (암호화)
    - API 키 조회 (복호화)
    - API 키 삭제
    - 연결 테스트
    - 마스킹된 키 조회 (UI용)
    """

    # 기본 설정 경로
    DEFAULT_CONFIG_DIR = Path("/data/config")
    DEFAULT_CONFIG_FILE = "api_keys.json"

    # 지원 모델 목록
    SUPPORTED_MODELS = {
        APIProvider.OPENAI: [
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "cost": "저렴", "recommended": True},
            {"id": "gpt-4o", "name": "GPT-4o", "cost": "중간", "recommended": False},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "cost": "높음", "recommended": False},
        ],
        APIProvider.ANTHROPIC: [
            {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "cost": "중간", "recommended": True},
            {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "cost": "높음", "recommended": False},
            {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku", "cost": "저렴", "recommended": False},
        ],
        APIProvider.LOCAL: [
            {"id": "blip-base", "name": "BLIP Base", "cost": "무료", "recommended": True},
            {"id": "custom", "name": "Custom Model", "cost": "무료", "recommended": False},
        ],
        APIProvider.GOOGLE: [
            {"id": "gemini-pro-vision", "name": "Gemini Pro Vision", "cost": "중간", "recommended": True},
        ],
    }

    def __init__(self, config_dir: Optional[Path] = None):
        """서비스 초기화

        Args:
            config_dir: 설정 파일 저장 디렉토리 (기본: /data/config)
        """
        self.config_dir = config_dir or self.DEFAULT_CONFIG_DIR
        self.config_file = self.config_dir / self.DEFAULT_CONFIG_FILE

        # 디렉토리 생성
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # 암호화 키 초기화
        self._init_encryption()

        # 설정 로드
        self._config: Dict[str, Any] = self._load_config()

        logger.info(f"[APIKeyService] 초기화 완료 (config: {self.config_file})")

    def _init_encryption(self):
        """암호화 키 초기화"""
        if not HAS_CRYPTOGRAPHY:
            logger.warning("[APIKeyService] cryptography 라이브러리 없음 - base64 인코딩 사용")
            self._fernet = None
            return

        # 마스터 키: 환경변수 또는 자동 생성
        master_key = os.getenv("API_KEY_MASTER_SECRET")

        if master_key:
            # 환경변수에서 키 사용
            key = base64.urlsafe_b64encode(
                hashlib.sha256(master_key.encode()).digest()
            )
        else:
            # 키 파일에서 로드 또는 생성
            key_file = self.config_dir / ".api_key_secret"
            if key_file.exists():
                key = key_file.read_bytes()
            else:
                key = Fernet.generate_key()
                key_file.write_bytes(key)
                # 파일 권한 제한
                os.chmod(key_file, 0o600)
                logger.info("[APIKeyService] 새 암호화 키 생성")

        self._fernet = Fernet(key)

    def _encrypt(self, plaintext: str) -> str:
        """문자열 암호화"""
        if not self._fernet:
            # 암호화 라이브러리 없으면 base64
            return base64.b64encode(plaintext.encode()).decode()
        return self._fernet.encrypt(plaintext.encode()).decode()

    def _decrypt(self, ciphertext: str) -> str:
        """문자열 복호화"""
        if not self._fernet:
            return base64.b64decode(ciphertext.encode()).decode()
        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except Exception as e:
            logger.error(f"[APIKeyService] 복호화 실패: {e}")
            return ""

    def _load_config(self) -> Dict[str, Any]:
        """설정 파일 로드"""
        if not self.config_file.exists():
            return self._create_default_config()

        try:
            with open(self.config_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"[APIKeyService] 설정 로드 실패: {e}")
            return self._create_default_config()

    def _save_config(self):
        """설정 파일 저장"""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            os.chmod(self.config_file, 0o600)
        except Exception as e:
            logger.error(f"[APIKeyService] 설정 저장 실패: {e}")
            raise

    def _create_default_config(self) -> Dict[str, Any]:
        """기본 설정 생성"""
        config = {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "providers": {
                provider.value: {
                    "enabled": False,
                    "api_key_encrypted": "",
                    "default_model": self.SUPPORTED_MODELS[provider][0]["id"] if provider in self.SUPPORTED_MODELS else "",
                    "base_url": "",
                    "options": {},
                }
                for provider in APIProvider
            },
            # 환경변수 폴백 설정
            "use_env_fallback": True,
        }

        # Local VL API 기본 URL
        config["providers"]["local"]["base_url"] = os.getenv("VL_API_URL", "http://vl-api:5004")
        config["providers"]["local"]["enabled"] = True  # 로컬은 기본 활성화

        self._config = config
        self._save_config()
        return config

    # ============================================================
    # 공개 API
    # ============================================================

    def set_api_key(
        self,
        provider: str,
        api_key: str,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """API 키 저장

        Args:
            provider: 프로바이더 (openai, anthropic, local, google)
            api_key: API 키 (빈 문자열이면 삭제)
            model: 기본 모델 ID
            base_url: API 기본 URL (local 프로바이더용)
            options: 추가 옵션

        Returns:
            저장 결과
        """
        provider = provider.lower()

        if provider not in [p.value for p in APIProvider]:
            raise ValueError(f"지원하지 않는 프로바이더: {provider}")

        provider_config = self._config["providers"].get(provider, {})

        # API 키 저장 (암호화)
        if api_key:
            provider_config["api_key_encrypted"] = self._encrypt(api_key)
            provider_config["enabled"] = True
        else:
            provider_config["api_key_encrypted"] = ""
            provider_config["enabled"] = False

        # 모델 설정
        if model:
            provider_config["default_model"] = model

        # URL 설정
        if base_url:
            provider_config["base_url"] = base_url

        # 추가 옵션
        if options:
            provider_config["options"] = options

        provider_config["updated_at"] = datetime.now().isoformat()

        self._config["providers"][provider] = provider_config
        self._config["updated_at"] = datetime.now().isoformat()
        self._save_config()

        logger.info(f"[APIKeyService] {provider} API 키 저장됨")

        return {
            "success": True,
            "provider": provider,
            "enabled": provider_config["enabled"],
            "model": provider_config.get("default_model", ""),
        }

    def get_api_key(self, provider: str) -> Optional[str]:
        """API 키 조회 (복호화)

        환경변수 폴백 순서:
        1. 저장된 API 키 (암호화)
        2. 환경변수 (use_env_fallback=True인 경우)

        Args:
            provider: 프로바이더

        Returns:
            API 키 (없으면 None)
        """
        provider = provider.lower()
        provider_config = self._config["providers"].get(provider, {})

        # 1. 저장된 키 확인
        encrypted = provider_config.get("api_key_encrypted", "")
        if encrypted:
            return self._decrypt(encrypted)

        # 2. 환경변수 폴백
        if self._config.get("use_env_fallback", True):
            env_mapping = {
                "openai": "OPENAI_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY",
                "google": "GOOGLE_API_KEY",
            }
            env_key = env_mapping.get(provider)
            if env_key:
                return os.getenv(env_key)

        return None

    def get_masked_key(self, provider: str) -> str:
        """마스킹된 API 키 조회 (UI용)

        예: sk-abc123... → sk-abc1****
        """
        key = self.get_api_key(provider)
        if not key:
            return ""

        if len(key) <= 8:
            return "*" * len(key)

        return key[:8] + "*" * 8

    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """프로바이더 설정 조회"""
        provider = provider.lower()
        config = self._config["providers"].get(provider, {})

        # 민감 정보 제외
        return {
            "provider": provider,
            "enabled": config.get("enabled", False),
            "has_key": bool(config.get("api_key_encrypted")),
            "masked_key": self.get_masked_key(provider),
            "default_model": config.get("default_model", ""),
            "base_url": config.get("base_url", ""),
            "options": config.get("options", {}),
            "updated_at": config.get("updated_at", ""),
        }

    def get_all_providers(self) -> List[Dict[str, Any]]:
        """모든 프로바이더 설정 조회"""
        result = []
        for provider in APIProvider:
            config = self.get_provider_config(provider.value)
            config["models"] = self.SUPPORTED_MODELS.get(provider, [])
            result.append(config)
        return result

    def delete_api_key(self, provider: str) -> Dict[str, Any]:
        """API 키 삭제"""
        return self.set_api_key(provider, "")

    def get_model(self, provider: str) -> str:
        """기본 모델 조회"""
        provider = provider.lower()
        config = self._config["providers"].get(provider, {})

        # 1. 저장된 모델
        if config.get("default_model"):
            return config["default_model"]

        # 2. 환경변수 폴백
        if provider == "openai":
            return os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        # 3. 기본값
        provider_enum = APIProvider(provider)
        models = self.SUPPORTED_MODELS.get(provider_enum, [])
        if models:
            return models[0]["id"]

        return ""

    def get_base_url(self, provider: str) -> str:
        """API Base URL 조회"""
        provider = provider.lower()
        config = self._config["providers"].get(provider, {})

        if config.get("base_url"):
            return config["base_url"]

        # 환경변수 폴백
        if provider == "local":
            return os.getenv("VL_API_URL", "http://vl-api:5004")

        return ""

    async def test_connection(self, provider: str) -> Dict[str, Any]:
        """API 연결 테스트

        Returns:
            {
                "success": bool,
                "provider": str,
                "model": str,
                "message": str,
                "latency_ms": float
            }
        """
        import time
        import httpx

        provider = provider.lower()
        api_key = self.get_api_key(provider)
        model = self.get_model(provider)

        start_time = time.time()

        try:
            if provider == "openai":
                return await self._test_openai(api_key, model, start_time)
            elif provider == "anthropic":
                return await self._test_anthropic(api_key, model, start_time)
            elif provider == "local":
                return await self._test_local(start_time)
            elif provider == "google":
                return await self._test_google(api_key, model, start_time)
            else:
                return {
                    "success": False,
                    "provider": provider,
                    "message": f"지원하지 않는 프로바이더: {provider}",
                    "latency_ms": 0,
                }
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return {
                "success": False,
                "provider": provider,
                "model": model,
                "message": str(e),
                "latency_ms": latency,
            }

    async def _test_openai(self, api_key: str, model: str, start_time: float) -> Dict[str, Any]:
        """OpenAI 연결 테스트"""
        import httpx
        import time

        if not api_key:
            return {
                "success": False,
                "provider": "openai",
                "model": model,
                "message": "API 키가 설정되지 않았습니다",
                "latency_ms": 0,
            }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"}
            )

            latency = (time.time() - start_time) * 1000

            if response.status_code == 200:
                return {
                    "success": True,
                    "provider": "openai",
                    "model": model,
                    "message": "연결 성공",
                    "latency_ms": latency,
                }
            elif response.status_code == 401:
                return {
                    "success": False,
                    "provider": "openai",
                    "model": model,
                    "message": "API 키가 유효하지 않습니다",
                    "latency_ms": latency,
                }
            else:
                return {
                    "success": False,
                    "provider": "openai",
                    "model": model,
                    "message": f"API 오류: {response.status_code}",
                    "latency_ms": latency,
                }

    async def _test_anthropic(self, api_key: str, model: str, start_time: float) -> Dict[str, Any]:
        """Anthropic 연결 테스트"""
        import httpx
        import time

        if not api_key:
            return {
                "success": False,
                "provider": "anthropic",
                "model": model,
                "message": "API 키가 설정되지 않았습니다",
                "latency_ms": 0,
            }

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Anthropic은 모델 목록 API가 없으므로 간단한 메시지 전송
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": 10,
                    "messages": [{"role": "user", "content": "Hi"}]
                }
            )

            latency = (time.time() - start_time) * 1000

            if response.status_code == 200:
                return {
                    "success": True,
                    "provider": "anthropic",
                    "model": model,
                    "message": "연결 성공",
                    "latency_ms": latency,
                }
            elif response.status_code == 401:
                return {
                    "success": False,
                    "provider": "anthropic",
                    "model": model,
                    "message": "API 키가 유효하지 않습니다",
                    "latency_ms": latency,
                }
            else:
                error_detail = response.json().get("error", {}).get("message", "Unknown error")
                return {
                    "success": False,
                    "provider": "anthropic",
                    "model": model,
                    "message": f"API 오류: {error_detail}",
                    "latency_ms": latency,
                }

    async def _test_local(self, start_time: float) -> Dict[str, Any]:
        """로컬 VL API 연결 테스트"""
        import httpx
        import time

        base_url = self.get_base_url("local")

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(f"{base_url}/health")
                latency = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    return {
                        "success": True,
                        "provider": "local",
                        "model": "blip-base",
                        "message": "연결 성공",
                        "latency_ms": latency,
                    }
                else:
                    return {
                        "success": False,
                        "provider": "local",
                        "model": "blip-base",
                        "message": f"서버 응답 오류: {response.status_code}",
                        "latency_ms": latency,
                    }
            except httpx.ConnectError:
                latency = (time.time() - start_time) * 1000
                return {
                    "success": False,
                    "provider": "local",
                    "model": "blip-base",
                    "message": f"서버에 연결할 수 없습니다: {base_url}",
                    "latency_ms": latency,
                }

    async def _test_google(self, api_key: str, model: str, start_time: float) -> Dict[str, Any]:
        """Google AI 연결 테스트 (향후 구현)"""
        import time

        latency = (time.time() - start_time) * 1000
        return {
            "success": False,
            "provider": "google",
            "model": model,
            "message": "Google AI 연동은 아직 구현되지 않았습니다",
            "latency_ms": latency,
        }

    def set_env_fallback(self, enabled: bool):
        """환경변수 폴백 설정"""
        self._config["use_env_fallback"] = enabled
        self._save_config()

    def get_active_provider(self) -> Optional[str]:
        """활성화된 프로바이더 중 우선순위가 높은 것 반환

        우선순위: openai > anthropic > google > local
        """
        priority = ["openai", "anthropic", "google", "local"]

        for provider in priority:
            if self.is_provider_ready(provider):
                return provider

        return None

    def is_provider_ready(self, provider: str) -> bool:
        """프로바이더가 사용 가능한지 확인"""
        provider = provider.lower()
        config = self._config["providers"].get(provider, {})

        # Local은 항상 사용 가능 (API 키 불필요)
        if provider == "local":
            return True

        # 저장된 키가 있거나 환경변수가 있으면 사용 가능
        if config.get("api_key_encrypted"):
            return True

        if self._config.get("use_env_fallback", True):
            api_key = self.get_api_key(provider)
            return bool(api_key)

        return False


# 싱글톤 인스턴스
_api_key_service: Optional[APIKeyService] = None


def get_api_key_service() -> APIKeyService:
    """API Key 서비스 싱글톤 인스턴스 반환"""
    global _api_key_service
    if _api_key_service is None:
        _api_key_service = APIKeyService()
    return _api_key_service
