#!/usr/bin/env python3
"""
PID2Graph YOLO Fine-tuning 스크립트

사용법:
    # 기본 학습
    python train.py

    # 사전 학습 모델에서 시작
    python train.py --pretrained pid_class_agnostic

    # 에폭 수 조정
    python train.py --epochs 100 --batch 16
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# Ultralytics YOLO import
try:
    from ultralytics import YOLO
except ImportError:
    print("Error: ultralytics not installed")
    print("Install with: pip install ultralytics")
    sys.exit(1)


# 기본 설정
DEFAULT_CONFIG = {
    "epochs": 100,
    "batch": 8,
    "imgsz": 1024,
    "device": "0",  # GPU 0 사용, CPU는 "cpu"
    "workers": 4,
    "patience": 20,  # Early stopping
    "save_period": 10,  # 체크포인트 저장 주기
    "amp": True,  # Mixed precision
}

# 사전 학습 모델 경로 (AX POC)
PRETRAINED_MODELS = {
    "pid_class_agnostic": "/home/uproot/ax/poc/models/yolo-api/weights/pid_class_agnostic.pt",
    "yolov11n": "yolo11n.pt",
    "yolov11s": "yolo11s.pt",
    "yolov11m": "yolo11m.pt",
    "yolov11l": "yolo11l.pt",
}


def train(
    data_yaml: str,
    pretrained: str = "yolov11n",
    epochs: int = DEFAULT_CONFIG["epochs"],
    batch: int = DEFAULT_CONFIG["batch"],
    imgsz: int = DEFAULT_CONFIG["imgsz"],
    device: str = DEFAULT_CONFIG["device"],
    project: str = "runs/pid2graph",
    name: str = None,
    resume: bool = False,
    **kwargs
):
    """YOLO 모델 학습"""

    # 모델 경로 결정
    if pretrained in PRETRAINED_MODELS:
        model_path = PRETRAINED_MODELS[pretrained]
    else:
        model_path = pretrained

    print("=" * 60)
    print("PID2Graph YOLO Fine-tuning")
    print("=" * 60)
    print(f"Data config: {data_yaml}")
    print(f"Pretrained model: {pretrained} ({model_path})")
    print(f"Epochs: {epochs}")
    print(f"Batch size: {batch}")
    print(f"Image size: {imgsz}")
    print(f"Device: {device}")
    print("=" * 60)

    # 실험 이름 생성
    if name is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"finetune_{pretrained}_{timestamp}"

    # 모델 로드
    if resume:
        print(f"Resuming from: {model_path}")
        model = YOLO(model_path)
    else:
        print(f"Loading pretrained model: {model_path}")
        model = YOLO(model_path)

    # 학습 시작
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        batch=batch,
        imgsz=imgsz,
        device=device,
        project=project,
        name=name,
        patience=DEFAULT_CONFIG["patience"],
        save_period=DEFAULT_CONFIG["save_period"],
        amp=DEFAULT_CONFIG["amp"],
        workers=DEFAULT_CONFIG["workers"],
        exist_ok=True,
        **kwargs
    )

    print("\n" + "=" * 60)
    print("Training Complete!")
    print("=" * 60)
    print(f"Results saved to: {project}/{name}")
    print(f"Best model: {project}/{name}/weights/best.pt")

    return results


def validate(model_path: str, data_yaml: str, device: str = "0"):
    """학습된 모델 검증"""
    print(f"Validating model: {model_path}")

    model = YOLO(model_path)
    results = model.val(data=data_yaml, device=device)

    print("\nValidation Results:")
    print(f"  mAP50: {results.box.map50:.4f}")
    print(f"  mAP50-95: {results.box.map:.4f}")

    return results


def export_model(model_path: str, format: str = "onnx"):
    """모델 내보내기"""
    print(f"Exporting model: {model_path} -> {format}")

    model = YOLO(model_path)
    model.export(format=format)

    print(f"Export complete!")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="PID2Graph YOLO Fine-tuning")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Train command
    train_parser = subparsers.add_parser("train", help="Train model")
    train_parser.add_argument("--data", type=str, default="dataset/data.yaml",
                              help="Path to data.yaml")
    train_parser.add_argument("--pretrained", type=str, default="yolov11n",
                              choices=list(PRETRAINED_MODELS.keys()) + ["custom"],
                              help="Pretrained model")
    train_parser.add_argument("--model", type=str, help="Custom model path (with --pretrained custom)")
    train_parser.add_argument("--epochs", type=int, default=100)
    train_parser.add_argument("--batch", type=int, default=8)
    train_parser.add_argument("--imgsz", type=int, default=1024)
    train_parser.add_argument("--device", type=str, default="0")
    train_parser.add_argument("--name", type=str, help="Experiment name")
    train_parser.add_argument("--resume", action="store_true", help="Resume training")

    # Validate command
    val_parser = subparsers.add_parser("val", help="Validate model")
    val_parser.add_argument("--model", type=str, required=True, help="Model path")
    val_parser.add_argument("--data", type=str, default="dataset/data.yaml")
    val_parser.add_argument("--device", type=str, default="0")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export model")
    export_parser.add_argument("--model", type=str, required=True, help="Model path")
    export_parser.add_argument("--format", type=str, default="onnx",
                               choices=["onnx", "torchscript", "openvino"])

    args = parser.parse_args()

    if args.command == "train":
        model_path = args.model if args.pretrained == "custom" else args.pretrained
        train(
            data_yaml=args.data,
            pretrained=model_path,
            epochs=args.epochs,
            batch=args.batch,
            imgsz=args.imgsz,
            device=args.device,
            name=args.name,
            resume=args.resume
        )
    elif args.command == "val":
        validate(args.model, args.data, args.device)
    elif args.command == "export":
        export_model(args.model, args.format)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
