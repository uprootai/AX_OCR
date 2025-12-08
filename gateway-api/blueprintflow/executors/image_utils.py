"""
Image Processing Utilities
이미지 입력 처리 및 변환을 위한 공통 유틸리티
"""
from typing import Dict, Any, Union, List, Tuple, Optional
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import logging

logger = logging.getLogger(__name__)


def extract_image_input(inputs: Dict[str, Any], context: Dict[str, Any]) -> Union[str, bytes, Image.Image]:
    """
    입력 또는 컨텍스트에서 이미지 추출

    Args:
        inputs: 노드 입력 딕셔너리
        context: 실행 컨텍스트

    Returns:
        이미지 데이터 (base64 문자열, bytes, 또는 PIL Image)

    Raises:
        ValueError: 이미지 입력이 없는 경우
    """
    image_input = inputs.get("image") or context.get("inputs", {}).get("image")

    if not image_input:
        raise ValueError("image 입력이 필요합니다")

    return image_input


def decode_base64_image(image_input: Union[str, bytes, Image.Image]) -> bytes:
    """
    Base64 문자열을 bytes로 디코딩

    Args:
        image_input: base64 문자열, bytes, 또는 PIL Image

    Returns:
        이미지 바이트 데이터

    Raises:
        ValueError: 지원하지 않는 이미지 형식
    """
    if isinstance(image_input, str):
        # Data URL prefix 제거 (data:image/png;base64, 등)
        if image_input.startswith('data:'):
            # "data:image/png;base64,..." -> "..." 추출
            if ',' in image_input:
                image_input = image_input.split(',', 1)[1]

        # Base64 디코딩
        return base64.b64decode(image_input)
    elif isinstance(image_input, bytes):
        return image_input
    elif isinstance(image_input, Image.Image):
        # PIL Image를 bytes로 변환
        buffer = BytesIO()
        image_input.save(buffer, format="JPEG")
        return buffer.getvalue()
    else:
        raise ValueError(f"지원하지 않는 이미지 형식: {type(image_input)}")


def decode_to_pil_image(image_input: Union[str, bytes, Image.Image]) -> Image.Image:
    """
    입력을 PIL Image로 변환

    Args:
        image_input: base64 문자열, bytes, 또는 PIL Image

    Returns:
        PIL Image 객체

    Raises:
        ValueError: 지원하지 않는 이미지 형식
    """
    if isinstance(image_input, Image.Image):
        return image_input

    # bytes로 변환 후 PIL Image로 디코딩
    file_bytes = decode_base64_image(image_input)
    return Image.open(BytesIO(file_bytes))


def prepare_image_for_api(
    inputs: Dict[str, Any],
    context: Dict[str, Any]
) -> bytes:
    """
    API 호출을 위한 이미지 준비 (원스톱 헬퍼)

    입력 추출 → bytes 변환을 한 번에 수행

    Args:
        inputs: 노드 입력 딕셔너리
        context: 실행 컨텍스트

    Returns:
        API 호출용 이미지 바이트 데이터
    """
    image_input = extract_image_input(inputs, context)
    return decode_base64_image(image_input)


def draw_ocr_visualization(
    image_input: Union[str, bytes, Image.Image],
    ocr_results: List[Dict[str, Any]],
    box_color: Tuple[int, int, int] = (0, 255, 0),
    text_color: Tuple[int, int, int] = (255, 0, 0),
    box_width: int = 2,
    font_size: int = 12,
    show_confidence: bool = True
) -> str:
    """
    OCR 결과를 이미지에 시각화하여 Base64로 반환

    Args:
        image_input: 원본 이미지 (base64, bytes, PIL Image)
        ocr_results: OCR 결과 리스트, 각 항목은 다음 형식:
            - text: 인식된 텍스트
            - bbox 또는 bounding_box: [x1, y1, x2, y2] 또는 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            - confidence: 신뢰도 (0~1 또는 0~100)
        box_color: 바운딩 박스 색상 (R, G, B)
        text_color: 텍스트 색상 (R, G, B)
        box_width: 바운딩 박스 선 두께
        font_size: 텍스트 크기
        show_confidence: 신뢰도 표시 여부

    Returns:
        시각화된 이미지의 Base64 문자열
    """
    # PIL Image로 변환
    img = decode_to_pil_image(image_input)

    # RGB 모드 확인
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # 이미지 크기 (정규화 좌표 변환에 필요)
    img_width, img_height = img.size

    draw = ImageDraw.Draw(img)

    # 기본 폰트 사용 (시스템 폰트 로드 시도)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
    except (OSError, IOError):
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except (OSError, IOError):
            font = ImageFont.load_default()

    for result in ocr_results:
        text = result.get('text', '')
        if not text:
            continue

        # 바운딩 박스 추출 (다양한 형식 지원, 이미지 크기 전달)
        bbox = _extract_bbox(result, img_width, img_height)
        if bbox is None:
            continue

        # 바운딩 박스 그리기
        x1, y1, x2, y2 = bbox
        draw.rectangle([x1, y1, x2, y2], outline=box_color, width=box_width)

        # 텍스트 라벨 준비
        confidence = result.get('confidence', result.get('score', None))
        if show_confidence and confidence is not None:
            # 신뢰도가 0~1 범위면 퍼센트로 변환
            if isinstance(confidence, float) and confidence <= 1:
                confidence = confidence * 100
            label = f"{text} ({confidence:.0f}%)"
        else:
            label = text

        # 텍스트 배경 박스
        text_bbox = draw.textbbox((x1, y1 - font_size - 4), label, font=font)
        draw.rectangle(text_bbox, fill=(255, 255, 255, 200))

        # 텍스트 그리기
        draw.text((x1, y1 - font_size - 4), label, fill=text_color, font=font)

    # Base64로 인코딩
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=95)
    buffer.seek(0)

    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def _extract_bbox(
    result: Dict[str, Any],
    img_width: int = 1,
    img_height: int = 1
) -> Optional[Tuple[int, int, int, int]]:
    """
    다양한 OCR 결과 형식에서 바운딩 박스 추출

    지원 형식:
    - bbox: [x1, y1, x2, y2] (픽셀 또는 정규화 좌표)
    - bbox: [[x1,y1], [x2,y2]] (DocTR 정규화 좌표)
    - bounding_box: [x1, y1, x2, y2]
    - box: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]] (4점 폴리곤)
    - coordinates: {x, y, width, height}
    - left, top, width, height (Tesseract 형식)

    Args:
        result: OCR 결과 딕셔너리
        img_width: 이미지 너비 (정규화 좌표 변환에 사용)
        img_height: 이미지 높이 (정규화 좌표 변환에 사용)

    Returns:
        (x1, y1, x2, y2) 튜플 또는 None
    """
    # bbox 또는 bounding_box 형식
    bbox = result.get('bbox') or result.get('bounding_box')
    if bbox:
        # DocTR 형식: [[x1, y1], [x2, y2]] (정규화 좌표 0~1)
        if len(bbox) == 2 and isinstance(bbox[0], (list, tuple)) and len(bbox[0]) == 2:
            x1, y1 = bbox[0]
            x2, y2 = bbox[1]
            # 정규화 좌표인지 확인 (모든 값이 0~1 사이)
            if all(0 <= v <= 1 for v in [x1, y1, x2, y2]):
                return (
                    int(x1 * img_width),
                    int(y1 * img_height),
                    int(x2 * img_width),
                    int(y2 * img_height)
                )
            else:
                return (int(x1), int(y1), int(x2), int(y2))

        # 표준 형식: [x1, y1, x2, y2]
        if len(bbox) == 4 and all(isinstance(x, (int, float)) for x in bbox):
            x1, y1, x2, y2 = bbox
            # 정규화 좌표인지 확인 (모든 값이 0~1 사이)
            if all(0 <= v <= 1 for v in bbox):
                return (
                    int(x1 * img_width),
                    int(y1 * img_height),
                    int(x2 * img_width),
                    int(y2 * img_height)
                )
            return tuple(map(int, bbox))

        # 4점 폴리곤 형식: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        elif len(bbox) == 4 and isinstance(bbox[0], (list, tuple)):
            xs = [p[0] for p in bbox]
            ys = [p[1] for p in bbox]
            # 정규화 좌표인지 확인
            if all(0 <= v <= 1 for v in xs + ys):
                return (
                    int(min(xs) * img_width),
                    int(min(ys) * img_height),
                    int(max(xs) * img_width),
                    int(max(ys) * img_height)
                )
            return (int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys)))

    # box 형식 (4점 폴리곤)
    box = result.get('box')
    if box and len(box) == 4:
        if isinstance(box[0], (list, tuple)):
            xs = [p[0] for p in box]
            ys = [p[1] for p in box]
            # 정규화 좌표인지 확인
            if all(0 <= v <= 1 for v in xs + ys):
                return (
                    int(min(xs) * img_width),
                    int(min(ys) * img_height),
                    int(max(xs) * img_width),
                    int(max(ys) * img_height)
                )
            return (int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys)))

    # coordinates 형식
    coords = result.get('coordinates')
    if coords and all(k in coords for k in ['x', 'y', 'width', 'height']):
        x, y = coords['x'], coords['y']
        w, h = coords['width'], coords['height']
        return (int(x), int(y), int(x + w), int(y + h))

    # Tesseract 형식 (left, top, width, height)
    if all(k in result for k in ['left', 'top', 'width', 'height']):
        x, y = result['left'], result['top']
        w, h = result['width'], result['height']
        return (int(x), int(y), int(x + w), int(y + h))

    return None


def normalize_ocr_results(
    raw_results: Any,
    source: str = "unknown"
) -> List[Dict[str, Any]]:
    """
    다양한 OCR API 응답을 표준 형식으로 정규화

    Args:
        raw_results: OCR API의 원본 응답
        source: OCR 소스 ('tesseract', 'trocr', 'doctr', 'easyocr', 'ensemble')

    Returns:
        정규화된 OCR 결과 리스트:
        [{"text": str, "bbox": [x1,y1,x2,y2], "confidence": float}, ...]
    """
    normalized = []

    if not raw_results:
        return normalized

    # 결과가 리스트인 경우
    if isinstance(raw_results, list):
        for item in raw_results:
            if isinstance(item, dict):
                entry = _normalize_single_result(item, source)
                if entry:
                    normalized.append(entry)
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                # EasyOCR 형식: (bbox, text, confidence)
                entry = _normalize_easyocr_tuple(item)
                if entry:
                    normalized.append(entry)

    # 결과가 딕셔너리인 경우 (중첩된 구조)
    elif isinstance(raw_results, dict):
        # Tesseract 형식: {"text": [...], "left": [...], ...}
        if 'text' in raw_results and isinstance(raw_results.get('text'), list):
            normalized = _normalize_tesseract_dict(raw_results)
        # words/detections 키가 있는 경우
        elif 'words' in raw_results:
            return normalize_ocr_results(raw_results['words'], source)
        elif 'detections' in raw_results:
            return normalize_ocr_results(raw_results['detections'], source)
        elif 'results' in raw_results:
            return normalize_ocr_results(raw_results['results'], source)
        else:
            # 단일 결과
            entry = _normalize_single_result(raw_results, source)
            if entry:
                normalized.append(entry)

    return normalized


def _normalize_single_result(item: Dict[str, Any], source: str) -> Optional[Dict[str, Any]]:
    """단일 OCR 결과 정규화"""
    text = item.get('text', item.get('word', item.get('value', '')))
    if not text or not str(text).strip():
        return None

    bbox = _extract_bbox(item)
    confidence = item.get('confidence', item.get('score', item.get('conf', 0)))

    # 신뢰도 정규화 (0~1 범위로)
    if isinstance(confidence, (int, float)):
        if confidence > 1:
            confidence = confidence / 100
    else:
        confidence = 0

    return {
        'text': str(text).strip(),
        'bbox': list(bbox) if bbox else None,
        'confidence': float(confidence)
    }


def _normalize_easyocr_tuple(item: tuple) -> Optional[Dict[str, Any]]:
    """EasyOCR 튜플 형식 정규화: (bbox, text, confidence)"""
    if len(item) < 2:
        return None

    bbox_raw, text = item[0], item[1]
    confidence = item[2] if len(item) > 2 else 0

    if not text or not str(text).strip():
        return None

    # bbox 변환
    bbox = None
    if isinstance(bbox_raw, (list, tuple)) and len(bbox_raw) == 4:
        if isinstance(bbox_raw[0], (list, tuple)):
            xs = [p[0] for p in bbox_raw]
            ys = [p[1] for p in bbox_raw]
            bbox = [int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))]
        else:
            bbox = list(map(int, bbox_raw))

    return {
        'text': str(text).strip(),
        'bbox': bbox,
        'confidence': float(confidence) if confidence <= 1 else float(confidence) / 100
    }


def _normalize_tesseract_dict(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Tesseract 딕셔너리 형식 정규화"""
    normalized = []

    texts = raw.get('text', [])
    lefts = raw.get('left', [])
    tops = raw.get('top', [])
    widths = raw.get('width', [])
    heights = raw.get('height', [])
    confs = raw.get('conf', raw.get('confidence', []))

    for i in range(len(texts)):
        text = texts[i] if i < len(texts) else ''
        if not text or not str(text).strip():
            continue

        left = lefts[i] if i < len(lefts) else 0
        top = tops[i] if i < len(tops) else 0
        width = widths[i] if i < len(widths) else 0
        height = heights[i] if i < len(heights) else 0
        conf = confs[i] if i < len(confs) else 0

        # 신뢰도 정규화
        if isinstance(conf, (int, float)):
            if conf > 1:
                conf = conf / 100
        else:
            conf = 0

        normalized.append({
            'text': str(text).strip(),
            'bbox': [int(left), int(top), int(left + width), int(top + height)],
            'confidence': float(conf)
        })

    return normalized
