#!/usr/bin/env python3
"""
Phase 2 Step 3: 레이아웃 모델 + K 방법 통합 PoC

검증 시나리오:
  1. 기존 K 방법 (전체 이미지) → 원 검출 + OCR
  2. 레이아웃 가이드 K 방법 (circle_feature 영역만) → 원 검출 + OCR
  3. 비베어링 자동 식별 (circle_feature 없으면 스킵)

GT-1: TD0062037 — OD=1036, ID=580, W=200
GT-2: TD0062055 — OD=515, ID=440, W=48
비베어링: TD0060700 (BOLT TORQUE TABLE)
"""

import sys
import time
from pathlib import Path

import cv2
import numpy as np

# YOLO 모델
from ultralytics import YOLO

# K 방법 import
sys.path.insert(0, str(Path("/home/uproot/ax/poc/blueprint-ai-bom/backend")))
from services.geometry_guided_extractor import (
    _detect_circles,
    _detect_circles_by_contour,
    _detect_circles_by_hough,
)

# ── 설정 ──────────────────────────────────────────────
RUNS_DIR = Path(__file__).parent / "runs"
best_candidates = sorted(RUNS_DIR.glob("layout_v1*/weights/best.pt"))
LAYOUT_MODEL_PATH = str(best_candidates[-1]) if best_candidates else None
DRAWINGS_DIR = Path("/home/uproot/ax/poc/blueprint-ai-bom/data/dse_batch_test/converted_pngs")
OUTPUT_DIR = Path(__file__).parent / "results" / "pipeline_test"

GT = {
    "TD0062037": {"OD": 1036, "ID": 580, "W": 200, "type": "THRUST BEARING ASSY"},
    "TD0062055": {"OD": 515, "ID": 440, "W": 48, "type": "RADIAL BEARING ASSY"},
    "TD0060700": {"OD": None, "ID": None, "W": None, "type": "BOLT TORQUE TABLE (비베어링)"},
}


def get_layout_regions(model, image_path: str, conf: float = 0.3):
    """YOLO 레이아웃 모델로 영역 검출"""
    results = model.predict(str(image_path), imgsz=640, conf=conf, device="0", verbose=False)
    boxes = results[0].boxes

    regions = {}
    for box, cls_id, score in zip(boxes.xyxy.cpu().numpy(), boxes.cls.cpu().numpy(), boxes.conf.cpu().numpy()):
        cls_name = model.names[int(cls_id)]
        if cls_name not in regions:
            regions[cls_name] = []
        regions[cls_name].append({
            "bbox": [int(x) for x in box],
            "confidence": float(score),
        })

    return regions


def bbox_iou(a, b):
    """두 bbox [x1,y1,x2,y2]의 IoU"""
    ix1 = max(a[0], b[0])
    iy1 = max(a[1], b[1])
    ix2 = min(a[2], b[2])
    iy2 = min(a[3], b[3])
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    area_a = (a[2]-a[0]) * (a[3]-a[1])
    area_b = (b[2]-b[0]) * (b[3]-b[1])
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0


def crop_to_region(img_gray, regions, target_class: str):
    """특정 클래스 영역으로 이미지 크롭 — main_view와 교차하는 영역 우선"""
    if target_class not in regions:
        return None, None

    candidates = regions[target_class]
    if not candidates:
        return None, None

    # circle_feature: 모든 고신뢰 영역의 union bbox (메인+ISO VIEW 모두 포함)
    if target_class == "circle_feature":
        high_conf = [c for c in candidates if c["confidence"] >= 0.5]
        if not high_conf:
            high_conf = candidates[:2]  # 최소 2개

        # union bbox 계산
        x1 = min(c["bbox"][0] for c in high_conf)
        y1 = min(c["bbox"][1] for c in high_conf)
        x2 = max(c["bbox"][2] for c in high_conf)
        y2 = max(c["bbox"][3] for c in high_conf)
        print(f"    → circle_feature union: {len(high_conf)}개 영역 합침")
    else:
        best = max(candidates, key=lambda r: r["confidence"])
        x1, y1, x2, y2 = best["bbox"]
    h, w = img_gray.shape[:2]

    # 20% 마진 추가 (치수선이 영역 밖에 있을 수 있음)
    margin_x = int((x2 - x1) * 0.2)
    margin_y = int((y2 - y1) * 0.2)
    x1 = max(0, x1 - margin_x)
    y1 = max(0, y1 - margin_y)
    x2 = min(w, x2 + margin_x)
    y2 = min(h, y2 + margin_y)

    cropped = img_gray[y1:y2, x1:x2]
    offset = (x1, y1)
    return cropped, offset


def detect_circles_in_region(img_gray, offset):
    """크롭된 영역에서 원 검출 후 원본 좌표로 변환"""
    h, w = img_gray.shape[:2]
    result = _detect_circles(img_gray, w, h)

    if result["found"] and offset:
        ox, oy = offset
        # 좌표 변환: 크롭 → 원본
        outer = list(result["outer"])
        outer[0] += ox  # cx
        outer[1] += oy  # cy
        result["outer"] = tuple(outer)

        if result.get("inner") is not None:
            inner = list(result["inner"])
            inner[0] += ox
            inner[1] += oy
            result["inner"] = tuple(inner)

    return result


def estimate_od_id(circles_result):
    """검출된 원으로 OD/ID 추정"""
    if not circles_result["found"]:
        return None, None

    outer = circles_result["outer"]
    inner = circles_result.get("inner")

    # 반지름 → 직경 (원본 이미지 기준 픽셀)
    od_r = outer[2]
    id_r = inner[2] if inner is not None else None

    return od_r, id_r


def test_drawing(model, drawing_id: str, gt: dict):
    """단일 도면 테스트: 기존 vs 레이아웃 가이드"""
    image_path = DRAWINGS_DIR / f"{drawing_id}.png"
    if not image_path.exists():
        print(f"[SKIP] {drawing_id}")
        return

    img_gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    orig_h, orig_w = img_gray.shape[:2]

    print(f"\n{'='*70}")
    print(f"[{drawing_id}] {gt['type']} (GT: OD={gt['OD']}, ID={gt['ID']}, W={gt['W']})")
    print(f"  이미지: {orig_w}x{orig_h}px")
    print(f"{'='*70}")

    # ── Step 1: 레이아웃 검출 ──
    t0 = time.time()
    regions = get_layout_regions(model, str(image_path))
    layout_time = time.time() - t0

    print(f"\n  [레이아웃] {layout_time:.3f}s")
    for cls_name, dets in regions.items():
        confs = [f"{d['confidence']:.2f}" for d in dets]
        print(f"    {cls_name}: {len(dets)}개 ({', '.join(confs)})")

    # 비베어링 판정
    has_circles = "circle_feature" in regions and len(regions["circle_feature"]) > 0
    if not has_circles:
        print(f"\n  ⚠️  circle_feature 없음 → 비베어링 판정")
        if gt["OD"] is None:
            print(f"  ✅ 비베어링 정확 판정!")
        else:
            print(f"  ❌ 오판: 실제로는 베어링 ({gt['type']})")
        return

    if gt["OD"] is None:
        print(f"\n  ❌ 비베어링인데 circle_feature 검출됨 (false positive)")

    # ── Step 2: 기존 방식 (전체 이미지) ──
    t0 = time.time()
    baseline_circles = _detect_circles(img_gray, orig_w, orig_h)
    baseline_time = time.time() - t0

    print(f"\n  [기존 K 방법] 전체 이미지 → 원 검출 ({baseline_time:.3f}s)")
    if baseline_circles["found"]:
        outer = baseline_circles["outer"]
        inner = baseline_circles.get("inner")
        print(f"    outer: cx={int(outer[0])}, cy={int(outer[1])}, r={int(outer[2])}")
        if inner is not None:
            print(f"    inner: cx={int(inner[0])}, cy={int(inner[1])}, r={int(inner[2])}")
        else:
            print(f"    inner: 미검출")
        # 직경 비율로 실제 치수 추정 가능 여부
        od_r, id_r = estimate_od_id(baseline_circles)
        ratio = id_r / od_r if id_r and od_r else None
        print(f"    반지름 비: outer={int(od_r)}px, inner={int(id_r) if id_r else '?'}px, ratio={ratio:.3f}" if ratio else f"    반지름: outer={int(od_r)}px")
    else:
        print(f"    ❌ 원 검출 실패: {baseline_circles.get('method', '?')}")

    # ── Step 3: 레이아웃 가이드 (circle_feature 영역만) ──
    t0 = time.time()
    cropped, offset = crop_to_region(img_gray, regions, "circle_feature")
    if cropped is not None:
        guided_circles = detect_circles_in_region(cropped, offset)
    else:
        guided_circles = {"found": False}
    guided_time = time.time() - t0

    print(f"\n  [레이아웃 가이드 K 방법] circle_feature 크롭 → 원 검출 ({guided_time:.3f}s)")
    if cropped is not None:
        ch, cw = cropped.shape[:2]
        reduction = (1.0 - (cw * ch) / (orig_w * orig_h)) * 100
        print(f"    크롭: {cw}x{ch}px (원본 대비 {reduction:.0f}% 감소)")

    if guided_circles["found"]:
        outer = guided_circles["outer"]
        inner = guided_circles.get("inner")
        print(f"    outer: cx={int(outer[0])}, cy={int(outer[1])}, r={int(outer[2])}")
        if inner is not None:
            print(f"    inner: cx={int(inner[0])}, cy={int(inner[1])}, r={int(inner[2])}")
        else:
            print(f"    inner: 미검출")
        od_r, id_r = estimate_od_id(guided_circles)
        ratio = id_r / od_r if id_r and od_r else None
        print(f"    반지름 비: outer={int(od_r)}px, inner={int(id_r) if id_r else '?'}px, ratio={ratio:.3f}" if ratio else f"    반지름: outer={int(od_r)}px")
    else:
        print(f"    ❌ 원 검출 실패")

    # ── Step 4: 비교 ──
    print(f"\n  [비교]")
    baseline_found = baseline_circles["found"]
    guided_found = guided_circles["found"]

    if baseline_found and guided_found:
        # 두 방법 모두 성공 시 — 반지름 비율로 정확도 비교
        b_outer_r = baseline_circles["outer"][2]
        g_outer_r = guided_circles["outer"][2]
        b_inner_r = baseline_circles["inner"][2] if baseline_circles.get("inner") is not None else None
        g_inner_r = guided_circles["inner"][2] if guided_circles.get("inner") is not None else None

        if gt["OD"] and gt["ID"]:
            gt_ratio = gt["ID"] / gt["OD"]
            b_ratio = b_inner_r / b_outer_r if b_inner_r else None
            g_ratio = g_inner_r / g_outer_r if g_inner_r else None

            print(f"    GT ID/OD 비율: {gt_ratio:.3f}")
            if b_ratio:
                b_err = abs(b_ratio - gt_ratio)
                print(f"    기존: {b_ratio:.3f} (오차: {b_err:.3f})")
            else:
                print(f"    기존: inner 미검출")
            if g_ratio:
                g_err = abs(g_ratio - gt_ratio)
                print(f"    가이드: {g_ratio:.3f} (오차: {g_err:.3f})")
            else:
                print(f"    가이드: inner 미검출")

            if b_ratio and g_ratio:
                if g_err < b_err:
                    print(f"    → ✅ 레이아웃 가이드가 더 정확 (오차 {b_err:.3f} → {g_err:.3f})")
                elif g_err > b_err:
                    print(f"    → 기존이 더 정확 (오차 {b_err:.3f} vs {g_err:.3f})")
                else:
                    print(f"    → 동일")
    elif guided_found and not baseline_found:
        print(f"    → ✅ 레이아웃 가이드만 성공! (기존은 실패)")
    elif baseline_found and not guided_found:
        print(f"    → 기존만 성공 (레이아웃 가이드 실패)")
    else:
        print(f"    → 둘 다 실패")

    # 시각화 저장
    save_comparison(image_path, regions, baseline_circles, guided_circles, drawing_id)


def save_comparison(image_path, regions, baseline, guided, drawing_id):
    """비교 시각화 저장"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    img = cv2.imread(str(image_path))

    # 레이아웃 영역 표시
    colors = {
        "circle_feature": (0, 255, 0),
        "section_view": (255, 0, 0),
        "title_block": (0, 0, 255),
        "table": (255, 255, 0),
        "notes": (0, 255, 255),
        "main_view": (255, 0, 255),
    }

    for cls_name, dets in regions.items():
        color = colors.get(cls_name, (128, 128, 128))
        for d in dets:
            x1, y1, x2, y2 = d["bbox"]
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 4)
            cv2.putText(img, f"{cls_name} {d['confidence']:.2f}",
                       (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)

    # 기존 원 (빨강)
    if baseline["found"]:
        o = baseline["outer"]
        cv2.circle(img, (int(o[0]), int(o[1])), int(o[2]), (0, 0, 255), 4)
        if baseline.get("inner") is not None:
            i = baseline["inner"]
            cv2.circle(img, (int(i[0]), int(i[1])), int(i[2]), (0, 0, 200), 3)

    # 가이드 원 (초록)
    if guided["found"]:
        o = guided["outer"]
        cv2.circle(img, (int(o[0]), int(o[1])), int(o[2]), (0, 255, 0), 4)
        if guided.get("inner") is not None:
            i = guided["inner"]
            cv2.circle(img, (int(i[0]), int(i[1])), int(i[2]), (0, 200, 0), 3)

    out = OUTPUT_DIR / f"{drawing_id}_comparison.jpg"
    cv2.imwrite(str(out), img)


def main():
    print("=" * 70)
    print("레이아웃 모델 + K 방법 통합 PoC")
    print(f"모델: {LAYOUT_MODEL_PATH}")
    print("=" * 70)

    model = YOLO(LAYOUT_MODEL_PATH)

    for drawing_id, gt in GT.items():
        test_drawing(model, drawing_id, gt)

    print(f"\n\n시각화: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
