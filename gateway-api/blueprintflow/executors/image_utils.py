"""
Image Processing Utilities
이미지 입력 처리 및 변환을 위한 공통 유틸리티
"""
from typing import Dict, Any, Union
import base64
from io import BytesIO
from PIL import Image


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
