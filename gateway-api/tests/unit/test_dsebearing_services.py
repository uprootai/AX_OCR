"""
DSE Bearing Services Unit Tests
"""
import pytest
from services.dsebearing_parser import get_parser, DSEBearingParser, TitleBlockData, PartsListItem
from services.price_database import get_price_database, PriceDatabase
from services.customer_config import get_customer_config, CustomerConfigService
from services.quote_exporter import get_quote_exporter, QuoteExporter


class TestDSEBearingParser:
    """DSE Bearing Parser 테스트"""

    @pytest.fixture
    def parser(self):
        return get_parser()

    def test_parse_title_block_with_drawing_number(self, parser):
        """도면번호 파싱 테스트"""
        ocr_texts = [
            {"text": "TD0062016", "confidence": 0.95},
            {"text": "REV.A", "confidence": 0.9},
            {"text": "THRUST BEARING ASSY", "confidence": 0.88},
        ]
        result = parser.parse_title_block(ocr_texts)

        assert result.drawing_number == "TD0062016"
        assert result.revision == "A"
        assert "BEARING" in result.part_name or "THRUST" in result.part_name

    def test_parse_title_block_with_material(self, parser):
        """재질 파싱 테스트"""
        ocr_texts = [
            {"text": "SF45A", "confidence": 0.92},
            {"text": "ASTM B23 GR.2", "confidence": 0.85},
        ]
        result = parser.parse_title_block(ocr_texts)

        assert result.material in ["SF45A", "ASTM B23 GR.2"]

    def test_parse_title_block_with_string_input(self, parser):
        """문자열 입력 테스트"""
        ocr_texts = ["TD0062016", "REV.B", "RING UPPER"]
        result = parser.parse_title_block(ocr_texts)

        assert result.drawing_number == "TD0062016"
        assert result.revision == "B"

    def test_parse_parts_list_from_table(self, parser):
        """테이블 데이터로 Parts List 파싱 테스트"""
        table_data = [
            ["NO", "DESCRIPTION", "MATERIAL", "QTY", "WT"],
            ["1", "BEARING RING", "SF45A", "2", "25"],
            ["2", "PAD ASSY", "ASTM B23", "4", "5"],
            ["3", "THRUST RUNNER", "SF440A", "1", "80"],
        ]
        items = parser.parse_parts_list(ocr_texts=[], table_data=table_data)

        assert len(items) == 3
        assert items[0].no == "1"
        assert items[0].description == "BEARING RING"
        assert items[0].material == "SF45A"
        assert items[0].qty == 2

    def test_parse_parts_list_empty(self, parser):
        """빈 데이터 테스트"""
        items = parser.parse_parts_list(ocr_texts=[], table_data=[])
        assert len(items) == 0

    def test_normalize_table_data_2d_array(self, parser):
        """2D 배열 정규화 테스트"""
        table_data = [["A", "B"], ["C", "D"]]
        normalized = parser._normalize_table_data(table_data)

        assert normalized == table_data

    def test_normalize_table_data_cells_format(self, parser):
        """cells 형식 정규화 테스트"""
        table_data = [
            {
                "cells": [
                    {"row": 0, "col": 0, "text": "NO"},
                    {"row": 0, "col": 1, "text": "DESC"},
                    {"row": 1, "col": 0, "text": "1"},
                    {"row": 1, "col": 1, "text": "RING"},
                ]
            }
        ]
        normalized = parser._normalize_table_data(table_data)

        assert len(normalized) == 2
        assert normalized[0][0] == "NO"
        assert normalized[1][1] == "RING"

    # --- Dimension Parser Tests ---

    def test_extract_iso_diameter(self, parser):
        """ISO 공차 직경 파싱 테스트 (Ø450H7)"""
        ocr_texts = [{"text": "Ø450H7", "confidence": 0.95}]
        dims = parser.extract_dimensions(ocr_texts)

        assert len(dims) >= 1
        dim = dims[0]
        assert dim["type"] == "iso_diameter"
        assert dim["value"] == 450
        assert dim["iso_grade"] == "H7"
        assert dim["upper_tolerance"] == 0.025
        assert dim["lower_tolerance"] == 0

    def test_extract_iso_linear(self, parser):
        """ISO 공차 선형 치수 테스트 (120h6)"""
        ocr_texts = [{"text": "120h6", "confidence": 0.9}]
        dims = parser.extract_dimensions(ocr_texts)

        assert len(dims) >= 1
        dim = dims[0]
        assert dim["type"] == "iso_linear"
        assert dim["value"] == 120
        assert dim["iso_grade"] == "h6"

    def test_extract_symmetric_tolerance(self, parser):
        """대칭 공차 테스트 (120±0.05)"""
        ocr_texts = [{"text": "120±0.05", "confidence": 0.92}]
        dims = parser.extract_dimensions(ocr_texts)

        assert len(dims) >= 1
        dim = dims[0]
        assert dim["type"] == "symmetric_tolerance"
        assert dim["value"] == 120
        assert dim["upper_tolerance"] == 0.05
        assert dim["lower_tolerance"] == -0.05

    def test_extract_asymmetric_tolerance(self, parser):
        """비대칭 공차 테스트 (50+0.025/-0.000)"""
        ocr_texts = [{"text": "50+0.025/-0.000", "confidence": 0.88}]
        dims = parser.extract_dimensions(ocr_texts)

        assert len(dims) >= 1
        dim = dims[0]
        assert dim["type"] == "asymmetric_tolerance"
        assert dim["value"] == 50
        assert dim["upper_tolerance"] == 0.025
        assert dim["lower_tolerance"] == 0

    def test_extract_thread(self, parser):
        """나사 치수 테스트 (M12x1.5)"""
        ocr_texts = [{"text": "M12x1.5", "confidence": 0.9}]
        dims = parser.extract_dimensions(ocr_texts)

        assert len(dims) >= 1
        dim = dims[0]
        assert dim["type"] == "thread"
        assert dim["nominal_diameter"] == 12
        assert dim["pitch"] == 1.5

    def test_extract_angle(self, parser):
        """각도 치수 테스트 (45°)"""
        ocr_texts = [{"text": "45°", "confidence": 0.95}]
        dims = parser.extract_dimensions(ocr_texts)

        assert len(dims) >= 1
        dim = dims[0]
        assert dim["type"] == "angle"
        assert dim["value"] == 45
        assert dim["unit"] == "deg"

    def test_extract_surface_roughness_ra(self, parser):
        """표면 거칠기 Ra 테스트"""
        ocr_texts = [{"text": "Ra 0.8", "confidence": 0.9}]
        dims = parser.extract_dimensions(ocr_texts)

        assert len(dims) >= 1
        dim = dims[0]
        assert dim["type"] == "roughness_ra"
        assert dim["value"] == 0.8
        assert dim["roughness_type"] == "Ra"
        assert dim["unit"] == "um"

    def test_extract_surface_roughness_n_grade(self, parser):
        """표면 거칠기 N등급 테스트"""
        ocr_texts = [{"text": "N6", "confidence": 0.9}]
        dims = parser.extract_dimensions(ocr_texts)

        assert len(dims) >= 1
        dim = dims[0]
        assert dim["type"] == "roughness_n"
        assert dim["value"] == 0.8
        assert dim["n_grade"] == "N6"

    def test_extract_bearing_od_id(self, parser):
        """베어링 OD×ID 테스트"""
        ocr_texts = [{"text": "OD 450 × ID 300", "confidence": 0.92}]
        dims = parser.extract_dimensions(ocr_texts)

        assert len(dims) >= 1
        dim = dims[0]
        assert dim["type"] == "bearing_od_id"
        assert dim["outer_diameter"] == 450
        assert dim["inner_diameter"] == 300

    def test_extract_multiple_dimensions(self, parser):
        """복수 치수 파싱 테스트"""
        ocr_texts = [
            {"text": "Ø450H7", "confidence": 0.95},
            {"text": "120±0.05", "confidence": 0.92},
            {"text": "M12x1.5", "confidence": 0.9},
            {"text": "Ra 0.8", "confidence": 0.88},
        ]
        dims = parser.extract_dimensions(ocr_texts)

        assert len(dims) == 4
        types = [d["type"] for d in dims]
        assert "iso_diameter" in types
        assert "symmetric_tolerance" in types
        assert "thread" in types
        assert "roughness_ra" in types

    def test_get_fit_type(self, parser):
        """끼워맞춤 유형 테스트"""
        assert parser._get_fit_type("H") == "clearance"
        assert parser._get_fit_type("K") == "transition"
        assert parser._get_fit_type("P") == "interference"


class TestPriceDatabase:
    """Price Database 테스트"""

    @pytest.fixture
    def price_db(self):
        return get_price_database()

    def test_get_material_price_exact_match(self, price_db):
        """정확한 재질 매칭 테스트"""
        price = price_db.get_material_price("SF45A")
        assert price == 5000  # KRW/kg

    def test_get_material_price_with_customer_discount(self, price_db):
        """고객 할인 적용 테스트"""
        base_price = price_db.get_material_price("SF45A")
        discounted = price_db.get_material_price("SF45A", customer_id="DSE")

        # DSE 고객은 5% 할인
        assert discounted == base_price * 0.95

    def test_get_labor_cost(self, price_db):
        """가공비 조회 테스트"""
        cost = price_db.get_labor_cost("BEARING RING")
        assert cost > 0

    def test_get_labor_cost_with_customer_discount(self, price_db):
        """가공비 고객 할인 테스트"""
        base_cost = price_db.get_labor_cost("BEARING")
        discounted = price_db.get_labor_cost("BEARING", customer_id="DSE")

        # DSE 고객은 3% 가공비 할인
        assert discounted == base_cost * 0.97

    def test_get_quantity_discount(self, price_db):
        """수량 할인 테스트"""
        assert price_db.get_quantity_discount(5) == 0.0
        assert price_db.get_quantity_discount(10) == 0.05
        assert price_db.get_quantity_discount(50) == 0.10
        assert price_db.get_quantity_discount(100) == 0.15

    def test_calculate_quote(self, price_db):
        """견적 계산 테스트"""
        parts = [
            {"no": "1", "description": "BEARING RING", "material": "SF45A", "qty": 2, "weight": 25},
            {"no": "2", "description": "PAD ASSY", "material": "ASTM B23 GR.2", "qty": 4, "weight": 5},
        ]
        quote = price_db.calculate_quote(parts, customer_id="DSE")

        assert "line_items" in quote
        assert "subtotal" in quote
        assert "total" in quote
        assert quote["total"] > 0
        assert quote["currency"] == "KRW"

    def test_list_materials(self, price_db):
        """재질 목록 테스트"""
        materials = price_db.list_materials()
        assert len(materials) >= 10

        # SF45A가 있어야 함
        codes = [m["code"] for m in materials]
        assert "SF45A" in codes


class TestCustomerConfig:
    """Customer Config 테스트"""

    @pytest.fixture
    def config(self):
        return get_customer_config()

    def test_get_customer_dse(self, config):
        """DSE 고객 조회 테스트"""
        customer = config.get_customer("DSE")

        assert customer is not None
        assert customer.customer_id == "DSE"
        assert customer.customer_name == "DSE Bearing"
        assert customer.material_discount == 0.05

    def test_get_customer_doosan(self, config):
        """두산 고객 조회 테스트"""
        customer = config.get_customer("DOOSAN")

        assert customer is not None
        assert customer.customer_name == "두산에너빌리티"
        assert customer.payment_terms == 45

    def test_get_customer_not_found(self, config):
        """존재하지 않는 고객 테스트"""
        customer = config.get_customer("UNKNOWN")
        assert customer is None

    def test_list_customers(self, config):
        """고객 목록 테스트"""
        customers = config.list_customers()

        assert len(customers) >= 2
        ids = [c["customer_id"] for c in customers]
        assert "DSE" in ids
        assert "DOOSAN" in ids

    def test_get_parsing_profile(self, config):
        """파싱 프로파일 조회 테스트"""
        profile = config.get_parsing_profile("DSE")

        assert profile is not None
        assert profile.profile_id == "dse_bearing"
        assert profile.ocr_engine == "edocr2"

    def test_get_quote_template(self, config):
        """견적 템플릿 조회 테스트"""
        template = config.get_quote_template("DSE")

        assert template is not None
        assert template.type == "quote"
        assert "unit_price" in template.visible_columns

    def test_get_customer_kepco(self, config):
        """KEPCO 고객 조회 테스트"""
        customer = config.get_customer("KEPCO")

        assert customer is not None
        assert customer.customer_name == "한국전력공사"
        assert customer.material_discount == 0.10
        assert customer.payment_terms == 60

    def test_get_customer_hyundai(self, config):
        """현대중공업 고객 조회 테스트"""
        customer = config.get_customer("HYUNDAI")

        assert customer is not None
        assert customer.customer_name == "현대중공업"
        assert customer.material_discount == 0.07

    def test_get_customer_samsung(self, config):
        """삼성물산 고객 조회 테스트"""
        customer = config.get_customer("SAMSUNG")

        assert customer is not None
        assert customer.customer_name == "삼성물산"
        assert customer.currency == "USD"  # 해외 프로젝트

    def test_get_customer_stx(self, config):
        """STX조선해양 고객 조회 테스트"""
        customer = config.get_customer("STX")

        assert customer is not None
        assert customer.customer_name == "STX조선해양"
        assert customer.payment_terms == 45

    def test_list_customers_count(self, config):
        """전체 고객 수 테스트"""
        customers = config.list_customers()
        assert len(customers) >= 6  # DSE, DOOSAN, KEPCO, HYUNDAI, SAMSUNG, STX


class TestQuoteExporter:
    """Quote Exporter 테스트"""

    @pytest.fixture
    def exporter(self, tmp_path):
        return QuoteExporter(str(tmp_path))

    @pytest.fixture
    def sample_quote(self):
        return {
            "quote_number": "Q-TEST-001",
            "date": "2026-01-22",
            "line_items": [
                {"no": "1", "description": "BEARING RING", "material": "SF45A", "qty": 2, "unit_price": 217500, "total_price": 435000},
                {"no": "2", "description": "PAD ASSY", "material": "ASTM B23", "qty": 4, "unit_price": 285000, "total_price": 1140000},
            ],
            "subtotal": 1575000,
            "discount_amount": 0,
            "tax_rate": 0.1,
            "tax": 157500,
            "total": 1732500,
            "currency": "KRW"
        }

    def test_export_to_excel(self, exporter, sample_quote):
        """Excel 내보내기 테스트"""
        excel_bytes = exporter.export_to_excel(sample_quote)

        assert excel_bytes is not None
        assert len(excel_bytes) > 0
        # Excel 파일 시그니처 확인 (PK)
        assert excel_bytes[:2] == b'PK'

    def test_export_to_pdf(self, exporter, sample_quote):
        """PDF 내보내기 테스트"""
        pdf_bytes = exporter.export_to_pdf(sample_quote)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        # PDF 파일 시그니처 확인
        assert pdf_bytes[:4] == b'%PDF'

    def test_save_quote_excel(self, exporter, sample_quote, tmp_path):
        """Excel 파일 저장 테스트"""
        filepath = exporter.save_quote(sample_quote, format="excel")

        assert filepath.endswith(".xlsx")
        import os
        assert os.path.exists(filepath)

    def test_save_quote_pdf(self, exporter, sample_quote, tmp_path):
        """PDF 파일 저장 테스트"""
        filepath = exporter.save_quote(sample_quote, format="pdf")

        assert filepath.endswith(".pdf")
        import os
        assert os.path.exists(filepath)

    def test_export_with_customer_info(self, exporter, sample_quote):
        """고객 정보 포함 내보내기 테스트"""
        customer_info = {
            "customer_name": "DSE Bearing",
            "contact_name": "홍길동",
        }
        excel_bytes = exporter.export_to_excel(sample_quote, customer_info)

        assert excel_bytes is not None
        assert len(excel_bytes) > 0


class TestEdgeCases:
    """Edge Cases 테스트"""

    @pytest.fixture
    def parser(self):
        return get_parser()

    @pytest.fixture
    def price_db(self):
        return get_price_database()

    @pytest.fixture
    def config(self):
        return get_customer_config()

    # --- Parser Edge Cases ---

    def test_parse_empty_ocr_texts(self, parser):
        """빈 OCR 결과 파싱"""
        result = parser.parse_title_block([])
        assert result.drawing_number == ""
        assert result.revision == ""

    def test_parse_title_block_no_drawing_number(self, parser):
        """도면번호 없는 OCR 결과"""
        ocr_texts = [{"text": "BEARING RING", "confidence": 0.9}]
        result = parser.parse_title_block(ocr_texts)
        assert result.drawing_number == ""
        assert "BEARING" in result.part_name or result.part_name == ""

    def test_parse_mixed_confidence_levels(self, parser):
        """다양한 신뢰도 OCR 결과"""
        ocr_texts = [
            {"text": "TD0062016", "confidence": 0.99},
            {"text": "REV.A", "confidence": 0.3},  # 낮은 신뢰도
            {"text": "BEARING", "confidence": 0.85},
        ]
        result = parser.parse_title_block(ocr_texts)
        assert result.drawing_number == "TD0062016"

    def test_extract_dimensions_empty(self, parser):
        """빈 치수 추출"""
        dims = parser.extract_dimensions([])
        assert len(dims) == 0

    def test_extract_dimensions_noise_filtering(self, parser):
        """노이즈 치수 필터링"""
        ocr_texts = [
            {"text": "0.5", "confidence": 0.9},  # 너무 작음
            {"text": "99999", "confidence": 0.9},  # 너무 큼
            {"text": "Ø450H7", "confidence": 0.95},  # 정상
        ]
        dims = parser.extract_dimensions(ocr_texts)
        # 정상 치수만 포함
        types = [d["type"] for d in dims]
        assert "iso_diameter" in types

    def test_parse_parts_list_invalid_no(self, parser):
        """잘못된 번호 형식 Parts List"""
        table_data = [
            ["NO", "DESCRIPTION", "MATERIAL", "QTY"],
            ["ABC", "RING", "SF45A", "2"],  # NO가 숫자가 아님
            ["1", "PAD", "ASTM B23", "4"],
        ]
        items = parser.parse_parts_list([], table_data=table_data)
        assert len(items) == 1  # 유효한 항목만
        assert items[0].no == "1"

    # --- Price Database Edge Cases ---

    def test_get_material_price_unknown(self, price_db):
        """알 수 없는 재질 가격 조회"""
        price = price_db.get_material_price("UNKNOWN_MATERIAL")
        assert price == 5000  # 기본값

    def test_calculate_quote_empty_parts(self, price_db):
        """빈 부품 목록 견적"""
        quote = price_db.calculate_quote([], customer_id="DSE")
        assert quote["subtotal"] == 0
        assert quote["total"] == 0

    def test_calculate_quote_missing_weight(self, price_db):
        """무게 없는 부품 견적"""
        parts = [
            {"no": "1", "description": "RING", "material": "SF45A", "qty": 1}
            # weight 없음
        ]
        quote = price_db.calculate_quote(parts)
        assert "line_items" in quote

    def test_get_quantity_discount_boundary(self, price_db):
        """수량 할인 경계값 테스트"""
        # 실제 할인 구조: 10→5%, 20→7%, 50→10%, 100→15%
        assert price_db.get_quantity_discount(9) == 0.0
        assert price_db.get_quantity_discount(10) == 0.05
        assert price_db.get_quantity_discount(19) == 0.05
        assert price_db.get_quantity_discount(20) == 0.07
        assert price_db.get_quantity_discount(49) == 0.07
        assert price_db.get_quantity_discount(50) == 0.10
        assert price_db.get_quantity_discount(99) == 0.10
        assert price_db.get_quantity_discount(100) == 0.15
        assert price_db.get_quantity_discount(1000) == 0.15

    # --- Customer Config Edge Cases ---

    def test_customer_parsing_profile_patterns(self, config):
        """고객별 파싱 패턴 테스트"""
        dse_profile = config.get_parsing_profile("DSE")
        assert "TD\\d{7}" in dse_profile.drawing_number_patterns

        kepco_profile = config.get_parsing_profile("KEPCO")
        assert kepco_profile is not None
        assert kepco_profile.ocr_engine == "edocr2"

    def test_customer_currency_settings(self, config):
        """고객별 통화 설정 테스트"""
        dse = config.get_customer("DSE")
        samsung = config.get_customer("SAMSUNG")

        assert dse.currency == "KRW"
        assert samsung.currency == "USD"

    def test_customer_discount_range(self, config):
        """고객 할인율 범위 테스트"""
        for customer in config.list_customers():
            assert 0 <= customer["material_discount"] <= 0.20
            assert 0 <= customer["labor_discount"] <= 0.15

    # --- Dimension Parser Complex Cases ---

    def test_dimension_iso_fit_types(self, parser):
        """ISO 끼워맞춤 유형 테스트"""
        # Clearance fit (H)
        ocr_texts = [{"text": "Ø100H7", "confidence": 0.95}]
        dims = parser.extract_dimensions(ocr_texts)
        assert dims[0]["fit_type"] == "clearance"

        # Transition fit (K)
        ocr_texts = [{"text": "Ø100K6", "confidence": 0.95}]
        dims = parser.extract_dimensions(ocr_texts)
        # K6 is not in our table, should still work
        assert dims[0]["type"] == "iso_diameter"

    def test_dimension_surface_roughness_values(self, parser):
        """표면 거칠기 값 테스트"""
        ocr_texts = [
            {"text": "N6", "confidence": 0.9},
            {"text": "Ra 1.6", "confidence": 0.9},
        ]
        dims = parser.extract_dimensions(ocr_texts)

        n6_dim = next((d for d in dims if d.get("n_grade") == "N6"), None)
        assert n6_dim is not None
        assert n6_dim["value"] == 0.8  # N6 = Ra 0.8

    def test_dimension_angle_dms(self, parser):
        """각도 분초 파싱 테스트"""
        ocr_texts = [{"text": "30°15'30\"", "confidence": 0.9}]
        dims = parser.extract_dimensions(ocr_texts)

        assert len(dims) >= 1
        dim = dims[0]
        assert dim["degrees"] == 30
        assert dim["minutes"] == 15
        # 30 + 15/60 + 30/3600 = 30.2583...
        assert 30.25 < dim["value"] < 30.27


class TestIntegration:
    """통합 테스트"""

    @pytest.fixture
    def parser(self):
        return get_parser()

    @pytest.fixture
    def price_db(self):
        return get_price_database()

    @pytest.fixture
    def config(self):
        return get_customer_config()

    def test_full_pipeline_mock(self, parser, price_db, config):
        """전체 파이프라인 모의 테스트"""
        # 1. Title Block 파싱
        ocr_texts = [
            {"text": "TD0062016", "confidence": 0.95},
            {"text": "REV.A", "confidence": 0.9},
            {"text": "RING ASSY T1", "confidence": 0.88},
            {"text": "SF45A", "confidence": 0.92},
        ]
        titleblock = parser.parse_title_block(ocr_texts)

        assert titleblock.drawing_number == "TD0062016"
        assert titleblock.revision == "A"

        # 2. Parts List 파싱
        table_data = [
            ["NO", "DESCRIPTION", "MATERIAL", "QTY", "WT"],
            ["1", "RING UPPER", "SF45A", "1", "25"],
            ["2", "PAD ASSY", "ASTM B23 GR.2", "8", "5"],
        ]
        parts = parser.parse_parts_list([], table_data=table_data)

        assert len(parts) == 2
        assert parts[0].description == "RING UPPER"

        # 3. 견적 생성
        quote_parts = [
            {"no": p.no, "description": p.description, "material": p.material,
             "qty": p.qty, "weight": p.weight or 10}
            for p in parts
        ]

        # 고객 설정 적용
        customer = config.get_customer("DSE")
        quote = price_db.calculate_quote(quote_parts, customer_id=customer.customer_id)

        assert quote["total"] > 0
        assert quote["currency"] == "KRW"
        assert len(quote["line_items"]) == 2

    def test_multi_customer_pricing(self, price_db, config):
        """다중 고객 가격 비교 테스트"""
        parts = [
            {"no": "1", "description": "BEARING RING", "material": "SF45A", "qty": 1, "weight": 25}
        ]

        dse_quote = price_db.calculate_quote(parts, customer_id="DSE")
        doosan_quote = price_db.calculate_quote(parts, customer_id="DOOSAN")
        no_customer_quote = price_db.calculate_quote(parts)  # 할인 없음

        # 모든 견적이 유효해야 함
        assert dse_quote["total"] > 0
        assert doosan_quote["total"] > 0
        assert no_customer_quote["total"] > 0

        # 고객 할인이 적용되면 기본 가격보다 낮아야 함
        assert dse_quote["total"] < no_customer_quote["total"]
        assert doosan_quote["total"] < no_customer_quote["total"]

        # DOOSAN이 DSE보다 많이 할인 (8% vs 5%)
        assert doosan_quote["total"] < dse_quote["total"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
