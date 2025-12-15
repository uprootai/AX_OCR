# Step-by-Step Migration Guide

## From Monolithic to Modular Architecture

This guide walks through migrating from `real_ai_app.py` (monolithic) to the modular architecture.

## Prerequisites

- Understanding of the monolithic codebase
- Python 3.9+
- Familiarity with Streamlit
- Basic knowledge of design patterns

## Migration Phases

### Phase 1: Analysis and Planning (Week 1)

#### 1.1 Code Analysis
```bash
# Analyze the monolithic file
wc -l real_ai_app.py  # Check size
grep "def " real_ai_app.py | wc -l  # Count methods
```

#### 1.2 Identify Components
- [ ] List all UI components
- [ ] List all business logic functions
- [ ] Identify data models
- [ ] Map dependencies

#### 1.3 Create Module Structure
```bash
mkdir -p app/{config,services,components,utils}
touch app/__init__.py
touch app/config/__init__.py
touch app/services/__init__.py
touch app/components/__init__.py
touch app/utils/__init__.py
```

### Phase 2: Configuration Extraction (Week 2)

#### 2.1 Create Settings Module
```python
# app/config/settings.py
from pydantic import BaseSettings, Field
from typing import Optional

class ModelSettings(BaseSettings):
    yolo_model_path: str = Field(default="models/yolo/best.pt")
    yolo11_model_path: str = Field(default="models/yolo/v11x/best.pt")
    confidence_threshold: float = Field(default=0.3)
    iou_threshold: float = Field(default=0.45)

class PathSettings(BaseSettings):
    uploads_dir: str = Field(default="uploads")
    results_dir: str = Field(default="results")
    test_drawings_dir: str = Field(default="test_drawings")
    pricing_json_path: str = Field(default="classes_info_with_pricing.json")

class UISettings(BaseSettings):
    app_title: str = Field(default="Drawing BOM Extractor")
    page_icon: str = Field(default="🎯")
    page_layout: str = Field(default="wide")
    sidebar_state: str = Field(default="expanded")

class Settings(BaseSettings):
    model: ModelSettings = Field(default_factory=ModelSettings)
    paths: PathSettings = Field(default_factory=PathSettings)
    ui: UISettings = Field(default_factory=UISettings)

settings = Settings()
```

#### 2.2 Replace Hardcoded Values
```python
# Before (monolithic)
confidence = 0.3
model_path = "models/yolo/best.pt"

# After (modular)
from app.config.settings import settings
confidence = settings.model.confidence_threshold
model_path = settings.model.yolo_model_path
```

### Phase 3: Service Layer Creation (Week 3-4)

#### 3.1 Extract Detection Service
```python
# app/services/detection_service.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import numpy as np

@dataclass
class Detection:
    """Detection result data class"""
    class_id: int
    class_name: str
    confidence: float
    bbox: List[float]
    model_id: str

class BaseDetector(ABC):
    """Abstract base for all detectors"""

    @abstractmethod
    def detect(self, image: np.ndarray) -> List[Detection]:
        """Perform detection on image"""
        pass

class YOLODetector(BaseDetector):
    """YOLO detector implementation"""

    def __init__(self, model_path: str, confidence: float = 0.3):
        self.model = YOLO(model_path)
        self.confidence = confidence

    def detect(self, image: np.ndarray) -> List[Detection]:
        results = self.model.predict(image, conf=self.confidence)
        return self._process_results(results)

class DetectionService:
    """Main detection service"""

    def __init__(self):
        self.detectors: Dict[str, BaseDetector] = {}

    def register_detector(self, name: str, detector: BaseDetector):
        self.detectors[name] = detector

    def detect_all(self, image: np.ndarray) -> Dict[str, List[Detection]]:
        results = {}
        for name, detector in self.detectors.items():
            results[name] = detector.detect(image)
        return results
```

#### 3.2 Extract BOM Service
```python
# app/services/bom_service.py
import pandas as pd
from typing import List, Dict

class BOMService:
    """BOM generation service"""

    def __init__(self, pricing_data_path: str):
        self.pricing_data = self._load_pricing_data(pricing_data_path)

    def create_bom(self, detections: List[Detection]) -> pd.DataFrame:
        """Create BOM from detections"""
        bom_data = []
        for detection in detections:
            if detection.status == 'approved':
                bom_data.append({
                    'Symbol': detection.class_name,
                    'Quantity': 1,
                    'Unit Price': self.get_price(detection.class_name),
                    'Total': self.get_price(detection.class_name)
                })
        return pd.DataFrame(bom_data)

    def get_price(self, class_name: str) -> float:
        """Get price for a class"""
        return self.pricing_data.get(class_name, {}).get('price', 0.0)
```

### Phase 4: Component Layer (Week 5)

#### 4.1 Create UI Components
```python
# app/components/file_uploader.py
import streamlit as st
from typing import Optional

class FileUploadComponent:
    """File upload UI component"""

    def __init__(self):
        self.allowed_types = ['pdf', 'png', 'jpg', 'jpeg']

    def render(self) -> Optional[UploadedFile]:
        """Render file upload widget"""
        uploaded_file = st.file_uploader(
            "📁 Upload Drawing",
            type=self.allowed_types,
            help="Upload CAD drawing or PDF"
        )
        return uploaded_file

    def process_file(self, file: UploadedFile) -> np.ndarray:
        """Convert uploaded file to image"""
        if file.type == "application/pdf":
            return self._process_pdf(file)
        else:
            return self._process_image(file)
```

#### 4.2 Symbol Verification Component
```python
# app/components/symbol_verification.py
class SymbolVerificationComponent:
    """Symbol verification UI"""

    def render_verification_ui(self, detections: List[Detection]):
        """Render verification interface"""
        st.subheader("🔍 Symbol Verification")

        for idx, detection in enumerate(detections):
            with st.container():
                col1, col2, col3, col4 = st.columns([1, 2, 1, 1])

                with col1:
                    # Show cropped image
                    st.image(detection.image_crop)

                with col2:
                    st.write(f"**Class**: {detection.class_name}")
                    st.write(f"**Confidence**: {detection.confidence:.2%}")

                with col3:
                    if st.button("✅", key=f"approve_{idx}"):
                        self._approve_detection(detection)

                with col4:
                    if st.button("❌", key=f"reject_{idx}"):
                        self._reject_detection(detection)
```

### Phase 5: Integration (Week 6)

#### 5.1 Create Main Application
```python
# app_modular.py
import streamlit as st
from app.config.settings import settings
from app.services.detection_service import DetectionService
from app.services.bom_service import BOMService
from app.components.file_uploader import FileUploadComponent

class DrawingBOMExtractorApp:
    """Main application orchestrator"""

    def __init__(self):
        self.settings = settings
        self._init_services()
        self._init_components()

    def _init_services(self):
        """Initialize services with caching"""
        self.detection_service = get_detection_service()
        self.bom_service = get_bom_service()

    def _init_components(self):
        """Initialize UI components"""
        self.file_uploader = FileUploadComponent()
        self.symbol_verification = SymbolVerificationComponent()

    def run(self):
        """Run application"""
        self.render_sidebar()
        self.render_main_workflow()

@st.cache_resource
def get_detection_service():
    """Get cached detection service"""
    return DetectionService()

@st.cache_resource
def get_bom_service():
    """Get cached BOM service"""
    return BOMService(settings.paths.pricing_json_path)

def main():
    app = DrawingBOMExtractorApp()
    app.run()

if __name__ == "__main__":
    main()
```

### Phase 6: Testing (Week 7)

#### 6.1 Create Unit Tests
```python
# tests/test_detection_service.py
import pytest
from app.services.detection_service import DetectionService, YOLODetector

def test_detection_service_registration():
    service = DetectionService()
    detector = YOLODetector("test_model.pt")

    service.register_detector("test", detector)
    assert "test" in service.detectors

def test_detection_service_detect_all():
    service = DetectionService()
    mock_image = np.zeros((640, 640, 3))

    results = service.detect_all(mock_image)
    assert isinstance(results, dict)
```

#### 6.2 Integration Tests
```python
# tests/test_integration.py
def test_full_workflow():
    """Test complete detection workflow"""
    app = DrawingBOMExtractorApp()

    # Load test image
    test_image = load_test_image()

    # Run detection
    results = app.detection_service.detect_all(test_image)

    # Verify results
    assert len(results) > 0

    # Generate BOM
    bom = app.bom_service.create_bom(results)
    assert not bom.empty
```

### Phase 7: Migration Validation (Week 8)

#### 7.1 Feature Parity Check
```python
# validation/feature_parity.py
def validate_features():
    """Ensure all features work in both versions"""

    features = [
        "file_upload",
        "model_selection",
        "detection_execution",
        "symbol_verification",
        "bom_generation",
        "excel_export"
    ]

    for feature in features:
        monolithic_result = test_monolithic(feature)
        modular_result = test_modular(feature)
        assert monolithic_result == modular_result
```

#### 7.2 Performance Comparison
```python
# validation/performance.py
import time

def benchmark_detection():
    """Compare detection performance"""

    # Monolithic
    start = time.time()
    run_monolithic_detection()
    monolithic_time = time.time() - start

    # Modular
    start = time.time()
    run_modular_detection()
    modular_time = time.time() - start

    print(f"Monolithic: {monolithic_time:.2f}s")
    print(f"Modular: {modular_time:.2f}s")
    print(f"Improvement: {(1 - modular_time/monolithic_time)*100:.1f}%")
```

## Migration Checklist

### Pre-Migration
- [ ] Backup current code
- [ ] Document current features
- [ ] Create test cases
- [ ] Set up development environment

### During Migration
- [ ] Extract configuration
- [ ] Create service layer
- [ ] Build components
- [ ] Implement caching
- [ ] Add error handling
- [ ] Write tests

### Post-Migration
- [ ] Validate feature parity
- [ ] Performance testing
- [ ] User acceptance testing
- [ ] Documentation update
- [ ] Deployment preparation

## Common Pitfalls and Solutions

### 1. Session State Management
**Problem**: Streamlit reruns cause state loss
**Solution**: Use proper session state initialization
```python
if 'detection_results' not in st.session_state:
    st.session_state.detection_results = {}
```

### 2. Circular Dependencies
**Problem**: Modules import each other
**Solution**: Use dependency injection
```python
# Instead of direct imports
class Service:
    def __init__(self, dependency):
        self.dependency = dependency
```

### 3. Cache Invalidation
**Problem**: Cached data becomes stale
**Solution**: Use cache keys and TTL
```python
@st.cache_data(ttl=3600)  # 1 hour TTL
def load_data(version: str):
    return fetch_data()
```

### 4. Performance Regression
**Problem**: Modular version slower
**Solution**: Profile and optimize
```python
import cProfile
cProfile.run('app.run()')
```

## Success Metrics

### Code Quality
- [ ] Cyclomatic complexity < 10
- [ ] Method length < 50 lines
- [ ] Test coverage > 80%
- [ ] No circular dependencies

### Performance
- [ ] Startup time < 3 seconds
- [ ] Detection time same or better
- [ ] Memory usage reduced by 30%
- [ ] Cache hit rate > 90%

### Maintainability
- [ ] New feature addition < 2 hours
- [ ] Bug fix time reduced by 50%
- [ ] Onboarding time < 1 day
- [ ] Code review time < 30 minutes

## Resources

- [Modular Architecture Documentation](../modular/architecture.md)
- [Service Layer Patterns](../modular/services.md)
- [Component Guidelines](../modular/components.md)
- [Testing Best Practices](../deployment/testing.md)

## Support

For questions during migration:
1. Check the [FAQ](faq.md)
2. Review [Common Issues](../deployment/troubleshooting.md)
3. Contact the development team

---

*Estimated Total Migration Time: 8 weeks*
*Team Size Recommendation: 2-3 developers*