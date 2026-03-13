"""
Customer Config — Default Customer Initializer

8개 기본 고객(DSE, DOOSAN, KEPCO, HYUNDAI, SAMSUNG, STX, PANASIA, HANJIN) 설정
"""

from typing import Dict

from .models import CustomerSettings, OutputTemplate, ParsingProfile


def init_default_customers() -> Dict[str, CustomerSettings]:
    """기본 고객 설정 딕셔너리 반환"""
    customers: Dict[str, CustomerSettings] = {}

    # ── DSE Bearing ───────────────────────────────────────────────────────────
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
        visible_columns=["no", "description", "material", "qty", "weight",
                         "material_cost", "labor_cost", "unit_price", "total_price"],
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
    customers["DSE"] = CustomerSettings(
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

    # ── DOOSAN (두산에너빌리티) ───────────────────────────────────────────────
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
    customers["DOOSAN"] = CustomerSettings(
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

    # ── KEPCO (한국전력) ──────────────────────────────────────────────────────
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
    customers["KEPCO"] = CustomerSettings(
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

    # ── HYUNDAI (현대중공업) ──────────────────────────────────────────────────
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
    customers["HYUNDAI"] = CustomerSettings(
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

    # ── SAMSUNG (삼성물산) ────────────────────────────────────────────────────
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
    customers["SAMSUNG"] = CustomerSettings(
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

    # ── STX (STX조선해양) ─────────────────────────────────────────────────────
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
    customers["STX"] = CustomerSettings(
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

    # ── PANASIA (파나시아 — BWMS 전문) ────────────────────────────────────────
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
    customers["PANASIA"] = CustomerSettings(
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

    # ── HANJIN (한진중공업) ───────────────────────────────────────────────────
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
    customers["HANJIN"] = CustomerSettings(
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

    return customers
