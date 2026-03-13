"""
API Key 모델 및 Provider 정의
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


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
