"""
Phase 1.1: YOLO (P&ID Mode) Confidence Tuning Experiment
P&ID 심볼 검출 최적 confidence 값 탐색

실행: python phase1_confidence_tuning.py

Note: YOLO 통합 API 사용 (model_type=pid_class_aware)
"""
import requests
import json
import time
from pathlib import Path
from collections import defaultdict
import cv2
import numpy as np
import base64

# 설정 - YOLO 통합 API (model_type으로 P&ID 모드 선택)
API_URL = "http://localhost:5005/api/v1/detect"
SAMPLE_IMAGE = Path(__file__).parent.parent.parent / "web-ui/public/samples/pid_detection_optimized.png"

# Ground Truth (내가 직접 P&ID에서 확인한 값)
GROUND_TRUTH = {
    "total_symbols": 90,  # 대략적 추정
    "categories": {
        "tank": 3,       # Column 1, 2, 3
        "heat_exchanger": 15,  # Condensers + Exchangers + Reboilers
        "pump": 12,
        "valve": 15,
        "instrument": 35,  # TI, FC, LC, PC, FI, TC
        "misc": 10
    }
}


def test_confidence(confidence: float, slice_size: int = 512) -> dict:
    """특정 confidence 값으로 검출 테스트"""
    with open(SAMPLE_IMAGE, "rb") as f:
        response = requests.post(
            API_URL,
            files={"file": f},
            data={
                "model_type": "pid_class_aware",  # P&ID 심볼 분류 모드
                "confidence": str(confidence),
                "slice_height": str(slice_size),
                "slice_width": str(slice_size),
                "overlap_ratio": "0.25",
                "use_sahi": "true",  # P&ID는 SAHI 권장
                "visualize": "false"
            },
            timeout=120
        )

    result = response.json()
    if not result.get("success"):
        return {"error": result.get("error")}

    detections = result["data"]["detections"]

    # 카테고리별 집계
    category_counts = defaultdict(int)
    class_counts = defaultdict(int)

    for det in detections:
        category = det.get("category", "misc")
        class_name = det.get("class_name", "unknown")
        category_counts[category] += 1
        class_counts[class_name] += 1

    return {
        "confidence": confidence,
        "total_detections": len(detections),
        "categories": dict(category_counts),
        "classes": dict(class_counts),
        "processing_time": result.get("processing_time", 0)
    }


def calculate_metrics(result: dict) -> dict:
    """Ground Truth 대비 정확도 계산"""
    total_detected = result["total_detections"]
    total_gt = GROUND_TRUTH["total_symbols"]

    # Precision/Recall 추정 (정확한 계산은 bbox matching 필요)
    if total_detected == 0:
        return {"precision": 0, "recall": 0, "f1": 0}

    # 대략적인 추정
    # - 검출 수가 GT보다 많으면 오탐(FP) 가능성
    # - 검출 수가 GT보다 적으면 미검(FN) 가능성

    if total_detected <= total_gt:
        # 미검출 상황: Recall 낮음
        recall = total_detected / total_gt
        precision = 0.95  # 검출된 것은 대부분 맞다고 가정
    else:
        # 오탐 상황: Precision 낮음
        recall = min(1.0, total_gt / total_detected * 1.1)  # GT만큼은 검출했다고 가정
        precision = total_gt / total_detected

    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "detection_ratio": round(total_detected / total_gt, 3)
    }


def run_experiment():
    """Confidence 값 범위에서 최적값 탐색"""
    print("=" * 60)
    print("Phase 1.1: YOLO (P&ID Mode) Confidence Tuning Experiment")
    print("=" * 60)
    print(f"\nSample Image: {SAMPLE_IMAGE}")
    print(f"Ground Truth: ~{GROUND_TRUTH['total_symbols']} symbols\n")

    # 테스트할 confidence 값들
    confidence_values = [0.05, 0.08, 0.10, 0.12, 0.15, 0.20, 0.25, 0.30]

    results = []

    print(f"{'Conf':<8} {'Total':<8} {'Ratio':<8} {'F1':<8} {'Time':<8}")
    print("-" * 45)

    for conf in confidence_values:
        result = test_confidence(conf)

        if "error" in result:
            print(f"{conf:<8} ERROR: {result['error']}")
            continue

        metrics = calculate_metrics(result)
        result["metrics"] = metrics
        results.append(result)

        print(f"{conf:<8.2f} {result['total_detections']:<8} "
              f"{metrics['detection_ratio']:<8.2f} {metrics['f1']:<8.3f} "
              f"{result['processing_time']:<8.2f}s")

    # 최적 값 찾기
    if results:
        best = max(results, key=lambda x: x["metrics"]["f1"])
        print("\n" + "=" * 60)
        print(f"최적 Confidence: {best['confidence']}")
        print(f"  - 검출 수: {best['total_detections']}")
        print(f"  - F1 Score: {best['metrics']['f1']}")
        print(f"  - Detection Ratio: {best['metrics']['detection_ratio']}")

        print(f"\n카테고리별 검출:")
        for cat, count in sorted(best["categories"].items()):
            gt_count = GROUND_TRUTH["categories"].get(cat, "?")
            print(f"  - {cat}: {count} (GT: {gt_count})")

        print(f"\n클래스별 상세 (상위 10개):")
        sorted_classes = sorted(best["classes"].items(), key=lambda x: -x[1])[:10]
        for cls, count in sorted_classes:
            print(f"  - {cls}: {count}")

        # 결과 저장
        output_path = Path(__file__).parent / "phase1_results.json"
        with open(output_path, "w") as f:
            json.dump({
                "experiment": "confidence_tuning",
                "best_confidence": best["confidence"],
                "all_results": results,
                "ground_truth": GROUND_TRUTH
            }, f, indent=2, ensure_ascii=False)
        print(f"\n결과 저장: {output_path}")

    return results


def test_slice_sizes():
    """Slice size 비교 테스트"""
    print("\n" + "=" * 60)
    print("Slice Size Comparison (confidence=0.10)")
    print("=" * 60)

    slice_sizes = [256, 384, 512, 640, 768]

    print(f"\n{'Slice':<8} {'Total':<8} {'Time':<10}")
    print("-" * 30)

    for size in slice_sizes:
        result = test_confidence(0.10, slice_size=size)
        if "error" not in result:
            print(f"{size:<8} {result['total_detections']:<8} {result['processing_time']:<10.2f}s")


if __name__ == "__main__":
    # 1. Confidence 튜닝
    results = run_experiment()

    # 2. Slice size 비교
    test_slice_sizes()
