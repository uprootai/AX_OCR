"""SVG Generator 테스트

Line Detector SVG 오버레이 생성 테스트:
- 라인 SVG 생성
- 영역 SVG 생성
- 색상 매핑
- HTML 이스케이프

2026-01-02: 초기 작성
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.svg_generator import (
    generate_line_svg,
    generate_region_svg,
    lines_to_svg_data,
    regions_to_svg_data,
    LINE_STYLE_COLORS,
    LINE_TYPE_COLORS,
    REGION_TYPE_COLORS,
)
from services.svg_common import escape_html


class TestLineSVGGeneration:
    """라인 SVG 생성 테스트"""

    @pytest.fixture
    def sample_lines(self):
        """테스트용 라인 검출 결과"""
        return [
            {
                "id": 1,
                "start_point": [100, 100],
                "end_point": [300, 100],
                "line_type": "pipe",
                "line_style": "solid",
            },
            {
                "id": 2,
                "waypoints": [[50, 200], [150, 200], [150, 300], [250, 300]],
                "line_type": "signal",
                "line_style": "dashed",
            },
        ]

    @pytest.fixture
    def image_size(self):
        return (640, 480)

    def test_generate_line_svg_returns_string(self, sample_lines, image_size):
        """SVG 생성 시 문자열 반환"""
        svg = generate_line_svg(sample_lines, image_size)
        assert isinstance(svg, str)

    def test_generate_line_svg_contains_svg_tag(self, sample_lines, image_size):
        """SVG 태그 포함 확인"""
        svg = generate_line_svg(sample_lines, image_size)
        assert "<svg" in svg
        assert "</svg>" in svg

    def test_generate_line_svg_contains_viewbox(self, sample_lines, image_size):
        """viewBox 속성 포함 확인"""
        svg = generate_line_svg(sample_lines, image_size)
        assert f'viewBox="0 0 {image_size[0]} {image_size[1]}"' in svg

    def test_generate_line_svg_with_simple_line(self, image_size):
        """단순 라인 (start_point/end_point) SVG 생성"""
        lines = [
            {
                "id": 1,
                "start_point": [0, 0],
                "end_point": [100, 100],
                "line_type": "pipe",
            }
        ]
        svg = generate_line_svg(lines, image_size)
        assert "<line" in svg
        assert 'x1="0"' in svg
        assert 'y1="0"' in svg

    def test_generate_line_svg_with_polyline(self, image_size):
        """폴리라인 (waypoints) SVG 생성"""
        lines = [
            {
                "id": 1,
                "waypoints": [[0, 0], [50, 50], [100, 0]],
                "line_type": "signal",
            }
        ]
        svg = generate_line_svg(lines, image_size)
        assert "<polyline" in svg
        assert "0,0 50,50 100,0" in svg

    def test_generate_line_svg_with_labels(self, sample_lines, image_size):
        """라벨 포함 SVG 생성"""
        svg = generate_line_svg(sample_lines, image_size, show_labels=True)
        assert 'class="line-label"' in svg

    def test_generate_line_svg_without_labels(self, sample_lines, image_size):
        """라벨 없는 SVG 생성"""
        svg = generate_line_svg(sample_lines, image_size, show_labels=False)
        assert 'class="line-label"' not in svg

    def test_generate_line_svg_color_by_type(self, sample_lines, image_size):
        """라인 타입별 색상 적용"""
        svg = generate_line_svg(sample_lines, image_size, color_by="line_type")
        assert LINE_TYPE_COLORS["pipe"] in svg
        assert LINE_TYPE_COLORS["signal"] in svg

    def test_generate_line_svg_color_by_style(self, sample_lines, image_size):
        """라인 스타일별 색상 적용"""
        svg = generate_line_svg(sample_lines, image_size, color_by="line_style")
        assert LINE_STYLE_COLORS["solid"] in svg
        assert LINE_STYLE_COLORS["dashed"] in svg

    def test_generate_line_svg_empty_lines(self, image_size):
        """빈 라인 결과 처리"""
        svg = generate_line_svg([], image_size)
        assert "<svg" in svg
        assert "</svg>" in svg


class TestRegionSVGGeneration:
    """영역 SVG 생성 테스트"""

    @pytest.fixture
    def sample_regions(self):
        """테스트용 영역 검출 결과"""
        return [
            {
                "id": 1,
                "bbox": [50, 50, 200, 150],
                "region_type": "signal_group",
                "region_type_korean": "신호 그룹",
            },
            {
                "id": 2,
                "bbox": [250, 100, 400, 250],
                "region_type": "equipment_boundary",
                "region_type_korean": "장비 경계",
            },
        ]

    @pytest.fixture
    def image_size(self):
        return (640, 480)

    def test_generate_region_svg_returns_string(self, sample_regions, image_size):
        """SVG 생성 시 문자열 반환"""
        svg = generate_region_svg(sample_regions, image_size)
        assert isinstance(svg, str)

    def test_generate_region_svg_contains_svg_tag(self, sample_regions, image_size):
        """SVG 태그 포함 확인"""
        svg = generate_region_svg(sample_regions, image_size)
        assert "<svg" in svg
        assert "</svg>" in svg

    def test_generate_region_svg_contains_rect(self, sample_regions, image_size):
        """영역 rect 포함 확인"""
        svg = generate_region_svg(sample_regions, image_size)
        assert 'class="region-box"' in svg

    def test_generate_region_svg_dashed_stroke(self, sample_regions, image_size):
        """점선 테두리 확인"""
        svg = generate_region_svg(sample_regions, image_size)
        assert 'stroke-dasharray=' in svg

    def test_generate_region_svg_with_labels(self, sample_regions, image_size):
        """라벨 포함 SVG 생성"""
        svg = generate_region_svg(sample_regions, image_size, show_labels=True)
        assert 'class="region-label"' in svg
        assert "신호 그룹" in svg or "signal_group" in svg

    def test_generate_region_svg_without_labels(self, sample_regions, image_size):
        """라벨 없는 SVG 생성"""
        svg = generate_region_svg(sample_regions, image_size, show_labels=False)
        assert 'class="region-label"' not in svg

    def test_generate_region_svg_colors(self, sample_regions, image_size):
        """영역 타입별 색상 적용"""
        svg = generate_region_svg(sample_regions, image_size)
        assert REGION_TYPE_COLORS["signal_group"] in svg
        assert REGION_TYPE_COLORS["equipment_boundary"] in svg

    def test_generate_region_svg_empty_regions(self, image_size):
        """빈 영역 결과 처리"""
        svg = generate_region_svg([], image_size)
        assert "<svg" in svg
        assert "</svg>" in svg


class TestSVGDataDict:
    """SVG 데이터 딕셔너리 테스트"""

    @pytest.fixture
    def sample_lines(self):
        return [
            {
                "id": 1,
                "start_point": [0, 0],
                "end_point": [100, 100],
                "line_type": "pipe",
            }
        ]

    @pytest.fixture
    def sample_regions(self):
        return [
            {
                "id": 1,
                "bbox": [0, 0, 100, 100],
                "region_type": "note_box",
            }
        ]

    def test_lines_svg_data_contains_required_keys(self, sample_lines):
        """라인 SVG 데이터 필수 키 포함"""
        data = lines_to_svg_data(sample_lines, (640, 480))
        assert "svg" in data
        assert "svg_minimal" in data
        assert "width" in data
        assert "height" in data
        assert "line_count" in data

    def test_lines_svg_data_correct_count(self, sample_lines):
        """정확한 라인 개수"""
        data = lines_to_svg_data(sample_lines, (640, 480))
        assert data["line_count"] == 1

    def test_regions_svg_data_contains_required_keys(self, sample_regions):
        """영역 SVG 데이터 필수 키 포함"""
        data = regions_to_svg_data(sample_regions, (640, 480))
        assert "svg" in data
        assert "svg_minimal" in data
        assert "width" in data
        assert "height" in data
        assert "region_count" in data

    def test_regions_svg_data_correct_count(self, sample_regions):
        """정확한 영역 개수"""
        data = regions_to_svg_data(sample_regions, (640, 480))
        assert data["region_count"] == 1


class TestColorMapping:
    """색상 매핑 테스트"""

    def test_line_type_colors_defined(self):
        """라인 타입 색상 정의 확인"""
        assert "pipe" in LINE_TYPE_COLORS
        assert "signal" in LINE_TYPE_COLORS
        assert "unknown" in LINE_TYPE_COLORS

    def test_line_style_colors_defined(self):
        """라인 스타일 색상 정의 확인"""
        assert "solid" in LINE_STYLE_COLORS
        assert "dashed" in LINE_STYLE_COLORS
        assert "dashed_single_dot" in LINE_STYLE_COLORS

    def test_region_type_colors_defined(self):
        """영역 타입 색상 정의 확인"""
        assert "signal_group" in REGION_TYPE_COLORS
        assert "equipment_boundary" in REGION_TYPE_COLORS
        assert "note_box" in REGION_TYPE_COLORS

    def test_colors_are_hex(self):
        """색상이 HEX 형식"""
        for colors in [LINE_TYPE_COLORS, LINE_STYLE_COLORS, REGION_TYPE_COLORS]:
            for color in colors.values():
                assert color.startswith("#")
                assert len(color) == 7


class TestHTMLEscape:
    """HTML 이스케이프 테스트"""

    def test_escape_ampersand(self):
        """& 이스케이프"""
        assert escape_html("A & B") == "A &amp; B"

    def test_escape_less_than(self):
        """< 이스케이프"""
        assert escape_html("A < B") == "A &lt; B"

    def test_escape_greater_than(self):
        """> 이스케이프"""
        assert escape_html("A > B") == "A &gt; B"

    def test_escape_quotes(self):
        """따옴표 이스케이프"""
        assert escape_html('A "B" C') == 'A &quot;B&quot; C'
        assert escape_html("A 'B' C") == "A &#039;B&#039; C"


class TestInteractivity:
    """인터랙티브 기능 테스트"""

    @pytest.fixture
    def sample_lines(self):
        return [
            {
                "id": 1,
                "start_point": [0, 0],
                "end_point": [100, 100],
                "line_type": "pipe",
            }
        ]

    @pytest.fixture
    def sample_regions(self):
        return [
            {
                "id": 1,
                "bbox": [0, 0, 100, 100],
                "region_type": "note_box",
            }
        ]

    def test_interactive_line_svg_has_hover_styles(self, sample_lines):
        """인터랙티브 라인 SVG에 호버 스타일 포함"""
        svg = generate_line_svg(sample_lines, (640, 480), interactive=True)
        assert ":hover" in svg

    def test_non_interactive_line_svg_no_hover_styles(self, sample_lines):
        """비인터랙티브 라인 SVG에 호버 스타일 없음"""
        svg = generate_line_svg(sample_lines, (640, 480), interactive=False)
        assert ":hover" not in svg

    def test_interactive_region_svg_has_hover_styles(self, sample_regions):
        """인터랙티브 영역 SVG에 호버 스타일 포함"""
        svg = generate_region_svg(sample_regions, (640, 480), interactive=True)
        assert ":hover" in svg

    def test_non_interactive_region_svg_no_hover_styles(self, sample_regions):
        """비인터랙티브 영역 SVG에 호버 스타일 없음"""
        svg = generate_region_svg(sample_regions, (640, 480), interactive=False)
        assert ":hover" not in svg

    def test_line_svg_has_data_attributes(self, sample_lines):
        """라인 SVG에 데이터 속성 포함"""
        svg = generate_line_svg(sample_lines, (640, 480))
        assert 'data-id="' in svg
        assert 'data-type="' in svg

    def test_region_svg_has_data_attributes(self, sample_regions):
        """영역 SVG에 데이터 속성 포함"""
        svg = generate_region_svg(sample_regions, (640, 480))
        assert 'data-id="' in svg
        assert 'data-type="' in svg
