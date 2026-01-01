"""
Executor 단위 테스트
모든 executor의 validate_parameters, get_input_schema, get_output_schema 테스트
"""
import pytest
from blueprintflow.executors.executor_registry import ExecutorRegistry


def create_executor(executor_type: str, parameters: dict):
    """Helper function to create executor with required arguments"""
    executor_class = ExecutorRegistry.get(executor_type)
    if executor_class is None:
        return None
    return executor_class(node_id="test", node_type=executor_type, parameters=parameters)


class TestExecutorValidation:
    """Executor validate_parameters 테스트"""

    def test_yolo_validate_valid_params(self):
        """YOLO: 유효한 파라미터 검증"""
        executor = create_executor("yolo", {
            "confidence": 0.5,
            "iou": 0.45,
            "visualize": True,
            "imgsz": 1280,
            "model_type": "engineering",
            "task": "detect",
            "use_sahi": False,
            "slice_height": 640,
            "slice_width": 640,
            "overlap_ratio": 0.2
        })
        is_valid, error = executor.validate_parameters()
        assert is_valid is True
        assert error is None

    def test_yolo_validate_invalid_confidence(self):
        """YOLO: 잘못된 confidence 값"""
        executor = create_executor("yolo", {"confidence": 1.5})  # > 1 이므로 무효
        is_valid, error = executor.validate_parameters()
        assert is_valid is False
        assert "confidence" in error.lower()

    def test_yolo_validate_invalid_iou(self):
        """YOLO: 잘못된 iou 값"""
        executor = create_executor("yolo", {"iou": -0.1})  # < 0 이므로 무효
        is_valid, error = executor.validate_parameters()
        assert is_valid is False
        assert "iou" in error.lower()

    def test_edocr2_validate_valid_params(self):
        """eDOCr2: 유효한 파라미터 검증"""
        executor = create_executor("edocr2", {"gdt_mode": "full", "visualize": True})
        is_valid, error = executor.validate_parameters()
        assert is_valid is True

    def test_edocr2_validate_with_empty_params(self):
        """eDOCr2: 빈 파라미터도 유효함 (기본값 사용)"""
        executor = create_executor("edocr2", {})
        is_valid, error = executor.validate_parameters()
        assert is_valid is True

    def test_skinmodel_validate_valid_params(self):
        """SkinModel: 유효한 파라미터 검증"""
        executor = create_executor("skinmodel", {"model_version": "v2", "include_visualization": True})
        is_valid, error = executor.validate_parameters()
        assert is_valid is True

    def test_paddleocr_validate_valid_params(self):
        """PaddleOCR: 유효한 파라미터 검증"""
        executor = create_executor("paddleocr", {"ocr_version": "PP-OCRv5", "lang": "korean", "visualize": True})
        is_valid, error = executor.validate_parameters()
        assert is_valid is True

    def test_tesseract_validate_valid_params(self):
        """Tesseract: 유효한 파라미터 검증"""
        executor = create_executor("tesseract", {"lang": "eng", "psm": "3"})
        is_valid, error = executor.validate_parameters()
        assert is_valid is True

    def test_trocr_validate_valid_params(self):
        """TrOCR: 유효한 파라미터 검증"""
        executor = create_executor("trocr", {"model_type": "printed", "max_length": 64})
        is_valid, error = executor.validate_parameters()
        assert is_valid is True

    def test_knowledge_validate_valid_params(self):
        """Knowledge: 유효한 파라미터 검증"""
        executor = create_executor("knowledge", {"search_mode": "hybrid", "graph_weight": 0.6, "top_k": 5})
        is_valid, error = executor.validate_parameters()
        assert is_valid is True

    def test_knowledge_validate_invalid_graph_weight(self):
        """Knowledge: 잘못된 graph_weight 값"""
        executor = create_executor("knowledge", {"search_mode": "hybrid", "graph_weight": 1.5})  # > 1
        is_valid, error = executor.validate_parameters()
        assert is_valid is False

    def test_esrgan_validate_valid_params(self):
        """ESRGAN: 유효한 파라미터 검증"""
        executor = create_executor("esrgan", {"scale": "4", "denoise_strength": 0.5})
        is_valid, error = executor.validate_parameters()
        assert is_valid is True

    def test_linedetector_validate_valid_params(self):
        """Line Detector: 유효한 파라미터 검증"""
        executor = create_executor("linedetector", {
            "method": "lsd",
            "merge_lines": True,
            "classify_types": True,
            "visualize": True
        })
        is_valid, error = executor.validate_parameters()
        assert is_valid is True

    def test_designchecker_validate_valid_params(self):
        """Design Checker: 유효한 파라미터 검증"""
        executor = create_executor("designchecker", {
            "categories": "all",
            "severity_threshold": "warning",
            "include_bwms": True
        })
        is_valid, error = executor.validate_parameters()
        assert is_valid is True

    def test_pidanalyzer_validate_valid_params(self):
        """PID Analyzer: 유효한 파라미터 검증"""
        executor = create_executor("pidanalyzer", {
            "generate_bom": True,
            "generate_valve_list": True,
            "visualize": True
        })
        is_valid, error = executor.validate_parameters()
        assert is_valid is True

    def test_gtcomparison_validate_valid_params(self):
        """GT Comparison: 유효한 파라미터 검증"""
        executor = create_executor("gtcomparison", {"iou_threshold": 0.5, "class_agnostic": False})
        is_valid, error = executor.validate_parameters()
        assert is_valid is True

    def test_gtcomparison_validate_invalid_iou(self):
        """GT Comparison: 잘못된 iou_threshold 값"""
        executor = create_executor("gtcomparison", {"iou_threshold": 1.5})  # > 1
        is_valid, error = executor.validate_parameters()
        assert is_valid is False

    def test_pdfexport_validate_valid_params(self):
        """PDF Export: 유효한 파라미터 검증"""
        executor = create_executor("pdfexport", {
            "export_type": "all",
            "project_name": "Test Project",
            "drawing_no": "DWG-001"
        })
        is_valid, error = executor.validate_parameters()
        assert is_valid is True

    def test_pdfexport_validate_invalid_export_type(self):
        """PDF Export: 잘못된 export_type 값"""
        executor = create_executor("pdfexport", {"export_type": "invalid_type"})
        is_valid, error = executor.validate_parameters()
        assert is_valid is False

    def test_excelexport_validate_valid_params(self):
        """Excel Export: 유효한 파라미터 검증"""
        executor = create_executor("excelexport", {
            "export_type": "all",
            "include_rejected": False
        })
        is_valid, error = executor.validate_parameters()
        assert is_valid is True

    def test_pidfeatures_validate_valid_params(self):
        """PID Features: 유효한 파라미터 검증"""
        executor = create_executor("pidfeatures", {
            "features": ["valve_signal", "equipment"],
            "product_type": "ECS",
            "confidence_threshold": 0.7
        })
        is_valid, error = executor.validate_parameters()
        assert is_valid is True

    def test_pidfeatures_validate_invalid_threshold(self):
        """PID Features: 잘못된 confidence_threshold 값"""
        executor = create_executor("pidfeatures", {"confidence_threshold": 1.5})  # > 1
        is_valid, error = executor.validate_parameters()
        assert is_valid is False

    def test_verificationqueue_validate_valid_params(self):
        """Verification Queue: 유효한 파라미터 검증"""
        executor = create_executor("verificationqueue", {
            "queue_filter": "all",
            "sort_by": "confidence_asc",
            "batch_size": 20,
            "auto_approve_threshold": 0.95
        })
        is_valid, error = executor.validate_parameters()
        assert is_valid is True

    def test_verificationqueue_validate_empty_params(self):
        """Verification Queue: 빈 파라미터도 유효함 (기본값 사용)"""
        executor = create_executor("verificationqueue", {})
        is_valid, error = executor.validate_parameters()
        assert is_valid is True


class TestExecutorSchemas:
    """Executor 스키마 테스트"""

    @pytest.mark.parametrize("executor_type", [
        "yolo", "edocr2", "skinmodel", "paddleocr", "tesseract",
        "trocr", "knowledge", "esrgan", "linedetector", "designchecker",
        "pidanalyzer", "gtcomparison", "pdfexport", "excelexport",
        "pidfeatures", "verificationqueue", "imageinput", "textinput",
        "if", "loop", "merge", "vl", "edgnet"
    ])
    def test_executor_has_input_schema(self, executor_type):
        """모든 executor는 입력 스키마를 반환해야 함"""
        executor = create_executor(executor_type, {})
        if executor is None:
            pytest.skip(f"Executor {executor_type} not registered")

        schema = executor.get_input_schema()
        assert isinstance(schema, dict)
        assert "type" in schema or "properties" in schema

    @pytest.mark.parametrize("executor_type", [
        "yolo", "edocr2", "skinmodel", "paddleocr", "tesseract",
        "trocr", "knowledge", "esrgan", "linedetector", "designchecker",
        "pidanalyzer", "gtcomparison", "pdfexport", "excelexport",
        "pidfeatures", "verificationqueue", "imageinput", "textinput",
        "if", "loop", "merge", "vl", "edgnet"
    ])
    def test_executor_has_output_schema(self, executor_type):
        """모든 executor는 출력 스키마를 반환해야 함"""
        executor = create_executor(executor_type, {})
        if executor is None:
            pytest.skip(f"Executor {executor_type} not registered")

        schema = executor.get_output_schema()
        assert isinstance(schema, dict)
        assert "type" in schema or "properties" in schema


class TestControlExecutors:
    """Control executor (if, loop, merge) 테스트"""

    def test_if_executor_valid_params(self):
        """IF Executor: 유효한 파라미터"""
        executor = create_executor("if", {
            "condition": {
                "field": "total_detections",
                "operator": ">",
                "value": 0
            }
        })
        is_valid, error = executor.validate_parameters()
        assert is_valid is True

    def test_if_executor_missing_condition(self):
        """IF Executor: condition 누락"""
        executor = create_executor("if", {})
        is_valid, error = executor.validate_parameters()
        assert is_valid is False

    def test_loop_executor_valid_params(self):
        """Loop Executor: 유효한 파라미터"""
        executor = create_executor("loop", {"max_iterations": 10, "break_condition": ""})
        is_valid, error = executor.validate_parameters()
        assert is_valid is True

    def test_merge_executor_valid_params(self):
        """Merge Executor: 유효한 파라미터"""
        executor = create_executor("merge", {"merge_strategy": "keep_all"})
        is_valid, error = executor.validate_parameters()
        assert is_valid is True

    def test_merge_executor_invalid_strategy(self):
        """Merge Executor: 잘못된 merge_strategy 값"""
        executor = create_executor("merge", {"merge_strategy": "invalid_strategy"})
        is_valid, error = executor.validate_parameters()
        assert is_valid is False


class TestInputExecutors:
    """Input executor (imageinput, textinput) 테스트"""

    def test_imageinput_executor_valid_params(self):
        """ImageInput Executor: 유효한 파라미터"""
        executor = create_executor("imageinput", {"input_mode": "upload"})
        is_valid, error = executor.validate_parameters()
        assert is_valid is True

    def test_textinput_executor_valid_params(self):
        """TextInput Executor: 유효한 파라미터"""
        executor = create_executor("textinput", {"text": "Test input text"})
        is_valid, error = executor.validate_parameters()
        assert is_valid is True


class TestOCRExecutors:
    """OCR executor 테스트"""

    def test_doctr_validate_valid_params(self):
        """DocTR: 유효한 파라미터 검증"""
        executor = create_executor("doctr", {
            "det_arch": "db_resnet50",
            "reco_arch": "crnn_vgg16_bn",
            "visualize": True
        })
        if executor is None:
            pytest.skip("DocTR executor not registered")
        is_valid, error = executor.validate_parameters()
        assert is_valid is True

    def test_easyocr_validate_valid_params(self):
        """EasyOCR: 유효한 파라미터 검증"""
        executor = create_executor("easyocr", {"languages": "ko,en", "detail": True})
        if executor is None:
            pytest.skip("EasyOCR executor not registered")
        is_valid, error = executor.validate_parameters()
        assert is_valid is True

    def test_suryaocr_validate_valid_params(self):
        """Surya OCR: 유효한 파라미터 검증"""
        executor = create_executor("suryaocr", {"languages": "ko,en", "detect_layout": False})
        if executor is None:
            pytest.skip("Surya OCR executor not registered")
        is_valid, error = executor.validate_parameters()
        assert is_valid is True

    def test_ocr_ensemble_validate_valid_params(self):
        """OCR Ensemble: 유효한 파라미터 검증"""
        executor = create_executor("ocr-ensemble", {
            "edocr2_weight": 0.4,
            "paddleocr_weight": 0.35,
            "tesseract_weight": 0.15,
            "trocr_weight": 0.10
        })
        if executor is None:
            pytest.skip("OCR Ensemble executor not registered")
        is_valid, error = executor.validate_parameters()
        assert is_valid is True


class TestExecutorInstantiation:
    """Executor 인스턴스화 테스트"""

    @pytest.mark.parametrize("executor_type", [
        "yolo", "edocr2", "skinmodel", "paddleocr", "tesseract",
        "trocr", "knowledge", "esrgan", "linedetector", "designchecker",
        "pidanalyzer", "imageinput", "textinput", "if", "loop", "merge",
        "vl", "edgnet", "gtcomparison", "pdfexport", "excelexport",
        "pidfeatures", "verificationqueue"
    ])
    def test_executor_can_be_instantiated(self, executor_type):
        """모든 등록된 executor는 인스턴스화 가능해야 함"""
        executor = create_executor(executor_type, {})
        if executor is None:
            pytest.skip(f"Executor {executor_type} not registered")

        assert executor is not None
        assert executor.node_id == "test"

    @pytest.mark.parametrize("executor_type", [
        "yolo", "edocr2", "skinmodel", "paddleocr", "tesseract",
        "trocr", "knowledge", "esrgan", "linedetector", "designchecker",
        "pidanalyzer", "imageinput", "textinput", "if", "loop", "merge",
        "vl", "edgnet", "gtcomparison", "pdfexport", "excelexport",
        "pidfeatures", "verificationqueue"
    ])
    def test_executor_has_execute_method(self, executor_type):
        """모든 executor는 execute 메서드가 있어야 함"""
        executor = create_executor(executor_type, {})
        if executor is None:
            pytest.skip(f"Executor {executor_type} not registered")

        assert hasattr(executor, "execute")
        assert callable(executor.execute)
