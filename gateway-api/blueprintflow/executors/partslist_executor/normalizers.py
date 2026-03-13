"""
Parts List 정규화 유틸리티
헤더 정규화, 재질 코드 정규화, 수량 파싱, 이미지 크롭
"""
import io
import re
from typing import TYPE_CHECKING

from .constants import HEADER_ALIASES, MATERIAL_NORMALIZATION, POSITION_PRESETS


def normalize_header(header: str) -> str:
    """헤더를 표준 이름으로 정규화"""
    header_upper = header.upper().strip()

    for standard, aliases in HEADER_ALIASES.items():
        if header_upper in [a.upper() for a in aliases]:
            return standard

    # 부분 매칭 시도
    for standard, aliases in HEADER_ALIASES.items():
        for alias in aliases:
            if alias.upper() in header_upper or header_upper in alias.upper():
                return standard

    return header.lower().replace(" ", "_").replace("'", "")


def normalize_material(material: str) -> str:
    """재질 코드 정규화"""
    if not material:
        return material

    upper = material.upper().strip()

    # 정규화 매핑 확인
    for key, normalized in MATERIAL_NORMALIZATION.items():
        if key.upper() == upper or key.upper() in upper:
            return normalized

    # 패턴 기반 정규화
    # SF 패턴
    sf_match = re.match(r"SF[- ]?(\d+)[- ]?([A-Z])?", upper)
    if sf_match:
        num = sf_match.group(1)
        grade = sf_match.group(2) or "A"
        return f"SF{num}{grade}"

    # SS 패턴
    ss_match = re.match(r"SS[- ]?(\d+)", upper)
    if ss_match:
        return f"SS{ss_match.group(1)}"

    # SM 패턴
    sm_match = re.match(r"SM[- ]?(\d+)[- ]?([A-Z])?", upper)
    if sm_match:
        num = sm_match.group(1)
        grade = sm_match.group(2) or "A"
        return f"SM{num}{grade}"

    return upper


def parse_quantity(qty_str: str) -> int:
    """수량 문자열을 숫자로 변환"""
    if not qty_str:
        return 1

    # 숫자만 추출
    numbers = re.findall(r"\d+", str(qty_str))
    if numbers:
        return int(numbers[0])
    return 1


def crop_image(file_bytes: bytes, position: str) -> bytes:
    """Parts List 위치 기반 이미지 크롭"""
    from PIL import Image

    if position not in POSITION_PRESETS or position == "full":
        return file_bytes

    x1_ratio, y1_ratio, x2_ratio, y2_ratio = POSITION_PRESETS[position]

    img = Image.open(io.BytesIO(file_bytes))
    w, h = img.size

    x1 = int(w * x1_ratio)
    y1 = int(h * y1_ratio)
    x2 = int(w * x2_ratio)
    y2 = int(h * y2_ratio)

    cropped = img.crop((x1, y1, x2, y2))

    output = io.BytesIO()
    cropped.save(output, format="PNG")
    return output.getvalue()
