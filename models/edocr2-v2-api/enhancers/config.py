"""
Configuration Management

Centralized configuration for enhancement strategies.
Follows Singleton pattern for global config access.
"""

import os
from typing import Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class EDGNetConfig:
    """EDGNet preprocessor configuration"""
    url: str = "http://edgnet-api:5002"
    timeout: int = 30
    merge_distance_threshold: int = 50


@dataclass
class VLConfig:
    """Vision-Language model configuration"""
    provider: str = "openai"
    model: Optional[str] = None
    api_key: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.1


@dataclass
class EnhancementConfig:
    """Global enhancement configuration"""
    edgnet: EDGNetConfig
    vl: VLConfig
    enable_caching: bool = False
    cache_ttl: int = 3600


class ConfigManager:
    """
    Configuration Manager (Singleton)

    Provides centralized access to all enhancement configurations.
    """
    _instance: Optional['ConfigManager'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # EDGNet config
        self.edgnet = EDGNetConfig(
            url=os.getenv("EDGNET_URL", "http://edgnet-api:5002"),
            timeout=int(os.getenv("EDGNET_TIMEOUT", "30")),
            merge_distance_threshold=int(os.getenv("EDGNET_MERGE_THRESHOLD", "50"))
        )

        # VL config
        self.vl = VLConfig(
            provider=os.getenv("VL_PROVIDER", "openai"),
            model=os.getenv("VL_MODEL"),
            api_key=self._get_vl_api_key(),
            max_tokens=int(os.getenv("VL_MAX_TOKENS", "1000")),
            temperature=float(os.getenv("VL_TEMPERATURE", "0.1"))
        )

        # Enhancement config
        self.enhancement = EnhancementConfig(
            edgnet=self.edgnet,
            vl=self.vl,
            enable_caching=os.getenv("ENABLE_CACHING", "false").lower() == "true",
            cache_ttl=int(os.getenv("CACHE_TTL", "3600"))
        )

        self._initialized = True
        logger.info("✅ ConfigManager initialized")

    def _get_vl_api_key(self) -> Optional[str]:
        """Get VL API key based on provider"""
        provider = os.getenv("VL_PROVIDER", "openai")

        if provider == "openai":
            return os.getenv("OPENAI_API_KEY")
        elif provider == "anthropic":
            return os.getenv("ANTHROPIC_API_KEY")

        return None

    def update_vl_provider(self, provider: str, api_key: Optional[str] = None):
        """Update VL provider at runtime"""
        self.vl.provider = provider
        if api_key:
            self.vl.api_key = api_key
        else:
            self.vl.api_key = self._get_vl_api_key()

        logger.info(f"VL provider updated to: {provider}")


# Global config instance
config = ConfigManager()
