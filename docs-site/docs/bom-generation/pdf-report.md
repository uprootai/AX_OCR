---
sidebar_position: 4
title: PDF Report
description: Formatted PDF quotation report with company branding and multi-page support
---

# PDF Report

The PDF report generates a professional manufacturing quotation document from verified BOM data. The report includes company branding, structured pricing tables, and optional drawing images.

## Report Layout

### Page 1: Cover / Summary

| Section | Content |
|---------|---------|
| **Header** | Company logo, company name, document title |
| **Document Info** | Quotation number, date, validity period |
| **Customer Info** | Customer name, project name, contact details |
| **Summary Table** | Total items, total cost, currency, payment terms |
| **Footer** | Page number, confidentiality notice |

### Page 2+: BOM Table

The BOM table spans multiple pages with automatic pagination:

| Column | Width | Description |
|--------|-------|-------------|
| No. | 5% | Sequential item number |
| Description | 25% | Part name and specification |
| Material | 12% | Material grade |
| Size | 15% | Dimensional specification |
| Qty | 5% | Quantity |
| Unit Price | 15% | Per-unit cost (KRW) |
| Total | 15% | Line total |
| Status | 8% | Verification status |

### Cost Summary Section

Appears at the bottom of the last BOM page:

| Line | Description |
|------|-------------|
| Subtotal (Materials) | Sum of all material costs |
| Subtotal (Machining) | Sum of all machining costs |
| Heat Treatment | Sum of treatment costs |
| Inspection & QC | Quality control costs |
| Packing & Transport | Logistics costs |
| **Grand Total** | **Sum of all line items** |

### Optional: Drawing Appendix

When enabled, the report includes the original drawing image with detection overlays highlighting identified components.

## Company Branding

The PDF generator supports customizable branding:

| Element | Customizable | Default |
|---------|:----------:|---------|
| Company logo | Yes | AX POC logo |
| Company name | Yes | "AX Engineering" |
| Address | Yes | Company address |
| Contact info | Yes | Phone, email |
| Primary color | Yes | `#1565c0` (blue) |
| Font | Yes | NanumGothic (Korean support) |
| Footer text | Yes | Confidentiality notice |

Branding configuration is stored in the project settings and applied to all generated reports.

## Multi-Page Support

The PDF engine handles BOM tables of any length:

- **Automatic pagination**: Tables split across pages with repeated headers
- **Page numbering**: "Page X of Y" format in footer
- **Orphan control**: Minimum 3 rows per page to avoid single-row pages
- **Summary placement**: Cost summary always appears on the last page after the BOM table

## Number Formatting

All monetary values use Korean Won (KRW) formatting:

| Format | Example |
|--------|---------|
| Unit price | 485,000 |
| Total price | 8,500,000 |
| Grand total | 12,350,000 |

Decimal values (weights, dimensions) use up to 2 decimal places.

## Generation Endpoints

### Generate Quotation PDF

```
POST /quotation/generate/{session_id}
```

**Request Body** (optional):

```json
{
  "customer_name": "Customer Corp.",
  "project_name": "Pump Overhaul Project",
  "validity_days": 30,
  "include_drawing": true,
  "include_cost_breakdown": true,
  "notes": "Delivery within 8 weeks after PO"
}
```

**Response**: PDF file download

### Export as PDF

```
GET /export/pdf/{session_id}
```

Returns the cached PDF if previously generated, or generates a new one.

## Page Size and Margins

| Property | Value |
|----------|-------|
| Page size | A4 (210 x 297 mm) |
| Top margin | 25 mm |
| Bottom margin | 20 mm |
| Left margin | 20 mm |
| Right margin | 20 mm |
| Header height | 35 mm |
| Footer height | 15 mm |

## Supported Languages

The PDF report supports bilingual content:

| Language | Font | Usage |
|----------|------|-------|
| Korean | NanumGothic | Part descriptions, headers |
| English | Helvetica / Arial | Technical specifications, class names |
| Mixed | Auto-detect | Supports mixed Korean/English text |
