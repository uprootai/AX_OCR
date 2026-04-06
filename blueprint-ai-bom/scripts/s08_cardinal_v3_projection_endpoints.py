#!/usr/bin/env python3
"""S08 Cardinal Projection v3 — OCR 매칭용 투사선 + LSD 끝점 시각화.

2-5 문서용 산출물:
1. Cardinal v3의 투사선(시안/노랑/보라)만 유지
2. LSD 끝점 중 투사선과 만나는 점만 파란 점으로 표시
3. 화살촉, 치수선 쌍, 원/seed 마커 같은 다른 오버레이는 제거
"""

from __future__ import annotations

import argparse
from typing import Any

import cv2
import numpy as np
from PIL import Image

from cardinal_common import (
    build_auxiliary_lines,
    build_circle_lines,
    build_protrusion_lines,
    collect_projection_data,
    save_pil,
)
from s08_cardinal_v3_endpoint_lines import (
    ENDPOINT_TOLERANCE,
    detect_lsd_segments,
    extract_endpoints,
    filter_endpoints_on_projections,
)
from s08_cardinal_v3_fullpage import (
    GT,
    SRC_DIR,
)

HORIZONTAL_COLOR = (255, 255, 0)
VERTICAL_COLOR = (0, 255, 255)
PROTRUSION_COLOR = (255, 0, 200)
ENDPOINT_COLOR = (255, 0, 0)
ENDPOINT_RADIUS = 6
MAX_OUTPUT_WIDTH = 1600


def draw_projection_line(
    canvas: np.ndarray,
    line: dict[str, Any],
    full_w: int,
    full_h: int,
    color: tuple[int, int, int],
) -> None:
    """투사선 하나를 전체 도면에 그린다."""
    if line["axis"] == "h":
        cv2.line(canvas, (0, int(line["py"])), (full_w, int(line["py"])), color, 2)
        return
    cv2.line(canvas, (int(line["px"]), 0), (int(line["px"]), full_h), color, 2)


def draw_projection_endpoint_overlay(
    img: np.ndarray,
    circle_lines: list[dict[str, Any]],
    protrusion_lines: list[dict[str, Any]],
    auxiliary_lines: list[dict[str, Any]],
    filtered_endpoints: list[dict[str, float | int]],
) -> Image.Image:
    """원본 도면 위에 투사선과 투사선 위 LSD 끝점만 그린다."""
    canvas = img.copy()
    full_h, full_w = canvas.shape[:2]

    for line in circle_lines:
        color = HORIZONTAL_COLOR if line["axis"] == "h" else VERTICAL_COLOR
        draw_projection_line(canvas, line, full_w, full_h, color)

    for line in protrusion_lines:
        draw_projection_line(canvas, line, full_w, full_h, PROTRUSION_COLOR)

    for line in auxiliary_lines:
        draw_projection_line(canvas, line, full_w, full_h, tuple(line.get("color", HORIZONTAL_COLOR)))

    for endpoint in filtered_endpoints:
        center = (
            int(round(float(endpoint["x"]))),
            int(round(float(endpoint["y"]))),
        )
        cv2.circle(canvas, center, ENDPOINT_RADIUS, ENDPOINT_COLOR, -1)

    return Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--doc",
        choices=[gt["name"] for gt in GT.values()],
        help="특정 도면만 처리",
    )
    return parser.parse_args()


def run() -> None:
    args = parse_args()
    print("S08 Cardinal v3 — projection endpoints for OCR")
    print("=" * 60)

    targets = [
        (doc_id, gt)
        for doc_id, gt in GT.items()
        if args.doc is None or gt["name"] == args.doc
    ]

    for doc_id, gt in targets:
        name = gt["name"]
        img_path = SRC_DIR / f"{doc_id}.png"
        if not img_path.exists():
            print(f"⚠ {name}: {img_path} 없음")
            continue

        print(f"\n{name.upper()} — {doc_id}")
        img = cv2.imread(str(img_path))
        gray = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
        if img is None or gray is None:
            print(f"  ⚠ 이미지 로드 실패: {img_path}")
            continue

        data = collect_projection_data(gray, image_path=img_path)
        circles_full = data["circles_full"]
        if not circles_full:
            print("  ⚠ 주 동심원 검출 실패")
            continue

        circle_lines = build_circle_lines(circles_full)
        protrusion_lines = build_protrusion_lines(
            data["peaks_full"],
            data["center_full"],
            data["outer_r"],
        )
        auxiliary_lines = build_auxiliary_lines(
            data["auxiliary_rows"],
            data["center_full"],
            data["section_vertical_cols"],
            data["section_horizontal_rows"],
            data["section_bounds"],
        )
        projection_lines = circle_lines + protrusion_lines + auxiliary_lines

        segments = detect_lsd_segments(gray)
        endpoints = extract_endpoints(segments)
        filtered_endpoints = filter_endpoints_on_projections(
            endpoints,
            projection_lines,
            tolerance=ENDPOINT_TOLERANCE,
        )

        pil = draw_projection_endpoint_overlay(
            img,
            circle_lines,
            protrusion_lines,
            auxiliary_lines,
            filtered_endpoints,
        )
        save_pil(
            pil,
            f"{name}_projection_endpoints.jpg",
            max_w=MAX_OUTPUT_WIDTH,
            show_size=True,
        )

        print(
            f"  투사선 {len(projection_lines)}개 | "
            f"LSD 선분 {len(segments)}개 | "
            f"전체 끝점 {len(endpoints)}개 | "
            f"투사선 위 끝점 {len(filtered_endpoints)}개 | "
            f"tolerance={ENDPOINT_TOLERANCE}px"
        )


if __name__ == "__main__":
    run()
