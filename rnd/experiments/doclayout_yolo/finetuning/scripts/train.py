#!/usr/bin/env python3
"""
DocLayout-YOLO Fine-tuning Script

도면 전용 레이아웃 분석 모델 학습

Usage:
    # Stage 1: Head만 학습
    python train.py --stage 1

    # Stage 2: 전체 Fine-tuning
    python train.py --stage 2

    # Stage 1 이어서 Stage 2 학습
    python train.py --stage 2 --resume runs/doclayout/drawing_finetuning_v1/weights/last.pt
"""

import argparse
import os
import sys
from pathlib import Path

import yaml

# 프로젝트 루트 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def load_config(config_path: str) -> dict:
    """YAML 설정 파일 로드"""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def train_stage1(config: dict, data_yaml: str):
    """Stage 1: Head만 학습 (클래스 매핑)"""
    from doclayout_yolo import YOLOv10

    print("=" * 70)
    print("Stage 1: Head만 학습 (클래스 매핑)")
    print("=" * 70)

    stage_config = config["stages"]["stage1"]

    # 베이스 모델 로드
    print(f"\n[1] 베이스 모델 로드: {config['model']['base']}")
    model = YOLOv10.from_pretrained(config["model"]["base"])

    # 학습
    print(f"\n[2] 학습 시작 (epochs={stage_config['epochs']}, freeze={stage_config['freeze']})")

    results = model.train(
        data=data_yaml,
        epochs=stage_config["epochs"],
        batch=stage_config["batch_size"],
        imgsz=config["training"]["imgsz"],
        device=config["training"]["device"],
        project=config["training"]["project"],
        name=f"{config['training']['name']}_stage1",
        exist_ok=config["training"]["exist_ok"],

        # 전이 학습
        freeze=stage_config["freeze"],
        lr0=stage_config["lr0"],

        # 최적화
        optimizer=config["training"]["optimizer"],
        weight_decay=config["training"]["weight_decay"],
        warmup_epochs=config["training"]["warmup_epochs"],

        # 증강
        augment=config["augmentation"]["augment"],
        degrees=config["augmentation"]["degrees"],
        scale=config["augmentation"]["scale"],
        mosaic=config["augmentation"]["mosaic"],
        flipud=config["augmentation"]["flipud"],
        fliplr=config["augmentation"]["fliplr"],

        # AMP
        amp=config["memory"]["amp"],

        # 기타
        patience=config["training"]["patience"],
        workers=config["training"]["workers"],
        pretrained=config["training"]["pretrained"],
        plots=config["validation"]["plots"],
        save=config["validation"]["save"],
    )

    print("\n[3] Stage 1 완료!")
    print(f"    Best mAP50: {results.results_dict.get('metrics/mAP50(B)', 'N/A')}")
    print(f"    Weights: {config['training']['project']}/{config['training']['name']}_stage1/weights/best.pt")

    return results


def train_stage2(config: dict, data_yaml: str, resume_weights: str = None):
    """Stage 2: 전체 Fine-tuning"""
    from doclayout_yolo import YOLOv10

    print("=" * 70)
    print("Stage 2: 전체 Fine-tuning (도면 특화)")
    print("=" * 70)

    stage_config = config["stages"]["stage2"]

    # 모델 로드
    if resume_weights:
        print(f"\n[1] Stage 1 가중치 로드: {resume_weights}")
        model = YOLOv10(resume_weights)
    else:
        # Stage 1 결과에서 자동 로드
        stage1_best = Path(config["training"]["project"]) / f"{config['training']['name']}_stage1" / "weights" / "best.pt"
        if stage1_best.exists():
            print(f"\n[1] Stage 1 가중치 로드: {stage1_best}")
            model = YOLOv10(str(stage1_best))
        else:
            print(f"\n[1] 베이스 모델 로드 (Stage 1 결과 없음): {config['model']['base']}")
            model = YOLOv10.from_pretrained(config["model"]["base"])

    # 학습
    print(f"\n[2] 학습 시작 (epochs={stage_config['epochs']}, freeze={stage_config['freeze']})")

    results = model.train(
        data=data_yaml,
        epochs=stage_config["epochs"],
        batch=stage_config["batch_size"],
        imgsz=config["training"]["imgsz"],
        device=config["training"]["device"],
        project=config["training"]["project"],
        name=f"{config['training']['name']}_stage2",
        exist_ok=config["training"]["exist_ok"],

        # 전체 학습
        freeze=stage_config["freeze"],
        lr0=stage_config["lr0"],

        # 최적화
        optimizer=config["training"]["optimizer"],
        weight_decay=config["training"]["weight_decay"],
        warmup_epochs=config["training"]["warmup_epochs"],

        # 증강
        augment=config["augmentation"]["augment"],
        degrees=config["augmentation"]["degrees"],
        scale=config["augmentation"]["scale"],
        mosaic=config["augmentation"]["mosaic"],
        flipud=config["augmentation"]["flipud"],
        fliplr=config["augmentation"]["fliplr"],

        # AMP
        amp=config["memory"]["amp"],

        # 기타
        patience=config["training"]["patience"],
        workers=config["training"]["workers"],
        pretrained=config["training"]["pretrained"],
        plots=config["validation"]["plots"],
        save=config["validation"]["save"],
    )

    print("\n[3] Stage 2 완료!")
    print(f"    Best mAP50: {results.results_dict.get('metrics/mAP50(B)', 'N/A')}")
    print(f"    Weights: {config['training']['project']}/{config['training']['name']}_stage2/weights/best.pt")

    return results


def collect_existing_images():
    """기존 프로젝트 이미지 수집"""
    base_path = Path(__file__).parent.parent.parent.parent.parent  # /home/uproot/ax/poc

    image_sources = [
        base_path / "web-ui/public/samples",
        base_path / "samples",
        base_path / "blueprint-ai-bom/test_drawings",
        base_path / "apply-company/techloss/test_output",
    ]

    images = []
    for source in image_sources:
        if source.exists():
            for ext in ["*.jpg", "*.png", "*.jpeg"]:
                for img in source.glob(ext):
                    # 결과 이미지 제외
                    if "_result" not in img.name and "_regions" not in img.name:
                        # 심볼/row 이미지 제외
                        if "symbol" not in str(img) and "row_" not in img.name:
                            images.append(img)

    return images


def main():
    parser = argparse.ArgumentParser(description="DocLayout-YOLO Fine-tuning")
    parser.add_argument("--stage", type=int, choices=[1, 2], default=1, help="학습 스테이지 (1: Head만, 2: 전체)")
    parser.add_argument("--resume", type=str, default=None, help="이어서 학습할 가중치 경로")
    parser.add_argument("--config", type=str, default="configs/train_config.yaml", help="학습 설정 파일")
    parser.add_argument("--data", type=str, default="configs/data.yaml", help="데이터 설정 파일")
    parser.add_argument("--collect-images", action="store_true", help="기존 이미지 수집 및 목록 출력")
    args = parser.parse_args()

    # 이미지 수집 모드
    if args.collect_images:
        images = collect_existing_images()
        print(f"\n수집된 이미지: {len(images)}개\n")
        for img in images:
            print(f"  {img}")
        return

    # 설정 파일 경로
    config_dir = Path(__file__).parent.parent / "configs"
    config_path = config_dir / "train_config.yaml"
    data_path = config_dir / "data.yaml"

    if not config_path.exists():
        print(f"[ERROR] 설정 파일 없음: {config_path}")
        return

    if not data_path.exists():
        print(f"[ERROR] 데이터 설정 파일 없음: {data_path}")
        return

    # 설정 로드
    config = load_config(str(config_path))

    # 학습 실행
    if args.stage == 1:
        train_stage1(config, str(data_path))
    else:
        train_stage2(config, str(data_path), args.resume)


if __name__ == "__main__":
    main()
