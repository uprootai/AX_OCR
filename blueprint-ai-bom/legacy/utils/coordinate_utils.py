"""
Coordinate Conversion Utilities
좌표 변환 관련 유틸리티 함수들
"""
from typing import Tuple

def yolo_to_xyxy(x_center: float, y_center: float, width: float, height: float,
                 img_width: int, img_height: int) -> Tuple[int, int, int, int]:
    """YOLO 형식을 xyxy 좌표로 변환 (더 정확한 반올림 적용)"""
    x_center_abs = x_center * img_width
    y_center_abs = y_center * img_height
    width_abs = width * img_width
    height_abs = height * img_height

    # round()를 사용하여 더 정확한 좌표 계산
    x1 = round(x_center_abs - width_abs / 2)
    y1 = round(y_center_abs - height_abs / 2)
    x2 = round(x_center_abs + width_abs / 2)
    y2 = round(y_center_abs + height_abs / 2)

    # 이미지 경계 내로 제한
    x1 = max(0, min(x1, img_width - 1))
    y1 = max(0, min(y1, img_height - 1))
    x2 = max(0, min(x2, img_width - 1))
    y2 = max(0, min(y2, img_height - 1))

    return x1, y1, x2, y2

def xyxy_to_yolo(x1: int, y1: int, x2: int, y2: int,
                 img_width: int, img_height: int) -> Tuple[float, float, float, float]:
    """xyxy 좌표를 YOLO 형식으로 변환"""
    x_center = ((x1 + x2) / 2) / img_width
    y_center = ((y1 + y2) / 2) / img_height
    width = (x2 - x1) / img_width
    height = (y2 - y1) / img_height

    return x_center, y_center, width, height