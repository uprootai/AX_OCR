"""Pricing Utils Tests - 가격 유틸리티 테스트"""

import pytest
import tempfile
import json
from pathlib import Path
import sys

# 상위 디렉토리 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.utils.pricing_utils import load_pricing_db, get_pricing_info
from schemas.typed_dicts import PricingInfo


class TestPricingUtils:
    """PricingUtils 테스트"""

    def test_load_pricing_db_file_not_exists(self):
        """존재하지 않는 파일 로드 테스트"""
        result = load_pricing_db("/nonexistent/path/pricing.json")
        assert result == {}

    def test_load_pricing_db_valid_file(self):
        """유효한 가격 DB 로드 테스트"""
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_data = {
                "CT": {
                    "모델명": "CT-100",
                    "비고": "테스트용",
                    "단가": 50000,
                    "공급업체": "테스트업체",
                    "리드타임": 7
                },
                "TR": {
                    "모델명": "TR-200",
                    "비고": "",
                    "단가": 100000,
                    "공급업체": "변압기제조",
                    "리드타임": 14
                }
            }
            json.dump(test_data, f, ensure_ascii=False)
            temp_path = f.name

        try:
            result = load_pricing_db(temp_path)
            assert len(result) == 2
            assert result["CT"]["모델명"] == "CT-100"
            assert result["CT"]["단가"] == 50000
            assert result["TR"]["공급업체"] == "변압기제조"
        finally:
            Path(temp_path).unlink()

    def test_load_pricing_db_invalid_json(self):
        """잘못된 JSON 파일 로드 테스트"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            temp_path = f.name

        try:
            result = load_pricing_db(temp_path)
            assert result == {}  # 오류 시 빈 딕셔너리 반환
        finally:
            Path(temp_path).unlink()

    def test_get_pricing_info_existing_class(self):
        """존재하는 클래스 가격 정보 조회 테스트"""
        pricing_db = {
            "CT": {
                "모델명": "CT-100",
                "비고": "변류기",
                "단가": 50000,
                "공급업체": "전기산업",
                "리드타임": 7
            }
        }

        result = get_pricing_info(pricing_db, "CT")
        assert result["모델명"] == "CT-100"
        assert result["단가"] == 50000
        assert result["공급업체"] == "전기산업"
        assert result["리드타임"] == 7

    def test_get_pricing_info_nonexistent_class(self):
        """존재하지 않는 클래스 기본값 테스트"""
        pricing_db = {
            "CT": {
                "모델명": "CT-100",
                "비고": "",
                "단가": 50000,
                "공급업체": "전기산업",
                "리드타임": 7
            }
        }

        result = get_pricing_info(pricing_db, "UNKNOWN")

        # 기본값 확인
        assert result["모델명"] == "N/A"
        assert result["비고"] == ""
        assert result["단가"] == 0
        assert result["공급업체"] == "미정"
        assert result["리드타임"] == 0

    def test_get_pricing_info_empty_db(self):
        """빈 가격 DB 테스트"""
        result = get_pricing_info({}, "CT")

        assert result["모델명"] == "N/A"
        assert result["단가"] == 0

    def test_pricing_info_type_annotation(self):
        """PricingInfo 타입 구조 테스트"""
        pricing_info: PricingInfo = {
            "모델명": "테스트",
            "비고": "비고 내용",
            "단가": 10000,
            "공급업체": "업체명",
            "리드타임": 14
        }

        # 필수 키 존재 확인
        assert "모델명" in pricing_info
        assert "비고" in pricing_info
        assert "단가" in pricing_info
        assert "공급업체" in pricing_info
        assert "리드타임" in pricing_info

        # 타입 확인
        assert isinstance(pricing_info["모델명"], str)
        assert isinstance(pricing_info["단가"], int)
        assert isinstance(pricing_info["리드타임"], int)


class TestTypedDicts:
    """TypedDict 타입 정의 테스트"""

    def test_bbox_dict_structure(self):
        """BBoxDict 구조 테스트"""
        from schemas.typed_dicts import BBoxDict

        bbox: BBoxDict = {
            "x1": 100.0,
            "y1": 150.0,
            "x2": 200.0,
            "y2": 250.0
        }

        assert bbox["x1"] == 100.0
        assert bbox["y2"] == 250.0

    def test_detection_dict_structure(self):
        """DetectionDict 구조 테스트"""
        from schemas.typed_dicts import DetectionDict, BBoxDict

        bbox: BBoxDict = {"x1": 0, "y1": 0, "x2": 100, "y2": 100}

        detection: DetectionDict = {
            "id": "det-001",
            "class_name": "CT",
            "class_id": 2,
            "confidence": 0.95,
            "bbox": bbox,
            "verification_status": "pending"
        }

        assert detection["id"] == "det-001"
        assert detection["class_name"] == "CT"
        assert detection["confidence"] == 0.95
        assert detection["bbox"]["x1"] == 0

    def test_dimension_dict_structure(self):
        """DimensionDict 구조 테스트"""
        from schemas.typed_dicts import DimensionDict, BBoxDict

        bbox: BBoxDict = {"x1": 50, "y1": 50, "x2": 150, "y2": 70}

        dimension: DimensionDict = {
            "id": "dim-001",
            "value": "100mm",
            "dimension_type": "length",
            "confidence": 0.88,
            "bbox": bbox
        }

        assert dimension["value"] == "100mm"
        assert dimension["dimension_type"] == "length"

    def test_bom_item_dict_structure(self):
        """BOMItemDict 구조 테스트"""
        from schemas.typed_dicts import BOMItemDict

        bom_item: BOMItemDict = {
            "item_no": 1,
            "class_name": "변압기",
            "quantity": 3,
            "unit_price": 100000,
            "total_price": 300000
        }

        assert bom_item["item_no"] == 1
        assert bom_item["quantity"] == 3
        assert bom_item["total_price"] == 300000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
