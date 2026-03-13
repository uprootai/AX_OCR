"""
Customer Config — Data Models

ParsingProfile, OutputTemplate, CustomerSettings 데이터클래스
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


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
    parsing_profile: Optional[ParsingProfile] = None
    # 가격 설정
    material_discount: float = 0.0
    labor_discount: float = 0.0
    payment_terms: int = 30
    currency: str = "KRW"
    # 출력 템플릿
    quote_template: Optional[OutputTemplate] = None
    bom_template: Optional[OutputTemplate] = None
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
