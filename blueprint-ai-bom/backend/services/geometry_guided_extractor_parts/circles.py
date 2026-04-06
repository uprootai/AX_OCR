"""Circle detection helpers for geometry-guided dimension extraction."""

import logging
from typing import Dict

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def _detect_circles(img_gray: np.ndarray, orig_w: int, orig_h: int) -> Dict:
    """동심원 검출 — 컨투어+타원피팅 우선, HoughCircles 보조."""
    max_dim = 2000
    scale = 1.0
    img = img_gray.copy()
    if max(orig_h, orig_w) > max_dim:
        scale = max_dim / max(orig_h, orig_w)
        img = cv2.resize(img, (int(orig_w * scale), int(orig_h * scale)))

    rh, rw = img.shape[:2]

    result = _detect_circles_by_contour(img, rw, rh, scale)
    if result["found"]:
        logger.info(f"컨투어 기반 원 검출 성공: outer r={int(result['outer'][2])}")
        return result

    logger.info("컨투어 실패 → HoughCircles 폴백")
    return _detect_circles_by_hough(img, rw, rh, scale)


def _detect_circles_by_contour(img: np.ndarray, rw: int, rh: int, scale: float) -> Dict:
    """Canny 에지 → 컨투어 → 타원 피팅으로 원 검출."""
    blurred = cv2.GaussianBlur(img, (5, 5), 1.5)
    edges = cv2.Canny(blurred, 30, 100)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    dilated = cv2.dilate(edges, kernel, iterations=2)

    contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    min_area = rw * rh * 0.002
    max_radius = min(rw, rh) * 0.45
    candidates = []

    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area or len(contour) < 20:
            continue

        x, y, bw, bh = cv2.boundingRect(contour)
        bb_aspect = min(bw, bh) / max(bw, bh) if max(bw, bh) > 0 else 0
        if bb_aspect < 0.6:
            continue

        ellipse = cv2.fitEllipse(contour)
        (cx, cy), (ma, MA), angle = ellipse
        aspect = min(ma, MA) / max(ma, MA) if max(ma, MA) > 0 else 0
        if aspect < 0.6:
            continue

        radius_est = (ma + MA) / 4
        if radius_est > max_radius:
            continue

        orig_cx = cx / scale
        orig_cy = cy / scale
        orig_r = radius_est / scale

        if orig_cx < 0 or orig_cy < 0:
            continue

        candidates.append(
            {
                "coords": np.array([int(orig_cx), int(orig_cy), int(orig_r)]),
                "aspect": aspect,
            }
        )

    if not candidates:
        return {"found": False, "reason": "컨투어 기반 원 검출 실패"}

    logger.info(f"컨투어 원 후보 {len(candidates)}개 검출")
    candidates.sort(key=lambda candidate: candidate["aspect"] * candidate["coords"][2], reverse=True)
    outer = candidates[0]["coords"]

    inner = None
    for candidate in candidates[1:]:
        circle = candidate["coords"]
        dist = np.sqrt((circle[0] - outer[0]) ** 2 + (circle[1] - outer[1]) ** 2)
        if dist < outer[2] * 0.4 and 0.3 < circle[2] / outer[2] < 0.95:
            inner = circle
            break

    return {
        "found": True,
        "outer": outer,
        "inner": inner,
        "total_circles": len(candidates),
    }


def _detect_circles_by_hough(img: np.ndarray, rw: int, rh: int, scale: float) -> Dict:
    """HoughCircles 폴백 — 단순 도면용."""
    blurred = cv2.GaussianBlur(img, (9, 9), 2)
    min_r = min(rw, rh) // 20
    max_r = min(rw, rh) // 3

    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=min_r,
        param1=100,
        param2=50,
        minRadius=min_r,
        maxRadius=max_r,
    )

    if circles is None:
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1.5,
            minDist=min_r // 2,
            param1=80,
            param2=30,
            minRadius=min_r // 2,
            maxRadius=max_r,
        )

    if circles is None:
        return {"found": False, "reason": "HoughCircles 검출 실패"}

    circles_arr = np.round(circles[0]).astype(int)
    if scale != 1.0:
        circles_arr = np.round(circles_arr / scale).astype(int)

    sorted_by_r = sorted(circles_arr, key=lambda circle: circle[2], reverse=True)
    outer = sorted_by_r[0]

    inner = None
    for circle in sorted_by_r[1:]:
        dist = np.sqrt((circle[0] - outer[0]) ** 2 + (circle[1] - outer[1]) ** 2)
        if dist < outer[2] * 0.3 and circle[2] < outer[2] * 0.95:
            inner = circle
            break

    return {
        "found": True,
        "outer": outer,
        "inner": inner,
        "total_circles": len(circles_arr),
    }
