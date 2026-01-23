#!/usr/bin/env python3
"""
YOLO Confidence Threshold Test
==============================
BWMS P&ID 도면에서 다양한 confidence threshold 설정으로 검출 결과를 비교합니다.

테스트 설정:
- Baseline: confidence=0.25 (현재)
- Test A: confidence=0.35
- Test B: confidence=0.45
- Test C: confidence=0.50

평가 지표:
- 총 검출 수
- 클래스별 검출 수
- 평균 신뢰도
- 최소/최대 신뢰도
- 저신뢰도 검출 비율 (< 50%, < 70%)
"""

import requests
import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Configuration
YOLO_API_URL = "http://localhost:5005/api/v1/detect"
SAMPLE_IMAGE = "/home/uproot/ax/poc/web-ui/public/samples/bwms_pid_sample.png"
OUTPUT_DIR = Path("/home/uproot/ax/poc/rnd/experiments/bwms_pipeline_improvement/results")

# Test configurations
TEST_CONFIGS = [
    {"name": "Baseline", "confidence": 0.25, "description": "현재 설정"},
    {"name": "Test_A", "confidence": 0.35, "description": "권장 설정"},
    {"name": "Test_B", "confidence": 0.45, "description": "보수적 설정"},
    {"name": "Test_C", "confidence": 0.50, "description": "고신뢰도 전용"},
]

# Common parameters
COMMON_PARAMS = {
    "model_type": "pid_class_aware",
    "iou": 0.45,
    "imgsz": 640,
    "use_sahi": True,
}


def run_detection(image_path: str, confidence: float) -> dict:
    """Run YOLO detection with specified confidence threshold using multipart/form-data."""
    with open(image_path, "rb") as f:
        files = {"file": (Path(image_path).name, f, "image/png")}
        data = {
            "model_type": COMMON_PARAMS["model_type"],
            "confidence": str(confidence),
            "iou": str(COMMON_PARAMS["iou"]),
            "imgsz": str(COMMON_PARAMS["imgsz"]),
            "use_sahi": str(COMMON_PARAMS["use_sahi"]).lower(),
            "visualize": "false",  # 시각화 비활성화로 속도 향상
        }

        response = requests.post(YOLO_API_URL, files=files, data=data, timeout=120)
        response.raise_for_status()
        return response.json()


def analyze_results(detections: list) -> dict:
    """Analyze detection results and compute metrics."""
    if not detections:
        return {
            "total_count": 0,
            "class_counts": {},
            "avg_confidence": 0,
            "min_confidence": 0,
            "max_confidence": 0,
            "below_50_pct": 0,
            "below_70_pct": 0,
            "confidence_distribution": {},
        }

    # Extract confidences
    confidences = [d.get("confidence", 0) for d in detections]

    # Class counts
    class_counts = defaultdict(int)
    class_confidences = defaultdict(list)
    for d in detections:
        cls = d.get("class_name", d.get("class", "unknown"))
        conf = d.get("confidence", 0)
        class_counts[cls] += 1
        class_confidences[cls].append(conf)

    # Confidence distribution
    distribution = {
        "90-100%": sum(1 for c in confidences if c >= 0.9),
        "80-90%": sum(1 for c in confidences if 0.8 <= c < 0.9),
        "70-80%": sum(1 for c in confidences if 0.7 <= c < 0.8),
        "50-70%": sum(1 for c in confidences if 0.5 <= c < 0.7),
        "30-50%": sum(1 for c in confidences if 0.3 <= c < 0.5),
        "<30%": sum(1 for c in confidences if c < 0.3),
    }

    # Class-level analysis
    class_analysis = {}
    for cls, counts in sorted(class_counts.items(), key=lambda x: -x[1]):
        confs = class_confidences[cls]
        class_analysis[cls] = {
            "count": counts,
            "avg_confidence": round(sum(confs) / len(confs) * 100, 1),
            "min_confidence": round(min(confs) * 100, 1),
        }

    return {
        "total_count": len(detections),
        "class_counts": dict(class_counts),
        "class_analysis": class_analysis,
        "avg_confidence": round(sum(confidences) / len(confidences) * 100, 1),
        "min_confidence": round(min(confidences) * 100, 1),
        "max_confidence": round(max(confidences) * 100, 1),
        "below_50_pct": sum(1 for c in confidences if c < 0.5),
        "below_70_pct": sum(1 for c in confidences if c < 0.7),
        "confidence_distribution": distribution,
    }


def print_results(config: dict, analysis: dict):
    """Print formatted results."""
    print(f"\n{'='*60}")
    print(f"🔬 {config['name']}: confidence={config['confidence']} ({config['description']})")
    print(f"{'='*60}")

    print(f"\n📊 총 검출: {analysis['total_count']}개")
    print(f"   평균 신뢰도: {analysis['avg_confidence']}%")
    print(f"   최소 신뢰도: {analysis['min_confidence']}%")
    print(f"   최대 신뢰도: {analysis['max_confidence']}%")

    print(f"\n⚠️  저신뢰도 검출:")
    print(f"   < 50%: {analysis['below_50_pct']}개 ({analysis['below_50_pct']/max(1,analysis['total_count'])*100:.1f}%)")
    print(f"   < 70%: {analysis['below_70_pct']}개 ({analysis['below_70_pct']/max(1,analysis['total_count'])*100:.1f}%)")

    print(f"\n📈 신뢰도 분포:")
    for range_name, count in analysis['confidence_distribution'].items():
        bar = "█" * (count // 2)
        print(f"   {range_name:>8}: {count:3}개 {bar}")

    print(f"\n🏷️  클래스별 검출 (상위 10개):")
    if analysis.get('class_analysis'):
        for i, (cls, info) in enumerate(list(analysis['class_analysis'].items())[:10]):
            status = "✅" if info['min_confidence'] >= 50 else "⚠️" if info['min_confidence'] >= 30 else "❌"
            print(f"   {status} {cls}: {info['count']}개 (avg: {info['avg_confidence']}%, min: {info['min_confidence']}%)")


def main():
    print("=" * 60)
    print("🔬 YOLO Confidence Threshold Test")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Image: {SAMPLE_IMAGE}")
    print("=" * 60)

    # Check image exists
    print("\n📷 Checking image...")
    if not Path(SAMPLE_IMAGE).exists():
        print(f"   ❌ Image not found: {SAMPLE_IMAGE}")
        sys.exit(1)
    file_size = Path(SAMPLE_IMAGE).stat().st_size // 1024
    print(f"   ✅ Image found ({file_size}KB)")

    # Run tests
    results = []
    for config in TEST_CONFIGS:
        print(f"\n🚀 Running {config['name']} (confidence={config['confidence']})...")
        try:
            response = run_detection(SAMPLE_IMAGE, config['confidence'])
            detections = response.get("detections", [])
            analysis = analyze_results(detections)

            results.append({
                "config": config,
                "analysis": analysis,
                "raw_response": response,
            })

            print_results(config, analysis)

        except requests.exceptions.RequestException as e:
            print(f"   ❌ API Error: {e}")
            continue

    # Summary comparison
    print("\n" + "=" * 60)
    print("📊 SUMMARY COMPARISON")
    print("=" * 60)
    print(f"\n{'Config':<12} {'Conf':>6} {'Total':>6} {'Avg%':>6} {'Min%':>6} {'<50%':>6} {'<70%':>6}")
    print("-" * 54)
    for r in results:
        c = r['config']
        a = r['analysis']
        print(f"{c['name']:<12} {c['confidence']:>6.2f} {a['total_count']:>6} {a['avg_confidence']:>6.1f} {a['min_confidence']:>6.1f} {a['below_50_pct']:>6} {a['below_70_pct']:>6}")

    # Recommendation
    print("\n" + "=" * 60)
    print("💡 RECOMMENDATION")
    print("=" * 60)

    # Find best balance
    for r in results:
        if r['config']['confidence'] == 0.35:
            baseline = results[0]['analysis']
            test_a = r['analysis']
            removed = baseline['total_count'] - test_a['total_count']
            low_conf_removed = baseline['below_50_pct'] - test_a['below_50_pct']
            print(f"\n✅ confidence=0.35 권장:")
            print(f"   - 총 검출: {baseline['total_count']} → {test_a['total_count']} ({removed}개 제거)")
            print(f"   - 저신뢰도(<50%) 제거: {low_conf_removed}개")
            print(f"   - 평균 신뢰도: {baseline['avg_confidence']}% → {test_a['avg_confidence']}%")
            print(f"   - 최소 신뢰도: {baseline['min_confidence']}% → {test_a['min_confidence']}%")

    # Save results
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"yolo_confidence_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        # Remove raw_response for cleaner output
        save_results = [
            {"config": r['config'], "analysis": r['analysis']}
            for r in results
        ]
        json.dump(save_results, f, indent=2, ensure_ascii=False)

    print(f"\n📁 Results saved: {output_file}")
    print("\n✅ Test completed!")


if __name__ == "__main__":
    main()
