"""
DSE Bearing Quote Router - 견적/가격/고객 관리 엔드포인트

Quote Generator, Price Database, Customer Config, Export
"""

import io
import json
import logging
from datetime import datetime
from fastapi import APIRouter, Form, HTTPException
from pydantic import BaseModel
from typing import List

from services.price_database import get_price_database
from services.customer_config import get_customer_config

logger = logging.getLogger(__name__)

router = APIRouter()


# =====================
# Response Models
# =====================

class QuoteLineItem(BaseModel):
    no: str
    description: str
    material: str
    material_cost: float
    labor_cost: float
    quantity: int
    unit_price: float
    total_price: float

class QuoteGeneratorResponse(BaseModel):
    success: bool
    quote_number: str
    date: str
    items: List[QuoteLineItem]
    subtotal: float
    discount: float
    tax: float
    total: float
    currency: str


# =====================
# Quote Constants
# =====================

# 재질별 단가 (KRW/kg)
MATERIAL_PRICES = {
    "SF45A": 5000,
    "SF440A": 5500,
    "SM490A": 4800,
    "S45C": 4500,
    "S45C-N": 4800,
    "SS400": 3500,
    "STS304": 12000,
    "SCM435": 7000,
    "ASTM B23 GR.2": 45000,  # Babbitt
    "ASTM A193 B7": 8000,
    "SEE EXCEL BOM": 5000,  # 기본값
    "DEFAULT": 5000,
}

# 부품 타입별 가공비 (KRW)
LABOR_COSTS = {
    "RING": 80000,
    "BEARING": 100000,
    "CASING": 120000,
    "PAD": 50000,
    "BOLT": 5000,
    "NUT": 3000,
    "PIN": 8000,
    "WASHER": 2000,
    "PLATE": 15000,
    "ASSY": 150000,
    "DEFAULT": 30000,
}

# 수량 할인
QUANTITY_DISCOUNTS = [
    (100, 0.15),  # 100개 이상: 15%
    (50, 0.10),   # 50개 이상: 10%
    (20, 0.07),   # 20개 이상: 7%
    (10, 0.05),   # 10개 이상: 5%
]


# =====================
# Helper Functions
# =====================

def get_material_price(material: str) -> float:
    """재질별 단가 조회"""
    material_upper = material.upper().strip()
    for key, price in MATERIAL_PRICES.items():
        if key in material_upper or material_upper in key:
            return price
    return MATERIAL_PRICES["DEFAULT"]


def get_labor_cost(description: str) -> float:
    """부품 타입별 가공비 조회"""
    desc_upper = description.upper()
    for key, cost in LABOR_COSTS.items():
        if key in desc_upper:
            return cost
    return LABOR_COSTS["DEFAULT"]


def get_quantity_discount(total_qty: int) -> float:
    """수량 할인율 계산"""
    for min_qty, discount in QUANTITY_DISCOUNTS:
        if total_qty >= min_qty:
            return discount
    return 0.0


# =====================
# Quote Generator
# =====================

@router.post("/quotegenerator", response_model=QuoteGeneratorResponse)
async def generate_quote(
    bom_data: str = Form(None),
    currency: str = Form("KRW"),
    material_markup: float = Form(1.3),
    labor_markup: float = Form(1.5),
    tax_rate: float = Form(0.1),
    customer_id: str = Form(None),
    profile: str = Form("bearing")
):
    """
    견적 생성 - BOM 데이터 기반 자동 견적

    - bom_data: BOM JSON 데이터
    - currency: 통화 (KRW, USD, etc.)
    - material_markup: 재질 마크업 (기본 1.3 = 30%)
    - labor_markup: 가공비 마크업 (기본 1.5 = 50%)
    - tax_rate: 세율 (기본 0.1 = 10%)
    - customer_id: 고객 ID (DSE, DOOSAN 등) - 고객별 할인 적용
    - profile: 프로파일 (bearing)
    """
    logger.info(f"Quote 생성 시작, currency={currency}, customer={customer_id}, profile={profile}")

    # 가격 데이터베이스 초기화
    price_db = get_price_database()

    # BOM 데이터 파싱
    bom_items = []
    if bom_data:
        try:
            data = json.loads(bom_data)
            if isinstance(data, dict):
                bom_items = data.get("matched_items", data.get("items", []))
            elif isinstance(data, list):
                bom_items = data
        except:
            pass

    # BOM이 없으면 Mock 데이터
    if not bom_items:
        bom_items = [
            {"no": "1", "description": "RING UPPER", "material": "SF45A", "qty": 1, "weight": 15.0},
            {"no": "2", "description": "RING LOWER", "material": "SF45A", "qty": 1, "weight": 15.0},
            {"no": "3", "description": "HEX SOCKET HD BOLT", "material": "SCM435", "qty": 4, "weight": 0.5},
            {"no": "4", "description": "DOWEL PIN", "material": "STS304", "qty": 2, "weight": 0.2},
        ]

    # 가격 데이터베이스로 견적 계산
    quote_result = price_db.calculate_quote(
        parts=bom_items,
        customer_id=customer_id,
        material_markup=material_markup,
        labor_markup=labor_markup,
        tax_rate=tax_rate
    )

    # 응답 형식으로 변환
    quote_items = []
    for item in quote_result["line_items"]:
        quote_items.append(QuoteLineItem(
            no=item["no"],
            description=f"{item['description']} ({item['material']})",
            material=item["material"],
            material_cost=item["material_cost"],
            labor_cost=item["labor_cost"],
            quantity=item["qty"],
            unit_price=item["unit_price"],
            total_price=item["total_price"]
        ))

    return QuoteGeneratorResponse(
        success=True,
        quote_number=f"Q-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        date=datetime.now().strftime("%Y-%m-%d"),
        items=quote_items,
        subtotal=quote_result["subtotal"],
        discount=quote_result["discount_amount"],
        tax=quote_result["tax"],
        total=quote_result["total"],
        currency=quote_result["currency"]
    )


# =====================
# Price Database API
# =====================

@router.get("/prices/materials")
async def list_materials():
    """재질 가격 목록 조회"""
    price_db = get_price_database()
    return {
        "success": True,
        "materials": price_db.list_materials(),
        "count": len(price_db.material_prices)
    }


@router.get("/prices/labor")
async def list_labor_costs():
    """가공비 목록 조회"""
    price_db = get_price_database()
    return {
        "success": True,
        "labor_costs": price_db.list_labor_costs(),
        "count": len(price_db.labor_costs)
    }


@router.get("/prices/discounts")
async def get_quantity_discounts_api():
    """수량 할인 테이블 조회"""
    price_db = get_price_database()
    return {
        "success": True,
        "discounts": [
            {"min_qty": qty, "discount_rate": rate, "discount_percent": f"{rate*100:.0f}%"}
            for qty, rate in price_db.quantity_discounts
        ]
    }


# =====================
# Customer API
# =====================

@router.get("/customers/{customer_id}")
async def get_customer_pricing(customer_id: str):
    """고객 가격 설정 조회"""
    price_db = get_price_database()
    config = price_db.get_customer_config(customer_id)

    if not config:
        raise HTTPException(status_code=404, detail=f"Customer not found: {customer_id}")

    return {
        "success": True,
        "customer": {
            "id": config.customer_id,
            "name": config.customer_name,
            "material_discount": config.material_discount,
            "labor_discount": config.labor_discount,
            "payment_terms": config.payment_terms,
            "currency": config.currency
        }
    }


@router.get("/customers")
async def list_customers():
    """고객 목록 조회 (상세 설정 포함)"""
    customer_config = get_customer_config()
    return {
        "success": True,
        "customers": customer_config.list_customers()
    }


@router.get("/customers/{customer_id}/profile")
async def get_customer_profile(customer_id: str):
    """고객 파싱 프로파일 조회"""
    customer_config = get_customer_config()
    profile = customer_config.get_parsing_profile(customer_id)

    if not profile:
        raise HTTPException(status_code=404, detail=f"Customer profile not found: {customer_id}")

    return {
        "success": True,
        "profile": {
            "profile_id": profile.profile_id,
            "name": profile.name,
            "drawing_number_patterns": profile.drawing_number_patterns,
            "revision_patterns": profile.revision_patterns,
            "material_patterns": profile.material_patterns,
            "table_headers": profile.table_headers,
            "ocr_engine": profile.ocr_engine,
            "ocr_profile": profile.ocr_profile,
            "confidence_threshold": profile.confidence_threshold
        }
    }


@router.get("/customers/{customer_id}/template/quote")
async def get_customer_quote_template(customer_id: str):
    """고객 견적서 템플릿 조회"""
    customer_config = get_customer_config()
    template = customer_config.get_quote_template(customer_id)

    if not template:
        raise HTTPException(status_code=404, detail=f"Quote template not found: {customer_id}")

    return {
        "success": True,
        "template": {
            "template_id": template.template_id,
            "name": template.name,
            "type": template.type,
            "include_logo": template.include_logo,
            "visible_columns": template.visible_columns,
            "column_headers_kr": template.column_headers_kr,
            "currency_format": template.currency_format,
            "decimal_places": template.decimal_places,
            "footer_text": template.footer_text
        }
    }


@router.get("/customers/{customer_id}/full")
async def get_customer_full_config(customer_id: str):
    """고객 전체 설정 조회"""
    customer_config = get_customer_config()
    customer = customer_config.get_customer(customer_id)

    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer not found: {customer_id}")

    return {
        "success": True,
        "customer": {
            "customer_id": customer.customer_id,
            "customer_name": customer.customer_name,
            "contact": {
                "name": customer.contact_name,
                "email": customer.contact_email,
                "phone": customer.contact_phone,
                "address": customer.address
            },
            "pricing": {
                "material_discount": customer.material_discount,
                "labor_discount": customer.labor_discount,
                "payment_terms": customer.payment_terms,
                "currency": customer.currency
            },
            "parsing_profile": {
                "profile_id": customer.parsing_profile.profile_id,
                "name": customer.parsing_profile.name,
                "ocr_engine": customer.parsing_profile.ocr_engine
            } if customer.parsing_profile else None,
            "quote_template": {
                "template_id": customer.quote_template.template_id,
                "name": customer.quote_template.name
            } if customer.quote_template else None,
            "is_active": customer.is_active,
            "created_at": customer.created_at,
            "updated_at": customer.updated_at
        }
    }


# =====================
# Quote Export
# =====================

@router.post("/quote/export/excel")
async def export_quote_excel(
    quote_data: str = Form(...),
    customer_id: str = Form(None)
):
    """
    견적서 Excel 내보내기

    - quote_data: 견적 데이터 JSON
    - customer_id: 고객 ID (선택)
    """
    from services.quote_exporter import get_quote_exporter
    from fastapi.responses import StreamingResponse

    try:
        quote = json.loads(quote_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid quote data JSON")

    customer_info = None
    if customer_id:
        customer_config = get_customer_config()
        customer = customer_config.get_customer(customer_id)
        if customer:
            customer_info = {
                "customer_name": customer.customer_name,
                "contact_name": customer.contact_name,
                "contact_email": customer.contact_email,
            }

    exporter = get_quote_exporter()
    excel_bytes = exporter.export_to_excel(quote, customer_info)

    quote_number = quote.get('quote_number', 'quote')
    filename = f"{quote_number}.xlsx"

    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/quote/export/pdf")
async def export_quote_pdf(
    quote_data: str = Form(...),
    customer_id: str = Form(None)
):
    """
    견적서 PDF 내보내기

    - quote_data: 견적 데이터 JSON
    - customer_id: 고객 ID (선택)
    """
    from services.quote_exporter import get_quote_exporter
    from fastapi.responses import StreamingResponse

    try:
        quote = json.loads(quote_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid quote data JSON")

    customer_info = None
    if customer_id:
        customer_config = get_customer_config()
        customer = customer_config.get_customer(customer_id)
        if customer:
            customer_info = {
                "customer_name": customer.customer_name,
                "contact_name": customer.contact_name,
                "contact_email": customer.contact_email,
            }

    exporter = get_quote_exporter()
    pdf_bytes = exporter.export_to_pdf(quote, customer_info)

    quote_number = quote.get('quote_number', 'quote')
    filename = f"{quote_number}.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
