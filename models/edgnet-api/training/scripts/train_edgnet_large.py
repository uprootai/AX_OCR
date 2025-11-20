#!/usr/bin/env python3
"""
EDGNet 대규모 학습 스크립트
증강된 데이터셋으로 프로덕션급 모델 학습
"""

import os
import sys
import argparse
import time
import json
from pathlib import Path
from datetime import datetime

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import cv2
import numpy as np
from tqdm import tqdm

# 간단한 UNet 모델 정의
class UNet(nn.Module):
    """UNet 세그멘테이션 모델"""

    def __init__(self, in_channels=1, out_channels=1):
        super(UNet, self).__init__()

        # Encoder
        self.enc1 = self.conv_block(in_channels, 64)
        self.enc2 = self.conv_block(64, 128)
        self.enc3 = self.conv_block(128, 256)
        self.enc4 = self.conv_block(256, 512)

        # Bottleneck
        self.bottleneck = self.conv_block(512, 1024)

        # Decoder
        self.upconv4 = nn.ConvTranspose2d(1024, 512, kernel_size=2, stride=2)
        self.dec4 = self.conv_block(1024, 512)

        self.upconv3 = nn.ConvTranspose2d(512, 256, kernel_size=2, stride=2)
        self.dec3 = self.conv_block(512, 256)

        self.upconv2 = nn.ConvTranspose2d(256, 128, kernel_size=2, stride=2)
        self.dec2 = self.conv_block(256, 128)

        self.upconv1 = nn.ConvTranspose2d(128, 64, kernel_size=2, stride=2)
        self.dec1 = self.conv_block(128, 64)

        # Output
        self.out = nn.Conv2d(64, out_channels, kernel_size=1)

        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)

    def conv_block(self, in_channels, out_channels):
        """Convolutional block"""
        return nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        # Encoder
        enc1 = self.enc1(x)
        enc2 = self.enc2(self.pool(enc1))
        enc3 = self.enc3(self.pool(enc2))
        enc4 = self.enc4(self.pool(enc3))

        # Bottleneck
        bottleneck = self.bottleneck(self.pool(enc4))

        # Decoder with skip connections
        dec4 = self.upconv4(bottleneck)
        dec4 = torch.cat([dec4, enc4], dim=1)
        dec4 = self.dec4(dec4)

        dec3 = self.upconv3(dec4)
        dec3 = torch.cat([dec3, enc3], dim=1)
        dec3 = self.dec3(dec3)

        dec2 = self.upconv2(dec3)
        dec2 = torch.cat([dec2, enc2], dim=1)
        dec2 = self.dec2(dec2)

        dec1 = self.upconv1(dec2)
        dec1 = torch.cat([dec1, enc1], dim=1)
        dec1 = self.dec1(dec1)

        return torch.sigmoid(self.out(dec1))


class EDGNetDataset(Dataset):
    """EDGNet 데이터셋"""

    def __init__(self, data_dir, image_size=512, augment=True):
        self.data_dir = Path(data_dir)
        self.image_size = image_size
        self.augment = augment

        # 이미지 파일 찾기
        self.image_files = []
        for ext in ['.jpg', '.jpeg', '.png', '.bmp']:
            self.image_files.extend(list(self.data_dir.glob(f'*{ext}')))
            self.image_files.extend(list(self.data_dir.glob(f'*{ext.upper()}')))

        # augmentation_metadata.json 제외
        self.image_files = [f for f in self.image_files if 'metadata' not in f.name.lower()]

        print(f"Found {len(self.image_files)} images in {data_dir}")

    def __len__(self):
        return len(self.image_files)

    def __getitem__(self, idx):
        # 이미지 로드
        img_path = self.image_files[idx]
        image = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)

        if image is None:
            raise ValueError(f"Failed to load image: {img_path}")

        # 리사이즈
        image = cv2.resize(image, (self.image_size, self.image_size))

        # 간단한 타겟 생성 (엣지 검출)
        # 실제로는 별도의 ground truth가 필요하지만, 여기서는 Canny edge를 타겟으로 사용
        target = cv2.Canny(image, 50, 150)

        # 정규화
        image = image.astype(np.float32) / 255.0
        target = target.astype(np.float32) / 255.0

        # Tensor로 변환
        image = torch.from_numpy(image).unsqueeze(0)  # [1, H, W]
        target = torch.from_numpy(target).unsqueeze(0)  # [1, H, W]

        return image, target


class DiceBCELoss(nn.Module):
    """Dice Loss + Binary Cross Entropy Loss"""

    def __init__(self, weight=None, size_average=True):
        super(DiceBCELoss, self).__init__()

    def forward(self, inputs, targets, smooth=1):
        # BCE loss
        bce = nn.functional.binary_cross_entropy(inputs, targets, reduction='mean')

        # Dice loss
        inputs_flat = inputs.view(-1)
        targets_flat = targets.view(-1)

        intersection = (inputs_flat * targets_flat).sum()
        dice = 1 - (2. * intersection + smooth) / (inputs_flat.sum() + targets_flat.sum() + smooth)

        return bce + dice


def calculate_iou(pred, target, threshold=0.5):
    """IoU (Intersection over Union) 계산"""
    pred = (pred > threshold).float()
    target = (target > threshold).float()

    intersection = (pred * target).sum()
    union = pred.sum() + target.sum() - intersection

    if union == 0:
        return 1.0

    return (intersection / union).item()


def train_epoch(model, dataloader, criterion, optimizer, device, epoch, total_epochs):
    """한 에포크 학습"""
    model.train()
    total_loss = 0
    total_iou = 0

    pbar = tqdm(dataloader, desc=f"Epoch {epoch}/{total_epochs}")

    for batch_idx, (images, targets) in enumerate(pbar):
        images = images.to(device)
        targets = targets.to(device)

        # Forward pass
        outputs = model(images)
        loss = criterion(outputs, targets)

        # Backward pass
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        # Metrics
        total_loss += loss.item()
        iou = calculate_iou(outputs, targets)
        total_iou += iou

        # Update progress bar
        pbar.set_postfix({
            'loss': f'{loss.item():.4f}',
            'iou': f'{iou:.4f}'
        })

    avg_loss = total_loss / len(dataloader)
    avg_iou = total_iou / len(dataloader)

    return avg_loss, avg_iou


def validate(model, dataloader, criterion, device):
    """검증"""
    model.eval()
    total_loss = 0
    total_iou = 0

    with torch.no_grad():
        for images, targets in dataloader:
            images = images.to(device)
            targets = targets.to(device)

            outputs = model(images)
            loss = criterion(outputs, targets)

            total_loss += loss.item()
            total_iou += calculate_iou(outputs, targets)

    avg_loss = total_loss / len(dataloader)
    avg_iou = total_iou / len(dataloader)

    return avg_loss, avg_iou


def main():
    parser = argparse.ArgumentParser(description='EDGNet 대규모 학습')
    parser.add_argument('--data', type=str, required=True, help='데이터셋 디렉토리')
    parser.add_argument('--epochs', type=int, default=100, help='학습 에포크 수')
    parser.add_argument('--batch-size', type=int, default=8, help='배치 크기')
    parser.add_argument('--lr', type=float, default=0.001, help='학습률')
    parser.add_argument('--image-size', type=int, default=512, help='이미지 크기')
    parser.add_argument('--save-dir', type=str, default='/home/uproot/ax/poc/edgnet-api/models', help='모델 저장 디렉토리')

    args = parser.parse_args()

    print("=" * 60)
    print("🚀 EDGNet 대규모 학습 시작")
    print("=" * 60)
    print(f"데이터셋: {args.data}")
    print(f"에포크: {args.epochs}")
    print(f"배치 크기: {args.batch_size}")
    print(f"학습률: {args.lr}")
    print(f"이미지 크기: {args.image_size}")
    print("=" * 60)

    # Device 설정
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"사용 디바이스: {device}")

    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"CUDA 버전: {torch.version.cuda}")

    # 데이터셋 로드
    print("\n📊 데이터셋 로딩 중...")
    dataset = EDGNetDataset(args.data, image_size=args.image_size)

    # Train/Val 분할 (80/20)
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(dataset, [train_size, val_size])

    print(f"학습 데이터: {len(train_dataset)} 이미지")
    print(f"검증 데이터: {len(val_dataset)} 이미지")

    # DataLoader
    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=4,
        pin_memory=True
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=4,
        pin_memory=True
    )

    # 모델 생성
    print("\n🏗️  모델 생성 중...")
    model = UNet(in_channels=1, out_channels=1).to(device)

    # 모델 파라미터 수 계산
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"총 파라미터: {total_params:,}")
    print(f"학습 가능 파라미터: {trainable_params:,}")

    # Loss, Optimizer
    criterion = DiceBCELoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)

    # 학습 시작
    print("\n🎓 학습 시작...\n")

    best_val_iou = 0.0
    history = {
        'train_loss': [],
        'train_iou': [],
        'val_loss': [],
        'val_iou': []
    }

    start_time = time.time()

    for epoch in range(1, args.epochs + 1):
        # 학습
        train_loss, train_iou = train_epoch(
            model, train_loader, criterion, optimizer, device, epoch, args.epochs
        )

        # 검증
        val_loss, val_iou = validate(model, val_loader, criterion, device)

        # Scheduler step
        scheduler.step(val_loss)

        # 기록
        history['train_loss'].append(train_loss)
        history['train_iou'].append(train_iou)
        history['val_loss'].append(val_loss)
        history['val_iou'].append(val_iou)

        # 로그 출력
        print(f"\nEpoch {epoch}/{args.epochs}:")
        print(f"  Train Loss: {train_loss:.4f}, Train IoU: {train_iou:.4f}")
        print(f"  Val Loss: {val_loss:.4f}, Val IoU: {val_iou:.4f}")

        # 최고 모델 저장
        if val_iou > best_val_iou:
            best_val_iou = val_iou
            save_dir = Path(args.save_dir)
            save_dir.mkdir(parents=True, exist_ok=True)

            model_path = save_dir / 'edgnet_large.pth'
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'train_loss': train_loss,
                'val_loss': val_loss,
                'train_iou': train_iou,
                'val_iou': val_iou,
            }, model_path)

            print(f"  ✅ 최고 모델 저장: {model_path} (IoU: {val_iou:.4f})")

        # 체크포인트 저장 (매 10 에포크)
        if epoch % 10 == 0:
            checkpoint_path = Path(args.save_dir) / f'edgnet_large_epoch_{epoch}.pth'
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'train_loss': train_loss,
                'val_loss': val_loss,
                'train_iou': train_iou,
                'val_iou': val_iou,
            }, checkpoint_path)
            print(f"  💾 체크포인트 저장: {checkpoint_path}")

    # 학습 완료
    elapsed_time = time.time() - start_time
    print("\n" + "=" * 60)
    print("✅ 학습 완료!")
    print("=" * 60)
    print(f"총 소요 시간: {elapsed_time / 3600:.2f} 시간")
    print(f"최고 Validation IoU: {best_val_iou:.4f}")
    print(f"모델 저장 위치: {args.save_dir}")

    # 학습 히스토리 저장
    history_path = Path(args.save_dir) / 'training_history.json'
    with open(history_path, 'w') as f:
        json.dump(history, f, indent=2)
    print(f"학습 히스토리 저장: {history_path}")

    # 모델 파일 크기 확인
    model_path = Path(args.save_dir) / 'edgnet_large.pth'
    if model_path.exists():
        size_mb = model_path.stat().st_size / (1024 * 1024)
        print(f"모델 파일 크기: {size_mb:.2f} MB")

    print("\n🎉 대규모 학습 성공!")


if __name__ == '__main__':
    main()
