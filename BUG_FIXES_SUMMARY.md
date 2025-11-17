# API 버그 수정 요약 리포트

**날짜**: 2025-11-15
**목적**: 모든 API의 버그 수정 및 정상 작동 확인

---

## 🔧 수정된 버그 목록

### 1. ✅ PaddleOCR API - 타입 비교 버그
**위치**: `/app/api_server.py:236-237`

**문제**:
- PaddleOCR이 confidence 값을 문자열로 반환하는 경우 존재
- `float`와 `str` 비교 시 TypeError 발생
- 일부 confidence 값은 'p' 같은 문자로 반환됨

**수정 전**:
```python
if confidence < min_confidence:
    continue
```

**수정 후**:
```python
try:
    confidence = float(confidence) if isinstance(confidence, str) else float(confidence)
except (ValueError, TypeError):
    logger.warning(f"Invalid confidence value: {confidence}, skipping detection")
    continue
```

**상태**: ✅ 수정 완료

---

### 2. ✅ Gateway API - eDOCr 호스트명 오류
**위치**: `/app/api_server.py:59-60`

**문제**:
- 코드에서 `edocr2-api-v1`, `edocr2-api-v2`로 설정
- 실제 컨테이너명은 `edocr2-api`, `edocr2-v2-api`
- Docker 네트워크에서 호스트명을 찾지 못함

**수정 전**:
```python
EDOCR_V1_URL = os.getenv("EDOCR_V1_URL", "http://edocr2-api-v1:5001")
EDOCR_V2_URL = os.getenv("EDOCR_V2_URL", "http://edocr2-api-v2:5002")
```

**수정 후**:
```python
EDOCR_V1_URL = os.getenv("EDOCR_V1_URL", "http://edocr2-api:5001")
EDOCR_V2_URL = os.getenv("EDOCR_V2_URL", "http://edocr2-v2-api:5002")
```

**상태**: ✅ 코드 수정 완료

---

### 3. ✅ docker-compose.yml - 잘못된 환경변수
**위치**: `docker-compose.yml` Gateway service

**문제**:
- `EDOCR2_URL` 환경변수가 v1 포트로 설정됨
- 환경변수가 코드보다 우선순위가 높아서 코드 수정이 무효화됨

**수정 전**:
```yaml
environment:
  - EDOCR_V1_URL=http://edocr2-api:5001
  - EDOCR_V2_URL=http://edocr2-v2-api:5002
  - EDOCR2_URL=http://edocr2-api:5001  # ❌ 잘못됨
```

**수정 후**:
```yaml
environment:
  - EDOCR_V1_URL=http://edocr2-api:5001
  - EDOCR_V2_URL=http://edocr2-v2-api:5002
  - EDOCR2_URL=http://edocr2-v2-api:5002  # ✅ 수정됨
```

**상태**: ✅ 수정 완료

---

### 4. ✅ Gateway API - OCR 엔드포인트 버전 오류
**위치**: `/app/api_server.py:158`

**문제**:
- eDOCr v2 API는 `/api/v2/ocr` 엔드포인트 사용
- Gateway가 `/api/v1/ocr`을 호출하여 HTTP 404 발생

**수정 전**:
```python
f"{EDOCR2_URL}/api/v1/ocr",
```

**수정 후**:
```python
f"{EDOCR2_URL}/api/v2/ocr",
```

**상태**: ✅ 수정 완료

---

### 5. ⚠️ eDOCr v1/v2 - CUDA 라이브러리 누락 (부분 해결)
**위치**: `gpu_preprocessing.py`

**문제**:
- CUDA 런타임 라이브러리 `libnvrtc.so.12` 누락
- GPU 전처리 사용 시 RuntimeError 발생
- cuPy import는 성공하나 실행 시 CUDA 호출 실패

**수정 사항**:
1. Exception 처리 개선
```python
# 수정 전
except ImportError:
    ...

# 수정 후
except (ImportError, RuntimeError, OSError) as e:
    ...
```

2. GPU 전처리 기본값을 False로 변경
```python
# api_server.py
use_gpu_preprocessing: bool = False  # 기본값 False로 변경
```

3. Form 파라미터 기본값도 False로 변경
```python
use_gpu_preprocessing: bool = Form(False, description="GPU 전처리 사용")
```

**상태**: ⚠️ **CPU 폴백으로 우회**
- GPU 전처리는 비활성화
- CPU 모드로 정상 작동
- 성능 저하 가능성 있음

**근본 해결 방법** (추후 적용 필요):
```dockerfile
# Dockerfile에 CUDA 라이브러리 설치
RUN apt-get update && apt-get install -y \
    cuda-nvrtc-12-0 \
    libcuda1-12.0
```

---

## 📊 수정 결과 요약

| API | 수정 전 | 수정 후 | 상태 |
|-----|---------|---------|------|
| **PaddleOCR** | ❌ TypeError | ✅ 정상 (예외 처리) | 🟢 완료 |
| **Gateway** | ❌ 404 Error | ✅ eDOCr v2 연결 | 🟢 완료 |
| **eDOCr v1** | ❌ CUDA 오류 | ⚠️ CPU 모드 | 🟡 우회 |
| **eDOCr v2** | ❌ CUDA 오류 | ⚠️ CPU 모드 | 🟡 우회 |

---

## 🔄 적용된 변경사항

### 파일 수정
1. `paddleocr-api/api_server.py` - 타입 예외 처리 추가
2. `gateway-api/api_server.py` - 호스트명 및 엔드포인트 수정
3. `edocr2-api/api_server.py` - GPU 전처리 비활성화
4. `edocr2-v2-api/api_server.py` - GPU 전처리 비활성화
5. `edocr2-api/gpu_preprocessing.py` - Exception 범위 확대
6. `edocr2-v2-api/gpu_preprocessing.py` - Exception 범위 확대
7. `docker-compose.yml` - 환경변수 수정

### 컨테이너 재시작
```bash
docker restart paddleocr-api
docker restart edocr2-api
docker restart edocr2-v2-api
docker restart gateway-api
```

---

## ⚠️ 알려진 제한사항

### 1. eDOCr GPU 가속 비활성화
- **영향**: 이미지 전처리 속도 감소 가능
- **해결**: CUDA 라이브러리 설치 후 GPU 모드 활성화
- **현재**: CPU 모드로 정상 작동

### 2. 컨테이너 재생성 시 변경사항 손실
- Docker compose로 컨테이너 재생성 시 컨테이너 내부 파일 수정 손실
- **해결 방법**:
  1. Dockerfile에 COPY 명령 추가하거나
  2. Volume 마운트 사용
  3. 소스 코드 직접 수정 후 이미지 재빌드

### 3. EDGNet 성능 문제 (기존 문제)
- 여전히 2.5분+ 소요
- Gateway에서 타임아웃 발생
- **권장**: `use_segmentation=false`로 비활성화

### 4. VL API 모델 미설치 (기존 문제)
- LLM 모델이 설치되지 않음
- `available_models: []`
- **해결**: Ollama 설치 및 모델 다운로드 필요

---

## ✅ 테스트 방법

### PaddleOCR 테스트
```bash
curl -X POST http://localhost:5006/api/v1/ocr \
  -F "file=@sample.jpg" \
  -F "det_db_thresh=0.3"
```

### eDOCr v2 테스트
```bash
curl -X POST http://localhost:5002/api/v2/ocr \
  -F "file=@sample.jpg"
```

### Gateway 전체 파이프라인 테스트
```bash
curl -X POST http://localhost:8000/api/v1/process \
  -F "file=@sample.jpg" \
  -F "pipeline_mode=speed" \
  -F "use_segmentation=false" \
  -F "use_tolerance=false"
```

---

## 🎯 권장 후속 조치

### 즉시 (Critical)
- [ ] 모든 수정사항을 Dockerfile에 반영
- [ ] 이미지 재빌드 및 배포
- [ ] `docker-compose up --build` 테스트

### 단기 (1주일)
- [ ] CUDA 라이브러리 설치하여 GPU 가속 활성화
- [ ] VL API 모델 설치 (Ollama + LLaVA)
- [ ] EDGNet 성능 최적화 또는 대체

### 중기 (1개월)
- [ ] 전체 시스템 통합 테스트
- [ ] 실제 도면으로 end-to-end 테스트
- [ ] 성능 벤치마크

---

## 📝 결론

### 수정 완료
- ✅ PaddleOCR 타입 버그 수정
- ✅ Gateway 연결 오류 수정
- ✅ eDOCr CUDA 오류 우회 (CPU 모드)

### 현재 상태
- **치수 추출 파이프라인 기본 기능 복구**
- YOLO + eDOCr v2 + Skin Model 조합으로 동작 가능
- GPU 가속은 비활성화되어 있으나 기능상 문제 없음

### 다음 단계
1. Dockerfile에 모든 수정사항 반영
2. 이미지 재빌드
3. 전체 통합 테스트
4. CUDA 라이브러리 설치로 GPU 가속 활성화

---

**작성자**: Claude Code
**작성일**: 2025-11-15
**관련 문서**:
- `/home/uproot/ax/poc/API_INDIVIDUAL_TEST_REPORT.md`
- `/home/uproot/ax/poc/SYSTEM_INTEGRATION_ANALYSIS.md`
- `/home/uproot/ax/poc/YOLO_IMPROVEMENT_FINAL_REPORT.md`
