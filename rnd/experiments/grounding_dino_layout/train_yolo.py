#!/usr/bin/env python3
"""
Phase 2 Step 2: YOLO v11 커스텀 파인튜닝 — 기계도면 레이아웃 디텍션

Pre-label(Grounding DINO) 기반 초기 학습.
노이즈가 있으므로 적은 에포크로 빠르게 baseline 확인.
"""

import torch
from pathlib import Path
from ultralytics import YOLO

# ── 설정 ──────────────────────────────────────────────
DATASET_DIR = Path(__file__).parent / "dataset"
DATA_YAML = DATASET_DIR / "data.yaml"
OUTPUT_DIR = Path(__file__).parent / "runs"

# 학습 파라미터 (pre-label이므로 보수적)
EPOCHS = 10          # pre-label이므로 10이면 충분
BATCH_SIZE = 8       # RTX 3080 Laptop — small 모델은 배치 늘려도 OK
IMG_SIZE = 640       # 빠른 실험용
MODEL_SIZE = "yolo11s.pt"  # small — 빠른 baseline


def main():
    print("=" * 60)
    print("YOLO v11 커스텀 파인튜닝 — 기계도면 레이아웃")
    print("=" * 60)

    # GPU 확인
    if torch.cuda.is_available():
        gpu = torch.cuda.get_device_name(0)
        mem = torch.cuda.get_device_properties(0).total_mem / 1024**3 if hasattr(torch.cuda.get_device_properties(0), 'total_mem') else 0
        print(f"[GPU] {gpu}")
    else:
        print("[WARN] CUDA not available")

    # 데이터셋 확인
    print(f"[DATA] {DATA_YAML}")
    n_images = len(list((DATASET_DIR / "images" / "train").glob("*.png")))
    n_labels = len(list((DATASET_DIR / "labels" / "train").glob("*.txt")))
    print(f"[DATA] {n_images} images, {n_labels} labels")

    # 모델 로드 (사전학습 COCO 체크포인트에서 시작)
    print(f"\n[MODEL] Loading {MODEL_SIZE}")
    model = YOLO(MODEL_SIZE)

    # 학습 실행
    print(f"\n[TRAIN] epochs={EPOCHS}, batch={BATCH_SIZE}, imgsz={IMG_SIZE}")
    print("-" * 60)

    results = model.train(
        data=str(DATA_YAML),
        epochs=EPOCHS,
        batch=BATCH_SIZE,
        imgsz=IMG_SIZE,
        device="0",
        project=str(OUTPUT_DIR),
        name="layout_v1",
        # 데이터 증강 (도면 특성 고려)
        hsv_h=0.0,       # 색조 변경 없음 (흑백 도면)
        hsv_s=0.0,        # 채도 변경 없음
        hsv_v=0.2,        # 명도만 약간
        degrees=0.0,      # 회전 없음 (도면은 정방향)
        translate=0.05,    # 약간의 이동
        scale=0.3,         # 스케일 변화
        flipud=0.0,        # 상하 반전 없음
        fliplr=0.0,        # 좌우 반전 없음 (도면 구조 유지)
        mosaic=0.0,        # 모자이크 없음 (도면 레이아웃 파괴 방지)
        mixup=0.0,         # 믹스업 없음
        # 학습률 (노이즈 라벨 대응)
        lr0=0.001,         # 낮은 초기 학습률
        lrf=0.01,          # 최종 학습률 비율
        warmup_epochs=3,
        # 기타
        patience=10,       # 조기 종료
        save_period=10,    # 10에포크마다 체크포인트
        plots=True,
        verbose=True,
    )

    # 결과 요약
    print(f"\n{'='*60}")
    print("학습 완료")
    print(f"{'='*60}")

    # best 모델로 검증
    best_model_path = OUTPUT_DIR / "layout_v1" / "weights" / "best.pt"
    if best_model_path.exists():
        print(f"[BEST] {best_model_path}")

        # 검증 실행
        val_model = YOLO(str(best_model_path))
        val_results = val_model.val(data=str(DATA_YAML), imgsz=IMG_SIZE, device="0")

        print(f"\n[VAL] mAP50: {val_results.box.map50:.3f}")
        print(f"[VAL] mAP50-95: {val_results.box.map:.3f}")

        # 클래스별 AP
        if hasattr(val_results.box, 'ap_class_index'):
            names = val_model.names
            for i, ap50 in enumerate(val_results.box.ap50):
                cls_name = names.get(i, f"class_{i}")
                print(f"  {cls_name}: AP50={ap50:.3f}")

    print(f"\n결과: {OUTPUT_DIR / 'layout_v1'}")


if __name__ == "__main__":
    main()
