"""
테크로스 P&ID 파서 단위 테스트
실제 OCR 테스트 데이터 기반 (apply-company/techloss/ocr_test/)
"""

import pytest
from services.techcross_parser import (
    extract_equipment_tags,
    extract_valve_tags,
    parse_title_block,
    match_equipment_list,
    parse_parts_list,
    TechcrossParser,
    get_parser,
    EquipmentTag,
    EQUIPMENT_DICTIONARY,
    VALVE_DICTIONARY,
)


# =====================
# 테스트 데이터 (실제 OCR 결과 기반)
# =====================

SAMPLE_OCR_TEXTS = [
    {"text": "CPC", "confidence": 0.9},
    {"text": "PDE-12A", "confidence": 0.9},
    {"text": "ECU 1000B", "confidence": 0.9},
    {"text": "PRU", "confidence": 0.9},
    {"text": "ANU-5T", "confidence": 0.9},
    {"text": "TSU-S", "confidence": 0.85},
    {"text": "NO.1 APU", "confidence": 0.9},
    {"text": "NO.2 APU", "confidence": 0.9},
    {"text": "FMU", "confidence": 0.9},
    {"text": "FTS", "confidence": 0.9},
    {"text": "CSU", "confidence": 0.9},
    {"text": "GDS", "confidence": 0.9},
    {"text": "EWU", "confidence": 0.9},
    {"text": "PCU", "confidence": 0.9},
    {"text": "BWV8", "confidence": 0.9},
    {"text": "BWV14", "confidence": 0.9},
    {"text": "FCV01", "confidence": 0.9},
    {"text": "MIXING S.W.PUMP", "confidence": 0.9},
]


# =====================
# 장비 태그 추출
# =====================

class TestExtractEquipmentTags:
    def test_basic_extraction(self):
        tags = extract_equipment_tags(SAMPLE_OCR_TEXTS)
        tag_ids = {t.tag_id for t in tags}
        assert "CPC" in tag_ids
        assert "PRU" in tag_ids
        assert "FMU" in tag_ids

    def test_tag_with_number(self):
        tags = extract_equipment_tags(SAMPLE_OCR_TEXTS)
        tag_ids = {t.tag_id for t in tags}
        assert "ECU 1000B" in tag_ids
        assert "PDE 12A" in tag_ids

    def test_no_prefix_pattern(self):
        """NO.1 APU → APU 태그로 추출"""
        tags = extract_equipment_tags(SAMPLE_OCR_TEXTS)
        tag_types = {t.tag_type for t in tags}
        assert "APU" in tag_types

    def test_full_name_lookup(self):
        tags = extract_equipment_tags(SAMPLE_OCR_TEXTS)
        ecu_tags = [t for t in tags if t.tag_type == "ECU"]
        assert len(ecu_tags) >= 1
        assert ecu_tags[0].full_name == "Electro Chlorination Unit"

    def test_deduplication(self):
        """동일 tag_id는 한 번만"""
        duped = [
            {"text": "CPC", "confidence": 0.9},
            {"text": "CPC", "confidence": 0.8},
        ]
        tags = extract_equipment_tags(duped)
        assert len([t for t in tags if t.tag_id == "CPC"]) == 1

    def test_empty_input(self):
        assert extract_equipment_tags([]) == []

    def test_no_match(self):
        tags = extract_equipment_tags([{"text": "HELLO WORLD", "confidence": 0.9}])
        assert tags == []

    def test_confidence_preserved(self):
        tags = extract_equipment_tags([{"text": "TSU-S", "confidence": 0.85}])
        tsu = [t for t in tags if t.tag_type == "TSU"]
        assert len(tsu) == 1
        assert tsu[0].confidence == 0.85


# =====================
# 밸브 태그 추출
# =====================

class TestExtractValveTags:
    def test_basic_valve_extraction(self):
        tags = extract_valve_tags(SAMPLE_OCR_TEXTS)
        tag_ids = {t.tag_id for t in tags}
        assert "BWV8" in tag_ids
        assert "BWV14" in tag_ids
        assert "FCV01" in tag_ids

    def test_valve_type_lookup(self):
        tags = extract_valve_tags(SAMPLE_OCR_TEXTS)
        bwv = [t for t in tags if t.valve_type == "BWV"]
        assert len(bwv) >= 2
        assert all(t.valve_type == "BWV" for t in bwv)

    def test_empty_input(self):
        assert extract_valve_tags([]) == []

    def test_no_match(self):
        tags = extract_valve_tags([{"text": "SOME TEXT", "confidence": 0.9}])
        assert tags == []


# =====================
# 표제란 파싱
# =====================

class TestParseTitleBlock:
    def test_system_detection_bwms(self):
        result = parse_title_block("BWMS SYSTEM P&ID DRAWING")
        assert result.system == "BWMS"

    def test_system_detection_ecs(self):
        result = parse_title_block("ECS Electro Chlorination System")
        assert result.system == "ECS"

    def test_drawing_number(self):
        result = parse_title_block("TP-ECS-001 REV.A")
        assert result.drawing_number is not None
        assert "TP" in result.drawing_number

    def test_revision(self):
        result = parse_title_block("DRAWING REV.B APPROVED")
        assert result.revision == "B"

    def test_class_society(self):
        result = parse_title_block("APPROVED BY DNV CLASSIFICATION")
        assert result.class_society == "DNV"

    def test_empty_input(self):
        result = parse_title_block("")
        assert result.drawing_number is None
        assert result.system is None


# =====================
# Equipment List 매칭
# =====================

class TestMatchEquipmentList:
    def test_full_match(self):
        detected = [
            EquipmentTag(tag_id="ECU 1000B", tag_type="ECU", tag_number="1000B",
                         full_name="Electro Chlorination Unit"),
            EquipmentTag(tag_id="CPC", tag_type="CPC", tag_number="",
                         full_name="Central Process Controller"),
        ]
        standard = [
            {"tag_type": "ECU", "description": "Electro Chlorination Unit"},
            {"tag_type": "CPC", "description": "Central Process Controller"},
        ]
        result = match_equipment_list(detected, standard)
        assert result["match_rate"] == 100.0
        assert "ECU" in result["matched"]
        assert "CPC" in result["matched"]

    def test_partial_match(self):
        detected = [
            EquipmentTag(tag_id="ECU 1000B", tag_type="ECU", tag_number="1000B",
                         full_name="Electro Chlorination Unit"),
        ]
        standard = [
            {"tag_type": "ECU", "description": "ECU"},
            {"tag_type": "GDS", "description": "GDS"},
        ]
        result = match_equipment_list(detected, standard)
        assert result["match_rate"] == 50.0
        assert "ECU" in result["matched"]
        assert "GDS" in result["in_list_only"]

    def test_empty_lists(self):
        result = match_equipment_list([], [])
        assert result["match_rate"] == 0.0


# =====================
# Parts List 파싱
# =====================

class TestParsePartsList:
    def test_table_parsing(self):
        table = [
            {"NO": "1", "DESCRIPTION": "ECU Unit", "TAG": "ECU-1", "QTY": "2"},
            {"NO": "2", "DESCRIPTION": "CPC Panel", "TAG": "CPC-1", "QTY": "1"},
        ]
        items = parse_parts_list(table_data=table)
        assert len(items) == 2
        assert items[0].item_no == "1"
        assert items[0].quantity == 2

    def test_empty_table(self):
        assert parse_parts_list(table_data=[]) == []

    def test_no_input(self):
        assert parse_parts_list() == []


# =====================
# TechcrossParser 클래스
# =====================

class TestTechcrossParser:
    def test_singleton(self):
        p1 = get_parser()
        p2 = get_parser()
        assert p1 is p2

    def test_parser_metadata(self):
        parser = TechcrossParser()
        assert parser.DRAWING_TYPE == "pid"
        assert parser.CUSTOMER_ID == "techcross"

    def test_extract_equipment_dict_output(self):
        parser = TechcrossParser()
        result = parser.extract_equipment(SAMPLE_OCR_TEXTS)
        assert isinstance(result, list)
        assert all("tag_id" in item for item in result)
        assert all("full_name" in item for item in result)

    def test_extract_valves_dict_output(self):
        parser = TechcrossParser()
        result = parser.extract_valves(SAMPLE_OCR_TEXTS)
        assert isinstance(result, list)
        assert all("tag_id" in item for item in result)

    def test_parse_title_block_dict_output(self):
        parser = TechcrossParser()
        result = parser.parse_title_block("BWMS SYSTEM TP-ECS-001 REV.A DNV")
        assert isinstance(result, dict)
        assert result["system"] == "BWMS"
        assert result["class_society"] == "DNV"
