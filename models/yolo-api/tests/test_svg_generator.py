"""SVG Generator 테스트

YOLO Detection SVG 오버레이 생성 테스트:
- SVG 문자열 생성
- 색상 매핑
- HTML 이스케이프
- 인터랙티브 기능

2026-01-02: 초기 작성
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.svg_generator import (
    generate_detection_svg,
    generate_detection_svg_minimal,
    detections_to_svg_data,
    MODEL_COLORS,
    CLASS_COLORS,
    _escape_html,
)


class TestSVGGeneration:
    """SVG 생성 기본 테스트"""

    @pytest.fixture
    def sample_detections(self):
        """테스트용 검출 결과"""
        return [
            {
                "class_id": 0,
                "class_name": "dimension_line",
                "confidence": 0.95,
                "bbox": {"x": 100, "y": 100, "width": 200, "height": 50},
            },
            {
                "class_id": 1,
                "class_name": "center_line",
                "confidence": 0.88,
                "bbox": {"x": 300, "y": 200, "width": 150, "height": 30},
            },
        ]

    @pytest.fixture
    def image_size(self):
        """테스트용 이미지 크기"""
        return (640, 480)

    def test_generate_svg_returns_string(self, sample_detections, image_size):
        """SVG 생성 시 문자열 반환"""
        svg = generate_detection_svg(sample_detections, image_size)
        assert isinstance(svg, str)

    def test_generate_svg_contains_svg_tag(self, sample_detections, image_size):
        """SVG 태그 포함 확인"""
        svg = generate_detection_svg(sample_detections, image_size)
        assert "<svg" in svg
        assert "</svg>" in svg

    def test_generate_svg_contains_viewbox(self, sample_detections, image_size):
        """viewBox 속성 포함 확인"""
        svg = generate_detection_svg(sample_detections, image_size)
        assert f'viewBox="0 0 {image_size[0]} {image_size[1]}"' in svg

    def test_generate_svg_contains_detection_boxes(self, sample_detections, image_size):
        """검출 박스 포함 확인"""
        svg = generate_detection_svg(sample_detections, image_size)
        assert 'class="detection-box"' in svg
        assert 'data-class-name="dimension_line"' in svg
        assert 'data-class-name="center_line"' in svg

    def test_generate_svg_with_labels(self, sample_detections, image_size):
        """라벨 포함 SVG 생성"""
        svg = generate_detection_svg(sample_detections, image_size, show_labels=True)
        assert 'class="detection-label"' in svg

    def test_generate_svg_without_labels(self, sample_detections, image_size):
        """라벨 없는 SVG 생성"""
        svg = generate_detection_svg(sample_detections, image_size, show_labels=False)
        assert 'class="detection-label"' not in svg

    def test_generate_svg_with_confidence(self, sample_detections, image_size):
        """신뢰도 표시 SVG 생성"""
        svg = generate_detection_svg(
            sample_detections, image_size,
            show_labels=True, show_confidence=True
        )
        assert "95.0%" in svg or "88.0%" in svg

    def test_generate_svg_empty_detections(self, image_size):
        """빈 검출 결과 처리"""
        svg = generate_detection_svg([], image_size)
        assert "<svg" in svg
        assert "</svg>" in svg


class TestSVGMinimal:
    """최소 SVG 생성 테스트"""

    @pytest.fixture
    def sample_detections(self):
        return [
            {
                "class_id": 0,
                "class_name": "test",
                "confidence": 0.9,
                "bbox": {"x": 10, "y": 10, "width": 100, "height": 100},
            }
        ]

    def test_minimal_svg_no_labels(self, sample_detections):
        """최소 SVG에 라벨 없음"""
        svg = generate_detection_svg_minimal(sample_detections, (640, 480))
        assert "class=" not in svg or "detection-label" not in svg

    def test_minimal_svg_contains_rect(self, sample_detections):
        """최소 SVG에 rect 포함"""
        svg = generate_detection_svg_minimal(sample_detections, (640, 480))
        assert "<rect" in svg


class TestSVGDataDict:
    """SVG 데이터 딕셔너리 테스트"""

    @pytest.fixture
    def sample_detections(self):
        return [
            {
                "class_id": 0,
                "class_name": "test",
                "confidence": 0.9,
                "bbox": {"x": 10, "y": 10, "width": 100, "height": 100},
            }
        ]

    def test_svg_data_contains_required_keys(self, sample_detections):
        """필수 키 포함 확인"""
        data = detections_to_svg_data(sample_detections, (640, 480), "engineering")
        assert "svg" in data
        assert "svg_minimal" in data
        assert "width" in data
        assert "height" in data
        assert "detection_count" in data
        assert "model_type" in data

    def test_svg_data_correct_dimensions(self, sample_detections):
        """정확한 이미지 크기"""
        data = detections_to_svg_data(sample_detections, (800, 600), "engineering")
        assert data["width"] == 800
        assert data["height"] == 600

    def test_svg_data_correct_count(self, sample_detections):
        """정확한 검출 개수"""
        data = detections_to_svg_data(sample_detections, (640, 480), "engineering")
        assert data["detection_count"] == 1

    def test_svg_data_model_type(self, sample_detections):
        """모델 타입 저장"""
        data = detections_to_svg_data(sample_detections, (640, 480), "pid_symbol")
        assert data["model_type"] == "pid_symbol"


class TestColorMapping:
    """색상 매핑 테스트"""

    def test_model_colors_defined(self):
        """모델 색상 정의 확인"""
        assert "engineering" in MODEL_COLORS
        assert "pid_symbol" in MODEL_COLORS
        assert "bom_detector" in MODEL_COLORS

    def test_class_colors_defined(self):
        """클래스 색상 정의 확인"""
        assert "dimension_line" in CLASS_COLORS
        assert "center_line" in CLASS_COLORS
        assert "weld_symbol" in CLASS_COLORS

    def test_colors_are_hex(self):
        """색상이 HEX 형식"""
        for color in MODEL_COLORS.values():
            assert color.startswith("#")
            assert len(color) == 7

    def test_class_color_used_in_svg(self):
        """클래스 색상이 SVG에 적용"""
        detections = [
            {
                "class_id": 0,
                "class_name": "dimension_line",
                "confidence": 0.9,
                "bbox": {"x": 10, "y": 10, "width": 100, "height": 100},
            }
        ]
        svg = generate_detection_svg(detections, (640, 480))
        assert CLASS_COLORS["dimension_line"] in svg


class TestHTMLEscape:
    """HTML 이스케이프 테스트"""

    def test_escape_ampersand(self):
        """& 이스케이프"""
        assert _escape_html("A & B") == "A &amp; B"

    def test_escape_less_than(self):
        """< 이스케이프"""
        assert _escape_html("A < B") == "A &lt; B"

    def test_escape_greater_than(self):
        """> 이스케이프"""
        assert _escape_html("A > B") == "A &gt; B"

    def test_escape_quotes(self):
        """따옴표 이스케이프"""
        assert _escape_html('A "B" C') == 'A &quot;B&quot; C'
        assert _escape_html("A 'B' C") == "A &#039;B&#039; C"

    def test_escape_in_svg(self):
        """SVG에서 이스케이프 적용"""
        detections = [
            {
                "class_id": 0,
                "class_name": "test<>&",
                "confidence": 0.9,
                "bbox": {"x": 10, "y": 10, "width": 100, "height": 100},
            }
        ]
        svg = generate_detection_svg(detections, (640, 480), show_labels=True)
        assert "&lt;" in svg
        assert "&gt;" in svg
        assert "&amp;" in svg


class TestInteractivity:
    """인터랙티브 기능 테스트"""

    @pytest.fixture
    def sample_detections(self):
        return [
            {
                "class_id": 0,
                "class_name": "test",
                "confidence": 0.9,
                "bbox": {"x": 10, "y": 10, "width": 100, "height": 100},
            }
        ]

    def test_interactive_svg_has_hover_styles(self, sample_detections):
        """인터랙티브 SVG에 호버 스타일 포함"""
        svg = generate_detection_svg(
            sample_detections, (640, 480), interactive=True
        )
        assert ":hover" in svg

    def test_non_interactive_svg_no_hover_styles(self, sample_detections):
        """비인터랙티브 SVG에 호버 스타일 없음"""
        svg = generate_detection_svg(
            sample_detections, (640, 480), interactive=False
        )
        assert ":hover" not in svg

    def test_svg_has_data_attributes(self, sample_detections):
        """SVG에 데이터 속성 포함"""
        svg = generate_detection_svg(sample_detections, (640, 480))
        assert 'data-id="' in svg
        assert 'data-class-id="' in svg
        assert 'data-confidence="' in svg
