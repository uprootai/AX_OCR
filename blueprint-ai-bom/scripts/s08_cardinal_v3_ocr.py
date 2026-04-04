#!/usr/bin/env python3
"""S08 Cardinal Projection v3 - Line Detector overlay for sections 2-6/2-7."""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import requests
from PIL import Image

from s08_cardinal_v3_endpoint_lines import (
    ENDPOINT_TOLERANCE,
    detect_lsd_segments,
    extract_endpoints,
    filter_endpoints_on_projections,
)
from s08_cardinal_v3_fullpage import (
    GT,
    SRC_DIR,
    build_auxiliary_lines,
    build_circle_lines,
    build_protrusion_lines,
    collect_projection_data,
    save_pil,
)
from s08_cardinal_v3_projection_endpoints import draw_projection_endpoint_overlay

OUT_DIR = Path("/home/uproot/ax/poc/docs-site-starlight/public/images/gt-validation/steps")
OUT_DIR.mkdir(exist_ok=True)

LINE_API = "http://localhost:5016/api/v1/process"
OCR_API = "http://localhost:5006/api/v1/ocr"

LINE_MIN_LENGTH = 20
LINE_MAX_LINES = 2000
LINE_CONNECTION_RADIUS = 40.0
OCR_SEARCH_RADIUS = 150.0
PROJECTION_AXIS_TOLERANCE = 30.0
LINE_KEY_COORD_BIN = 10.0
LINE_KEY_SPAN_BIN = 20.0

CONNECTED_LINE_COLOR = (0, 128, 255)
PAIR_LINE_COLOR = (0, 0, 255)
CONNECTED_LINE_THICKNESS = 5
PAIR_LINE_THICKNESS = 7
OCR_BOX_COLOR = (255, 255, 255)
OCR_TEXT_COLOR = (40, 255, 40)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--doc",
        choices=[gt["name"] for gt in GT.values()],
        help="process one drawing only",
    )
    parser.add_argument(
        "--no-ocr",
        action="store_true",
        help="skip OCR matching and render connected lines only",
    )
    return parser.parse_args()


def squared_distance(point_a: tuple[float, float], point_b: tuple[float, float]) -> float:
    dx = point_a[0] - point_b[0]
    dy = point_a[1] - point_b[1]
    return dx * dx + dy * dy


def get_line_endpoints(line: dict[str, Any]) -> tuple[tuple[float, float], tuple[float, float]]:
    start = line.get("start_point", [0.0, 0.0])
    end = line.get("end_point", [0.0, 0.0])
    return (float(start[0]), float(start[1])), (float(end[0]), float(end[1]))


def get_line_waypoints(line: dict[str, Any]) -> list[tuple[float, float]]:
    raw_waypoints = line.get("waypoints")
    if isinstance(raw_waypoints, list):
        waypoints: list[tuple[float, float]] = []
        for point in raw_waypoints:
            if not isinstance(point, (list, tuple)) or len(point) < 2:
                continue
            try:
                waypoints.append((float(point[0]), float(point[1])))
            except (TypeError, ValueError):
                continue
        if len(waypoints) >= 2:
            return waypoints

    start_point, end_point = get_line_endpoints(line)
    return [start_point, end_point]


def find_line_projection_alignment(
    line: dict[str, Any],
    projection_lines: list[dict[str, Any]],
    start_match: dict[str, Any] | None = None,
    end_match: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    waypoints = get_line_waypoints(line)
    if start_match is not None:
        waypoints[0] = (float(start_match["x"]), float(start_match["y"]))
    if end_match is not None:
        waypoints[-1] = (float(end_match["x"]), float(end_match["y"]))

    best_alignment: dict[str, Any] | None = None
    best_length = -1.0

    for segment_start, segment_end in zip(waypoints, waypoints[1:]):
        if squared_distance(segment_start, segment_end) == 0.0:
            continue

        projection_alignment = find_projection_alignment(
            segment_start,
            segment_end,
            projection_lines,
        )
        if projection_alignment is None:
            continue

        segment_length = math.sqrt(squared_distance(segment_start, segment_end))
        if segment_length <= best_length:
            continue

        best_length = segment_length
        best_alignment = {
            "projection_alignment": projection_alignment,
            "segment_start_point": segment_start,
            "segment_end_point": segment_end,
        }

    return best_alignment


def find_nearest_projection_endpoint(
    point: tuple[float, float],
    endpoints: list[dict[str, float | int]],
    radius: float,
) -> dict[str, Any] | None:
    best_endpoint: dict[str, float | int] | None = None
    best_dist_sq = radius * radius
    for endpoint in endpoints:
        candidate = (float(endpoint["x"]), float(endpoint["y"]))
        dist_sq = squared_distance(point, candidate)
        if dist_sq > best_dist_sq:
            continue
        best_dist_sq = dist_sq
        best_endpoint = endpoint

    if best_endpoint is None:
        return None

    return {
        "endpoint_idx": int(best_endpoint["endpoint_idx"]),
        "segment_idx": int(best_endpoint["segment_idx"]),
        "x": float(best_endpoint["x"]),
        "y": float(best_endpoint["y"]),
        "distance": math.sqrt(best_dist_sq),
    }


def detect_lines_api(image_path: Path) -> list[dict[str, Any]]:
    with image_path.open("rb") as file_obj:
        response = requests.post(
            LINE_API,
            files={"file": (image_path.name, file_obj, "image/png")},
            data={
                "method": "lsd",
                "min_length": str(LINE_MIN_LENGTH),
                "max_lines": str(LINE_MAX_LINES),
                "merge_lines": "true",
                "classify_types": "false",
                "find_intersections_flag": "false",
                "visualize": "false",
            },
            timeout=120,
        )
    response.raise_for_status()
    return response.json().get("data", {}).get("lines", [])


def run_ocr(image_path: Path) -> list[dict[str, Any]]:
    with image_path.open("rb") as file_obj:
        response = requests.post(
            OCR_API,
            files={"file": (image_path.name, file_obj, "image/png")},
            timeout=120,
        )
    response.raise_for_status()
    return response.json().get("detections", [])


def build_projection_endpoint_candidates(
    gray: np.ndarray,
    projection_lines: list[dict[str, Any]],
) -> tuple[list[dict[str, float | int]], int]:
    lsd_segments = detect_lsd_segments(gray)
    endpoints = extract_endpoints(lsd_segments)
    filtered_endpoints = filter_endpoints_on_projections(
        endpoints,
        projection_lines,
        tolerance=ENDPOINT_TOLERANCE,
    )

    indexed_endpoints: list[dict[str, float | int]] = []
    for endpoint_idx, endpoint in enumerate(filtered_endpoints):
        indexed_endpoints.append(
            {
                **endpoint,
                "endpoint_idx": endpoint_idx,
            }
        )
    return indexed_endpoints, len(lsd_segments)


def find_projection_alignment(
    start_point: tuple[float, float],
    end_point: tuple[float, float],
    projection_lines: list[dict[str, Any]],
) -> dict[str, Any] | None:
    horizontal_matches: list[int] = []
    vertical_matches: list[int] = []

    for projection_idx, projection_line in enumerate(projection_lines):
        if projection_line["axis"] == "h":
            py = float(projection_line["py"])
            if (
                abs(start_point[1] - end_point[1]) <= PROJECTION_AXIS_TOLERANCE
                and abs(start_point[1] - py) <= PROJECTION_AXIS_TOLERANCE
                and abs(end_point[1] - py) <= PROJECTION_AXIS_TOLERANCE
            ):
                horizontal_matches.append(projection_idx)
            continue

        px = float(projection_line["px"])
        if (
            abs(start_point[0] - end_point[0]) <= PROJECTION_AXIS_TOLERANCE
            and abs(start_point[0] - px) <= PROJECTION_AXIS_TOLERANCE
            and abs(end_point[0] - px) <= PROJECTION_AXIS_TOLERANCE
        ):
            vertical_matches.append(projection_idx)

    if horizontal_matches:
        return {"axis": "h", "projection_indices": horizontal_matches}
    if vertical_matches:
        return {"axis": "v", "projection_indices": vertical_matches}
    return None


def dedupe_lines(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[tuple[Any, ...], dict[str, Any]] = {}
    for line in sorted(lines, key=lambda item: float(item.get("length", 0.0)), reverse=True):
        start_point = line["start_point_xy"]
        end_point = line["end_point_xy"]
        alignment = line["projection_alignment"]
        axis = alignment["axis"]

        if axis == "h":
            coord = round(((start_point[1] + end_point[1]) / 2.0) / LINE_KEY_COORD_BIN)
            span_start = round(min(start_point[0], end_point[0]) / LINE_KEY_SPAN_BIN)
            span_end = round(max(start_point[0], end_point[0]) / LINE_KEY_SPAN_BIN)
        else:
            coord = round(((start_point[0] + end_point[0]) / 2.0) / LINE_KEY_COORD_BIN)
            span_start = round(min(start_point[1], end_point[1]) / LINE_KEY_SPAN_BIN)
            span_end = round(max(start_point[1], end_point[1]) / LINE_KEY_SPAN_BIN)

        key = (
            axis,
            coord,
            span_start,
            span_end,
            tuple(alignment["projection_indices"][:2]),
        )
        if key in deduped:
            continue
        deduped[key] = line

    return list(deduped.values())


def filter_connected_lines(
    lines: list[dict[str, Any]],
    projection_endpoints: list[dict[str, float | int]],
    projection_lines: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    connected_lines: list[dict[str, Any]] = []
    pair_lines: list[dict[str, Any]] = []

    for line in lines:
        start_point, end_point = get_line_endpoints(line)
        start_match = find_nearest_projection_endpoint(
            start_point,
            projection_endpoints,
            radius=LINE_CONNECTION_RADIUS,
        )
        end_match = find_nearest_projection_endpoint(
            end_point,
            projection_endpoints,
            radius=LINE_CONNECTION_RADIUS,
        )

        if start_match is None and end_match is None:
            continue

        projection_alignment_info = find_line_projection_alignment(
            line,
            projection_lines,
            start_match=start_match,
            end_match=end_match,
        )
        if projection_alignment_info is None:
            continue

        aligned_start_point = projection_alignment_info["segment_start_point"]
        aligned_end_point = projection_alignment_info["segment_end_point"]
        annotated = {
            **line,
            "start_match": start_match,
            "end_match": end_match,
            "projection_alignment": projection_alignment_info["projection_alignment"],
            "start_point_xy": aligned_start_point,
            "end_point_xy": aligned_end_point,
            "midpoint": (
                (aligned_start_point[0] + aligned_end_point[0]) / 2.0,
                (aligned_start_point[1] + aligned_end_point[1]) / 2.0,
            ),
        }
        connected_lines.append(annotated)

        if start_match is None or end_match is None:
            continue
        if start_match["endpoint_idx"] == end_match["endpoint_idx"]:
            continue

        pair_lines.append(annotated)

    return dedupe_lines(connected_lines), dedupe_lines(pair_lines)


def bbox_center(bbox: list[list[float]]) -> tuple[float, float] | None:
    if not isinstance(bbox, list) or len(bbox) < 4:
        return None

    try:
        xs = [float(point[0]) for point in bbox]
        ys = [float(point[1]) for point in bbox]
    except (TypeError, ValueError, IndexError):
        return None

    return (sum(xs) / len(xs), sum(ys) / len(ys))


def is_dimension_like_text(text: str) -> bool:
    cleaned = text.strip()
    if not cleaned:
        return False
    if re.fullmatch(r"\(?[Øø]?\s*\d+(?:\.\d+)?\)?", cleaned):
        numeric_value = float(re.sub(r"[^\d.]", "", cleaned))
        return numeric_value >= 10.0
    if re.fullmatch(r"\d+\)", cleaned):
        numeric_value = float(re.sub(r"[^\d.]", "", cleaned))
        return numeric_value >= 10.0
    if re.fullmatch(r"\d+(?:\.\d+)?", cleaned):
        numeric_value = float(cleaned)
        return numeric_value >= 10.0
    if re.fullmatch(r"[Øø]\s*\d+(?:\.\d+)?", cleaned):
        numeric_value = float(re.sub(r"[^\d.]", "", cleaned))
        return numeric_value >= 10.0
    if re.fullmatch(r"M\d+(?:\.\d+)?", cleaned, flags=re.IGNORECASE):
        return True
    return False


def build_ocr_candidates(detections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for detection in detections:
        text = str(detection.get("text", "")).strip()
        bbox = detection.get("bbox", [])
        center = bbox_center(bbox)
        if center is None or not is_dimension_like_text(text):
            continue

        candidates.append(
            {
                "text": text,
                "bbox": bbox,
                "center": center,
                "confidence": float(detection.get("confidence", 0.0)),
            }
        )
    return candidates


def match_ocr_to_pair_lines(
    pair_lines: list[dict[str, Any]],
    ocr_candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    matched_pairs: list[dict[str, Any]] = []
    for pair in pair_lines:
        midpoint = pair["midpoint"]
        best_candidate: dict[str, Any] | None = None
        best_dist_sq = OCR_SEARCH_RADIUS * OCR_SEARCH_RADIUS
        for candidate in ocr_candidates:
            dist_sq = squared_distance(midpoint, candidate["center"])
            if dist_sq > best_dist_sq:
                continue
            best_dist_sq = dist_sq
            best_candidate = candidate

        matched_pairs.append(
            {
                **pair,
                "ocr": best_candidate,
                "ocr_distance": math.sqrt(best_dist_sq) if best_candidate else None,
            }
        )
    return matched_pairs


def unique_ocr_labels(matched_pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    labels: list[dict[str, Any]] = []
    seen: set[tuple[str, int, int]] = set()
    for pair in matched_pairs:
        ocr = pair.get("ocr")
        if not ocr:
            continue
        cx, cy = ocr["center"]
        key = (ocr["text"], int(round(cx)), int(round(cy)))
        if key in seen:
            continue
        seen.add(key)
        labels.append(ocr)
    return labels


def draw_text_with_outline(
    canvas: np.ndarray,
    text: str,
    origin: tuple[int, int],
    font_scale: float,
    color: tuple[int, int, int],
) -> None:
    cv2.putText(
        canvas,
        text,
        origin,
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        (0, 0, 0),
        4,
        cv2.LINE_AA,
    )
    cv2.putText(
        canvas,
        text,
        origin,
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        color,
        2,
        cv2.LINE_AA,
    )


def render_overlay(
    image: np.ndarray,
    circle_lines: list[dict[str, Any]],
    protrusion_lines: list[dict[str, Any]],
    auxiliary_lines: list[dict[str, Any]],
    projection_endpoints: list[dict[str, float | int]],
    connected_lines: list[dict[str, Any]],
    matched_pairs: list[dict[str, Any]],
) -> Image.Image:
    base = draw_projection_endpoint_overlay(
        image,
        circle_lines,
        protrusion_lines,
        auxiliary_lines,
        projection_endpoints,
    )
    canvas = cv2.cvtColor(np.array(base), cv2.COLOR_RGB2BGR)
    height, width = canvas.shape[:2]

    label_font_scale = max(0.45, min(width, height) / 2500.0)
    for ocr in unique_ocr_labels(matched_pairs):
        bbox = np.array(ocr["bbox"], dtype=np.int32)
        cv2.polylines(canvas, [bbox], True, OCR_BOX_COLOR, 1, cv2.LINE_AA)
        text_x = int(np.min(bbox[:, 0]))
        text_y = int(np.min(bbox[:, 1])) - 8
        text_y = max(24, text_y)
        draw_text_with_outline(
            canvas,
            ocr["text"],
            (text_x, text_y),
            label_font_scale,
            OCR_TEXT_COLOR,
        )

    # Draw line-detector segments after projection lines/endpoints so they stay visible.
    for line in connected_lines:
        is_pair = line.get("start_match") is not None and line.get("end_match") is not None
        color = PAIR_LINE_COLOR if is_pair else CONNECTED_LINE_COLOR
        thickness = PAIR_LINE_THICKNESS if is_pair else CONNECTED_LINE_THICKNESS
        waypoints = get_line_waypoints(line)
        points = np.array(
            [[int(round(x)), int(round(y))] for x, y in waypoints],
            dtype=np.int32,
        )
        if len(points) >= 2:
            cv2.polylines(canvas, [points], False, color, thickness, cv2.LINE_AA)

    return Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))


def summarize_labels(matched_pairs: list[dict[str, Any]]) -> str:
    labels = [pair["ocr"]["text"] for pair in matched_pairs if pair.get("ocr")]
    if not labels:
        return "-"

    counts: dict[str, int] = {}
    order: list[str] = []
    for label in labels:
        if label not in counts:
            counts[label] = 0
            order.append(label)
        counts[label] += 1

    parts = []
    for label in order:
        count = counts[label]
        if count == 1:
            parts.append(label)
        else:
            parts.append(f"{label} x{count}")
    return ", ".join(parts)


def run() -> None:
    args = parse_args()
    mode = "connected lines only" if args.no_ocr else "line detector + OCR"
    print(f"S08 Cardinal v3 - {mode}")
    print("=" * 60)

    targets = [
        (doc_id, gt)
        for doc_id, gt in GT.items()
        if args.doc is None or gt["name"] == args.doc
    ]

    results: list[dict[str, Any]] = []

    for doc_id, gt in targets:
        name = gt["name"]
        image_path = SRC_DIR / f"{doc_id}.png"
        if not image_path.exists():
            print(f"⚠ {name}: {image_path} not found")
            continue

        print(f"\n{name.upper()} - {doc_id}")
        image = cv2.imread(str(image_path))
        gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if image is None or gray is None:
            print(f"  ⚠ image load failed: {image_path}")
            continue

        data = collect_projection_data(gray)
        circles_full = data["circles_full"]
        if not circles_full:
            print("  ⚠ no primary concentric circles")
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

        projection_endpoints, lsd_count = build_projection_endpoint_candidates(
            gray,
            projection_lines,
        )
        print(
            f"  projections={len(projection_lines)} | "
            f"lsd_segments={lsd_count} | "
            f"projection_endpoints={len(projection_endpoints)}"
        )

        line_detector_lines = detect_lines_api(image_path)
        connected_lines, pair_lines = filter_connected_lines(
            line_detector_lines,
            projection_endpoints,
            projection_lines,
        )
        print(
            f"  line_detector={len(line_detector_lines)} | "
            f"connected_lines={len(connected_lines)} | "
            f"pair_lines={len(pair_lines)}"
        )

        ocr_detections: list[dict[str, Any]] = []
        ocr_candidates: list[dict[str, Any]] = []
        matched_pairs = [
            {**pair, "ocr": None, "ocr_distance": None}
            for pair in pair_lines
        ]
        matched_count = 0
        label_summary = "-"
        if not args.no_ocr:
            ocr_detections = run_ocr(image_path)
            ocr_candidates = build_ocr_candidates(ocr_detections)
            matched_pairs = match_ocr_to_pair_lines(pair_lines, ocr_candidates)
            matched_count = sum(1 for pair in matched_pairs if pair.get("ocr"))
            label_summary = summarize_labels(matched_pairs)
            print(
                f"  ocr_detections={len(ocr_detections)} | "
                f"ocr_candidates={len(ocr_candidates)} | "
                f"ocr_matches={matched_count}"
            )
            print(f"  labels={label_summary}")

        overlay = render_overlay(
            image,
            circle_lines,
            protrusion_lines,
            auxiliary_lines,
            projection_endpoints,
            connected_lines,
            matched_pairs,
        )
        output_name = (
            f"{name}_connected_lines.jpg"
            if args.no_ocr
            else f"{name}_line_detector_ocr.jpg"
        )
        save_pil(overlay, output_name, max_w=1600)

        results.append(
            {
                "name": name.upper(),
                "line_detector": len(line_detector_lines),
                "connected_lines": len(connected_lines),
                "pair_lines": len(pair_lines),
                "ocr_matches": matched_count,
                "labels": label_summary,
            }
        )

    if not results:
        return

    print("\nMarkdown stats")
    if args.no_ocr:
        print("| 도면 | Line Detector 선분 수 | 연결 선분 수 | 치수선 쌍 수 |")
        print("|------|:---:|:---:|:---:|")
    else:
        print("| 도면 | Line Detector 선분 수 | 연결 선분 수 | 치수선 쌍 수 | OCR 매칭 | OCR 라벨 |")
        print("|------|:---:|:---:|:---:|:---:|------|")
    for row in results:
        if args.no_ocr:
            print(
                f"| {row['name']} | {row['line_detector']}개 | "
                f"{row['connected_lines']}개 | {row['pair_lines']}개 |"
            )
        else:
            print(
                f"| {row['name']} | {row['line_detector']}개 | {row['connected_lines']}개 | "
                f"{row['pair_lines']}개 | {row['ocr_matches']}개 | {row['labels']} |"
            )


if __name__ == "__main__":
    run()
