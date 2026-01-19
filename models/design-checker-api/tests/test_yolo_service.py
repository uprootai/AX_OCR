"""
YOLO Service Tests
YOLO API 연동 서비스 테스트
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx


class TestYOLOServiceImport:
    """YOLO 서비스 모듈 임포트 테스트"""

    def test_import_yolo_service_module(self):
        """yolo_service 모듈 임포트"""
        from services import yolo_service
        assert yolo_service is not None

    def test_import_yolo_service_class(self):
        """YOLOService 클래스 임포트"""
        from services.yolo_service import YOLOService
        assert YOLOService is not None

    def test_import_detection_dataclass(self):
        """Detection 데이터클래스 임포트"""
        from services.yolo_service import Detection
        assert Detection is not None

    def test_import_yolo_result_dataclass(self):
        """YOLOResult 데이터클래스 임포트"""
        from services.yolo_service import YOLOResult
        assert YOLOResult is not None

    def test_singleton_instance(self):
        """싱글톤 인스턴스 확인"""
        from services.yolo_service import yolo_service, YOLOService
        assert isinstance(yolo_service, YOLOService)


class TestYOLOServiceInit:
    """YOLO 서비스 초기화 테스트"""

    def test_default_base_url(self):
        """기본 URL 확인"""
        from services.yolo_service import YOLOService, YOLO_API_URL
        service = YOLOService()
        assert service.base_url == YOLO_API_URL

    def test_custom_base_url(self):
        """커스텀 URL 설정"""
        from services.yolo_service import YOLOService
        service = YOLOService(base_url="http://custom:5005")
        assert service.base_url == "http://custom:5005"

    def test_timeout_setting(self):
        """타임아웃 설정 확인"""
        from services.yolo_service import YOLOService, YOLO_TIMEOUT
        service = YOLOService()
        assert service.timeout == YOLO_TIMEOUT


class TestDetectionDataclass:
    """Detection 데이터클래스 테스트"""

    def test_detection_creation(self):
        """Detection 생성"""
        from services.yolo_service import Detection

        det = Detection(
            class_name="Valve",
            class_id=0,
            confidence=0.95,
            bbox={"x": 100, "y": 200, "width": 50, "height": 50},
            center=[125, 225],
        )

        assert det.class_name == "Valve"
        assert det.class_id == 0
        assert det.confidence == 0.95
        assert det.bbox["x"] == 100
        assert det.center == [125, 225]


class TestYOLOResultDataclass:
    """YOLOResult 데이터클래스 테스트"""

    def test_yolo_result_success(self):
        """성공 결과 생성"""
        from services.yolo_service import YOLOResult, Detection

        det = Detection(
            class_name="Valve",
            class_id=0,
            confidence=0.95,
            bbox={"x": 100, "y": 200, "width": 50, "height": 50},
            center=[125, 225],
        )

        result = YOLOResult(
            success=True,
            detections=[det],
            total_detections=1,
            class_counts={"Valve": 1},
            visualized_image="base64...",
            processing_time=0.5,
        )

        assert result.success is True
        assert len(result.detections) == 1
        assert result.error is None

    def test_yolo_result_failure(self):
        """실패 결과 생성"""
        from services.yolo_service import YOLOResult

        result = YOLOResult(
            success=False,
            detections=[],
            total_detections=0,
            class_counts={},
            visualized_image=None,
            processing_time=0,
            error="Connection failed",
        )

        assert result.success is False
        assert result.error == "Connection failed"


class TestSymbolToEquipmentMapping:
    """심볼-장비 매핑 테스트"""

    def test_pid_symbol_to_equipment_exists(self):
        """매핑 딕셔너리 존재"""
        from services.yolo_service import PID_SYMBOL_TO_EQUIPMENT
        assert isinstance(PID_SYMBOL_TO_EQUIPMENT, dict)
        assert len(PID_SYMBOL_TO_EQUIPMENT) > 0

    def test_valve_mapping(self):
        """밸브 타입 매핑"""
        from services.yolo_service import PID_SYMBOL_TO_EQUIPMENT
        assert "Valve" in PID_SYMBOL_TO_EQUIPMENT
        assert "Valve Ball" in PID_SYMBOL_TO_EQUIPMENT
        assert "Control Valve" in PID_SYMBOL_TO_EQUIPMENT

    def test_esdv_mapping(self):
        """ESDV 매핑"""
        from services.yolo_service import PID_SYMBOL_TO_EQUIPMENT
        assert "ESDV Valve Ball" in PID_SYMBOL_TO_EQUIPMENT
        assert "ESDV" in PID_SYMBOL_TO_EQUIPMENT["ESDV Valve Ball"]

    def test_sensor_mapping(self):
        """센서 매핑"""
        from services.yolo_service import PID_SYMBOL_TO_EQUIPMENT
        assert "Sensor" in PID_SYMBOL_TO_EQUIPMENT
        assert "Ultrasonic Flow Meter" in PID_SYMBOL_TO_EQUIPMENT


class TestMapSymbolsToEquipment:
    """map_symbols_to_equipment 메서드 테스트"""

    def test_map_single_detection(self):
        """단일 검출 매핑"""
        from services.yolo_service import YOLOService, Detection

        service = YOLOService()
        det = Detection(
            class_name="Valve",
            class_id=0,
            confidence=0.95,
            bbox={"x": 100, "y": 200, "width": 50, "height": 50},
            center=[125, 225],
        )

        result = service.map_symbols_to_equipment([det])

        assert isinstance(result, dict)
        assert len(result) > 0  # Valve → ["Valve", "Manual Valve"]

    def test_map_multiple_detections(self):
        """다중 검출 매핑"""
        from services.yolo_service import YOLOService, Detection

        service = YOLOService()
        detections = [
            Detection(class_name="Valve", class_id=0, confidence=0.9,
                      bbox={"x": 100, "y": 100, "width": 50, "height": 50}, center=[125, 125]),
            Detection(class_name="Sensor", class_id=1, confidence=0.85,
                      bbox={"x": 200, "y": 200, "width": 30, "height": 30}, center=[215, 215]),
        ]

        result = service.map_symbols_to_equipment(detections)

        assert len(result) >= 2  # Valve 관련 + Sensor 관련

    def test_map_unknown_symbol(self):
        """알 수 없는 심볼 처리"""
        from services.yolo_service import YOLOService, Detection

        service = YOLOService()
        det = Detection(
            class_name="UnknownSymbol",
            class_id=99,
            confidence=0.8,
            bbox={"x": 0, "y": 0, "width": 10, "height": 10},
            center=[5, 5],
        )

        result = service.map_symbols_to_equipment([det])

        # 알 수 없는 심볼은 클래스명 그대로 사용
        assert "UnknownSymbol" in result


class TestGetDetectedEquipmentList:
    """get_detected_equipment_list 메서드 테스트"""

    def test_get_equipment_list(self):
        """장비 목록 추출"""
        from services.yolo_service import YOLOService, Detection

        service = YOLOService()
        detections = [
            Detection(class_name="Valve", class_id=0, confidence=0.9,
                      bbox={"x": 100, "y": 100, "width": 50, "height": 50}, center=[125, 125]),
            Detection(class_name="Valve Ball", class_id=1, confidence=0.85,
                      bbox={"x": 200, "y": 200, "width": 30, "height": 30}, center=[215, 215]),
        ]

        result = service.get_detected_equipment_list(detections)

        assert isinstance(result, list)
        assert len(result) > 0

    def test_filter_by_confidence(self):
        """신뢰도 필터링"""
        from services.yolo_service import YOLOService, Detection

        service = YOLOService()
        detections = [
            Detection(class_name="Valve", class_id=0, confidence=0.9,
                      bbox={"x": 100, "y": 100, "width": 50, "height": 50}, center=[125, 125]),
            Detection(class_name="Sensor", class_id=1, confidence=0.2,  # 낮은 신뢰도
                      bbox={"x": 200, "y": 200, "width": 30, "height": 30}, center=[215, 215]),
        ]

        result = service.get_detected_equipment_list(detections, min_confidence=0.3)

        # 낮은 신뢰도의 Sensor는 제외
        assert any("Valve" in eq for eq in result)

    def test_sorted_result(self):
        """결과 정렬 확인"""
        from services.yolo_service import YOLOService, Detection

        service = YOLOService()
        detections = [
            Detection(class_name="Sensor", class_id=1, confidence=0.9,
                      bbox={}, center=[]),
            Detection(class_name="Valve", class_id=0, confidence=0.9,
                      bbox={}, center=[]),
        ]

        result = service.get_detected_equipment_list(detections)

        # 정렬되어 있어야 함
        assert result == sorted(result)


class TestGenerateOCRTextsFromDetections:
    """generate_ocr_texts_from_detections 메서드 테스트"""

    def test_generate_ocr_texts(self):
        """OCR 텍스트 생성"""
        from services.yolo_service import YOLOService, Detection

        service = YOLOService()
        detections = [
            Detection(class_name="Valve", class_id=0, confidence=0.9,
                      bbox={}, center=[]),
        ]

        result = service.generate_ocr_texts_from_detections(detections)

        assert isinstance(result, list)
        assert "Valve" in result

    def test_unique_texts(self):
        """중복 제거 확인"""
        from services.yolo_service import YOLOService, Detection

        service = YOLOService()
        detections = [
            Detection(class_name="Valve", class_id=0, confidence=0.9, bbox={}, center=[]),
            Detection(class_name="Valve", class_id=0, confidence=0.85, bbox={}, center=[]),
        ]

        result = service.generate_ocr_texts_from_detections(detections)

        # 중복 제거됨
        assert len(result) == len(set(result))


class TestDetectPIDSymbolsAsync:
    """detect_pid_symbols 비동기 메서드 테스트"""

    @pytest.mark.asyncio
    async def test_detect_success_mock(self):
        """성공적인 검출 (모킹)"""
        from services.yolo_service import YOLOService

        service = YOLOService()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "processing_time": 0.5,
            "data": {
                "detections": [
                    {
                        "class_name": "Valve",
                        "class_id": 0,
                        "confidence": 0.95,
                        "bbox": {"x": 100, "y": 200, "width": 50, "height": 50},
                        "center": [125, 225],
                    }
                ],
                "total_detections": 1,
                "class_counts": {"Valve": 1},
            },
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await service.detect_pid_symbols(b"fake_image_data")

            assert result.success is True
            assert len(result.detections) == 1
            assert result.detections[0].class_name == "Valve"

    @pytest.mark.asyncio
    async def test_detect_api_error(self):
        """API 오류 처리"""
        from services.yolo_service import YOLOService

        service = YOLOService()

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await service.detect_pid_symbols(b"fake_image_data")

            assert result.success is False
            assert "500" in result.error

    @pytest.mark.asyncio
    async def test_detect_timeout(self):
        """타임아웃 처리"""
        from services.yolo_service import YOLOService

        service = YOLOService()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.side_effect = httpx.TimeoutException("Timeout")
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await service.detect_pid_symbols(b"fake_image_data")

            assert result.success is False
            assert "timeout" in result.error.lower()

    @pytest.mark.asyncio
    async def test_detect_exception(self):
        """일반 예외 처리"""
        from services.yolo_service import YOLOService

        service = YOLOService()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.side_effect = Exception("Connection refused")
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await service.detect_pid_symbols(b"fake_image_data")

            assert result.success is False
            assert result.error is not None
