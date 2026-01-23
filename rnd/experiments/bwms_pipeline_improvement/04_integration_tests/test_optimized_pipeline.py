#!/usr/bin/env python3
"""
BWMS Pipeline Integration Test
==============================
Baseline vs Optimized 설정 비교 테스트

Baseline 설정:
- YOLO: confidence=0.25, 필터링 없음
- Line Detector: min_length=0, method=combined
- Design Checker: product_type=AUTO

Optimized 설정:
- YOLO: confidence=0.25 + 클라이언트 필터 0.35
- Line Detector: min_length=50, method=lsd
- Design Checker: product_type=ECS
"""

import requests
import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Configuration
YOLO_API_URL = "http://localhost:5005/api/v1/detect"
LINE_DETECTOR_URL = "http://localhost:5016/api/v1/process"
DESIGN_CHECKER_URL = "http://localhost:5019/api/v1/check"
SAMPLE_IMAGE = "/home/uproot/ax/poc/web-ui/public/samples/bwms_pid_sample.png"
OUTPUT_DIR = Path("/home/uproot/ax/poc/rnd/experiments/bwms_pipeline_improvement/results")

# Test configurations
CONFIGS = {
    "baseline": {
        "name": "Baseline",
        "description": "현재 설정",
        "yolo": {
            "model_type": "pid_class_aware",
            "confidence": 0.25,
            "iou": 0.45,
            "imgsz": 640,
            "use_sahi": True,
        },
        "line_detector": {
            "method": "combined",
            "min_length": 0,
            "merge_lines": True,
            "classify_types": True,
            "classify_colors": True,
            "classify_styles": True,
            "find_intersections": True,
        },
        "design_checker": {
            "categories": "bwms",
            "severity_threshold": "info",
            "include_bwms": True,
        },
        "client_filter": 0.0,  # No client-side filtering
    },
    "optimized": {
        "name": "Optimized",
        "description": "권장 설정",
        "yolo": {
            "model_type": "pid_class_aware",
            "confidence": 0.25,
            "iou": 0.45,
            "imgsz": 640,
            "use_sahi": True,
        },
        "line_detector": {
            "method": "lsd",
            "min_length": 50,
            "merge_lines": True,
            "classify_types": True,
            "classify_colors": True,
            "classify_styles": True,
            "find_intersections": True,
        },
        "design_checker": {
            "categories": "bwms",
            "severity_threshold": "info",
            "include_bwms": True,
        },
        "client_filter": 0.35,  # Client-side confidence filter
    },
}


def run_yolo(image_path: str, params: dict) -> dict:
    """Run YOLO detection."""
    with open(image_path, "rb") as f:
        files = {"file": (Path(image_path).name, f, "image/png")}
        data = {
            "model_type": params["model_type"],
            "confidence": str(params["confidence"]),
            "iou": str(params["iou"]),
            "imgsz": str(params["imgsz"]),
            "use_sahi": str(params["use_sahi"]).lower(),
            "visualize": "false",
        }
        response = requests.post(YOLO_API_URL, files=files, data=data, timeout=180)
        response.raise_for_status()
        return response.json()


def run_line_detector(image_path: str, params: dict) -> dict:
    """Run Line Detector."""
    with open(image_path, "rb") as f:
        files = {"file": (Path(image_path).name, f, "image/png")}
        data = {
            "method": params["method"],
            "min_length": str(params["min_length"]),
            "merge_lines": str(params["merge_lines"]).lower(),
            "classify_types": str(params["classify_types"]).lower(),
            "classify_colors": str(params["classify_colors"]).lower(),
            "classify_styles": str(params["classify_styles"]).lower(),
            "find_intersections": str(params["find_intersections"]).lower(),
            "visualize": "false",
        }
        response = requests.post(LINE_DETECTOR_URL, files=files, data=data, timeout=120)
        response.raise_for_status()
        return response.json()


def run_design_checker(symbols: list, connections: list, params: dict) -> dict:
    """Run Design Checker."""
    payload = {
        "symbols": symbols,
        "connections": connections,
        "categories": params["categories"],
        "severity_threshold": params["severity_threshold"],
        "include_bwms": params["include_bwms"],
    }
    response = requests.post(DESIGN_CHECKER_URL, json=payload, timeout=60)
    response.raise_for_status()
    return response.json()


def filter_detections(detections: list, min_confidence: float) -> list:
    """Filter detections by confidence threshold."""
    if min_confidence <= 0:
        return detections
    return [d for d in detections if d.get("confidence", 0) >= min_confidence]


def analyze_yolo_results(detections: list) -> dict:
    """Analyze YOLO detection results."""
    if not detections:
        return {
            "total": 0,
            "avg_confidence": 0,
            "min_confidence": 0,
            "max_confidence": 0,
            "by_class": {},
            "low_confidence_count": 0,
        }

    confidences = [d.get("confidence", 0) for d in detections]
    class_counts = defaultdict(int)
    for d in detections:
        cls = d.get("class_name", d.get("class", "unknown"))
        class_counts[cls] += 1

    return {
        "total": len(detections),
        "avg_confidence": round(sum(confidences) / len(confidences) * 100, 1),
        "min_confidence": round(min(confidences) * 100, 1),
        "max_confidence": round(max(confidences) * 100, 1),
        "by_class": dict(class_counts),
        "low_confidence_count": sum(1 for c in confidences if c < 0.5),
    }


def analyze_line_results(response: dict) -> dict:
    """Analyze Line Detector results."""
    data = response.get("data", response)
    lines = data.get("lines", [])
    intersections = data.get("intersections", [])

    return {
        "total_lines": len(lines),
        "total_intersections": len(intersections),
    }


def run_pipeline(config_name: str, config: dict) -> dict:
    """Run full pipeline with given configuration."""
    print(f"\n{'='*60}")
    print(f"🚀 Running {config['name']} ({config['description']})")
    print(f"{'='*60}")

    results = {
        "config_name": config_name,
        "config": config,
        "timings": {},
        "results": {},
    }

    import time

    # Step 1: YOLO Detection
    print("\n📍 Step 1: YOLO Detection...")
    start = time.time()
    try:
        yolo_response = run_yolo(SAMPLE_IMAGE, config["yolo"])
        yolo_time = time.time() - start
        results["timings"]["yolo"] = round(yolo_time, 2)

        detections = yolo_response.get("data", yolo_response).get("detections", [])
        print(f"   ✅ Raw detections: {len(detections)} ({yolo_time:.2f}s)")

        # Apply client-side filter
        filtered = filter_detections(detections, config["client_filter"])
        print(f"   ✅ After filter (>={config['client_filter']*100:.0f}%): {len(filtered)}")

        results["results"]["yolo_raw"] = analyze_yolo_results(detections)
        results["results"]["yolo_filtered"] = analyze_yolo_results(filtered)
        results["detections"] = filtered

    except Exception as e:
        print(f"   ❌ YOLO Error: {e}")
        results["results"]["yolo_raw"] = {"total": 0, "error": str(e)}
        results["results"]["yolo_filtered"] = {"total": 0}
        results["detections"] = []

    # Step 2: Line Detector
    print("\n📍 Step 2: Line Detector...")
    start = time.time()
    try:
        line_response = run_line_detector(SAMPLE_IMAGE, config["line_detector"])
        line_time = time.time() - start
        results["timings"]["line_detector"] = round(line_time, 2)

        line_analysis = analyze_line_results(line_response)
        print(f"   ✅ Lines: {line_analysis['total_lines']}, Intersections: {line_analysis['total_intersections']} ({line_time:.2f}s)")

        results["results"]["line_detector"] = line_analysis

    except Exception as e:
        print(f"   ❌ Line Detector Error: {e}")
        results["results"]["line_detector"] = {"total_lines": 0, "error": str(e)}

    # Step 3: Design Checker (simplified - just count rules)
    print("\n📍 Step 3: Design Checker...")
    start = time.time()
    try:
        # Convert detections to symbols format
        symbols = [
            {
                "class_name": d.get("class_name", "unknown"),
                "bbox": d.get("bbox", {}),
                "confidence": d.get("confidence", 0),
            }
            for d in results.get("detections", [])
        ]

        checker_response = run_design_checker(symbols, [], config["design_checker"])
        checker_time = time.time() - start
        results["timings"]["design_checker"] = round(checker_time, 2)

        data = checker_response.get("data", checker_response)
        violations = data.get("violations", [])
        summary = data.get("summary", {})

        print(f"   ✅ Rules: {summary.get('total_rules', 0)}, Violations: {len(violations)} ({checker_time:.2f}s)")

        results["results"]["design_checker"] = {
            "total_rules": summary.get("total_rules", 0),
            "passed": summary.get("passed", 0),
            "failed": summary.get("failed", 0),
            "violations": len(violations),
            "compliance_score": summary.get("compliance_score", 0),
        }

    except Exception as e:
        print(f"   ❌ Design Checker Error: {e}")
        results["results"]["design_checker"] = {"total_rules": 0, "error": str(e)}

    # Total time
    results["timings"]["total"] = round(sum(results["timings"].values()), 2)
    print(f"\n⏱️  Total time: {results['timings']['total']:.2f}s")

    return results


def print_comparison(baseline: dict, optimized: dict):
    """Print comparison between baseline and optimized results."""
    print("\n" + "=" * 70)
    print("📊 COMPARISON: Baseline vs Optimized")
    print("=" * 70)

    # Header
    print(f"\n{'Metric':<35} {'Baseline':>12} {'Optimized':>12} {'Change':>12}")
    print("-" * 70)

    # YOLO
    b_yolo = baseline["results"].get("yolo_filtered", {})
    o_yolo = optimized["results"].get("yolo_filtered", {})

    b_det = b_yolo.get("total", 0)
    o_det = o_yolo.get("total", 0)
    det_change = o_det - b_det
    print(f"{'YOLO Detections (filtered)':<35} {b_det:>12} {o_det:>12} {det_change:>+12}")

    b_avg = b_yolo.get("avg_confidence", 0)
    o_avg = o_yolo.get("avg_confidence", 0)
    avg_change = o_avg - b_avg
    print(f"{'YOLO Avg Confidence (%)':<35} {b_avg:>11.1f}% {o_avg:>11.1f}% {avg_change:>+11.1f}%")

    b_low = b_yolo.get("low_confidence_count", 0)
    o_low = o_yolo.get("low_confidence_count", 0)
    low_change = o_low - b_low
    print(f"{'YOLO Low Confidence (<50%)':<35} {b_low:>12} {o_low:>12} {low_change:>+12}")

    # Line Detector
    b_line = baseline["results"].get("line_detector", {})
    o_line = optimized["results"].get("line_detector", {})

    b_lines = b_line.get("total_lines", 0)
    o_lines = o_line.get("total_lines", 0)
    lines_change = o_lines - b_lines
    lines_pct = (lines_change / max(1, b_lines)) * 100
    print(f"{'Line Detector Lines':<35} {b_lines:>12} {o_lines:>12} {lines_change:>+8} ({lines_pct:>+.0f}%)")

    b_inter = b_line.get("total_intersections", 0)
    o_inter = o_line.get("total_intersections", 0)
    inter_change = o_inter - b_inter
    print(f"{'Line Detector Intersections':<35} {b_inter:>12} {o_inter:>12} {inter_change:>+12}")

    # Design Checker
    b_dc = baseline["results"].get("design_checker", {})
    o_dc = optimized["results"].get("design_checker", {})

    b_rules = b_dc.get("total_rules", 0)
    o_rules = o_dc.get("total_rules", 0)
    rules_change = o_rules - b_rules
    print(f"{'Design Checker Rules':<35} {b_rules:>12} {o_rules:>12} {rules_change:>+12}")

    # Timing
    print("-" * 70)
    b_time = baseline["timings"].get("total", 0)
    o_time = optimized["timings"].get("total", 0)
    time_change = o_time - b_time
    print(f"{'Total Processing Time (s)':<35} {b_time:>11.2f}s {o_time:>11.2f}s {time_change:>+11.2f}s")

    # Summary
    print("\n" + "=" * 70)
    print("💡 SUMMARY")
    print("=" * 70)

    improvements = []
    if lines_change < 0:
        improvements.append(f"✅ 라인 수 {abs(lines_pct):.0f}% 감소 ({b_lines} → {o_lines})")
    if o_avg > b_avg:
        improvements.append(f"✅ 평균 신뢰도 {o_avg - b_avg:.1f}%p 향상")
    if o_low < b_low:
        improvements.append(f"✅ 저신뢰도 검출 {b_low - o_low}개 제거")
    if o_rules > b_rules:
        improvements.append(f"✅ 적용 규칙 {o_rules - b_rules}개 추가 (+{(o_rules/max(1,b_rules)-1)*100:.0f}%)")

    if improvements:
        print("\n개선 사항:")
        for imp in improvements:
            print(f"   {imp}")
    else:
        print("\n⚠️  유의미한 개선 없음")

    return {
        "lines_reduction": lines_pct,
        "confidence_improvement": o_avg - b_avg,
        "low_confidence_reduction": b_low - o_low,
        "rules_increase": o_rules - b_rules,
        "time_change": time_change,
    }


def main():
    print("=" * 70)
    print("🔬 BWMS Pipeline Integration Test")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Image: {SAMPLE_IMAGE}")
    print("=" * 70)

    # Check image exists
    print("\n📷 Checking image...")
    if not Path(SAMPLE_IMAGE).exists():
        print(f"   ❌ Image not found: {SAMPLE_IMAGE}")
        sys.exit(1)
    file_size = Path(SAMPLE_IMAGE).stat().st_size // 1024
    print(f"   ✅ Image found ({file_size}KB)")

    # Run both configurations
    baseline_results = run_pipeline("baseline", CONFIGS["baseline"])
    optimized_results = run_pipeline("optimized", CONFIGS["optimized"])

    # Compare results
    comparison = print_comparison(baseline_results, optimized_results)

    # Save results
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"integration_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    save_data = {
        "timestamp": datetime.now().isoformat(),
        "image": SAMPLE_IMAGE,
        "baseline": {
            "config": baseline_results["config"],
            "timings": baseline_results["timings"],
            "results": baseline_results["results"],
        },
        "optimized": {
            "config": optimized_results["config"],
            "timings": optimized_results["timings"],
            "results": optimized_results["results"],
        },
        "comparison": comparison,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(save_data, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n📁 Results saved: {output_file}")
    print("\n✅ Integration test completed!")


if __name__ == "__main__":
    main()
