"""Pricing Utilities - 가격 데이터베이스 공통 유틸리티

detection_service.py와 bom_service.py에서 공통으로 사용하는 가격 DB 로드 로직
"""

import json
import os
import logging
from typing import Dict

from schemas.typed_dicts import PricingInfo

logger = logging.getLogger(__name__)

# 기본 가격 DB 경로
DEFAULT_PRICING_DB_PATH = "/app/classes_info_with_pricing.json"


def load_pricing_db(pricing_db_path: str = DEFAULT_PRICING_DB_PATH) -> Dict[str, PricingInfo]:
    """
    가격 데이터베이스 로드

    Args:
        pricing_db_path: 가격 DB JSON 파일 경로

    Returns:
        가격 정보 딕셔너리 (클래스명 -> PricingInfo)
    """
    if os.path.exists(pricing_db_path):
        try:
            with open(pricing_db_path, 'r', encoding='utf-8') as f:
                pricing_db = json.load(f)
            logger.info(f"[PricingUtils] 가격 DB 로드 성공: {len(pricing_db)} 항목")
            return pricing_db
        except Exception as e:
            logger.error(f"[PricingUtils] 가격 DB 로드 실패: {e}")
    else:
        logger.warning(f"[PricingUtils] 가격 DB 파일 없음: {pricing_db_path}")

    return {}


def get_pricing_info(pricing_db: Dict[str, PricingInfo], class_name: str) -> PricingInfo:
    """
    클래스별 가격 정보 조회

    Args:
        pricing_db: 가격 데이터베이스
        class_name: 클래스 이름

    Returns:
        PricingInfo 타입의 가격 정보
    """
    default_pricing: PricingInfo = {
        "모델명": "N/A",
        "비고": "",
        "단가": 0,
        "공급업체": "미정",
        "리드타임": 0
    }
    return pricing_db.get(class_name, default_pricing)
