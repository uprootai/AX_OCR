#!/usr/bin/env python3
"""
eDOCr 결과를 YOLO 데이터셋으로 변환
"""
import os
import json
import shutil
from pathlib import Path
from PIL import Image
import random

def create_dataset_structure(output_dir):
    """데이터셋 디렉토리 생성"""
    dirs = [
        'images/train', 'images/val', 'images/test',
        'labels/train', 'labels/val', 'labels/test'
    ]
    for d in dirs:
        Path(output_dir / d).mkdir(parents=True, exist_ok=True)

def classify_dimension(text):
    """치수 텍스트를 클래스로 분류"""
    text = text.strip()

    # Diameter
    if text.startswith('φ') or text.startswith('Ø'):
        return 0, 'diameter_dim'

    # Radius
    if text.startswith('R'):
        return 2, 'radius_dim'

    # Angular
    if '°' in text:
        return 3, 'angular_dim'

    # Chamfer
    if 'x' in text and '°' in text:
        return 4, 'chamfer_dim'
    if text.startswith('C'):
        return 4, 'chamfer_dim'

    # Tolerance
    if '±' in text or ('+' in text and '-' in text):
        return 5, 'tolerance_dim'

    # Reference (in parentheses)
    if text.startswith('(') and text.endswith(')'):
        return 6, 'reference_dim'

    # Default: linear dimension
    return 1, 'linear_dim'

def classify_gdt_symbol(symbol_type):
    """GD&T 기호 분류"""
    gdt_map = {
        'flatness': 7,
        'cylindricity': 8,
        'position': 9,
        'perpendicularity': 10,
        'parallelism': 11
    }
    return gdt_map.get(symbol_type.lower(), 7)

def edocr_to_yolo_format(bbox, image_width, image_height):
    """eDOCr bbox를 YOLO 포맷으로 변환"""
    x = bbox.get('x', 0)
    y = bbox.get('y', 0)
    w = bbox.get('width', 50)
    h = bbox.get('height', 30)

    # 중심점 계산
    x_center = (x + w / 2) / image_width
    y_center = (y + h / 2) / image_height

    # 크기 정규화
    norm_width = w / image_width
    norm_height = h / image_height

    # 0-1 범위로 클리핑
    x_center = max(0, min(1, x_center))
    y_center = max(0, min(1, y_center))
    norm_width = max(0, min(1, norm_width))
    norm_height = max(0, min(1, norm_height))

    return x_center, y_center, norm_width, norm_height

def convert_annotation(annotation, image_path, output_label_path):
    """
    단일 어노테이션을 YOLO 포맷으로 변환
    """
    # 이미지 크기 가져오기
    with Image.open(image_path) as img:
        img_width, img_height = img.size

    yolo_lines = []

    # Dimensions 변환
    if 'dimensions' in annotation and annotation['dimensions']:
        for dim in annotation['dimensions']:
            if 'bbox' not in dim or 'value' not in dim:
                continue

            bbox = dim['bbox']
            value = dim['value']

            # 클래스 분류
            class_id, class_name = classify_dimension(value)

            # YOLO 포맷 변환
            x_center, y_center, width, height = edocr_to_yolo_format(
                bbox, img_width, img_height
            )

            yolo_lines.append(
                f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}"
            )

    # GD&T 기호 변환
    if 'gdt' in annotation and annotation['gdt']:
        for gdt in annotation['gdt']:
            if 'bbox' not in gdt or 'type' not in gdt:
                continue

            bbox = gdt['bbox']
            symbol_type = gdt['type']

            # 클래스 분류
            class_id = classify_gdt_symbol(symbol_type)

            # YOLO 포맷 변환
            x_center, y_center, width, height = edocr_to_yolo_format(
                bbox, img_width, img_height
            )

            yolo_lines.append(
                f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}"
            )

    # 라벨 파일 저장
    with open(output_label_path, 'w') as f:
        f.write('\n'.join(yolo_lines))

    return len(yolo_lines)

def split_dataset(image_files, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15):
    """데이터셋을 train/val/test로 분할"""
    random.shuffle(image_files)

    total = len(image_files)
    train_end = int(total * train_ratio)
    val_end = train_end + int(total * val_ratio)

    return {
        'train': image_files[:train_end],
        'val': image_files[train_end:val_end],
        'test': image_files[val_end:]
    }

def main():
    """메인 실행 함수"""
    # 설정
    source_images_dir = Path('/home/uproot/ax/poc/edocr2-api/uploads')
    source_annotations_dir = Path('/home/uproot/ax/poc/edocr2-api/results')
    output_dir = Path('/home/uproot/ax/poc/datasets/engineering_drawings')

    print("📁 Creating dataset structure...")
    create_dataset_structure(output_dir)

    # 이미지 파일 수집
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    image_files = []

    for ext in image_extensions:
        image_files.extend(source_images_dir.glob(f'*{ext}'))

    print(f"📊 Found {len(image_files)} images")

    if len(image_files) == 0:
        print("❌ No images found. Please add images to:", source_images_dir)
        print("   Run eDOCr2 API to generate annotations first.")
        return

    # Train/Val/Test 분할
    splits = split_dataset(image_files)

    print(f"✂️  Split: Train={len(splits['train'])}, Val={len(splits['val'])}, Test={len(splits['test'])}")

    # 각 분할별로 처리
    total_annotations = 0

    for split_name, split_files in splits.items():
        print(f"\n🔄 Processing {split_name} split...")

        for img_path in split_files:
            # 어노테이션 파일 찾기
            annotation_path = source_annotations_dir / f"{img_path.stem}_result.json"

            if not annotation_path.exists():
                print(f"⚠️  No annotation for {img_path.name}, skipping")
                continue

            # 이미지 복사
            dst_image = output_dir / 'images' / split_name / img_path.name
            shutil.copy(img_path, dst_image)

            # 어노테이션 로드
            with open(annotation_path, 'r') as f:
                annotation = json.load(f)

            # YOLO 라벨 생성
            dst_label = output_dir / 'labels' / split_name / f"{img_path.stem}.txt"
            count = convert_annotation(annotation, img_path, dst_label)

            total_annotations += count

            if count > 0:
                print(f"✅ {img_path.name}: {count} objects")
            else:
                print(f"⚠️  {img_path.name}: No objects detected")

    print(f"\n🎉 Dataset creation complete!")
    print(f"   Total images: {len(image_files)}")
    print(f"   Total annotations: {total_annotations}")
    print(f"   Output directory: {output_dir}")

    # data.yaml 생성
    yaml_path = output_dir / 'data.yaml'
    with open(yaml_path, 'w') as f:
        f.write(f"""# Engineering Drawings Dataset
path: {output_dir}
train: images/train
val: images/val
test: images/test

# Classes
names:
  0: diameter_dim
  1: linear_dim
  2: radius_dim
  3: angular_dim
  4: chamfer_dim
  5: tolerance_dim
  6: reference_dim
  7: flatness
  8: cylindricity
  9: position
  10: perpendicularity
  11: parallelism
  12: surface_roughness
  13: text_block

nc: 14
""")

    print(f"📝 Created data.yaml at: {yaml_path}")

if __name__ == '__main__':
    main()
