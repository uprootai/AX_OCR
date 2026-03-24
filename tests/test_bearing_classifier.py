"""Bearing vs Non-Bearing classifier for DSE batch drawings."""
import json, re, time
from pathlib import Path
import cv2, numpy as np, requests

DATA_DIR = Path("/home/uproot/ax/poc/blueprint-ai-bom/data/dse_batch_test/converted_pngs")
OCR_URL = "http://localhost:5006/api/v1/ocr"
OUTPUT = Path("/tmp/bearing_classification.json")


def detect_circles(img_path):
    """Count large circles via HoughCircles (resized for speed)."""
    img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        return 0
    h, w = img.shape
    # Resize to max 1024 for speed
    max_side = 1024
    scale = min(max_side / w, max_side / h)
    if scale < 1:
        img = cv2.resize(img, (int(w * scale), int(h * scale)))
        h, w = img.shape
    diag = np.sqrt(h**2 + w**2)
    blur = cv2.GaussianBlur(img, (9, 9), 2)
    circles = cv2.HoughCircles(
        blur, cv2.HOUGH_GRADIENT, dp=1.5, minDist=diag * 0.08,
        param1=80, param2=40,
        minRadius=int(diag * 0.05), maxRadius=int(diag * 0.5),
    )
    return len(circles[0]) if circles is not None else 0


def ocr_features(img_path):
    """Get Ø presence and large dimension count from PaddleOCR."""
    try:
        with open(img_path, 'rb') as f:
            resp = requests.post(OCR_URL, files={'file': f}, timeout=15)
        if resp.status_code != 200:
            return False, 0
        detections = resp.json().get('detections', [])
        texts = [d.get('text', '') for d in detections]
        full = ' '.join(texts)
        has_dia = bool(re.search(r'[Øøφ⌀∅]', full))
        nums = re.findall(r'\d{2,4}(?:\.\d{1,2})?', full)
        large = [float(n) for n in nums if 50 <= float(n) <= 5000]
        return has_dia, len(set(large))
    except Exception:
        return False, 0


def classify(n_circles, has_dia, n_large_dims):
    """Simple bearing heuristic."""
    if n_circles >= 2 and has_dia:
        return True, 0.95, f"{n_circles} circles + Ø"
    if n_circles >= 3:
        return True, 0.85, f"{n_circles} circles"
    if n_circles >= 2 and n_large_dims >= 3:
        return True, 0.80, f"{n_circles} circles + {n_large_dims} dims"
    if has_dia and n_large_dims >= 3:
        return True, 0.75, f"Ø + {n_large_dims} dims"
    if n_circles == 0 and not has_dia and n_large_dims < 2:
        return False, 0.90, "no circles, no Ø, few dims"
    if n_circles == 0 and not has_dia:
        return False, 0.80, "no circles, no Ø"
    if n_circles <= 1 and n_large_dims <= 2:
        return False, 0.65, f"{n_circles} circles, {n_large_dims} dims"
    # Ambiguous
    return True, 0.55, f"{n_circles} circles, Ø={has_dia}, {n_large_dims} dims"


# --- Run ---
png_files = sorted(DATA_DIR.glob('*.png'))
print(f'Classifying {len(png_files)} drawings...\n')

results = {}
start = time.time()

for i, f in enumerate(png_files):
    n_circles = detect_circles(f)
    has_dia, n_dims = ocr_features(f)
    is_bearing, conf, reason = classify(n_circles, has_dia, n_dims)
    results[f.stem] = {
        "is_bearing": is_bearing,
        "confidence": conf,
        "reason": reason,
        "n_circles": n_circles,
        "has_diameter_symbol": has_dia,
        "n_large_dims": n_dims,
    }
    if (i + 1) % 20 == 0:
        print(f'  {i+1}/{len(png_files)} ({time.time()-start:.0f}s)')

elapsed = time.time() - start
print(f'\nDone in {elapsed:.0f}s ({elapsed/len(png_files):.1f}s/drawing)\n')

# --- Summary ---
bearings = {k: v for k, v in results.items() if v["is_bearing"]}
non_bearings = {k: v for k, v in results.items() if not v["is_bearing"]}

print(f'=== Classification ===')
print(f'  Bearing: {len(bearings)} / {len(results)}')
print(f'  Non-Bearing: {len(non_bearings)} / {len(results)}')

# Cross-ref with ensemble results
prev_path = Path('/tmp/batch_ensemble_results.json')
if prev_path.exists():
    prev = json.loads(prev_path.read_text())
    all_fail = [k for k, v in prev.items() if not (v.get("od") and v.get("id") and v.get("w"))]
    non_b_in_fail = [k for k in all_fail if k in non_bearings]
    print(f'\n  Ensemble all-fail: {len(all_fail)} drawings')
    print(f'  Of which non-bearing: {len(non_b_in_fail)} ({len(non_b_in_fail)/max(len(all_fail),1)*100:.0f}%)')
    print(f'  Bearing but failed: {len(all_fail) - len(non_b_in_fail)}')

    # Effective accuracy: bearing-only
    bearing_total = len(bearings)
    bearing_detected = sum(1 for k in bearings if k in prev and prev[k].get("od") and prev[k].get("id") and prev[k].get("w"))
    print(f'\n  Bearing-only accuracy: {bearing_detected}/{bearing_total} ({bearing_detected/max(bearing_total,1)*100:.0f}%)')

print(f'\n=== Non-Bearing Drawings ===')
for name, v in sorted(non_bearings.items()):
    print(f'  {name}: {v["reason"]} (conf={v["confidence"]:.2f})')

OUTPUT.write_text(json.dumps(results, indent=2, ensure_ascii=False))
print(f'\nSaved to {OUTPUT}')
