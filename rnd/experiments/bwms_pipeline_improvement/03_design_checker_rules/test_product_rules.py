#!/usr/bin/env python3
"""
Design Checker BWMS Rules Test
==============================
BWMS P&ID 도면에서 제품별(ECS/HYCHLOR/AUTO) 규칙 적용 결과를 비교합니다.

테스트 설정:
- Baseline: product_type=AUTO (현재)
- Test A: product_type=ECS
- Test B: product_type=HYCHLOR

평가 지표:
- 적용된 규칙 수
- 카테고리별 위반 사항
- 심각도별 위반 사항
- 규정 준수율 (compliance_score)
"""

import requests
import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Configuration
DESIGN_CHECKER_URL = "http://localhost:5019/api/v1/pipeline/validate"
SAMPLE_IMAGE = "/home/uproot/ax/poc/web-ui/public/samples/bwms_pid_sample.png"
OUTPUT_DIR = Path("/home/uproot/ax/poc/rnd/experiments/bwms_pipeline_improvement/results")

# Test configurations
TEST_CONFIGS = [
    {"name": "AUTO", "product_type": "AUTO", "description": "자동 감지 (현재)"},
    {"name": "ECS", "product_type": "ECS", "description": "ECS 전용 규칙"},
    {"name": "HYCHLOR", "product_type": "HYCHLOR", "description": "HYCHLOR 전용 규칙"},
]

# Common parameters
COMMON_PARAMS = {
    "model_type": "pid_class_aware",
    "confidence": "0.25",
    "use_ocr": "true",
    "ocr_source": "edocr2",
}


def run_validation(image_path: str, product_type: str) -> dict:
    """Run Design Checker validation with specified product type."""
    with open(image_path, "rb") as f:
        files = {"file": (Path(image_path).name, f, "image/png")}
        data = {
            **COMMON_PARAMS,
            "product_type": product_type,
        }

        response = requests.post(DESIGN_CHECKER_URL, files=files, data=data, timeout=180)
        response.raise_for_status()
        return response.json()


def analyze_results(response: dict) -> dict:
    """Analyze validation results and compute metrics."""
    data = response.get("data", response)
    validation = data.get("validation", {})
    summary = data.get("summary", validation.get("summary", {}))
    violations = validation.get("violations", [])
    rules_applied = validation.get("rules_applied", [])
    processing_time = response.get("processing_time", data.get("processing_time", 0))

    # YOLO stats
    yolo = data.get("yolo", {})
    yolo_detections = yolo.get("total_detections", 0)
    yolo_class_counts = yolo.get("class_counts", {})

    # Violation analysis
    by_severity = defaultdict(int)
    by_category = defaultdict(int)
    by_rule = defaultdict(int)

    for v in violations:
        severity = v.get("severity", "unknown")
        category = v.get("category", "unknown")
        rule_id = v.get("rule_id", "unknown")
        by_severity[severity] += 1
        by_category[category] += 1
        by_rule[rule_id] += 1

    return {
        "yolo_detections": yolo_detections,
        "yolo_class_counts": yolo_class_counts,
        "rules_applied": len(rules_applied) if isinstance(rules_applied, list) else rules_applied,
        "total_violations": len(violations),
        "violations_by_severity": dict(by_severity),
        "violations_by_category": dict(by_category),
        "violations_by_rule": dict(by_rule),
        "compliance_score": summary.get("compliance_score", 0),
        "total_rules": summary.get("total_rules", 0),
        "passed_rules": summary.get("passed", 0),
        "failed_rules": summary.get("failed", 0),
        "processing_time": processing_time,
        "violations_detail": violations[:10],  # Top 10 violations for details
    }


def print_results(config: dict, analysis: dict):
    """Print formatted results."""
    print(f"\n{'='*60}")
    print(f"🔬 {config['name']}: product_type={config['product_type']} ({config['description']})")
    print(f"{'='*60}")

    print(f"\n📊 YOLO 검출: {analysis['yolo_detections']}개")
    if analysis['yolo_class_counts']:
        top_classes = sorted(analysis['yolo_class_counts'].items(), key=lambda x: -x[1])[:5]
        for cls, count in top_classes:
            print(f"   - {cls}: {count}개")

    print(f"\n📋 규칙 검사:")
    print(f"   적용된 규칙: {analysis['rules_applied']}개")
    print(f"   총 규칙: {analysis['total_rules']}개")
    print(f"   통과: {analysis['passed_rules']}개")
    print(f"   실패: {analysis['failed_rules']}개")
    print(f"   준수율: {analysis['compliance_score']:.1f}%")

    print(f"\n⚠️  위반 사항: {analysis['total_violations']}개")

    if analysis['violations_by_severity']:
        print(f"\n   심각도별:")
        for severity, count in sorted(analysis['violations_by_severity'].items()):
            icon = "❌" if severity == "error" else "⚠️" if severity == "warning" else "ℹ️"
            print(f"   {icon} {severity}: {count}개")

    if analysis['violations_by_category']:
        print(f"\n   카테고리별:")
        for category, count in sorted(analysis['violations_by_category'].items(), key=lambda x: -x[1])[:5]:
            print(f"      {category}: {count}개")

    if analysis['violations_detail']:
        print(f"\n   주요 위반 사항 (상위 5개):")
        for i, v in enumerate(analysis['violations_detail'][:5], 1):
            severity = v.get("severity", "unknown")
            rule_id = v.get("rule_id", "unknown")
            message = v.get("message", v.get("description", ""))[:50]
            icon = "❌" if severity == "error" else "⚠️" if severity == "warning" else "ℹ️"
            print(f"   {i}. {icon} [{rule_id}] {message}...")

    print(f"\n⏱️  처리 시간: {analysis['processing_time']:.2f}초")


def main():
    print("=" * 60)
    print("🔬 Design Checker BWMS Rules Test")
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
        print(f"\n🚀 Running {config['name']} (product_type={config['product_type']})...")
        try:
            response = run_validation(SAMPLE_IMAGE, config['product_type'])
            analysis = analyze_results(response)

            results.append({
                "config": config,
                "analysis": analysis,
            })

            print_results(config, analysis)

        except requests.exceptions.RequestException as e:
            print(f"   ❌ API Error: {e}")
            continue
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            continue

    if not results:
        print("\n❌ All tests failed!")
        sys.exit(1)

    # Summary comparison
    print("\n" + "=" * 60)
    print("📊 SUMMARY COMPARISON")
    print("=" * 60)
    print(f"\n{'Config':<10} {'Rules':>6} {'Passed':>7} {'Failed':>7} {'Score':>7} {'Time':>6}")
    print("-" * 50)

    for r in results:
        c = r['config']
        a = r['analysis']
        print(f"{c['name']:<10} {a['total_rules']:>6} {a['passed_rules']:>7} {a['failed_rules']:>7} {a['compliance_score']:>6.1f}% {a['processing_time']:>5.1f}s")

    # Rules comparison
    print("\n" + "=" * 60)
    print("📋 RULES COMPARISON")
    print("=" * 60)

    if len(results) >= 2:
        auto_result = next((r for r in results if r['config']['product_type'] == 'AUTO'), None)
        ecs_result = next((r for r in results if r['config']['product_type'] == 'ECS'), None)
        hychlor_result = next((r for r in results if r['config']['product_type'] == 'HYCHLOR'), None)

        if auto_result and ecs_result:
            auto = auto_result['analysis']
            ecs = ecs_result['analysis']
            print(f"\n🔄 AUTO vs ECS:")
            print(f"   규칙 수: {auto['total_rules']} vs {ecs['total_rules']} ({ecs['total_rules'] - auto['total_rules']:+d})")
            print(f"   위반 수: {auto['total_violations']} vs {ecs['total_violations']} ({ecs['total_violations'] - auto['total_violations']:+d})")
            print(f"   준수율: {auto['compliance_score']:.1f}% vs {ecs['compliance_score']:.1f}%")

        if auto_result and hychlor_result:
            auto = auto_result['analysis']
            hychlor = hychlor_result['analysis']
            print(f"\n🔄 AUTO vs HYCHLOR:")
            print(f"   규칙 수: {auto['total_rules']} vs {hychlor['total_rules']} ({hychlor['total_rules'] - auto['total_rules']:+d})")
            print(f"   위반 수: {auto['total_violations']} vs {hychlor['total_violations']} ({hychlor['total_violations'] - auto['total_violations']:+d})")
            print(f"   준수율: {auto['compliance_score']:.1f}% vs {hychlor['compliance_score']:.1f}%")

    # Recommendation
    print("\n" + "=" * 60)
    print("💡 RECOMMENDATION")
    print("=" * 60)

    if results:
        # Find best product type based on rule coverage
        best = max(results, key=lambda r: r['analysis']['total_rules'])
        print(f"\n✅ 권장 설정: product_type={best['config']['product_type']}")
        print(f"   - 적용 규칙: {best['analysis']['total_rules']}개")
        print(f"   - 위반 사항: {best['analysis']['total_violations']}개")
        print(f"   - 규정 준수율: {best['analysis']['compliance_score']:.1f}%")

    # Save results
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"design_checker_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        # Clean up for JSON serialization
        save_results = []
        for r in results:
            save_results.append({
                "config": r['config'],
                "analysis": {k: v for k, v in r['analysis'].items() if k != 'violations_detail'}
            })
        json.dump(save_results, f, indent=2, ensure_ascii=False)

    print(f"\n📁 Results saved: {output_file}")
    print("\n✅ Test completed!")


if __name__ == "__main__":
    main()
