#!/usr/bin/env python3
"""
데이터 준비 스크립트

기존 프로젝트 이미지를 수집하고 라벨링을 위한 구조로 정리

Usage:
    # 이미지 수집 및 복사
    python prepare_data.py --collect

    # 라벨링 상태 확인
    python prepare_data.py --status

    # train/val 분할
    python prepare_data.py --split --ratio 0.8
"""

import argparse
import os
import shutil
import random
from pathlib import Path
from typing import List, Tuple


# 프로젝트 경로
# 스크립트 위치: rnd/experiments/doclayout_yolo/finetuning/scripts/
PROJECT_ROOT = Path("/home/uproot/ax/poc")  # 고정 경로
DATA_ROOT = Path(__file__).parent.parent / "data"


def find_drawing_images() -> List[Tuple[Path, str]]:
    """도면 이미지 찾기"""

    sources = {
        "mechanical": [
            PROJECT_ROOT / "web-ui/public/samples",
            PROJECT_ROOT / "samples",
        ],
        "pid": [
            PROJECT_ROOT / "apply-company/techloss/test_output",
            PROJECT_ROOT / "web-ui/public/samples",  # P&ID 샘플도 포함
        ],
        "panel": [
            PROJECT_ROOT / "blueprint-ai-bom/test_drawings",
        ],
    }

    images = []
    seen = set()  # 중복 방지

    for category, paths in sources.items():
        for source_path in paths:
            if not source_path.exists():
                print(f"  [SKIP] 경로 없음: {source_path}")
                continue

            for ext in ["*.jpg", "*.png", "*.jpeg", "*.JPG", "*.PNG"]:
                for img in source_path.glob(ext):
                    # 중복 체크
                    if img in seen:
                        continue

                    # 결과/처리된 이미지 제외
                    if any(x in img.name for x in ["_result", "_regions", "symbol", "row_", "_resized", "detection"]):
                        continue

                    # P&ID 페이지 이미지
                    if "page_" in img.name:
                        images.append((img, "pid"))
                        seen.add(img)
                    # P&ID 샘플
                    elif "pid" in img.name.lower() or "bwms" in img.name.lower():
                        images.append((img, "pid"))
                        seen.add(img)
                    # 기계 도면
                    elif category == "mechanical":
                        images.append((img, "mechanical"))
                        seen.add(img)
                    # 패널 도면
                    elif category == "panel":
                        images.append((img, "panel"))
                        seen.add(img)

    return images


def collect_images(dry_run: bool = False):
    """이미지 수집 및 복사"""

    print("=" * 70)
    print("도면 이미지 수집")
    print("=" * 70)

    images = find_drawing_images()
    print(f"\n발견된 이미지: {len(images)}개\n")

    # 카테고리별 통계
    categories = {}
    for img, cat in images:
        categories[cat] = categories.get(cat, 0) + 1

    print("카테고리별 분포:")
    for cat, count in sorted(categories.items()):
        print(f"  - {cat}: {count}개")

    if dry_run:
        print("\n[DRY RUN] 복사하지 않음")
        return images

    # 복사 디렉토리 생성
    unlabeled_dir = DATA_ROOT / "unlabeled"
    unlabeled_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n이미지 복사 중... → {unlabeled_dir}")

    copied = 0
    for img, cat in images:
        # 카테고리 접두사로 파일명 생성
        new_name = f"{cat}_{img.stem}{img.suffix}"
        dest = unlabeled_dir / new_name

        if not dest.exists():
            shutil.copy2(img, dest)
            copied += 1
            print(f"  복사: {new_name}")

    print(f"\n완료: {copied}개 복사됨")
    print(f"라벨링 대상: {unlabeled_dir}")

    return images


def check_status():
    """라벨링 상태 확인"""

    print("=" * 70)
    print("라벨링 상태 확인")
    print("=" * 70)

    # 각 디렉토리 확인
    dirs = {
        "unlabeled (라벨링 전)": DATA_ROOT / "unlabeled",
        "train/images": DATA_ROOT / "train/images",
        "train/labels": DATA_ROOT / "train/labels",
        "val/images": DATA_ROOT / "val/images",
        "val/labels": DATA_ROOT / "val/labels",
    }

    for name, path in dirs.items():
        if path.exists():
            count = len(list(path.glob("*")))
            print(f"  {name}: {count}개")
        else:
            print(f"  {name}: (없음)")

    # 라벨링 완료율 계산
    train_images = len(list((DATA_ROOT / "train/images").glob("*"))) if (DATA_ROOT / "train/images").exists() else 0
    train_labels = len(list((DATA_ROOT / "train/labels").glob("*.txt"))) if (DATA_ROOT / "train/labels").exists() else 0

    if train_images > 0:
        print(f"\n라벨링 완료율: {train_labels}/{train_images} ({train_labels/train_images*100:.1f}%)")


def split_data(ratio: float = 0.8):
    """train/val 분할"""

    print("=" * 70)
    print(f"데이터 분할 (train:val = {ratio}:{1-ratio})")
    print("=" * 70)

    # 라벨링된 이미지 찾기
    unlabeled_dir = DATA_ROOT / "unlabeled"

    if not unlabeled_dir.exists():
        print("[ERROR] unlabeled 디렉토리가 없습니다. --collect 먼저 실행하세요.")
        return

    # 이미지와 라벨 페어 찾기
    labeled_images = []
    for img in unlabeled_dir.glob("*.jpg"):
        label = img.with_suffix(".txt")
        if label.exists():
            labeled_images.append((img, label))

    for img in unlabeled_dir.glob("*.png"):
        label = img.with_suffix(".txt")
        if label.exists():
            labeled_images.append((img, label))

    if not labeled_images:
        print("[INFO] 라벨링된 이미지가 없습니다.")
        print("       LabelImg, CVAT, 또는 Roboflow를 사용하여 라벨링하세요.")
        print(f"       라벨 형식: YOLO (class_id x_center y_center width height)")
        return

    print(f"라벨링된 이미지: {len(labeled_images)}개")

    # 셔플 및 분할
    random.shuffle(labeled_images)
    split_idx = int(len(labeled_images) * ratio)
    train_set = labeled_images[:split_idx]
    val_set = labeled_images[split_idx:]

    print(f"  Train: {len(train_set)}개")
    print(f"  Val: {len(val_set)}개")

    # 디렉토리 생성
    for split in ["train", "val"]:
        (DATA_ROOT / split / "images").mkdir(parents=True, exist_ok=True)
        (DATA_ROOT / split / "labels").mkdir(parents=True, exist_ok=True)

    # 파일 복사
    for img, label in train_set:
        shutil.copy2(img, DATA_ROOT / "train/images" / img.name)
        shutil.copy2(label, DATA_ROOT / "train/labels" / label.name)

    for img, label in val_set:
        shutil.copy2(img, DATA_ROOT / "val/images" / img.name)
        shutil.copy2(label, DATA_ROOT / "val/labels" / label.name)

    print("\n분할 완료!")


def create_sample_label():
    """샘플 라벨 파일 생성 (가이드용)"""

    sample_label = """# YOLO 라벨 형식 예시
# class_id x_center y_center width height
# 모든 좌표는 0-1 범위로 정규화

# 클래스 ID:
# 0: title_block
# 1: main_view
# 2: detail_view
# 3: section_view
# 4: bom_table
# 5: notes
# 6: legend
# 7: revision_block

# 예시: 표제란 (우하단)
0 0.85 0.9 0.25 0.15

# 예시: 주 도면 뷰 (중앙)
1 0.4 0.5 0.7 0.8

# 예시: BOM 테이블 (우측)
4 0.9 0.3 0.18 0.4
"""

    sample_path = DATA_ROOT / "sample_label.txt"
    sample_path.parent.mkdir(parents=True, exist_ok=True)

    with open(sample_path, "w") as f:
        f.write(sample_label)

    print(f"샘플 라벨 생성: {sample_path}")


def main():
    parser = argparse.ArgumentParser(description="DocLayout-YOLO 데이터 준비")
    parser.add_argument("--collect", action="store_true", help="이미지 수집 및 복사")
    parser.add_argument("--status", action="store_true", help="라벨링 상태 확인")
    parser.add_argument("--split", action="store_true", help="train/val 분할")
    parser.add_argument("--ratio", type=float, default=0.8, help="train 비율 (기본: 0.8)")
    parser.add_argument("--dry-run", action="store_true", help="실제 복사 없이 확인만")
    parser.add_argument("--sample-label", action="store_true", help="샘플 라벨 파일 생성")
    args = parser.parse_args()

    if args.collect:
        collect_images(dry_run=args.dry_run)
    elif args.status:
        check_status()
    elif args.split:
        split_data(ratio=args.ratio)
    elif args.sample_label:
        create_sample_label()
    else:
        # 기본: 상태 확인
        check_status()
        print("\n사용법:")
        print("  python prepare_data.py --collect      # 이미지 수집")
        print("  python prepare_data.py --status       # 상태 확인")
        print("  python prepare_data.py --split        # train/val 분할")
        print("  python prepare_data.py --sample-label # 샘플 라벨 생성")


if __name__ == "__main__":
    main()
