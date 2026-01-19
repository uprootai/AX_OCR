#!/usr/bin/env python3
"""
PID2Graph Benchmark Results Analysis
Generates detailed reports from evaluation results.
"""
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List


def load_results(results_path: Path) -> Dict:
    """Load evaluation results from JSON file."""
    with open(results_path) as f:
        return json.load(f)


def generate_markdown_report(results: Dict, output_path: Path):
    """Generate a markdown report from results."""
    summary = results.get("summary", {})
    metrics = results.get("metrics", [])

    report = []
    report.append("# PID2Graph Benchmark Results")
    report.append("")
    report.append(f"> **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append(f"> **Dataset**: {results.get('dataset', 'N/A')}")
    report.append(f"> **Total Images**: {results.get('total_images', 0)}")
    report.append("")
    report.append("---")
    report.append("")

    # Summary Section
    report.append("## Summary")
    report.append("")

    if summary:
        report.append("### Overall Performance")
        report.append("")
        report.append("| Metric | Node (Symbol) | Edge (Connection) |")
        report.append("|--------|---------------|-------------------|")
        report.append(f"| **Precision** | {summary.get('avg_node_precision', 0):.1%} | {summary.get('avg_edge_precision', 0):.1%} |")
        report.append(f"| **Recall** | {summary.get('avg_node_recall', 0):.1%} | {summary.get('avg_edge_recall', 0):.1%} |")
        report.append(f"| **F1 Score** | {summary.get('avg_node_f1', 0):.1%} | {summary.get('avg_edge_f1', 0):.1%} |")
        report.append("")
        report.append(f"**Average Processing Time**: {summary.get('avg_processing_time_ms', 0):.0f}ms")
        report.append("")
    else:
        report.append("*No summary available*")
        report.append("")

    # Comparison with SOTA
    report.append("### Comparison with Relationformer (SOTA)")
    report.append("")
    report.append("| Metric | AX POC | Relationformer | Gap |")
    report.append("|--------|--------|----------------|-----|")

    node_f1 = summary.get('avg_node_f1', 0) if summary else 0
    edge_f1 = summary.get('avg_edge_f1', 0) if summary else 0
    sota_node = 0.8363  # Relationformer node AP
    sota_edge = 0.7546  # Relationformer edge mAP

    node_gap = node_f1 - sota_node
    edge_gap = edge_f1 - sota_edge

    report.append(f"| Node AP/F1 | {node_f1:.1%} | {sota_node:.1%} | {node_gap:+.1%} |")
    report.append(f"| Edge mAP/F1 | {edge_f1:.1%} | {sota_edge:.1%} | {edge_gap:+.1%} |")
    report.append("")

    # Analysis
    report.append("## Analysis")
    report.append("")

    if node_gap < -0.1:
        report.append("### Node Detection")
        report.append("")
        report.append("- ⚠️ **Gap identified**: Node detection is below SOTA by {:.1%}".format(abs(node_gap)))
        report.append("- **Possible improvements**:")
        report.append("  - Fine-tune YOLO model on PID2Graph dataset")
        report.append("  - Apply SAHI (Slicing Aided Hyper Inference) for small symbols")
        report.append("  - Add more P&ID-specific classes")
        report.append("")

    if edge_gap < -0.1:
        report.append("### Edge Detection")
        report.append("")
        report.append("- ⚠️ **Gap identified**: Edge detection is below SOTA by {:.1%}".format(abs(edge_gap)))
        report.append("- **Possible improvements**:")
        report.append("  - Improve Line Detector accuracy")
        report.append("  - Better connection point inference")
        report.append("  - Consider GNN-based post-processing")
        report.append("")

    # Per-image details (top errors)
    error_images = [m for m in metrics if m.get("error")]
    if error_images:
        report.append("### Errors")
        report.append("")
        report.append(f"**{len(error_images)} images had errors:**")
        report.append("")
        for m in error_images[:10]:
            report.append(f"- `{Path(m['image_path']).name}`: {m['error']}")
        if len(error_images) > 10:
            report.append(f"- ... and {len(error_images) - 10} more")
        report.append("")

    # Recommendations
    report.append("## Recommendations")
    report.append("")
    report.append("### Short-term (Current Pipeline)")
    report.append("")
    report.append("1. **SAHI Integration**: Apply tiled inference for small symbol detection")
    report.append("2. **Threshold Tuning**: Optimize confidence thresholds per class")
    report.append("3. **Post-processing Rules**: Add domain-specific heuristics")
    report.append("")
    report.append("### Medium-term (Architecture Updates)")
    report.append("")
    report.append("1. **RT-DETR**: Consider End-to-End detection without NMS")
    report.append("2. **GNN Post-processor**: Graph Neural Network for connection refinement")
    report.append("3. **Multi-scale Feature Fusion**: Better handle varying symbol sizes")
    report.append("")
    report.append("### Long-term (Full Upgrade)")
    report.append("")
    report.append("1. **Relationformer**: End-to-End node+edge detection (requires 8GB+ GPU)")
    report.append("2. **Custom Training**: Fine-tune on TECHCROSS domain data")
    report.append("")

    report.append("---")
    report.append("")
    report.append("*Generated by AX POC PID2Graph Benchmark*")

    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write("\n".join(report))

    print(f"✅ Report saved to: {output_path}")
    return "\n".join(report)


def print_quick_stats(results: Dict):
    """Print quick statistics to console."""
    summary = results.get("summary", {})

    print("\n" + "=" * 50)
    print("QUICK STATS")
    print("=" * 50)

    if summary:
        print(f"\n📊 Node Detection F1: {summary.get('avg_node_f1', 0):.1%}")
        print(f"📊 Edge Detection F1: {summary.get('avg_edge_f1', 0):.1%}")
        print(f"⏱️  Avg Processing: {summary.get('avg_processing_time_ms', 0):.0f}ms")

        # SOTA comparison
        sota_node = 0.8363
        sota_edge = 0.7546
        node_f1 = summary.get('avg_node_f1', 0)
        edge_f1 = summary.get('avg_edge_f1', 0)

        print(f"\n🎯 vs SOTA (Relationformer):")
        print(f"   Node: {(node_f1 - sota_node) / sota_node:+.1%} relative")
        print(f"   Edge: {(edge_f1 - sota_edge) / sota_edge:+.1%} relative")
    else:
        print("No summary available")


def main():
    parser = argparse.ArgumentParser(description="Analyze PID2Graph evaluation results")
    parser.add_argument("--results", type=str, required=True, help="Results JSON file")
    parser.add_argument("--report", type=str, help="Output report path (markdown)")
    args = parser.parse_args()

    results_path = Path(args.results)
    if not results_path.exists():
        print(f"❌ Results file not found: {results_path}")
        return

    results = load_results(results_path)
    print_quick_stats(results)

    if args.report:
        report_path = Path(args.report)
        generate_markdown_report(results, report_path)


if __name__ == "__main__":
    main()
