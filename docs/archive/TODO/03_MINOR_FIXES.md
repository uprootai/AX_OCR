# 간단한 수정 사항 (Priority 1-2)

> 작성일: 2025-11-13
> 예상 소요: 4-8시간
> 우선순위: 🟡 중간

---

## 📋 개요

시스템의 안정성과 사용자 경험을 개선하기 위한 간단하지만 중요한 수정 사항들을 정리합니다.
각 항목은 1-2시간 내에 완료 가능하며, 즉각적인 효과가 있습니다.

---

## 1. VL API 키 검증 추가 🔴

### 현재 문제

**파일**: `vl-api/api_server.py`

```python
# 현재 구현 (시작 시 검증 없음)
@app.post("/api/v1/extract_info_block")
async def extract_info_block(file: UploadFile, model: str = "claude-3-5-sonnet-20241022"):
    # API 키가 없어도 요청 받음
    # 실제 호출 시점에 에러 발생
    ...
```

**증상**:
- 사용자가 파일 업로드 후 5-10초 대기
- 그 후 `ANTHROPIC_API_KEY not set` 에러
- 시간 낭비 + 나쁜 UX

### 해결 방법

**Option A: 시작 시 검증 (추천)**

```python
import os
from fastapi import FastAPI, HTTPException, status

app = FastAPI()

# 필요한 API 키 목록
REQUIRED_KEYS = {
    "ANTHROPIC_API_KEY": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229"],
    "OPENAI_API_KEY": ["gpt-4o", "gpt-4-turbo"]
}

@app.on_event("startup")
async def validate_api_keys():
    """서버 시작 시 API 키 검증"""
    missing_keys = []

    for key_name, models in REQUIRED_KEYS.items():
        if not os.getenv(key_name):
            missing_keys.append(f"{key_name} (required for {', '.join(models)})")

    if missing_keys:
        error_msg = "Missing required API keys:\n" + "\n".join(f"  - {k}" for k in missing_keys)
        print(f"❌ {error_msg}")
        raise RuntimeError(error_msg)

    print("✅ All required API keys are present")

@app.get("/api/v1/health")
async def health():
    """헬스체크 - API 키 상태 포함"""
    keys_status = {
        key: "✅" if os.getenv(key) else "❌"
        for key in REQUIRED_KEYS.keys()
    }

    return {
        "status": "healthy",
        "api_keys": keys_status
    }
```

**Option B: 요청 시 조기 검증**

```python
from fastapi import Depends, HTTPException

def verify_api_key_for_model(model: str):
    """모델별 API 키 검증 의존성"""
    if model.startswith("claude-"):
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="ANTHROPIC_API_KEY is not configured"
            )
    elif model.startswith("gpt-"):
        if not os.getenv("OPENAI_API_KEY"):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OPENAI_API_KEY is not configured"
            )

@app.post("/api/v1/extract_info_block")
async def extract_info_block(
    file: UploadFile,
    model: str = "claude-3-5-sonnet-20241022",
    _: None = Depends(lambda model=model: verify_api_key_for_model(model))
):
    # API 키가 없으면 파일 업로드 전에 에러 반환
    ...
```

**추천**: Option A + Option B 조합
- 시작 시 검증으로 배포 시 즉시 발견
- 요청 시 검증으로 런타임 안전성 확보

### 예상 효과

- ✅ 사용자 시간 절약 (5-10초 → 즉시 에러)
- ✅ 명확한 에러 메시지
- ✅ 배포 시 조기 발견

---

## 2. EDGNet 모델 파일 검증 강화 🟡

### 현재 문제

**파일**: `edgnet-api/api_server.py` (153-163줄)

```python
if os.path.exists(model_path):
    try:
        model.load_state_dict(torch.load(model_path, map_location=device))
        print(f"✅ Loaded model from {model_path}")
    except Exception as e:
        print(f"⚠️ Failed to load model: {e}, using mock")
        use_mock = True  # ← Silent fallback
else:
    print(f"⚠️ Model not found at {model_path}, using mock")
    use_mock = True
```

**문제점**:
- 모델 없으면 조용히 Mock으로 fallback
- 사용자는 실제 모델 사용 중인지 모름
- Mock 결과가 실제 결과처럼 보임

### 해결 방법

**Option A: 명시적 에러 (추천 - 프로덕션)**

```python
if not os.path.exists(model_path):
    error_msg = f"Model file not found: {model_path}"
    print(f"❌ {error_msg}")
    raise RuntimeError(error_msg)

try:
    model.load_state_dict(torch.load(model_path, map_location=device))
    print(f"✅ Loaded EDGNet model from {model_path}")
except Exception as e:
    error_msg = f"Failed to load EDGNet model: {e}"
    print(f"❌ {error_msg}")
    raise RuntimeError(error_msg)
```

**Option B: 환경 변수 제어 (추천 - 개발)**

```python
import os

ALLOW_MOCK = os.getenv("EDGNET_ALLOW_MOCK", "false").lower() == "true"

if not os.path.exists(model_path):
    if ALLOW_MOCK:
        print(f"⚠️ Model not found, using mock (EDGNET_ALLOW_MOCK=true)")
        use_mock = True
    else:
        raise RuntimeError(f"Model file not found: {model_path}")
```

**Option C: 응답에 플래그 추가**

```python
# 응답 모델 수정
class SegmentationResponse(BaseModel):
    components: List[Dict]
    total_components: int
    processing_time: float
    is_mock: bool = Field(False, description="Mock 데이터 여부")  # ← 추가

# 응답 시 플래그 설정
return {
    "components": components,
    "total_components": len(components),
    "processing_time": elapsed,
    "is_mock": use_mock  # ← 명시적 표시
}
```

**추천**: Option B (개발) + Option C (항상)
- 개발 시 Mock 허용 가능
- 프로덕션 배포 시 `EDGNET_ALLOW_MOCK=false` (기본값)
- 모든 응답에 `is_mock` 플래그 포함

---

## 3. Gateway 에러 핸들링 개선 🟡

### 현재 문제

**파일**: `gateway-api/api_server.py`

```python
# 마이크로서비스 호출 시 에러 처리 부족
response = requests.post(f"{YOLO_API_URL}/api/v1/detect", ...)
# ← requests.exceptions.RequestException 처리 안 됨
```

**증상**:
- 마이크로서비스 다운 시 Gateway 크래시
- 불명확한 에러 메시지
- 부분 실패 시 전체 실패

### 해결 방법

```python
import requests
from typing import Optional

class ServiceCallError(Exception):
    """마이크로서비스 호출 에러"""
    pass

def call_service(
    service_name: str,
    url: str,
    method: str = "POST",
    **kwargs
) -> Optional[Dict]:
    """안전한 마이크로서비스 호출"""
    try:
        if method == "POST":
            response = requests.post(url, timeout=30, **kwargs)
        elif method == "GET":
            response = requests.get(url, timeout=30, **kwargs)

        response.raise_for_status()
        return response.json()

    except requests.exceptions.Timeout:
        print(f"⚠️ {service_name} timeout (30s)")
        raise ServiceCallError(f"{service_name} did not respond within 30 seconds")

    except requests.exceptions.ConnectionError:
        print(f"⚠️ {service_name} connection failed")
        raise ServiceCallError(f"Cannot connect to {service_name} at {url}")

    except requests.exceptions.HTTPError as e:
        print(f"⚠️ {service_name} HTTP error: {e.response.status_code}")
        raise ServiceCallError(f"{service_name} returned {e.response.status_code}: {e.response.text}")

    except Exception as e:
        print(f"❌ {service_name} unexpected error: {e}")
        raise ServiceCallError(f"Unexpected error calling {service_name}: {str(e)}")

# 사용 예시
try:
    yolo_result = call_service(
        service_name="YOLO API",
        url=f"{YOLO_API_URL}/api/v1/detect",
        files={"file": file_data},
        data={"conf_threshold": conf_threshold}
    )
except ServiceCallError as e:
    return {
        "status": "error",
        "error": str(e),
        "service": "YOLO API",
        "processing_time": time.time() - start_time
    }
```

---

## 4. 로깅 개선 🟢

### 현재 문제

- `print()` 문으로만 로깅
- 로그 레벨 없음 (INFO/WARNING/ERROR 구분 안 됨)
- 파일 저장 없음 (재시작 시 손실)
- 타임스탬프 불일치

### 해결 방법

```python
import logging
from logging.handlers import RotatingFileHandler
import sys

def setup_logging(service_name: str, log_level: str = "INFO"):
    """통합 로깅 설정"""
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, log_level.upper()))

    # 포맷
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 파일 핸들러 (10MB, 5개 백업)
    file_handler = RotatingFileHandler(
        f"logs/{service_name}.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

# 각 서비스에서 사용
logger = setup_logging("gateway-api", log_level=os.getenv("LOG_LEVEL", "INFO"))

# 기존 print() → logger 변경
# print(f"✅ YOLO detected {n} objects")  # Before
logger.info(f"YOLO detected {n} objects")  # After

# print(f"⚠️ Model not found")  # Before
logger.warning("Model not found at {path}")  # After

# print(f"❌ Failed: {e}")  # Before
logger.error(f"Failed: {e}", exc_info=True)  # After (스택 트레이스 포함)
```

---

## 5. Docker Health Check 추가 🟢

### 현재 문제

```yaml
# docker-compose.yml - 현재 health check 없음
services:
  yolo-api:
    image: yolo-api:latest
    ports:
      - "5005:5005"
    # ← healthcheck 없음
```

**문제점**:
- 컨테이너 Up ≠ 서비스 Ready
- Gateway가 준비 안 된 서비스 호출
- 재시작 시 타이밍 이슈

### 해결 방법

```yaml
# docker-compose.yml
services:
  yolo-api:
    image: yolo-api:latest
    ports:
      - "5005:5005"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5005/api/v1/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 30s
    depends_on:
      - gateway-api

  edocr2-api:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5001/api/v1/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 30s

  # 모든 서비스에 동일하게 적용...
```

**각 서비스에 Health 엔드포인트 추가**:

```python
@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    # 간단한 체크
    return {
        "status": "healthy",
        "service": "YOLO API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/health/ready")
async def readiness_check():
    """Readiness check - 모델 로드 확인"""
    if not model_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")

    return {
        "status": "ready",
        "model_loaded": True
    }
```

---

## 6. 파일 업로드 크기 제한 🟢

### 현재 문제

```python
# 무제한 업로드 허용
@app.post("/api/v1/process")
async def process_drawing(file: UploadFile):
    # 100MB PDF도 받음 → 메모리 부족
    ...
```

### 해결 방법

```python
from fastapi import HTTPException, File, UploadFile
import os

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

async def validate_file_size(file: UploadFile):
    """파일 크기 검증"""
    # 헤더에서 크기 확인
    if hasattr(file, "size") and file.size:
        if file.size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max size: {MAX_FILE_SIZE / 1024 / 1024}MB"
            )

    # 실제 읽으면서 확인
    chunk_size = 1024 * 1024  # 1MB chunks
    total_size = 0
    chunks = []

    while chunk := await file.read(chunk_size):
        total_size += len(chunk)
        if total_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max size: {MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        chunks.append(chunk)

    # 원래 위치로 복원
    await file.seek(0)
    return total_size

@app.post("/api/v1/process")
async def process_drawing(file: UploadFile = File(...)):
    file_size = await validate_file_size(file)
    print(f"Processing file: {file.filename} ({file_size / 1024 / 1024:.2f}MB)")
    ...
```

---

## 📋 구현 체크리스트

### 우선순위 1 (즉시 적용)

- [ ] VL API 키 검증 추가 (Option A + B)
- [ ] EDGNet 모델 검증 강화 (Option B + C)
- [ ] Gateway 에러 핸들링 개선

### 우선순위 2 (1주일 내)

- [ ] 로깅 시스템 구현
- [ ] Docker Health Check 추가
- [ ] 파일 크기 제한 추가

---

## 📊 예상 효과

| 항목 | 소요 시간 | 효과 | 우선순위 |
|------|----------|------|----------|
| VL API 키 검증 | 1시간 | UX 개선, 배포 안전성 | 🔴 높음 |
| EDGNet 모델 검증 | 1시간 | 투명성, 디버깅 용이 | 🟡 중간 |
| Gateway 에러 핸들링 | 2시간 | 안정성, 명확한 에러 | 🟡 중간 |
| 로깅 개선 | 2시간 | 디버깅, 모니터링 | 🟢 낮음 |
| Health Check | 1시간 | 재시작 안정성 | 🟢 낮음 |
| 파일 크기 제한 | 1시간 | 보안, 리소스 보호 | 🟢 낮음 |

**총 예상 소요**: 8시간

---

## 🎯 결론

이 문서의 모든 수정 사항은:
- ✅ 구현이 간단함 (1-2시간)
- ✅ 즉각적인 효과가 있음
- ✅ 기존 기능을 변경하지 않음
- ✅ 프로덕션 배포 전 필수

**다음 단계**: 우선순위 1 항목부터 순차적으로 구현

---

**관련 문서**:
- `01_CURRENT_STATUS_OVERVIEW.md`: 전체 시스템 현황
- `02_EDOCR2_INTEGRATION_PLAN.md`: 주요 개선 과제
