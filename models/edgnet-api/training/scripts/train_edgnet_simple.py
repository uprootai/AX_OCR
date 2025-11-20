#!/usr/bin/env python3
"""
EDGNet 간단 GPU 학습 스크립트

증강된 데이터셋으로 GraphSAGE 모델 학습
"""

import sys
import json
import time
import logging
from pathlib import Path
from typing import List, Dict
import numpy as np

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import Adam
from sklearn.model_selection import train_test_split

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 클래스 매핑
CLASS_NAMES = [
    'diameter_dim', 'linear_dim', 'radius_dim', 'angular_dim',
    'chamfer_dim', 'tolerance_dim', 'reference_dim',
    'flatness', 'cylindricity', 'position', 'perpendicularity',
    'parallelism', 'surface_roughness', 'text_block'
]
CLASS_TO_IDX = {name: idx for idx, name in enumerate(CLASS_NAMES)}


class SimpleGraphNet(nn.Module):
    """간단한 그래프 신경망"""

    def __init__(self, num_features: int, num_classes: int, hidden_dim: int = 64):
        super().__init__()

        # 노드 특징 임베딩
        self.fc1 = nn.Linear(num_features, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, num_classes)

        self.dropout = nn.Dropout(0.3)

    def forward(self, x):
        """
        x: (num_nodes, num_features)
        """
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.fc3(x)
        return x


def load_dataset(data_dir: Path):
    """증강된 데이터셋 로드"""

    logger.info(f"Loading dataset from {data_dir}")

    json_files = [f for f in data_dir.glob("*.json") if f.name != "metadata.json"]

    all_features = []
    all_labels = []

    for json_file in json_files:
        with open(json_file, 'r') as f:
            data = json.load(f)

        nodes = data.get('graph_nodes', [])

        for node in nodes:
            # 특징 추출: bbox (x, y, width, height) + 정규화
            bbox = node.get('bbox', {})
            x = bbox.get('x', 0)
            y = bbox.get('y', 0)
            w = bbox.get('width', 1)
            h = bbox.get('height', 1)

            # 간단한 특징: [x, y, w, h, area, aspect_ratio]
            area = w * h
            aspect = w / max(h, 1)

            features = [x / 2000.0, y / 2000.0, w / 500.0, h / 500.0, area / 100000.0, aspect]

            # 레이블
            class_name = node.get('class_name', 'text_block')
            label = CLASS_TO_IDX.get(class_name, CLASS_TO_IDX['text_block'])

            all_features.append(features)
            all_labels.append(label)

    logger.info(f"Loaded {len(all_features)} nodes")

    return np.array(all_features, dtype=np.float32), np.array(all_labels, dtype=np.int64)


def train_model(data_dir: Path, output_dir: Path, device: str = 'cuda', epochs: int = 100):
    """모델 학습"""

    logger.info("=" * 70)
    logger.info("EDGNet 간단 학습")
    logger.info("=" * 70)

    # GPU 확인
    if device == 'cuda' and not torch.cuda.is_available():
        logger.warning("CUDA not available, using CPU")
        device = 'cpu'

    if device == 'cuda':
        logger.info(f"🔥 GPU: {torch.cuda.get_device_name(0)}")
        logger.info(f"   VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

    device = torch.device(device)

    # 데이터 로드
    X, y = load_dataset(data_dir)

    # Train/val split
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    logger.info(f"Train: {len(X_train)}, Val: {len(X_val)}")

    # 텐서 변환
    X_train_t = torch.from_numpy(X_train).to(device)
    y_train_t = torch.from_numpy(y_train).to(device)
    X_val_t = torch.from_numpy(X_val).to(device)
    y_val_t = torch.from_numpy(y_val).to(device)

    # 모델
    num_features = X.shape[1]
    num_classes = len(CLASS_NAMES)

    model = SimpleGraphNet(num_features, num_classes, hidden_dim=64).to(device)

    num_params = sum(p.numel() for p in model.parameters())
    logger.info(f"Model parameters: {num_params:,}")

    # 옵티마이저
    optimizer = Adam(model.parameters(), lr=0.01)
    criterion = nn.CrossEntropyLoss()

    # 학습
    logger.info("🚀 Training started...")
    start_time = time.time()

    best_val_acc = 0.0
    best_model_state = None

    for epoch in range(epochs):
        # Train
        model.train()
        optimizer.zero_grad()

        out = model(X_train_t)
        loss = criterion(out, y_train_t)
        loss.backward()
        optimizer.step()

        train_acc = (out.argmax(dim=1) == y_train_t).float().mean().item()

        # Validation
        model.eval()
        with torch.no_grad():
            val_out = model(X_val_t)
            val_loss = criterion(val_out, y_val_t)
            val_acc = (val_out.argmax(dim=1) == y_val_t).float().mean().item()

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_model_state = model.state_dict().copy()

        if epoch % 10 == 0 or epoch == epochs - 1:
            logger.info(
                f"Epoch {epoch:3d}/{epochs} | "
                f"Loss: {loss.item():.4f}, Acc: {train_acc:.4f} | "
                f"Val Loss: {val_loss.item():.4f}, Val Acc: {val_acc:.4f}"
            )

    total_time = time.time() - start_time
    logger.info(f"✅ Training completed in {total_time:.1f} seconds")
    logger.info(f"   Best Val Accuracy: {best_val_acc:.4f}")

    # 모델 저장
    output_dir.mkdir(parents=True, exist_ok=True)
    model_path = output_dir / "edgnet_simple.pth"

    torch.save({
        'model_state_dict': best_model_state,
        'num_features': num_features,
        'num_classes': num_classes,
        'hidden_dim': 64,
        'class_names': CLASS_NAMES,
        'best_val_acc': best_val_acc
    }, model_path)

    logger.info(f"💾 Model saved to {model_path}")

    # 메타데이터
    metadata = {
        'model': 'SimpleGraphNet',
        'num_features': num_features,
        'num_classes': num_classes,
        'num_parameters': num_params,
        'epochs': epochs,
        'best_val_acc': float(best_val_acc),
        'training_time_seconds': total_time,
        'device': str(device),
        'training_samples': len(X_train),
        'validation_samples': len(X_val)
    }

    metadata_path = output_dir / "training_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"📄 Metadata saved to {metadata_path}")
    logger.info("=" * 70)

    return model, metadata


def main():
    """메인 함수"""

    # 경로
    data_dir = Path("/home/uproot/ax/poc/edgnet_dataset_augmented")
    output_dir = Path("/home/uproot/ax/poc/edgnet-api/models")

    # 데이터 확인
    if not data_dir.exists():
        logger.error(f"❌ Dataset not found: {data_dir}")
        logger.error("   Please run: python3 scripts/augment_edgnet_simple.py")
        return 1

    # 학습
    try:
        model, metadata = train_model(
            data_dir=data_dir,
            output_dir=output_dir,
            device='cuda',
            epochs=100
        )

        logger.info("")
        logger.info("🎉 EDGNet training successful!")
        logger.info(f"📈 Validation Accuracy: {metadata['best_val_acc']:.2%}")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Test the model")
        logger.info("2. Update EDGNet API to use new model")
        logger.info("3. Restart edgnet-api service")

        return 0

    except Exception as e:
        logger.error(f"❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
