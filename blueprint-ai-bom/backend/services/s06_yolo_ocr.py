"""S06: YOLO 텍스트 검출 → PaddleOCR 읽기 → 규칙 분류"""

import cv2
import re
from typing import Dict


def run_s06_yolo_ocr(image_path: str, model_path: str) -> Dict:
    """S06: YOLO 텍스트 검출 → PaddleOCR 읽기 → 규칙 분류"""
    import requests
    from ultralytics import YOLO

    model = YOLO(model_path)
    results = model(image_path, verbose=False, conf=0.3)
    if not results or not results[0].boxes:
        return {"od": None, "id": None, "w": None}

    img = cv2.imread(image_path)
    h, w_img = img.shape[:2]

    dim_values = []
    for box in results[0].boxes:
        cls_id = int(box.cls[0])
        if cls_id != 0:
            continue
        x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
        pad = 5
        x1, y1 = max(0, x1 - pad), max(0, y1 - pad)
        x2, y2 = min(w_img, x2 + pad), min(h, y2 + pad)
        crop = img[y1:y2, x1:x2]
        if crop.size == 0:
            continue

        _, buf = cv2.imencode('.png', crop)
        try:
            resp = requests.post(
                'http://localhost:5006/api/v1/ocr',
                files={'file': ('crop.png', buf.tobytes(), 'image/png')},
                timeout=10,
            )
            if resp.status_code == 200:
                for det in resp.json().get('detections', []):
                    text = det.get('text', '')
                    has_dia = any(c in text for c in 'ØøΦ⌀∅')
                    nums = re.findall(r'[\d.]+', text)
                    for n in nums:
                        try:
                            val = float(n)
                            if 10 <= val <= 9999:
                                cx = (x1 + x2) / 2
                                cy = (y1 + y2) / 2
                                dim_values.append({
                                    "val": val, "has_dia": has_dia,
                                    "cx": cx, "cy": cy,
                                    "is_horizontal": (x2 - x1) > (y2 - y1),
                                })
                        except ValueError:
                            pass
        except Exception:
            pass

    if not dim_values:
        return {"od": None, "id": None, "w": None}

    dia_cands = sorted(
        [d for d in dim_values if d["has_dia"]],
        key=lambda x: x["val"], reverse=True,
    )
    horiz_cands = sorted(
        [d for d in dim_values if d["is_horizontal"] and not d["has_dia"]],
        key=lambda x: x["val"],
    )
    all_sorted = sorted(dim_values, key=lambda x: x["val"], reverse=True)

    od = dia_cands[0]["val"] if dia_cands else (all_sorted[0]["val"] if all_sorted else None)
    id_val = None
    w_val = None

    if dia_cands and len(dia_cands) >= 2:
        id_val = dia_cands[1]["val"]
    elif all_sorted and len(all_sorted) >= 2:
        remaining = [d for d in all_sorted if d["val"] != od]
        if remaining:
            id_val = remaining[0]["val"]

    if horiz_cands:
        w_val = horiz_cands[0]["val"]
    elif all_sorted and len(all_sorted) >= 3:
        used = {od, id_val}
        for d in sorted(all_sorted, key=lambda x: x["val"]):
            if d["val"] not in used:
                w_val = d["val"]
                break

    return {
        "od": f"Ø{od:.0f}" if od else None,
        "id": f"{id_val:.0f}" if id_val else None,
        "w": f"{w_val:.0f}" if w_val else None,
    }
