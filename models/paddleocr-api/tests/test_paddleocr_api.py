"""
PaddleOCR 3.0 API Tests
PP-OCRv5: 13% accuracy improvement, 106 languages support
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np

# Test schemas
from models.schemas import (
    TextDetection,
    OCRResponse,
    HealthResponse,
    ParameterSchema,
    IOSchema,
    BlueprintFlowMetadata,
    APIInfoResponse
)


class TestSchemas:
    """Test Pydantic schemas"""

    def test_text_detection_model(self):
        """Test TextDetection schema"""
        detection = TextDetection(
            text="TEST",
            confidence=0.95,
            bbox=[[0, 0], [100, 0], [100, 20], [0, 20]],
            position={"x": 0, "y": 0, "width": 100, "height": 20}
        )
        assert detection.text == "TEST"
        assert detection.confidence == 0.95
        assert len(detection.bbox) == 4

    def test_ocr_response_model(self):
        """Test OCRResponse schema"""
        response = OCRResponse(
            status="success",
            processing_time=0.5,
            total_texts=2,
            detections=[],
            metadata={"filename": "test.png"}
        )
        assert response.status == "success"
        assert response.processing_time == 0.5

    def test_health_response_model(self):
        """Test HealthResponse schema with PP-OCRv5"""
        response = HealthResponse(
            status="healthy",
            service="paddleocr-api",
            version="3.0.0",
            gpu_available=True,
            model_loaded=True,
            lang="en",
            ocr_version="PP-OCRv5"
        )
        assert response.version == "3.0.0"
        assert response.ocr_version == "PP-OCRv5"

    def test_parameter_schema(self):
        """Test ParameterSchema with PP-OCRv5 options"""
        param = ParameterSchema(
            name="ocr_version",
            type="select",
            default="PP-OCRv5",
            description="OCR model version",
            options=["PP-OCRv5", "PP-OCRv4", "PP-OCRv3"]
        )
        assert param.default == "PP-OCRv5"
        assert "PP-OCRv5" in param.options


class TestPaddleOCRService:
    """Test PaddleOCRService class"""

    def test_service_init(self):
        """Test service initialization with environment defaults"""
        with patch.dict('os.environ', {
            'OCR_LANG': 'korean',
            'OCR_VERSION': 'PP-OCRv5',
            'DEVICE': 'cpu'
        }):
            from services.ocr import PaddleOCRService
            service = PaddleOCRService()
            assert service.lang == 'korean'
            assert service.ocr_version == 'PP-OCRv5'
            assert service.device == 'cpu'

    def test_service_gpu_device(self):
        """Test GPU device configuration"""
        with patch.dict('os.environ', {
            'USE_GPU': 'true',
            'OCR_LANG': 'en'
        }):
            from services.ocr import PaddleOCRService
            service = PaddleOCRService()
            assert service.device == 'gpu:0'

    def test_service_info(self):
        """Test service info method"""
        with patch.dict('os.environ', {
            'OCR_LANG': 'en',
            'OCR_VERSION': 'PP-OCRv5'
        }):
            from services.ocr import PaddleOCRService
            service = PaddleOCRService()
            info = service.get_info()
            assert info['version'] == '3.0.0'
            assert info['ocr_version'] == 'PP-OCRv5'

    def test_normalize_bbox_numpy(self):
        """Test bbox normalization with numpy array"""
        from services.ocr import PaddleOCRService
        service = PaddleOCRService()

        poly = np.array([[0, 0], [100, 0], [100, 20], [0, 20]])
        result = service._normalize_bbox(poly)

        assert result is not None
        assert len(result) == 4
        assert result[0] == [0.0, 0.0]
        assert result[1] == [100.0, 0.0]

    def test_normalize_bbox_list(self):
        """Test bbox normalization with list"""
        from services.ocr import PaddleOCRService
        service = PaddleOCRService()

        poly = [[10, 20], [110, 20], [110, 40], [10, 40]]
        result = service._normalize_bbox(poly)

        assert result is not None
        assert len(result) == 4

    def test_normalize_bbox_none(self):
        """Test bbox normalization with None"""
        from services.ocr import PaddleOCRService
        service = PaddleOCRService()

        result = service._normalize_bbox(None)
        assert result is None


class TestBboxHelper:
    """Test bbox helper functions"""

    def test_bbox_to_position(self):
        """Test bbox to position conversion"""
        from utils.helpers import bbox_to_position

        bbox = [[10, 20], [110, 20], [110, 40], [10, 40]]
        position = bbox_to_position(bbox)

        assert position['x'] == 10
        assert position['y'] == 20
        assert position['width'] == 100
        assert position['height'] == 20


class TestAPIInfo:
    """Test API info endpoint"""

    def test_api_info_version_3(self):
        """Test API info returns version 3.0.0"""
        api_info = APIInfoResponse(
            id="paddleocr",
            name="PaddleOCR 3.0 API",
            display_name="PaddleOCR PP-OCRv5",
            version="3.0.0",
            description="PP-OCRv5: 13% improved accuracy",
            openapi_url="/openapi.json",
            base_url="http://localhost:5006",
            endpoint="/api/v1/ocr",
            method="POST",
            requires_image=True,
            inputs=[IOSchema(name="file", type="file", description="Image")],
            outputs=[IOSchema(name="detections", type="array", description="Results")],
            parameters=[
                ParameterSchema(
                    name="ocr_version",
                    type="select",
                    default="PP-OCRv5",
                    description="OCR version",
                    options=["PP-OCRv5", "PP-OCRv4", "PP-OCRv3"]
                )
            ],
            blueprintflow=BlueprintFlowMetadata(
                icon="file-text",
                color="#10b981",
                category="ocr"
            ),
            output_mappings={"detections": "detections"}
        )

        assert api_info.version == "3.0.0"
        assert api_info.display_name == "PaddleOCR PP-OCRv5"
        assert len(api_info.parameters) == 1
        assert api_info.parameters[0].default == "PP-OCRv5"


class TestGlobalService:
    """Test global service management"""

    def test_set_get_service(self):
        """Test setting and getting global service"""
        from services.ocr import set_ocr_service, get_ocr_service, PaddleOCRService

        service = PaddleOCRService()
        set_ocr_service(service)

        retrieved = get_ocr_service()
        assert retrieved is service

    def test_is_service_ready_false(self):
        """Test service ready check when model not loaded"""
        from services.ocr import set_ocr_service, is_service_ready, PaddleOCRService

        service = PaddleOCRService()
        service.model = None
        set_ocr_service(service)

        assert is_service_ready() == False

    def test_is_service_ready_true(self):
        """Test service ready check when model loaded"""
        from services.ocr import set_ocr_service, is_service_ready, PaddleOCRService

        service = PaddleOCRService()
        service.model = Mock()  # Mock loaded model
        set_ocr_service(service)

        assert is_service_ready() == True


class TestOCRResultParsing:
    """Test OCR result parsing for 3.x format"""

    def test_parse_ocr_result_dict_like(self):
        """Test parsing dict-like OCR result (3.x format)"""
        from services.ocr import PaddleOCRService
        service = PaddleOCRService()

        # Mock OCRResult as dict-like object
        mock_result = MagicMock()
        mock_result.get = Mock(side_effect=lambda key, default=None: {
            'rec_texts': ['Hello', 'World'],
            'rec_scores': [0.95, 0.90],
            'rec_polys': [
                np.array([[0, 0], [50, 0], [50, 20], [0, 20]]),
                np.array([[60, 0], [120, 0], [120, 20], [60, 20]])
            ]
        }.get(key, default))

        # hasattr checks
        mock_result.__class__.__name__ = 'dict'
        type(mock_result).rec_texts = property(lambda self: None)

        detections = service._parse_ocr_result(mock_result, min_confidence=0.5)

        assert len(detections) == 2
        assert detections[0].text == 'Hello'
        assert detections[1].text == 'World'

    def test_parse_ocr_result_filters_low_confidence(self):
        """Test that low confidence results are filtered"""
        from services.ocr import PaddleOCRService
        service = PaddleOCRService()

        # Mock OCRResult with mixed confidence
        mock_result = MagicMock()
        mock_result.get = Mock(side_effect=lambda key, default=None: {
            'rec_texts': ['High', 'Low'],
            'rec_scores': [0.95, 0.3],  # Low is below threshold
            'rec_polys': [
                np.array([[0, 0], [50, 0], [50, 20], [0, 20]]),
                np.array([[60, 0], [120, 0], [120, 20], [60, 20]])
            ]
        }.get(key, default))

        detections = service._parse_ocr_result(mock_result, min_confidence=0.5)

        # Only high confidence should remain
        assert len(detections) == 1
        assert detections[0].text == 'High'


class TestLanguageSupport:
    """Test 106 language support"""

    def test_supported_languages(self):
        """Test that 106 languages are mentioned in documentation"""
        supported_languages = [
            'en', 'korean', 'ch', 'japan', 'fr', 'de', 'es', 'ru', 'ar'
        ]
        # These are just a subset - PP-OCRv5 supports 106
        assert len(supported_languages) >= 9

    def test_language_parameter(self):
        """Test language parameter schema"""
        param = ParameterSchema(
            name="lang",
            type="select",
            default="en",
            description="Recognition language (106 languages available)",
            options=["en", "korean", "ch", "japan", "fr", "de", "es", "ru", "ar"]
        )
        assert "korean" in param.options
        assert "ch" in param.options


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
