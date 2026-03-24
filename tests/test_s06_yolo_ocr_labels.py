"""S06 Retry: YOLOv11 dimension text detection with OCR-based pseudo-labels.

ML containers are running — use PaddleOCR to get accurate text bboxes,
then fine-tune YOLOv11n to detect dimension text regions in drawings.
"""
import torch
import numpy as np
import cv2
import json
import requests
from pathlib import Path
from PIL import Image
import time

print(f'CUDA: {torch.cuda.is_available()}, VRAM free: {torch.cuda.mem_get_info()[0]/1024**3:.1f}GB')

DATA_DIR = Path('/home/uproot/ax/poc/blueprint-ai-bom/data/dse_batch_test/converted_pngs')
YOLO_DIR = Path('/tmp/yolo_dim_ocr_dataset')
PADDLE_URL = 'http://localhost:5006/api/v1/ocr'

# ── Step 1: Get OCR bboxes from PaddleOCR ──

print('\n--- Extracting OCR bboxes from PaddleOCR ---')
png_files = sorted(DATA_DIR.glob('*.png'))
print(f'Found {len(png_files)} PNG files')

all_labels = {}
ocr_cache = {}
failed = 0

for idx, img_path in enumerate(png_files):
    try:
        with open(img_path, 'rb') as f:
            resp = requests.post(PADDLE_URL, files={'file': f}, timeout=30)
        if resp.status_code != 200:
            failed += 1
            continue
        data = resp.json()
    except Exception as e:
        failed += 1
        continue

    # Extract text regions with bboxes
    results = data.get('detections', data.get('results', data.get('result', [])))
    if not results:
        results = data.get('data', {}).get('results', [])

    img = cv2.imread(str(img_path))
    if img is None:
        continue
    h, w = img.shape[:2]

    labels = []
    dim_texts = []
    for item in results:
        text = item.get('text', '')
        bbox = item.get('bbox', item.get('box', item.get('points', [])))
        conf = item.get('confidence', item.get('score', 0))

        if conf < 0.3:
            continue

        # Parse bbox (PaddleOCR returns [[x1,y1],[x2,y2],[x3,y3],[x4,y4]])
        if isinstance(bbox, list) and len(bbox) >= 4:
            if isinstance(bbox[0], (list, tuple)):
                xs = [p[0] for p in bbox]
                ys = [p[1] for p in bbox]
                x1, y1, x2, y2 = min(xs), min(ys), max(xs), max(ys)
            elif len(bbox) == 4:
                x1, y1, x2, y2 = bbox
            else:
                continue
        elif isinstance(bbox, dict):
            x1 = bbox.get('x1', bbox.get('left', 0))
            y1 = bbox.get('y1', bbox.get('top', 0))
            x2 = bbox.get('x2', bbox.get('right', 0))
            y2 = bbox.get('y2', bbox.get('bottom', 0))
        else:
            continue

        # Validate
        if x2 <= x1 or y2 <= y1:
            continue
        if (x2 - x1) < 5 or (y2 - y1) < 5:
            continue

        # YOLO format: class cx cy w h (normalized)
        cx = ((x1 + x2) / 2) / w
        cy = ((y1 + y2) / 2) / h
        bw = (x2 - x1) / w
        bh = (y2 - y1) / h

        # Skip too large or too small
        if bw > 0.5 or bh > 0.3 or bw < 0.005 or bh < 0.003:
            continue

        # Classify based on text content
        # 0: dimension_number (contains digits, possibly with Ø/R prefix)
        # 1: annotation_text (tolerances, notes, materials)
        import re
        is_dimension = bool(re.search(r'[\dØøR]\d{1,4}', text.replace(' ', '')))
        cls = 0 if is_dimension else 1

        labels.append(f'{cls} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}')
        dim_texts.append({'text': text, 'cls': cls, 'bbox': [x1, y1, x2, y2]})

    if labels:
        all_labels[img_path.stem] = labels
        ocr_cache[img_path.stem] = dim_texts

    if (idx + 1) % 20 == 0:
        print(f'  Processed {idx+1}/{len(png_files)} ({len(all_labels)} with labels, {failed} failed)')

print(f'\nTotal: {len(all_labels)} images with OCR labels, {failed} failed')

# Show sample
for name in list(all_labels.keys())[:3]:
    dims = [t for t in ocr_cache[name] if t['cls'] == 0]
    annots = [t for t in ocr_cache[name] if t['cls'] == 1]
    print(f'  {name}: {len(dims)} dimensions, {len(annots)} annotations')
    for d in dims[:5]:
        print(f'    dim: "{d["text"]}" @ {d["bbox"]}')

if len(all_labels) < 5:
    print('Not enough labeled data. Exiting.')
    exit(0)

# ── Step 2: Create YOLO dataset ──

print('\n--- Creating YOLO dataset ---')
for split in ['train', 'val']:
    (YOLO_DIR / 'images' / split).mkdir(parents=True, exist_ok=True)
    (YOLO_DIR / 'labels' / split).mkdir(parents=True, exist_ok=True)

names = list(all_labels.keys())
n_val = max(5, len(names) // 5)  # 20% validation
n_train = len(names) - n_val
train_names = names[:n_train]
val_names = names[n_train:]

for split, split_names in [('train', train_names), ('val', val_names)]:
    for name in split_names:
        src = DATA_DIR / f'{name}.png'
        dst = YOLO_DIR / 'images' / split / f'{name}.png'
        if dst.exists():
            dst.unlink()
        dst.symlink_to(src)
        with open(YOLO_DIR / 'labels' / split / f'{name}.txt', 'w') as f:
            f.write('\n'.join(all_labels[name]))

yaml_content = f"""path: {YOLO_DIR}
train: images/train
val: images/val
nc: 2
names: ['dimension_number', 'annotation_text']
"""
with open(YOLO_DIR / 'data.yaml', 'w') as f:
    f.write(yaml_content)

print(f'Dataset: {n_train} train, {n_val} val')

# ── Step 3: Fine-tune YOLOv11n ──

print('\n--- Fine-tuning YOLOv11n on OCR-labeled dimension text ---')
from ultralytics import YOLO

model = YOLO('yolo11n.pt')
start = time.time()

results = model.train(
    data=str(YOLO_DIR / 'data.yaml'),
    epochs=50,
    imgsz=640,
    batch=4,
    device='cuda',
    project='/tmp/yolo_s06_ocr',
    name='dim_detect_v2',
    exist_ok=True,
    verbose=False,
    workers=0,
    patience=10,  # Early stopping
)
elapsed = time.time() - start
print(f'Training complete in {elapsed:.0f}s')

# ── Step 4: Evaluate ──

print('\n--- Evaluation ---')
metrics = model.val(data=str(YOLO_DIR / 'data.yaml'), verbose=False)
print(f'mAP50: {metrics.box.map50:.3f}')
print(f'mAP50-95: {metrics.box.map:.3f}')

# Test on T5
test_img = DATA_DIR / 'TD0062037.png'
if test_img.exists():
    print(f'\n--- Test on T5 ({test_img.stem}) ---')
    preds = model(str(test_img), verbose=False, conf=0.25)
    for r in preds:
        boxes = r.boxes
        dims = [(int(b.cls[0]), float(b.conf[0]), b.xyxy[0].tolist()) for b in boxes]
        dim_nums = [d for d in dims if d[0] == 0]
        annots = [d for d in dims if d[0] == 1]
        print(f'  Dimension numbers: {len(dim_nums)}')
        for cls_id, conf, xyxy in sorted(dim_nums, key=lambda x: -x[1])[:10]:
            print(f'    ({conf:.2f}) [{xyxy[0]:.0f}, {xyxy[1]:.0f}, {xyxy[2]:.0f}, {xyxy[3]:.0f}]')
        print(f'  Annotations: {len(annots)}')

# Save model path
best_model = Path('/tmp/yolo_s06_ocr/dim_detect_v2/weights/best.pt')
print(f'\nBest model: {best_model}')
print(f'Model size: {best_model.stat().st_size / 1024**2:.1f}MB' if best_model.exists() else 'Model not found')

torch.cuda.empty_cache()
print(f'VRAM after cleanup: {torch.cuda.mem_get_info()[0]/1024**3:.1f}GB')
print('Done.')
