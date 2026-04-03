#!/usr/bin/env python3
"""S01 + Cardinal 통합 시각화.

요구사항:
1. S01 Black Hat 화살촉 검출은 arrowhead_detector의 detect_arrowheads 사용
2. 화살촉 쌍 매칭은 arrowhead_detector의 match_arrowhead_pairs 사용
3. 투사선 끝점은 2-2와 동일하게 ALT 동심원 + cardinal_max_scan 기반 geometry 사용
4. 전체 도면 위에 S01 전체 쌍과 투사선 위 쌍을 함께 시각화
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent / ".." / "backend"))

from services.arrowhead_detector import detect_arrowheads, match_arrowhead_pairs
from s08_cardinal_v3_fullpage import (
    build_auxiliary_lines,
    build_circle_lines,
    build_protrusion_lines,
    collect_projection_data,
    draw_projection_lines_only,
)

SRC_DIR = Path("/home/uproot/ax/poc/blueprint-ai-bom/data/dse_batch_test/converted_pngs")
OUT_DIR = Path("/home/uproot/ax/poc/docs-site-starlight/public/images/gt-validation/steps")
OUT_DIR.mkdir(exist_ok=True)

OCR_API = "http://localhost:5006/api/v1/ocr"

GT: Dict[str, Dict[str, Any]] = {
    "TD0062015": {"name": "t1", "od": 360, "id": 190, "w": 200},
    "TD0062021": {"name": "t2", "od": 380, "id": 190, "w": 200},
    "TD0062031": {"name": "t4", "od": 420, "id": 260, "w": 260},
    "TD0062050": {"name": "t8", "od": 500, "id": 260, "w": 200},
}


def get_font(size: int = 16) -> ImageFont.ImageFont:
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def add_header(
    img_bgr: np.ndarray,
    title: str,
    subtitle: str = "",
    subtitle2: str = "",
) -> Image.Image:
    pil = Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil)
    height, width = img_bgr.shape[:2]
    font = get_font(max(16, height // 60))
    font_sm = get_font(max(12, height // 80))
    bar_h = 80 if subtitle2 else 60
    draw.rectangle([0, 0, width, bar_h], fill="#222222")
    draw.text((10, 5), title, fill="white", font=font)
    if subtitle:
        draw.text((10, 30), subtitle, fill="#AAAAAA", font=font_sm)
    if subtitle2:
        draw.text((10, 52), subtitle2, fill="#66BB6A", font=font_sm)
    return pil


def save_pil(pil_img: Image.Image, name: str, max_w: int = 1600) -> None:
    if pil_img.width > max_w:
        ratio = max_w / pil_img.width
        pil_img = pil_img.resize(
            (max_w, int(pil_img.height * ratio)),
            Image.LANCZOS,
        )
    out_path = OUT_DIR / name
    pil_img.save(out_path, quality=90)
    print(f"  ✓ {name} ({pil_img.width}x{pil_img.height})")


def run_ocr(image_path: Path) -> List[Dict[str, Any]]:
    with image_path.open("rb") as file_obj:
        response = requests.post(
            OCR_API,
            files={"file": (image_path.name, file_obj, "image/png")},
            timeout=120,
        )
    response.raise_for_status()
    return response.json().get("detections", [])


def normalize_ocr_bbox(bbox: Any) -> Optional[Tuple[List[float], List[float]]]:
    if not isinstance(bbox, list) or len(bbox) < 4:
        return None
    try:
        xs = [float(point[0]) for point in bbox]
        ys = [float(point[1]) for point in bbox]
    except (TypeError, ValueError, IndexError):
        return None
    return xs, ys


def match_ocr_to_dimlines(
    dim_lines: List[Dict[str, Any]],
    ocr_dets: List[Dict[str, Any]],
    search_radius: float = 150.0,
) -> List[Dict[str, Any]]:
    ocr_numbers: List[Dict[str, Any]] = []
    for det in ocr_dets:
        text = str(det.get("text", "")).strip()
        bbox = normalize_ocr_bbox(det.get("bbox"))
        if not text or bbox is None:
            continue

        normalized = re.sub(r"\s+", "", re.sub(r"[()]", "", text))
        if re.search(r"[A-Za-z]", normalized) and not re.fullmatch(
            r"[ØøΦ⌀∅RrMm]?\d+(\.\d+)?",
            normalized,
        ):
            continue

        match = re.search(r"(\d+\.?\d*)", normalized)
        if not match:
            continue

        value = float(match.group(1))
        if not 10 < value < 3000:
            continue

        xs, ys = bbox
        ocr_numbers.append(
            {
                "text": text,
                "value": value,
                "cx": sum(xs) / len(xs),
                "cy": sum(ys) / len(ys),
            }
        )

    matched: List[Dict[str, Any]] = []
    for dim_line in dim_lines:
        mid_x = float(dim_line["midpoint"]["x"])
        mid_y = float(dim_line["midpoint"]["y"])
        best: Optional[Dict[str, Any]] = None
        best_dist = float("inf")

        for ocr in ocr_numbers:
            distance = float(np.hypot(ocr["cx"] - mid_x, ocr["cy"] - mid_y))
            if distance <= search_radius and distance < best_dist:
                best_dist = distance
                best = ocr

        matched.append({"dim_line": dim_line, "ocr": best, "distance": best_dist})

    return matched


def collect_projection_lines(gray: np.ndarray) -> Tuple[List[Tuple[float, float, float]], List[Dict[str, Any]]]:
    data = collect_projection_data(gray)
    circles_full = data["circles_full"]

    projection_lines: List[Dict[str, Any]] = []
    for line in build_circle_lines(circles_full):
        projection_lines.append(
            {
                "px": int(line["px"]),
                "py": int(line["py"]),
                "axis": str(line["axis"]),
                "source": "circle",
            }
        )

    for line in build_protrusion_lines(
        data["peaks_full"],
        data["center_full"],
        data["outer_r"],
    ):
        projection_lines.append(
            {
                "px": int(line["px"]),
                "py": int(line["py"]),
                "axis": str(line["axis"]),
                "source": "protrusion",
            }
        )

    for line in build_auxiliary_lines(
        data["auxiliary_rows"],
        data["center_full"],
    ):
        projection_lines.append(
            {
                "px": int(line["px"]),
                "py": int(line["py"]),
                "axis": str(line["axis"]),
                "source": "auxiliary",
            }
        )

    return circles_full, projection_lines


def pair_hits_projection(
    dim_line: Dict[str, Any],
    projection_line: Dict[str, Any],
    tolerance: int,
) -> bool:
    sx = float(dim_line["start"]["x"])
    sy = float(dim_line["start"]["y"])
    ex = float(dim_line["end"]["x"])
    ey = float(dim_line["end"]["y"])
    mx = float(dim_line["midpoint"]["x"])
    my = float(dim_line["midpoint"]["y"])
    px = int(projection_line["px"])
    py = int(projection_line["py"])

    if projection_line["axis"] == "h":
        return any(abs(value - py) <= tolerance for value in (sy, ey, my))
    return any(abs(value - px) <= tolerance for value in (sx, ex, mx))


def filter_pairs_on_projections(
    dim_lines: List[Dict[str, Any]],
    projection_lines: List[Dict[str, Any]],
    tolerance: int = 20,
) -> List[Dict[str, Any]]:
    filtered: List[Dict[str, Any]] = []
    for dim_line in dim_lines:
        hits = [
            projection_line
            for projection_line in projection_lines
            if pair_hits_projection(dim_line, projection_line, tolerance)
        ]
        if not hits:
            continue
        filtered.append({**dim_line, "_projection_hits": hits})
    return filtered


def projection_color(line: Dict[str, Any]) -> Tuple[int, int, int]:
    if line["source"] == "protrusion":
        return (255, 0, 200)
    if line["axis"] == "h":
        return (255, 255, 0)
    return (0, 255, 255)


def draw_projection_line(
    canvas: np.ndarray,
    line: Dict[str, Any],
    width: int,
    height: int,
) -> None:
    color = projection_color(line)
    if line["axis"] == "h":
        cv2.line(canvas, (0, int(line["py"])), (width, int(line["py"])), color, 2)
    else:
        cv2.line(canvas, (int(line["px"]), 0), (int(line["px"]), height), color, 2)


def draw_arrowhead_marker(canvas: np.ndarray, arrow: Dict[str, Any]) -> None:
    ax = int(arrow["x"])
    ay = int(arrow["y"])
    cv2.circle(canvas, (ax, ay), 6, (0, 0, 255), -1)
    cv2.circle(canvas, (ax, ay), 8, (0, 0, 255), 1)


def classify_gt_label(value: float, gt: Dict[str, Any]) -> Optional[str]:
    for label, key in (("OD", "od"), ("ID", "id"), ("W", "w")):
        gt_value = float(gt[key])
        if abs(value - gt_value) / gt_value < 0.05:
            return f"{label}={int(gt_value)}"
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--doc",
        choices=[str(gt["name"]) for gt in GT.values()],
        help="특정 도면만 처리",
    )
    parser.add_argument(
        "--projection-arrows-only",
        action="store_true",
        help="2-2 직선 투사 이미지 위에 S01 화살촉 점만 추가한 산출물 생성",
    )
    return parser.parse_args()


def resolve_targets(doc_name: Optional[str]) -> List[Tuple[str, Dict[str, Any]]]:
    return [
        (doc_id, gt)
        for doc_id, gt in GT.items()
        if doc_name is None or gt["name"] == doc_name
    ]


def visualize_projection_arrowheads_only(
    img: np.ndarray,
    circles_full: List[Tuple[float, float, float]],
    circle_lines: List[Dict[str, Any]],
    peaks_full: List[Tuple[float, float, float, float]],
    protrusion_lines: List[Dict[str, Any]],
    auxiliary_lines: List[Dict[str, Any]],
    arrowheads: List[Dict[str, Any]],
) -> Image.Image:
    base = draw_projection_lines_only(
        img,
        circles_full,
        circle_lines,
        peaks_full,
        protrusion_lines,
        auxiliary_lines,
    )
    canvas = cv2.cvtColor(np.array(base), cv2.COLOR_RGB2BGR)

    for arrow in arrowheads:
        draw_arrowhead_marker(canvas, arrow)

    return Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))


def format_ocr_label(ocr: Dict[str, Any], gt: Dict[str, Any]) -> str:
    label = classify_gt_label(float(ocr["value"]), gt)
    if label:
        return label
    return re.sub(r"\s+", "", str(ocr["text"]))


def visualize(
    img: np.ndarray,
    circles_full: List[Tuple[float, float, float]],
    projection_lines: List[Dict[str, Any]],
    arrowheads: List[Dict[str, Any]],
    all_pairs: List[Dict[str, Any]],
    filtered_pairs: List[Dict[str, Any]],
    ocr_matched: List[Dict[str, Any]],
    name: str,
    gt: Dict[str, Any],
) -> Image.Image:
    height, width = img.shape[:2]
    canvas = img.copy()

    for cx, cy, radius in circles_full:
        cv2.circle(canvas, (int(cx), int(cy)), int(radius), (67, 160, 71), 3)

    for line in projection_lines:
        draw_projection_line(canvas, line, width, height)

    for dim_line in all_pairs:
        cv2.line(
            canvas,
            (int(dim_line["start"]["x"]), int(dim_line["start"]["y"])),
            (int(dim_line["end"]["x"]), int(dim_line["end"]["y"])),
            (0, 165, 255),
            1,
        )

    for dim_line in filtered_pairs:
        cv2.line(
            canvas,
            (int(dim_line["start"]["x"]), int(dim_line["start"]["y"])),
            (int(dim_line["end"]["x"]), int(dim_line["end"]["y"])),
            (0, 255, 0),
            3,
        )

    for match in ocr_matched:
        ocr = match["ocr"]
        if ocr is None:
            continue
        label = format_ocr_label(ocr, gt)
        mid_x = int(match["dim_line"]["midpoint"]["x"])
        mid_y = int(match["dim_line"]["midpoint"]["y"])
        cv2.putText(
            canvas,
            label,
            (mid_x + 10, mid_y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 0, 0),
            4,
            cv2.LINE_AA,
        )
        cv2.putText(
            canvas,
            label,
            (mid_x + 10, mid_y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

    for arrow in arrowheads:
        draw_arrowhead_marker(canvas, arrow)

    detected_labels = [
        format_ocr_label(match["ocr"], gt)
        for match in ocr_matched
        if match["ocr"] is not None
    ]
    pil = add_header(
        canvas,
        f"{name.upper()} — S01 Arrowhead Pair Matching",
        (
            f"화살촉 {len(arrowheads)}개 | 치수선 쌍 {len(all_pairs)}개 | "
            f"투사선 위 쌍 {len(filtered_pairs)}개 | 투사선 {len(projection_lines)}개"
        ),
        f"GT: OD={gt['od']} ID={gt['id']} W={gt['w']} | OCR: {detected_labels}",
    )
    return pil


def run() -> None:
    args = parse_args()
    print("S01 + Cardinal 통합 시각화")
    print("=" * 60)

    for doc_id, gt in resolve_targets(args.doc):
        name = str(gt["name"])
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
        outer_r = data["outer_r"]
        center_full = data["center_full"]
        projection_lines = []
        circle_lines = build_circle_lines(circles_full)
        protrusion_lines = build_protrusion_lines(peaks_full, center_full, outer_r)
        auxiliary_lines = build_auxiliary_lines(
            data["auxiliary_rows"],
            center_full,
        )
        for line in circle_lines:
            projection_lines.append(
                {
                    "px": int(line["px"]),
                    "py": int(line["py"]),
                    "axis": str(line["axis"]),
                    "source": "circle",
                }
            )
        for line in protrusion_lines:
            projection_lines.append(
                {
                    "px": int(line["px"]),
                    "py": int(line["py"]),
                    "axis": str(line["axis"]),
                    "source": "protrusion",
                }
            )
        for line in auxiliary_lines:
            projection_lines.append(
                {
                    "px": int(line["px"]),
                    "py": int(line["py"]),
                    "axis": str(line["axis"]),
                    "source": "auxiliary",
                }
            )
        print(f"  [1] ALT 동심원: {len(circles_full)}개")
        print(f"  [2] 투사선: {len(projection_lines)}개")

        arrowheads = detect_arrowheads(gray)
        print(f"  [3] S01 화살촉: {len(arrowheads)}개")

        if args.projection_arrows_only:
            pil = visualize_projection_arrowheads_only(
                img,
                circles_full,
                circle_lines,
                peaks_full,
                protrusion_lines,
                auxiliary_lines,
                arrowheads,
            )
            save_pil(pil, f"{name}_s01_arrows.jpg")
            continue

        all_pairs = match_arrowhead_pairs(arrowheads)
        print(f"  [4] 치수선 쌍: {len(all_pairs)}개")

        filtered_pairs = filter_pairs_on_projections(all_pairs, projection_lines)
        print(f"  [5] 투사선 위 쌍: {len(filtered_pairs)}개")

        ocr_dets = run_ocr(img_path)
        ocr_matched = match_ocr_to_dimlines(filtered_pairs, ocr_dets)
        ocr_hits = [match for match in ocr_matched if match["ocr"] is not None]
        print(f"  [6] OCR 매칭: {len(ocr_hits)}개")
        for match in ocr_hits:
            print(f"      {format_ocr_label(match['ocr'], gt)}")

        pil = visualize(
            img,
            circles_full,
            projection_lines,
            arrowheads,
            all_pairs,
            filtered_pairs,
            ocr_matched,
            name,
            gt,
        )
        save_pil(pil, f"{name}_s01_cardinal.jpg")

    print(f"\n완료: {OUT_DIR}")


if __name__ == "__main__":
    run()
