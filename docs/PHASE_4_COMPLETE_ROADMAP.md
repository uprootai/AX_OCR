# 🗺️ Phase 4 Complete Roadmap

**BlueprintFlow Parameter Expansion & Backend Integration**

**Last Updated**: 2025-11-21
**Current Status**: Phase 4A ✅ Complete, Phase 4B ⏳ Pending

---

## 📊 Overall Progress

| Phase | Status | Completion | Lines Added | Time |
|-------|--------|------------|-------------|------|
| **Phase 4A** | ✅ Complete | 100% | +195 lines | ~30 min |
| **Phase 4B** | ⏳ Pending | 0% | ~440 lines | ~2-3 hours |
| **Phase 4C** | ⏳ Pending | 0% | ~200 lines | ~1-2 hours |
| **Phase 4D** | ⏳ Pending | 0% | ~100 lines | ~1 hour |

**Total Estimated**: ~835 lines, 4-6 hours

---

## ✅ Phase 4A: Frontend Parameter Overhaul (COMPLETE)

### Summary
**Goal**: Expose all API parameters in BlueprintFlow UI
**Result**: 4 params → 31 params (+675% increase)

### Completed Work

#### File Modified
**`web-ui/src/config/nodeDefinitions.ts`**
- Before: 398 lines
- After: 593 lines
- Change: +195 lines (+49%)

#### API Coverage Improvements

| API | Before | After | Parameters Added |
|-----|--------|-------|------------------|
| **eDOCr2** | 0 params (0%) | 7 params (100%) | version, extract_dimensions, extract_gdt, extract_text, use_vl_model, visualize, use_gpu_preprocessing |
| **SkinModel** | 0 params (0%) | 4 params (100%) | material, manufacturing_process, correlation_length, task |
| **VL** | 0 params (0%) | 4 params (100%) | model, task, query_fields, temperature |
| **YOLO** | 2 params (33%) | 6 params (100%) | model_type (5 specialized models), confidence, iou_threshold, imgsz, visualize, task |
| **PaddleOCR** | 1 param (25%) | 5 params (100%) | lang (expanded), det_db_thresh, det_db_box_thresh, use_angle_cls, min_confidence |
| **EDGNet** | 1 param (25%) | 5 params (100%) | model (graphsage/unet), num_classes, visualize, save_graph, vectorize |

#### Key Improvements
1. **YOLO**: 5 specialized models (symbol, dimension, GD&T, text-region, general)
2. **eDOCr2**: Selective extraction flags (speed optimization)
3. **VL**: 4 model choices (Claude, GPT-4o, GPT-4 Turbo, Gemini)
4. **SkinModel**: Material/process-aware tolerance analysis
5. **PaddleOCR**: Rotated text detection
6. **EDGNet**: UNet model option, DXF vectorization

### Verification
- ✅ File saved correctly
- ✅ Build successful
- ✅ UI displays all 31 parameters
- ✅ Dev server (port 5174) working
- ✅ User confirmed: "정상이네요"

### Documentation Created
- `docs/PHASE_4A_COMPLETION_REPORT.md` (252 lines)
- `docs/PHASE_4A_FINAL_SUMMARY.md` (340 lines)
- `docs/api/yolo/parameters.md` (90 lines)
- `docs/api/edocr2/parameters.md` (94 lines)
- `docs/api/edgnet/parameters.md` (91 lines)
- `docs/api/skinmodel/parameters.md` (84 lines)
- `docs/api/paddleocr/parameters.md` (99 lines)
- `docs/api/vl/parameters.md` (94 lines)

---

## ⏳ Phase 4B: Backend API Integration (PENDING)

### Summary
**Goal**: Modify backend APIs to handle new parameters
**Estimated Time**: 2-3 hours
**Estimated LOC**: ~440 lines

### Tasks by Priority

#### Priority 1: Critical APIs (Immediate Impact)

##### 1. eDOCr2 API ⭐ (Highest Impact)
**File**: `models/edocr2-v2-api/api_server.py`
**Lines**: ~100 lines
**Difficulty**: Medium

**Changes**:
```python
# Add to endpoint
@app.post("/api/v2/ocr")
async def process_drawing(
    file: UploadFile,
    version: str = "ensemble",              # NEW
    extract_dimensions: bool = True,        # NEW
    extract_gdt: bool = True,               # NEW
    extract_text: bool = True,              # NEW
    use_vl_model: bool = False,             # NEW
    visualize: bool = False,                # NEW
    use_gpu_preprocessing: bool = False     # NEW
)
```

**Implementation Steps**:
1. Add parameters to endpoint
2. Implement version selection (v1/v2/ensemble)
3. Add conditional extraction logic
4. Implement GPU preprocessing (CLAHE, denoising)
5. Add VL model fallback option
6. Update response format

**Expected Benefit**: Processing time -53% (1.5s → 0.7s with selective extraction)

---

##### 2. YOLO API ⭐ (Model Diversification)
**File**: `models/yolo-api/api_server.py`
**Lines**: ~120 lines
**Difficulty**: High (requires model files)

**Changes**:
```python
# Model mapping
MODEL_FILES = {
    'symbol-detector-v1': 'weights/symbol_v1.pt',
    'dimension-detector-v1': 'weights/dimension_v1.pt',
    'gdt-detector-v1': 'weights/gdt_v1.pt',
    'text-region-detector-v1': 'weights/text_region_v1.pt',
    'yolo11n-general': 'weights/yolo11n.pt'
}

@app.post("/api/v1/detect")
async def detect_objects(
    file: UploadFile,
    model_type: str = "symbol-detector-v1",  # NEW
    confidence: float = 0.5,
    iou_threshold: float = 0.45,             # NEW
    imgsz: int = 640,                        # NEW
    visualize: bool = True,                  # NEW
    task: str = "detect"                     # NEW
)
```

**Implementation Steps**:
1. Add model loading logic (5 models)
2. Add iou_threshold parameter to YOLO
3. Add imgsz parameter
4. Add task parameter (detect vs segment)
5. Update visualization logic

**Critical Issue**: Model files needed
- ✅ `yolo11n.pt` already exists
- ❌ 4 specialized models need training

**Temporary Solution**:
```python
# Use general model for all types initially
MODEL_FILES = {
    'symbol-detector-v1': 'weights/yolo11n.pt',      # Temporary
    'dimension-detector-v1': 'weights/yolo11n.pt',   # Temporary
    'gdt-detector-v1': 'weights/yolo11n.pt',         # Temporary
    'text-region-detector-v1': 'weights/yolo11n.pt', # Temporary
    'yolo11n-general': 'weights/yolo11n.pt'
}
```

**Expected Benefit**: Accuracy +20-32% (when specialized models trained)

---

#### Priority 2: High Value APIs

##### 3. SkinModel API
**File**: `models/skinmodel-api/api_server.py`
**Lines**: ~80 lines
**Difficulty**: Medium

**Changes**:
```python
@app.post("/api/v1/analyze_tolerance")
async def analyze_tolerance(
    ocr_results: dict,
    material: str = "steel",                      # NEW
    manufacturing_process: str = "machining",     # NEW
    correlation_length: float = 1.0,              # NEW
    task: str = "tolerance"                       # NEW
)
```

**Implementation Steps**:
1. Add material property lookup table
2. Add manufacturing process tolerance tables
3. Implement correlation_length in Random Field model
4. Add task branching (tolerance/validate/manufacturability)

**Expected Benefit**: Accuracy +20% (75% → 90%)

---

##### 4. VL API
**File**: `models/vl-api/api_server.py`
**Lines**: ~120 lines
**Difficulty**: Medium

**Changes**:
```python
@app.post("/api/v1/vl_analyze")
async def vl_analyze(
    file: UploadFile,
    model: str = "claude-3-5-sonnet-20241022",    # NEW
    task: str = "extract_info_block",             # NEW
    query_fields: str = '["name", "material"]',   # NEW
    temperature: float = 0.0                      # NEW
)
```

**Implementation Steps**:
1. Add multi-model support (Claude, GPT-4o, GPT-4 Turbo, Gemini)
2. Implement 4 task types
3. Add query_fields JSON parsing
4. Add temperature parameter to LLM calls

**Expected Benefit**: 4 specialized tasks vs 1 generic

---

#### Priority 3: Enhancement APIs

##### 5. PaddleOCR API
**File**: `models/paddleocr-api/api_server.py`
**Lines**: ~60 lines
**Difficulty**: Low

**Changes**:
```python
@app.post("/api/v1/ocr")
async def paddle_ocr(
    file: UploadFile,
    lang: str = "en",
    det_db_thresh: float = 0.3,          # NEW
    det_db_box_thresh: float = 0.5,      # NEW
    use_angle_cls: bool = True,          # NEW
    min_confidence: float = 0.5          # NEW
)
```

**Implementation Steps**:
1. Pass det_db_thresh to PaddleOCR detector
2. Pass det_db_box_thresh
3. Enable/disable angle classifier
4. Filter results by confidence

**Expected Benefit**: Rotated text detection enabled

---

##### 6. EDGNet API
**File**: `models/edgnet-api/api_server.py`
**Lines**: ~80 lines
**Difficulty**: Medium

**Changes**:
```python
@app.post("/api/v1/segment")
async def segment_edges(
    file: UploadFile,
    model: str = "graphsage",         # NEW
    num_classes: int = 3,             # NEW
    visualize: bool = True,           # NEW
    save_graph: bool = False,         # NEW
    vectorize: bool = False           # NEW
)
```

**Implementation Steps**:
1. Add UNet model loading
2. Add num_classes parameter
3. Implement DXF vectorization (Bezier curves)
4. Add graph JSON export

**Expected Benefit**: UNet model option, DXF export

---

## ⏳ Phase 4C: Post-Processing Nodes (PENDING)

### Summary
**Goal**: Add 3 new post-processing nodes for pipeline optimization
**Estimated Time**: 1-2 hours
**Estimated LOC**: ~200 lines

### New Nodes

#### 1. BackgroundRemoval Node
**File**: `web-ui/src/components/blueprintflow/nodes/PostProcessNodes.tsx`
**Lines**: ~60 lines

**Functionality**:
- Remove background noise from images
- OpenCV-based implementation
- Parameter: `threshold` (0-255)

**Use Case**: Before OCR to improve accuracy

---

#### 2. CropAndScale Node
**File**: Same as above
**Lines**: ~70 lines

**Functionality**:
- Crop BBox regions from YOLO detections
- Scale up for small text recognition
- Parameters: `scale_factor` (1.0-3.0), `padding` (0-50px)

**Use Case**: Individual object OCR with zoom

---

#### 3. BatchOCR Node
**File**: Same as above
**Lines**: ~70 lines

**Functionality**:
- Process multiple regions simultaneously
- Parallel OCR calls
- Parameter: `batch_size` (1-32)

**Use Case**: Speed up multi-object OCR

---

### Integration
- Add to `nodeDefinitions.ts` (+30 lines)
- Update NodePalette (+20 lines)
- Create backend endpoints (+80 lines)

---

## ⏳ Phase 4D: Advanced Templates (PENDING)

### Summary
**Goal**: Add 4 specialized workflow templates
**Estimated Time**: 1 hour
**Estimated LOC**: ~100 lines

### New Templates

#### Template 5: Symbol Recognition Pipeline
**Workflow**:
```
YOLO (symbol-detector-v1)
  → Loop
    → CropAndScale (2x)
    → eDOCr2 (extract_text only)
  → Merge
```

**Target**: Welding symbols, bearings, gears (F1: 92%)

---

#### Template 6: Dimension Extraction Pipeline
**Workflow**:
```
YOLO (dimension-detector-v1)
  → Loop
    → CropAndScale (3x)
    → eDOCr2 (extract_dimensions only)
  → SkinModel (tolerance analysis)
```

**Target**: Dimension text regions (F1: 88%)

---

#### Template 7: GD&T Analysis Pipeline
**Workflow**:
```
YOLO (gdt-detector-v1)
  → Loop
    → eDOCr2 (extract_gdt only)
  → SkinModel (validate task)
```

**Target**: Geometric tolerance symbols (F1: 85%)

---

#### Template 8: English Drawing Pipeline
**Workflow**:
```
YOLO (text-region-detector-v1)
  → BackgroundRemoval
  → PaddleOCR (lang=en, use_angle_cls=true)
  → VL (Claude 3.5, extract_info_block)
```

**Target**: Overseas manufacturer drawings (F1: 90%)

---

## 🎯 Implementation Strategy

### Recommended Order

#### Week 1: Critical APIs (Phase 4B - Priority 1)
**Day 1-2**: eDOCr2 API
- Highest immediate impact
- No model training needed
- Speed improvement: -53%

**Day 3-4**: YOLO API (with temporary general model)
- Implement parameter handling
- Use `yolo11n.pt` for all model types initially
- Plan specialized model training

**Day 5**: Testing & Documentation

---

#### Week 2: Enhancement APIs (Phase 4B - Priority 2-3)
**Day 1**: SkinModel API
**Day 2**: VL API
**Day 3**: PaddleOCR API
**Day 4**: EDGNet API
**Day 5**: Integration testing

---

#### Week 3: Post-Processing & Templates (Phase 4C-D)
**Day 1-2**: Post-processing nodes
**Day 3**: Advanced templates
**Day 4-5**: End-to-end testing

---

#### Future: Model Training (Phase 4E)
**Requires**:
- 2,000+ labeled drawings
- GPU training time: ~2-3 days per model
- 4 models × 3 days = ~12 days

**Models**:
1. symbol-detector-v1 (2,000 samples)
2. dimension-detector-v1 (1,500 samples)
3. gdt-detector-v1 (800 samples)
4. text-region-detector-v1 (1,200 samples)

---

## 📝 Testing Checklist

### Phase 4B Testing
- [ ] eDOCr2: Test selective extraction (dimensions only, GD&T only, etc.)
- [ ] eDOCr2: Test GPU preprocessing
- [ ] YOLO: Test all 5 model types (even with same weights)
- [ ] YOLO: Test iou_threshold, imgsz parameters
- [ ] SkinModel: Test material/process combinations
- [ ] VL: Test all 4 model choices
- [ ] VL: Test all 4 task types
- [ ] PaddleOCR: Test rotated text detection
- [ ] EDGNet: Test UNet model, vectorization

### Phase 4C Testing
- [ ] BackgroundRemoval: Test with noisy images
- [ ] CropAndScale: Test with YOLO detections
- [ ] BatchOCR: Test parallel processing

### Phase 4D Testing
- [ ] Template 5: Test symbol recognition workflow
- [ ] Template 6: Test dimension extraction workflow
- [ ] Template 7: Test GD&T analysis workflow
- [ ] Template 8: Test English drawing workflow

---

## 📊 Expected Performance Impact

### Speed Improvements
| Optimization | Before | After | Improvement |
|--------------|--------|-------|-------------|
| **Selective eDOCr2** | 1.5s | 0.7s | -53% |
| **Batch OCR** | N × 0.3s | 0.5s | -80% (N=10) |
| **Background Removal** | - | +0.1s | +15% accuracy |

### Accuracy Improvements
| API | Before | After | Improvement |
|-----|--------|-------|-------------|
| **YOLO (specialized)** | 60% | 85-92% | +20-32% |
| **SkinModel (material-aware)** | 75% | 90% | +20% |
| **PaddleOCR (rotated text)** | 70% | 85% | +15% |

### Functionality Improvements
| Feature | Before | After | Increase |
|---------|--------|-------|----------|
| **API Parameters** | 4 | 31 | +675% |
| **YOLO Models** | 1 general | 5 specialized | +400% |
| **VL Tasks** | 1 generic | 4 specialized | +300% |
| **Templates** | 4 basic | 8 optimized | +100% |

---

## 🚨 Known Issues & Mitigation

### Issue 1: YOLO Specialized Models Missing
**Problem**: 4 specialized models not trained yet
**Impact**: Can't achieve full accuracy improvement
**Mitigation**:
- Use general model temporarily
- Plan training schedule (Week 4+)
- Document expected vs actual performance

### Issue 2: GPU Preprocessing Not Implemented
**Problem**: `use_gpu_preprocessing` requires CUDA setup
**Impact**: Can't achieve +15% accuracy boost
**Mitigation**:
- Implement CPU version first
- Add GPU version when available
- Make it optional

### Issue 3: DXF Vectorization Complex
**Problem**: Bezier curve fitting requires research
**Impact**: EDGNet `vectorize` may take longer
**Mitigation**:
- Implement basic polyline export first
- Enhance to Bezier curves later

---

## 📚 Documentation Requirements

### For Each Phase
- [ ] Update API documentation
- [ ] Add code examples
- [ ] Update CHANGELOG.md
- [ ] Update README.md
- [ ] Create migration guide if needed

### Final Documentation
- [ ] Complete API reference
- [ ] Performance benchmarks
- [ ] Best practices guide
- [ ] Troubleshooting guide

---

## ✅ Success Criteria

### Phase 4B Success
- [ ] All 6 APIs accept new parameters without errors
- [ ] Backward compatibility maintained (old clients still work)
- [ ] Docker rebuild successful
- [ ] All endpoints return valid responses
- [ ] Performance metrics meet expectations

### Phase 4C Success
- [ ] 3 post-processing nodes functional
- [ ] Can be chained in workflows
- [ ] Performance overhead acceptable (<200ms per node)

### Phase 4D Success
- [ ] 4 new templates work end-to-end
- [ ] Performance better than basic templates
- [ ] Accuracy improvements measurable

---

## 🎖️ Completion Milestones

| Milestone | Target Date | Status |
|-----------|-------------|--------|
| Phase 4A: Frontend Complete | 2025-11-21 | ✅ Done |
| Phase 4B: Backend APIs | TBD | ⏳ Pending |
| Phase 4C: Post-Processing | TBD | ⏳ Pending |
| Phase 4D: Templates | TBD | ⏳ Pending |
| Phase 4E: Model Training | TBD | ⏳ Future |

---

**Next Action**: Choose which Phase 4B API to implement first

**Recommended**: Start with eDOCr2 (highest impact, no model training needed)
