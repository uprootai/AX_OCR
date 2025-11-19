"""
Image Processing Utilities

이미지 변환, crop, upscale, 시각화 등 이미지 처리 함수들
"""
import io
import base64
import logging
from typing import Dict, List, Any
from PIL import Image
import cv2
import numpy as np
import fitz  # PyMuPDF
from fastapi import HTTPException

logger = logging.getLogger(__name__)


# YOLO 클래스명 매핑 (시각화용)
CLASS_DISPLAY_NAMES = {
    'diameter_dim': 'Diameter (Ø)',
    'linear_dim': 'Linear Dim',
    'radius_dim': 'Radius (R)',
    'angular_dim': 'Angular',
    'chamfer_dim': 'Chamfer',
    'tolerance_dim': 'Tolerance',
    'reference_dim': 'Reference',
    'flatness': 'Flatness (⏥)',
    'cylindricity': 'Cylindricity (⌭)',
    'position': 'Position (⌖)',
    'perpendicularity': 'Perpendicular (⊥)',
    'parallelism': 'Parallel (∥)',
    'surface_roughness': 'Roughness (Ra)',
    'text_block': 'Text'
}


def pdf_to_image(pdf_bytes: bytes, dpi: int = 150) -> bytes:
    """
    PDF의 첫 페이지를 PNG 이미지로 변환

    Args:
        pdf_bytes: PDF 파일의 바이트 데이터
        dpi: 이미지 해상도 (기본 150)

    Returns:
        PNG 이미지의 바이트 데이터
    """
    try:
        logger.info(f"Converting PDF to image (DPI={dpi})")

        # PDF 열기
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")

        # 첫 페이지 가져오기
        page = pdf_document[0]

        # 이미지로 렌더링 (DPI 설정)
        zoom = dpi / 72  # 72 DPI가 기본값
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        # PIL Image로 변환
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # PNG로 저장
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        pdf_document.close()

        logger.info(f"PDF converted to image: {pix.width}x{pix.height}px")
        return img_byte_arr.getvalue()

    except Exception as e:
        logger.error(f"PDF to image conversion failed: {e}")
        raise HTTPException(status_code=500, detail=f"PDF conversion error: {str(e)}")


def calculate_bbox_iou(bbox1: Dict[str, int], bbox2: Dict[str, int]) -> float:
    """
    두 바운딩 박스의 IoU (Intersection over Union) 계산

    Args:
        bbox1, bbox2: {x, y, width, height} 형식의 바운딩 박스

    Returns:
        IoU 값 (0.0 ~ 1.0)
    """
    x1_1, y1_1 = bbox1['x'], bbox1['y']
    x2_1, y2_1 = x1_1 + bbox1['width'], y1_1 + bbox1['height']

    x1_2, y1_2 = bbox2['x'], bbox2['y']
    x2_2, y2_2 = x1_2 + bbox2['width'], y1_2 + bbox2['height']

    # Intersection
    x1_i = max(x1_1, x1_2)
    y1_i = max(y1_1, y1_2)
    x2_i = min(x2_1, x2_2)
    y2_i = min(y2_1, y2_2)

    if x2_i < x1_i or y2_i < y1_i:
        return 0.0

    intersection = (x2_i - x1_i) * (y2_i - y1_i)

    # Union
    area1 = bbox1['width'] * bbox1['height']
    area2 = bbox2['width'] * bbox2['height']
    union = area1 + area2 - intersection

    return intersection / union if union > 0 else 0.0


def format_class_name(class_name: str) -> str:
    """클래스명을 사람이 읽기 쉬운 형태로 변환"""
    return CLASS_DISPLAY_NAMES.get(class_name, class_name)


def redraw_yolo_visualization(image_bytes: bytes, detections: List[Dict]) -> str:
    """
    매칭된 검출 결과로 시각화 이미지 재생성

    Args:
        image_bytes: 원본 이미지 바이트
        detections: 검출 목록 (bbox, class_name, class_id, confidence, value 포함)

    Returns:
        Base64 인코딩된 시각화 이미지
    """
    # bytes → numpy array
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    annotated_img = image.copy()

    # 색상 정의 (BGR)
    colors = {
        'dimension': (255, 100, 0),     # Blue
        'gdt': (0, 255, 100),           # Green
        'surface': (0, 165, 255),       # Orange
        'text': (255, 255, 0)           # Cyan
    }

    for det in detections:
        bbox = det.get('bbox', {})
        x1 = bbox.get('x', 0)
        y1 = bbox.get('y', 0)
        x2 = x1 + bbox.get('width', 0)
        y2 = y1 + bbox.get('height', 0)

        class_id = det.get('class_id', 0)
        class_name = det.get('class_name', '')
        confidence = det.get('confidence', 0.0)
        value = det.get('value')

        # 색상 선택
        if class_id <= 6:
            color = colors['dimension']
        elif class_id <= 11:
            color = colors['gdt']
        elif class_id == 12:
            color = colors['surface']
        else:
            color = colors['text']

        # 박스 그리기
        cv2.rectangle(annotated_img, (x1, y1), (x2, y2), color, 2)

        # 라벨 그리기 (OCR 값 포함)
        display_name = format_class_name(class_name)
        if value:
            # OCR 값이 있으면 표시
            label = f"{display_name}: {value} ({confidence:.2f})"
        else:
            # OCR 값이 없으면 클래스명과 신뢰도만
            label = f"{display_name} ({confidence:.2f})"

        (label_w, label_h), _ = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
        )

        # 라벨 배경
        cv2.rectangle(
            annotated_img,
            (x1, y1 - label_h - 12),
            (x1 + label_w + 10, y1),
            color,
            -1
        )

        # 라벨 텍스트
        cv2.putText(
            annotated_img,
            label,
            (x1 + 5, y1 - 6),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

    # 범례(Legend) 추가
    legend_height = 140
    legend_width = 280
    legend_x = 10
    legend_y = 10

    # 범례 배경
    overlay = annotated_img.copy()
    cv2.rectangle(overlay, (legend_x, legend_y), (legend_x + legend_width, legend_y + legend_height), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.7, annotated_img, 0.3, 0, annotated_img)

    # 범례 테두리
    cv2.rectangle(annotated_img, (legend_x, legend_y), (legend_x + legend_width, legend_y + legend_height), (255, 255, 255), 2)

    # 범례 제목
    cv2.putText(annotated_img, "Detection Classes", (legend_x + 10, legend_y + 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # 범례 항목
    legend_items = [
        ("Dimensions", colors['dimension']),
        ("GD&T Symbols", colors['gdt']),
        ("Surface Roughness", colors['surface']),
        ("Text Blocks", colors['text'])
    ]

    y_offset = legend_y + 50
    for label, color in legend_items:
        # 색상 박스
        cv2.rectangle(annotated_img, (legend_x + 10, y_offset - 10), (legend_x + 30, y_offset + 5), color, -1)
        cv2.rectangle(annotated_img, (legend_x + 10, y_offset - 10), (legend_x + 30, y_offset + 5), (255, 255, 255), 1)
        # 라벨
        cv2.putText(annotated_img, label, (legend_x + 40, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        y_offset += 25

    # numpy array → Base64
    _, buffer = cv2.imencode('.jpg', annotated_img)
    img_base64 = base64.b64encode(buffer).decode('utf-8')

    return img_base64


def upscale_image_region(image_bytes: bytes, bbox: Dict[str, int], scale: int = 4) -> bytes:
    """
    이미지의 특정 영역을 확대

    Args:
        image_bytes: 원본 이미지 바이트
        bbox: 바운딩 박스 {x, y, width, height}
        scale: 확대 배율 (기본 4x)

    Returns:
        확대된 이미지 영역의 바이트
    """
    try:
        # bytes → PIL Image
        image = Image.open(io.BytesIO(image_bytes))

        # 영역 추출
        x = bbox['x']
        y = bbox['y']
        w = bbox['width']
        h = bbox['height']

        # 여백 추가 (10%)
        margin = int(min(w, h) * 0.1)
        x = max(0, x - margin)
        y = max(0, y - margin)
        w = min(image.width - x, w + 2 * margin)
        h = min(image.height - y, h + 2 * margin)

        # 크롭
        cropped = image.crop((x, y, x + w, y + h))

        # 확대 (Lanczos 리샘플링으로 고품질 유지)
        upscaled = cropped.resize(
            (w * scale, h * scale),
            Image.Resampling.LANCZOS
        )

        # PIL Image → bytes
        img_byte_arr = io.BytesIO()
        upscaled.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        logger.info(f"Upscaled region from {w}x{h} to {w*scale}x{h*scale}")
        return img_byte_arr.getvalue()

    except Exception as e:
        logger.error(f"Upscaling failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upscale error: {str(e)}")


def crop_bbox(
    image_bytes: bytes,
    bbox: Dict,
    padding: float = 0.1,
    min_size: int = 50,
    upscale_small: bool = True,
    upscale_factor: float = 2.0
) -> bytes:
    """
    YOLO bbox로 이미지 crop (패딩 추가, 최소 크기 보장, 작은 영역 upscaling)

    Args:
        image_bytes: 원본 이미지
        bbox: YOLO 바운딩 박스 {x, y, width, height}
        padding: crop 시 패딩 비율 (기본 10%)
        min_size: 최소 crop 크기 (픽셀, 기본 50)
        upscale_small: 작은 crop을 upscale할지 여부 (기본 True)
        upscale_factor: upscale 배율 (기본 2.0x)

    Returns:
        Crop된 이미지 바이트
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))

        x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']
        logger.info(f"Crop bbox: x={x}, y={y}, w={w}, h={h}, img_size=({image.width}, {image.height})")

        # bbox가 이미지 밖에 있는지 확인
        if x >= image.width or y >= image.height or x + w <= 0 or y + h <= 0:
            raise ValueError(f"BBox completely outside image bounds")

        # bbox를 이미지 경계 내로 클램핑
        x = max(0, min(x, image.width - 1))
        y = max(0, min(y, image.height - 1))
        w = max(1, min(w, image.width - x))
        h = max(1, min(h, image.height - y))

        # 패딩 추가
        padding_x = max(1, int(w * padding))
        padding_y = max(1, int(h * padding))

        # 좌표 계산 (패딩 포함, 이미지 경계 내로 클램핑)
        x1 = max(0, x - padding_x)
        y1 = max(0, y - padding_y)
        x2 = min(image.width, x + w + padding_x)
        y2 = min(image.height, y + h + padding_y)

        # 최소 크기 보장
        crop_width = x2 - x1
        crop_height = y2 - y1

        if crop_width < min_size:
            # 중심을 유지하면서 확장
            center_x = (x1 + x2) / 2
            x1 = max(0, int(center_x - min_size / 2))
            x2 = min(image.width, x1 + min_size)
            crop_width = x2 - x1

        if crop_height < min_size:
            center_y = (y1 + y2) / 2
            y1 = max(0, int(center_y - min_size / 2))
            y2 = min(image.height, y1 + min_size)
            crop_height = y2 - y1

        logger.info(f"Crop coords (clamped): ({x1}, {y1}, {x2}, {y2}), size: {crop_width}x{crop_height}")
        cropped = image.crop((x1, y1, x2, y2))

        # 작은 영역 upscaling (OCR 정확도 향상)
        if upscale_small and (crop_width < min_size * 2 or crop_height < min_size * 2):
            new_width = int(crop_width * upscale_factor)
            new_height = int(crop_height * upscale_factor)
            cropped = cropped.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.info(f"Upscaled small crop: {crop_width}x{crop_height} → {new_width}x{new_height}")

        # PIL Image → bytes
        img_byte_arr = io.BytesIO()
        cropped.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        return img_byte_arr.getvalue()

    except Exception as e:
        logger.error(f"Crop failed: {e}")
        raise HTTPException(status_code=500, detail=f"Crop error: {str(e)}")
