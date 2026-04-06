"""SECTION view detection and OCR scan helpers for dimension ensemble."""

import logging
import re
from typing import Dict, Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)

PADDLE_URL = "http://paddleocr-api:5006/api/v1/ocr"


def _paddle_ocr(png_bytes, timeout=60):
    """모듈 레벨 PaddleOCR 호출."""
    import requests

    try:
        resp = requests.post(
            PADDLE_URL,
            files={"file": ("img.png", png_bytes, "image/png")},
            timeout=timeout,
        )
        resp.raise_for_status()
        return resp.json().get("detections", [])
    except Exception:
        return []


def _to_img_bytes(img, fmt="JPEG"):
    """PIL Image → bytes 변환."""
    import io

    buf = io.BytesIO()
    if fmt == "JPEG":
        img = img.convert("RGB")
    img.save(buf, format=fmt, quality=90)
    return buf.getvalue()


def _auto_detect_section(image_path: str, paddle_fn, img_bytes_fn) -> Optional[Dict]:
    """OCR 앵커 + 콘텐츠 밀도로 SECTION 영역 자동 감지 (하드코딩 제거)."""
    from PIL import Image

    try:
        img_cv = cv2.imread(image_path)
        if img_cv is None:
            return None
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        pil_img = Image.open(image_path)
        full_bytes = img_bytes_fn(pil_img)
        dets = paddle_fn(full_bytes, timeout=120)

        anchors = {}
        for detection in dets:
            text = (detection.get("text", "") or "").upper()
            bbox = detection.get("bbox", [])
            if not (
                isinstance(bbox, list)
                and len(bbox) >= 4
                and isinstance(bbox[0], list)
            ):
                continue
            xs = [point[0] for point in bbox]
            ys = [point[1] for point in bbox]
            cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)

            if "SECTION" in text and len(text) > 5:
                anchors["section"] = {"cx": cx, "cy": cy, "y_top": min(ys)}
            elif "GEN" in text and "SIDE" in text:
                anchors["gen"] = {"cx": cx, "cy": cy}
            elif "TBN" in text and "SIDE" in text:
                anchors["tbn"] = {"cx": cx, "cy": cy}

        sec = anchors.get("section")
        if not sec:
            return None

        gen_x = anchors.get("gen", {}).get("cx", sec["cx"] - w * 0.15)
        tbn_x = anchors.get("tbn", {}).get("cx", sec["cx"] + w * 0.15)
        col_left = int(min(gen_x, tbn_x))
        col_right = int(max(gen_x, tbn_x))

        _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        label_y = int(sec["y_top"])
        content_top = label_y

        in_content = False
        for row_y in range(label_y, 0, -1):
            row = binary[row_y, col_left:col_right]
            density = np.sum(row > 0) / max(len(row), 1)
            if density > 0.03:
                in_content = True
            elif density < 0.005 and in_content:
                gap = sum(
                    1
                    for cy in range(row_y, max(row_y - 25, 0), -1)
                    if np.sum(binary[cy, col_left:col_right] > 0)
                    / max(col_right - col_left, 1)
                    < 0.005
                )
                if gap > 20:
                    content_top = row_y + 20
                    break

        margin_x = w * 0.03
        margin_y = h * 0.02
        return {
            "left": max(0, (col_left - margin_x)) / w,
            "top": max(0, (content_top - margin_y)) / h,
            "right": min(w, (col_right + margin_x)) / w,
            "bottom": min(h, (label_y + h * 0.05)) / h,
            "anchors": anchors,
            "ocr_dets": dets,
        }
    except Exception as exc:
        logger.warning(f"SECTION auto-detect failed: {exc}")
        return None


def _detect_drawing_views(
    ocr_dets: list,
    img_w: int,
    img_h: int,
    image_path: str = "",
) -> Dict[str, Dict]:
    """OCR 앵커 + 콘텐츠 밀도로 ASSY 도면의 4개 뷰 영역을 감지."""
    anchors = {}
    for detection in ocr_dets:
        text = (detection.get("text", "") or "").upper()
        bbox = detection.get("bbox", [])
        if not (isinstance(bbox, list) and len(bbox) >= 4 and isinstance(bbox[0], list)):
            continue
        xs = [point[0] for point in bbox]
        ys = [point[1] for point in bbox]
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)

        if "ISO" in text and "VIEW" in text:
            anchors["iso"] = {"cx": cx, "cy": cy}
        if "GEN" in text and "SIDE" in text:
            anchors["gen"] = {"cx": cx, "cy": cy}
        if "TBN" in text and "SIDE" in text:
            anchors["tbn"] = {"cx": cx, "cy": cy}

    views = {}
    iso_x = anchors.get("iso", {}).get("cx")
    gen_x = anchors.get("gen", {}).get("cx")
    tbn_x = anchors.get("tbn", {}).get("cx")

    sec_left = min(gen_x, tbn_x) / img_w if gen_x and tbn_x else 0.46
    right_bound = (iso_x / img_w - 0.02) if iso_x else 0.75

    left_right = min(sec_left, right_bound)
    split_y = None

    if image_path:
        try:
            img_cv = cv2.imread(image_path)
            if img_cv is not None:
                gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
                h_px, w_px = binary.shape

                scan_x1 = int(w_px * 0.05)
                scan_x2 = int(w_px * left_right)

                densities = []
                for row_y in range(int(h_px * 0.10), int(h_px * 0.60)):
                    row = binary[row_y, scan_x1:scan_x2]
                    density = np.sum(row > 0) / max(len(row), 1)
                    densities.append((row_y, density))

                gap_start = None
                gap_best = None
                gap_best_len = 0
                for row_y, density in densities:
                    if density < 0.01:
                        if gap_start is None:
                            gap_start = row_y
                    else:
                        if gap_start is not None:
                            gap_len = row_y - gap_start
                            if gap_len > gap_best_len:
                                gap_best = (gap_start, row_y)
                                gap_best_len = gap_len
                            gap_start = None
                if gap_start is not None:
                    last_y = densities[-1][0]
                    gap_len = last_y - gap_start
                    if gap_len > gap_best_len:
                        gap_best = (gap_start, last_y)
                        gap_best_len = gap_len

                if gap_best and gap_best_len > 15:
                    split_y = (gap_best[0] + gap_best[1]) / 2 / h_px
                    logger.info(f"View split: y={split_y:.3f} (gap={gap_best_len}px)")
        except Exception as exc:
            logger.warning(f"Content density scan failed: {exc}")

    if split_y is None:
        split_y = 0.30
        logger.info("View split: fallback y=0.30")

    views["auxiliary_view"] = {
        "left": 0.0,
        "top": 0.02,
        "right": left_right,
        "bottom": split_y - 0.01,
    }
    views["main_view"] = {
        "left": 0.0,
        "top": split_y,
        "right": sec_left,
        "bottom": 0.92,
    }

    if gen_x and tbn_x:
        sec_right = max(gen_x, tbn_x) / img_w
        views["section_view"] = {
            "left": sec_left - 0.02,
            "top": 0.25,
            "right": sec_right + 0.02,
            "bottom": 0.92,
        }

    if iso_x:
        views["iso_view"] = {
            "left": iso_x / img_w - 0.05,
            "top": 0.25,
            "right": 1.0,
            "bottom": 0.60,
        }

    return views


def _scan_side_view(
    image_path: str,
    side_region: Dict,
    hint_od: Optional[float] = None,
    hint_id: Optional[float] = None,
) -> Optional[float]:
    """측면도(축방향 뷰)에서 W(폭) 추출 — 단일 PaddleOCR 호출."""
    from PIL import Image, ImageEnhance

    img = Image.open(image_path)
    iw, ih = img.size
    x1 = int(iw * side_region["left"])
    y1 = int(ih * side_region["top"])
    x2 = int(iw * side_region["right"])
    y2 = int(ih * side_region["bottom"])
    crop = img.crop((x1, y1, x2, y2))
    cw, ch = crop.size
    if cw < 50 or ch < 50:
        return None

    up = crop.resize((cw * 2, ch * 2), Image.LANCZOS)
    enhanced = ImageEnhance.Contrast(up).enhance(1.5)
    dets = _paddle_ocr(_to_img_bytes(enhanced, fmt="PNG"))

    w_cands = []
    for detection in dets:
        text = detection.get("text", "")
        if re.match(r"^M\d", text, re.IGNORECASE):
            continue
        if re.search(r"TORQUE|NM$|SECTION|VIEW|SIDE|DWG|SCALE", text, re.IGNORECASE):
            continue
        if re.search(r"[ØøΦ⌀∅]", text):
            continue
        is_ref = bool(re.match(r"^\s*\(.*\)\s*$", text.strip()))
        cleaned = re.sub(r"[()]", "", text)
        match = re.search(r"(\d+\.?\d*)", cleaned)
        if not match:
            continue
        num = float(match.group(1))
        if num < 30 or num > 1000:
            continue
        if hint_od and num >= hint_od:
            continue
        bbox = detection.get("bbox", [])
        if isinstance(bbox, list) and len(bbox) >= 4 and isinstance(bbox[0], list):
            xs = [point[0] for point in bbox]
            ys = [point[1] for point in bbox]
            bw = max(xs) - min(xs)
            bh = max(ys) - min(ys)
            is_vertical = bh > bw * 1.2
            w_cands.append(
                {"num": num, "is_ref": is_ref, "is_vertical": is_vertical}
            )

    if not w_cands:
        return None

    if hint_id:
        for candidate in w_cands:
            if abs(candidate["num"] - hint_id) / max(hint_id, 1) < 0.05:
                logger.info(f"SIDE W: {candidate['num']} matches hint_id={hint_id}")
                return candidate["num"]

    non_ref_vert = [
        candidate
        for candidate in w_cands
        if not candidate["is_ref"] and candidate["is_vertical"]
    ]
    non_ref = [candidate for candidate in w_cands if not candidate["is_ref"]]
    pool = non_ref_vert or non_ref or w_cands
    pool.sort(key=lambda candidate: candidate["num"])
    return pool[0]["num"]


def _run_section_scan(image_path: str, drawing_title: str = "") -> Dict:
    """SEC: SECTION 단면도 세로 텍스트 스캔 → OD/ID/W 추출."""
    import time
    from PIL import Image, ImageEnhance

    _paddle = _paddle_ocr
    _img_bytes = _to_img_bytes

    img = Image.open(image_path)
    w, h = img.size

    sec_region = _auto_detect_section(image_path, _paddle, _img_bytes)
    if not sec_region:
        logger.info("SEC auto-detect failed, skipping SEC method (no hardcoded fallback)")
        return {
            "method_id": "SEC",
            "od": None,
            "id_val": None,
            "width": None,
            "classified_dims": [],
            "views": {},
        }

    views = _detect_drawing_views(sec_region.get("ocr_dets", []), w, h, image_path)
    logger.info(f"Views detected: {list(views.keys())}")

    sx1 = int(w * sec_region["left"])
    sy1 = int(h * sec_region["top"])
    sx2 = int(w * sec_region["right"])
    sy2 = int(h * sec_region["bottom"])
    logger.info(
        "SEC auto-detect: "
        f"left={sec_region['left']:.2f} "
        f"top={sec_region['top']:.2f} "
        f"right={sec_region['right']:.2f} "
        f"bottom={sec_region['bottom']:.2f}"
    )

    cropped = img.crop((sx1, sy1, sx2, sy2))
    cw, ch = cropped.size
    dets = _paddle(_img_bytes(cropped))

    nums = []
    for detection in dets:
        text = detection.get("text", "")
        if re.match(r"^M\d", text, re.IGNORECASE):
            continue
        if re.search(r"TORQUE|NM$", text, re.IGNORECASE):
            continue
        has_dia = bool(re.search(r"[ØøΦ⌀∅]", text))
        is_ref = bool(re.match(r"^\s*\(.*\)\s*$", text.strip()))
        cleaned = re.sub(r"[()]", "", text)
        match = re.search(r"(\d+\.?\d*)", cleaned)
        if not match:
            continue
        num = float(match.group(1))
        if num < 10 or num > 2000:
            continue
        bbox = detection.get("bbox", [])
        if isinstance(bbox, list) and len(bbox) >= 4 and isinstance(bbox[0], list):
            x_c = sum(point[0] for point in bbox) / len(bbox)
            y_c = sum(point[1] for point in bbox) / len(bbox)
        else:
            continue
        nums.append(
            {
                "num": num,
                "x": x_c / max(cw, 1),
                "y": y_c / max(ch, 1),
                "has_dia": has_dia,
                "is_ref": is_ref,
            }
        )

    hint_od = None
    match = re.search(r"OD\s*(\d+)", drawing_title, re.IGNORECASE)
    if match:
        hint_od = float(match.group(1))
    else:
        match = re.search(r"\((\d+)\s*[xX×]\s*(\d+)\)", drawing_title)
        if match:
            hint_od = float(match.group(1))
        else:
            match = re.search(r"(\d{3,4})\s*[xX×]\s*(\d{2,3})", drawing_title)
            if match:
                hint_od = float(match.group(1))

    id_cands = [
        num
        for num in nums
        if num["x"] < 0.60 and 0.30 < num["y"] < 0.70 and num["num"] >= 30
    ]
    od_ref = hint_od
    if od_ref:
        id_cands = [num for num in id_cands if num["num"] < od_ref * 0.95]

    id_dia = [num for num in id_cands if num["has_dia"]]
    id_large = [num for num in id_cands if num["num"] >= 100]
    if id_dia:
        id_dia.sort(key=lambda num: num["num"])
        id_val = id_dia[0]["num"]
    elif id_large:
        id_large.sort(key=lambda num: num["num"])
        id_val = id_large[0]["num"]
    elif id_cands:
        id_cands.sort(key=lambda num: num["num"], reverse=True)
        id_val = id_cands[0]["num"]
    else:
        id_val = None

    if not id_large and not id_dia:
        try:
            id_x2 = int(cw * 0.60)
            id_y1 = int(ch * 0.30)
            id_y2 = int(ch * 0.70)
            id_zone = cropped.crop((0, id_y1, id_x2, id_y2))
            arr = np.array(id_zone.convert("L"))
            adapt = cv2.adaptiveThreshold(
                arr,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                31,
                10,
            )
            adapt_img = Image.fromarray(adapt).resize(
                (adapt.shape[1] * 4, adapt.shape[0] * 4),
                Image.LANCZOS,
            )
            retry_dets = _paddle(_img_bytes(adapt_img, fmt="PNG"))
            for detection in retry_dets:
                text = detection.get("text", "")
                if re.match(r"^M\d", text, re.IGNORECASE):
                    continue
                cleaned = re.sub(r"[{}\[\]()]", "", text)
                match = re.search(r"(\d{3,4}\.?\d*)", cleaned)
                if match:
                    num = float(match.group(1))
                    od_limit = od_ref * 0.95 if od_ref else 2000
                    if 50 <= num <= min(od_limit, 2000):
                        id_val = num
                        logger.info(
                            f"SEC ID retry (adaptive): found {num} from '{text}'"
                        )
                        break
        except Exception as exc:
            logger.debug(f"SEC ID retry failed: {exc}")

    w_top_real = {
        int(num["num"])
        for num in nums
        if num["y"] < 0.20 and num["num"] >= 30 and not num.get("is_ref")
    }
    w_bot_real = {
        int(num["num"])
        for num in nums
        if num["y"] > 0.75 and num["num"] >= 30 and not num.get("is_ref")
    }
    w_top_all = {
        int(num["num"])
        for num in nums
        if num["y"] < 0.20 and num["num"] >= 30
    }
    w_bot_all = {
        int(num["num"])
        for num in nums
        if num["y"] > 0.75 and num["num"] >= 30
    }

    w_common_real = w_top_real & w_bot_real
    w_common_all = w_top_all & w_bot_all
    if w_common_real:
        w_val = float(min(w_common_real))
    elif w_common_all:
        w_val = float(min(w_common_all))
    elif w_bot_real:
        w_val = float(max(w_bot_real))
    elif w_bot_all:
        w_val = float(max(w_bot_all))
    elif w_top_real:
        w_val = float(min(w_top_real))
    elif w_top_all:
        w_val = float(min(w_top_all))
    else:
        w_val = None

    scan_left = sx1 + int((sx2 - sx1) * 0.30)
    scan_right = sx1 + int((sx2 - sx1) * 0.80)
    scan_height = sy2 - sy1
    od_found = []
    for frac in [0.15, 0.30, 0.45, 0.60, 0.75]:
        scan_top = sy1 + int(scan_height * frac)
        scan_bot = sy1 + int(scan_height * (frac + 0.20))
        strip = img.crop((scan_left, scan_top, scan_right, min(scan_bot, sy2)))
        rotated = strip.rotate(-90, expand=True)
        up = rotated.resize((rotated.width * 3, rotated.height * 3), Image.LANCZOS)
        enhanced = ImageEnhance.Contrast(up).enhance(1.8).convert("L")
        scan_dets = _paddle(_img_bytes(enhanced, fmt="PNG"))
        for detection in scan_dets:
            text = detection.get("text", "")
            cleaned = re.sub(r"^[(\s]*0?", "", text)
            match = re.search(r"(\d{3,4}\.?\d*)", cleaned)
            if match:
                num = float(match.group(1))
                if 100 < num < 2000 and num not in [found for found, _ in od_found]:
                    od_found.append((num, text))
        time.sleep(0.5)

    od_val = None
    if od_found:
        if hint_od:
            near = [
                (num, text)
                for num, text in od_found
                if abs(num - hint_od) / hint_od < 0.20
            ]
            od_val = near[0][0] if near else max(num for num, _ in od_found)
        else:
            od_val = max(num for num, _ in od_found)
    elif hint_od:
        od_val = hint_od

    return {
        "od": f"Ø{od_val:.0f}" if od_val else None,
        "id": f"{id_val:.0f}" if id_val else None,
        "w": f"{w_val:.0f}" if w_val else None,
        "views": views,
    }
