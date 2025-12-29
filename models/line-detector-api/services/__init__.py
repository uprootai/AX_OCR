"""
Line Detector Services
라인 검출 및 분류 서비스 모듈
"""

from .constants import (
    LINE_COLOR_TYPES,
    LINE_STYLE_TYPES,
    LINE_PURPOSE_TYPES,
    REGION_TYPES,
)

from .detection_service import (
    thin_image,
    detect_lines_lsd,
    detect_lines_hough,
    merge_collinear_lines,
    find_intersections,
)

from .classification_service import (
    classify_line_type,
    classify_line_by_color,
    classify_all_lines_by_color,
    classify_line_style,
    classify_all_lines_by_style,
    classify_line_purpose,
)

from .region_service import (
    find_dashed_regions,
    count_lines_in_region,
    get_symbols_in_region,
    classify_region_type_by_keywords,
)

from .visualization_service import (
    visualize_lines,
    visualize_regions,
    numpy_to_base64,
)

__all__ = [
    # Constants
    'LINE_COLOR_TYPES',
    'LINE_STYLE_TYPES',
    'LINE_PURPOSE_TYPES',
    'REGION_TYPES',
    # Detection
    'thin_image',
    'detect_lines_lsd',
    'detect_lines_hough',
    'merge_collinear_lines',
    'find_intersections',
    # Classification
    'classify_line_type',
    'classify_line_by_color',
    'classify_all_lines_by_color',
    'classify_line_style',
    'classify_all_lines_by_style',
    'classify_line_purpose',
    # Region
    'find_dashed_regions',
    'count_lines_in_region',
    'get_symbols_in_region',
    'classify_region_type_by_keywords',
    # Visualization
    'visualize_lines',
    'visualize_regions',
    'numpy_to_base64',
]
