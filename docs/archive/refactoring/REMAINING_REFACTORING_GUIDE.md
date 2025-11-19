# Quick Guide: Complete Remaining API Refactorings

This guide provides the exact steps to complete the refactoring of edgnet-api, skinmodel-api, and paddleocr-api.

## Status Summary

- ✅ **yolo-api**: DONE (324 lines, builds successfully)
- ✅ **edocr2-v2-api**: DONE (228 lines, build in progress)
- ⏸️ **edgnet-api**: Structure created, needs code extraction (583 → ~250 lines)
- ⏸️ **skinmodel-api**: Structure created, needs code extraction (488 → ~220 lines)
- ⏸️ **paddleocr-api**: Structure created, needs code extraction (316 → ~180 lines)

## Directory Structure (Already Created)

```
edgnet-api/
├── models/        ✅ Created
├── services/      ✅ Created  
└── utils/         ✅ Created

skinmodel-api/
├── models/        ✅ Created
├── services/      ✅ Created
└── utils/         ✅ Created

paddleocr-api/
├── models/        ✅ Created
├── services/      ✅ Created
└── utils/         ✅ Created
```

## Refactoring Steps for Each API

### 1. edgnet-api (583 lines → ~250 lines)

**File**: `/home/uproot/ax/poc/edgnet-api/api_server.py`

#### Extract to `models/schemas.py`:
```python
class HealthResponse(BaseModel)       # Line 84-88
class SegmentRequest(BaseModel)       # Line 91-94
class ClassificationStats(BaseModel)  # Line 97-100
class GraphStats(BaseModel)           # Line 103-106
class SegmentResponse(BaseModel)      # Line 109-113
class VectorizeRequest(BaseModel)     # Line 116-117
class VectorizeResponse(BaseModel)    # Line 120-124
```

#### Extract to `utils/helpers.py`:
```python
allowed_file()                        # Line 131-133
bezier_to_bbox()                      # Line 136-164
cleanup_old_files()                   # Line 330-341
```

#### Extract to `services/segmentation.py`:
```python
class EDGNetSegmentationService:
    - load_pipeline()                 # Load EDGNet model
    - process_segmentation()          # Line 167-287
    - process_vectorization()         # Line 290-327
```

#### Update `Dockerfile`:
```dockerfile
COPY models/ ./models/
COPY services/ ./services/
COPY utils/ ./utils/
```

### 2. skinmodel-api (488 lines → ~220 lines)

**File**: `/home/uproot/ax/poc/skinmodel-api/api_server.py`

#### Extract to `models/schemas.py`:
- All Pydantic BaseModel classes
- ToleranceData, GeometricData, etc.

#### Extract to `utils/helpers.py`:
- File validation functions
- Cleanup functions
- Data conversion utilities

#### Extract to `services/tolerance_analyzer.py`:
```python
class SkinModelAnalyzer:
    - load_model()
    - analyze_tolerance()
    - compute_geometric_features()
```

#### Update `Dockerfile`:
```dockerfile
COPY models/ ./models/
COPY services/ ./services/
COPY utils/ ./utils/
```

### 3. paddleocr-api (316 lines → ~180 lines)

**File**: `/home/uproot/ax/poc/paddleocr-api/api_server.py`

#### Extract to `models/schemas.py`:
- All Pydantic BaseModel classes
- OCRResult, TextBlock, etc.

#### Extract to `utils/helpers.py`:
- Image preprocessing
- File validation
- Cleanup functions

#### Extract to `services/ocr_service.py`:
```python
class PaddleOCRService:
    - load_model()
    - detect_text()
    - recognize_text()
    - process_image()
```

#### Update `Dockerfile`:
```dockerfile
COPY models/ ./models/
COPY services/ ./services/
COPY utils/ ./utils/
```

## Testing Commands

After refactoring each API:

```bash
# Build the API
cd /home/uproot/ax/poc
docker-compose build edgnet-api

# Test the build
docker-compose build skinmodel-api

# Final build
docker-compose build paddleocr-api

# Build all at once (after all are refactored)
docker-compose build yolo-api edocr2-v2-api edgnet-api skinmodel-api paddleocr-api

# Start services
docker-compose up -d

# Test health endpoints
curl http://localhost:5005/api/v1/health  # yolo-api
curl http://localhost:5001/api/v2/health  # edocr2-v2-api
curl http://localhost:5002/api/v1/health  # edgnet-api
curl http://localhost:5003/api/v1/health  # skinmodel-api
curl http://localhost:5004/api/v1/health  # paddleocr-api
```

## Checklist for Each API

- [ ] Create `models/__init__.py` with exports
- [ ] Create `models/schemas.py` with all Pydantic models
- [ ] Create `services/__init__.py` with exports
- [ ] Create `services/{name}_service.py` with business logic class
- [ ] Create `utils/__init__.py` with exports
- [ ] Create `utils/helpers.py` with utility functions
- [ ] Update `api_server.py` with clean imports
- [ ] Update `Dockerfile` COPY commands
- [ ] Test build with `docker-compose build {api-name}`
- [ ] Verify line count reduction (should be ~50-60%)

## Expected Line Counts After Refactoring

| API | api_server.py | models/ | services/ | utils/ | Total |
|-----|---------------|---------|-----------|--------|-------|
| edgnet-api | ~250 | ~80 | ~200 | ~100 | ~630 |
| skinmodel-api | ~220 | ~60 | ~180 | ~80 | ~540 |
| paddleocr-api | ~180 | ~50 | ~150 | ~70 | ~450 |

## Pattern to Follow

Look at the completed refactorings as templates:

1. **yolo-api** - Best example for ML inference service
2. **edocr2-v2-api** - Best example for OCR service with GPU preprocessing

Use the same patterns:
- Service classes with `__init__` and methods
- Singleton pattern for global instances (`get_processor()`)
- Clean `__init__.py` exports
- Stateless utility functions

## Common Issues to Avoid

1. ❌ Don't forget to update imports in api_server.py
2. ❌ Don't miss the Dockerfile COPY commands
3. ❌ Don't put business logic in api_server.py
4. ❌ Don't forget `__all__` exports in `__init__.py`
5. ❌ Don't break existing functionality

## Time Estimate

- edgnet-api: 30-40 minutes
- skinmodel-api: 25-35 minutes
- paddleocr-api: 20-30 minutes
- **Total**: 1.5-2 hours

---

**Note**: The directory structures are already created. You just need to:
1. Read the current api_server.py
2. Extract code to appropriate files
3. Update imports
4. Update Dockerfile
5. Test build

Good luck! 🚀
