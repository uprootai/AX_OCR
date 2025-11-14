#!/usr/bin/env python3
"""
EDGNet 데이터 증강 스크립트
5개 이미지 → 50+ 증강 이미지 생성
"""

import os
import cv2
import numpy as np
from pathlib import Path
import json
from tqdm import tqdm

# 증강 파라미터
AUGMENTATIONS = {
    'rotation': [-15, -10, -5, 5, 10, 15],  # 회전 각도
    'brightness': [0.7, 0.85, 1.15, 1.3],   # 밝기 조정
    'contrast': [0.7, 0.85, 1.15, 1.3],     # 대비 조정
    'blur': [0, 1, 3],                       # 가우시안 블러
    'noise': [0, 5, 10],                     # 노이즈 추가
}

def rotate_image(image, angle):
    """이미지 회전"""
    height, width = image.shape[:2]
    center = (width // 2, height // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, matrix, (width, height),
                             borderMode=cv2.BORDER_CONSTANT,
                             borderValue=(255, 255, 255))
    return rotated

def adjust_brightness(image, factor):
    """밝기 조정"""
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    hsv = hsv.astype(np.float32)
    hsv[:, :, 2] = hsv[:, :, 2] * factor
    hsv[:, :, 2] = np.clip(hsv[:, :, 2], 0, 255)
    hsv = hsv.astype(np.uint8)
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

def adjust_contrast(image, factor):
    """대비 조정"""
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB).astype(np.float32)
    lab[:, :, 0] = lab[:, :, 0] * factor
    lab[:, :, 0] = np.clip(lab[:, :, 0], 0, 255)
    lab = lab.astype(np.uint8)
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

def add_gaussian_blur(image, kernel_size):
    """가우시안 블러 추가"""
    if kernel_size == 0:
        return image
    kernel = (kernel_size * 2 + 1, kernel_size * 2 + 1)
    return cv2.GaussianBlur(image, kernel, 0)

def add_noise(image, noise_level):
    """노이즈 추가"""
    if noise_level == 0:
        return image
    noise = np.random.normal(0, noise_level, image.shape).astype(np.uint8)
    noisy = cv2.add(image, noise)
    return noisy

def horizontal_flip(image):
    """좌우 반전"""
    return cv2.flip(image, 1)

def vertical_flip(image):
    """상하 반전"""
    return cv2.flip(image, 0)

def augment_image(image, aug_params):
    """단일 증강 적용"""
    augmented = image.copy()

    # 회전
    if 'rotation' in aug_params:
        augmented = rotate_image(augmented, aug_params['rotation'])

    # 밝기
    if 'brightness' in aug_params:
        augmented = adjust_brightness(augmented, aug_params['brightness'])

    # 대비
    if 'contrast' in aug_params:
        augmented = adjust_contrast(augmented, aug_params['contrast'])

    # 블러
    if 'blur' in aug_params:
        augmented = add_gaussian_blur(augmented, aug_params['blur'])

    # 노이즈
    if 'noise' in aug_params:
        augmented = add_noise(augmented, aug_params['noise'])

    # 플립
    if aug_params.get('h_flip', False):
        augmented = horizontal_flip(augmented)

    if aug_params.get('v_flip', False):
        augmented = vertical_flip(augmented)

    return augmented

def generate_augmentation_params():
    """증강 파라미터 조합 생성"""
    params_list = []

    # 1. 회전만
    for angle in AUGMENTATIONS['rotation']:
        params_list.append({'rotation': angle})

    # 2. 밝기만
    for brightness in AUGMENTATIONS['brightness']:
        params_list.append({'brightness': brightness})

    # 3. 대비만
    for contrast in AUGMENTATIONS['contrast']:
        params_list.append({'contrast': contrast})

    # 4. 회전 + 밝기
    for angle in AUGMENTATIONS['rotation'][:3]:  # 3개만
        for brightness in AUGMENTATIONS['brightness'][:2]:  # 2개만
            params_list.append({
                'rotation': angle,
                'brightness': brightness
            })

    # 5. 좌우 반전
    params_list.append({'h_flip': True})

    # 6. 좌우 반전 + 밝기
    for brightness in AUGMENTATIONS['brightness'][:2]:
        params_list.append({
            'h_flip': True,
            'brightness': brightness
        })

    return params_list

def augment_dataset(source_dir, output_dir, target_count=50):
    """데이터셋 증강"""
    source_path = Path(source_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 이미지 파일 찾기
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    image_files = []
    for ext in image_extensions:
        image_files.extend(list(source_path.glob(f'*{ext}')))
        image_files.extend(list(source_path.glob(f'*{ext.upper()}')))

    if not image_files:
        print(f"❌ No images found in {source_dir}")
        return

    print(f"📊 Found {len(image_files)} original images")
    print(f"🎯 Target: {target_count} augmented images per original")

    # 증강 파라미터 생성
    aug_params_list = generate_augmentation_params()
    print(f"🔧 Generated {len(aug_params_list)} augmentation combinations")

    total_generated = 0
    metadata = {'augmentations': [], 'statistics': {}}

    # 각 이미지에 대해 증강 수행
    for img_file in tqdm(image_files, desc="Augmenting images"):
        # 원본 이미지 읽기
        image = cv2.imread(str(img_file))
        if image is None:
            print(f"⚠️  Failed to load {img_file}")
            continue

        # 원본 복사
        output_name = output_path / img_file.name
        cv2.imwrite(str(output_name), image)
        metadata['augmentations'].append({
            'original': img_file.name,
            'augmented': img_file.name,
            'params': 'original'
        })
        total_generated += 1

        # 증강 적용
        for idx, aug_params in enumerate(aug_params_list[:target_count-1]):
            augmented = augment_image(image, aug_params)

            # 파일명 생성
            stem = img_file.stem
            ext = img_file.suffix
            aug_name = f"{stem}_aug_{idx:03d}{ext}"
            aug_path = output_path / aug_name

            # 저장
            cv2.imwrite(str(aug_path), augmented)

            metadata['augmentations'].append({
                'original': img_file.name,
                'augmented': aug_name,
                'params': aug_params
            })
            total_generated += 1

    # 메타데이터 저장
    metadata['statistics'] = {
        'original_count': len(image_files),
        'augmented_count': total_generated,
        'augmentation_factor': total_generated / len(image_files) if image_files else 0
    }

    metadata_path = output_path / 'augmentation_metadata.json'
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Augmentation complete!")
    print(f"   Original images: {len(image_files)}")
    print(f"   Augmented images: {total_generated}")
    print(f"   Augmentation factor: {total_generated / len(image_files):.1f}x")
    print(f"   Output directory: {output_dir}")
    print(f"   Metadata saved: {metadata_path}")

def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description='EDGNet 데이터 증강')
    parser.add_argument('--source', type=str,
                       default='/home/uproot/ax/poc/edgnet_dataset',
                       help='Source dataset directory')
    parser.add_argument('--output', type=str,
                       default='/home/uproot/ax/poc/edgnet_dataset_large',
                       help='Output directory for augmented dataset')
    parser.add_argument('--target', type=int, default=50,
                       help='Target number of images per original (default: 50)')

    args = parser.parse_args()

    print("=" * 60)
    print("🎨 EDGNet 데이터 증강 시작")
    print("=" * 60)
    print(f"Source: {args.source}")
    print(f"Output: {args.output}")
    print(f"Target: {args.target} images per original")
    print("=" * 60)

    augment_dataset(args.source, args.output, args.target)

    print("\n" + "=" * 60)
    print("🎉 데이터 증강 완료!")
    print("=" * 60)

if __name__ == '__main__':
    main()
