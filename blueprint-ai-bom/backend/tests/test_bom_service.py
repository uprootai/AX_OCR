"""BOM Service Tests - 전력 설비 BOM 생성 테스트"""

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
        """검출 결과로 BOM 생성 테스트 - 전력 설비"""
        detections = [
            {"id": "d1", "class_id": 2, "class_name": "CT", "confidence": 0.9, "verification_status": "approved"},
            {"id": "d2", "class_id": 2, "class_name": "CT", "confidence": 0.85, "verification_status": "approved"},
            {"id": "d3", "class_id": 17, "class_name": "TR", "confidence": 0.95, "verification_status": "approved"},
            {"id": "d4", "class_id": 24, "class_name": "차단기", "confidence": 0.8, "verification_status": "rejected"},  # 제외
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
        assert bom["summary"]["total_items"] == 2  # CT, TR
        assert bom["summary"]["total_quantity"] == 3  # CT x2 + TR x1

    def test_generate_bom_with_modified_class(self):
        """수정된 클래스명으로 BOM 생성 테스트"""
        detections = [
            {"id": "d1", "class_id": 2, "class_name": "CT", "confidence": 0.9,
             "verification_status": "modified", "modified_class_name": "GPT"},
        ]

        bom = self.service.generate_bom(
            session_id="test-session",
            detections=detections
        )

        # 수정된 클래스명 사용
        assert bom["items"][0]["class_name"] == "GPT"

    def test_export_json(self):
        """JSON 내보내기 테스트"""
        bom = self.service.generate_bom(
            session_id="test-session",
            detections=[
                {"id": "d1", "class_id": 2, "class_name": "CT", "confidence": 0.9, "verification_status": "approved"}
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
                {"id": "d1", "class_id": 2, "class_name": "CT", "confidence": 0.9, "verification_status": "approved"}
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
                {"id": "d1", "class_id": 2, "class_name": "CT", "confidence": 0.9, "verification_status": "approved"}
            ]
        )

        output_path = self.service.export_excel(bom, customer_name="Test Customer")

        assert output_path.exists()
        assert output_path.suffix == ".xlsx"

    def test_export_pdf(self):
        """PDF 내보내기 테스트"""
        bom = self.service.generate_bom(
            session_id="test-session",
            detections=[
                {"id": "d1", "class_id": 2, "class_name": "CT", "confidence": 0.9, "verification_status": "approved"}
            ]
        )

        # PDF 내보내기가 구현되어 있으므로 정상 동작해야 함
        output_path = self.service.export_pdf(bom)
        assert output_path.exists()
        assert output_path.suffix == ".pdf"

    def test_summary_calculation(self):
        """요약 계산 테스트"""
        detections = [
            {"id": "d1", "class_id": 2, "class_name": "CT", "confidence": 0.9, "verification_status": "approved"},
            {"id": "d2", "class_id": 17, "class_name": "TR", "confidence": 0.95, "verification_status": "approved"},
            {"id": "d3", "class_id": 17, "class_name": "TR", "confidence": 0.9, "verification_status": "approved"},
        ]

        bom = self.service.generate_bom(
            session_id="test-session",
            detections=detections
        )

        summary = bom["summary"]

        # 가격이 pricing_db에서 로드되므로 기본값 사용 (10000원)
        # CT x1 = 10000, TR x2 = 20000 => 소계 30000
        expected_subtotal = 30000
        expected_vat = expected_subtotal * 0.1
        expected_total = expected_subtotal + expected_vat

        assert summary["subtotal"] == expected_subtotal
        assert summary["vat"] == expected_vat
        assert summary["total"] == expected_total

    def test_bom_items_structure(self):
        """BOM 항목 구조 테스트"""
        detections = [
            {"id": "d1", "class_id": 2, "class_name": "CT", "confidence": 0.9, "verification_status": "approved"},
        ]

        bom = self.service.generate_bom(
            session_id="test-session",
            detections=detections
        )

        assert len(bom["items"]) == 1
        item = bom["items"][0]

        # 필수 필드 확인
        assert "item_no" in item
        assert "class_name" in item
        assert "quantity" in item
        assert "unit_price" in item
        assert "total_price" in item
        assert "detection_ids" in item
        assert "avg_confidence" in item


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
