"""PDF Report Service 테스트

PDF 리포트 생성 기능 테스트
"""

import pytest
from io import BytesIO

from services.pdf_report_service import PDFReportService, get_pdf_report_service


class TestPDFReportService:
    """PDFReportService 테스트"""

    @pytest.fixture
    def service(self):
        """PDF 서비스 인스턴스"""
        return PDFReportService()

    @pytest.fixture
    def mock_session_data(self):
        """테스트용 세션 데이터"""
        return {
            "session_id": "test-session-123",
            "pid_equipment": [
                {
                    "tag": "P-101",
                    "equipment_type": "Pump",
                    "description": "Ballast Water Pump",
                    "vendor_supply": True,
                    "confidence": 0.95,
                    "verification_status": "verified",
                    "notes": "Main pump"
                },
                {
                    "tag": "V-201",
                    "equipment_type": "Vessel",
                    "description": "Reactor Vessel",
                    "vendor_supply": False,
                    "confidence": 0.88,
                    "verification_status": "pending",
                    "notes": ""
                }
            ],
            "pid_valves": [
                {
                    "valve_id": "XV-101",
                    "valve_type": "Ball Valve",
                    "category": "Isolation",
                    "region_name": "Reactor Area",
                    "confidence": 0.92,
                    "verification_status": "verified",
                    "notes": ""
                },
                {
                    "valve_id": "CV-102",
                    "valve_type": "Control Valve",
                    "category": "Control",
                    "region_name": "Pump Area",
                    "confidence": 0.78,
                    "verification_status": "pending",
                    "notes": "Check sizing"
                }
            ],
            "pid_checklist_items": [
                {
                    "item_no": "1.1",
                    "category": "Safety",
                    "description": "All safety valves are properly sized",
                    "auto_status": "pass",
                    "final_status": "pass",
                    "evidence": "PSV-101 sizing verified",
                    "verification_status": "verified",
                    "reviewer_notes": ""
                },
                {
                    "item_no": "2.1",
                    "category": "Control",
                    "description": "All control valves have proper fail positions",
                    "auto_status": "fail",
                    "final_status": "fail",
                    "evidence": "CV-102 missing fail position",
                    "verification_status": "verified",
                    "reviewer_notes": "Need to update"
                },
                {
                    "item_no": "3.1",
                    "category": "Instrumentation",
                    "description": "All instruments are tagged",
                    "auto_status": "pass",
                    "final_status": "N/A",
                    "evidence": "",
                    "verification_status": "pending",
                    "reviewer_notes": ""
                }
            ],
            "pid_deviations": [
                {
                    "category": "Safety",
                    "severity": "major",
                    "source": "Design Checker",
                    "title": "Missing PSV on reactor vessel",
                    "description": "Reactor vessel V-201 requires pressure safety valve",
                    "location": "Reactor Area",
                    "reference_standard": "ASME VIII",
                    "reference_value": "Required",
                    "actual_value": "Not found",
                    "action_required": "Add PSV to vessel",
                    "action_taken": "",
                    "verification_status": "pending",
                    "notes": ""
                }
            ]
        }

    @pytest.fixture
    def empty_session_data(self):
        """빈 세션 데이터"""
        return {
            "session_id": "empty-session",
            "pid_equipment": [],
            "pid_valves": [],
            "pid_checklist_items": [],
            "pid_deviations": []
        }

    def test_service_initialization(self, service):
        """서비스 초기화 테스트"""
        assert service is not None
        assert service.styles is not None

    def test_singleton_instance(self):
        """싱글톤 패턴 테스트"""
        service1 = get_pdf_report_service()
        service2 = get_pdf_report_service()
        assert service1 is service2

    def test_generate_full_report(self, service, mock_session_data):
        """전체 리포트 생성 테스트"""
        buffer = service.generate_report(
            session_data=mock_session_data,
            project_name="Test Project",
            drawing_no="DWG-001",
            export_type="all",
            include_rejected=False
        )

        assert isinstance(buffer, BytesIO)
        # PDF 헤더 확인
        buffer.seek(0)
        header = buffer.read(4)
        assert header == b'%PDF', "Generated file is not a valid PDF"

    def test_generate_equipment_only_report(self, service, mock_session_data):
        """Equipment만 포함된 리포트 생성 테스트"""
        buffer = service.generate_report(
            session_data=mock_session_data,
            project_name="Test Project",
            drawing_no="DWG-001",
            export_type="equipment",
            include_rejected=False
        )

        assert isinstance(buffer, BytesIO)
        buffer.seek(0)
        content = buffer.read()
        assert len(content) > 0

    def test_generate_valve_only_report(self, service, mock_session_data):
        """Valve만 포함된 리포트 생성 테스트"""
        buffer = service.generate_report(
            session_data=mock_session_data,
            project_name="Test Project",
            drawing_no="DWG-001",
            export_type="valve",
            include_rejected=False
        )

        assert isinstance(buffer, BytesIO)
        buffer.seek(0)
        content = buffer.read()
        assert len(content) > 0

    def test_generate_checklist_only_report(self, service, mock_session_data):
        """Checklist만 포함된 리포트 생성 테스트"""
        buffer = service.generate_report(
            session_data=mock_session_data,
            project_name="Test Project",
            drawing_no="DWG-001",
            export_type="checklist",
            include_rejected=False
        )

        assert isinstance(buffer, BytesIO)
        buffer.seek(0)
        content = buffer.read()
        assert len(content) > 0

    def test_generate_deviation_only_report(self, service, mock_session_data):
        """Deviation만 포함된 리포트 생성 테스트"""
        buffer = service.generate_report(
            session_data=mock_session_data,
            project_name="Test Project",
            drawing_no="DWG-001",
            export_type="deviation",
            include_rejected=False
        )

        assert isinstance(buffer, BytesIO)
        buffer.seek(0)
        content = buffer.read()
        assert len(content) > 0

    def test_generate_empty_report(self, service, empty_session_data):
        """빈 데이터로 리포트 생성 테스트"""
        # 빈 데이터도 최소한 표지와 요약은 생성되어야 함
        buffer = service.generate_report(
            session_data=empty_session_data,
            project_name="Empty Project",
            drawing_no="N/A",
            export_type="all",
            include_rejected=False
        )

        assert isinstance(buffer, BytesIO)
        buffer.seek(0)
        header = buffer.read(4)
        assert header == b'%PDF'

    def test_include_rejected_items(self, service, mock_session_data):
        """거부된 항목 포함 테스트"""
        # rejected 항목 추가
        mock_session_data["pid_equipment"].append({
            "tag": "REJECTED-001",
            "equipment_type": "Unknown",
            "description": "Should be excluded unless include_rejected=True",
            "vendor_supply": False,
            "confidence": 0.3,
            "verification_status": "rejected",
            "notes": "False positive"
        })

        # include_rejected=False
        buffer1 = service.generate_report(
            session_data=mock_session_data,
            export_type="equipment",
            include_rejected=False
        )

        # include_rejected=True
        buffer2 = service.generate_report(
            session_data=mock_session_data,
            export_type="equipment",
            include_rejected=True
        )

        # 둘 다 유효한 PDF여야 함
        buffer1.seek(0)
        buffer2.seek(0)
        assert buffer1.read(4) == b'%PDF'
        assert buffer2.read(4) == b'%PDF'

    def test_truncate_long_text(self, service):
        """긴 텍스트 잘라내기 테스트"""
        long_text = "A" * 100
        truncated = service._truncate(long_text, 20)
        assert len(truncated) == 20
        assert truncated.endswith("...")

    def test_truncate_short_text(self, service):
        """짧은 텍스트는 잘리지 않음"""
        short_text = "Short"
        result = service._truncate(short_text, 20)
        assert result == short_text

    def test_truncate_empty_text(self, service):
        """빈 텍스트 처리"""
        result = service._truncate("", 20)
        assert result == ""

    def test_truncate_none_text(self, service):
        """None 텍스트 처리"""
        result = service._truncate(None, 20)
        assert result == ""

    def test_format_status(self, service):
        """상태 포맷팅 테스트"""
        assert service._format_status("verified") == "Verified"
        assert service._format_status("pending") == "Pending"
        assert service._format_status("rejected") == "Rejected"
        assert service._format_status("auto_verified") == "Auto"
        assert service._format_status("unknown") == "unknown"

    def test_status_indicator(self, service):
        """상태 표시자 테스트"""
        assert "Complete" in service._status_indicator(10, 10)
        assert "Done" in service._status_indicator(9, 10)
        assert "Pending" in service._status_indicator(5, 10)
        assert "No Data" == service._status_indicator(0, 0)

    def test_checklist_status(self, service):
        """체크리스트 상태 테스트"""
        assert "FAIL" in service._checklist_status(8, 2, 10)
        assert "ALL PASS" == service._checklist_status(10, 0, 10)
        assert "In Progress" in service._checklist_status(5, 0, 10)
        assert "No Data" == service._checklist_status(0, 0, 0)

    def test_severity_indicator(self, service):
        """심각도 표시자 테스트"""
        assert service._severity_indicator([]) == "None"
        assert "CRITICAL" in service._severity_indicator([{"severity": "critical"}])
        assert "Major" in service._severity_indicator([{"severity": "major"}])
        assert "Minor" in service._severity_indicator([{"severity": "minor"}])

    def test_korean_project_name(self, service, mock_session_data):
        """한국어 프로젝트명 테스트"""
        # reportlab은 기본적으로 한국어 지원이 제한적
        # 하지만 ASCII로 변환하여 처리해야 함
        buffer = service.generate_report(
            session_data=mock_session_data,
            project_name="테스트 프로젝트",  # 한국어
            drawing_no="도면-001",
            export_type="all",
            include_rejected=False
        )

        assert isinstance(buffer, BytesIO)
        buffer.seek(0)
        # 에러 없이 생성되어야 함
        header = buffer.read(4)
        assert header == b'%PDF'


class TestExportRouterPDF:
    """Export Router PDF 엔드포인트 테스트"""

    @pytest.fixture
    def mock_session_service(self, mock_session_data):
        """Mock 세션 서비스"""
        class MockSessionService:
            def __init__(self, data):
                self.data = data

            def get_session(self, session_id):
                if session_id == "test-session":
                    return self.data
                return None

        return MockSessionService(mock_session_data)

    @pytest.fixture
    def mock_session_data(self):
        """테스트용 세션 데이터"""
        return {
            "pid_equipment": [
                {"tag": "P-101", "equipment_type": "Pump", "verification_status": "verified"}
            ],
            "pid_valves": [],
            "pid_checklist_items": [],
            "pid_deviations": []
        }

    # FastAPI TestClient 테스트는 별도 통합 테스트에서 수행
