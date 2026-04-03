#!/usr/bin/env python3
"""S08 Cardinal Projection v3 — LSD 끝점 토폴로지 시각화.

2-2와 동일한 투사선을 사용하고, Method L의 핵심인 LSD 선분 끝점을
투사선 위 후보로 필터링해 문서용 이미지를 생성한다.
"""

import argparse

import cv2
import numpy as np

from s08_cardinal_v3_fullpage import (
    GT,
    SRC_DIR,
    add_header,
    build_auxiliary_lines,
    build_circle_lines,
    build_protrusion_lines,
    collect_projection_data,
    draw_projection_lines_only,
    save_pil,
)

ENDPOINT_TOLERANCE = 15
MIN_LINE_LENGTH = 30.0


def detect_lsd_segments(gray: np.ndarray) -> list[tuple[float, float, float, float, float]]:
    """Method L과 같은 방식으로 LSD 선분을 검출한다."""
    lsd = cv2.createLineSegmentDetector(0)
    lines, _, _, _ = lsd.detect(gray)
    if lines is None:
        return []

    result = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        length = float(np.hypot(x2 - x1, y2 - y1))
        if length >= MIN_LINE_LENGTH:
            result.append((float(x1), float(y1), float(x2), float(y2), length))
    return result


def extract_endpoints(
    segments: list[tuple[float, float, float, float, float]]
) -> list[dict[str, float | int]]:
    endpoints: list[dict[str, float | int]] = []
    for idx, (x1, y1, x2, y2, _) in enumerate(segments):
        endpoints.append({"segment_idx": idx, "x": float(x1), "y": float(y1)})
        endpoints.append({"segment_idx": idx, "x": float(x2), "y": float(y2)})
    return endpoints


def filter_endpoints_on_projections(
    endpoints: list[dict[str, float | int]],
    projection_lines: list[dict[str, object]],
    tolerance: int = ENDPOINT_TOLERANCE,
) -> list[dict[str, float | int]]:
    filtered: list[dict[str, float | int]] = []
    for endpoint in endpoints:
        px = float(endpoint["x"])
        py = float(endpoint["y"])
        match_count = 0
        for line in projection_lines:
            if line["axis"] == "h":
                distance = abs(py - float(line["py"]))
            else:
                distance = abs(px - float(line["px"]))
            if distance <= tolerance:
                match_count += 1
        if match_count:
            filtered.append({**endpoint, "match_count": match_count})
    return filtered


def draw_endpoint_overlay(
    img: np.ndarray,
    name: str,
    circles_full: list[tuple[float, float, float]],
    circle_lines: list[dict[str, object]],
    peaks_full: list[tuple[float, float, float, float]],
    protrusion_lines: list[dict[str, object]],
    auxiliary_lines: list[dict[str, object]],
    filtered_endpoints: list[dict[str, float | int]],
    segment_count: int,
    total_endpoints: int,
) -> None:
    base_pil = draw_projection_lines_only(
        img,
        circles_full,
        circle_lines,
        peaks_full,
        protrusion_lines,
        auxiliary_lines,
    )
    canvas = cv2.cvtColor(np.array(base_pil), cv2.COLOR_RGB2BGR)
    full_h, full_w = canvas.shape[:2]

    for endpoint in filtered_endpoints:
        center = (int(round(float(endpoint["x"]))), int(round(float(endpoint["y"]))))
        cv2.circle(canvas, center, 8, (255, 0, 0), -1)
        cv2.circle(canvas, center, 12, (255, 255, 255), 2)

    ratio = 0.0 if total_endpoints == 0 else len(filtered_endpoints) / total_endpoints * 100.0
    pil = add_header(
        canvas,
        f"{name.upper()} — L Endpoint Topology ({full_w}x{full_h})",
        (
            f"LSD 선분 {segment_count}개 | 전체 끝점 {total_endpoints}개 | "
            f"투사선 위 끝점 {len(filtered_endpoints)}개 ({ratio:.1f}%)"
        ),
        f"projection tolerance={ENDPOINT_TOLERANCE}px | blue dot = endpoint on projection",
    )
    save_pil(pil, f"{name}_endpoint_lines.jpg", max_w=1600)


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
    print("S08 Cardinal v3 — LSD endpoint topology")
    print("=" * 60)

    results = []
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

        data = collect_projection_data(gray)
        circles_full = data["circles_full"]
        peaks_full = data["peaks_full"]
        if not circles_full:
            print("  ⚠ 주 동심원 검출 실패")
            continue

        circle_lines = build_circle_lines(circles_full)
        protrusion_lines = build_protrusion_lines(
            peaks_full,
            data["center_full"],
            data["outer_r"],
        )
        auxiliary_lines = build_auxiliary_lines(
            data["auxiliary_rows"],
            data["center_full"],
        )
        projection_lines = circle_lines + protrusion_lines + auxiliary_lines

        segments = detect_lsd_segments(gray)
        endpoints = extract_endpoints(segments)
        filtered_endpoints = filter_endpoints_on_projections(
            endpoints,
            projection_lines,
        )

        print(
            f"  투사선 {len(projection_lines)}개 | "
            f"LSD 선분 {len(segments)}개 | "
            f"전체 끝점 {len(endpoints)}개 | "
            f"투사선 위 끝점 {len(filtered_endpoints)}개"
        )

        draw_endpoint_overlay(
            img,
            name,
            circles_full,
            circle_lines,
            peaks_full,
            protrusion_lines,
            auxiliary_lines,
            filtered_endpoints,
            len(segments),
            len(endpoints),
        )

        results.append(
            {
                "name": name.upper(),
                "segments": len(segments),
                "endpoints": len(endpoints),
                "on_projection": len(filtered_endpoints),
            }
        )

    if results:
        print("\nMarkdown stats")
        print("| 도면 | LSD 선분 수 | 전체 끝점 수 | 투사선 위 끝점 수 | 비율 |")
        print("|------|:---:|:---:|:---:|:---:|")
        for row in results:
            ratio = row["on_projection"] / row["endpoints"] * 100 if row["endpoints"] else 0.0
            print(
                f"| {row['name']} | {row['segments']}개 | {row['endpoints']}개 | "
                f"{row['on_projection']}개 | {ratio:.1f}% |"
            )


if __name__ == "__main__":
    run()
