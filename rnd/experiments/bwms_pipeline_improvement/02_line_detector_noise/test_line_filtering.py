#!/usr/bin/env python3
"""
Line Detector Noise Filtering Test
===================================
BWMS P&ID 도면에서 다양한 min_length 설정으로 라인 검출 결과를 비교합니다.

테스트 설정:
- Baseline: min_length=0 (현재, 필터링 없음)
- Test A: min_length=30
- Test B: min_length=50
- Test C: min_length=80
- Test D: min_length=100

평가 지표:
- 총 라인 수
- 스타일별 라인 수 (solid, dashed, dotted 등)
- 총 교차점 수
- 평균 라인 길이
- 처리 시간
"""

import requests
import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Configuration
LINE_DETECTOR_URL = "http://localhost:5016/api/v1/process"
SAMPLE_IMAGE = "/home/uproot/ax/poc/web-ui/public/samples/bwms_pid_sample.png"
OUTPUT_DIR = Path("/home/uproot/ax/poc/rnd/experiments/bwms_pipeline_improvement/results")

# Test configurations
TEST_CONFIGS = [
    {"name": "Baseline", "min_length": 0, "description": "필터링 없음 (현재)"},
    {"name": "Test_A", "min_length": 30, "description": "최소 30px"},
    {"name": "Test_B", "min_length": 50, "description": "최소 50px (권장)"},
    {"name": "Test_C", "min_length": 80, "description": "최소 80px"},
    {"name": "Test_D", "min_length": 100, "description": "최소 100px (보수적)"},
]

# Common parameters
COMMON_PARAMS = {
    "method": "lsd",
    "merge_lines": "true",
    "classify_types": "true",
    "classify_colors": "true",
    "classify_styles": "true",
    "find_intersections": "true",
    "detect_regions": "false",
    "visualize": "false",  # 시각화 비활성화로 속도 향상
}


def run_line_detection(image_path: str, min_length: int) -> dict:
    """Run Line Detector with specified min_length."""
    with open(image_path, "rb") as f:
        files = {"file": (Path(image_path).name, f, "image/png")}
        data = {
            **COMMON_PARAMS,
            "min_length": str(min_length),
        }

        response = requests.post(LINE_DETECTOR_URL, files=files, data=data, timeout=120)
        response.raise_for_status()
        return response.json()


def analyze_results(response: dict) -> dict:
    """Analyze line detection results and compute metrics."""
    data = response.get("data", response)
    lines = data.get("lines", [])
    intersections = data.get("intersections", [])
    statistics = data.get("statistics", {})
    processing_time = response.get("processing_time", data.get("processing_time", 0))

    if not lines:
        return {
            "total_lines": 0,
            "total_intersections": 0,
            "by_style": {},
            "by_type": {},
            "by_color": {},
            "avg_length": 0,
            "min_length": 0,
            "max_length": 0,
            "length_distribution": {},
            "processing_time": processing_time,
        }

    # Calculate line lengths
    lengths = []
    for line in lines:
        # Support both [x1, y1, x2, y2] and {start: [x1, y1], end: [x2, y2]} formats
        if isinstance(line, dict):
            if "start" in line and "end" in line:
                x1, y1 = line["start"]
                x2, y2 = line["end"]
            elif "x1" in line:
                x1, y1, x2, y2 = line["x1"], line["y1"], line["x2"], line["y2"]
            else:
                continue
        elif isinstance(line, (list, tuple)) and len(line) >= 4:
            x1, y1, x2, y2 = line[:4]
        else:
            continue

        length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        lengths.append(length)

    # Style distribution
    style_counts = defaultdict(int)
    type_counts = defaultdict(int)
    color_counts = defaultdict(int)

    for line in lines:
        if isinstance(line, dict):
            style = line.get("style", "unknown")
            line_type = line.get("type", line.get("usage", "unknown"))
            color = line.get("color", "unknown")
            style_counts[style] += 1
            type_counts[line_type] += 1
            color_counts[color] += 1

    # Length distribution
    distribution = {
        "0-30px": sum(1 for l in lengths if l < 30),
        "30-50px": sum(1 for l in lengths if 30 <= l < 50),
        "50-80px": sum(1 for l in lengths if 50 <= l < 80),
        "80-100px": sum(1 for l in lengths if 80 <= l < 100),
        "100-200px": sum(1 for l in lengths if 100 <= l < 200),
        "200-500px": sum(1 for l in lengths if 200 <= l < 500),
        ">500px": sum(1 for l in lengths if l >= 500),
    }

    return {
        "total_lines": len(lines),
        "total_intersections": len(intersections),
        "by_style": dict(style_counts) if style_counts else statistics.get("by_style", {}),
        "by_type": dict(type_counts),
        "by_color": dict(color_counts) if color_counts else statistics.get("by_color", {}),
        "avg_length": round(sum(lengths) / len(lengths), 1) if lengths else 0,
        "min_length": round(min(lengths), 1) if lengths else 0,
        "max_length": round(max(lengths), 1) if lengths else 0,
        "length_distribution": distribution,
        "processing_time": processing_time,
    }


def print_results(config: dict, analysis: dict):
    """Print formatted results."""
    print(f"\n{'='*60}")
    print(f"🔬 {config['name']}: min_length={config['min_length']} ({config['description']})")
    print(f"{'='*60}")

    print(f"\n📊 총 라인: {analysis['total_lines']}개")
    print(f"   총 교차점: {analysis['total_intersections']}개")
    print(f"   처리 시간: {analysis['processing_time']:.2f}초")

    print(f"\n📏 라인 길이:")
    print(f"   평균: {analysis['avg_length']}px")
    print(f"   최소: {analysis['min_length']}px")
    print(f"   최대: {analysis['max_length']}px")

    print(f"\n📈 길이 분포:")
    for range_name, count in analysis['length_distribution'].items():
        bar = "█" * (count // 20)
        pct = count / max(1, analysis['total_lines']) * 100
        print(f"   {range_name:>10}: {count:4}개 ({pct:5.1f}%) {bar}")

    if analysis['by_style']:
        print(f"\n🎨 스타일별:")
        for style, count in sorted(analysis['by_style'].items(), key=lambda x: -x[1]):
            pct = count / max(1, analysis['total_lines']) * 100
            print(f"   {style:>12}: {count:4}개 ({pct:5.1f}%)")

    if analysis['by_type']:
        print(f"\n🏷️  타입별:")
        for line_type, count in sorted(analysis['by_type'].items(), key=lambda x: -x[1])[:5]:
            pct = count / max(1, analysis['total_lines']) * 100
            print(f"   {line_type:>12}: {count:4}개 ({pct:5.1f}%)")


def main():
    print("=" * 60)
    print("🔬 Line Detector Noise Filtering Test")
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
        print(f"\n🚀 Running {config['name']} (min_length={config['min_length']})...")
        try:
            response = run_line_detection(SAMPLE_IMAGE, config['min_length'])
            analysis = analyze_results(response)

            results.append({
                "config": config,
                "analysis": analysis,
            })

            print_results(config, analysis)

        except requests.exceptions.RequestException as e:
            print(f"   ❌ API Error: {e}")
            continue

    if not results:
        print("\n❌ All tests failed!")
        sys.exit(1)

    # Summary comparison
    print("\n" + "=" * 60)
    print("📊 SUMMARY COMPARISON")
    print("=" * 60)
    print(f"\n{'Config':<12} {'MinLen':>6} {'Lines':>7} {'Intersect':>9} {'AvgLen':>7} {'Time':>6}")
    print("-" * 54)

    baseline_lines = results[0]['analysis']['total_lines'] if results else 0

    for r in results:
        c = r['config']
        a = r['analysis']
        reduction = (1 - a['total_lines'] / max(1, baseline_lines)) * 100 if baseline_lines else 0
        print(f"{c['name']:<12} {c['min_length']:>6} {a['total_lines']:>7} {a['total_intersections']:>9} {a['avg_length']:>7.1f} {a['processing_time']:>5.2f}s")

    # Noise analysis
    print("\n" + "=" * 60)
    print("🔍 NOISE ANALYSIS")
    print("=" * 60)

    if results:
        baseline = results[0]['analysis']
        print(f"\n📊 Baseline (min_length=0):")
        print(f"   총 라인: {baseline['total_lines']}개")
        short_lines = baseline['length_distribution'].get('0-30px', 0) + baseline['length_distribution'].get('30-50px', 0)
        print(f"   짧은 라인 (<50px): {short_lines}개 ({short_lines/max(1,baseline['total_lines'])*100:.1f}%)")

        # Find best setting
        for r in results[1:]:
            if r['config']['min_length'] == 50:
                test = r['analysis']
                removed = baseline['total_lines'] - test['total_lines']
                print(f"\n✅ min_length=50 권장:")
                print(f"   - 총 라인: {baseline['total_lines']} → {test['total_lines']} ({removed}개 제거, {removed/max(1,baseline['total_lines'])*100:.1f}%)")
                print(f"   - 교차점: {baseline['total_intersections']} → {test['total_intersections']}")
                print(f"   - 평균 길이: {baseline['avg_length']}px → {test['avg_length']}px")

    # Save results
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"line_detector_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n📁 Results saved: {output_file}")
    print("\n✅ Test completed!")


if __name__ == "__main__":
    main()
