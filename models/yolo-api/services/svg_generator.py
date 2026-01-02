"""
YOLO Detection SVG Generator

검출 결과를 인터랙티브 SVG 오버레이로 변환
프론트엔드에서 호버, 클릭 이벤트 지원
"""

from typing import List, Dict, Any, Tuple, Optional


# 모델별 기본 색상 설정
MODEL_COLORS: Dict[str, str] = {
    "engineering": "#3b82f6",      # 파랑 - 기계도면
    "pid_symbol": "#10b981",       # 초록 - P&ID 심볼
    "pid_class_aware": "#10b981",  # 초록 - P&ID 분류
    "pid_class_agnostic": "#6366f1",  # 인디고 - P&ID 범용
    "bom_detector": "#f59e0b",     # 황색 - 전력 설비
}

# 클래스별 색상 (engineering 모델용)
CLASS_COLORS: Dict[str, str] = {
    "dimension_line": "#ef4444",     # 빨강
    "center_line": "#3b82f6",        # 파랑
    "weld_symbol": "#f59e0b",        # 황색
    "surface_finish": "#8b5cf6",     # 보라
    "tolerance_frame": "#10b981",    # 초록
    "datum_target": "#ec4899",       # 핑크
    "section_line": "#06b6d4",       # 청록
    "hidden_line": "#6b7280",        # 회색
    "leader_line": "#84cc16",        # 라임
    "extension_line": "#14b8a6",     # 틸
    "break_line": "#f97316",         # 오렌지
    "cutting_plane": "#dc2626",      # 진빨강
    "phantom_line": "#a855f7",       # 퍼플
    "chain_line": "#0ea5e9",         # 스카이
}


def generate_detection_svg(
    detections: List[Dict[str, Any]],
    image_size: Tuple[int, int],
    model_type: str = "engineering",
    show_labels: bool = True,
    show_confidence: bool = True,
    interactive: bool = True,
    stroke_width: int = 2,
    opacity: float = 0.8,
) -> str:
    """
    검출 결과를 SVG 오버레이로 변환

    Args:
        detections: 검출 결과 리스트 [{class_id, class_name, confidence, bbox}]
        image_size: (width, height) 이미지 크기
        model_type: 모델 타입 (색상 결정용)
        show_labels: 라벨 표시 여부
        show_confidence: 신뢰도 표시 여부
        interactive: 인터랙티브 기능 활성화
        stroke_width: 테두리 두께
        opacity: 투명도

    Returns:
        SVG 문자열
    """
    width, height = image_size
    default_color = MODEL_COLORS.get(model_type, "#3b82f6")

    # SVG 시작
    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" class="yolo-detection-overlay">'
    ]

    # 스타일 정의
    interactive_style = """
        .detection-box:hover { stroke-width: 4; filter: brightness(1.2); }
        .detection-box:hover + .detection-label { display: block; }
        .detection-box { cursor: pointer; }
    """ if interactive else ""

    svg_parts.append(f'''
    <defs>
        <style>
            .yolo-detection-overlay {{ pointer-events: none; }}
            .detection-box {{
                fill: none;
                opacity: {opacity};
                pointer-events: auto;
            }}
            .detection-label {{
                font-family: 'Pretendard', Arial, sans-serif;
                font-size: 12px;
                fill: white;
                pointer-events: none;
            }}
            .detection-label-bg {{
                opacity: 0.85;
            }}
            {interactive_style}
        </style>
    </defs>
    ''')

    # 검출 박스 그리기
    svg_parts.append('<g class="detections-layer">')

    for i, det in enumerate(detections):
        bbox = det.get("bbox", {})
        x = bbox.get("x", 0)
        y = bbox.get("y", 0)
        w = bbox.get("width", 0)
        h = bbox.get("height", 0)

        class_name = det.get("class_name", "unknown")
        class_id = det.get("class_id", 0)
        confidence = det.get("confidence", 0)

        # 클래스별 색상 또는 모델 기본 색상
        color = CLASS_COLORS.get(class_name, default_color)

        # 검출 박스
        svg_parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
            f'class="detection-box" '
            f'stroke="{color}" stroke-width="{stroke_width}" '
            f'data-id="{i}" data-class-id="{class_id}" '
            f'data-class-name="{class_name}" data-confidence="{confidence:.3f}"/>'
        )

        # 라벨 표시
        if show_labels:
            label_text = class_name
            if show_confidence:
                label_text += f" ({confidence*100:.1f}%)"

            label_width = len(label_text) * 7 + 8
            label_height = 18
            label_y = max(0, y - label_height - 2)

            # 라벨 배경
            svg_parts.append(
                f'<rect x="{x}" y="{label_y}" width="{label_width}" height="{label_height}" '
                f'class="detection-label-bg" fill="{color}" rx="2"/>'
            )

            # 라벨 텍스트
            svg_parts.append(
                f'<text x="{x + 4}" y="{label_y + 13}" class="detection-label">'
                f'{_escape_html(label_text)}</text>'
            )

    svg_parts.append('</g>')
    svg_parts.append('</svg>')

    return '\n'.join(svg_parts)


def generate_detection_svg_minimal(
    detections: List[Dict[str, Any]],
    image_size: Tuple[int, int],
    color: str = "#3b82f6",
) -> str:
    """
    최소한의 SVG 생성 (라벨 없음, 박스만)

    Args:
        detections: 검출 결과 리스트
        image_size: (width, height)
        color: 박스 색상

    Returns:
        SVG 문자열
    """
    width, height = image_size

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">'
    ]

    for det in detections:
        bbox = det.get("bbox", {})
        x = bbox.get("x", 0)
        y = bbox.get("y", 0)
        w = bbox.get("width", 0)
        h = bbox.get("height", 0)

        svg_parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
            f'fill="none" stroke="{color}" stroke-width="2"/>'
        )

    svg_parts.append('</svg>')

    return '\n'.join(svg_parts)


def detections_to_svg_data(
    detections: List[Dict[str, Any]],
    image_size: Tuple[int, int],
    model_type: str = "engineering",
) -> Dict[str, Any]:
    """
    검출 결과를 SVG 데이터 딕셔너리로 변환

    Args:
        detections: 검출 결과 리스트
        image_size: (width, height)
        model_type: 모델 타입

    Returns:
        SVG 데이터 딕셔너리
    """
    return {
        "svg": generate_detection_svg(detections, image_size, model_type),
        "svg_minimal": generate_detection_svg_minimal(
            detections, image_size, MODEL_COLORS.get(model_type, "#3b82f6")
        ),
        "width": image_size[0],
        "height": image_size[1],
        "detection_count": len(detections),
        "model_type": model_type,
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
