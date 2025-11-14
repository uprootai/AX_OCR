# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AX 실증산단 - Microservice API System**

This is a microservices-based system for automated quotation generation from engineering drawings. The system consists of 4 independent API services plus a web UI that work together to process engineering drawings, extract dimensions, perform segmentation, predict tolerances, and generate cost estimates.

## Architecture

### Services Overview

The system follows a microservices architecture with these components:

```
┌─────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│  eDOCr2 API     │     │  EDGNet API     │     │  Skin Model API  │
│  Port: 5001/5002│     │  Port: 5012     │     │  Port: 5003      │
│  OCR Processing │     │  Segmentation   │     │  Tolerance Pred. │
└─────────────────┘     └─────────────────┘     └──────────────────┘
         ↑                       ↑                       ↑
         └───────────────────────┴───────────────────────┘
                                 │
                        ┌────────────────┐
                        │  Gateway API   │
                        │  Port: 8000    │
                        │  Orchestrator  │
                        └────────────────┘
                                 ↑
                        ┌────────────────┐
                        │  Web UI        │
                        │  Port: 5173    │
                        │  React + Vite  │
                        └────────────────┘
```

### Service Details

1. **eDOCr2 API** (edocr2-api/)
   - Dual deployment: v1 (port 5001) and v2 (port 5002)
   - v1: Uses eDOCr v1 with Keras 2.x models (.h5)
   - v2: Uses edocr2 v2 with Keras 3.x models (.keras) + supports table OCR
   - Extracts: dimensions, GD&T symbols, text/infoblock from drawings
   - Server files: `api_server_edocr_v1.py`, `api_server_edocr_v2.py`
   - CRITICAL: v2 models require both `.keras` AND corresponding `.txt` alphabet files

2. **EDGNet API** (edgnet-api/)
   - Graph neural network-based drawing segmentation
   - Classifies drawing components (contours, text, dimensions)
   - Model: GraphSAGE dimension classifier (.pth)
   - Exposes: `/api/v1/segment`, `/api/v1/vectorize`

3. **Skin Model API** (skinmodel-api/)
   - Geometric tolerance prediction
   - Manufacturing feasibility analysis
   - GD&T validation

4. **Gateway API** (gateway-api/)
   - Orchestrates full pipeline across all services
   - Manages workflow between eDOCr2, EDGNet, and Skin Model
   - Generates quotations from analysis results

5. **Web UI** (web-ui/)
   - React 19 + TypeScript + Vite
   - TailStack: Tailwind CSS styling
   - State: Zustand for monitoring/trace state
   - Data fetching: TanStack Query (React Query)
   - Routing: React Router v7

## Development Commands

### Building & Running Services

#### Full System (All Services)
```bash
# Start all services via docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

#### Individual Services

**eDOCr2 API (Dual Deployment - v1 + v2)**
```bash
cd edocr2-api

# Build v1
docker build -f Dockerfile.v1 -t edocr-api:v1 .

# Build v2
docker build -f Dockerfile.v2 -t edocr-api:v2 .

# Run dual deployment (v1 on 5001, v2 on 5002)
docker-compose -f docker-compose-dual.yml up -d

# Health checks
curl http://localhost:5001/api/v1/health  # v1
curl http://localhost:5002/api/v2/health  # v2
```

**EDGNet API**
```bash
cd edgnet-api
docker build -t edgnet-api .
docker run -d -p 5012:5002 --name edgnet edgnet-api
curl http://localhost:5012/api/v1/health
```

**Skin Model API**
```bash
cd skinmodel-api
docker build -t skinmodel-api .
docker run -d -p 5003:5003 --name skinmodel skinmodel-api
curl http://localhost:5003/api/v1/health
```

**Gateway API**
```bash
cd gateway-api
docker build -t gateway-api .
docker run -d -p 8000:8000 --name gateway gateway-api
curl http://localhost:8000/api/v1/health
```

**Web UI**
```bash
cd web-ui

# Development mode (hot reload)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint
npm run lint

# Docker deployment
docker build -t web-ui .
docker run -d -p 5173:80 --name web-ui web-ui
```

### Testing

#### API Health Checks
```bash
# Test all services at once
cd /home/uproot/ax/poc
./test_apis.sh
```

#### Python Test Scripts
```bash
# General API testing
python test_apis.py

# eDOCr2 visualization testing
python test_edocr2_viz.py

# OCR visualization testing
python test_ocr_visualization.py

# PDF conversion testing
python test_pdf_conversion.py

# Bounding box verification
python test_edocr2_bbox.py
python test_edocr2_bbox_detailed.py
python verify_bbox_api.py
```

#### Manual API Testing

**eDOCr2 v1 OCR**
```bash
curl -X POST http://localhost:5001/api/v1/ocr \
  -F "file=@drawing.pdf" \
  -F "extract_dimensions=true" \
  -F "extract_gdt=true" \
  -F "extract_text=true"
```

**eDOCr2 v2 OCR (with table extraction)**
```bash
curl -X POST http://localhost:5002/api/v2/ocr \
  -F "file=@drawing.pdf" \
  -F "extract_dimensions=true" \
  -F "extract_gdt=true" \
  -F "extract_text=true" \
  -F "extract_tables=true"
```

**EDGNet Segmentation**
```bash
curl -X POST http://localhost:5012/api/v1/segment \
  -F "file=@drawing.png" \
  -F "visualize=true"
```

**Gateway Full Pipeline**
```bash
curl -X POST http://localhost:8000/api/v1/process \
  -F "file=@drawing.pdf" \
  -F "generate_quote=true"
```

## Key Technical Details

### eDOCr2 Dual Deployment System

This project runs TWO versions of eDOCr simultaneously:

- **v1 (port 5001)**: Faster, uses Keras 2.x, stable
- **v2 (port 5002)**: Advanced features (table OCR), uses Keras 3.x, requires alphabet files

**CRITICAL**: When working with v2:
1. Model files need BOTH `.keras` and `.txt` files (e.g., `recognizer_dimensions_2.keras` + `recognizer_dimensions_2.txt`)
2. The `.txt` files contain alphabet definitions required by the recognizer
3. Missing alphabet files will cause `FileNotFoundError`
4. Download v2 models from: https://github.com/javvi51/edocr2/releases/tag/v1.0.0

### Data Transformation Layer

Both eDOCr v1 and v2 have different output formats. The API servers transform these to a UI-compatible format:

**v1**: Uses `transform_edocr_to_ui_format()` in `api_server_edocr_v1.py`
- Handles eDOCr v1 format with 'pred', 'box' keys
- Converts 'value'/'nominal' to UI expected format

**v2**: Uses `transform_edocr2_to_ui_format()` in `api_server_edocr_v2.py`
- Handles edocr2 format with different schema
- Includes coordinate scaling/offset for processed images
- Supports table extraction results

**Key transformation**: Both functions convert to this UI format:
```json
{
  "dimensions": [{"type": "linear|diameter|radius", "value": 50.5, "unit": "mm", "tolerance": "±0.1", "location": {"x": 100, "y": 200}}],
  "gdt": [{"type": "⏤", "value": 0.05, "datum": "A", "location": {"x": 150, "y": 250}}],
  "text": {"drawing_number": "DWG-001", "revision": "A", "title": "Part", "material": "Steel", "notes": [], "total_blocks": 5}
}
```

### Web UI Architecture

**State Management**:
- `monitoringStore.ts`: Zustand store for API health status and request traces
- Tracks service health for: gateway, edocr2_v1, edocr2_v2, edgnet, skinmodel
- Maintains request trace history (max 50 traces)
- Calculates performance metrics (avgResponseTime, successRate, errorRate)

**Key Components**:
- `TestEdocr2.tsx`: Allows switching between v1/v2, visualizes OCR results with bounding boxes
- `OCRVisualization.tsx`: Renders dimensions/GD&T overlays on images
- `APIStatusMonitor.tsx`: Real-time service health monitoring
- `RequestInspector.tsx`: Debug tool for API request/response inspection

**Version Selection**:
The UI supports selecting between eDOCr v1 and v2 via dropdown. This changes the API endpoint from `/api/v1/ocr` to `/api/v2/ocr`.

### Docker Volumes

All services use volume mounts for:
- Model files (read-only): Shared from `/home/uproot/ax/dev/`
- Upload directories: Temporary file storage
- Results directories: Processed outputs

Example for eDOCr2:
```yaml
volumes:
  - ./dev/edocr2/edocr2:/app/edocr2:ro  # Source code (read-only)
  - ./dev/edocr2/models:/models:ro      # Model files (read-only)
  - ./edocr2-api/uploads:/tmp/edocr2/uploads
  - ./edocr2-api/results:/tmp/edocr2/results
```

### CORS Configuration

All API services have CORS enabled for local development:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Web UI
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Environment Variables

Each service can be configured via environment variables (see docker-compose.yml):

- `EDOCR2_PORT`, `EDOCR2_WORKERS`, `EDOCR2_MODEL_PATH`, `EDOCR2_LOG_LEVEL`
- `EDGNET_PORT`, `EDGNET_WORKERS`, `EDGNET_MODEL_PATH`, `EDGNET_LOG_LEVEL`
- `SKINMODEL_PORT`, `SKINMODEL_WORKERS`, `SKINMODEL_LOG_LEVEL`
- `GATEWAY_PORT`, `GATEWAY_WORKERS`, `EDOCR2_URL`, `EDGNET_URL`, `SKINMODEL_URL`, `GATEWAY_LOG_LEVEL`

## Common Patterns

### Adding a New API Endpoint

1. Define Pydantic models for request/response
2. Add FastAPI route handler
3. Implement business logic
4. Add CORS if needed
5. Update API documentation (auto-generated via FastAPI)
6. Add health check if new service
7. Update docker-compose.yml if needed

### Working with NumPy/TensorFlow Output

Use `convert_to_serializable()` helper to convert NumPy types to JSON-serializable Python types:
```python
def convert_to_serializable(obj):
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    # ... handle dicts, lists recursively
```

### Bounding Box Handling

When working with bounding boxes from OCR results:
- eDOCr v1 uses `box` or `bbox` key (format: [[x,y], [x,y], [x,y], [x,y]])
- eDOCr v2 uses `bbox` key
- UI expects: `{x: int, y: int, width: int, height: int}`
- Always validate bbox has 4 points before processing
- Apply coordinate scaling when image was resized during processing

### Adding UI Components

1. Create component in `web-ui/src/components/`
2. Use existing UI primitives from `components/ui/` (Card, Button, Badge, Tooltip)
3. Integrate with Zustand store if state needed
4. Use TanStack Query for data fetching
5. Add route in `App.tsx` if new page
6. Follow existing TypeScript patterns

## Troubleshooting

### Port Conflicts
```bash
# Check what's using a port
sudo lsof -i :5001
sudo lsof -i :5002
sudo lsof -i :5012
sudo lsof -i :5003
sudo lsof -i :8000
```

### Container Logs
```bash
# Individual service
docker logs -f edocr2-api-v1
docker logs -f edocr2-api-v2
docker logs -f edgnet
docker logs -f gateway

# All services
docker-compose logs -f
```

### Model File Issues

**eDOCr v1**: Models auto-download to `~/.keras-ocr/` on first run
**eDOCr v2**: Must manually download `.keras` + `.txt` files to `edocr2-api/models/`

```bash
cd edocr2-api/models
curl -L -O https://github.com/javvi51/edocr2/releases/download/v1.0.0/recognizer_dimensions_2.keras
curl -L -O https://github.com/javvi51/edocr2/releases/download/v1.0.0/recognizer_dimensions_2.txt
curl -L -O https://github.com/javvi51/edocr2/releases/download/v1.0.0/recognizer_gdts.keras
curl -L -O https://github.com/javvi51/edocr2/releases/download/v1.0.0/recognizer_gdts.txt
```

### Web UI Not Connecting to APIs

1. Check if all services are running: `docker ps`
2. Verify CORS settings in API servers
3. Check environment variables in `web-ui/Dockerfile` or `.env`
4. Ensure ports match between UI config and docker-compose

### JSON Serialization Errors

If you see errors like "Object of type 'int64' is not JSON serializable":
- Use `convert_to_serializable()` helper on all data before returning
- Common with NumPy arrays, TensorFlow outputs, PIL images

## Reference Documentation

- **eDOCr v1**: https://github.com/javvi51/eDOCr
- **edocr2 v2**: https://github.com/javvi51/edocr2
- **FastAPI**: https://fastapi.tiangolo.com/
- **React Query**: https://tanstack.com/query/latest
- **Zustand**: https://zustand-demo.pmnd.rs/

## Project-Specific Notes

- Primary language: Korean (도면 = drawing, 치수 = dimension, 공차 = tolerance, 견적 = quotation)
- Target domain: Manufacturing/machining cost estimation from engineering drawings
- Performance: ~25-30s for full pipeline (CPU), ~8-10s per service
- GPU support planned but not yet configured
- Test samples available in `/home/uproot/ax/reference/02. 수요처 및 도메인 자료/2. 도면(샘플)/`

---

## 🎯 OCR Performance Improvement Strategy

### Current Issues

**Limitations of eDOCr v2 Alone**:
- Dimension recall: ~50% (target: 90%+)
- GD&T recall: ~20% (target: 75%+)
- Missing dimensions in complex areas
- Context information not utilized

**Root Causes**:
1. Single OCR engine limitations
2. Image-based detection limits (complex drawings)
3. Dimension-GD&T-contour relationships not utilized
4. No missing validation mechanism

### Improvement Strategy: Multi-Model Pipeline

#### Strategy 1: Use EDGNet as Preprocessor ⭐⭐⭐

**EDGNet Strengths**:
- Graph neural network-based accurate region segmentation
- Contour/Text/Dimension separation: 90.82% accuracy
- Context utilization (GraphSAGE)

**Application Method**:
```
Original Drawing
  ↓
EDGNet Vectorization + Segmentation
  ├─ Contour regions
  ├─ Text regions
  └─ Dimension regions (Focus here!)
  ↓
Optimized OCR per region
  ├─ Dimension regions → eDOCr v2 CRNN
  ├─ Text regions → Tesseract + EasyOCR
  └─ GD&T → eDOCr v2 (focused search near dimensions)
  ↓
Utilize graph relationships
  └─ GD&T-dimension matching
  └─ Dimension-contour linking
```

**Expected Impact**:
- Dimension recall: 50% → **85%** (+35%p)
- GD&T recall: 20% → **70%** (+50%p)
- Reduced false positives

#### Strategy 2: Skin Model for Validation & Recovery ⭐⭐

**Skin Model Role**:
- Predict expected dimension locations via geometry analysis
- Detect missing dimensions
- Validate recognized dimension plausibility

**Application Method**:
```python
# Predict expected dimensions from geometry
expected_dims = skin_model.predict_expected_dimensions(contours)

# Compare with OCR results
missing = find_missing_dimensions(ocr_results, expected_dims)

# Retry OCR on missing locations
for miss in missing:
    enhanced_region = super_resolution(crop(image, miss.location))
    recovered = ocr_engine.recognize(enhanced_region)
```

**Expected Impact**:
- Prevent critical dimension omissions (diameters, major lengths)
- Improved OCR confidence
- Alert users to potential missing data

#### Strategy 3: Gateway Multi-Stage Pipeline ⭐⭐⭐

**Enhanced Gateway**:
```python
# 4-stage pipeline
async def advanced_ocr_pipeline(image):
    # Stage 1: EDGNet segmentation
    segmentation = await edgnet.segment(image)

    # Stage 2: v1/v2 ensemble OCR
    ocr_v1 = await edocr_v1.ocr(image, regions=segmentation['dimensions'])
    ocr_v2 = await edocr_v2.ocr(image, regions=segmentation['dimensions'])
    dimensions = ensemble(ocr_v1, ocr_v2, weights={'v1': 0.6, 'v2': 0.4})

    # Stage 3: Skin Model validation
    validation = await skinmodel.validate(segmentation['contours'], dimensions)

    # Stage 4: Missing recovery
    if validation['missing']:
        recovered = await retry_missing_regions(image, validation['missing'])
        dimensions.extend(recovered)

    return dimensions
```

**Expected Impact**:
- Recall: 50% → **90%**
- Improved precision
- Increased confidence

### Expected Performance Improvement

| Metric | Current (v2 Only) | After (Multi-Model) | Gain |
|--------|------------------|---------------------|------|
| Dimension Recall | ~50% | **90%** | +40%p |
| GD&T Recall | ~20% | **75%** | +55%p |
| Overall F1 | 0.59 | **0.88** | +0.29 |

### Implementation Priorities

1. **Phase 1**: EDGNet integration (1-2 weeks) - Highest impact
2. **Phase 2**: Gateway multi-stage (2-3 weeks)
3. **Phase 3**: Skin Model validation (2-3 weeks)
4. **Phase 4**: Optimization & evaluation (1-2 weeks)

**Total Time**: 6-10 weeks

**Target Achievement**:
- ✅ MaP 0.88 (project goal) → Achievable
- ✅ Metadata extraction accuracy 0.9 → Achievable

### References

Detailed analysis: `/home/uproot/ax/poc/OCR_IMPROVEMENT_STRATEGY.md`

**Note**: A Korean version of this guide is available at `/home/uproot/ax/poc/CLAUDE_KR.md`
