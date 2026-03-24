"""YOLOv11 zero-shot detection on bearing drawings.

Tests what a pre-trained YOLO can detect on engineering drawings
without any fine-tuning. This baseline determines if YOLO-OBB
fine-tuning for dimension regions is worth pursuing.
"""
import torch
from ultralytics import YOLO
from PIL import Image
import json

print(f'CUDA: {torch.cuda.is_available()}, VRAM free: {torch.cuda.mem_get_info()[0]/1024**3:.1f}GB')

# Test with YOLO11n (smallest, fastest)
model = YOLO('yolo11n.pt')
print(f'Loaded YOLO11n')

img_path = '/home/uproot/ax/poc/blueprint-ai-bom/data/dse_batch_test/converted_pngs/TD0062037.png'
img = Image.open(img_path)
print(f'Image: {img.size}')

# Run detection
results = model(img, verbose=False)

for r in results:
    boxes = r.boxes
    print(f'\nDetected {len(boxes)} objects:')
    for i, box in enumerate(boxes):
        cls_id = int(box.cls[0])
        cls_name = model.names[cls_id]
        conf = float(box.conf[0])
        xyxy = box.xyxy[0].tolist()
        print(f'  [{i}] {cls_name} ({conf:.2f}): [{xyxy[0]:.0f}, {xyxy[1]:.0f}, {xyxy[2]:.0f}, {xyxy[3]:.0f}]')

# Also try YOLO11n-seg for segmentation
print('\n--- YOLO11n-seg ---')
model_seg = YOLO('yolo11n-seg.pt')
results_seg = model_seg(img, verbose=False)
for r in results_seg:
    boxes = r.boxes
    print(f'Detected {len(boxes)} objects (seg):')
    for i, box in enumerate(boxes):
        cls_id = int(box.cls[0])
        cls_name = model_seg.names[cls_id]
        conf = float(box.conf[0])
        print(f'  [{i}] {cls_name} ({conf:.2f})')

# Summary assessment for S06
print('\n--- S06 Assessment ---')
print('Pre-trained YOLO is for natural images (COCO classes).')
print('For engineering drawings, we need either:')
print('  1. Fine-tune on annotated dimension regions (need pseudo-labels)')
print('  2. Use YOLO just for text region detection (reuse as OCR preprocessor)')
print('  3. Skip YOLO, use Florence-2 grounding directly')

del model, model_seg
torch.cuda.empty_cache()
print('\nDone.')
