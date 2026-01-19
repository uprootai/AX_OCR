#!/usr/bin/env python3
"""
PID2Graph Benchmark Evaluation Script
Evaluates the current AX POC P&ID pipeline against PID2Graph dataset.

주요 기능:
- 공통 bbox 유틸리티 사용 (models/shared/bbox_utils.py)
- Class-agnostic 평가 지원
- SAHI 슬라이싱 지원
- 다양한 모델 타입 선택 가능
"""
import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

import requests
import networkx as nx

# 공통 유틸리티 import
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))
from models.shared.bbox_utils import (
    normalize_bbox,
    calculate_iou,
    match_boxes,
    calculate_metrics,
    convert_yolo_detections,
)

# API Endpoints (AX POC)
YOLO_API = os.getenv("YOLO_API", "http://localhost:5005")
LINE_DETECTOR_API = os.getenv("LINE_DETECTOR_API", "http://localhost:5016")
PID_ANALYZER_API = os.getenv("PID_ANALYZER_API", "http://localhost:5018")


@dataclass
class EvalMetrics:
    """Evaluation metrics for a single image."""
    image_path: str
    # Node (Symbol) Detection
    node_tp: int = 0
    node_fp: int = 0
    node_fn: int = 0
    node_precision: float = 0.0
    node_recall: float = 0.0
    node_f1: float = 0.0
    # Edge (Connection) Detection
    edge_tp: int = 0
    edge_fp: int = 0
    edge_fn: int = 0
    edge_precision: float = 0.0
    edge_recall: float = 0.0
    edge_f1: float = 0.0
    # Processing
    processing_time_ms: float = 0.0
    yolo_detections: int = 0
    gt_nodes: int = 0
    error: str = None


def load_graphml(graphml_path: Path) -> nx.Graph:
    """Load ground truth graph from GraphML file."""
    try:
        G = nx.read_graphml(graphml_path)
        print(f"  Loaded graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        return G
    except Exception as e:
        print(f"  Error loading graphml: {e}")
        return None


def extract_ground_truth(G: nx.Graph) -> Tuple[List[Dict], List[Tuple]]:
    """Extract nodes and edges from ground truth graph."""
    nodes = []
    for node_id, attrs in G.nodes(data=True):
        # GT는 이미 xyxy 형식 (xmin, ymin, xmax, ymax)
        node_data = {
            "id": node_id,
            "label": attrs.get("label", "unknown"),
            "bbox": {
                "xmin": float(attrs.get("xmin", 0)),
                "ymin": float(attrs.get("ymin", 0)),
                "xmax": float(attrs.get("xmax", 0)),
                "ymax": float(attrs.get("ymax", 0)),
            }
        }
        nodes.append(node_data)

    edges = []
    for src, dst, attrs in G.edges(data=True):
        edge_data = (src, dst, attrs.get("label", "connection"))
        edges.append(edge_data)

    return nodes, edges


def call_yolo_api(
    image_path: Path,
    model_type: str = "pid_class_agnostic",
    confidence: float = 0.2,
    use_sahi: bool = False,
    sahi_slice_size: int = 512,
    sahi_overlap: float = 0.25
) -> Dict:
    """
    Call YOLO API for symbol detection.

    Args:
        image_path: 이미지 경로
        model_type: 모델 타입 (pid_class_agnostic, pid_class_aware, pid_symbol)
        confidence: 신뢰도 임계값
        use_sahi: SAHI 슬라이싱 사용 여부
        sahi_slice_size: SAHI 슬라이스 크기
        sahi_overlap: SAHI 오버랩 비율
    """
    url = f"{YOLO_API}/api/v1/detect"

    with open(image_path, "rb") as f:
        files = {"file": (image_path.name, f, "image/png")}
        data = {
            "model_type": model_type,
            "confidence": confidence,
        }

        # SAHI 옵션
        if use_sahi:
            data["use_sahi"] = "true"
            data["slice_size"] = sahi_slice_size
            data["overlap_ratio"] = sahi_overlap

        response = requests.post(url, files=files, data=data, timeout=120)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"YOLO API error: {response.status_code} - {response.text}")


def call_line_detector_api(image_path: Path, min_length: int = 20) -> Dict:
    """Call Line Detector API."""
    url = f"{LINE_DETECTOR_API}/api/v1/detect"
    with open(image_path, "rb") as f:
        files = {"file": (image_path.name, f, "image/png")}
        data = {"min_length": min_length}
        response = requests.post(url, files=files, data=data, timeout=60)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Line Detector API error: {response.status_code}")


def call_pid_analyzer_api(image_path: Path, symbols: List, lines: List) -> Dict:
    """Call PID Analyzer API for connection analysis."""
    url = f"{PID_ANALYZER_API}/api/v1/analyze"
    payload = {
        "symbols": symbols,
        "lines": lines,
        "analyze_connections": True
    }
    with open(image_path, "rb") as f:
        files = {"file": (image_path.name, f, "image/png")}
        response = requests.post(url, files=files, data={"config": json.dumps(payload)}, timeout=60)
    if response.status_code == 200:
        return response.json()
    else:
        return {"connections": [], "graph": None}


def run_ax_poc_pipeline(
    image_path: Path,
    model_type: str = "pid_class_agnostic",
    confidence: float = 0.2,
    use_sahi: bool = False,
    sahi_slice_size: int = 512,
    sahi_overlap: float = 0.25,
    skip_line_detector: bool = False,
    skip_pid_analyzer: bool = True
) -> Tuple[List[Dict], List[Tuple], float, int]:
    """
    Run the full AX POC pipeline on an image.

    Returns:
        (pred_nodes, pred_edges, processing_time, num_detections)
    """
    import time
    start_time = time.time()

    # Step 1: YOLO Symbol Detection
    print(f"  Running YOLO detection (model={model_type}, conf={confidence}, sahi={use_sahi})...")
    try:
        yolo_result = call_yolo_api(
            image_path,
            model_type=model_type,
            confidence=confidence,
            use_sahi=use_sahi,
            sahi_slice_size=sahi_slice_size,
            sahi_overlap=sahi_overlap
        )
        detections = yolo_result.get("detections", [])
        print(f"    Found {len(detections)} symbols")
    except Exception as e:
        print(f"    YOLO error: {e}")
        detections = []

    # Step 2: Line Detection (optional)
    lines = []
    if not skip_line_detector:
        print(f"  Running Line detection...")
        try:
            line_result = call_line_detector_api(image_path)
            lines = line_result.get("lines", [])
            print(f"    Found {len(lines)} lines")
        except Exception as e:
            print(f"    Line Detector error: {e}")

    # Step 3: PID Analysis (optional)
    connections = []
    if not skip_pid_analyzer:
        print(f"  Running PID analysis...")
        try:
            pid_result = call_pid_analyzer_api(image_path, detections, lines)
            connections = pid_result.get("connections", [])
            print(f"    Found {len(connections)} connections")
        except Exception as e:
            print(f"    PID Analyzer error: {e}")

    # Convert detections to standard format with xyxy bbox
    # YOLO는 xywh 형식으로 반환하므로 xyxy로 변환
    pred_nodes = []
    for det in detections:
        # bbox 정규화 (xywh -> xyxy)
        bbox = det.get("bbox", {})
        bbox_xyxy = normalize_bbox(bbox, "xyxy")

        node = {
            "id": det.get("id", str(len(pred_nodes))),
            "label": det.get("class_name", det.get("label", "symbol")),
            "bbox": bbox_xyxy,
            "confidence": det.get("confidence", 0)
        }
        pred_nodes.append(node)

    pred_edges = []
    for conn in connections:
        edge = (
            conn.get("source", conn.get("from", "")),
            conn.get("target", conn.get("to", "")),
            conn.get("type", "connection")
        )
        pred_edges.append(edge)

    processing_time = (time.time() - start_time) * 1000  # ms
    return pred_nodes, pred_edges, processing_time, len(detections)


def match_nodes(
    pred_nodes: List[Dict],
    gt_nodes: List[Dict],
    iou_threshold: float = 0.5,
    class_agnostic: bool = True
) -> Tuple[int, int, int]:
    """
    Match predicted nodes to ground truth nodes using shared utility.
    """
    tp, fp, fn, _ = match_boxes(
        pred_nodes,
        gt_nodes,
        iou_threshold=iou_threshold,
        class_agnostic=class_agnostic
    )
    return tp, fp, fn


def match_edges(pred_edges: List[Tuple], gt_edges: List[Tuple]) -> Tuple[int, int, int]:
    """Match predicted edges to ground truth edges."""
    pred_set = set()
    for e in pred_edges:
        if len(e) >= 2:
            pred_set.add(frozenset([str(e[0]), str(e[1])]))

    gt_set = set()
    for e in gt_edges:
        if len(e) >= 2:
            gt_set.add(frozenset([str(e[0]), str(e[1])]))

    tp = len(pred_set & gt_set)
    fp = len(pred_set - gt_set)
    fn = len(gt_set - pred_set)

    return tp, fp, fn


def evaluate_image(
    image_path: Path,
    graphml_path: Path,
    model_type: str = "pid_class_agnostic",
    confidence: float = 0.2,
    iou_threshold: float = 0.5,
    use_sahi: bool = False,
    sahi_slice_size: int = 512,
    class_agnostic: bool = True
) -> EvalMetrics:
    """Evaluate a single image against ground truth."""
    metrics = EvalMetrics(image_path=str(image_path))

    # Load ground truth
    G = load_graphml(graphml_path)
    if G is None:
        metrics.error = "Failed to load ground truth"
        return metrics

    gt_nodes, gt_edges = extract_ground_truth(G)
    metrics.gt_nodes = len(gt_nodes)
    print(f"  Ground truth: {len(gt_nodes)} nodes, {len(gt_edges)} edges")

    # Run pipeline
    try:
        pred_nodes, pred_edges, processing_time, num_detections = run_ax_poc_pipeline(
            image_path,
            model_type=model_type,
            confidence=confidence,
            use_sahi=use_sahi,
            sahi_slice_size=sahi_slice_size
        )
        metrics.processing_time_ms = processing_time
        metrics.yolo_detections = num_detections
    except Exception as e:
        metrics.error = str(e)
        return metrics

    # Calculate node metrics
    metrics.node_tp, metrics.node_fp, metrics.node_fn = match_nodes(
        pred_nodes, gt_nodes, iou_threshold=iou_threshold, class_agnostic=class_agnostic
    )
    metrics.node_precision, metrics.node_recall, metrics.node_f1 = calculate_metrics(
        metrics.node_tp, metrics.node_fp, metrics.node_fn
    )

    # Calculate edge metrics
    metrics.edge_tp, metrics.edge_fp, metrics.edge_fn = match_edges(pred_edges, gt_edges)
    metrics.edge_precision, metrics.edge_recall, metrics.edge_f1 = calculate_metrics(
        metrics.edge_tp, metrics.edge_fp, metrics.edge_fn
    )

    return metrics


def find_image_graphml_pairs(data_dir: Path) -> List[Tuple[Path, Path]]:
    """Find matching image and graphml file pairs."""
    pairs = []

    for img_path in data_dir.rglob("*.png"):
        graphml_path = img_path.with_suffix(".graphml")
        if graphml_path.exists():
            pairs.append((img_path, graphml_path))

    for img_path in data_dir.rglob("*.jpg"):
        graphml_path = img_path.with_suffix(".graphml")
        if graphml_path.exists():
            pairs.append((img_path, graphml_path))

    print(f"Found {len(pairs)} image-graphml pairs")
    return pairs


def evaluate_dataset(
    data_dir: Path,
    output_path: Path,
    model_type: str = "pid_class_agnostic",
    confidence: float = 0.2,
    iou_threshold: float = 0.5,
    use_sahi: bool = False,
    sahi_slice_size: int = 512,
    class_agnostic: bool = True,
    limit: int = None
):
    """Evaluate the full dataset."""
    pairs = find_image_graphml_pairs(data_dir)

    if limit:
        pairs = pairs[:limit]
        print(f"Limiting to {limit} images")

    results = {
        "timestamp": datetime.now().isoformat(),
        "dataset": str(data_dir),
        "config": {
            "model_type": model_type,
            "confidence": confidence,
            "iou_threshold": iou_threshold,
            "use_sahi": use_sahi,
            "sahi_slice_size": sahi_slice_size,
            "class_agnostic": class_agnostic
        },
        "total_images": len(pairs),
        "metrics": [],
        "summary": {}
    }

    all_metrics = []
    for i, (img_path, graphml_path) in enumerate(pairs):
        print(f"\n[{i+1}/{len(pairs)}] Evaluating: {img_path.name}")
        metrics = evaluate_image(
            img_path,
            graphml_path,
            model_type=model_type,
            confidence=confidence,
            iou_threshold=iou_threshold,
            use_sahi=use_sahi,
            sahi_slice_size=sahi_slice_size,
            class_agnostic=class_agnostic
        )
        all_metrics.append(metrics)
        results["metrics"].append(asdict(metrics))

        # Print intermediate results
        if metrics.error:
            print(f"  ❌ Error: {metrics.error}")
        else:
            print(f"  YOLO: {metrics.yolo_detections} detections, GT: {metrics.gt_nodes} nodes")
            print(f"  Node: TP={metrics.node_tp} FP={metrics.node_fp} FN={metrics.node_fn}")
            print(f"  Node: P={metrics.node_precision:.2%} R={metrics.node_recall:.2%} F1={metrics.node_f1:.2%}")
            print(f"  Edge: P={metrics.edge_precision:.2%} R={metrics.edge_recall:.2%} F1={metrics.edge_f1:.2%}")

    # Calculate summary
    valid_metrics = [m for m in all_metrics if m.error is None]
    if valid_metrics:
        results["summary"] = {
            "total_evaluated": len(valid_metrics),
            "total_yolo_detections": sum(m.yolo_detections for m in valid_metrics),
            "total_gt_nodes": sum(m.gt_nodes for m in valid_metrics),
            "total_node_tp": sum(m.node_tp for m in valid_metrics),
            "total_node_fp": sum(m.node_fp for m in valid_metrics),
            "total_node_fn": sum(m.node_fn for m in valid_metrics),
            "avg_node_precision": sum(m.node_precision for m in valid_metrics) / len(valid_metrics),
            "avg_node_recall": sum(m.node_recall for m in valid_metrics) / len(valid_metrics),
            "avg_node_f1": sum(m.node_f1 for m in valid_metrics) / len(valid_metrics),
            "avg_edge_precision": sum(m.edge_precision for m in valid_metrics) / len(valid_metrics),
            "avg_edge_recall": sum(m.edge_recall for m in valid_metrics) / len(valid_metrics),
            "avg_edge_f1": sum(m.edge_f1 for m in valid_metrics) / len(valid_metrics),
            "avg_processing_time_ms": sum(m.processing_time_ms for m in valid_metrics) / len(valid_metrics),
        }

        # Micro-averaged metrics (전체 TP/FP/FN 기반)
        total_tp = results["summary"]["total_node_tp"]
        total_fp = results["summary"]["total_node_fp"]
        total_fn = results["summary"]["total_node_fn"]
        micro_p, micro_r, micro_f1 = calculate_metrics(total_tp, total_fp, total_fn)
        results["summary"]["micro_node_precision"] = micro_p
        results["summary"]["micro_node_recall"] = micro_r
        results["summary"]["micro_node_f1"] = micro_f1

    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n✅ Results saved to: {output_path}")

    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Config: model={model_type}, conf={confidence}, iou_thresh={iou_threshold}, sahi={use_sahi}")
    print("=" * 70)
    if results["summary"]:
        s = results["summary"]
        print(f"Images evaluated: {s['total_evaluated']}")
        print(f"Total YOLO detections: {s['total_yolo_detections']}")
        print(f"Total GT nodes: {s['total_gt_nodes']}")
        print(f"\nNode (Symbol) Detection - Macro Averaged:")
        print(f"  Precision: {s['avg_node_precision']:.2%}")
        print(f"  Recall:    {s['avg_node_recall']:.2%}")
        print(f"  F1 Score:  {s['avg_node_f1']:.2%}")
        print(f"\nNode (Symbol) Detection - Micro Averaged (Overall):")
        print(f"  TP: {s['total_node_tp']}, FP: {s['total_node_fp']}, FN: {s['total_node_fn']}")
        print(f"  Precision: {s['micro_node_precision']:.2%}")
        print(f"  Recall:    {s['micro_node_recall']:.2%}")
        print(f"  F1 Score:  {s['micro_node_f1']:.2%}")
        print(f"\nEdge (Connection) Detection:")
        print(f"  Precision: {s['avg_edge_precision']:.2%}")
        print(f"  Recall:    {s['avg_edge_recall']:.2%}")
        print(f"  F1 Score:  {s['avg_edge_f1']:.2%}")
        print(f"\nProcessing Time: {s['avg_processing_time_ms']:.0f}ms avg")

    return results


def main():
    parser = argparse.ArgumentParser(description="Evaluate AX POC against PID2Graph")
    parser.add_argument("--data_dir", type=str, default="data", help="Dataset directory")
    parser.add_argument("--output", type=str, default="results/evaluation.json", help="Output file")
    parser.add_argument("--image", type=str, help="Evaluate single image")
    parser.add_argument("--limit", type=int, help="Limit number of images")

    # Model options
    parser.add_argument("--model", type=str, default="pid_class_agnostic",
                        choices=["pid_class_agnostic", "pid_class_aware", "pid_symbol"],
                        help="YOLO model type")
    parser.add_argument("--confidence", type=float, default=0.2, help="Confidence threshold")
    parser.add_argument("--iou_threshold", type=float, default=0.5, help="IoU threshold for matching")

    # SAHI options
    parser.add_argument("--sahi", action="store_true", help="Enable SAHI slicing")
    parser.add_argument("--sahi_slice_size", type=int, default=512, help="SAHI slice size")

    # Evaluation options
    parser.add_argument("--class_aware", action="store_true",
                        help="Enable class-aware matching (default: class-agnostic)")

    args = parser.parse_args()

    script_dir = Path(__file__).parent.parent
    data_dir = script_dir / args.data_dir
    output_path = script_dir / args.output

    print("=" * 70)
    print("PID2Graph Benchmark Evaluation (v2 - with shared bbox utilities)")
    print("=" * 70)
    print(f"Data directory: {data_dir}")
    print(f"Output: {output_path}")
    print(f"Model: {args.model}")
    print(f"Confidence: {args.confidence}")
    print(f"IoU Threshold: {args.iou_threshold}")
    print(f"SAHI: {args.sahi} (slice_size={args.sahi_slice_size})")
    print(f"Class-agnostic: {not args.class_aware}")
    print(f"YOLO API: {YOLO_API}")
    print(f"Line Detector API: {LINE_DETECTOR_API}")
    print(f"PID Analyzer API: {PID_ANALYZER_API}")
    print("=" * 70)

    if args.image:
        # Single image evaluation
        img_path = Path(args.image)
        graphml_path = img_path.with_suffix(".graphml")
        if not graphml_path.exists():
            print(f"❌ GraphML file not found: {graphml_path}")
            sys.exit(1)
        metrics = evaluate_image(
            img_path,
            graphml_path,
            model_type=args.model,
            confidence=args.confidence,
            iou_threshold=args.iou_threshold,
            use_sahi=args.sahi,
            sahi_slice_size=args.sahi_slice_size,
            class_agnostic=not args.class_aware
        )
        print(json.dumps(asdict(metrics), indent=2))
    else:
        # Full dataset evaluation
        if not data_dir.exists():
            print(f"❌ Data directory not found: {data_dir}")
            print("\nPlease download the dataset first:")
            print("  python scripts/download.py --full")
            sys.exit(1)

        evaluate_dataset(
            data_dir,
            output_path,
            model_type=args.model,
            confidence=args.confidence,
            iou_threshold=args.iou_threshold,
            use_sahi=args.sahi,
            sahi_slice_size=args.sahi_slice_size,
            class_agnostic=not args.class_aware,
            limit=args.limit
        )


if __name__ == "__main__":
    main()
