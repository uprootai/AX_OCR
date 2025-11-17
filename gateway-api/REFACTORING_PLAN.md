# Gateway API 리팩토링 계획

**작성일**: 2025-11-16
**현재 상태**: api_server.py 2005 라인 (단일 파일)
**목표**: 모듈화된 구조로 분리 (파일당 ~150 라인)

---

## 🎯 목표 구조

```
gateway-api/
├── api_server.py         (~200 lines) - FastAPI 앱 + 엔드포인트만
├── services/
│   ├── __init__.py
│   ├── ocr_service.py    (~300 lines) - OCR 관련 통합 로직
│   ├── ensemble_service.py (~200 lines) - 앙상블 전략
│   ├── yolo_service.py   (~150 lines) - YOLO API 호출
│   ├── tolerance_service.py (~150 lines) - 공차 분석
│   └── quote_service.py  (~200 lines) - 견적 생성
├── models/
│   ├── __init__.py
│   ├── request_models.py (~100 lines) - Pydantic 요청 모델
│   └── response_models.py (~100 lines) - Pydantic 응답 모델
├── utils/
│   ├── __init__.py
│   ├── image_utils.py    (~150 lines) - crop, upscale, pdf2img
│   ├── filters.py        (~100 lines) - False Positive 필터
│   └── progress.py       (~100 lines) - ProgressTracker 클래스
├── config.py             (~50 lines) - 환경 변수, 상수
├── cost_estimator.py     (기존 유지)
├── pdf_generator.py      (기존 유지)
└── advanced_features.py  (기존 유지)
```

---

## 📋 Phase 1: 모델 분리

### 1.1 Request Models (`models/request_models.py`)
현재 위치: `api_server.py:99-181`

이동할 클래스:
- `ProcessDrawingRequest`
- `CostEstimateRequest`
- `QuoteRequest`

### 1.2 Response Models (`models/response_models.py`)
현재 위치: 암시적 (dict 반환)

생성할 클래스:
- `YOLODetectionResponse`
- `OCRResultResponse`
- `EnsembleResultResponse`
- `ToleranceAnalysisResponse`
- `ProcessDrawingResponse`

---

## 📋 Phase 2: 유틸리티 분리

### 2.1 Image Utils (`utils/image_utils.py`)
현재 위치: `api_server.py:693-774`

이동할 함수:
- `crop_bbox()` (line 693)
- `upscale_image()` (line 729)
- `convert_pdf_to_images()` (line 1151)

### 2.2 Filters (`utils/filters.py`)
현재 위치: `api_server.py:777-815`

이동할 함수:
- `is_false_positive()` (line 777)

### 2.3 Progress Tracker (`utils/progress.py`)
현재 위치: `api_server.py:184-398`

이동할 클래스:
- `ProgressTracker` (line 184)

---

## 📋 Phase 3: 서비스 분리

### 3.1 OCR Service (`services/ocr_service.py`)
현재 위치: `api_server.py:819-958`

이동할 함수:
- `process_yolo_crop_ocr()` (line 819)
- `call_edocr_v2()` (신규 - 인라인 코드 추출)
- `call_paddleocr()` (신규 - 인라인 코드 추출)

클래스 구조:
```python
class OCRService:
    def __init__(self, edocr_url: str, paddle_url: str):
        self.edocr_url = edocr_url
        self.paddle_url = paddle_url

    async def process_yolo_crop_ocr(self, yolo_results, image_path):
        # 기존 로직
        pass

    async def call_edocr_v2(self, image_bytes):
        # eDOCr v2 API 호출
        pass

    async def call_paddleocr(self, image_bytes):
        # PaddleOCR API 호출
        pass
```

### 3.2 Ensemble Service (`services/ensemble_service.py`)
현재 위치: `api_server.py:961-1047`

이동할 함수:
- `ensemble_ocr_results()` (line 961)

클래스 구조:
```python
class EnsembleService:
    def __init__(self, yolo_weight: float = 0.6, edocr_weight: float = 0.4):
        self.yolo_weight = yolo_weight
        self.edocr_weight = edocr_weight

    def ensemble_ocr_results(self, yolo_ocr, edocr_ocr):
        # 기존 로직
        pass

    def _calculate_similarity(self, text1, text2):
        # 유사도 계산
        pass
```

### 3.3 YOLO Service (`services/yolo_service.py`)
현재 위치: 인라인 코드 (`api_server.py:1520-1570`)

신규 클래스:
```python
class YOLOService:
    def __init__(self, yolo_url: str):
        self.yolo_url = yolo_url

    async def detect(self, image_bytes: bytes, options: dict):
        # YOLO API 호출
        pass

    def parse_response(self, response: dict):
        # 응답 파싱
        pass
```

### 3.4 Tolerance Service (`services/tolerance_service.py`)
현재 위치: 인라인 코드 (`api_server.py:1770-1820`)

신규 클래스:
```python
class ToleranceService:
    def __init__(self, skinmodel_url: str):
        self.skinmodel_url = skinmodel_url

    async def analyze(self, dimensions: list, drawing_info: dict):
        # 공차 분석
        pass
```

### 3.5 Quote Service (`services/quote_service.py`)
현재 위치: `api_server.py:409-503`

이동할 함수:
- `estimate_cost_endpoint()` (line 409)
- `generate_quote_endpoint()` (line 459)

---

## 📋 Phase 4: 설정 분리

### config.py
현재 위치: `api_server.py:58-96`

이동할 상수:
- 환경 변수 (EDOCR_V1_URL, EDOCR_V2_URL, ...)
- 업로드 디렉토리 경로
- CORS 설정 (ALLOWED_ORIGINS)
- 기본값 상수

---

## 📋 Phase 5: 엔드포인트 정리

### api_server.py (최종 모습)
```python
from fastapi import FastAPI
from services.ocr_service import OCRService
from services.ensemble_service import EnsembleService
from services.yolo_service import YOLOService
from services.tolerance_service import ToleranceService
from models.request_models import ProcessDrawingRequest
from models.response_models import ProcessDrawingResponse
from config import CORS_SETTINGS, API_URLS

app = FastAPI()

# 서비스 인스턴스 생성
ocr_service = OCRService(API_URLS['edocr'], API_URLS['paddle'])
ensemble_service = EnsembleService()
yolo_service = YOLOService(API_URLS['yolo'])
tolerance_service = ToleranceService(API_URLS['skinmodel'])

@app.post("/api/v1/process", response_model=ProcessDrawingResponse)
async def process_drawing(request: ProcessDrawingRequest):
    # 1. YOLO 검출
    yolo_results = await yolo_service.detect(image_bytes, options)

    # 2. OCR 수행
    if request.use_yolo_crop_ocr:
        yolo_ocr = await ocr_service.process_yolo_crop_ocr(yolo_results, image_path)

    # 3. 앙상블
    if request.use_ensemble:
        final_ocr = ensemble_service.ensemble_ocr_results(yolo_ocr, edocr_ocr)

    # 4. 공차 분석
    tolerance = await tolerance_service.analyze(final_ocr)

    return ProcessDrawingResponse(...)
```

---

## 🚀 마이그레이션 전략

### 단계별 진행
1. **Phase 1 (모델 분리)**: 타입 정의 먼저 → 컴파일 오류 방지
2. **Phase 2 (유틸리티 분리)**: 의존성 없는 함수부터
3. **Phase 3 (서비스 분리)**: 하나씩 순차적으로
4. **Phase 4 (설정 분리)**: import 최소화
5. **Phase 5 (엔드포인트 정리)**: 마지막 통합

### 테스트 전략
각 Phase 후:
```bash
# 1. 빌드
docker-compose build gateway-api

# 2. 재시작
docker rm -f gateway-api
docker-compose up -d gateway-api

# 3. Health Check
curl http://localhost:8000/api/v1/health

# 4. 기능 테스트
curl -X POST http://localhost:8000/api/v1/process \
  -F "file=@test_drawing.png" \
  -F "use_yolo_crop_ocr=true" \
  -F "use_ensemble=true"
```

### 롤백 계획
- 각 Phase 전에 `git commit` 생성
- 문제 발생 시 `git revert` 또는 `git reset --hard`

---

## 📊 예상 효과

| 지표 | 현재 | 목표 |
|------|------|------|
| 파일당 라인 수 | 2005 | ~150 |
| 단일 책임 원칙 | ❌ | ✅ |
| 테스트 용이성 | ❌ | ✅ |
| LLM 컨텍스트 효율 | 낮음 | 높음 |
| 병렬 개발 가능 | ❌ | ✅ |

---

## ⚠️ 주의사항

1. **순환 import 방지**: `models` → `utils` → `services` → `api_server` 순서 유지
2. **타입 힌트 필수**: Python 3.8+ Type Hints 사용
3. **Async/Await 유지**: 비동기 함수 시그니처 변경 금지
4. **환경 변수 호환성**: 기존 `.env` 파일과 호환 유지

---

**다음 단계**: Phase 1 (모델 분리) 시작
