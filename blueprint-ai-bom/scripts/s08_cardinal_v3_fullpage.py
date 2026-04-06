#!/usr/bin/env python3
"""S08 Cardinal Projection v3 — 전체 도면에서 직선 투사."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import cv2
import numpy as np

from cardinal_common import (
    add_header,
    build_auxiliary_lines,
    build_circle_lines,
    build_protrusion_lines,
    collect_projection_data,
    draw_projection_lines_only,
    save_pil,
)

SCRIPT_DIR = Path(__file__).resolve().parent
BLUEPRINT_ROOT = SCRIPT_DIR.parent
PROJECT_ROOT = BLUEPRINT_ROOT.parent

SRC_DIR = Path(
    os.environ.get(
        "AX_DSE_BATCH_PNG_DIR",
        str(BLUEPRINT_ROOT / "data" / "dse_batch_test" / "converted_pngs"),
    )
)
OUT_DIR = Path(
    os.environ.get(
        "AX_GT_VALIDATION_OUT_DIR",
        str(
            PROJECT_ROOT
            / "docs-site-starlight"
            / "public"
            / "images"
            / "gt-validation"
            / "steps"
        ),
    )
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

GT = {
    "TD0062015": {"name": "t1", "od": 360, "id": 190},
    "TD0062021": {"name": "t2", "od": 380, "id": 190},
    "TD0062031": {"name": "t4", "od": 420, "id": 260},
    "TD0062050": {"name": "t8", "od": 500, "id": 260},
}


def detect_arrowheads(gray: np.ndarray) -> list[dict[str, float]]:
    """S01 방식 — Black Hat 모폴로지로 실선 삼각형 화살촉만 검출."""
    _, binary = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU,
    )

    ks = max(3, min(gray.shape[0], gray.shape[1]) // 150)
    ks = ks if ks % 2 == 1 else ks + 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ks, ks))
    black_hat = cv2.subtract(
        cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel),
        binary,
    )

    dil_k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    black_hat = cv2.dilate(black_hat, dil_k, iterations=1)

    contours, _ = cv2.findContours(
        black_hat,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    arrows = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 50 or area > 500:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        if h == 0 or w == 0:
            continue
        aspect = w / h
        if aspect < 0.3 or aspect > 3.0:
            continue
        moments = cv2.moments(cnt)
        if moments["m00"] < 1e-6:
            acx, acy = x + w // 2, y + h // 2
        else:
            acx = int(moments["m10"] / moments["m00"])
            acy = int(moments["m01"] / moments["m00"])
        arrows.append({"x": float(acx), "y": float(acy), "area": float(area)})
    return arrows


def attach_circle_hits(
    circle_lines: list[dict[str, object]],
    arrows: list[dict[str, float]] | None = None,
    hit_tolerance: int = 15,
) -> list[dict[str, object]]:
    arrows = arrows or []
    annotated = []
    for line in circle_lines:
        hits = []
        cx = float(line["cx"])
        cy = float(line["cy"])
        radius = float(line["r"])
        for arrow in arrows:
            ax, ay = arrow["x"], arrow["y"]
            if line["axis"] == "h" and abs(ay - int(line["py"])) <= hit_tolerance:
                if np.sqrt((ax - cx) ** 2 + (ay - cy) ** 2) < radius * 0.9:
                    continue
                hits.append((int(ax), int(ay)))
            elif line["axis"] == "v" and abs(ax - int(line["px"])) <= hit_tolerance:
                if np.sqrt((ax - cx) ** 2 + (ay - cy) ** 2) < radius * 0.9:
                    continue
                hits.append((int(ax), int(ay)))
        annotated.append({**line, "hits": hits})
    return annotated


def attach_protrusion_hits(
    protrusion_lines: list[dict[str, object]],
    arrows: list[dict[str, float]] | None = None,
    hit_tolerance: int = 15,
) -> list[dict[str, object]]:
    arrows = arrows or []
    annotated = []
    for line in protrusion_lines:
        hits = []
        ccx = float(line["ccx"])
        ccy = float(line["ccy"])
        outer_r = float(line["outer_r"])
        for arrow in arrows:
            ax, ay = arrow["x"], arrow["y"]
            if line["axis"] == "h" and abs(ay - int(line["py"])) <= hit_tolerance:
                if np.sqrt((ax - ccx) ** 2 + (ay - ccy) ** 2) > outer_r * 0.9:
                    hits.append((int(ax), int(ay)))
            elif line["axis"] == "v" and abs(ax - int(line["px"])) <= hit_tolerance:
                if np.sqrt((ax - ccx) ** 2 + (ay - ccy) ** 2) > outer_r * 0.9:
                    hits.append((int(ax), int(ay)))
        annotated.append({**line, "hits": hits})
    return annotated


def attach_auxiliary_hits(
    auxiliary_lines: list[dict[str, object]],
    arrows: list[dict[str, float]] | None = None,
    hit_tolerance: int = 15,
) -> list[dict[str, object]]:
    arrows = arrows or []
    annotated = []
    for line in auxiliary_lines:
        hits = []
        for arrow in arrows:
            ax, ay = arrow["x"], arrow["y"]
            if line["axis"] == "h" and abs(ay - int(line["py"])) <= hit_tolerance:
                hits.append((int(ax), int(ay)))
            elif line["axis"] == "v" and abs(ax - int(line["px"])) <= hit_tolerance:
                hits.append((int(ax), int(ay)))
        annotated.append({**line, "hits": hits})
    return annotated


def draw_projection_axis(
    canvas: np.ndarray,
    line: dict[str, object],
    full_w: int,
    full_h: int,
    thickness: int,
) -> None:
    color = tuple(line["color"])
    if line["axis"] == "h":
        cv2.line(canvas, (0, int(line["py"])), (full_w, int(line["py"])), color, thickness)
    else:
        cv2.line(canvas, (int(line["px"]), 0), (int(line["px"]), full_h), color, thickness)


def draw_fullpage_projection(
    img: np.ndarray,
    circles_full: list[tuple[float, float, float]],
    circle_lines: list[dict[str, object]],
    protrusion_lines: list[dict[str, object]],
    gt: dict[str, int | str],
    name: str,
    auxiliary_lines: list[dict[str, object]] | None = None,
):
    full_h, full_w = img.shape[:2]
    canvas = img.copy()
    auxiliary_lines = auxiliary_lines or []

    for cx, cy, radius in circles_full:
        cv2.circle(canvas, (int(cx), int(cy)), int(radius), (67, 160, 71), 3)

    circle_hit = 0
    circle_hit_lines = 0
    for line in circle_lines:
        draw_projection_axis(canvas, line, full_w, full_h, 2 if line["hits"] else 1)
        cv2.circle(
            canvas,
            (int(line["px"]), int(line["py"])),
            8,
            (255, 255, 255),
            2 if line["hits"] else 1,
        )
        if not line["hits"]:
            continue
        circle_hit_lines += 1
        for hx, hy in line["hits"]:
            cv2.drawMarker(
                canvas,
                (hx, hy),
                (0, 0, 255),
                cv2.MARKER_TILTED_CROSS,
                15,
                2,
            )
            circle_hit += 1

    protrusion_hit = 0
    protrusion_hit_lines = 0
    for line in protrusion_lines:
        draw_projection_axis(canvas, line, full_w, full_h, 2 if line["hits"] else 1)
        cv2.drawMarker(
            canvas,
            (int(line["px"]), int(line["py"])),
            (0, 0, 255),
            cv2.MARKER_DIAMOND,
            12,
            3 if line["hits"] else 1,
        )
        if not line["hits"]:
            continue
        protrusion_hit_lines += 1
        for hx, hy in line["hits"]:
            cv2.drawMarker(
                canvas,
                (hx, hy),
                (255, 0, 200),
                cv2.MARKER_TILTED_CROSS,
                12,
                2,
            )
            protrusion_hit += 1

    auxiliary_hit = 0
    auxiliary_hit_lines = 0
    section_hit = 0
    section_hit_lines = 0
    for line in auxiliary_lines:
        draw_projection_axis(canvas, line, full_w, full_h, 2 if line["hits"] else 1)
        if not line["hits"]:
            continue
        if line.get("source") == "section":
            section_hit_lines += 1
        else:
            auxiliary_hit_lines += 1
        for hx, hy in line["hits"]:
            cv2.drawMarker(
                canvas,
                (hx, hy),
                (0, 165, 255) if line.get("source") != "section" else (0, 215, 255),
                cv2.MARKER_TILTED_CROSS,
                12,
                2,
            )
            if line.get("source") == "section":
                section_hit += 1
            else:
                auxiliary_hit += 1

    total_lines = len(circle_lines) + len(protrusion_lines) + len(auxiliary_lines)
    active_lines = (
        circle_hit_lines
        + protrusion_hit_lines
        + auxiliary_hit_lines
        + section_hit_lines
    )
    print(f"  전체 직선: {total_lines}개 → 히트 있는 직선: {active_lines}개")
    print(f"  동심원 히트: {circle_hit}개 ({circle_hit_lines}개 직선)")
    print(f"  돌출부 히트: {protrusion_hit}개 ({protrusion_hit_lines}개 직선)")
    if auxiliary_lines:
        print(f"  보조도 히트: {auxiliary_hit}개 ({auxiliary_hit_lines}개 직선)")
        print(f"  SECTION 히트: {section_hit}개 ({section_hit_lines}개 직선)")

    auxiliary_count = sum(1 for line in auxiliary_lines if line.get("source") == "auxiliary")
    section_count = sum(1 for line in auxiliary_lines if line.get("source") == "section")

    for cx, cy, radius in circles_full:
        cv2.putText(
            canvas,
            f"r={radius:.0f}",
            (int(cx + radius * 0.7), int(cy - radius * 0.3)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (67, 160, 71),
            2,
        )

    return add_header(
        canvas,
        f"{name.upper()} — Cardinal v3 + Protrusion ({full_w}x{full_h})",
        (
            f"동심원 {len(circles_full)}개 + 돌출 {len(protrusion_lines) // 2}개 + "
            f"보조도 {auxiliary_count}개 + SECTION {section_count}개 | "
            f"히트: 원{circle_hit} + 돌출{protrusion_hit} + 보조{auxiliary_hit} + SECTION{section_hit}"
        ),
        f"GT: OD={gt['od']} ID={gt['id']}",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--doc",
        choices=[gt["name"] for gt in GT.values()],
        help="특정 도면만 처리",
    )
    parser.add_argument(
        "--lines-only",
        action="store_true",
        help="화살촉 히트 없이 끝점과 투사선만 그린 이미지 생성",
    )
    return parser.parse_args()


def run() -> None:
    args = parse_args()
    print("S08 Cardinal v3 — 전체 도면 투사 + 4방향 돌출부")
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

        print(f"\n{name.upper()} — {doc_id} (GT: OD={gt['od']} ID={gt['id']})")

        img = cv2.imread(str(img_path))
        gray = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
        if img is None or gray is None:
            print(f"  ⚠ 이미지 로드 실패: {img_path}")
            continue

        full_h, full_w = gray.shape
        print(f"  전체 도면: {full_w}x{full_h}")

        data = collect_projection_data(gray, image_path=img_path)
        circles_full = data["circles_full"]
        peaks_full = data["peaks_full"]
        outer_r = data["outer_r"]
        center_full = data["center_full"]
        auxiliary_rows = data["auxiliary_rows"]
        section_vertical_cols = data["section_vertical_cols"]
        section_horizontal_rows = data["section_horizontal_rows"]

        print(
            f"  ALT 후보: {len(data['raw_circles_roi'])}개 → "
            f"주 동심원: {len(circles_full)}개"
        )
        print(f"  돌출 끝점: {len(peaks_full)}개")
        print(f"  보조도 수평선: {len(auxiliary_rows)}개 ({auxiliary_rows})")
        print(
            f"  SECTION 수직선: {len(section_vertical_cols)}개 "
            f"({section_vertical_cols})"
        )
        print(
            f"  SECTION 수평선: {len(section_horizontal_rows)}개 "
            f"({section_horizontal_rows})"
        )

        if not circles_full:
            continue

        base_circle_lines = build_circle_lines(circles_full)
        base_protrusion_lines = build_protrusion_lines(peaks_full, center_full, outer_r)
        auxiliary_lines = build_auxiliary_lines(
            auxiliary_rows,
            center_full,
            section_vertical_cols,
            section_horizontal_rows,
            data["section_bounds"],
        )

        if args.lines_only:
            print(
                f"  lines-only 산출물: 동심원 직선 {len(base_circle_lines)}개 + "
                f"돌출 직선 {len(base_protrusion_lines)}개 + "
                f"보조도 직선 {len(auxiliary_lines)}개"
            )
            pil = draw_projection_lines_only(
                img,
                circles_full,
                base_circle_lines,
                peaks_full,
                base_protrusion_lines,
                auxiliary_lines,
            )
            save_pil(
                pil,
                f"{name}_projection_lines_only.jpg",
                max_w=1600,
                out_dir=OUT_DIR,
                show_size=True,
            )
            continue

        arrows = detect_arrowheads(gray)
        print(f"  화살촉 후보: {len(arrows)}개")
        circle_lines = attach_circle_hits(base_circle_lines, arrows)
        protrusion_lines = attach_protrusion_hits(base_protrusion_lines, arrows)
        auxiliary_hit_lines = attach_auxiliary_hits(auxiliary_lines, arrows)

        pil = draw_fullpage_projection(
            img,
            circles_full,
            circle_lines,
            protrusion_lines,
            gt,
            name,
            auxiliary_hit_lines,
        )
        save_pil(
            pil,
            f"{name}_cardinal_v3_full.jpg",
            max_w=1600,
            out_dir=OUT_DIR,
            show_size=True,
        )

    print(f"\n완료: {OUT_DIR}")


if __name__ == "__main__":
    run()
