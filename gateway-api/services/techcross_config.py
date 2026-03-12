"""
테크로스 (techcross) Customer Configuration
도면 유형: pid — P&ID 공정배관계장도

생성일: 2026-03-12
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class TechcrossParsingProfile:
    """
    테크로스 도면 파싱 프로파일
    @AX:TODO: 실제 테크로스 패턴으로 교체
    """
    profile_id: str = "techcross"
    name: str = "테크로스"

    drawing_number_patterns: List[str] = field(default_factory=lambda: [
        r"[A-Z]{2}\d{5,8}",
        r"\d{4}-\d{4}",
    ])
    revision_patterns: List[str] = field(default_factory=lambda: [
        r"REV[.\s]*([A-Z])",
        r"Rev[.\s]*([A-Z0-9]+)",
    ])
    material_patterns: List[str] = field(default_factory=lambda: [
        r"S[A-Z]\d{2,3}[A-Z]?",
        r"ASTM\s*[AB]\d+",
    ])

    # @AX:TODO: 실제 헤더로 교체
    table_headers: List[str] = field(default_factory=lambda: [
        "NO", "DESCRIPTION", "MATERIAL", "QTY"
    ])
    column_mapping: Dict[str, str] = field(default_factory=lambda: {
        "NO": "item_no",
        "DESCRIPTION": "description",
        "MATERIAL": "material",
        "QTY": "quantity",
    })

    ocr_engine: str = "edocr2"
    drawing_type: str = "pid"


@dataclass
class TechcrossPricingConfig:
    """
    테크로스 가격 설정
    @AX:WARN — 실제 계약 단가로 반드시 교체
    """
    customer_id: str = "techcross"
    customer_name: str = "테크로스"

    base_rates: Dict[str, float] = field(default_factory=lambda: {
        "machining_per_hour": 0.0,
        "material_markup": 0.0,
        "setup_fee": 0.0,
    })

    lead_times: Dict[str, int] = field(default_factory=lambda: {
        "standard": 14,
        "express": 7,
        "urgent": 3,
    })

    min_order_qty: int = 1
    currency: str = "KRW"


@dataclass
class TechcrossConfig:
    """
    테크로스 통합 설정 — 파싱 + 가격 + 메타데이터
    """
    customer_id: str = "techcross"
    customer_name: str = "테크로스"
    drawing_type: str = "pid"
    is_active: bool = True

    parsing: TechcrossParsingProfile = field(default_factory=TechcrossParsingProfile)
    pricing: TechcrossPricingConfig = field(default_factory=TechcrossPricingConfig)

    model_pipeline: List[str] = field(default_factory=lambda: ["edocr2", "yolo_detection"])


_config_instance: Optional[TechcrossConfig] = None


def get_config() -> TechcrossConfig:
    """설정 인스턴스 반환 (싱글톤)"""
    global _config_instance
    if _config_instance is None:
        _config_instance = TechcrossConfig()
        logger.info(
            f"Loaded config for {_config_instance.customer_name} "
            f"(type: {_config_instance.drawing_type})"
        )
    return _config_instance
