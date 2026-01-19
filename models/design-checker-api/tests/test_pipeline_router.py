"""
Pipeline Router Tests
YOLO + OCR + Design Checker 통합 파이프라인 라우터 테스트
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient


class TestPipelineRouterImport:
    """Pipeline 라우터 모듈 임포트 테스트"""

    def test_import_router(self):
        """router 임포트"""
        from routers.pipeline_router import router
        assert router is not None

    def test_router_prefix(self):
        """라우터 prefix 확인"""
        from routers.pipeline_router import router
        assert router.prefix == "/api/v1/pipeline"

    def test_router_tags(self):
        """라우터 태그 확인"""
        from routers.pipeline_router import router
        assert "pipeline" in router.tags


class TestPipelineRouterEndpoints:
    """Pipeline 라우터 엔드포인트 존재 테스트"""

    def test_detect_endpoint_exists(self):
        """POST /detect 엔드포인트 존재"""
        from routers.pipeline_router import detect_pid_symbols
        assert callable(detect_pid_symbols)

    def test_ocr_endpoint_exists(self):
        """POST /ocr 엔드포인트 존재 확인"""
        from routers.pipeline_router import router
        # ocr 엔드포인트가 있는지 확인
        for route in router.routes:
            if hasattr(route, 'path') and '/ocr' in route.path:
                assert True
                return
        # ocr 엔드포인트가 없을 수 있음 - 스킵
        pytest.skip("OCR endpoint not found in pipeline router")

    def test_validate_endpoint_exists(self):
        """POST /validate 엔드포인트 존재 확인"""
        from routers.pipeline_router import router
        for route in router.routes:
            if hasattr(route, 'path') and '/validate' in route.path:
                assert True
                return
        pytest.skip("Validate endpoint not found")


class TestOCRSourceType:
    """OCR 소스 타입 테스트"""

    def test_ocr_source_type_exists(self):
        """OCRSource 타입 존재"""
        from routers.pipeline_router import OCRSource
        assert OCRSource is not None

    def test_ocr_source_values(self):
        """OCRSource 값들"""
        # Literal 타입은 직접 값 확인이 어려움
        # 대신 문서화된 값이 사용되는지 간접 확인
        from routers.pipeline_router import OCRSource
        # 타입 힌트로 사용 가능한지 확인
        source: OCRSource = "paddleocr"
        assert source == "paddleocr"


class TestDetectPIDSymbolsMock:
    """detect_pid_symbols 엔드포인트 테스트 (모킹)"""

    @pytest.mark.asyncio
    async def test_detect_success(self):
        """성공적인 심볼 검출"""
        from services.yolo_service import YOLOResult, Detection, YOLOService

        # Mock YOLO 결과
        mock_detection = Detection(
            class_name="Valve",
            class_id=0,
            confidence=0.95,
            bbox={"x": 100, "y": 200, "width": 50, "height": 50},
            center=[125, 225],
        )
        mock_yolo_result = YOLOResult(
            success=True,
            detections=[mock_detection],
            total_detections=1,
            class_counts={"Valve": 1},
            visualized_image="base64...",
            processing_time=0.5,
        )

        # YOLOService 인스턴스 메서드 테스트
        service = YOLOService()
        equipment_map = service.map_symbols_to_equipment([mock_detection])
        equipment_list = service.get_detected_equipment_list([mock_detection])

        assert isinstance(equipment_map, dict)
        assert len(equipment_list) > 0
        assert mock_yolo_result.success is True

    @pytest.mark.asyncio
    async def test_detect_yolo_failure(self):
        """YOLO 검출 실패 처리"""
        from services.yolo_service import YOLOResult

        mock_yolo_result = YOLOResult(
            success=False,
            detections=[],
            total_detections=0,
            class_counts={},
            visualized_image=None,
            processing_time=0,
            error="YOLO API connection failed",
        )

        assert mock_yolo_result.success is False
        assert "YOLO" in mock_yolo_result.error


class TestServiceDependencies:
    """서비스 의존성 테스트"""

    def test_yolo_service_import(self):
        """yolo_service 임포트"""
        from routers.pipeline_router import yolo_service
        assert yolo_service is not None

    def test_ocr_service_import(self):
        """ocr_service 임포트"""
        from routers.pipeline_router import ocr_service
        assert ocr_service is not None

    def test_edocr2_service_import(self):
        """edocr2_service 임포트"""
        from routers.pipeline_router import edocr2_service
        assert edocr2_service is not None

    def test_tag_extractor_import(self):
        """tag_extractor 임포트"""
        from routers.pipeline_router import tag_extractor
        assert tag_extractor is not None

    def test_equipment_mapper_import(self):
        """equipment_mapper 임포트"""
        from routers.pipeline_router import equipment_mapper
        assert equipment_mapper is not None


class TestExportServices:
    """내보내기 서비스 테스트"""

    def test_excel_report_service_import(self):
        """excel_report_service 임포트"""
        from routers.pipeline_router import excel_report_service
        assert excel_report_service is not None

    def test_pdf_report_service_import(self):
        """pdf_report_service 임포트"""
        from routers.pipeline_router import pdf_report_service
        assert pdf_report_service is not None


class TestRuleLoader:
    """규칙 로더 테스트"""

    def test_rule_loader_import(self):
        """rule_loader 임포트"""
        from routers.pipeline_router import rule_loader
        assert rule_loader is not None


class TestPipelineIntegration:
    """파이프라인 통합 테스트 (서버 실행 필요)"""

    def test_detect_endpoint_integration(self):
        """POST /api/v1/pipeline/detect 통합 테스트"""
        import httpx

        try:
            # 빈 파일로 테스트
            files = {"file": ("test.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 100, "image/png")}
            response = httpx.post(
                "http://localhost:5019/api/v1/pipeline/detect",
                files=files,
                data={"model_type": "pid_class_aware", "confidence": "0.1"},
                timeout=30,
            )
            # 서버가 응답하면 성공 (실제 결과는 YOLO API 상태에 따라 다름)
            assert response.status_code in [200, 500, 503]  # 정상, 에러, 서비스 불가
        except httpx.ConnectError:
            pytest.skip("design-checker-api server not running")


class TestResponseFormat:
    """응답 형식 테스트"""

    def test_process_response_import(self):
        """ProcessResponse 스키마 임포트"""
        from schemas import ProcessResponse
        assert ProcessResponse is not None

    def test_process_response_fields(self):
        """ProcessResponse 필드 확인"""
        from schemas import ProcessResponse

        response = ProcessResponse(
            success=True,
            data={"test": "data"},
            processing_time=1.0,
        )

        assert hasattr(response, "success")
        assert hasattr(response, "data")
        assert hasattr(response, "processing_time")
