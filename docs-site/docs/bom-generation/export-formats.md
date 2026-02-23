---
sidebar_position: 3
title: Export Formats
description: BOM and quotation export formats - Excel, JSON, and PDF
---

# Export Formats

The BOM system supports multiple export formats for different use cases. Each format contains the complete BOM data with detection results, dimensions, pricing, and verification status.

## Format Comparison

| Feature | Excel (.xlsx) | JSON (.json) | PDF (.pdf) |
|---------|:------------:|:------------:|:----------:|
| Structured BOM table | Yes | Yes | Yes |
| Pricing breakdown | Yes | Yes | Yes |
| Drawing image | No | No | Yes |
| Detection overlay | No | No | Yes |
| Machine-readable | Partial | Yes | No |
| Human-readable | Yes | Partial | Yes |
| Editable | Yes | Yes | No |
| Self-contained | Yes | Yes | Yes |
| Typical file size | 50-200 KB | 20-100 KB | 500 KB - 2 MB |
| Primary use case | Procurement | API integration | Customer quotation |

## Excel Export

The Excel export produces a structured workbook with BOM data organized for procurement and manufacturing workflows.

### Sheet Structure

**Sheet 1: BOM**

| Column | Description | Example |
|--------|-------------|---------|
| No. | Item number | 1 |
| Part Number | Drawing part number | T1-001 |
| Description | Part name | T1 BEARING ASSY |
| Material | Material specification | SCM440+QT |
| Size | Dimension specification | OD670XID440X29.5T |
| Quantity | Count | 2 |
| Unit | Unit of measure | EA |
| Unit Price | Per-unit cost | 485,000 |
| Total Price | Quantity x Unit Price | 970,000 |
| Verification | Status | Approved |

**Sheet 2: Cost Breakdown (when pricing is included)**

| Column | Description |
|--------|-------------|
| Description | Part name |
| Weight (kg) | Calculated weight |
| Material Cost | Raw material cost |
| Machining Cost | Manufacturing cost |
| Treatment Cost | Heat/surface treatment |
| Setup Cost | Setup/tooling cost |
| Inspection Cost | QC cost |
| Transport Cost | Logistics cost |
| Subtotal | Total item cost |
| Cost Source | calculated / estimated / catalog |

### Export Endpoint

```
GET /export/excel/{session_id}
```

## JSON Export

The JSON format provides the complete BOM data structure for API integration and programmatic processing.

### Response Structure

```json
{
  "session_id": "abc-123",
  "filename": "drawing-001.png",
  "drawing_type": "electrical",
  "created_at": "2026-02-22T10:30:00Z",
  "bom": {
    "items": [
      {
        "id": "item-001",
        "part_number": "T1-001",
        "description": "T1 BEARING ASSY",
        "material": "SCM440+QT",
        "size": "OD670XID440X29.5T",
        "quantity": 2,
        "unit": "EA",
        "class_name": "BEARING",
        "confidence": 0.92,
        "verification_status": "approved",
        "pricing": {
          "unit_price": 485000,
          "total_price": 970000,
          "cost_breakdown": {
            "weight_kg": 45.2,
            "material_cost": 356400,
            "machining_cost": 120000,
            "treatment_cost": 36160,
            "setup_cost": 0,
            "inspection_cost": 25630,
            "transport_cost": 4520,
            "subtotal": 970000,
            "cost_source": "calculated"
          }
        },
        "dimensions": {
          "od": 670,
          "id": 440,
          "length": 29.5
        },
        "bbox": { "x1": 100, "y1": 200, "x2": 300, "y2": 350 }
      }
    ],
    "summary": {
      "total_items": 15,
      "total_cost": 8500000,
      "currency": "KRW"
    }
  },
  "detections": [...],
  "dimensions": [...]
}
```

### Export Endpoint

```
GET /export/json/{session_id}
```

## PDF Export

The PDF format produces a formatted quotation document suitable for customer delivery. See [PDF Report](./pdf-report.md) for detailed layout information.

### Export Endpoint

```
GET /export/pdf/{session_id}
POST /quotation/generate/{session_id}
```

## Self-Contained Export Package

For archival and offline review, the system can generate a self-contained export package:

```
export-package/
  ├── bom.xlsx           # BOM spreadsheet
  ├── bom.json           # Machine-readable BOM
  ├── quotation.pdf      # Formatted quotation
  ├── drawing.png        # Original drawing image
  ├── detection.png      # Drawing with detection overlay
  └── metadata.json      # Session and analysis metadata
```

### Package Export Endpoint

```
POST /export/package/{session_id}
```

Returns a ZIP archive containing all export files.

## Session I/O

Beyond export, the system supports session import/export for backup and transfer:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/session/export/{session_id}` | GET | Export complete session state |
| `/session/import` | POST | Import session from exported data |
| `/project/export/{project_id}` | GET | Export all sessions in a project |
| `/project/import` | POST | Import project with all sessions |
