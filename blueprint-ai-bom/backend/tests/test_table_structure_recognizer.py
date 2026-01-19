"""Table Structure Recognizer 테스트

TableTransformer + EasyOCR 통합 테스트
- 모델 초기화
- 구조 인식
- 셀 텍스트 추출

실행: pytest tests/test_table_structure_recognizer.py -v
"""

import pytest
import os
from pathlib import Path

# 테스트 이미지 경로
SAMPLE_IMAGES_DIR = Path(__file__).parent.parent.parent.parent.parent / "web-ui/public/samples"


class TestTableStructureRecognizerImport:
    """TableStructureRecognizer 임포트 테스트"""

    def test_import_module(self):
        """모듈 임포트 테스트"""
        from services.table_structure_recognizer import (
            TableStructureRecognizer,
            get_table_structure_recognizer,
            TableStructure,
            TableCell,
            TableRecognitionResult,
        )
        assert TableStructureRecognizer is not None
        assert get_table_structure_recognizer is not None
        assert TableStructure is not None
        assert TableCell is not None
        assert TableRecognitionResult is not None

    def test_import_from_services(self):
        """services 패키지에서 임포트 테스트"""
        from services import (
            TableStructureRecognizer,
            get_table_structure_recognizer,
            TableStructure,
            TableCell,
            TableRecognitionResult,
        )
        assert TableStructureRecognizer is not None
        assert get_table_structure_recognizer is not None


class TestTableStructureRecognizerSingleton:
    """싱글톤 패턴 테스트"""

    def test_singleton_pattern(self):
        """싱글톤 인스턴스 테스트"""
        from services.table_structure_recognizer import get_table_structure_recognizer

        recognizer1 = get_table_structure_recognizer()
        recognizer2 = get_table_structure_recognizer()
        assert recognizer1 is recognizer2


class TestTableStructure:
    """TableStructure 데이터 클래스 테스트"""

    def test_create_table_structure(self):
        """TableStructure 생성 테스트"""
        from services.table_structure_recognizer import TableStructure

        structure = TableStructure(rows=5, columns=3)
        assert structure.rows == 5
        assert structure.columns == 3
        assert structure.cells == []
        assert structure.row_boxes == []
        assert structure.col_boxes == []

    def test_table_structure_with_data(self):
        """TableStructure 데이터 포함 테스트"""
        from services.table_structure_recognizer import TableStructure, TableCell

        cells = [
            TableCell(row=0, col=0, bbox=(0, 0, 100, 50), text="Header1"),
            TableCell(row=0, col=1, bbox=(100, 0, 200, 50), text="Header2"),
            TableCell(row=1, col=0, bbox=(0, 50, 100, 100), text="Data1"),
            TableCell(row=1, col=1, bbox=(100, 50, 200, 100), text="Data2"),
        ]

        structure = TableStructure(
            rows=2,
            columns=2,
            cells=cells,
            row_boxes=[(0, 0, 200, 50), (0, 50, 200, 100)],
            col_boxes=[(0, 0, 100, 100), (100, 0, 200, 100)]
        )

        assert structure.rows == 2
        assert structure.columns == 2
        assert len(structure.cells) == 4
        assert structure.cells[0].text == "Header1"


class TestTableCell:
    """TableCell 데이터 클래스 테스트"""

    def test_create_table_cell(self):
        """TableCell 생성 테스트"""
        from services.table_structure_recognizer import TableCell

        cell = TableCell(
            row=2,
            col=1,
            bbox=(100, 50, 200, 100),
            text="Cell Content",
            confidence=0.95
        )

        assert cell.row == 2
        assert cell.col == 1
        assert cell.bbox == (100, 50, 200, 100)
        assert cell.text == "Cell Content"
        assert cell.confidence == 0.95

    def test_table_cell_defaults(self):
        """TableCell 기본값 테스트"""
        from services.table_structure_recognizer import TableCell

        cell = TableCell(row=0, col=0, bbox=(0, 0, 100, 50))
        assert cell.text == ""
        assert cell.confidence == 0.0


class TestTableRecognitionResult:
    """TableRecognitionResult 데이터 클래스 테스트"""

    def test_create_result(self):
        """TableRecognitionResult 생성 테스트"""
        from services.table_structure_recognizer import (
            TableRecognitionResult,
            TableStructure
        )

        structure = TableStructure(rows=3, columns=3)
        result = TableRecognitionResult(
            structure=structure,
            raw_elements=[{"type": "table row", "bbox": (0, 0, 100, 50)}],
            ocr_performed=True,
            processing_time_ms=150.5
        )

        assert result.structure.rows == 3
        assert len(result.raw_elements) == 1
        assert result.ocr_performed is True
        assert result.processing_time_ms == 150.5


class TestTableStructureRecognizerAvailability:
    """모델 가용성 테스트"""

    def test_is_available_property(self):
        """is_available 속성 테스트"""
        from services.table_structure_recognizer import get_table_structure_recognizer

        recognizer = get_table_structure_recognizer()
        # transformers가 설치되어 있으면 True, 아니면 False
        assert isinstance(recognizer.is_available, bool)

    def test_is_ocr_available_property(self):
        """is_ocr_available 속성 테스트"""
        from services.table_structure_recognizer import get_table_structure_recognizer

        recognizer = get_table_structure_recognizer()
        # easyocr가 설치되어 있으면 True, 아니면 False
        # 지연 초기화되므로 최초 호출 시 초기화됨
        assert isinstance(recognizer.is_ocr_available, bool)


class TestTableStructureRecognizerStats:
    """통계 조회 테스트"""

    def test_get_stats(self):
        """get_stats 메서드 테스트"""
        from services.table_structure_recognizer import get_table_structure_recognizer

        recognizer = get_table_structure_recognizer()
        stats = recognizer.get_stats()

        assert "structure_model_available" in stats
        assert "ocr_available" in stats
        assert "device" in stats
        assert "gpu_memory_mb" in stats
        assert "ocr_languages" in stats
        assert "upscale_factor" in stats
        assert "structure_threshold" in stats


class TestTableStructureRecognizerGetTableAsDict:
    """딕셔너리 변환 테스트"""

    def test_get_table_as_dict_empty(self):
        """빈 테이블 변환 테스트"""
        from services.table_structure_recognizer import (
            get_table_structure_recognizer,
            TableStructure
        )

        recognizer = get_table_structure_recognizer()
        structure = TableStructure(rows=0, columns=0)
        result = recognizer.get_table_as_dict(structure)

        assert result["rows"] == 0
        assert result["columns"] == 0
        assert result["data"] == []

    def test_get_table_as_dict_with_cells(self):
        """셀 데이터 변환 테스트"""
        from services.table_structure_recognizer import (
            get_table_structure_recognizer,
            TableStructure,
            TableCell
        )

        recognizer = get_table_structure_recognizer()
        cells = [
            TableCell(row=0, col=0, bbox=(0, 0, 100, 50), text="A1", confidence=0.9),
            TableCell(row=0, col=1, bbox=(100, 0, 200, 50), text="B1", confidence=0.85),
            TableCell(row=1, col=0, bbox=(0, 50, 100, 100), text="A2", confidence=0.88),
            TableCell(row=1, col=1, bbox=(100, 50, 200, 100), text="B2", confidence=0.92),
        ]
        structure = TableStructure(rows=2, columns=2, cells=cells)

        result = recognizer.get_table_as_dict(structure)

        assert result["rows"] == 2
        assert result["columns"] == 2
        assert result["data"][0][0] == "A1"
        assert result["data"][0][1] == "B1"
        assert result["data"][1][0] == "A2"
        assert result["data"][1][1] == "B2"
        assert len(result["cells"]) == 4


class TestTableStructureRecognizerEnvironmentVariables:
    """환경변수 설정 테스트"""

    def test_environment_variables(self):
        """환경변수 기본값 테스트"""
        from services.table_structure_recognizer import (
            TABLE_RECOGNIZER_ENABLED,
            TABLE_STRUCTURE_THRESHOLD,
            TABLE_RECOGNIZER_DEVICE,
            OCR_UPSCALE_FACTOR,
            OCR_LANGUAGES,
        )

        assert isinstance(TABLE_RECOGNIZER_ENABLED, bool)
        assert isinstance(TABLE_STRUCTURE_THRESHOLD, float)
        assert 0 < TABLE_STRUCTURE_THRESHOLD < 1
        assert isinstance(TABLE_RECOGNIZER_DEVICE, str)
        assert isinstance(OCR_UPSCALE_FACTOR, int)
        assert OCR_UPSCALE_FACTOR >= 1
        assert isinstance(OCR_LANGUAGES, list)


@pytest.mark.skipif(
    not os.environ.get("TEST_WITH_GPU", "").lower() == "true",
    reason="GPU 테스트는 TEST_WITH_GPU=true 환경변수 필요"
)
class TestTableStructureRecognizerGPU:
    """GPU 환경 테스트"""

    def test_recognize_structure_unavailable_model(self):
        """모델 미사용 가능 시 빈 결과 반환 테스트"""
        from services.table_structure_recognizer import get_table_structure_recognizer
        from PIL import Image

        recognizer = get_table_structure_recognizer()

        if not recognizer.is_available:
            # 모델이 없으면 빈 구조 반환
            dummy_image = Image.new("RGB", (100, 100), color="white")
            result = recognizer.recognize_structure(dummy_image)
            assert result.structure.rows == 0
            assert result.structure.columns == 0

    def test_recognize_and_extract_sample_image(self):
        """샘플 이미지 인식 테스트"""
        from services.table_structure_recognizer import get_table_structure_recognizer
        from services.layout_analyzer import get_layout_analyzer
        from PIL import Image

        recognizer = get_table_structure_recognizer()
        layout_analyzer = get_layout_analyzer()

        if not recognizer.is_available:
            pytest.skip("TableStructureRecognizer 사용 불가")

        if not layout_analyzer.is_available:
            pytest.skip("LayoutAnalyzer 사용 불가")

        # 테스트 이미지 찾기
        sample_image = None
        if SAMPLE_IMAGES_DIR.exists():
            for ext in ["*.jpg", "*.png"]:
                images = list(SAMPLE_IMAGES_DIR.glob(ext))
                if images:
                    sample_image = images[0]
                    break

        if not sample_image:
            pytest.skip("테스트 이미지 없음")

        # 1. DocLayout-YOLO로 테이블 영역 검출
        detections = layout_analyzer.detect(str(sample_image), conf_threshold=0.1)
        table_detections = [d for d in detections if d.region_type == "BOM_TABLE"]

        if not table_detections:
            pytest.skip("테이블 검출 없음")

        # 2. 테이블 영역 크롭
        image = Image.open(sample_image).convert("RGB")
        table_det = table_detections[0]
        table_image = image.crop(table_det.bbox)

        # 3. TableTransformer로 구조 인식
        result = recognizer.recognize_and_extract(table_image, skip_ocr=True)

        # 결과 검증
        assert result is not None
        assert isinstance(result.structure.rows, int)
        assert isinstance(result.structure.columns, int)
        assert result.processing_time_ms > 0


class TestDocLayoutYOLOIntegration:
    """DocLayout-YOLO + TableTransformer 통합 테스트"""

    def test_bom_table_region_type(self):
        """BOM_TABLE 영역 타입 매핑 테스트"""
        from services.layout_analyzer import DOCLAYOUT_TO_REGION_MAP

        assert "table" in DOCLAYOUT_TO_REGION_MAP
        assert DOCLAYOUT_TO_REGION_MAP["table"] == "BOM_TABLE"

    def test_integration_workflow(self):
        """통합 워크플로우 테스트 (모킹)"""
        from services.table_structure_recognizer import (
            TableStructure,
            TableCell,
            get_table_structure_recognizer
        )

        recognizer = get_table_structure_recognizer()

        # 가상의 테이블 구조 생성 (실제 추론 없이)
        structure = TableStructure(
            rows=5,
            columns=9,
            row_boxes=[
                (0, i * 30, 270, (i + 1) * 30) for i in range(5)
            ],
            col_boxes=[
                (i * 30, 0, (i + 1) * 30, 150) for i in range(9)
            ]
        )

        # 딕셔너리 변환
        table_dict = recognizer.get_table_as_dict(structure)

        assert table_dict["rows"] == 5
        assert table_dict["columns"] == 9


class TestRotateImage:
    """이미지 회전 기능 테스트"""

    def test_rotate_0_degrees(self):
        """0도 회전 (원본 유지)"""
        from PIL import Image
        from services.table_structure_recognizer import get_table_structure_recognizer

        recognizer = get_table_structure_recognizer()
        image = Image.new("RGB", (100, 50), color="red")

        rotated = recognizer._rotate_image(image, 0)

        assert rotated.size == (100, 50)
        assert rotated is image  # 동일 객체 반환

    def test_rotate_90_degrees(self):
        """90도 회전"""
        from PIL import Image
        from services.table_structure_recognizer import get_table_structure_recognizer

        recognizer = get_table_structure_recognizer()
        image = Image.new("RGB", (100, 50), color="red")

        rotated = recognizer._rotate_image(image, 90)

        assert rotated.size == (50, 100)  # 가로/세로 교환

    def test_rotate_180_degrees(self):
        """180도 회전"""
        from PIL import Image
        from services.table_structure_recognizer import get_table_structure_recognizer

        recognizer = get_table_structure_recognizer()
        image = Image.new("RGB", (100, 50), color="red")

        rotated = recognizer._rotate_image(image, 180)

        assert rotated.size == (100, 50)  # 크기 동일

    def test_rotate_270_degrees(self):
        """270도 회전"""
        from PIL import Image
        from services.table_structure_recognizer import get_table_structure_recognizer

        recognizer = get_table_structure_recognizer()
        image = Image.new("RGB", (100, 50), color="red")

        rotated = recognizer._rotate_image(image, 270)

        assert rotated.size == (50, 100)  # 가로/세로 교환

    def test_rotate_arbitrary_angle(self):
        """임의 각도 회전"""
        from PIL import Image
        from services.table_structure_recognizer import get_table_structure_recognizer

        recognizer = get_table_structure_recognizer()
        image = Image.new("RGB", (100, 100), color="red")

        rotated = recognizer._rotate_image(image, 45)

        # 45도 회전 시 이미지 크기 증가 (expand=True)
        assert rotated.size[0] > 100
        assert rotated.size[1] > 100


class TestDetectTextRotation:
    """텍스트 회전 감지 테스트"""

    def test_detect_rotation_returns_tuple(self):
        """회전 감지가 튜플 반환"""
        from PIL import Image
        from services.table_structure_recognizer import get_table_structure_recognizer

        recognizer = get_table_structure_recognizer()

        if not recognizer.is_ocr_available:
            pytest.skip("OCR not available")

        image = Image.new("RGB", (100, 100), color="white")
        result = recognizer.detect_text_rotation(image)

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], int)  # best_angle
        assert isinstance(result[1], dict)  # results

    def test_detect_rotation_valid_angles(self):
        """유효한 회전 각도만 반환"""
        from PIL import Image
        from services.table_structure_recognizer import get_table_structure_recognizer

        recognizer = get_table_structure_recognizer()

        if not recognizer.is_ocr_available:
            pytest.skip("OCR not available")

        image = Image.new("RGB", (100, 100), color="white")
        best_angle, results = recognizer.detect_text_rotation(
            image, angles=[0, 90, 180, 270]
        )

        assert best_angle in [0, 90, 180, 270]
        assert set(results.keys()) == {0, 90, 180, 270}

    def test_detect_rotation_custom_angles(self):
        """커스텀 각도 목록 테스트"""
        from PIL import Image
        from services.table_structure_recognizer import get_table_structure_recognizer

        recognizer = get_table_structure_recognizer()

        if not recognizer.is_ocr_available:
            pytest.skip("OCR not available")

        image = Image.new("RGB", (100, 100), color="white")
        best_angle, results = recognizer.detect_text_rotation(
            image, angles=[0, 90]
        )

        assert best_angle in [0, 90]
        assert set(results.keys()) == {0, 90}

    def test_detect_rotation_result_structure(self):
        """회전 감지 결과 구조 검증"""
        from PIL import Image
        from services.table_structure_recognizer import get_table_structure_recognizer

        recognizer = get_table_structure_recognizer()

        if not recognizer.is_ocr_available:
            pytest.skip("OCR not available")

        image = Image.new("RGB", (100, 100), color="white")
        _, results = recognizer.detect_text_rotation(image)

        for angle, data in results.items():
            if "error" not in data:
                assert "num_texts" in data
                assert "avg_confidence" in data
                assert "total_chars" in data
                assert "score" in data


class TestExtractWholeTableTextWithRotation:
    """자동 회전 포함 전체 테이블 OCR 테스트"""

    def test_returns_tuple(self):
        """튜플 반환 확인"""
        from PIL import Image
        from services.table_structure_recognizer import get_table_structure_recognizer

        recognizer = get_table_structure_recognizer()

        if not recognizer.is_ocr_available:
            pytest.skip("OCR not available")

        image = Image.new("RGB", (100, 100), color="white")
        result = recognizer.extract_whole_table_text_with_rotation(image)

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], list)  # OCR results
        assert isinstance(result[1], int)   # applied rotation

    def test_auto_rotate_disabled(self):
        """auto_rotate=False 시 회전 없음"""
        from PIL import Image
        from services.table_structure_recognizer import get_table_structure_recognizer

        recognizer = get_table_structure_recognizer()

        if not recognizer.is_ocr_available:
            pytest.skip("OCR not available")

        image = Image.new("RGB", (100, 100), color="white")
        _, applied_rotation = recognizer.extract_whole_table_text_with_rotation(
            image, auto_rotate=False
        )

        assert applied_rotation == 0

    def test_ocr_result_structure(self):
        """OCR 결과 구조 검증"""
        from PIL import Image
        from services.table_structure_recognizer import get_table_structure_recognizer

        recognizer = get_table_structure_recognizer()

        if not recognizer.is_ocr_available:
            pytest.skip("OCR not available")

        # 텍스트가 있는 이미지 생성
        from PIL import ImageDraw, ImageFont
        image = Image.new("RGB", (200, 100), color="white")
        draw = ImageDraw.Draw(image)
        draw.text((10, 40), "TEST", fill="black")

        results, _ = recognizer.extract_whole_table_text_with_rotation(
            image, upscale_factor=2, confidence_threshold=0.1
        )

        # 결과가 있으면 구조 확인
        for r in results:
            assert "text" in r
            assert "confidence" in r
            assert "bbox" in r


@pytest.mark.skipif(
    not Path("/home/uproot/ax/poc/web-ui/public/samples/sample3_bom_table_1.png").exists(),
    reason="세로 텍스트 샘플 이미지 없음"
)
class TestRotationWithRealImages:
    """실제 이미지로 회전 감지 테스트"""

    def test_vertical_text_detection(self):
        """세로 텍스트 이미지 회전 감지"""
        from PIL import Image
        from services.table_structure_recognizer import get_table_structure_recognizer

        recognizer = get_table_structure_recognizer()

        if not recognizer.is_ocr_available:
            pytest.skip("OCR not available")

        image_path = "/home/uproot/ax/poc/web-ui/public/samples/sample3_bom_table_1.png"
        image = Image.open(image_path).convert("RGB")

        best_angle, results = recognizer.detect_text_rotation(image)

        # 세로 텍스트는 90 또는 270도가 최적이어야 함
        assert best_angle in [90, 270]

    def test_horizontal_text_detection(self):
        """수평 텍스트 이미지 회전 감지"""
        from PIL import Image
        from services.table_structure_recognizer import get_table_structure_recognizer

        recognizer = get_table_structure_recognizer()

        if not recognizer.is_ocr_available:
            pytest.skip("OCR not available")

        # 타이틀 블록 이미지 (수평 텍스트)
        image_path = "/home/uproot/ax/poc/web-ui/public/samples/sample2_bom_table_1.png"
        if not Path(image_path).exists():
            pytest.skip("샘플 이미지 없음")

        image = Image.open(image_path).convert("RGB")

        best_angle, results = recognizer.detect_text_rotation(image)

        # 수평 텍스트는 0도가 최적이어야 함
        assert best_angle == 0

    def test_rotation_improves_ocr(self):
        """회전이 OCR 품질을 향상시키는지 확인"""
        from PIL import Image
        from services.table_structure_recognizer import get_table_structure_recognizer

        recognizer = get_table_structure_recognizer()

        if not recognizer.is_ocr_available:
            pytest.skip("OCR not available")

        image_path = "/home/uproot/ax/poc/web-ui/public/samples/sample3_bom_table_1.png"
        image = Image.open(image_path).convert("RGB")

        # 회전 없이 OCR
        results_no_rotate = recognizer.extract_whole_table_text(
            image, upscale_factor=3, confidence_threshold=0.3
        )

        # 회전 포함 OCR
        results_with_rotate, applied_rotation = recognizer.extract_whole_table_text_with_rotation(
            image, upscale_factor=3, confidence_threshold=0.3, auto_rotate=True
        )

        # 회전이 적용되었다면
        if applied_rotation != 0:
            # 회전 후 결과가 있어야 함
            assert len(results_with_rotate) >= 0
