#!/usr/bin/env python3
"""S05 — 합성 원 데이터 생성 + U-Net 학습

1단계: 87개 도면에서 HoughCircles로 원 영역 크롭
2단계: 크롭된 원을 랜덤 배치하여 1000개 합성 이미지 생성
3단계: U-Net (0.5M params) 학습 — dense circle mask label
"""

import cv2
import numpy as np
import os
import json
import random
import time
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

# ================================================================
# 1단계: 도면에서 원 크롭 수집
# ================================================================

SRC_DIR = Path(__file__).parent / ".." / "data" / "dse_batch_test" / "converted_pngs"
OUT_DIR = Path(__file__).parent / "s05_data"
CROP_DIR = OUT_DIR / "circle_crops"
SYNTH_DIR = OUT_DIR / "synthetic"
MODEL_DIR = OUT_DIR / "models"

IMG_SIZE = 256  # 학습 이미지 크기


def extract_circles_from_drawings(max_per_drawing=10):
    """87개 도면에서 HoughCircles로 원 크롭 수집"""
    CROP_DIR.mkdir(parents=True, exist_ok=True)
    crops = []

    pngs = sorted(SRC_DIR.glob("*.png"))
    print(f"[1/3] 원 크롭 수집 — {len(pngs)}개 도면")

    for png in pngs:
        img = cv2.imread(str(png))
        if img is None:
            continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        # 다양한 파라미터로 원 검출
        blurred = cv2.GaussianBlur(gray, (5, 5), 1.5)
        circles = cv2.HoughCircles(
            blurred, cv2.HOUGH_GRADIENT, dp=1.5,
            minDist=max(h, w) // 20,
            param1=100, param2=50,
            minRadius=max(h, w) // 40,
            maxRadius=max(h, w) // 4,
        )
        if circles is None:
            continue

        circles = np.round(circles[0]).astype(int)
        count = 0
        for cx, cy, r in circles:
            if count >= max_per_drawing:
                break
            # 유효 영역 체크
            x1, y1 = max(0, cx - r - 10), max(0, cy - r - 10)
            x2, y2 = min(w, cx + r + 10), min(h, cy + r + 10)
            if x2 - x1 < 30 or y2 - y1 < 30:
                continue
            crop = img[y1:y2, x1:x2]
            crop_name = f"{png.stem}_c{count}.png"
            cv2.imwrite(str(CROP_DIR / crop_name), crop)
            crops.append({
                "file": crop_name,
                "r_original": int(r),
                "crop_w": x2 - x1,
                "crop_h": y2 - y1,
            })
            count += 1

    print(f"  수집된 원 크롭: {len(crops)}개")
    with open(OUT_DIR / "crops_meta.json", "w") as f:
        json.dump(crops, f, indent=2)
    return crops


# ================================================================
# 2단계: 합성 이미지 생성
# ================================================================

def generate_synthetic_dataset(crops, n_images=1000):
    """크롭된 원을 랜덤 배치하여 합성 이미지 + mask 생성"""
    SYNTH_DIR.mkdir(parents=True, exist_ok=True)
    (SYNTH_DIR / "images").mkdir(exist_ok=True)
    (SYNTH_DIR / "masks").mkdir(exist_ok=True)

    print(f"\n[2/3] 합성 데이터 생성 — {n_images}개")

    crop_files = [c for c in crops if os.path.exists(str(CROP_DIR / c["file"]))]
    if not crop_files:
        print("  ERROR: 크롭 파일 없음")
        return []

    labels = []

    for i in range(n_images):
        # 빈 캔버스 (도면 느낌의 노이즈 배경)
        canvas = np.ones((IMG_SIZE, IMG_SIZE, 3), dtype=np.uint8) * 245
        mask = np.zeros((IMG_SIZE, IMG_SIZE), dtype=np.float32)

        # 배경 노이즈 (도면 선 모방)
        n_lines = random.randint(3, 15)
        for _ in range(n_lines):
            pt1 = (random.randint(0, IMG_SIZE), random.randint(0, IMG_SIZE))
            pt2 = (random.randint(0, IMG_SIZE), random.randint(0, IMG_SIZE))
            cv2.line(canvas, pt1, pt2, (200, 200, 200), random.randint(1, 2))

        # 1~3개 원 배치
        n_circles = random.randint(1, 3)
        circles_placed = []

        for _ in range(n_circles):
            crop_info = random.choice(crop_files)
            crop_img = cv2.imread(str(CROP_DIR / crop_info["file"]))
            if crop_img is None:
                continue

            # 랜덤 반지름 (20~80px)
            r = random.randint(20, 80)
            diameter = r * 2

            # 리사이즈
            crop_resized = cv2.resize(crop_img, (diameter, diameter))

            # 랜덤 위치 (캔버스 안에 들어가도록)
            cx = random.randint(r + 5, IMG_SIZE - r - 5)
            cy = random.randint(r + 5, IMG_SIZE - r - 5)

            # 원형 마스크로 블렌딩
            circle_mask = np.zeros((diameter, diameter), dtype=np.uint8)
            cv2.circle(circle_mask, (r, r), r, 255, -1)

            # 캔버스에 배치
            x1, y1 = cx - r, cy - r
            x2, y2 = x1 + diameter, y1 + diameter
            if x1 < 0 or y1 < 0 or x2 > IMG_SIZE or y2 > IMG_SIZE:
                continue

            roi = canvas[y1:y2, x1:x2]
            mask_3ch = cv2.merge([circle_mask, circle_mask, circle_mask])
            blended = np.where(mask_3ch > 0, crop_resized, roi)
            canvas[y1:y2, x1:x2] = blended

            # 원 테두리 (도면 스타일)
            cv2.circle(canvas, (cx, cy), r, (0, 0, 0), 1 + random.randint(0, 1))

            # Dense mask: 원 내부를 1.0으로
            cv2.circle(mask, (cx, cy), r, 1.0, -1)

            circles_placed.append({"cx": cx, "cy": cy, "r": r})

        # 랜덤 회전
        angle = random.choice([0, 0, 0, 90, 180, 270])
        if angle > 0:
            M = cv2.getRotationMatrix2D((IMG_SIZE // 2, IMG_SIZE // 2), angle, 1.0)
            canvas = cv2.warpAffine(canvas, M, (IMG_SIZE, IMG_SIZE),
                                     borderValue=(245, 245, 245))
            mask = cv2.warpAffine(mask, M, (IMG_SIZE, IMG_SIZE))

        # 저장
        cv2.imwrite(str(SYNTH_DIR / "images" / f"{i:04d}.png"), canvas)
        cv2.imwrite(str(SYNTH_DIR / "masks" / f"{i:04d}.png"),
                    (mask * 255).astype(np.uint8))
        labels.append({"id": i, "circles": circles_placed})

        if (i + 1) % 200 == 0:
            print(f"  {i + 1}/{n_images}")

    with open(SYNTH_DIR / "labels.json", "w") as f:
        json.dump(labels, f, indent=2)

    print(f"  생성 완료: {n_images}개 (images + masks)")
    return labels


# ================================================================
# 3단계: U-Net 학습
# ================================================================

class TinyUNet(nn.Module):
    """0.3M params U-Net — 최소 GPU 메모리"""

    def __init__(self):
        super().__init__()
        # Encoder
        self.enc1 = self._block(1, 16)
        self.enc2 = self._block(16, 32)
        self.enc3 = self._block(32, 64)
        self.pool = nn.MaxPool2d(2)

        # Bottleneck
        self.bot = self._block(64, 128)

        # Decoder
        self.up3 = nn.ConvTranspose2d(128, 64, 2, stride=2)
        self.dec3 = self._block(128, 64)
        self.up2 = nn.ConvTranspose2d(64, 32, 2, stride=2)
        self.dec2 = self._block(64, 32)
        self.up1 = nn.ConvTranspose2d(32, 16, 2, stride=2)
        self.dec1 = self._block(32, 16)

        self.out = nn.Conv2d(16, 1, 1)

    def _block(self, in_c, out_c):
        return nn.Sequential(
            nn.Conv2d(in_c, out_c, 3, padding=1),
            nn.BatchNorm2d(out_c),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_c, out_c, 3, padding=1),
            nn.BatchNorm2d(out_c),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool(e1))
        e3 = self.enc3(self.pool(e2))
        b = self.bot(self.pool(e3))
        d3 = self.dec3(torch.cat([self.up3(b), e3], 1))
        d2 = self.dec2(torch.cat([self.up2(d3), e2], 1))
        d1 = self.dec1(torch.cat([self.up1(d2), e1], 1))
        return torch.sigmoid(self.out(d1))


class CircleDataset(Dataset):
    def __init__(self, img_dir, mask_dir):
        self.imgs = sorted(Path(img_dir).glob("*.png"))
        self.mask_dir = Path(mask_dir)

    def __len__(self):
        return len(self.imgs)

    def __getitem__(self, idx):
        img = cv2.imread(str(self.imgs[idx]), cv2.IMREAD_GRAYSCALE)
        img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
        img = img.astype(np.float32) / 255.0

        mask_path = self.mask_dir / self.imgs[idx].name
        mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
        mask = cv2.resize(mask, (IMG_SIZE, IMG_SIZE))
        mask = (mask > 127).astype(np.float32)

        return (torch.tensor(img).unsqueeze(0),
                torch.tensor(mask).unsqueeze(0))


def train_model(n_epochs=80, batch_size=16, lr=1e-3):
    """U-Net 학습 — dense circle mask"""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n[3/3] U-Net 학습 — device={device}")

    dataset = CircleDataset(
        SYNTH_DIR / "images",
        SYNTH_DIR / "masks",
    )

    n_val = max(1, len(dataset) // 10)
    n_train = len(dataset) - n_val
    train_ds, val_ds = torch.utils.data.random_split(dataset, [n_train, n_val])

    train_dl = DataLoader(train_ds, batch_size=batch_size, shuffle=True,
                          num_workers=2, pin_memory=True)
    val_dl = DataLoader(val_ds, batch_size=batch_size, num_workers=2)

    model = TinyUNet().to(device)
    params = sum(p.numel() for p in model.parameters())
    print(f"  모델: TinyUNet ({params:,} params, {params * 4 / 1024 / 1024:.1f}MB)")
    print(f"  데이터: train={n_train}, val={n_val}")

    optimizer = optim.Adam(model.parameters(), lr=lr)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, n_epochs)

    # Dice + BCE loss
    bce = nn.BCELoss()

    def dice_loss(pred, target, smooth=1.0):
        pred_flat = pred.view(-1)
        target_flat = target.view(-1)
        intersection = (pred_flat * target_flat).sum()
        return 1 - (2 * intersection + smooth) / (pred_flat.sum() + target_flat.sum() + smooth)

    best_val = float("inf")
    t0 = time.time()

    for epoch in range(n_epochs):
        model.train()
        train_loss = 0
        for imgs, masks in train_dl:
            imgs, masks = imgs.to(device), masks.to(device)
            pred = model(imgs)
            loss = bce(pred, masks) + dice_loss(pred, masks)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            train_loss += loss.item()

        train_loss /= len(train_dl)

        # Validation
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for imgs, masks in val_dl:
                imgs, masks = imgs.to(device), masks.to(device)
                pred = model(imgs)
                loss = bce(pred, masks) + dice_loss(pred, masks)
                val_loss += loss.item()
        val_loss /= max(len(val_dl), 1)

        scheduler.step()

        if (epoch + 1) % 10 == 0 or epoch == 0:
            elapsed = time.time() - t0
            print(f"  epoch {epoch+1:3d}/{n_epochs} — "
                  f"train={train_loss:.4f} val={val_loss:.4f} "
                  f"({elapsed:.0f}s)")

        if val_loss < best_val:
            best_val = val_loss
            torch.save(model.state_dict(), MODEL_DIR / "circlenet_best.pt")

    elapsed = time.time() - t0
    print(f"\n  학습 완료: {elapsed:.1f}s, best_val={best_val:.4f}")
    print(f"  모델 저장: {MODEL_DIR / 'circlenet_best.pt'}")

    # 추론 테스트 — 실제 도면
    return evaluate_on_real(model, device)


def evaluate_on_real(model, device):
    """학습된 모델로 실제 도면에서 원 검출 테스트"""
    print("\n[평가] 실제 도면 추론")

    test_files = [
        ("TD0062015", "T1"),
        ("TD0062037", "T5"),
    ]

    results = []
    for drawing_no, name in test_files:
        img_path = SRC_DIR / f"{drawing_no}.png"
        if not img_path.exists():
            continue

        img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
        h_orig, w_orig = img.shape
        img_resized = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
        tensor = torch.tensor(img_resized.astype(np.float32) / 255.0).unsqueeze(0).unsqueeze(0).to(device)

        model.eval()
        with torch.no_grad():
            pred = model(tensor).squeeze().cpu().numpy()

        # 임계값 적용
        binary = (pred > 0.5).astype(np.uint8)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        circles_found = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 100:  # 너무 작은 건 무시
                continue
            (cx, cy), radius = cv2.minEnclosingCircle(cnt)
            # 원본 스케일로 변환
            cx_orig = cx * w_orig / IMG_SIZE
            cy_orig = cy * h_orig / IMG_SIZE
            r_orig = radius * max(w_orig, h_orig) / IMG_SIZE
            circles_found.append({
                "cx": round(cx_orig),
                "cy": round(cy_orig),
                "r": round(r_orig),
                "area": int(area),
            })

        circles_found.sort(key=lambda c: c["r"], reverse=True)
        print(f"  {name}: {len(circles_found)}개 원 검출 (상위 5: {[c['r'] for c in circles_found[:5]]})")
        results.append({"name": name, "circles": circles_found[:10]})

    # 결과 저장
    with open(OUT_DIR / "eval_results.json", "w") as f:
        json.dump(results, f, indent=2)

    return results


# ================================================================
# Main
# ================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  S05 — 합성 원 데이터 생성 + TinyUNet 학습")
    print("=" * 60)

    # 1. 원 크롭 수집
    crops = extract_circles_from_drawings()

    # 2. 합성 데이터 생성 (1000개)
    generate_synthetic_dataset(crops, n_images=1000)

    # 3. 학습 + 평가
    train_model(n_epochs=80, batch_size=16)

    print("\n" + "=" * 60)
    print("  완료!")
    print("=" * 60)
