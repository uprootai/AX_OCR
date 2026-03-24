"""S05: CircleNet-inspired circle detection using simple CNN + heatmap.

Instead of full CenterNet architecture, use a lightweight approach:
1. Generate pseudo-label heatmaps from existing circle detections (K-method RANSAC)
2. Train a small U-Net to predict circle center heatmaps + radius regression
3. Evaluate on held-out drawings

This is a feasibility test — can we train a model to detect circles in bearing drawings?
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import cv2
from PIL import Image
from pathlib import Path
import json
import time

print(f'CUDA: {torch.cuda.is_available()}, VRAM free: {torch.cuda.mem_get_info()[0]/1024**3:.1f}GB')

# ── Step 1: Generate pseudo-labels from existing circle detection ──

DATA_DIR = Path('/home/uproot/ax/poc/blueprint-ai-bom/data/dse_batch_test/converted_pngs')
IMG_SIZE = 512  # Train at 512x512


def detect_circles_opencv(img_path, max_circles=20):
    """Detect circles using OpenCV HoughCircles as pseudo-labels."""
    img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        return [], img.shape[:2] if img is not None else (0, 0)
    h, w = img.shape[:2]

    # Resize for consistent detection
    scale = IMG_SIZE / max(h, w)
    img_r = cv2.resize(img, (int(w * scale), int(h * scale)))
    h_r, w_r = img_r.shape[:2]

    # Bilateral filter to reduce noise while preserving edges
    img_f = cv2.bilateralFilter(img_r, 9, 75, 75)

    # Detect circles
    circles_list = []
    for dp in [1.5, 2.0]:
        for min_dist in [30, 50]:
            circles = cv2.HoughCircles(
                img_f, cv2.HOUGH_GRADIENT, dp=dp,
                minDist=min_dist,
                param1=100, param2=40,
                minRadius=int(max(h_r, w_r) * 0.03),
                maxRadius=int(max(h_r, w_r) * 0.45),
            )
            if circles is not None:
                for c in circles[0]:
                    circles_list.append((float(c[0]), float(c[1]), float(c[2])))

    # Deduplicate (merge circles within 10px of each other)
    if not circles_list:
        return [], (h_r, w_r)

    merged = []
    used = set()
    for i, (x1, y1, r1) in enumerate(circles_list):
        if i in used:
            continue
        group = [(x1, y1, r1)]
        for j, (x2, y2, r2) in enumerate(circles_list):
            if j <= i or j in used:
                continue
            if np.sqrt((x1-x2)**2 + (y1-y2)**2) < 15:
                group.append((x2, y2, r2))
                used.add(j)
        used.add(i)
        avg_x = np.mean([g[0] for g in group])
        avg_y = np.mean([g[1] for g in group])
        avg_r = np.mean([g[2] for g in group])
        merged.append((avg_x, avg_y, avg_r))

    # Take top N by radius (larger circles are more likely to be bearing OD/ID)
    merged.sort(key=lambda c: c[2], reverse=True)
    return merged[:max_circles], (h_r, w_r)


def make_heatmap(circles, img_size, sigma=4):
    """Create Gaussian heatmap from circle centers."""
    h, w = img_size
    heatmap = np.zeros((h, w), dtype=np.float32)
    for cx, cy, r in circles:
        y, x = np.ogrid[0:h, 0:w]
        g = np.exp(-((x - cx)**2 + (y - cy)**2) / (2 * sigma**2))
        heatmap = np.maximum(heatmap, g)
    return heatmap


def prepare_input(img_path):
    """Load and preprocess image to tensor."""
    img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None
    h, w = img.shape[:2]
    scale = IMG_SIZE / max(h, w)
    img_r = cv2.resize(img, (int(w * scale), int(h * scale)))
    # Pad to IMG_SIZE x IMG_SIZE
    h_r, w_r = img_r.shape[:2]
    padded = np.zeros((IMG_SIZE, IMG_SIZE), dtype=np.uint8)
    padded[:h_r, :w_r] = img_r
    # Normalize
    tensor = torch.from_numpy(padded).float() / 255.0
    return tensor.unsqueeze(0)  # [1, H, W]


# ── Step 2: Simple U-Net-lite model ──

class CircleDetector(nn.Module):
    """Tiny U-Net for circle center heatmap prediction."""
    def __init__(self):
        super().__init__()
        # Encoder
        self.enc1 = nn.Sequential(
            nn.Conv2d(1, 32, 3, padding=1), nn.ReLU(),
            nn.Conv2d(32, 32, 3, padding=1), nn.ReLU(),
        )
        self.enc2 = nn.Sequential(
            nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(),
            nn.Conv2d(64, 64, 3, padding=1), nn.ReLU(),
        )
        self.enc3 = nn.Sequential(
            nn.Conv2d(64, 128, 3, padding=1), nn.ReLU(),
            nn.Conv2d(128, 128, 3, padding=1), nn.ReLU(),
        )
        # Decoder
        self.up2 = nn.ConvTranspose2d(128, 64, 2, stride=2)
        self.dec2 = nn.Sequential(
            nn.Conv2d(128, 64, 3, padding=1), nn.ReLU(),
            nn.Conv2d(64, 64, 3, padding=1), nn.ReLU(),
        )
        self.up1 = nn.ConvTranspose2d(64, 32, 2, stride=2)
        self.dec1 = nn.Sequential(
            nn.Conv2d(64, 32, 3, padding=1), nn.ReLU(),
            nn.Conv2d(32, 32, 3, padding=1), nn.ReLU(),
        )
        # Output: heatmap (1ch) + radius (1ch)
        self.head = nn.Conv2d(32, 2, 1)
        self.pool = nn.MaxPool2d(2)

    def forward(self, x):
        # Encoder
        e1 = self.enc1(x)        # [B, 32, H, W]
        e2 = self.enc2(self.pool(e1))  # [B, 64, H/2, W/2]
        e3 = self.enc3(self.pool(e2))  # [B, 128, H/4, W/4]
        # Decoder
        d2 = self.up2(e3)  # [B, 64, H/2, W/2]
        d2 = self.dec2(torch.cat([d2, e2], dim=1))
        d1 = self.up1(d2)  # [B, 32, H, W]
        d1 = self.dec1(torch.cat([d1, e1], dim=1))
        out = self.head(d1)  # [B, 2, H, W]
        heatmap = torch.sigmoid(out[:, 0:1])  # [B, 1, H, W]
        radius = torch.relu(out[:, 1:2])      # [B, 1, H, W]
        return heatmap, radius


# ── Step 3: Generate dataset ──

print('\n--- Generating pseudo-labels ---')
png_files = sorted(DATA_DIR.glob('*.png'))
print(f'Found {len(png_files)} PNG files')

dataset = []
for img_path in png_files[:30]:  # Use first 30 for speed
    circles, img_sz = detect_circles_opencv(img_path)
    if not circles:
        continue
    inp = prepare_input(img_path)
    if inp is None:
        continue
    heatmap = make_heatmap(circles, (IMG_SIZE, IMG_SIZE), sigma=6)
    # Radius map: at each circle center, store the radius
    radius_map = np.zeros((IMG_SIZE, IMG_SIZE), dtype=np.float32)
    for cx, cy, r in circles:
        y, x = int(cy), int(cx)
        if 0 <= y < IMG_SIZE and 0 <= x < IMG_SIZE:
            # Paint radius in a small area around center
            for dy in range(-3, 4):
                for dx in range(-3, 4):
                    yy, xx = y+dy, x+dx
                    if 0 <= yy < IMG_SIZE and 0 <= xx < IMG_SIZE:
                        radius_map[yy, xx] = r / IMG_SIZE  # Normalized
    dataset.append({
        'input': inp,
        'heatmap': torch.from_numpy(heatmap).unsqueeze(0),
        'radius': torch.from_numpy(radius_map).unsqueeze(0),
        'name': img_path.stem,
        'circles': circles,
    })
    if len(dataset) % 10 == 0:
        print(f'  Processed {len(dataset)} images...')

print(f'Dataset: {len(dataset)} images with circles')

if len(dataset) < 5:
    print('Not enough data for training. Exiting.')
    exit(0)

# ── Step 4: Train ──

print('\n--- Training CircleDetector ---')
model = CircleDetector().cuda()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
n_params = sum(p.numel() for p in model.parameters())
print(f'Model params: {n_params:,} ({n_params*4/1024**2:.1f}MB)')

# Split
n_train = max(1, len(dataset) - 5)
train_data = dataset[:n_train]
val_data = dataset[n_train:]
print(f'Train: {n_train}, Val: {len(val_data)}')

best_val_loss = float('inf')
start = time.time()

for epoch in range(50):
    model.train()
    epoch_loss = 0
    np.random.shuffle(train_data)
    for item in train_data:
        inp = item['input'].unsqueeze(0).cuda()  # [1, 1, H, W]
        gt_hm = item['heatmap'].unsqueeze(0).cuda()
        gt_r = item['radius'].unsqueeze(0).cuda()

        pred_hm, pred_r = model(inp)

        # Focal loss for heatmap
        pos_mask = (gt_hm > 0.5).float()
        neg_mask = 1 - pos_mask
        pos_loss = -pos_mask * (1 - pred_hm)**2 * torch.log(pred_hm + 1e-8)
        neg_loss = -neg_mask * pred_hm**2 * torch.log(1 - pred_hm + 1e-8)
        hm_loss = (pos_loss + neg_loss).mean()

        # L1 loss for radius (only at circle centers)
        r_mask = (gt_r > 0).float()
        r_loss = (torch.abs(pred_r - gt_r) * r_mask).sum() / (r_mask.sum() + 1e-8)

        loss = hm_loss + 0.1 * r_loss
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        epoch_loss += loss.item()

    # Validation
    model.eval()
    val_loss = 0
    with torch.no_grad():
        for item in val_data:
            inp = item['input'].unsqueeze(0).cuda()
            gt_hm = item['heatmap'].unsqueeze(0).cuda()
            pred_hm, _ = model(inp)
            pos_mask = (gt_hm > 0.5).float()
            neg_mask = 1 - pos_mask
            pos_loss = -pos_mask * (1 - pred_hm)**2 * torch.log(pred_hm + 1e-8)
            neg_loss = -neg_mask * pred_hm**2 * torch.log(1 - pred_hm + 1e-8)
            val_loss += (pos_loss + neg_loss).mean().item()

    avg_train = epoch_loss / len(train_data)
    avg_val = val_loss / max(len(val_data), 1)

    if (epoch + 1) % 10 == 0 or epoch == 0:
        elapsed = time.time() - start
        print(f'  Epoch {epoch+1:3d} | train_loss={avg_train:.4f} | val_loss={avg_val:.4f} | {elapsed:.0f}s')

    if avg_val < best_val_loss:
        best_val_loss = avg_val

print(f'\nBest val loss: {best_val_loss:.4f}')
print(f'Total training time: {time.time()-start:.0f}s')

# ── Step 5: Evaluate ──

print('\n--- Evaluation on validation set ---')
model.eval()
for item in val_data:
    inp = item['input'].unsqueeze(0).cuda()
    with torch.no_grad():
        pred_hm, pred_r = model(inp)

    # Find peaks in heatmap
    hm = pred_hm[0, 0].cpu().numpy()
    # Simple peak detection: threshold + NMS
    peaks = []
    threshold = 0.3
    mask = (hm > threshold).astype(np.uint8)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        M = cv2.moments(cnt)
        if M['m00'] > 0:
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])
            conf = hm[cy, cx]
            r = pred_r[0, 0, cy, cx].item() * IMG_SIZE
            peaks.append((cx, cy, r, conf))

    gt_circles = item['circles']
    print(f'\n  {item["name"]}:')
    print(f'    GT circles: {len(gt_circles)} (top 3: {[(round(c[0]),round(c[1]),round(c[2])) for c in gt_circles[:3]]})')
    print(f'    Predicted peaks: {len(peaks)} (top 3: {[(p[0],p[1],round(p[2]),round(p[3],2)) for p in sorted(peaks, key=lambda x:-x[3])[:3]]})')

# Save model
model_path = '/tmp/circle_detector_s05.pt'
torch.save(model.state_dict(), model_path)
print(f'\nModel saved to {model_path}')

del model
torch.cuda.empty_cache()
print(f'VRAM after cleanup: {torch.cuda.mem_get_info()[0]/1024**3:.1f}GB')
print('Done.')
