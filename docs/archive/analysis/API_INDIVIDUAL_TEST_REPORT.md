# API 개별 기능 테스트 리포트

**작성일**: 2025-11-15
**목적**: 모든 API가 개별적으로 정상 작동하고 유의미한 결과를 생성하는지 검증
**테스트 대상**: 9개 마이크로서비스 API

---

## 📋 전체 요약

| API | 포트 | Health Check | 기능 테스트 | 상태 | 비고 |
|-----|------|-------------|-----------|------|------|
| **YOLOv11** | 5005 | ✅ Healthy | ✅ 완전 동작 | 🟢 **정상** | 19개 검출, 1.6초 |
| **eDOCr v1** | 5001 | ✅ Healthy | ❌ CUDA 오류 | 🔴 **고장** | libnvrtc.so.12 누락 |
| **eDOCr v2** | 5002 | ✅ Healthy | ❌ CUDA 오류 | 🔴 **고장** | libnvrtc.so.12 누락 |
| **PaddleOCR** | 5006 | ✅ Healthy | ❌ 타입 오류 | 🔴 **고장** | str vs float 비교 버그 |
| **EDGNet** | 5012 | ✅ Healthy | ⚠️ 타임아웃 | 🟡 **심각한 성능 문제** | 2.5분+ 소요 (실용 불가) |
| **Skin Model** | 5003 | ✅ Healthy | ✅ 완전 동작 | 🟢 **정상** | 0.61초, 공차 예측 성공 |
| **VL API** | 5004 | ✅ Healthy | ❌ 모델 없음 | 🔴 **고장** | available_models: [] |
| **Gateway** | 8000 | ✅ Healthy | ⚠️ 부분 동작 | 🟡 **설정 오류** | YOLO만 성공, OCR 404 |
| **Web UI** | 5173 | ✅ 동작 | ✅ YOLO 연동 | 🟢 **정상** | 웹 인터페이스 작동 |

### 종합 상태
- 🟢 **완전 정상**: 3개 (YOLOv11, Skin Model, Web UI)
- 🟡 **부분 작동**: 2개 (EDGNet, Gateway)
- 🔴 **완전 고장**: 4개 (eDOCr v1/v2, PaddleOCR, VL API)
- **전체 가동률**: 33% (3/9 완전 정상)

---

## 🔍 API별 상세 테스트 결과

---

### 1. YOLOv11 API (포트 5005) - ✅ **정상**

**Health Check**:
```bash
curl http://localhost:5005/api/v1/health
# ✅ {"status":"healthy","service":"yolo-api","version":"1.0.0"}
```

**기능 테스트**:
```bash
# 웹 UI를 통한 테스트 (S60ME-C Shaft 샘플)
```

**결과**:
- ✅ 검출 성공: 19개 객체
- ✅ 처리 시간: ~1.6초
- ✅ 필터링 적용됨 (text_block 20개 제거)
- ✅ 유의미한 출력:
  - parallelism: 5개 (최대 신뢰도 84.5%)
  - tolerance_dim: 5개
  - diameter_dim: 1개
  - linear_dim: 1개

**평가**: ⭐⭐⭐⭐⭐ **우수** - 최근 개선 사항이 모두 적용되어 완벽하게 동작

---

### 2. eDOCr v1 API (포트 5001) - ❌ **고장**

**Health Check**:
```bash
curl http://localhost:5001/api/v1/health
# ✅ {"status":"healthy","service":"eDOCr2 API","version":"1.0.0"}
```

**기능 테스트**:
```bash
curl -X POST http://localhost:5001/api/v1/ocr -F "file=@sample.jpg"
# ❌ HTTP 500 Internal Server Error
```

**에러 로그**:
```
RuntimeError: CuPy failed to load libnvrtc.so.12:
OSError: libnvrtc.so.12: cannot open shared object file: No such file or directory
```

**원인**:
- CUDA 런타임 라이브러리 누락
- Docker 컨테이너에 `libnvrtc.so.12` 설치되지 않음
- GPU 가속 OCR을 실행할 수 없음

**해결 방안**:
1. 컨테이너에 CUDA 12.x 라이브러리 설치
2. CPU 폴백 모드 구현
3. 또는 PaddleOCR을 주 OCR로 사용

**평가**: ⭐☆☆☆☆ **사용 불가** - 핵심 기능 완전 고장

---

### 3. eDOCr v2 API (포트 5002) - ❌ **고장**

**Health Check**:
```bash
curl http://localhost:5002/api/v2/health
# ✅ {"status":"healthy","service":"eDOCr2 v2 API","version":"2.0.0"}
```

**기능 테스트**:
```bash
curl -X POST http://localhost:5002/api/v2/ocr -F "file=@sample.jpg"
# ❌ HTTP 500 Internal Server Error
```

**에러**: eDOCr v1과 동일 - `libnvrtc.so.12` 누락

**영향**:
- **치수 추출 파이프라인 핵심 API 고장**
- Gateway가 의존하는 주요 OCR 엔진 동작 불가
- Hybrid 모드, Speed 모드 모두 영향받음

**평가**: ⭐☆☆☆☆ **사용 불가** - 치수 추출의 핵심 컴포넌트 고장

---

### 4. PaddleOCR API (포트 5006) - ❌ **고장**

**Health Check**:
```bash
curl http://localhost:5006/api/v1/health
# ✅ {"status":"healthy","service":"paddleocr-api","version":"1.0.0","gpu_available":true,"model_loaded":true}
```

**기능 테스트**:
```bash
curl -X POST http://localhost:5006/api/v1/ocr \
  -F "file=@S60ME-C INTERM-SHAFT_대 주조전.jpg" \
  -F "det_db_thresh=0.3" \
  -F "use_angle_cls=true"
# ❌ HTTP 500
# {"detail":"OCR processing error: '<' not supported between instances of 'str' and 'float'"}
```

**에러 분석**:
```python
# api_server.py:236
if confidence < min_confidence:  # ❌ TypeError
    # PaddleOCR이 confidence를 문자열로 반환하는데 float와 비교
```

**원인**:
- PaddleOCR 응답 파싱 버그
- Confidence 값이 문자열로 반환되지만 float와 비교
- 간단한 타입 캐스팅으로 해결 가능

**해결 방안**:
```python
# 수정 필요
confidence = float(confidence) if isinstance(confidence, str) else confidence
if confidence < min_confidence:
    ...
```

**평가**: ⭐⭐☆☆☆ **버그** - 인프라는 정상이나 코드 버그로 사용 불가

---

### 5. EDGNet API (포트 5012) - ⚠️ **심각한 성능 문제**

**Health Check**:
```bash
curl http://localhost:5012/api/v1/health
# ✅ {"status":"healthy","service":"EDGNet API","version":"1.0.0"}
```

**기능 테스트**:
```bash
curl -X POST http://localhost:5012/api/v1/segment \
  -F "file=@S60ME-C INTERM-SHAFT_대 주조전.jpg" \
  -F "num_classes=3"
# ⚠️ 2분 30초 이상 소요, 타임아웃으로 강제 종료
```

**로그**:
```
[1/4] Vectorization...
  ✓ Thinning complete
# 여기서 멈춤 (2.5분+)
```

**문제**:
- Vectorization/Thinning 단계에서 병목 발생
- 1684x1190 이미지에 2.5분 이상 소요
- 실시간 처리 불가능
- Gateway 파이프라인에서 60초 타임아웃 발생

**영향**:
- Gateway Speed 모드에서 EDGNet 호출 시 전체 파이프라인 60초 지연
- 세그멘테이션 결과 얻지 못함

**해결 방안**:
1. 이미지 다운샘플링 (해상도 축소)
2. Vectorization 알고리즘 최적화
3. C++/GPU 가속 구현
4. 또는 Gateway에서 EDGNet 비활성화

**평가**: ⭐⭐☆☆☆ **실용 불가** - 기술적으로 동작하나 성능상 사용 불가

---

### 6. Skin Model API (포트 5003) - ✅ **정상**

**Health Check**:
```bash
curl http://localhost:5003/api/v1/health
# ✅ {"status":"healthy","service":"Skin Model API","version":"1.0.0"}
```

**기능 테스트**:
```bash
curl -X POST http://localhost:5003/api/v1/tolerance \
  -H "Content-Type: application/json" \
  -d '{
    "dimensions": [{"type": "diameter", "value": 100.0, "unit": "mm"}],
    "material": {"name": "Steel"},
    "manufacturing_process": "machining"
  }'
```

**결과**:
```json
{
  "status": "success",
  "data": {
    "predicted_tolerances": {
      "flatness": 0.021,
      "cylindricity": 0.0315,
      "position": 0.0263,
      "perpendicularity": 0.0147
    },
    "manufacturability": {
      "score": 0.65,
      "difficulty": "Hard",
      "recommendations": [
        "Requires precision machining equipment",
        "Consider CNC grinding for tight tolerances",
        "Quality control critical - CMM inspection required"
      ]
    },
    "assemblability": {
      "score": 0.85,
      "clearance": 0.079,
      "interference_risk": "Low"
    }
  },
  "processing_time": 0.61
}
```

**평가**: ⭐⭐⭐⭐⭐ **우수** - 완벽한 기능, 빠른 속도, 유의미한 출력

---

### 7. VL API (포트 5004) - ❌ **고장**

**Health Check**:
```bash
curl http://localhost:5004/api/v1/health
# ✅ {"status":"healthy","available_models":[]}
```

**기능 테스트**:
```bash
curl -X POST http://localhost:5004/api/v1/extract_dimensions \
  -F "file=@sample.jpg"
# ❌ HTTP 500
# {"detail":""}
```

**문제**:
- `available_models: []` - 모델이 로드되지 않음
- VLM (Vision-Language Model)이 없어서 분석 불가
- 멀티모달 분석 기능 전혀 사용할 수 없음

**원인**:
- LLM 모델 파일 누락 또는 경로 설정 오류
- Ollama/LLaVA 등의 모델이 설치되지 않음

**영향**:
- Gateway의 VL 통합 기능 사용 불가
- 고급 이미지 이해 기능 비활성화

**평가**: ⭐☆☆☆☆ **사용 불가** - 모델 없어서 기능 전혀 사용 불가

---

### 8. Gateway API (포트 8000) - ⚠️ **부분 작동**

**Health Check**:
```bash
curl http://localhost:8000/api/v1/health
# ✅ {"status":"healthy","service":"Gateway API","version":"1.0.0",
#     "services":{"edocr2":"healthy","edgnet":"healthy","skinmodel":"healthy"}}
```

**기능 테스트 (Speed 모드)**:
```bash
curl -X POST http://localhost:8000/api/v1/process \
  -F "file=@sample.jpg" \
  -F "pipeline_mode=speed" \
  -F "use_segmentation=true" \
  -F "use_tolerance=true" \
  -F "use_ocr=true"
# ⚠️ 60초 소요
```

**결과 분석**:
```json
{
  "status": "success",
  "data": {
    "yolo_results": null,
    "ocr_results": null,
    "segmentation_results": null,
    "tolerance_results": null
  },
  "processing_time": 60.03
}
```

**로그 분석**:
```
✅ YOLO API: 28개 검출 성공 (0.3초)
❌ eDOCr2 API: HTTP 404 - POST http://edocr2-api:5001/api/v2/ocr
❌ EDGNet API: 타임아웃 (60초)
```

**문제**:
1. **eDOCr2 설정 오류**: Gateway가 `edocr2-api:5001`에 `/api/v2/ocr`을 호출
   - 포트 5001은 eDOCr **v1**이고 `/api/v1/ocr` 엔드포인트만 있음
   - 포트 5002가 eDOCr **v2**인데 잘못된 포트로 호출
2. **EDGNet 타임아웃**: 60초 대기 후 실패
3. **앙상블 결과 없음**: OCR 결과가 없어서 최종 출력 0개

**해결 방안**:
```python
# gateway-api 설정 수정 필요
EDOCR2_API_URL = "http://edocr2-api:5002"  # 5001 → 5002로 변경
```

**평가**: ⭐⭐⭐☆☆ **설정 오류** - YOLO는 동작하나 OCR 설정 오류로 전체 파이프라인 실패

---

### 9. Web UI (포트 5173) - ✅ **정상**

**접근 테스트**:
```bash
# Chrome MCP로 테스트
http://localhost:5173
```

**기능 테스트**:
- ✅ 페이지 로드 성공
- ✅ 샘플 이미지 선택 가능
- ✅ YOLO 검출 실행 성공
- ✅ 검출 결과 시각화 표시

**평가**: ⭐⭐⭐⭐⭐ **정상** - 웹 인터페이스 완벽 동작

---

## 🚨 **Critical Issues (즉시 해결 필요)**

### Priority 1 - 완전 고장 (4개)

#### 1. eDOCr v1/v2 CUDA 라이브러리 누락 🔴
**영향**: 치수 추출의 핵심 OCR 기능 전혀 사용 불가
**해결**:
```dockerfile
# Dockerfile에 추가
RUN apt-get update && apt-get install -y \
    cuda-nvrtc-12-0 \
    libcuda1-12.0
```
또는 CPU 폴백:
```python
try:
    import cupy
except:
    use_cpu = True
```

#### 2. PaddleOCR 타입 비교 버그 🔴
**영향**: 대체 OCR 엔진도 사용 불가
**해결**: `api_server.py:236` 수정
```python
confidence = float(result.get('confidence', 0))
if confidence < min_confidence:
    continue
```

#### 3. VL API 모델 미설치 🔴
**영향**: 멀티모달 분석 불가
**해결**:
```bash
# Ollama 설치 및 LLaVA 모델 다운로드
docker exec vl-api ollama pull llava:13b
```

#### 4. Gateway eDOCr2 포트 설정 오류 🔴
**영향**: Gateway 파이프라인 전체 실패
**해결**: `gateway-api/config.py` 수정
```python
EDOCR2_API_URL = "http://edocr2-api:5002"  # 5001 → 5002
```

---

### Priority 2 - 성능 문제 (1개)

#### 5. EDGNet 극심한 성능 저하 ⚠️
**영향**: 파이프라인 60초 지연
**해결**:
1. 단기: Gateway에서 EDGNet 비활성화
2. 장기: Vectorization 알고리즘 최적화 또는 GPU 가속

---

## 📊 통계 요약

### API 상태 분포
```
🟢 완전 정상:    3개 (33%)  ██████░░░░░░░░░░░░
🟡 부분 작동:    2개 (22%)  ████░░░░░░░░░░░░░░
🔴 완전 고장:    4개 (45%)  █████████░░░░░░░░░
```

### 치수 추출 파이프라인 구성요소별 상태
| 구성요소 | 상태 | 가용성 |
|---------|------|--------|
| 객체 검출 (YOLO) | 🟢 정상 | 100% |
| OCR (eDOCr v1) | 🔴 고장 | 0% |
| OCR (eDOCr v2) | 🔴 고장 | 0% |
| OCR (PaddleOCR) | 🔴 고장 | 0% |
| 세그멘테이션 (EDGNet) | 🟡 느림 | 10% |
| 공차 예측 (Skin Model) | 🟢 정상 | 100% |
| 멀티모달 (VL) | 🔴 고장 | 0% |
| 오케스트레이션 (Gateway) | 🟡 설정 오류 | 30% |

**결론**: OCR 기능이 **완전히 불가능**하여 치수 추출 파이프라인 동작 불가

---

## 🎯 즉시 실행 가능한 최소 기능 복구 계획

### Step 1: PaddleOCR 버그 수정 (10분)
```bash
# 1. 컨테이너 진입
docker exec -it paddleocr-api /bin/bash

# 2. api_server.py 수정
vim /app/api_server.py
# Line 236 수정: confidence = float(confidence)

# 3. 재시작
docker restart paddleocr-api
```

### Step 2: Gateway 포트 수정 (5분)
```bash
# gateway-api/config.py 또는 환경변수 수정
docker exec -it gateway-api /bin/bash
# EDOCR2_API_URL을 5002로 변경
docker restart gateway-api
```

### Step 3: EDGNet 비활성화 (1분)
```bash
# Gateway 호출 시 use_segmentation=false 설정
curl -X POST http://localhost:8000/api/v1/process \
  -F "file=@sample.jpg" \
  -F "use_segmentation=false"
```

**복구 후 최소 기능**:
- ✅ YOLO 객체 검출
- ✅ PaddleOCR 치수 추출 (버그 수정 후)
- ✅ Skin Model 공차 예측
- ✅ Gateway 파이프라인 동작

---

## 📝 결론

### 현재 상태
**최소 기능조차 작동하지 않음** - 9개 API 중 3개만 완전 정상

### 주요 문제
1. **OCR 완전 불능**: eDOCr v1/v2 CUDA 오류, PaddleOCR 버그
2. **Gateway 설정 오류**: 잘못된 포트로 OCR 호출
3. **VL API 모델 미설치**: 멀티모달 분석 불가
4. **EDGNet 성능 저하**: 실시간 처리 불가능

### 권장 사항
1. **즉시**: PaddleOCR 버그 수정 및 Gateway 포트 수정 (최소 기능 복구)
2. **단기**: eDOCr CUDA 라이브러리 설치 또는 CPU 폴백 구현
3. **중기**: EDGNet 성능 최적화 또는 대체 솔루션
4. **장기**: VL API 모델 설치 및 통합

---

**작성자**: Claude Code (Anthropic)
**작성일**: 2025-11-15
**테스트 환경**: WSL2 Ubuntu, Docker 컨테이너
