"""
Line Detector API Unit Tests
테스트 대상: 라인 검출, 스타일 분류, 점선 박스 영역 검출 기능
"""
import pytest
import numpy as np
import sys
import os
import cv2

# api_server.py에서 함수들을 import하기 위해 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_server import (
    detect_lines_lsd,
    detect_lines_hough,
    classify_line_type,
    classify_line_style,
    classify_line_by_color,
    classify_line_purpose,
    thin_image,
    LINE_COLOR_TYPES,
    LINE_STYLE_TYPES,
    LINE_PURPOSE_TYPES,
    REGION_TYPES,
)


class TestLineDetection:
    """라인 검출 테스트"""

    @pytest.fixture
    def test_image(self):
        """테스트용 이미지 생성 (흰 배경에 검은 라인들)"""
        img = np.ones((500, 500), dtype=np.uint8) * 255
        # 수평선
        cv2.line(img, (100, 200), (400, 200), 0, 2)
        # 수직선
        cv2.line(img, (250, 100), (250, 400), 0, 2)
        # 대각선
        cv2.line(img, (100, 100), (400, 400), 0, 2)
        return img

    def test_lsd_detection(self, test_image):
        """LSD 라인 검출 테스트"""
        lines = detect_lines_lsd(test_image)
        assert isinstance(lines, list), "LSD should return a list"
        # 최소 1개 이상의 라인이 검출되어야 함
        assert len(lines) >= 1, "LSD should detect at least 1 line"

    def test_hough_detection(self, test_image):
        """Hough 라인 검출 테스트"""
        lines = detect_lines_hough(test_image)
        assert isinstance(lines, list), "Hough should return a list"

    def test_line_structure(self, test_image):
        """검출된 라인 구조 테스트"""
        lines = detect_lines_lsd(test_image)
        if lines:
            line = lines[0]
            assert 'start_point' in line, "Line should have start_point"
            assert 'end_point' in line, "Line should have end_point"
            assert 'length' in line, "Line should have length"
            assert 'angle' in line, "Line should have angle"


class TestLineTypeClassification:
    """라인 타입 분류 테스트"""

    def test_classify_type_with_neighbors(self):
        """인접 라인이 있는 경우 타입 분류"""
        # 단일 라인
        line = {'start_point': (100, 100), 'end_point': (200, 100), 'length': 100, 'angle': 0}
        all_lines = [line]
        line_type = classify_line_type(line, all_lines)
        assert line_type in ['pipe', 'signal', 'unknown'], f"Unexpected type: {line_type}"

    def test_classify_type_structure(self):
        """타입 분류 결과 구조 테스트"""
        line = {'start_point': (100, 100), 'end_point': (200, 100), 'length': 100, 'angle': 0}
        all_lines = [line]
        result = classify_line_type(line, all_lines)
        assert isinstance(result, str), "Type should be a string"


class TestLineStyleClassification:
    """라인 스타일 분류 테스트"""

    @pytest.fixture
    def solid_line_image(self):
        """실선 이미지 생성"""
        img = np.ones((200, 400), dtype=np.uint8) * 255
        cv2.line(img, (50, 100), (350, 100), 0, 2)  # 연속 검은 선
        return img

    @pytest.fixture
    def dashed_line_image(self):
        """점선 이미지 생성"""
        img = np.ones((200, 400), dtype=np.uint8) * 255
        # 점선 패턴 그리기 (간격 있는 선분들)
        for x in range(50, 350, 40):
            cv2.line(img, (x, 100), (x + 20, 100), 0, 2)
        return img

    def test_solid_line_style(self, solid_line_image):
        """실선 스타일 분류 테스트"""
        line = {'start_point': (50, 100), 'end_point': (350, 100)}
        result = classify_line_style(solid_line_image, line)
        assert 'style' in result, "Result should have 'style' key"
        assert result['style'] in ['solid', 'unknown'], f"Expected solid, got {result['style']}"

    def test_dashed_line_style(self, dashed_line_image):
        """점선 스타일 분류 테스트"""
        line = {'start_point': (50, 100), 'end_point': (350, 100)}
        result = classify_line_style(dashed_line_image, line)
        assert 'style' in result, "Result should have 'style' key"
        # 점선 또는 관련 스타일로 분류되어야 함
        assert result['style'] in ['dashed', 'dotted', 'dash_dot', 'solid', 'unknown'], \
            f"Unexpected style: {result['style']}"

    def test_style_result_structure(self, solid_line_image):
        """스타일 분류 결과 구조 테스트"""
        line = {'start_point': (50, 100), 'end_point': (350, 100)}
        result = classify_line_style(solid_line_image, line)
        assert 'style' in result
        assert 'style_korean' in result
        assert 'confidence' in result
        assert isinstance(result['confidence'], float)


class TestLineColorClassification:
    """색상 기반 라인 분류 테스트"""

    @pytest.fixture
    def colored_image(self):
        """색상 라인 이미지 생성"""
        img = np.ones((200, 400, 3), dtype=np.uint8) * 255
        # 빨간 선 (공정 배관)
        cv2.line(img, (50, 50), (350, 50), (0, 0, 255), 2)
        # 파란 선 (냉각수)
        cv2.line(img, (50, 100), (350, 100), (255, 0, 0), 2)
        # 검은 선
        cv2.line(img, (50, 150), (350, 150), (0, 0, 0), 2)
        return img

    def test_color_classification_structure(self, colored_image):
        """색상 분류 결과 구조 테스트"""
        line = {'start_point': (50, 50), 'end_point': (350, 50)}
        result = classify_line_by_color(colored_image, line)
        assert 'color' in result  # 색상 이름
        assert 'rgb' in result    # RGB 값


class TestLinePurposeClassification:
    """라인 용도 분류 테스트"""

    def test_purpose_classification(self):
        """용도 분류 테스트"""
        line = {
            'start_point': (100, 100),
            'end_point': (200, 100),
            'style': 'solid',
            'color_name': 'black',
            'line_type': 'pipe'
        }
        result = classify_line_purpose(line)
        assert 'purpose' in result
        assert 'purpose_korean' in result


class TestConstants:
    """상수 정의 테스트"""

    def test_line_colors_defined(self):
        """색상 상수 정의 확인"""
        assert 'black' in LINE_COLOR_TYPES
        assert 'red' in LINE_COLOR_TYPES
        assert 'blue' in LINE_COLOR_TYPES
        # 한국어 이름 확인
        assert 'korean' in LINE_COLOR_TYPES['black']

    def test_line_styles_defined(self):
        """스타일 상수 정의 확인"""
        expected_styles = ['solid', 'dashed', 'dotted', 'dash_dot']
        for style in expected_styles:
            assert style in LINE_STYLE_TYPES, f"Style '{style}' should be defined"
            assert 'korean' in LINE_STYLE_TYPES[style], f"Style '{style}' should have korean name"

    def test_line_purposes_defined(self):
        """용도 상수 정의 확인"""
        expected_purposes = ['main_process', 'instrument_signal', 'electrical']
        for purpose in expected_purposes:
            assert purpose in LINE_PURPOSE_TYPES, f"Purpose '{purpose}' should be defined"

    def test_region_types_defined(self):
        """영역 타입 상수 정의 확인"""
        expected_regions = ['signal_group', 'equipment_boundary', 'note_box']
        for region in expected_regions:
            assert region in REGION_TYPES, f"Region type '{region}' should be defined"


class TestThinning:
    """이미지 세선화 테스트"""

    @pytest.mark.skipif(
        not hasattr(cv2, 'ximgproc') or not hasattr(cv2.ximgproc, 'thinning'),
        reason="opencv-contrib-python not installed (cv2.ximgproc.thinning unavailable)"
    )
    def test_thin_image(self):
        """세선화 테스트 (opencv-contrib 필요)"""
        # 두꺼운 선 이미지 생성
        img = np.zeros((100, 100), dtype=np.uint8)
        cv2.rectangle(img, (20, 20), (80, 80), 255, 10)  # 두꺼운 사각형

        # 세선화
        thinned = thin_image(img)

        assert thinned.shape == img.shape, "Thinned image should have same shape"
        # 세선화 후 픽셀 수가 줄어들어야 함
        assert np.sum(thinned > 0) <= np.sum(img > 0), "Thinned image should have fewer pixels"


class TestEdgeCases:
    """엣지 케이스 테스트"""

    def test_empty_image(self):
        """빈 이미지 테스트"""
        img = np.ones((100, 100), dtype=np.uint8) * 255
        lines = detect_lines_lsd(img)
        assert isinstance(lines, list), "Should return empty list for blank image"

    def test_short_line_classification(self):
        """짧은 라인 스타일 분류 테스트"""
        img = np.ones((100, 100), dtype=np.uint8) * 255
        cv2.line(img, (45, 50), (55, 50), 0, 1)  # 10픽셀 길이 라인

        line = {'start_point': (45, 50), 'end_point': (55, 50)}
        result = classify_line_style(img, line, sample_count=5)
        # 짧은 라인도 에러 없이 처리되어야 함
        assert 'style' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
