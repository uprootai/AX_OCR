---
sidebar_position: 1
title: Detection Classes
description: Complete list of 73 detection classes for BOM generation and annotation
---

# Detection Classes

The system uses specialized YOLO v11 models trained on engineering drawings. Across all models, 73+ classes are recognized, divided into BOM-relevant components and annotation elements.

## BOM-Relevant Classes (27)

These classes represent physical components detected in electrical single-line diagrams. Each detection contributes to the Bill of Materials with quantity counting and pricing.

### Electrical Equipment Classes

The `bom_detector` model detects 27 classes of power distribution equipment:

| Class ID | Class Name | Display Name | Category |
|----------|-----------|-------------|----------|
| 0 | ARRESTER | Arrester | Protection |
| 1 | CB DS ASSY | CB DS Assembly | Switching |
| 2 | CT | Current Transformer | Measurement |
| 3 | CVT | Capacitive Voltage Transformer | Measurement |
| 4 | DS ASSY | Disconnector Assembly | Switching |
| 5 | ES / EST | Earth Switch | Grounding |
| 6 | GIS | Gas Insulated Switchgear | Switching |
| 7 | LA | Lightning Arrester | Protection |
| 8 | LS | Line Switch | Switching |
| 9 | MOF | Metering Outfit | Measurement |
| 10 | NGR | Neutral Grounding Resistor | Grounding |
| 11 | P.Fuse | Power Fuse | Protection |
| 12 | PI | Power Indicator | Measurement |
| 13 | PT | Potential Transformer | Measurement |
| 14 | SA | Surge Arrester | Protection |
| 15 | SPD | Surge Protection Device | Protection |
| 16 | T.C | Contactor | Switching |
| 17 | TR | Transformer | Power |
| 18 | VT | Voltage Transformer | Measurement |
| 19 | Branch (U-type) | U-type Branch | Wiring |
| 20 | Disconnector | Disconnector | Switching |
| 21 | Motor | Motor | Load |
| 22 | Power Fuse | Power Fuse | Protection |
| 23 | Rectifier | Rectifier | Conversion |
| 24 | Circuit Breaker | Circuit Breaker | Protection |
| 25 | Capacitor | Capacitor | Power Factor |
| 26 | Arrester (alt) | Arrester | Protection |

### Class Categories Summary

| Category | Count | Classes |
|----------|-------|---------|
| **Protection** | 7 | ARRESTER, LA, SA, SPD, P.Fuse, Power Fuse, Circuit Breaker |
| **Switching** | 6 | CB DS ASSY, DS ASSY, GIS, LS, T.C, Disconnector |
| **Measurement** | 6 | CT, CVT, MOF, PI, PT, VT |
| **Power** | 1 | TR |
| **Grounding** | 2 | ES/EST, NGR |
| **Load** | 1 | Motor |
| **Conversion** | 1 | Rectifier |
| **Power Factor** | 1 | Capacitor |
| **Wiring** | 1 | Branch (U-type) |
| **Other** | 1 | Arrester (alt) |

## P&ID Symbol Classes (60)

The `pid_symbol` model detects P&ID symbols used in process and instrumentation diagrams:

### Valve Types

| Class | Description |
|-------|-------------|
| Gate Valve | Standard gate valve |
| Globe Valve | Globe/control valve |
| Ball Valve | Ball valve |
| Butterfly Valve | Butterfly valve |
| Check Valve | Non-return valve |
| Relief Valve | Pressure relief |
| Control Valve | Automated control valve |
| Solenoid Valve | Electrically actuated |
| 3-Way Valve | Three-way routing valve |
| Needle Valve | Fine flow control |

### Equipment

| Class | Description |
|-------|-------------|
| Pump | Centrifugal/positive displacement |
| Compressor | Gas compression |
| Heat Exchanger | Shell and tube / plate |
| Tank | Storage vessel |
| Reactor | Chemical reactor |
| Filter | Filtration equipment |
| Separator | Phase separation |
| Column | Distillation/absorption |

### Instruments

| Class | Description |
|-------|-------------|
| Pressure Indicator | PI |
| Temperature Indicator | TI |
| Flow Indicator | FI |
| Level Indicator | LI |
| Pressure Transmitter | PT |
| Temperature Transmitter | TT |
| Flow Transmitter | FT |
| Level Transmitter | LT |
| Controller | PID Controller |

### Piping Elements

| Class | Description |
|-------|-------------|
| Reducer | Pipe size reduction |
| Tee | T-junction |
| Elbow | Direction change |
| Flange | Pipe connection |
| Orifice | Flow measurement |
| Spectacle Blind | Isolation |

## Annotation Classes (46+)

Annotation classes are detected across all drawing types and provide supplementary information. These do not contribute directly to the BOM count but enrich the extracted data.

### Dimension Types

| Type | Description | Example |
|------|-------------|---------|
| Length | Linear dimension | `45.2 mm` |
| Diameter | Circular dimension | `OD 670 mm` |
| Radius | Arc dimension | `R 25` |
| Angle | Angular dimension | `45.0 deg` |
| Thread | Thread specification | `M24x120L` |

### Tolerance Types

| Type | Description | Example |
|------|-------------|---------|
| Bilateral | Plus/minus tolerance | `45.2 +/- 0.1` |
| Unilateral | One-direction tolerance | `45.2 +0.05 / -0.00` |
| Limit | Min/max range | `45.15 - 45.25` |

### GD&T Symbols

| Symbol | Description |
|--------|-------------|
| Straightness | Line straightness |
| Flatness | Surface flatness |
| Circularity | Cross-section roundness |
| Cylindricity | Full cylinder form |
| Perpendicularity | 90-degree relation |
| Parallelism | Parallel surfaces |
| Position | True position |
| Concentricity | Axis alignment |
| Runout | Rotation deviation |
| Total Runout | Full indicator movement |
| Profile of a Line | Line profile |
| Profile of a Surface | Surface profile |

### Surface Finish

| Class | Description |
|-------|-------------|
| Surface Roughness | Ra / Rz values |
| Machining Symbol | Machining requirement |
| Welding Symbol | Weld type specification |

## Model Configuration

Each detection model has specific default parameters:

| Model | Confidence | IOU | Image Size | SAHI |
|-------|-----------|-----|-----------|------|
| `bom_detector` | 0.40 | 0.50 | 1024 | Off |
| `pid_symbol` | 0.10 | 0.45 | 1024 | On |
| `pid_class_aware` | 0.10 | 0.45 | 1024 | On |
| `pid_class_agnostic` | 0.10 | 0.45 | 1024 | On |
| `engineering` | 0.50 | 0.45 | 640 | Off |
| `panasia` | 0.40 | 0.50 | 1024 | Off |

**SAHI** (Slicing Aided Hyper Inference) is enabled for P&ID models to improve detection of small symbols by processing the image in overlapping 512x512 slices with 25% overlap.

## Margin Penalty

Detections in drawing margin areas (title block, revision block, outer edges) receive a 50% confidence penalty to reduce false positives:

| Region | Condition | Penalty |
|--------|-----------|---------|
| Title block | x > 65% and y > 85% | 0.5x |
| Revision block | x > 75% and y < 15% | 0.5x |
| Top/bottom margin | y < 3% or y > 97% | 0.5x |
| Left/right margin | x < 3% or x > 97% | 0.5x |
