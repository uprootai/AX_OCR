"""
Image Renderer Service
이미지 렌더링 및 인코딩 유틸리티
"""

import base64
from typing import Optional, Tuple

import cv2
import numpy as np


def render_to_image(
    image: np.ndarray,
    output_format: str = "png",
    quality: int = 95
) -> bytes:
    """
    NumPy 이미지를 바이트로 인코딩

    Args:
        image: 이미지 (BGR)
        output_format: 출력 형식 (png, jpg, webp)
        quality: JPEG/WebP 품질 (0-100)

    Returns:
        인코딩된 이미지 바이트
    """
    if output_format.lower() == "jpg" or output_format.lower() == "jpeg":
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        _, buffer = cv2.imencode('.jpg', image, encode_param)
    elif output_format.lower() == "webp":
        encode_param = [int(cv2.IMWRITE_WEBP_QUALITY), quality]
        _, buffer = cv2.imencode('.webp', image, encode_param)
    else:  # png
        _, buffer = cv2.imencode('.png', image)

    return buffer.tobytes()


def image_to_base64(
    image: np.ndarray,
    output_format: str = "png",
    quality: int = 95
) -> str:
    """
    NumPy 이미지를 Base64 문자열로 변환

    Args:
        image: 이미지 (BGR)
        output_format: 출력 형식 (png, jpg, webp)
        quality: JPEG/WebP 품질 (0-100)

    Returns:
        Base64 인코딩된 문자열
    """
    image_bytes = render_to_image(image, output_format, quality)
    return base64.b64encode(image_bytes).decode('utf-8')


def base64_to_image(base64_str: str) -> np.ndarray:
    """
    Base64 문자열을 NumPy 이미지로 변환

    Args:
        base64_str: Base64 인코딩된 이미지 문자열

    Returns:
        이미지 (BGR)
    """
    # Data URL 접두사 제거
    if ',' in base64_str:
        base64_str = base64_str.split(',')[1]

    image_bytes = base64.b64decode(base64_str)
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return image


def resize_image(
    image: np.ndarray,
    max_size: Optional[Tuple[int, int]] = None,
    scale: Optional[float] = None
) -> np.ndarray:
    """
    이미지 리사이즈

    Args:
        image: 원본 이미지
        max_size: 최대 크기 (width, height)
        scale: 스케일 비율

    Returns:
        리사이즈된 이미지
    """
    if scale is not None:
        new_width = int(image.shape[1] * scale)
        new_height = int(image.shape[0] * scale)
        return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)

    if max_size is not None:
        max_w, max_h = max_size
        h, w = image.shape[:2]

        if w > max_w or h > max_h:
            scale = min(max_w / w, max_h / h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)

    return image


def add_legend(
    image: np.ndarray,
    layer_counts: dict,
    position: str = "bottom-left"
) -> np.ndarray:
    """
    이미지에 범례 추가

    Args:
        image: 원본 이미지
        layer_counts: {"symbols": 10, "lines": 20, ...}
        position: 범례 위치

    Returns:
        범례가 추가된 이미지
    """
    vis = image.copy()
    h, w = vis.shape[:2]

    # 범례 설정
    legend_items = [
        ("Symbols", (0, 120, 255), layer_counts.get('symbols', 0)),
        ("Lines", (255, 0, 0), layer_counts.get('lines', 0)),
        ("Texts", (0, 165, 255), layer_counts.get('texts', 0)),
        ("Regions", (255, 255, 0), layer_counts.get('regions', 0)),
    ]

    # 표시할 항목만 필터링
    legend_items = [(name, color, count) for name, color, count in legend_items if count > 0]

    if not legend_items:
        return vis

    # 범례 크기 계산
    line_height = 25
    legend_height = len(legend_items) * line_height + 20
    legend_width = 150

    # 위치 결정
    if position == "bottom-left":
        x, y = 10, h - legend_height - 10
    elif position == "bottom-right":
        x, y = w - legend_width - 10, h - legend_height - 10
    elif position == "top-left":
        x, y = 10, 10
    else:  # top-right
        x, y = w - legend_width - 10, 10

    # 배경
    overlay = vis.copy()
    cv2.rectangle(overlay, (x, y), (x + legend_width, y + legend_height), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.7, vis, 0.3, 0, vis)

    # 테두리
    cv2.rectangle(vis, (x, y), (x + legend_width, y + legend_height), (255, 255, 255), 1)

    # 항목 그리기
    for i, (name, color, count) in enumerate(legend_items):
        item_y = y + 15 + i * line_height

        # 색상 박스
        cv2.rectangle(vis, (x + 10, item_y - 8), (x + 25, item_y + 7), color, -1)

        # 텍스트
        cv2.putText(vis, f"{name}: {count}", (x + 35, item_y + 4),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

    return vis
