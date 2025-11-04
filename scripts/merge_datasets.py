#!/usr/bin/env python3
"""
여러 데이터셋을 병합하여 하나의 통합 데이터셋 생성
"""
import argparse
import shutil
from pathlib import Path
import yaml
from tqdm import tqdm

def merge_datasets(dataset_paths, output_dir, weights=None):
    """
    여러 데이터셋을 병합

    Args:
        dataset_paths: 데이터셋 디렉토리 리스트
        output_dir: 출력 디렉토리
        weights: 각 데이터셋의 샘플링 비율 (None이면 균등)
    """
    output_path = Path(output_dir)

    # 출력 디렉토리 생성
    for split in ['train', 'val', 'test']:
        (output_path / 'images' / split).mkdir(parents=True, exist_ok=True)
        (output_path / 'labels' / split).mkdir(parents=True, exist_ok=True)

    # 데이터셋별 통계
    dataset_stats = {}

    # 클래스 이름 수집 (첫 번째 데이터셋 기준)
    class_names = None
    nc = 0

    print("=" * 70)
    print("🔄 Merging datasets...")
    print("=" * 70)

    for dataset_path in dataset_paths:
        dataset_path = Path(dataset_path)
        dataset_name = dataset_path.name

        print(f"\n📂 Processing: {dataset_name}")

        # data.yaml 로드
        yaml_path = dataset_path / 'data.yaml'
        if not yaml_path.exists():
            print(f"⚠️  No data.yaml found, skipping {dataset_name}")
            continue

        with open(yaml_path, 'r') as f:
            data_config = yaml.safe_load(f)

        # 클래스 이름 저장 (첫 번째만)
        if class_names is None:
            class_names = data_config.get('names', {})
            nc = data_config.get('nc', 14)

        stats = {'train': 0, 'val': 0, 'test': 0}

        # 각 split별로 처리
        for split in ['train', 'val', 'test']:
            src_images = dataset_path / 'images' / split
            src_labels = dataset_path / 'labels' / split

            if not src_images.exists():
                continue

            # 이미지 파일 목록
            image_files = list(src_images.glob('*.jpg')) + \
                         list(src_images.glob('*.jpeg')) + \
                         list(src_images.glob('*.png'))

            print(f"  {split}: {len(image_files)} images")

            for img_file in tqdm(image_files, desc=f"  {split}", leave=False):
                # 새 파일명 (중복 방지)
                new_name = f"{dataset_name}_{img_file.stem}{img_file.suffix}"

                # 이미지 복사
                dst_img = output_path / 'images' / split / new_name
                shutil.copy(img_file, dst_img)

                # 라벨 복사
                label_file = src_labels / f"{img_file.stem}.txt"
                if label_file.exists():
                    dst_label = output_path / 'labels' / split / f"{Path(new_name).stem}.txt"
                    shutil.copy(label_file, dst_label)
                    stats[split] += 1

        dataset_stats[dataset_name] = stats

    # data.yaml 생성
    yaml_path = output_path / 'data.yaml'
    with open(yaml_path, 'w') as f:
        f.write(f"""# Merged Dataset
path: {output_path.absolute()}
train: images/train
val: images/val
test: images/test

# Classes
names:
""")
        for cls_id, cls_name in class_names.items():
            f.write(f"  {cls_id}: {cls_name}\n")

        f.write(f"\nnc: {nc}\n")

    # 통계 출력
    print("\n" + "=" * 70)
    print("✅ Merge complete!")
    print("=" * 70)

    total_train = sum(stats['train'] for stats in dataset_stats.values())
    total_val = sum(stats['val'] for stats in dataset_stats.values())
    total_test = sum(stats['test'] for stats in dataset_stats.values())

    print(f"\n📊 Dataset Statistics:")
    for dataset_name, stats in dataset_stats.items():
        print(f"\n{dataset_name}:")
        print(f"  Train: {stats['train']}")
        print(f"  Val: {stats['val']}")
        print(f"  Test: {stats['test']}")
        print(f"  Total: {sum(stats.values())}")

    print(f"\n📈 Combined Total:")
    print(f"  Train: {total_train}")
    print(f"  Val: {total_val}")
    print(f"  Test: {total_test}")
    print(f"  Total: {total_train + total_val + total_test}")

    print(f"\n📁 Output: {output_path}")
    print(f"📝 Config: {yaml_path}")

def main():
    parser = argparse.ArgumentParser(
        description='Merge multiple YOLO datasets'
    )

    parser.add_argument('--datasets', nargs='+', required=True,
                        help='List of dataset directories to merge')
    parser.add_argument('--output', type=str, default='datasets/merged',
                        help='Output directory')
    parser.add_argument('--weights', nargs='+', type=float,
                        help='Sampling weights for each dataset')

    args = parser.parse_args()

    merge_datasets(
        dataset_paths=args.datasets,
        output_dir=args.output,
        weights=args.weights
    )

if __name__ == '__main__':
    main()
