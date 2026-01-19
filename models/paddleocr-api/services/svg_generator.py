"""
PaddleOCR SVG Generator

OCR 결과를 인터랙티브 SVG 오버레이로 변환
텍스트 검출 박스 시각화, 호버/클릭 이벤트 지원
"""

from typing import List, Dict, Any, Tuple, Optional


# 신뢰도 기반 색상 설정
CONFIDENCE_COLORS: Dict[str, str] = {
    "high": "#22c55e",       # 초록 (>=0.9)
    "medium": "#3b82f6",     # 파랑 (>=0.7)
    "low": "#f59e0b",        # 황색 (>=0.5)
    "very_low": "#ef4444",   # 빨강 (<0.5)
}


def get_confidence_color(confidence: float) -> str:
    """신뢰도에 따른 색상 반환"""
    if confidence >= 0.9:
        return CONFIDENCE_COLORS["high"]
    elif confidence >= 0.7:
        return CONFIDENCE_COLORS["medium"]
    elif confidence >= 0.5:
        return CONFIDENCE_COLORS["low"]
    else:
        return CONFIDENCE_COLORS["very_low"]


def generate_ocr_svg(
    detections: List[Dict[str, Any]],
    image_size: Tuple[int, int],
    show_labels: bool = True,
    show_confidence: bool = True,
    interactive: bool = True,
    stroke_width: int = 2,
    opacity: float = 0.8,
    color_by_confidence: bool = True,
    default_color: str = "#3b82f6",
) -> str:
    """
    OCR 검출 결과를 SVG 오버레이로 변환

    Args:
        detections: 검출 결과 리스트 [{text, confidence, bbox, ...}]
        image_size: (width, height) 이미지 크기
        show_labels: 텍스트 라벨 표시 여부
        show_confidence: 신뢰도 표시 여부
        interactive: 인터랙티브 기능 활성화
        stroke_width: 테두리 두께
        opacity: 투명도
        color_by_confidence: 신뢰도에 따른 색상 사용
        default_color: 기본 색상

    Returns:
        SVG 문자열
    """
    width, height = image_size

    # SVG 시작
    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" class="paddleocr-detection-overlay">'
    ]

    # 스타일 정의
    interactive_style = """
        .text-box:hover { stroke-width: 4; filter: brightness(1.2); }
        .text-box:hover + .text-label { display: block; }
        .text-box { cursor: pointer; }
    """ if interactive else ""

    svg_parts.append(f'''
    <defs>
        <style>
            .paddleocr-detection-overlay {{ pointer-events: none; }}
            .text-box {{
                fill: none;
                opacity: {opacity};
                pointer-events: auto;
            }}
            .text-box-filled {{
                opacity: 0.1;
                pointer-events: auto;
            }}
            .text-label {{
                font-family: 'Pretendard', Arial, sans-serif;
                font-size: 11px;
                fill: white;
                pointer-events: none;
            }}
            .text-label-bg {{
                opacity: 0.9;
            }}
            {interactive_style}
        </style>
    </defs>
    ''')

    # 검출 레이어
    svg_parts.append('<g class="detections-layer">')

    for i, det in enumerate(detections):
        # 검출 객체에서 데이터 추출
        if hasattr(det, 'text'):
            # TextDetection 객체인 경우
            text = det.text
            confidence = det.confidence
            bbox = det.bbox
        elif isinstance(det, dict):
            # 딕셔너리인 경우
            text = det.get("text", "")
            confidence = det.get("confidence", 0.0)
            bbox = det.get("bbox", [])
        else:
            continue

        # bbox 파싱
        parsed_bbox = _parse_bbox(bbox)
        if not parsed_bbox:
            continue

        x, y, w, h = parsed_bbox

        # 색상 결정
        if color_by_confidence:
            color = get_confidence_color(confidence)
        else:
            color = default_color

        # 박스 배경 (반투명)
        svg_parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
            f'class="text-box-filled" fill="{color}"/>'
        )

        # 박스 테두리
        escaped_text = _escape_html(str(text))
        svg_parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
            f'class="text-box" stroke="{color}" stroke-width="{stroke_width}" '
            f'data-id="{i}" data-text="{escaped_text}" '
            f'data-confidence="{confidence:.3f}"/>'
        )

        # 라벨
        if show_labels or show_confidence:
            label_text = ""
            if show_labels and text:
                # 텍스트가 너무 길면 자르기
                display_text = text[:25] + "..." if len(text) > 25 else text
                label_text = display_text
            if show_confidence:
                conf_text = f"{confidence*100:.0f}%"
                if label_text:
                    label_text += f" ({conf_text})"
                else:
                    label_text = conf_text

            if label_text:
                label_width = min(len(label_text) * 6 + 8, w + 40)
                label_height = 16
                label_y = max(0, y - label_height - 2)

                svg_parts.append(
                    f'<rect x="{x}" y="{label_y}" width="{label_width}" height="{label_height}" '
                    f'class="text-label-bg" fill="{color}" rx="2"/>'
                )
                svg_parts.append(
                    f'<text x="{x + 4}" y="{label_y + 12}" class="text-label">'
                    f'{_escape_html(label_text)}</text>'
                )

    svg_parts.append('</g>')

    # 범례 추가
    svg_parts.append(_generate_legend(width, height))

    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)


def _generate_legend(width: int, height: int) -> str:
    """범례 SVG 생성"""
    legend_x = width - 130
    legend_y = 10

    return f'''
    <g class="legend" transform="translate({legend_x}, {legend_y})">
        <rect x="0" y="0" width="120" height="80" fill="white" fill-opacity="0.9" rx="4" stroke="#e5e7eb"/>
        <text x="10" y="16" font-size="10" font-weight="bold" fill="#374151">Confidence</text>
        <rect x="10" y="24" width="12" height="12" fill="{CONFIDENCE_COLORS['high']}"/>
        <text x="26" y="34" font-size="9" fill="#374151">High (≥90%)</text>
        <rect x="10" y="40" width="12" height="12" fill="{CONFIDENCE_COLORS['medium']}"/>
        <text x="26" y="50" font-size="9" fill="#374151">Medium (≥70%)</text>
        <rect x="10" y="56" width="12" height="12" fill="{CONFIDENCE_COLORS['low']}"/>
        <text x="26" y="66" font-size="9" fill="#374151">Low (≥50%)</text>
    </g>
    '''


def _parse_bbox(bbox: Any) -> Optional[Tuple[float, float, float, float]]:
    """
    다양한 bbox 형식을 (x, y, width, height)로 변환

    지원 형식:
    - [[x1,y1], [x2,y2], [x3,y3], [x4,y4]] - 4점 폴리곤
    - [x1, y1, x2, y2] - 2점 좌표
    - {"x": x, "y": y, "width": w, "height": h} - 딕셔너리
    """
    if not bbox:
        return None

    try:
        # 딕셔너리 형식
        if isinstance(bbox, dict):
            return (
                float(bbox.get("x", 0)),
                float(bbox.get("y", 0)),
                float(bbox.get("width", 0)),
                float(bbox.get("height", 0))
            )

        # 리스트 형식
        if isinstance(bbox, (list, tuple)):
            # numpy array 처리
            if hasattr(bbox, 'tolist'):
                bbox = bbox.tolist()

            # 4점 폴리곤: [[x1,y1], [x2,y2], ...]
            if len(bbox) >= 4 and isinstance(bbox[0], (list, tuple)):
                xs = [float(p[0]) for p in bbox]
                ys = [float(p[1]) for p in bbox]
                x_min, x_max = min(xs), max(xs)
                y_min, y_max = min(ys), max(ys)
                return (x_min, y_min, x_max - x_min, y_max - y_min)

            # 2점 좌표 또는 xywh: [x1, y1, x2, y2] or [x, y, w, h]
            if len(bbox) >= 4:
                # 4점 좌표 평탄화된 형식
                x1, y1, x2, y2 = float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])
                # x2, y2가 x1, y1보다 작으면 w,h 형식
                if x2 < x1 or y2 < y1:
                    return (x1, y1, x2, y2)
                return (min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))

    except (TypeError, ValueError, IndexError):
        pass

    return None


def generate_ocr_svg_minimal(
    detections: List[Dict[str, Any]],
    image_size: Tuple[int, int],
) -> str:
    """최소한의 SVG 생성 (라벨 없음, 박스만)"""
    return generate_ocr_svg(
        detections, image_size,
        show_labels=False, show_confidence=False, interactive=False,
        stroke_width=1, opacity=0.6, color_by_confidence=True
    ).replace(_generate_legend(image_size[0], image_size[1]), '')


def ocr_to_svg_data(
    detections: List[Dict[str, Any]],
    image_size: Tuple[int, int],
) -> Dict[str, Any]:
    """
    OCR 결과를 SVG 데이터 딕셔너리로 변환

    Args:
        detections: 검출 결과 리스트
        image_size: (width, height)

    Returns:
        SVG 데이터 딕셔너리
    """
    return {
        "svg": generate_ocr_svg(detections, image_size),
        "svg_minimal": generate_ocr_svg_minimal(detections, image_size),
        "width": image_size[0],
        "height": image_size[1],
        "detection_count": len(detections),
    }


def _escape_html(text: str) -> str:
    """HTML 특수문자 이스케이프"""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#039;")
    )
