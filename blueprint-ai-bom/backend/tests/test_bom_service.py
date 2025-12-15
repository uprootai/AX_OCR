"""BOM Service Tests"""

import pytest
import tempfile
from pathlib import Path
import sys

# 상위 디렉토리 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.bom_service import BOMService
from schemas.bom import ExportFormat


class TestBOMService:
    """BOMService 테스트"""

    def setup_method(self):
        """테스트 설정"""
        self.temp_dir = tempfile.mkdtemp()
        self.service = BOMService(output_dir=Path(self.temp_dir))

    def test_default_prices(self):
        """기본 단가 테이블 테스트"""
        assert len(self.service.DEFAULT_PRICES) == 27
        assert self.service.DEFAULT_PRICES["valve"] == 150000
        assert self.service.DEFAULT_PRICES["bolt"] == 500
        assert self.service.DEFAULT_PRICES["pump"] == 500000

    def test_generate_bom_empty(self):
        """빈 검출에서 BOM 생성 테스트"""
        bom = self.service.generate_bom(
            session_id="test-session",
            detections=[]
        )

        assert bom["session_id"] == "test-session"
        assert bom["items"] == []
        assert bom["summary"]["total_items"] == 0
        assert bom["summary"]["total"] == 0

    def test_generate_bom_with_detections(self):
        """검출 결과로 BOM 생성 테스트"""
        detections = [
            {"id": "d1", "class_id": 17, "class_name": "valve", "confidence": 0.9, "verification_status": "approved"},
            {"id": "d2", "class_id": 17, "class_name": "valve", "confidence": 0.85, "verification_status": "approved"},
            {"id": "d3", "class_id": 1, "class_name": "bolt", "confidence": 0.95, "verification_status": "approved"},
            {"id": "d4", "class_id": 10, "class_name": "pipe", "confidence": 0.8, "verification_status": "rejected"},  # 제외
        ]

        bom = self.service.generate_bom(
            session_id="test-session",
            detections=detections,
            filename="test.png"
        )

        assert bom["session_id"] == "test-session"
        assert bom["filename"] == "test.png"
        assert bom["detection_count"] == 4
        assert bom["approved_count"] == 3  # rejected 제외

        # 항목 확인
        assert bom["summary"]["total_items"] == 2  # valve, bolt
        assert bom["summary"]["total_quantity"] == 3  # valve x2 + bolt x1

        # valve 항목 확인
        valve_item = next(i for i in bom["items"] if i["class_name"] == "valve")
        assert valve_item["quantity"] == 2
        assert valve_item["unit_price"] == 150000
        assert valve_item["total_price"] == 300000
        assert len(valve_item["detection_ids"]) == 2

    def test_generate_bom_with_modified_class(self):
        """수정된 클래스명으로 BOM 생성 테스트"""
        detections = [
            {"id": "d1", "class_id": 17, "class_name": "valve", "confidence": 0.9,
             "verification_status": "modified", "modified_class_name": "gate_valve"},
        ]

        bom = self.service.generate_bom(
            session_id="test-session",
            detections=detections
        )

        # 수정된 클래스명 사용
        assert bom["items"][0]["class_name"] == "gate_valve"

    def test_export_json(self):
        """JSON 내보내기 테스트"""
        bom = self.service.generate_bom(
            session_id="test-session",
            detections=[
                {"id": "d1", "class_id": 1, "class_name": "bolt", "confidence": 0.9, "verification_status": "approved"}
            ]
        )

        output_path = self.service.export_json(bom)

        assert output_path.exists()
        assert output_path.suffix == ".json"

        import json
        with open(output_path) as f:
            data = json.load(f)
            assert data["session_id"] == "test-session"

    def test_export_csv(self):
        """CSV 내보내기 테스트"""
        bom = self.service.generate_bom(
            session_id="test-session",
            detections=[
                {"id": "d1", "class_id": 1, "class_name": "bolt", "confidence": 0.9, "verification_status": "approved"}
            ]
        )

        output_path = self.service.export_csv(bom)

        assert output_path.exists()
        assert output_path.suffix == ".csv"

    def test_export_excel(self):
        """Excel 내보내기 테스트"""
        bom = self.service.generate_bom(
            session_id="test-session",
            detections=[
                {"id": "d1", "class_id": 1, "class_name": "bolt", "confidence": 0.9, "verification_status": "approved"}
            ]
        )

        output_path = self.service.export_excel(bom, customer_name="Test Customer")

        assert output_path.exists()
        assert output_path.suffix == ".xlsx"

    def test_export_pdf_not_implemented(self):
        """PDF 내보내기 미구현 테스트"""
        bom = self.service.generate_bom(
            session_id="test-session",
            detections=[]
        )

        with pytest.raises(NotImplementedError):
            self.service.export(bom, ExportFormat.PDF)

    def test_summary_calculation(self):
        """요약 계산 테스트"""
        detections = [
            {"id": "d1", "class_id": 17, "class_name": "valve", "confidence": 0.9, "verification_status": "approved"},
            {"id": "d2", "class_id": 1, "class_name": "bolt", "confidence": 0.95, "verification_status": "approved"},
            {"id": "d3", "class_id": 1, "class_name": "bolt", "confidence": 0.9, "verification_status": "approved"},
        ]

        bom = self.service.generate_bom(
            session_id="test-session",
            detections=detections
        )

        summary = bom["summary"]

        # valve: 150000, bolt x2: 1000
        expected_subtotal = 150000 + 1000
        expected_vat = expected_subtotal * 0.1
        expected_total = expected_subtotal + expected_vat

        assert summary["subtotal"] == expected_subtotal
        assert summary["vat"] == expected_vat
        assert summary["total"] == expected_total


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
