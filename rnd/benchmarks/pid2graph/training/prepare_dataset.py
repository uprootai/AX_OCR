#!/usr/bin/env python3
"""
PID2Graph 데이터셋을 YOLO 형식으로 변환하는 스크립트

GraphML -> YOLO txt 형식 변환:
- GraphML: xmin, ymin, xmax, ymax (절대 좌표)
- YOLO: class_id x_center y_center width height (정규화 좌표 0-1)
"""
import os
import sys
import shutil
import random
from pathlib import Path
from PIL import Image
import networkx as nx
from tqdm import tqdm
import yaml


# PID2Graph 클래스 매핑
CLASS_NAMES = [
    "crossing",      # 0 - 파이프 교차점
    "connector",     # 1 - 연결점
    "border_node",   # 2 - 경계 노드
    "general",       # 3 - 일반 장비
    "tank",          # 4 - 탱크
    "valve",         # 5 - 밸브
    "pump",          # 6 - 펌프
    "arrow",         # 7 - 화살표
]

CLASS_TO_ID = {name: idx for idx, name in enumerate(CLASS_NAMES)}


def load_graphml_annotations(graphml_path: Path) -> list:
    """GraphML에서 어노테이션 추출"""
    try:
        G = nx.read_graphml(graphml_path)
    except Exception as e:
        print(f"Error loading {graphml_path}: {e}")
        return []

    annotations = []
    for node_id, attrs in G.nodes(data=True):
        label = attrs.get("label", "unknown")

        # 클래스 ID 매핑
        if label not in CLASS_TO_ID:
            continue  # 알 수 없는 클래스는 건너뛰기

        class_id = CLASS_TO_ID[label]

        # bbox 추출 (xmin, ymin, xmax, ymax)
        xmin = float(attrs.get("xmin", 0))
        ymin = float(attrs.get("ymin", 0))
        xmax = float(attrs.get("xmax", 0))
        ymax = float(attrs.get("ymax", 0))

        if xmax > xmin and ymax > ymin:
            annotations.append({
                "class_id": class_id,
                "xmin": xmin,
                "ymin": ymin,
                "xmax": xmax,
                "ymax": ymax
            })

    return annotations


def convert_to_yolo_format(annotations: list, img_width: int, img_height: int) -> list:
    """YOLO 형식으로 변환 (정규화된 중심 좌표 + 크기)"""
    yolo_annotations = []

    for ann in annotations:
        # 중심 좌표와 크기 계산
        x_center = (ann["xmin"] + ann["xmax"]) / 2 / img_width
        y_center = (ann["ymin"] + ann["ymax"]) / 2 / img_height
        width = (ann["xmax"] - ann["xmin"]) / img_width
        height = (ann["ymax"] - ann["ymin"]) / img_height

        # 범위 확인 (0-1)
        x_center = max(0, min(1, x_center))
        y_center = max(0, min(1, y_center))
        width = max(0, min(1, width))
        height = max(0, min(1, height))

        if width > 0 and height > 0:
            yolo_annotations.append({
                "class_id": ann["class_id"],
                "x_center": x_center,
                "y_center": y_center,
                "width": width,
                "height": height
            })

    return yolo_annotations


def write_yolo_label(annotations: list, output_path: Path):
    """YOLO 라벨 파일 작성"""
    with open(output_path, "w") as f:
        for ann in annotations:
            line = f"{ann['class_id']} {ann['x_center']:.6f} {ann['y_center']:.6f} {ann['width']:.6f} {ann['height']:.6f}\n"
            f.write(line)


def prepare_dataset(
    source_dir: Path,
    output_dir: Path,
    train_ratio: float = 0.8,
    val_ratio: float = 0.15,
    test_ratio: float = 0.05,
    max_images: int = None
):
    """데이터셋 준비 및 분할"""

    # 출력 디렉토리 생성
    for split in ["train", "val", "test"]:
        (output_dir / "images" / split).mkdir(parents=True, exist_ok=True)
        (output_dir / "labels" / split).mkdir(parents=True, exist_ok=True)

    # 이미지-GraphML 쌍 찾기
    pairs = []
    for img_path in source_dir.rglob("*.png"):
        graphml_path = img_path.with_suffix(".graphml")
        if graphml_path.exists():
            pairs.append((img_path, graphml_path))

    print(f"Found {len(pairs)} image-graphml pairs")

    if max_images and len(pairs) > max_images:
        random.shuffle(pairs)
        pairs = pairs[:max_images]
        print(f"Limited to {max_images} images")

    # 데이터 분할
    random.shuffle(pairs)
    n_train = int(len(pairs) * train_ratio)
    n_val = int(len(pairs) * val_ratio)

    splits = {
        "train": pairs[:n_train],
        "val": pairs[n_train:n_train + n_val],
        "test": pairs[n_train + n_val:]
    }

    print(f"Split: train={len(splits['train'])}, val={len(splits['val'])}, test={len(splits['test'])}")

    # 변환 및 복사
    stats = {"total": 0, "skipped": 0, "annotations": 0}

    for split_name, split_pairs in splits.items():
        print(f"\nProcessing {split_name}...")

        for img_path, graphml_path in tqdm(split_pairs):
            try:
                # 이미지 크기 확인
                with Image.open(img_path) as img:
                    img_width, img_height = img.size

                # 어노테이션 로드 및 변환
                annotations = load_graphml_annotations(graphml_path)
                if not annotations:
                    stats["skipped"] += 1
                    continue

                yolo_annotations = convert_to_yolo_format(annotations, img_width, img_height)

                # 파일명 생성 (고유하게)
                relative_path = img_path.relative_to(source_dir)
                safe_name = str(relative_path).replace("/", "_").replace("\\", "_")
                base_name = Path(safe_name).stem

                # 이미지 복사
                dest_img = output_dir / "images" / split_name / f"{base_name}.png"
                shutil.copy2(img_path, dest_img)

                # 라벨 파일 작성
                dest_label = output_dir / "labels" / split_name / f"{base_name}.txt"
                write_yolo_label(yolo_annotations, dest_label)

                stats["total"] += 1
                stats["annotations"] += len(yolo_annotations)

            except Exception as e:
                print(f"Error processing {img_path}: {e}")
                stats["skipped"] += 1

    print(f"\n{'='*60}")
    print(f"Dataset preparation complete!")
    print(f"  Total images: {stats['total']}")
    print(f"  Total annotations: {stats['annotations']}")
    print(f"  Skipped: {stats['skipped']}")
    print(f"{'='*60}")

    return stats


def create_data_yaml(output_dir: Path):
    """YOLO 데이터 설정 파일 생성"""
    data_config = {
        "path": str(output_dir.absolute()),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "names": {i: name for i, name in enumerate(CLASS_NAMES)},
        "nc": len(CLASS_NAMES)
    }

    yaml_path = output_dir / "data.yaml"
    with open(yaml_path, "w") as f:
        yaml.dump(data_config, f, default_flow_style=False, sort_keys=False)

    print(f"Created: {yaml_path}")
    return yaml_path


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Prepare PID2Graph dataset for YOLO training")
    parser.add_argument("--source", type=str, default="../data/PID2Graph",
                        help="Source PID2Graph directory")
    parser.add_argument("--output", type=str, default="dataset",
                        help="Output directory for YOLO dataset")
    parser.add_argument("--max_images", type=int, default=None,
                        help="Maximum number of images to process")
    parser.add_argument("--train_ratio", type=float, default=0.8)
    parser.add_argument("--val_ratio", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)

    args = parser.parse_args()

    random.seed(args.seed)

    source_dir = Path(args.source)
    output_dir = Path(args.output)

    if not source_dir.exists():
        print(f"Error: Source directory not found: {source_dir}")
        sys.exit(1)

    print(f"Source: {source_dir}")
    print(f"Output: {output_dir}")

    # 데이터셋 준비
    prepare_dataset(
        source_dir,
        output_dir,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=1.0 - args.train_ratio - args.val_ratio,
        max_images=args.max_images
    )

    # data.yaml 생성
    create_data_yaml(output_dir)

    print("\nDataset ready for training!")
    print(f"  Data config: {output_dir}/data.yaml")


if __name__ == "__main__":
    main()
