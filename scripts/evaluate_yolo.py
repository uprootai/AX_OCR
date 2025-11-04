#!/usr/bin/env python3
"""
YOLOv11 모델 평가
"""
import argparse
from ultralytics import YOLO

def evaluate_model(
    model_path,
    data_yaml='datasets/engineering_drawings/data.yaml',
    split='test',
    imgsz=1280,
    device='0'
):
    """
    모델 평가 실행
    """
    print("=" * 70)
    print("📊 YOLOv11 Model Evaluation")
    print("=" * 70)
    print(f"Model: {model_path}")
    print(f"Dataset: {data_yaml}")
    print(f"Split: {split}")
    print("=" * 70)

    # 모델 로드
    model = YOLO(model_path)

    # 평가 실행
    metrics = model.val(
        data=data_yaml,
        split=split,
        imgsz=imgsz,
        device=device,
        save_json=True,
        save_hybrid=True,
        plots=True
    )

    # 결과 출력
    print("\n" + "=" * 70)
    print("📈 Evaluation Results")
    print("=" * 70)
    print(f"Precision: {metrics.box.p:.4f}")
    print(f"Recall: {metrics.box.r:.4f}")
    print(f"mAP50: {metrics.box.map50:.4f}")
    print(f"mAP50-95: {metrics.box.map:.4f}")

    # F1 Score 계산
    if metrics.box.p > 0 and metrics.box.r > 0:
        f1_score = 2 * (metrics.box.p * metrics.box.r) / (metrics.box.p + metrics.box.r)
        print(f"F1 Score: {f1_score:.4f}")
    else:
        print("F1 Score: N/A (precision or recall is 0)")

    return metrics

def main():
    parser = argparse.ArgumentParser(description='Evaluate YOLOv11 model')

    parser.add_argument('--model', type=str, required=True,
                        help='Path to model weights')
    parser.add_argument('--data', type=str,
                        default='datasets/engineering_drawings/data.yaml',
                        help='Path to data.yaml')
    parser.add_argument('--split', type=str, default='test',
                        choices=['train', 'val', 'test'],
                        help='Dataset split to evaluate')
    parser.add_argument('--imgsz', type=int, default=1280,
                        help='Image size')
    parser.add_argument('--device', type=str, default='0',
                        help='CUDA device or cpu')

    args = parser.parse_args()

    evaluate_model(
        model_path=args.model,
        data_yaml=args.data,
        split=args.split,
        imgsz=args.imgsz,
        device=args.device
    )

if __name__ == '__main__':
    main()
