"""S06: YOLOv11 fine-tuned on dimension text regions + VLM classification.

Pipeline:
1. Generate pseudo-labels from K-method OCR (dimension text bboxes)
2. Fine-tune YOLOv11n on dimension text detection
3. Use Florence-2 grounding or simple rules to classify OD/ID/W

Step 1 only for now — generate YOLO dataset from existing OCR results.
"""
import torch
import numpy as np
import cv2
import json
from pathlib import Path
from PIL import Image
import sys
sys.path.insert(0, '/home/uproot/ax/poc/blueprint-ai-bom/backend')

print(f'CUDA: {torch.cuda.is_available()}, VRAM free: {torch.cuda.mem_get_info()[0]/1024**3:.1f}GB')

DATA_DIR = Path('/home/uproot/ax/poc/blueprint-ai-bom/data/dse_batch_test/converted_pngs')
YOLO_DIR = Path('/tmp/yolo_dimension_dataset')

png_files = sorted(DATA_DIR.glob('*.png'))[:20]  # First 20 for speed

# ── Step 1: Generate pseudo-labels from contour analysis (OCR-free) ──
print('\n--- Generating pseudo-labels from contour analysis ---')

all_labels = {}
for img_path in png_files:
    img = cv2.imread(str(img_path))
    if img is None:
        continue
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Binary threshold (engineering drawings are high contrast)
    _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    # Find connected components (text regions)
    n_labels_cc, label_map, stats, centroids = cv2.connectedComponentsWithStats(binary)

    labels = []
    for i in range(1, n_labels_cc):  # Skip background
        x1, y1, bw, bh, area = stats[i]
        x2, y2 = x1 + bw, y1 + bh

        # Filter: text-like aspect ratio and size
        aspect = bw / max(bh, 1)
        if area < 50 or area > w * h * 0.1:
            continue
        if bh < 8 or bh > h * 0.1:
            continue
        if bw < 10 or bw > w * 0.3:
            continue
        # Text is typically wider than tall, or square-ish
        if aspect < 0.3 or aspect > 15:
            continue

        cx = ((x1 + x2) / 2) / w
        cy = ((y1 + y2) / 2) / h
        nw = bw / w
        nh = bh / h

        labels.append(f'0 {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}')

    if labels:
        all_labels[img_path.stem] = labels[:50]  # Cap at 50 per image

print(f'Contour-based labels: {len(all_labels)} images')
for name, lbls in list(all_labels.items())[:3]:
    print(f'  {name}: {len(lbls)} text regions')

# ── Step 2: Create YOLO dataset ──

if len(all_labels) >= 3:
    print('\n--- Creating YOLO dataset ---')
    for split in ['train', 'val']:
        (YOLO_DIR / 'images' / split).mkdir(parents=True, exist_ok=True)
        (YOLO_DIR / 'labels' / split).mkdir(parents=True, exist_ok=True)

    names = list(all_labels.keys())
    n_train = max(1, len(names) - 3)
    train_names = names[:n_train]
    val_names = names[n_train:]

    for split, split_names in [('train', train_names), ('val', val_names)]:
        for name in split_names:
            # Symlink image
            src = DATA_DIR / f'{name}.png'
            dst = YOLO_DIR / 'images' / split / f'{name}.png'
            if not dst.exists():
                dst.symlink_to(src)
            # Write label
            with open(YOLO_DIR / 'labels' / split / f'{name}.txt', 'w') as f:
                f.write('\n'.join(all_labels[name]))

    # Write dataset YAML
    yaml_content = f"""path: {YOLO_DIR}
train: images/train
val: images/val
nc: 1
names: ['text_region']
"""
    with open(YOLO_DIR / 'data.yaml', 'w') as f:
        f.write(yaml_content)

    print(f'Dataset created: {n_train} train, {len(val_names)} val')
    print(f'YAML: {YOLO_DIR / "data.yaml"}')

    # ── Step 3: Fine-tune YOLOv11n ──
    print('\n--- Fine-tuning YOLOv11n ---')
    from ultralytics import YOLO

    model = YOLO('yolo11n.pt')
    results = model.train(
        data=str(YOLO_DIR / 'data.yaml'),
        epochs=20,
        imgsz=640,
        batch=4,
        device='cuda',
        project='/tmp/yolo_s06',
        name='dim_detect',
        exist_ok=True,
        verbose=False,
        workers=0,  # Avoid multiprocessing issues
    )
    print(f'Training complete.')

    # Evaluate
    print('\n--- Evaluation ---')
    metrics = model.val(data=str(YOLO_DIR / 'data.yaml'), verbose=False)
    print(f'mAP50: {metrics.box.map50:.3f}')
    print(f'mAP50-95: {metrics.box.map:.3f}')

    # Test on a specific image
    test_img = DATA_DIR / 'TD0062037.png'
    if test_img.exists():
        print(f'\n--- Test on T5 ({test_img.stem}) ---')
        results = model(str(test_img), verbose=False)
        for r in results:
            boxes = r.boxes
            print(f'Detected {len(boxes)} dimension regions:')
            for i, box in enumerate(boxes[:10]):
                cls_id = int(box.cls[0])
                cls_name = 'text_region' if cls_id == 0 else '?'
                conf = float(box.conf[0])
                xyxy = box.xyxy[0].tolist()
                print(f'  [{i}] {cls_name} ({conf:.2f}): [{xyxy[0]:.0f}, {xyxy[1]:.0f}, {xyxy[2]:.0f}, {xyxy[3]:.0f}]')
else:
    print('Insufficient data for YOLO training.')

torch.cuda.empty_cache()
print(f'\nVRAM after cleanup: {torch.cuda.mem_get_info()[0]/1024**3:.1f}GB')
print('Done.')
