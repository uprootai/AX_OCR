#!/usr/bin/env python3
"""
랜덤 배치 합성 데이터 생성기

빈 배경에 치수, GD&T 기호 등을 랜덤하게 배치하여
무한한 학습 데이터 생성
"""
import os
import random
import argparse
from pathlib import Path
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
from tqdm import tqdm
import json

# =====================
# 클래스 정의
# =====================

CLASS_NAMES = {
    0: 'diameter_dim',
    1: 'linear_dim',
    2: 'radius_dim',
    3: 'angular_dim',
    4: 'chamfer_dim',
    5: 'tolerance_dim',
    6: 'reference_dim',
    7: 'flatness',
    8: 'cylindricity',
    9: 'position',
    10: 'perpendicularity',
    11: 'parallelism',
    12: 'surface_roughness',
    13: 'text_block'
}

CLASS_IDS = {v: k for k, v in CLASS_NAMES.items()}

# =====================
# 요소 템플릿
# =====================

def generate_dimension_text(dim_type):
    """치수 텍스트 생성"""
    if dim_type == 'diameter_dim':
        value = random.randint(5, 500)
        symbol = random.choice(['φ', 'Ø', '⌀'])
        return f"{symbol}{value}"

    elif dim_type == 'linear_dim':
        value = random.randint(1, 1000)
        unit = random.choice(['', 'mm', ' mm'])
        return f"{value}{unit}"

    elif dim_type == 'radius_dim':
        value = random.randint(1, 250)
        prefix = random.choice(['R', 'r'])
        return f"{prefix}{value}"

    elif dim_type == 'angular_dim':
        value = random.choice([30, 45, 60, 90, 120, 135, 180])
        return f"{value}°"

    elif dim_type == 'chamfer_dim':
        value = random.uniform(0.5, 10)
        return random.choice([f"{value:.1f}x45°", f"C{value:.1f}"])

    elif dim_type == 'tolerance_dim':
        value = random.randint(10, 500)
        tol = random.uniform(0.01, 2.0)
        templates = [
            f"±{tol:.2f}",
            f"{value}±{tol:.1f}",
            f"+{tol:.2f}/-{tol*0.5:.2f}",
        ]
        return random.choice(templates)

    elif dim_type == 'reference_dim':
        value = random.randint(10, 500)
        return f"({value})"

    elif dim_type == 'flatness':
        value = random.uniform(0.01, 0.5)
        symbol = random.choice(['⌹', '⏥', '□'])
        return f"{symbol}{value:.2f}"

    elif dim_type == 'cylindricity':
        value = random.uniform(0.01, 0.3)
        symbol = random.choice(['○', '◯'])
        return f"{symbol}{value:.2f}"

    elif dim_type == 'position':
        value = random.uniform(0.01, 0.5)
        symbol = random.choice(['⌖', '⊕'])
        datum = random.choice(['A', 'B', 'C'])
        return f"{symbol}{value:.2f}|{datum}"

    elif dim_type == 'perpendicularity':
        value = random.uniform(0.01, 0.3)
        symbol = random.choice(['⊥', '┴'])
        datum = random.choice(['A', 'B', 'C'])
        return f"{symbol}{value:.2f}|{datum}"

    elif dim_type == 'parallelism':
        value = random.uniform(0.01, 0.3)
        symbol = random.choice(['∥', '‖'])
        datum = random.choice(['A', 'B', 'C'])
        return f"{symbol}{value:.2f}|{datum}"

    elif dim_type == 'surface_roughness':
        value = random.choice([0.4, 0.8, 1.6, 3.2, 6.3, 12.5, 25])
        prefix = random.choice(['Ra', 'Rz', 'Rmax'])
        return f"{prefix}{value}"

    elif dim_type == 'text_block':
        texts = ['SECTION A-A', 'DETAIL B', 'NOTE:', 'MATERIAL: STS304',
                 'SCALE 1:2', 'DRAWING NO.', 'REV. A']
        return random.choice(texts)

    return "ERROR"

# =====================
# 이미지 생성 함수
# =====================

def get_font_path():
    """사용 가능한 폰트 찾기"""
    # Linux 시스템 폰트
    font_paths = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf',
    ]

    for font_path in font_paths:
        if os.path.exists(font_path):
            return font_path

    # Fallback
    return None

def draw_text_on_canvas(canvas, text, x, y, font_size, angle, color=(0, 0, 0)):
    """
    캔버스에 텍스트 그리기 (회전 지원)

    Returns:
        bbox: (x_min, y_min, x_max, y_max)
    """
    # PIL로 변환
    pil_image = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_image)

    # 폰트 로드
    font_path = get_font_path()
    if font_path:
        try:
            font = ImageFont.truetype(font_path, int(font_size))
        except:
            font = ImageFont.load_default()
    else:
        font = ImageFont.load_default()

    # 텍스트 크기 계산
    bbox_raw = draw.textbbox((0, 0), text, font=font)
    text_width = bbox_raw[2] - bbox_raw[0]
    text_height = bbox_raw[3] - bbox_raw[1]

    # 회전된 텍스트 이미지 생성
    text_img = Image.new('RGB', (int(text_width * 1.5), int(text_height * 1.5)), (255, 255, 255))
    text_draw = ImageDraw.Draw(text_img)
    text_draw.text((text_width * 0.25, text_height * 0.25), text, fill=color, font=font)

    # 회전
    rotated = text_img.rotate(angle, expand=True, fillcolor=(255, 255, 255))

    # 붙여넣기 위치 계산
    paste_x = int(x - rotated.width / 2)
    paste_y = int(y - rotated.height / 2)

    # 캔버스 경계 확인
    if paste_x < 0:
        paste_x = 0
    if paste_y < 0:
        paste_y = 0
    if paste_x + rotated.width > pil_image.width:
        paste_x = pil_image.width - rotated.width
    if paste_y + rotated.height > pil_image.height:
        paste_y = pil_image.height - rotated.height

    # 붙여넣기
    pil_image.paste(rotated, (paste_x, paste_y), mask=None)

    # OpenCV로 변환
    canvas[:] = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    # Bounding box 반환
    bbox = (paste_x, paste_y, paste_x + rotated.width, paste_y + rotated.height)
    return bbox

def generate_synthetic_image(
    width=1920,
    height=1080,
    num_elements_range=(10, 30),
    font_size_range=(20, 60)
):
    """
    합성 이미지 생성

    Returns:
        image: numpy array (BGR)
        annotations: list of dicts
    """
    # 빈 캔버스 (흰색)
    canvas = np.ones((height, width, 3), dtype=np.uint8) * 255

    # 가끔 회색 배경
    if random.random() < 0.1:
        bg_color = random.randint(240, 255)
        canvas[:] = bg_color

    # 랜덤 요소 개수
    num_elements = random.randint(*num_elements_range)

    annotations = []

    # 클래스별 비율 (치수가 더 많이)
    class_weights = {
        'diameter_dim': 3,
        'linear_dim': 4,
        'radius_dim': 2,
        'angular_dim': 1,
        'chamfer_dim': 1,
        'tolerance_dim': 2,
        'reference_dim': 1,
        'flatness': 1,
        'cylindricity': 1,
        'position': 1,
        'perpendicularity': 1,
        'parallelism': 1,
        'surface_roughness': 1,
        'text_block': 1,
    }

    class_list = []
    for cls, weight in class_weights.items():
        class_list.extend([cls] * weight)

    for i in range(num_elements):
        # 클래스 선택
        element_class = random.choice(class_list)
        class_id = CLASS_IDS[element_class]

        # 텍스트 생성
        text = generate_dimension_text(element_class)

        # 랜덤 위치 (마진 50px)
        margin = 50
        x = random.randint(margin, width - margin)
        y = random.randint(margin, height - margin)

        # 랜덤 크기
        font_size = random.uniform(*font_size_range)

        # 랜덤 회전 (주로 수평/수직)
        if random.random() < 0.7:
            # 수평/수직 (±5도 오차)
            base_angle = random.choice([0, 90, 180, 270])
            angle = base_angle + random.uniform(-5, 5)
        else:
            # 자유 각도
            angle = random.uniform(0, 360)

        # 색상 (대부분 검정)
        if random.random() < 0.9:
            color = (0, 0, 0)  # Black
        else:
            color = random.choice([
                (255, 0, 0),   # Blue
                (0, 0, 255),   # Red
            ])

        # 텍스트 그리기
        try:
            bbox = draw_text_on_canvas(canvas, text, x, y, font_size, angle, color)

            # 어노테이션 저장
            annotations.append({
                'class_id': class_id,
                'class_name': element_class,
                'text': text,
                'bbox': bbox,  # (x_min, y_min, x_max, y_max)
                'center': (x, y),
                'font_size': font_size,
                'angle': angle,
            })
        except Exception as e:
            # 드물게 실패 가능 (무시)
            pass

    return canvas, annotations

def bbox_to_yolo_format(bbox, img_width, img_height):
    """
    Bounding box를 YOLO 포맷으로 변환

    Args:
        bbox: (x_min, y_min, x_max, y_max)
        img_width, img_height: 이미지 크기

    Returns:
        (x_center, y_center, width, height) 정규화된 좌표
    """
    x_min, y_min, x_max, y_max = bbox

    # 중심점 계산
    x_center = (x_min + x_max) / 2 / img_width
    y_center = (y_min + y_max) / 2 / img_height

    # 크기 정규화
    width = (x_max - x_min) / img_width
    height = (y_max - y_min) / img_height

    # 0-1 범위로 클리핑
    x_center = np.clip(x_center, 0, 1)
    y_center = np.clip(y_center, 0, 1)
    width = np.clip(width, 0, 1)
    height = np.clip(height, 0, 1)

    return x_center, y_center, width, height

# =====================
# 데이터셋 생성
# =====================

def create_dataset(
    output_dir,
    num_images=1000,
    train_ratio=0.7,
    val_ratio=0.15,
    test_ratio=0.15,
    image_size=(1920, 1080)
):
    """
    합성 데이터셋 생성
    """
    output_path = Path(output_dir)

    # 디렉토리 생성
    for split in ['train', 'val', 'test']:
        (output_path / 'images' / split).mkdir(parents=True, exist_ok=True)
        (output_path / 'labels' / split).mkdir(parents=True, exist_ok=True)

    # 분할 개수 계산
    num_train = int(num_images * train_ratio)
    num_val = int(num_images * val_ratio)
    num_test = num_images - num_train - num_val

    splits = {
        'train': num_train,
        'val': num_val,
        'test': num_test,
    }

    total_annotations = 0

    for split, count in splits.items():
        print(f"\n📊 Generating {split} split ({count} images)...")

        for i in tqdm(range(count), desc=split):
            # 이미지 생성
            image, annotations = generate_synthetic_image(
                width=image_size[0],
                height=image_size[1]
            )

            # 파일명
            img_name = f"synthetic_{split}_{i:06d}.jpg"
            img_path = output_path / 'images' / split / img_name
            label_path = output_path / 'labels' / split / f"synthetic_{split}_{i:06d}.txt"

            # 이미지 저장
            cv2.imwrite(str(img_path), image)

            # 라벨 저장 (YOLO 포맷)
            with open(label_path, 'w') as f:
                for ann in annotations:
                    class_id = ann['class_id']
                    bbox = ann['bbox']

                    # YOLO 포맷 변환
                    x_center, y_center, width, height = bbox_to_yolo_format(
                        bbox, image_size[0], image_size[1]
                    )

                    f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")

            total_annotations += len(annotations)

    # data.yaml 생성
    yaml_path = output_path / 'data.yaml'
    with open(yaml_path, 'w') as f:
        f.write(f"""# Synthetic Engineering Drawings Dataset (Random Placement)
path: {output_path.absolute()}
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

    # 통계 저장
    stats = {
        'total_images': num_images,
        'train': num_train,
        'val': num_val,
        'test': num_test,
        'total_annotations': total_annotations,
        'avg_annotations_per_image': total_annotations / num_images,
        'image_size': image_size,
    }

    stats_path = output_path / 'dataset_stats.json'
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)

    print(f"\n🎉 Dataset generation complete!")
    print(f"   Total images: {num_images}")
    print(f"   Total annotations: {total_annotations}")
    print(f"   Avg annotations/image: {total_annotations / num_images:.1f}")
    print(f"   Output directory: {output_path}")
    print(f"   data.yaml: {yaml_path}")

def main():
    parser = argparse.ArgumentParser(
        description='Generate synthetic engineering drawing dataset with random placement'
    )

    parser.add_argument('--output', type=str, default='datasets/synthetic_random',
                        help='Output directory')
    parser.add_argument('--count', type=int, default=1000,
                        help='Total number of images to generate')
    parser.add_argument('--width', type=int, default=1920,
                        help='Image width')
    parser.add_argument('--height', type=int, default=1080,
                        help='Image height')
    parser.add_argument('--train-ratio', type=float, default=0.7,
                        help='Train split ratio')
    parser.add_argument('--val-ratio', type=float, default=0.15,
                        help='Validation split ratio')

    args = parser.parse_args()

    print("=" * 70)
    print("🎨 Synthetic Data Generator (Random Placement)")
    print("=" * 70)
    print(f"Output: {args.output}")
    print(f"Count: {args.count} images")
    print(f"Size: {args.width}x{args.height}")
    print(f"Split: Train={args.train_ratio}, Val={args.val_ratio}, Test={1-args.train_ratio-args.val_ratio}")
    print("=" * 70)

    create_dataset(
        output_dir=args.output,
        num_images=args.count,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=1 - args.train_ratio - args.val_ratio,
        image_size=(args.width, args.height)
    )

if __name__ == '__main__':
    main()
