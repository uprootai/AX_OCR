"""
Customer Config — CustomerConfigService

고객 설정 CRUD 서비스 (로드/저장/조회)
"""

import json
import logging
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .defaults import init_default_customers
from .models import CustomerSettings, OutputTemplate, ParsingProfile

logger = logging.getLogger(__name__)


class CustomerConfigService:
    """고객 설정 서비스"""

    def __init__(self, config_dir: Optional[str] = None):
        """
        초기화

        Args:
            config_dir: 설정 파일 디렉토리 경로
        """
        self.config_dir = Path(config_dir) if config_dir else None
        self.customers: Dict[str, CustomerSettings] = {}

        # 기본 고객 설정 초기화
        self.customers.update(init_default_customers())

        # 외부 설정 파일 로드
        if self.config_dir and self.config_dir.exists():
            self._load_configs()

    def _load_configs(self):
        """외부 설정 파일 로드"""
        if not self.config_dir:
            return

        for config_file in self.config_dir.glob("*.json"):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                customer_id = data.get("customer_id")
                if customer_id:
                    # ParsingProfile 로드
                    parsing_data = data.get("parsing_profile", {})
                    parsing = ParsingProfile(**parsing_data) if parsing_data else None

                    # OutputTemplate 로드
                    quote_data = data.get("quote_template", {})
                    quote = OutputTemplate(**quote_data) if quote_data else None

                    bom_data = data.get("bom_template", {})
                    bom = OutputTemplate(**bom_data) if bom_data else None

                    # CustomerSettings 생성
                    settings = CustomerSettings(
                        customer_id=customer_id,
                        customer_name=data.get("customer_name", ""),
                        contact_name=data.get("contact_name", ""),
                        contact_email=data.get("contact_email", ""),
                        contact_phone=data.get("contact_phone", ""),
                        address=data.get("address", ""),
                        parsing_profile=parsing,
                        material_discount=data.get("material_discount", 0.0),
                        labor_discount=data.get("labor_discount", 0.0),
                        payment_terms=data.get("payment_terms", 30),
                        currency=data.get("currency", "KRW"),
                        quote_template=quote,
                        bom_template=bom,
                        is_active=data.get("is_active", True),
                        created_at=data.get("created_at", ""),
                        updated_at=data.get("updated_at", "")
                    )
                    self.customers[customer_id] = settings
                    logger.info(f"고객 설정 로드: {customer_id}")

            except Exception as e:
                logger.error(f"설정 파일 로드 실패 {config_file}: {e}")

    def get_customer(self, customer_id: str) -> Optional[CustomerSettings]:
        """고객 설정 조회 (대소문자 무관)"""
        return self.customers.get(customer_id) or self.customers.get(customer_id.upper())

    def list_customers(self) -> List[Dict[str, Any]]:
        """모든 고객 목록"""
        return [
            {
                "customer_id": c.customer_id,
                "customer_name": c.customer_name,
                "material_discount": c.material_discount,
                "labor_discount": c.labor_discount,
                "payment_terms": c.payment_terms,
                "currency": c.currency,
                "is_active": c.is_active
            }
            for c in self.customers.values()
        ]

    def get_parsing_profile(self, customer_id: str) -> Optional[ParsingProfile]:
        """고객 파싱 프로파일 조회"""
        customer = self.get_customer(customer_id)
        return customer.parsing_profile if customer else None

    def get_quote_template(self, customer_id: str) -> Optional[OutputTemplate]:
        """고객 견적서 템플릿 조회"""
        customer = self.get_customer(customer_id)
        return customer.quote_template if customer else None

    def save_customer(self, settings: CustomerSettings) -> bool:
        """고객 설정 저장"""
        if not self.config_dir:
            logger.warning("설정 디렉토리가 지정되지 않음")
            self.customers[settings.customer_id] = settings
            return True

        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            config_file = self.config_dir / f"{settings.customer_id}.json"

            settings.updated_at = datetime.now().isoformat()

            data = {
                "customer_id": settings.customer_id,
                "customer_name": settings.customer_name,
                "contact_name": settings.contact_name,
                "contact_email": settings.contact_email,
                "contact_phone": settings.contact_phone,
                "address": settings.address,
                "parsing_profile": asdict(settings.parsing_profile) if settings.parsing_profile else {},
                "material_discount": settings.material_discount,
                "labor_discount": settings.labor_discount,
                "payment_terms": settings.payment_terms,
                "currency": settings.currency,
                "quote_template": asdict(settings.quote_template) if settings.quote_template else {},
                "bom_template": asdict(settings.bom_template) if settings.bom_template else {},
                "is_active": settings.is_active,
                "created_at": settings.created_at,
                "updated_at": settings.updated_at
            }

            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self.customers[settings.customer_id] = settings
            logger.info(f"고객 설정 저장: {settings.customer_id}")
            return True

        except Exception as e:
            logger.error(f"고객 설정 저장 실패: {e}")
            return False
