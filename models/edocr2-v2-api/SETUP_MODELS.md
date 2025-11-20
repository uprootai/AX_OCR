# eDOCr2 Models Setup Guide

> eDOCr2 API 모델 설정 가이드
> 실제 OCR 기능을 활성화하려면 모델 파일을 다운로드해야 합니다.

---

## 📋 Overview

eDOCr2 API는 **javvi51/edocr2** 저장소의 모델을 사용합니다.
Mock 데이터 대신 실제 OCR 결과를 받으려면 다음 단계를 수행하세요.

---

## 🚀 Setup Steps

### Step 1: 모델 파일 다운로드

**GitHub Releases에서 다운로드**:
- URL: https://github.com/javvi51/edocr2/releases/tag/download_recognizers
- Release: `v1.0.0 - download_recognizers`
- Assets: 6개 파일

**필요한 파일 목록**:
```
1. recognizer_gdts.keras           (GD&T 인식 모델)
2. recognizer_dimensions_2.keras    (치수 인식 모델)
3. (기타 4개 파일)
```

**다운로드 방법**:

```bash
# 1. Models 디렉토리 생성
mkdir -p /home/uproot/ax/opensource/01-immediate/edocr2/edocr2/models

# 2. GitHub에서 수동 다운로드
# https://github.com/javvi51/edocr2/releases/tag/download_recognizers
# 위 URL에서 6개 파일 모두 다운로드

# 3. 다운로드한 파일들을 models 디렉토리로 이동
mv ~/Downloads/recognizer_*.keras /home/uproot/ax/opensource/01-immediate/edocr2/edocr2/models/

# 4. 파일 확인
ls -lh /home/uproot/ax/opensource/01-immediate/edocr2/edocr2/models/
```

**예상 결과**:
```
total 120M
-rw-r--r-- 1 user user  45M Nov 13 10:00 recognizer_gdts.keras
-rw-r--r-- 1 user user  43M Nov 13 10:00 recognizer_dimensions_2.keras
-rw-r--r-- 1 user user  10M Nov 13 10:00 detector_*.keras
... (기타 파일들)
```

---

### Step 2: Docker 이미지 재빌드

모델 파일 준비 후 Docker 이미지를 재빌드합니다.

```bash
cd /home/uproot/ax/poc

# 1. 기존 컨테이너 중지 및 삭제
docker-compose stop edocr2-api
docker-compose rm -f edocr2-api

# 2. 이미지 재빌드
docker-compose build edocr2-api

# 3. 새 컨테이너 시작
docker-compose up -d edocr2-api

# 4. 로그 확인
docker-compose logs -f edocr2-api
```

**예상 로그 (성공 시)**:
```
edocr2-api_1  | 2025-11-13 10:00:00 - __main__ - INFO - 🚀 Starting eDOCr2 API...
edocr2-api_1  | 2025-11-13 10:00:00 - __main__ - INFO - ✅ eDOCr2 modules loaded successfully
edocr2-api_1  | 2025-11-13 10:00:00 - __main__ - INFO - 📦 Loading eDOCr2 models...
edocr2-api_1  | 2025-11-13 10:00:01 - __main__ - INFO -   Loading GD&T recognizer from ...
edocr2-api_1  | 2025-11-13 10:00:03 - __main__ - INFO -   ✅ GD&T recognizer loaded
edocr2-api_1  | 2025-11-13 10:00:03 - __main__ - INFO -   Loading dimension recognizer from ...
edocr2-api_1  | 2025-11-13 10:00:05 - __main__ - INFO -   ✅ Dimension recognizer loaded
edocr2-api_1  | 2025-11-13 10:00:05 - __main__ - INFO -   Loading detector
edocr2-api_1  | 2025-11-13 10:00:07 - __main__ - INFO -   ✅ Detector loaded
edocr2-api_1  | 2025-11-13 10:00:07 - __main__ - INFO - ✅ All models loaded successfully in 7.23s
edocr2-api_1  | 2025-11-13 10:00:07 - __main__ - INFO - ✅ eDOCr2 API ready
edocr2-api_1  | INFO:     Uvicorn running on http://0.0.0.0:5001
```

**예상 로그 (모델 없을 시)**:
```
edocr2-api_1  | 2025-11-13 10:00:00 - __main__ - ERROR - ❌ GD&T model not found: .../recognizer_gdts.keras
edocr2-api_1  | 2025-11-13 10:00:00 - __main__ - ERROR -    Download from: https://github.com/javvi51/edocr2/releases/tag/download_recognizers
edocr2-api_1  | 2025-11-13 10:00:00 - __main__ - WARNING - ⚠️ eDOCr2 API will return empty results until models are installed
```

---

### Step 3: API 테스트

모델 로드 후 실제 OCR을 테스트합니다.

```bash
# Health check
curl http://localhost:5001/api/v1/health

# OCR 테스트
curl -X POST http://localhost:5001/api/v1/ocr \
  -F "file=@test_samples/sample_drawing.pdf" \
  -F "extract_dimensions=true" \
  -F "extract_gdt=true" \
  -F "extract_text=true"
```

**예상 응답 (모델 로드 성공)**:
```json
{
  "status": "success",
  "data": {
    "dimensions": [
      {
        "value": 100.0,
        "unit": "mm",
        "type": "linear",
        "tolerance": "±0.1",
        "location": {"x": 450, "y": 320}
      }
    ],
    "gdt": [
      {
        "type": "flatness",
        "value": 0.05,
        "datum": "A",
        "location": {"x": 200, "y": 150}
      }
    ],
    "text": {
      "drawing_number": "DWG-001",
      "revision": "Rev.1"
    },
    "tables": [...]
  },
  "processing_time": 5.234,
  "file_id": "..."
}
```

**예상 응답 (모델 없음)**:
```json
{
  "status": "success",
  "data": {
    "dimensions": [],
    "gdt": [],
    "text": {},
    "warning": "eDOCr2 models not found. Download from GitHub Releases."
  },
  "processing_time": 0.001,
  "file_id": "..."
}
```

---

## 🔧 Troubleshooting

### 문제 1: 모델 파일을 찾을 수 없음

**증상**:
```
❌ GD&T model not found: .../recognizer_gdts.keras
```

**해결**:
1. 모델 파일 위치 확인:
   ```bash
   ls -la /home/uproot/ax/opensource/01-immediate/edocr2/edocr2/models/
   ```

2. 파일이 없으면 다시 다운로드:
   - https://github.com/javvi51/edocr2/releases/tag/download_recognizers

3. 파일 권한 확인:
   ```bash
   chmod 644 /home/uproot/ax/opensource/01-immediate/edocr2/edocr2/models/*.keras
   ```

### 문제 2: TensorFlow 에러

**증상**:
```
ImportError: cannot import name 'Recognizer' from 'edocr2.keras_ocr.recognition'
```

**해결**:
1. TensorFlow 설치 확인:
   ```bash
   docker-compose exec edocr2-api python -c "import tensorflow as tf; print(tf.__version__)"
   ```

2. 의존성 재설치:
   ```bash
   docker-compose build --no-cache edocr2-api
   docker-compose up -d edocr2-api
   ```

### 문제 3: GPU 메모리 부족

**증상**:
```
tensorflow.python.framework.errors_impl.ResourceExhaustedError: OOM when allocating tensor
```

**해결**:
1. GPU 메모리 증가 설정 (이미 적용됨):
   ```python
   gpus = tf.config.list_physical_devices('GPU')
   for gpu in gpus:
       tf.config.experimental.set_memory_growth(gpu, True)
   ```

2. 또는 CPU 사용:
   ```bash
   # docker-compose.yml에서 GPU 제거
   # deploy:
   #   resources:
   #     reservations:
   #       devices: []  # GPU 비활성화
   ```

### 문제 4: 처리 속도 느림

**증상**: OCR 처리에 30초 이상 소요

**해결**:
1. **GPU 사용 권장** (CPU 대비 10x 빠름)
   - NVIDIA GPU: RTX 3090 (24GB) 권장
   - 최소: GTX 1080 (8GB)

2. 이미지 크기 축소:
   ```python
   # api_server.py의 process_ocr 함수에서
   max_img_size=1048  # 기본값
   # → max_img_size=512  # 속도 우선
   ```

---

## 📊 Performance Expectations

### 하드웨어별 예상 처리 시간

| 하드웨어 | 치수 추출 | GD&T 추출 | 전체 OCR | 비고 |
|----------|----------|----------|----------|------|
| **RTX 3090 (24GB)** | 2-3초 | 1-2초 | 5-7초 | 권장 |
| **GTX 1080 (8GB)** | 3-5초 | 2-3초 | 8-12초 | 최소 사양 |
| **CPU (i7-12700K)** | 20-30초 | 10-15초 | 50-80초 | 느림 |

### 정확도 목표

| 항목 | 목표 정확도 | 실제 성능 (논문) |
|------|------------|-----------------|
| **치수 추출** | 90%+ | 93.75% (Recall) |
| **GD&T 추출** | 85%+ | ~90% |
| **텍스트 추출** | 90%+ | <1% CER |

---

## 📚 References

- **eDOCr2 GitHub**: https://github.com/javvi51/edocr2
- **eDOCr2 Releases**: https://github.com/javvi51/edocr2/releases/tag/download_recognizers
- **eDOCr2 Paper**: http://dx.doi.org/10.2139/ssrn.5045921
- **License**: MIT

---

## ✅ Checklist

완료 시 체크하세요:

- [ ] 모델 파일 6개 다운로드 완료
- [ ] 모델 파일을 올바른 디렉토리에 배치
- [ ] Docker 이미지 재빌드 완료
- [ ] 컨테이너 시작 로그에서 "✅ All models loaded" 확인
- [ ] API 테스트로 실제 OCR 결과 확인 (빈 배열 아님)
- [ ] 처리 시간 < 10초 (GPU 사용 시)

---

**작성일**: 2025-11-13
**버전**: 1.0.0
**상태**: eDOCr2 실제 파이프라인 통합 완료
