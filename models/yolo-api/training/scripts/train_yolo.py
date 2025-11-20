#!/usr/bin/env python3
"""
YOLOv11 모델 학습 스크립트
"""
import argparse
from pathlib import Path
from ultralytics import YOLO
import torch

def train_model(
    model_size='n',
    data_yaml='datasets/engineering_drawings/data.yaml',
    epochs=100,
    imgsz=1280,
    batch=16,
    device='0',
    project='runs/train',
    name='engineering_drawings',
    resume=False,
    pretrained=True
):
    """
    YOLOv11 모델 학습
    """

    print("=" * 70)
    print("🚀 YOLOv11 Training Configuration")
    print("=" * 70)
    print(f"Model Size: yolo11{model_size}")
    print(f"Dataset: {data_yaml}")
    print(f"Epochs: {epochs}")
    print(f"Image Size: {imgsz}")
    print(f"Batch Size: {batch}")
    print(f"Device: {device}")
    print(f"Pretrained: {pretrained}")
    print("=" * 70)

    # GPU 확인
    if device != 'cpu':
        if not torch.cuda.is_available():
            print("⚠️  CUDA not available, using CPU")
            device = 'cpu'
        else:
            gpu_name = torch.cuda.get_device_name(0)
            print(f"✅ Using GPU: {gpu_name}")

    # 모델 로드
    if resume:
        print("📂 Resuming from last checkpoint...")
        model_path = Path(project) / name / 'weights' / 'last.pt'
        if not model_path.exists():
            print(f"❌ Checkpoint not found: {model_path}")
            return
        model = YOLO(str(model_path))
    else:
        if pretrained:
            model_name = f'yolo11{model_size}.pt'
            print(f"📥 Loading pretrained model: {model_name}")
        else:
            model_name = f'yolo11{model_size}.yaml'
            print(f"🔨 Training from scratch: {model_name}")

        model = YOLO(model_name)

    # 학습 시작
    print("\n🎯 Starting training...")
    print("=" * 70)

    results = model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=device,
        project=project,
        name=name,

        # Optimization
        optimizer='AdamW',
        lr0=0.001,           # 초기 학습률
        lrf=0.01,            # 최종 학습률 (lr0 * lrf)
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3.0,
        warmup_momentum=0.8,
        warmup_bias_lr=0.1,

        # Augmentation
        hsv_h=0.015,         # 색조 증강
        hsv_s=0.7,           # 채도 증강
        hsv_v=0.4,           # 명도 증강
        degrees=10.0,        # 회전 (±10도)
        translate=0.1,       # 이동
        scale=0.5,           # 스케일
        shear=0.0,           # 전단
        perspective=0.0,     # 원근
        flipud=0.0,          # 상하 반전 (도면은 방향 중요)
        fliplr=0.5,          # 좌우 반전
        mosaic=1.0,          # 모자이크 증강
        mixup=0.0,           # MixUp 증강
        copy_paste=0.0,      # Copy-Paste 증강

        # Settings
        save=True,
        save_period=10,      # 10 에폭마다 체크포인트 저장
        plots=True,
        verbose=True,
        patience=50,         # Early stopping

        # Validation
        val=True,
    )

    print("\n" + "=" * 70)
    print("✅ Training complete!")
    print("=" * 70)
    print(f"📊 Results saved to: {results.save_dir}")
    print(f"🏆 Best model: {results.save_dir / 'weights' / 'best.pt'}")

    # 메트릭 출력
    if hasattr(results, 'results_dict'):
        print(f"📈 Metrics:")
        metrics_dict = results.results_dict
        if 'metrics/mAP50(B)' in metrics_dict:
            print(f"   - mAP50: {metrics_dict['metrics/mAP50(B)']:.4f}")
        if 'metrics/mAP50-95(B)' in metrics_dict:
            print(f"   - mAP50-95: {metrics_dict['metrics/mAP50-95(B)']:.4f}")

    return results

def main():
    parser = argparse.ArgumentParser(description='Train YOLOv11 on engineering drawings')

    parser.add_argument('--model-size', type=str, default='n',
                        choices=['n', 's', 'm', 'l', 'x'],
                        help='Model size (n=nano, s=small, m=medium, l=large, x=xlarge)')
    parser.add_argument('--data', type=str,
                        default='datasets/engineering_drawings/data.yaml',
                        help='Path to data.yaml')
    parser.add_argument('--epochs', type=int, default=100,
                        help='Number of epochs')
    parser.add_argument('--imgsz', type=int, default=1280,
                        help='Image size (high resolution for drawings)')
    parser.add_argument('--batch', type=int, default=16,
                        help='Batch size')
    parser.add_argument('--device', type=str, default='0',
                        help='CUDA device (0, 1, 2, ...) or cpu')
    parser.add_argument('--project', type=str, default='runs/train',
                        help='Project directory')
    parser.add_argument('--name', type=str, default='engineering_drawings',
                        help='Experiment name')
    parser.add_argument('--resume', action='store_true',
                        help='Resume training from last checkpoint')
    parser.add_argument('--no-pretrained', action='store_true',
                        help='Train from scratch (no pretrained weights)')

    args = parser.parse_args()

    train_model(
        model_size=args.model_size,
        data_yaml=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        project=args.project,
        name=args.name,
        resume=args.resume,
        pretrained=not args.no_pretrained
    )

if __name__ == '__main__':
    main()
