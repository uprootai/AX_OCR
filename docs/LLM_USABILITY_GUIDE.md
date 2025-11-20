# LLM 사용성 가이드 (LLM Usability Guide)

**Date**: 2025-11-19
**Purpose**: LLM이 이 코드베이스를 쉽게 이해하고 수정할 수 있도록 하는 가이드

---

## 📚 Table of Contents

1. [프로젝트 구조 이해하기](#1-프로젝트-구조-이해하기)
2. [모듈별 역할](#2-모듈별-역할)
3. [일반적인 작업 패턴](#3-일반적인-작업-패턴)
4. [코드 탐색 전략](#4-코드-탐색-전략)
5. [수정 시 주의사항](#5-수정-시-주의사항)
6. [테스트 방법](#6-테스트-방법)

---

## 1. 프로젝트 구조 이해하기

### 1.1 Overall Architecture

```
/home/uproot/ax/poc/
├── gateway-api/          ← 메인 오케스트레이터
├── yolo-api/            ← 객체 검출
├── edocr2-v2-api/       ← OCR 서비스
├── edgnet-api/          ← 세그멘테이션
├── skinmodel-api/       ← 공차 분석
└── paddleocr-api/       ← 보조 OCR
```

### 1.2 Standardized API Structure

**모든 API가 동일한 구조를 따릅니다**:

```
{api-name}/
├── api_server.py          ← FastAPI endpoints (200-350 lines)
├── models/
│   ├── __init__.py        ← Exports
│   └── schemas.py         ← Pydantic models (30-80 lines)
├── services/
│   ├── __init__.py        ← Exports
│   └── {service}.py       ← Business logic (150-250 lines)
├── utils/
│   ├── __init__.py        ← Exports
│   └── helpers.py         ← Utility functions (70-100 lines)
├── Dockerfile
└── requirements.txt
```

**이 구조의 장점**:
- ✅ 어느 API든 동일한 방식으로 탐색 가능
- ✅ models/ → 데이터 구조 확인
- ✅ services/ → 비즈니스 로직 확인
- ✅ utils/ → 헬퍼 함수 확인
- ✅ api_server.py → 엔드포인트만 확인

---

## 2. 모듈별 역할

### 2.1 models/schemas.py

**Purpose**: Pydantic 데이터 모델 정의

**What you'll find**:
- Request models (API 입력)
- Response models (API 출력)
- Internal data structures

**Example** (yolo-api/models/schemas.py):
```python
class Detection(BaseModel):
    """단일 검출 결과"""
    class_id: int = Field(..., description="클래스 ID (0-13)")
    class_name: str = Field(..., description="클래스 이름")
    confidence: float = Field(..., description="신뢰도 (0-1)")
    bbox: Dict[str, int] = Field(..., description="바운딩 박스")
```

**When to modify**:
- 새로운 필드 추가
- 타입 변경
- Validation 규칙 추가

**LLM Tip**:
- 파일 크기: 30-80 lines
- 읽기 시간: 3-5초
- 명확한 Field descriptions 제공

---

### 2.2 services/{service}.py

**Purpose**: 비즈니스 로직 구현

**What you'll find**:
- ML 모델 추론
- API 호출 로직
- 데이터 처리 파이프라인

**Example** (yolo-api/services/inference.py):
```python
class YOLOInferenceService:
    """YOLO 추론 서비스"""

    def __init__(self):
        self.model = None
        self.device = None

    def load_model(self, model_path: str):
        """모델 로드"""
        self.model = YOLO(model_path)

    def predict(
        self,
        image_bytes: bytes,
        conf_threshold: float = 0.25
    ) -> Dict[str, Any]:
        """객체 검출 수행"""
        # Implementation
```

**When to modify**:
- 모델 추론 로직 변경
- 파라미터 조정
- 후처리 로직 수정

**LLM Tip**:
- 파일 크기: 150-250 lines
- 읽기 시간: 10-15초
- 클래스 기반 구조로 명확함

---

### 2.3 utils/helpers.py

**Purpose**: 재사용 가능한 헬퍼 함수

**What you'll find**:
- 이미지 인코딩/디코딩
- 파일 I/O
- 데이터 변환

**Example** (yolo-api/utils/helpers.py):
```python
def decode_image(image_bytes: bytes) -> np.ndarray:
    """바이트를 NumPy 이미지로 변환"""
    nparr = np.frombuffer(image_bytes, np.uint8)
    return cv2.imdecode(nparr, cv2.IMREAD_COLOR)

def encode_image_to_base64(image: np.ndarray) -> str:
    """NumPy 이미지를 Base64로 인코딩"""
    _, buffer = cv2.imencode('.jpg', image)
    return base64.b64encode(buffer).decode('utf-8')
```

**When to modify**:
- 새로운 유틸리티 함수 추가
- 기존 함수 최적화

**LLM Tip**:
- 파일 크기: 70-100 lines
- 읽기 시간: 5-8초
- 순수 함수로 테스트 쉬움

---

### 2.4 api_server.py

**Purpose**: FastAPI 엔드포인트 정의

**What you'll find**:
- @app.post() 데코레이터
- 엔드포인트 함수
- Request validation
- Response formatting

**Example** (yolo-api/api_server.py):
```python
from models import Detection, DetectionResponse
from services import YOLOInferenceService
from utils import decode_image

yolo_service = YOLOInferenceService()

@app.post("/api/v1/detect", response_model=DetectionResponse)
async def detect_objects(
    file: UploadFile = File(...),
    conf_threshold: float = Form(0.25)
):
    """객체 검출 API"""
    image_bytes = await file.read()
    results = yolo_service.predict(image_bytes, conf_threshold)
    return results
```

**When to modify**:
- 새 엔드포인트 추가
- 파라미터 변경
- Response 형식 변경

**LLM Tip**:
- 파일 크기: 200-350 lines
- 읽기 시간: 15-20초
- 엔드포인트만 정의, 로직은 services/에

---

## 3. 일반적인 작업 패턴

### 3.1 새로운 기능 추가

**Scenario**: Tesseract OCR 엔진 추가

**Step 1**: Create service module
```bash
# File: gateway-api/services/tesseract_service.py
async def call_tesseract_ocr(
    image_bytes: bytes,
    lang: str = "eng"
) -> Dict[str, Any]:
    """Tesseract OCR API 호출"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{TESSERACT_API_URL}/api/v1/ocr",
            files={"file": ("image.jpg", image_bytes, "image/jpeg")},
            data={"lang": lang}
        )
        return response.json()
```

**Step 2**: Export from __init__.py
```python
# File: gateway-api/services/__init__.py
from .tesseract_service import call_tesseract_ocr

__all__ = [
    # ... existing exports
    "call_tesseract_ocr"
]
```

**Step 3**: Add response model
```python
# File: gateway-api/models/response.py
class TesseractResults(BaseModel):
    text: str
    confidence: float
    language: str
```

**Step 4**: Use in api_server.py
```python
# File: gateway-api/api_server.py
from services import call_tesseract_ocr

@app.post("/api/v1/process")
async def process_drawing(...):
    # ... existing code
    tesseract_results = await call_tesseract_ocr(file_bytes)
    # ...
```

**Files modified**: 4 (services/tesseract_service.py, services/__init__.py, models/response.py, api_server.py)
**Total lines**: ~150

---

### 3.2 기존 기능 수정

**Scenario**: YOLO confidence threshold 기본값 변경

**Step 1**: Locate the service
```bash
grep -r "conf_threshold" yolo-api/services/
# Result: yolo-api/services/inference.py:145
```

**Step 2**: Modify the function
```python
# File: yolo-api/services/inference.py (Line 145)
def predict(
    self,
    image_bytes: bytes,
    conf_threshold: float = 0.30,  # Changed from 0.25
    iou_threshold: float = 0.7,
    imgsz: int = 1280,
    visualize: bool = True
) -> Dict[str, Any]:
```

**Step 3**: Update tests (if any)
```python
# File: tests/test_yolo_service.py
def test_default_confidence():
    service = YOLOInferenceService()
    result = service.predict(test_image)
    assert result["conf_threshold"] == 0.30  # Updated
```

**Files modified**: 2 (services/inference.py, tests/)
**Total lines**: ~3

---

### 3.3 기능 삭제

**Scenario**: PaddleOCR 제거

**Step 1**: Delete service file
```bash
rm gateway-api/services/paddleocr_service.py
```

**Step 2**: Remove from __init__.py
```python
# File: gateway-api/services/__init__.py
# Remove: from .paddleocr_service import call_paddleocr_detect
```

**Step 3**: Remove from models
```python
# File: gateway-api/models/response.py
# Remove: class PaddleOCRResults(BaseModel): ...
```

**Step 4**: Remove from api_server.py
```python
# File: gateway-api/api_server.py
# Remove: from services import call_paddleocr_detect
# Remove: paddleocr_results = await call_paddleocr_detect(...)
```

**Step 5**: Verify no remaining references
```bash
grep -r "paddleocr" gateway-api/
# Should return empty
```

**Files modified**: 4
**Total lines removed**: ~150

---

### 3.4 코드 이해/조회

**Scenario**: "YOLO가 어떤 클래스를 검출하나요?"

**Method 1**: Read models
```bash
# Read: yolo-api/models/schemas.py (45 lines)
# Look for: Detection class, class_name field
```

**Method 2**: Read service
```bash
# Read: yolo-api/services/inference.py (189 lines)
# Look for: CLASSES or class_names variable
```

**Method 3**: Grep
```bash
grep -r "class_name" yolo-api/
```

**LLM Tip**:
- 데이터 구조 질문 → models/schemas.py
- 로직 질문 → services/{service}.py
- 엔드포인트 질문 → api_server.py

---

## 4. 코드 탐색 전략

### 4.1 Top-Down Approach

**Use when**: "전체 시스템이 어떻게 작동하나요?"

1. Read: `REFACTORING_COMPLETE.md` (전체 구조 파악)
2. Read: `gateway-api/api_server.py` (main endpoints)
3. Read: `gateway-api/services/` (각 서비스 역할)
4. Read: `{specific-api}/` (관심 있는 API)

**Example**:
```
Q: "도면 처리 파이프라인이 어떻게 되나요?"
A:
1. Read REFACTORING_COMPLETE.md → "하이브리드 파이프라인" 확인
2. Read gateway-api/api_server.py → POST /api/v1/process 확인
3. Read services/yolo_service.py → YOLO 호출 확인
4. Read services/ocr_service.py → OCR 호출 확인
```

---

### 4.2 Bottom-Up Approach

**Use when**: "특정 함수가 어디서 사용되나요?"

1. Grep for function name
2. Read caller files
3. Understand context

**Example**:
```
Q: "crop_bbox 함수가 어디서 사용되나요?"
A:
1. grep -r "crop_bbox" gateway-api/
   → services/ensemble_service.py:142
   → utils/image_utils.py:23 (definition)
2. Read ensemble_service.py → YOLO Crop OCR에서 사용
3. Read image_utils.py → bbox 자르고 upscale하는 함수
```

---

### 4.3 Data Flow Tracking

**Use when**: "데이터가 어떻게 변환되나요?"

1. Read request model
2. Read service logic
3. Read response model

**Example**:
```
Q: "업로드된 이미지가 어떻게 YOLO 결과로 변환되나요?"
A:
1. models/schemas.py → DetectionResponse 구조 확인
2. services/inference.py → predict() 함수 로직 확인
   - decode_image() → NumPy array
   - model.predict() → YOLO results
   - parse_results() → DetectionResponse
3. utils/helpers.py → decode_image() 구현 확인
```

---

## 5. 수정 시 주의사항

### 5.1 Import 순환 방지

**Rule**: `models` → `utils` → `services` → `api_server`

**DO**:
```python
# services/yolo_service.py
from models import Detection  # ✅ OK
from utils import decode_image  # ✅ OK
```

**DON'T**:
```python
# models/schemas.py
from services import YOLOInferenceService  # ❌ NO! Circular import
```

---

### 5.2 Pydantic Model 수정

**When adding field**:
```python
# BEFORE
class Detection(BaseModel):
    class_id: int
    class_name: str

# AFTER (with default)
class Detection(BaseModel):
    class_id: int
    class_name: str
    color: str = "blue"  # ✅ Default value for backward compatibility
```

**When removing field**:
```python
# BEFORE
class Detection(BaseModel):
    class_id: int
    class_name: str
    deprecated_field: str  # ← Remove this

# AFTER (Step 1: Make optional)
class Detection(BaseModel):
    class_id: int
    class_name: str
    deprecated_field: Optional[str] = None  # ← First make optional

# AFTER (Step 2: Remove completely after migration)
class Detection(BaseModel):
    class_id: int
    class_name: str
    # deprecated_field removed
```

---

### 5.3 Service 함수 수정

**Rule**: 함수 signature 변경 시 모든 caller 확인

**Example**:
```python
# BEFORE
def predict(image_bytes: bytes, conf_threshold: float = 0.25):
    pass

# AFTER (adding parameter)
def predict(
    image_bytes: bytes,
    conf_threshold: float = 0.25,
    new_param: str = "default"  # ✅ Default value
):
    pass
```

**Verification**:
```bash
# Find all callers
grep -r "predict(" yolo-api/
# Update each caller if needed
```

---

### 5.4 Docker 관련 수정

**When adding new file**:
```dockerfile
# Dockerfile
COPY models/ ./models/
COPY services/ ./services/
COPY utils/ ./utils/
COPY new_module/ ./new_module/  # ← Add this
```

**When adding dependency**:
```txt
# requirements.txt
fastapi==0.104.1
uvicorn==0.24.0
new-package==1.0.0  # ← Add this
```

**Rebuild**:
```bash
docker-compose build {service-name}
docker-compose up -d {service-name}
```

---

## 6. 테스트 방법

### 6.1 Health Check

**모든 서비스**:
```bash
curl http://localhost:8000/api/v1/health  # Gateway
curl http://localhost:5005/api/v1/health  # YOLO
curl http://localhost:5002/api/v2/health  # eDOCr2 v2
curl http://localhost:5012/api/v1/health  # EDGNet
curl http://localhost:5003/api/v1/health  # Skin Model
curl http://localhost:5006/api/v1/health  # PaddleOCR
```

---

### 6.2 Unit Test (예시)

**Service Test**:
```python
# tests/test_yolo_service.py
import pytest
from services import YOLOInferenceService

def test_yolo_service_load():
    service = YOLOInferenceService()
    service.load_model("/app/models/best.pt")
    assert service.model is not None

def test_yolo_service_predict():
    service = YOLOInferenceService()
    service.load_model("/app/models/best.pt")

    with open("test_image.jpg", "rb") as f:
        image_bytes = f.read()

    result = service.predict(image_bytes, conf_threshold=0.25)
    assert result["status"] == "success"
    assert "detections" in result
```

---

### 6.3 Integration Test

**End-to-End**:
```python
# tests/test_integration.py
import requests

def test_full_pipeline():
    with open("test_drawing.jpg", "rb") as f:
        files = {"file": f}
        data = {
            "use_ocr": True,
            "use_segmentation": True,
            "use_tolerance": True,
            "visualize": True
        }

        response = requests.post(
            "http://localhost:8000/api/v1/process",
            files=files,
            data=data
        )

    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "success"
    assert "yolo_results" in result["data"]
    assert "ocr_results" in result["data"]
```

---

### 6.4 Manual Test via Web UI

1. Open: http://localhost:5173/test/gateway
2. Upload test drawing
3. Select options
4. Click "통합 분석 실행"
5. Verify results

---

## 7. 빠른 참조 (Quick Reference)

### 7.1 File Size Cheat Sheet

| File | Typical Size | Read Time |
|------|--------------|-----------|
| models/schemas.py | 30-80 lines | 3-5s |
| services/{service}.py | 150-250 lines | 10-15s |
| utils/helpers.py | 70-100 lines | 5-8s |
| api_server.py | 200-350 lines | 15-20s |

### 7.2 Common Grep Patterns

```bash
# Find function definition
grep -r "def function_name" .

# Find class definition
grep -r "class ClassName" .

# Find API endpoint
grep -r "@app.post" .

# Find all imports of module
grep -r "from services import" .

# Find Pydantic model usage
grep -r "BaseModel" .
```

### 7.3 Module Responsibility Matrix

| Module | Responsible For | NOT Responsible For |
|--------|----------------|---------------------|
| **models/** | Data validation, type definitions | Business logic, API calls |
| **services/** | Business logic, ML inference, API calls | Data validation, HTTP routing |
| **utils/** | Helper functions, data transformation | Business logic, model definitions |
| **api_server.py** | HTTP routing, request handling | Business logic, data processing |

---

## 8. LLM-Specific Tips

### 8.1 Context Window Management

**Priority Order** (read in this order):
1. models/schemas.py (smallest, most important)
2. services/{specific_service}.py (focused logic)
3. utils/helpers.py (if needed)
4. api_server.py (last, largest)

**Example**:
```
Q: "YOLO detection 결과 형식이 뭔가요?"
LLM: Read yolo-api/models/schemas.py (45 lines)
     → DetectionResponse class 확인
     → 완료 (45 lines only!)
```

---

### 8.2 Fast Code Navigation

**Use grep first**:
```bash
# Instead of reading entire file
grep -n "def predict" yolo-api/services/inference.py
# Output: 145: def predict(...)
# Now read only lines 145-200
```

---

### 8.3 Dependency Graph

```
api_server.py
    ↓ imports
services/
    ↓ imports
utils/
    ↓ imports
models/
    ↓ (no imports from project)
```

**Rule**: Always read dependencies bottom-up
1. models/ (no dependencies)
2. utils/ (depends on models)
3. services/ (depends on utils, models)
4. api_server.py (depends on all)

---

## 9. Summary

### 9.1 Key Takeaways

1. ✅ **모든 API가 동일한 구조**: models/ → utils/ → services/ → api_server.py
2. ✅ **작은 파일 크기**: 평균 150 lines (LLM에 최적화)
3. ✅ **명확한 역할 분리**: SRP 준수
4. ✅ **쉬운 수정**: 모듈 격리로 side effect 최소화
5. ✅ **쉬운 추가**: 새 모듈 추가만으로 기능 확장
6. ✅ **쉬운 삭제**: 파일 삭제만으로 기능 제거
7. ✅ **쉬운 조회**: grep + 작은 파일

### 9.2 Before vs After

| Aspect | Before | After |
|--------|--------|-------|
| **Average File Size** | 817 lines | 152 lines |
| **LLM Read Time** | 30-60s | 3-15s |
| **Modify Risk** | High | Low |
| **Add Feature** | Difficult | Easy |
| **Delete Feature** | Risky | Safe |
| **Code Search** | Slow | Fast |

---

**Last Updated**: 2025-11-19
**Maintained By**: Claude Code Team
**Status**: ✅ Production Ready
