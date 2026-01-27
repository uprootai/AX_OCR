"""
DSE Bearing Customer Configuration Service

고객별 파싱 프로파일, 가격 설정, 출력 템플릿 관리
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ParsingProfile:
    """파싱 프로파일 설정"""
    profile_id: str
    name: str
    # Title Block 파싱 설정
    drawing_number_patterns: List[str] = field(default_factory=lambda: [r"TD\d{7}"])
    revision_patterns: List[str] = field(default_factory=lambda: [r"REV[.\s]*([A-Z])"])
    material_patterns: List[str] = field(default_factory=lambda: [r"SF\d{2,3}[A-Z]?"])
    # Parts List 파싱 설정
    table_headers: List[str] = field(default_factory=lambda: ["NO", "DESCRIPTION", "MATERIAL", "QTY"])
    column_mapping: Dict[str, str] = field(default_factory=dict)
    # OCR 설정
    ocr_engine: str = "edocr2"
    ocr_profile: str = "bearing"
    confidence_threshold: float = 0.7


@dataclass
class OutputTemplate:
    """출력 템플릿 설정"""
    template_id: str
    name: str
    type: str  # quote, bom, report
    # Excel 출력 설정
    include_logo: bool = True
    logo_path: str = ""
    header_format: Dict[str, Any] = field(default_factory=dict)
    footer_text: str = ""
    # 필드 표시 설정
    visible_columns: List[str] = field(default_factory=lambda: [
        "no", "description", "material", "qty", "unit_price", "total_price"
    ])
    column_headers_kr: Dict[str, str] = field(default_factory=lambda: {
        "no": "No.",
        "description": "품명",
        "material": "재질",
        "qty": "수량",
        "unit_price": "단가",
        "total_price": "금액"
    })
    currency_format: str = "KRW"
    decimal_places: int = 0


@dataclass
class CustomerSettings:
    """고객별 전체 설정"""
    customer_id: str
    customer_name: str
    # 연락처 정보
    contact_name: str = ""
    contact_email: str = ""
    contact_phone: str = ""
    address: str = ""
    # 파싱 프로파일
    parsing_profile: ParsingProfile = None
    # 가격 설정
    material_discount: float = 0.0
    labor_discount: float = 0.0
    payment_terms: int = 30
    currency: str = "KRW"
    # 출력 템플릿
    quote_template: OutputTemplate = None
    bom_template: OutputTemplate = None
    # 활성화 상태
    is_active: bool = True
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if self.parsing_profile is None:
            self.parsing_profile = ParsingProfile(
                profile_id=f"{self.customer_id}_default",
                name="Default Profile"
            )
        if self.quote_template is None:
            self.quote_template = OutputTemplate(
                template_id=f"{self.customer_id}_quote",
                name="Default Quote Template",
                type="quote"
            )
        if self.bom_template is None:
            self.bom_template = OutputTemplate(
                template_id=f"{self.customer_id}_bom",
                name="Default BOM Template",
                type="bom"
            )
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()


class CustomerConfigService:
    """고객 설정 서비스"""

    # 기본 고객 설정
    DEFAULT_CUSTOMERS: Dict[str, CustomerSettings] = {}

    def __init__(self, config_dir: Optional[str] = None):
        """
        초기화

        Args:
            config_dir: 설정 파일 디렉토리 경로
        """
        self.config_dir = Path(config_dir) if config_dir else None
        self.customers: Dict[str, CustomerSettings] = {}

        # 기본 고객 설정 초기화
        self._init_default_customers()

        # 외부 설정 파일 로드
        if self.config_dir and self.config_dir.exists():
            self._load_configs()

    def _init_default_customers(self):
        """기본 고객 설정 초기화"""
        # DSE Bearing
        dse_parsing = ParsingProfile(
            profile_id="dse_bearing",
            name="DSE Bearing Profile",
            drawing_number_patterns=[r"TD\d{7}", r"TD\d{6}"],
            revision_patterns=[r"REV[.\s]*([A-Z])", r"Rev[.\s]*([A-Z])"],
            material_patterns=[r"SF\d{2,3}[A-Z]?", r"SM\d{3}[A-Z]?", r"ASTM\s*B23"],
            table_headers=["NO", "DESCRIPTION", "MATERIAL", "SIZE/DWG.NO", "QTY", "WT"],
            ocr_engine="edocr2",
            ocr_profile="bearing"
        )

        dse_quote = OutputTemplate(
            template_id="dse_quote",
            name="DSE Bearing 견적서",
            type="quote",
            include_logo=True,
            visible_columns=["no", "description", "material", "qty", "weight", "material_cost", "labor_cost", "unit_price", "total_price"],
            column_headers_kr={
                "no": "No.",
                "description": "품명/규격",
                "material": "재질",
                "qty": "수량",
                "weight": "중량(kg)",
                "material_cost": "재료비",
                "labor_cost": "가공비",
                "unit_price": "단가",
                "total_price": "금액"
            },
            footer_text="※ 본 견적서는 30일간 유효합니다."
        )

        self.customers["DSE"] = CustomerSettings(
            customer_id="DSE",
            customer_name="DSE Bearing",
            contact_name="홍길동",
            contact_email="dse@example.com",
            contact_phone="010-1234-5678",
            address="서울시 강남구",
            parsing_profile=dse_parsing,
            material_discount=0.05,
            labor_discount=0.03,
            payment_terms=30,
            currency="KRW",
            quote_template=dse_quote
        )

        # DOOSAN
        doosan_parsing = ParsingProfile(
            profile_id="doosan_enerbility",
            name="두산에너빌리티 Profile",
            drawing_number_patterns=[r"TD\d{7}", r"DW\d{8}"],
            revision_patterns=[r"REV[.\s]*([A-Z\d])"],
            material_patterns=[r"SF\d{2,3}[A-Z]?", r"SM\d{3}[A-Z]?", r"STS\d{3}"],
            table_headers=["NO", "DESCRIPTION", "MATERIAL", "DWG.NO", "Q'TY", "REMARK"],
            ocr_engine="edocr2",
            ocr_profile="bearing"
        )

        doosan_quote = OutputTemplate(
            template_id="doosan_quote",
            name="두산에너빌리티 견적서",
            type="quote",
            include_logo=True,
            visible_columns=["no", "description", "material", "qty", "unit_price", "total_price"],
            column_headers_kr={
                "no": "항목",
                "description": "품명",
                "material": "재질",
                "qty": "수량",
                "unit_price": "단가",
                "total_price": "합계"
            },
            footer_text="※ 결제조건: 납품 후 45일\n※ 부가세 별도"
        )

        self.customers["DOOSAN"] = CustomerSettings(
            customer_id="DOOSAN",
            customer_name="두산에너빌리티",
            contact_name="김철수",
            contact_email="doosan@example.com",
            contact_phone="02-1234-5678",
            address="창원시 성산구",
            parsing_profile=doosan_parsing,
            material_discount=0.08,
            labor_discount=0.05,
            payment_terms=45,
            currency="KRW",
            quote_template=doosan_quote
        )

        # KEPCO (한국전력)
        kepco_parsing = ParsingProfile(
            profile_id="kepco_power",
            name="한국전력 Profile",
            drawing_number_patterns=[r"KP\d{8}", r"TD\d{7}"],
            revision_patterns=[r"REV[.\s]*(\d+)", r"R(\d+)"],
            material_patterns=[r"SF\d{2,3}[A-Z]?", r"SUS\d{3}", r"STS\d{3}"],
            table_headers=["NO", "PART NAME", "MATERIAL", "DWG NO", "QTY", "REMARK"],
            ocr_engine="edocr2",
            ocr_profile="bearing"
        )

        kepco_quote = OutputTemplate(
            template_id="kepco_quote",
            name="한국전력 견적서",
            type="quote",
            include_logo=True,
            visible_columns=["no", "description", "material", "qty", "unit_price", "total_price"],
            column_headers_kr={
                "no": "순번",
                "description": "품명/규격",
                "material": "재질",
                "qty": "수량",
                "unit_price": "단가(원)",
                "total_price": "금액(원)"
            },
            footer_text="※ 결제조건: 납품 후 60일\n※ 부가세 별도\n※ 입찰보증금 별도"
        )

        self.customers["KEPCO"] = CustomerSettings(
            customer_id="KEPCO",
            customer_name="한국전력공사",
            contact_name="박영희",
            contact_email="kepco@example.com",
            contact_phone="02-3456-7890",
            address="나주시 빛가람동",
            parsing_profile=kepco_parsing,
            material_discount=0.10,  # 10% 할인 (대량구매)
            labor_discount=0.07,
            payment_terms=60,
            currency="KRW",
            quote_template=kepco_quote
        )

        # HYUNDAI (현대중공업)
        hyundai_parsing = ParsingProfile(
            profile_id="hyundai_heavy",
            name="현대중공업 Profile",
            drawing_number_patterns=[r"HHI-\d{6}", r"HD\d{7}"],
            revision_patterns=[r"REV[.\s]*([A-Z])", r"R([A-Z])"],
            material_patterns=[r"SF\d{2,3}[A-Z]?", r"SM\d{3}[A-Z]?", r"SCM\d{3}"],
            table_headers=["ITEM", "DESCRIPTION", "MATERIAL", "SPEC", "QTY", "UNIT", "REMARKS"],
            ocr_engine="edocr2",
            ocr_profile="bearing"
        )

        hyundai_quote = OutputTemplate(
            template_id="hyundai_quote",
            name="현대중공업 견적서",
            type="quote",
            include_logo=True,
            visible_columns=["no", "description", "material", "spec", "qty", "unit_price", "total_price"],
            column_headers_kr={
                "no": "ITEM",
                "description": "품명",
                "material": "재질",
                "spec": "규격",
                "qty": "수량",
                "unit_price": "단가",
                "total_price": "금액"
            },
            footer_text="※ 결제조건: 납품 후 30일\n※ 부가세 별도\n※ 납기: 발주 후 4주"
        )

        self.customers["HYUNDAI"] = CustomerSettings(
            customer_id="HYUNDAI",
            customer_name="현대중공업",
            contact_name="이민수",
            contact_email="hyundai@example.com",
            contact_phone="052-123-4567",
            address="울산시 동구",
            parsing_profile=hyundai_parsing,
            material_discount=0.07,
            labor_discount=0.05,
            payment_terms=30,
            currency="KRW",
            quote_template=hyundai_quote
        )

        # SAMSUNG (삼성물산)
        samsung_parsing = ParsingProfile(
            profile_id="samsung_engineering",
            name="삼성물산 Profile",
            drawing_number_patterns=[r"SEC-\d{6}", r"SG\d{7}"],
            revision_patterns=[r"REV[.\s]*([A-Z\d])"],
            material_patterns=[r"SF\d{2,3}[A-Z]?", r"SUS\d{3}[A-Z]?", r"A\d{4}"],
            table_headers=["NO", "ITEM", "MATERIAL", "SIZE", "Q'TY", "REMARK"],
            ocr_engine="edocr2",
            ocr_profile="bearing"
        )

        samsung_quote = OutputTemplate(
            template_id="samsung_quote",
            name="삼성물산 견적서",
            type="quote",
            include_logo=True,
            visible_columns=["no", "description", "material", "qty", "unit_price", "total_price", "lead_time"],
            column_headers_kr={
                "no": "Item",
                "description": "Description",
                "material": "Material",
                "qty": "Qty",
                "unit_price": "Unit Price",
                "total_price": "Amount",
                "lead_time": "Lead Time"
            },
            currency_format="USD",
            footer_text="※ Payment Terms: T/T 30 days\n※ Delivery: 4-6 weeks after PO\n※ Validity: 30 days"
        )

        self.customers["SAMSUNG"] = CustomerSettings(
            customer_id="SAMSUNG",
            customer_name="삼성물산",
            contact_name="최정우",
            contact_email="samsung@example.com",
            contact_phone="02-2145-6789",
            address="서울시 서초구",
            parsing_profile=samsung_parsing,
            material_discount=0.06,
            labor_discount=0.04,
            payment_terms=30,
            currency="USD",  # 해외 프로젝트 대응
            quote_template=samsung_quote
        )

        # STX (STX조선해양)
        stx_parsing = ParsingProfile(
            profile_id="stx_offshore",
            name="STX조선해양 Profile",
            drawing_number_patterns=[r"STX-\d{6}", r"SO\d{7}"],
            revision_patterns=[r"REV[.\s]*([A-Z])"],
            material_patterns=[r"SF\d{2,3}[A-Z]?", r"SM\d{3}[A-Z]?", r"AB/AH\d+"],
            table_headers=["NO", "DESCRIPTION", "MATERIAL", "DWG NO", "QTY"],
            ocr_engine="edocr2",
            ocr_profile="bearing"
        )

        stx_quote = OutputTemplate(
            template_id="stx_quote",
            name="STX조선해양 견적서",
            type="quote",
            include_logo=True,
            visible_columns=["no", "description", "material", "qty", "unit_price", "total_price"],
            column_headers_kr={
                "no": "품번",
                "description": "품명",
                "material": "재질",
                "qty": "수량",
                "unit_price": "단가",
                "total_price": "금액"
            },
            footer_text="※ 결제조건: 납품 후 45일\n※ 부가세 별도\n※ 선급금 30% 별도"
        )

        self.customers["STX"] = CustomerSettings(
            customer_id="STX",
            customer_name="STX조선해양",
            contact_name="정대현",
            contact_email="stx@example.com",
            contact_phone="055-234-5678",
            address="창원시 진해구",
            parsing_profile=stx_parsing,
            material_discount=0.05,
            labor_discount=0.03,
            payment_terms=45,
            currency="KRW",
            quote_template=stx_quote
        )

        # PANASIA (파나시아 - BWMS 전문)
        panasia_parsing = ParsingProfile(
            profile_id="panasia_bwms",
            name="파나시아 BWMS Profile",
            drawing_number_patterns=[
                r"PA-\d{6}",        # PA-123456
                r"PNA-\d{5}",       # PNA-12345
                r"BWMS-\d{4}",      # BWMS-1234
                r"PID-\d{4}",       # P&ID 도면
            ],
            revision_patterns=[r"REV[.\s]*([A-Z\d])", r"R(\d+)"],
            material_patterns=[
                r"STS\d{3}[A-Z]?",  # STS316, STS304L
                r"SUS\d{3}[A-Z]?",  # SUS316, SUS304
                r"AL\d{4}",         # AL5083
                r"CPVC",            # CPVC 파이프
                r"HDPE",            # HDPE 파이프
                r"TITANIUM",        # 티타늄
            ],
            table_headers=["TAG NO", "DESCRIPTION", "MATERIAL", "SIZE", "QTY", "REMARK"],
            column_mapping={
                "TAG NO": "tag_no",
                "DESCRIPTION": "description",
                "MATERIAL": "material",
                "SIZE": "size",
                "QTY": "qty",
                "REMARK": "remark"
            },
            ocr_engine="edocr2",
            ocr_profile="pid",  # P&ID 특화 프로파일
            confidence_threshold=0.75
        )

        panasia_quote = OutputTemplate(
            template_id="panasia_quote",
            name="파나시아 견적서",
            type="quote",
            include_logo=True,
            visible_columns=["no", "tag_no", "description", "material", "size", "qty", "unit_price", "total_price"],
            column_headers_kr={
                "no": "No.",
                "tag_no": "TAG NO",
                "description": "품명/규격",
                "material": "재질",
                "size": "SIZE",
                "qty": "수량",
                "unit_price": "단가",
                "total_price": "금액"
            },
            footer_text="※ 결제조건: 납품 후 30일\n※ 부가세 별도\n※ 납기: 발주 후 6-8주\n※ IMO 인증 제품"
        )

        self.customers["PANASIA"] = CustomerSettings(
            customer_id="PANASIA",
            customer_name="파나시아",
            contact_name="김해양",
            contact_email="panasia@example.com",
            contact_phone="051-987-6543",
            address="부산시 강서구 미음산단",
            parsing_profile=panasia_parsing,
            material_discount=0.06,
            labor_discount=0.04,
            payment_terms=30,
            currency="KRW",
            quote_template=panasia_quote
        )

        # HANJIN (한진중공업)
        hanjin_parsing = ParsingProfile(
            profile_id="hanjin_heavy",
            name="한진중공업 Profile",
            drawing_number_patterns=[r"HJ-\d{6}", r"HJH\d{7}"],
            revision_patterns=[r"REV[.\s]*([A-Z])"],
            material_patterns=[r"SF\d{2,3}[A-Z]?", r"SM\d{3}[A-Z]?", r"AH\d{2}"],
            table_headers=["NO", "PART NAME", "MATERIAL", "SIZE", "Q'TY", "REMARK"],
            ocr_engine="edocr2",
            ocr_profile="bearing"
        )

        hanjin_quote = OutputTemplate(
            template_id="hanjin_quote",
            name="한진중공업 견적서",
            type="quote",
            include_logo=True,
            visible_columns=["no", "description", "material", "qty", "unit_price", "total_price"],
            column_headers_kr={
                "no": "번호",
                "description": "품명",
                "material": "재질",
                "qty": "수량",
                "unit_price": "단가",
                "total_price": "금액"
            },
            footer_text="※ 결제조건: 납품 후 30일\n※ 부가세 별도"
        )

        self.customers["HANJIN"] = CustomerSettings(
            customer_id="HANJIN",
            customer_name="한진중공업",
            contact_name="박조선",
            contact_email="hanjin@example.com",
            contact_phone="051-234-5678",
            address="부산시 영도구",
            parsing_profile=hanjin_parsing,
            material_discount=0.05,
            labor_discount=0.03,
            payment_terms=30,
            currency="KRW",
            quote_template=hanjin_quote
        )

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
        """고객 설정 조회"""
        return self.customers.get(customer_id)

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


# 싱글톤 인스턴스
_customer_config_instance = None


def get_customer_config(config_dir: Optional[str] = None) -> CustomerConfigService:
    """고객 설정 서비스 인스턴스 반환"""
    global _customer_config_instance
    if _customer_config_instance is None:
        _customer_config_instance = CustomerConfigService(config_dir)
    return _customer_config_instance


# ========== 고객-모델 매핑 ==========
# 고객별 최적화된 YOLO 모델 자동 선택
# model_registry.yaml의 모델 ID와 매핑

CUSTOMER_TO_MODEL_MAP: Dict[str, str] = {
    # BWMS/해양 - P&ID 심볼 모델
    "PANASIA": "pid_symbol",        # 파나시아 (BWMS 전문, P&ID 도면)
    "STX": "pid_symbol",            # STX조선해양 (선박 P&ID)
    "HANJIN": "pid_symbol",         # 한진중공업 (조선/해양)
    "HYUNDAI": "pid_symbol",        # 현대중공업 (조선/해양)

    # 전력 설비 - BOM 검출 모델
    "KEPCO": "bom_detector",        # 한국전력 (전력 설비 단선도)

    # 베어링/기계 - 기계도면 모델
    "DSE": "engineering",           # DSE Bearing (기계도면)
    "DOOSAN": "engineering",        # 두산에너빌리티 (발전설비 기계도면)

    # 해외 프로젝트 - 기본 모델
    "SAMSUNG": "engineering",       # 삼성물산 (기본)
}

# 도면 타입별 추천 모델
DRAWING_TYPE_TO_MODEL_MAP: Dict[str, str] = {
    "pid": "pid_symbol",            # P&ID 도면
    "pfd": "pid_symbol",            # 공정 흐름도
    "sld": "bom_detector",          # 전력 단선도
    "mechanical": "engineering",    # 기계도면
    "bearing": "engineering",       # 베어링 도면
    "mcp": "panasia",               # MCP 제어반
    "control_panel": "panasia",     # 제어반
}


def get_model_for_customer(
    customer_id: str,
    drawing_type: Optional[str] = None,
    default_model: str = "engineering"
) -> str:
    """
    고객 ID 또는 도면 타입에 따른 YOLO 모델 반환

    Args:
        customer_id: 고객 ID (DSE, PANASIA 등)
        drawing_type: 도면 타입 (pid, sld, mechanical 등)
        default_model: 매칭 실패 시 기본 모델

    Returns:
        YOLO 모델 ID (model_registry.yaml의 키)
    """
    # 1. 도면 타입으로 먼저 확인 (더 구체적)
    if drawing_type:
        drawing_type_lower = drawing_type.lower()
        if drawing_type_lower in DRAWING_TYPE_TO_MODEL_MAP:
            return DRAWING_TYPE_TO_MODEL_MAP[drawing_type_lower]

    # 2. 고객 ID로 확인
    customer_upper = customer_id.upper() if customer_id else ""
    if customer_upper in CUSTOMER_TO_MODEL_MAP:
        return CUSTOMER_TO_MODEL_MAP[customer_upper]

    # 3. 기본 모델 반환
    return default_model


def list_available_models() -> List[Dict[str, Any]]:
    """사용 가능한 모델 목록 반환"""
    return [
        {"model_id": "engineering", "name": "기계도면 심볼", "classes": 14},
        {"model_id": "pid_symbol", "name": "P&ID 심볼", "classes": 32},
        {"model_id": "pid_class_agnostic", "name": "P&ID 범용", "classes": 1},
        {"model_id": "pid_class_aware", "name": "P&ID 분류", "classes": 32},
        {"model_id": "bom_detector", "name": "전력 설비 단선도", "classes": 27},
        {"model_id": "panasia", "name": "파나시아 MCP Panel", "classes": 27},
    ]
