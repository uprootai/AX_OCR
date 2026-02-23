---
sidebar_position: 1
title: Node Catalog
description: Complete reference of all 29+ BlueprintFlow node types organized by category
---

# Node Catalog

BlueprintFlow provides 29+ node types across 9 categories. Each node wraps a microservice API endpoint and exposes configurable parameters through the properties panel.

## Input Nodes

Entry points for data into the workflow.

| Node | Description | Key Parameters |
|------|-------------|----------------|
| **ImageInput** | Upload or reference a drawing image | `source`, `format` |
| **TextInput** | Provide text input (part numbers, queries) | `text`, `mode` |

## Detection Nodes

Object and symbol detection on images.

| Node | Port | Description | Key Parameters |
|------|------|-------------|----------------|
| **YOLO** | 5005 | YOLOv11 symbol detection (73 classes) | `model_type`, `confidence`, `iou`, `imgsz`, `use_sahi`, `slice_height`, `slice_width`, `overlap_ratio`, `visualize`, `task` |
| **Table Detector** | 5022 | Table structure detection and extraction | `mode`, `ocr_engine`, `borderless`, `confidence_threshold`, `min_confidence`, `output_format` |

## OCR Nodes

Text and dimension extraction engines.

| Node | Port | Description | Key Parameters |
|------|------|-------------|----------------|
| **eDOCr2** | 5002 | Korean engineering drawing OCR | `language`, `extract_dimensions`, `extract_gdt`, `extract_text`, `extract_tables`, `cluster_threshold`, `visualize`, `enable_crop_upscale`, `crop_preset`, `upscale_scale`, `upscale_denoise` |
| **PaddleOCR** | 5006 | Multi-language OCR (80+ languages) | `language`, `det_model`, `rec_model` |
| **Tesseract** | 5008 | General document OCR | `language`, `psm`, `oem` |
| **TrOCR** | 5009 | Handwritten text recognition | `model_size` |
| **OCR Ensemble** | 5011 | 4-engine weighted voting | `engines`, `weights` |
| **Surya OCR** | 5013 | Layout-aware OCR (90+ languages) | `language`, `detect_layout` |
| **DocTR** | 5014 | Two-stage detection + recognition | `det_arch`, `reco_arch` |
| **EasyOCR** | 5015 | Easy-to-use OCR (80+ languages) | `language`, `detail` |

## Segmentation Nodes

Image segmentation and line detection.

| Node | Port | Description | Key Parameters |
|------|------|-------------|----------------|
| **EDGNet** | 5012 | Edge segmentation for contour extraction | `threshold`, `mode` |
| **Line Detector** | 5016 | P&ID line and connection detection | `min_length`, `merge_distance` |

## Preprocessing Nodes

Image enhancement before analysis.

| Node | Port | Description | Key Parameters |
|------|------|-------------|----------------|
| **ESRGAN** | 5010 | 4x image super-resolution upscaling | `scale`, `denoise_strength` |

## Analysis Nodes

Domain-specific analysis and reporting.

| Node | Port | Description | Key Parameters |
|------|------|-------------|----------------|
| **SkinModel** | 5003 | GD&T tolerance analysis | `material_type`, `manufacturing_process`, `correlation_length`, `task` |
| **PID Analyzer** | 5018 | P&ID connection and flow analysis | `analysis_mode` |
| **Design Checker** | 5019 | P&ID design rule verification | `ruleset` |
| **GT Comparison** | -- | Ground truth / revision comparison | `threshold`, `mode` |
| **PDF Export** | -- | Generate PDF report from results | `template`, `include_images` |
| **PID Features** | -- | P&ID feature extraction | `feature_types` |
| **Verification Queue** | -- | Human-in-the-Loop review queue | `priority`, `auto_approve_threshold` |
| **Dimension Updater** | -- | Update dimension values from OCR | `merge_strategy` |

## BOM Nodes

Bill of Materials generation and management.

| Node | Port | Description | Key Parameters |
|------|------|-------------|----------------|
| **Blueprint AI BOM** | 5020 | Human-in-the-Loop BOM generation | `features` (array: `verification`, `gt_comparison`, `bom_generation`, `dimension_extraction`) |

## Knowledge Nodes

Knowledge graph and retrieval.

| Node | Port | Description | Key Parameters |
|------|------|-------------|----------------|
| **Knowledge** | 5007 | Neo4j GraphRAG for engineering knowledge | `query_type`, `depth` |

## AI Nodes

Vision-Language model integration.

| Node | Port | Description | Key Parameters |
|------|------|-------------|----------------|
| **VL** | 5004 | Qwen2-VL vision-language model | `task`, `prompt` |

## Control Nodes

Workflow control flow and branching.

| Node | Description | Key Parameters |
|------|-------------|----------------|
| **IF** | Conditional branching based on result values | `condition`, `field`, `value` |
| **Loop** | Iterate over arrays or repeat N times | `mode`, `count`, `field` |
| **Merge** | Combine results from multiple branches | `strategy` |

## Node Category Types

All nodes are assigned one of the following categories in code:

```typescript
type NodeCategory =
  | 'input'
  | 'detection'
  | 'ocr'
  | 'segmentation'
  | 'preprocessing'
  | 'analysis'
  | 'knowledge'
  | 'ai'
  | 'control';
```

Note: The `'api'` type is not used.

## Notes

- Parameter names must match those defined in `gateway-api/api_specs/*.yaml`. Do not use parameters not present in the API specification.
- GPU-accelerated nodes (YOLO, eDOCr2, VL, etc.) can be configured for GPU allocation through the Dashboard.
- The `visualize` parameter, where available, returns annotated images alongside JSON results.
