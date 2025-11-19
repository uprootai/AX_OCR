# eDOCr2 실제 구현 통합 계획

> 작성일: 2025-11-13
> 우선순위: 🔴 **긴급 (Priority 1)**
> 예상 소요: 2-3일
> 영향: 파이프라인 40% 기능 복구

---

## 🚨 문제 정의

### 현재 상황

**파일**: `edocr2-api/api_server.py` (122-149줄)

```python
def process_ocr(...):
    """
    TODO: 실제 eDOCr2 파이프라인 연동
    현재는 Mock 데이터 반환
    """

    # 실제 OCR 엔진 임포트 모두 주석 처리
    # from edocr2.keras_ocr import pipeline    # ❌
    # from edocr2.tools import ocr_pipelines   # ❌

    time.sleep(2)  # 가짜 지연

    return {
        "dimensions": [],  # 🚨 항상 빈 배열
        "gdt": [],         # 🚨 항상 빈 배열
        "text": {"drawing_number": "MOCK-001"}  # 🚨 하드코딩
    }
```

### 영향 범위

1. **치수 추출 0%**: dimensions 배열 항상 비어있음
2. **GD&T 추출 0%**: gdt 배열 항상 비어있음
3. **Gateway 앙상블 실패**: YOLO bbox + eDOCr 값 병합 불가
4. **전체 파이프라인 마비**: 핵심 기능 동작 안 함

---

## 🎯 목표

**eDOCr2 Mock 구현을 실제 OCR 엔진으로 교체**

### 성공 기준

1. ✅ `dimensions` 배열에 실제 치수 값 반환
2. ✅ `gdt` 배열에 실제 GD&T 기호 반환
3. ✅ 처리 시간 < 10초 (실용 가능 수준)
4. ✅ 정확도 > 80% (F1 Score 기준)

---

## 📋 사용 가능한 옵션

### Option A: `/home/uproot/ax/dev/edocr2` (최우선)

**위치**: `/home/uproot/ax/dev/edocr2/`
**상태**: 미확인 (존재 여부 및 작동 여부 불명)

**장점**:
- ✅ 이미 로컬에 존재 (다운로드 불필요)
- ✅ 수정/커스터마이징 가능
- ✅ 버전 제어 가능

**검증 절차**:
```bash
# 1. 디렉토리 존재 확인
cd /home/uproot/ax/dev/edocr2

# 2. 구조 확인
ls -la
cat README.md

# 3. 의존성 확인
cat requirements.txt

# 4. 테스트 실행
python test_drawing.py tests/sample.jpg

# 5. 결과 확인 (dimensions, gdt 추출 여부)
```

**통합 방법**:
```python
# edocr2-api/api_server.py 수정
import sys
sys.path.insert(0, '/home/uproot/ax/dev/edocr2')

from edocr2.keras_ocr import pipeline
from edocr2.tools import ocr_pipelines

def process_ocr(file_path, ...):
    # 실제 eDOCr2 파이프라인 호출
    results = pipeline.process_drawing(str(file_path))

    return {
        "dimensions": results.get("dimensions", []),
        "gdt": results.get("gdt_symbols", []),
        "text": results.get("text_blocks", {})
    }
```

**예상 소요**: 4-6시간 (작동한다면)

---

### Option B: GitHub edocr2 v2 (공식 최신 버전)

**위치**: `/home/uproot/ax/poc/opensource/01-immediate/edocr2/`
**GitHub**: https://github.com/javvi51/edocr2
**상태**: ✅ 이미 클론됨, 미통합

**장점**:
- ✅ 공식 저장소 (최신 업데이트)
- ✅ 문서화 완료
- ✅ 커뮤니티 지원

**단점**:
- ⚠️ 의존성 많음 (TensorFlow, Keras, OpenCV, Tesseract)
- ⚠️ GPU 메모리 요구량 높음
- ⚠️ 초기 모델 다운로드 필요

**의존성** (requirements.txt 확인 필요):
```txt
tensorflow>=2.15.0
keras>=2.15.0
opencv-python==4.8.1.78
pytesseract==0.3.10
pdf2image==1.16.3
pillow>=10.0.0
numpy>=1.24.0
scipy>=1.11.0
matplotlib>=3.8.0
```

**모델 파일**:
```
models/
├── recognizer_gdts.keras           # GD&T 기호 인식
├── recognizer_dimensions_2.keras   # 치수 인식
└── text_detector.keras             # 텍스트 검출
```

**통합 방법**:
```bash
# 1. Dockerfile 수정
FROM python:3.10-slim

# Tesseract 설치 (시스템 패키지)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# edocr2 복사
COPY opensource/01-immediate/edocr2 /app/edocr2

# 의존성 설치
RUN pip install -r /app/edocr2/requirements.txt

# API 서버
COPY api_server.py .
CMD ["python", "api_server.py"]
```

```python
# api_server.py 수정
import sys
sys.path.insert(0, '/app/edocr2')

from edocr2.main import EDOCr2Pipeline

# 초기화 (startup event)
@app.on_event("startup")
async def load_edocr2():
    global edocr_pipeline
    edocr_pipeline = EDOCr2Pipeline(
        model_dir="/app/edocr2/models",
        device="cuda" if torch.cuda.is_available() else "cpu"
    )

# OCR 처리
def process_ocr(file_path, ...):
    results = edocr_pipeline.process(str(file_path))
    return {
        "dimensions": results["dimensions"],
        "gdt": results["gdt_symbols"],
        "text": results["text_blocks"]
    }
```

**예상 소요**: 1-2일 (의존성 설치 + 통합)

---

### Option C: GitHub eDOCr v1 (안정 버전)

**위치**: `/home/uproot/ax/poc/opensource/01-immediate/eDOCr/`
**GitHub**: https://github.com/[original-author]/eDOCr
**논문**: https://www.frontiersin.org/articles/10.3389/fmtec.2023.1154132/full
**상태**: ✅ 이미 클론됨, 미통합

**장점**:
- ✅ 논문 출판 (검증됨)
- ✅ 의존성 적음 (edocr2보다 가벼움)
- ✅ 안정적 (v1.0.0 릴리스)

**단점**:
- ⚠️ v2보다 성능 낮을 가능성
- ⚠️ 업데이트 중단 가능성

**문서 참조**:
- `docs/opensource/COMPARISON_REPORT.md`: eDOCr v1 vs v2 비교
- `docs/opensource/SOLUTION.md`: 복구 가이드

**성능 (문서 기준)**:
```
eDOCr v1:
- Precision: 19.0%
- Recall: 5.5%
- F1: 8.3%

⚠️ 주의: 이 성능은 Mock 구현 테스트 결과일 수 있음
실제 eDOCr v1 구현은 논문 기준 훨씬 높을 것으로 예상
```

**통합 방법**: Option B와 유사

**예상 소요**: 1-2일

---

### Option D: VL API로 임시 대체 (빠른 해결책)

**현재 상태**: ✅ 이미 구현되어 있음
**파일**: `vl-api/api_server.py`

**장점**:
- ✅ 즉시 사용 가능 (코드 수정만)
- ✅ 정확도 95%+ (eDOCr보다 높음)
- ✅ 유연함 (다양한 도면 처리)

**단점**:
- ⚠️ 비용: $0.01-0.10/이미지
- ⚠️ 속도: 5-30초 (느림)
- ⚠️ API 키 필요
- ⚠️ 외부 의존성

**Gateway 수정**:
```python
# gateway-api/api_server.py 수정

# eDOCr2 대신 VL API 호출
if use_vl_fallback or EDOCR2_UNAVAILABLE:
    vl_response = await client.post(
        f"{VL_API_URL}/api/v1/extract_dimensions",
        files={"file": image_bytes}
    )
    ocr_results = vl_response.json()
else:
    # 기존 eDOCr2 호출
    edocr_response = await client.post(...)
```

**예상 소요**: 4시간 (설정 + 테스트)

**권장**: 장기 해결책 아님, Option A/B/C 구현 전까지만 사용

---

## 🔄 권장 통합 전략

### Phase 1: 검증 (Day 1 오전)

```bash
# Step 1: Option A 검증
cd /home/uproot/ax/dev/edocr2
python test_drawing.py tests/sample.jpg

# 결과 확인:
# - dimensions 배열에 값이 있는가?
# - gdt 배열에 값이 있는가?
# - 처리 시간 < 10초?

# Step 2: 작동하지 않으면 Option B로
cd /home/uproot/ax/poc/opensource/01-immediate/edocr2
pip install -r requirements.txt
python test.py
```

### Phase 2: 통합 (Day 1 오후 ~ Day 2)

**Option A 작동 시**:
```bash
# 1. edocr2-api/api_server.py 수정
vim edocr2-api/api_server.py

# 2. Dockerfile 수정 (경로 추가)
vim edocr2-api/Dockerfile

# 3. 로컬 테스트
cd edocr2-api
python api_server.py

# 4. 컨테이너 빌드 & 재시작
cd ..
docker-compose build edocr2-api
docker-compose up -d edocr2-api

# 5. Gateway 테스트
curl -X POST http://localhost:8000/api/v1/process \
  -F "file=@test_drawing.pdf"
```

**Option B 필요 시**:
```bash
# 1. 의존성 큰 Dockerfile 작성
cat > edocr2-api/Dockerfile.full <<EOF
FROM python:3.10-slim

RUN apt-get update && apt-get install -y \\
    tesseract-ocr \\
    libtesseract-dev \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY opensource/01-immediate/edocr2 /app/edocr2
RUN pip install -r /app/edocr2/requirements.txt

COPY api_server.py .
CMD ["python", "api_server.py"]
EOF

# 2. 빌드 (시간 오래 걸림)
docker build -f edocr2-api/Dockerfile.full -t edocr2-api:full .

# 3. docker-compose.yml 수정
vim docker-compose.yml
# image: edocr2-api:full

# 4. 재시작
docker-compose up -d edocr2-api
```

### Phase 3: 검증 (Day 2 오후)

**테스트 케이스**:
```bash
# 1. 기본 동작 확인
curl -X POST http://localhost:5001/api/v1/ocr \
  -F "file=@tests/sample_drawing.pdf" \
  | jq '.dimensions | length'

# 기대 결과: > 0 (비어있지 않음)

# 2. Gateway 통합 확인
curl -X POST http://localhost:8000/api/v1/process \
  -F "file=@tests/sample_drawing.pdf" \
  | jq '.data.ocr_results.dimensions | length'

# 기대 결과: > 0

# 3. 정확도 측정 (별도 스크립트)
python tests/measure_accuracy.py tests/labeled_drawings/
```

### Phase 4: 문서화 (Day 3)

```bash
# 1. 통합 과정 문서화
vim edocr2-api/INTEGRATION_LOG.md

# 2. 성능 측정 결과 기록
vim docs/testing/EDOCR2_PERFORMANCE_REPORT.md

# 3. 사용 가이드 업데이트
vim edocr2-api/README.md
```

---

## ⚠️ 예상 문제 및 해결책

### 문제 1: Tesseract 설치 실패

**증상**:
```
ERROR: Could not find tesseract executable
```

**해결**:
```dockerfile
# Dockerfile에 추가
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    libtesseract-dev
```

### 문제 2: GPU 메모리 부족

**증상**:
```
RuntimeError: CUDA out of memory
```

**해결**:
```python
# CPU 모드로 전환
device = "cpu"

# 또는 배치 크기 줄이기
batch_size = 1
```

### 문제 3: 모델 파일 없음

**증상**:
```
FileNotFoundError: models/recognizer_gdts.keras
```

**해결**:
```bash
# GitHub Releases에서 다운로드
cd /app/edocr2/models
wget https://github.com/javvi51/edocr2/releases/download/v2.0/models.zip
unzip models.zip
```

### 문제 4: 처리 시간 너무 오래 걸림 (>30초)

**원인**: 이미지 크기가 너무 큼

**해결**:
```python
# 이미지 다운샘플링
from PIL import Image

img = Image.open(file_path)
if img.width > 2000:
    scale = 2000 / img.width
    new_size = (2000, int(img.height * scale))
    img = img.resize(new_size, Image.LANCZOS)
    img.save("/tmp/resized.jpg")
    file_path = "/tmp/resized.jpg"
```

### 문제 5: dimensions/gdt 배열 여전히 비어있음

**원인**: 후처리 로직 누락

**해결**:
```python
# OCR 원시 결과를 구조화된 데이터로 변환
def parse_dimensions(raw_text):
    """
    "φ476" → {"type": "diameter", "value": 476, "unit": "mm"}
    "50±0.5" → {"value": 50, "tolerance": {"upper": 0.5, "lower": -0.5}}
    """
    dimensions = []
    # 정규표현식 또는 ML 파싱
    ...
    return dimensions
```

---

## 📊 성공 지표

### 통합 전 (Mock)

```json
{
  "dimensions": [],           // 🔴 빈 배열
  "gdt": [],                  // 🔴 빈 배열
  "text": {
    "drawing_number": "MOCK-001"  // 🔴 하드코딩
  }
}
```

### 통합 후 (Real)

```json
{
  "dimensions": [
    {
      "type": "diameter",
      "value": 476.0,
      "unit": "mm",
      "bbox": {"x": 150, "y": 200, "width": 60, "height": 20},
      "confidence": 0.92
    },
    {
      "type": "linear",
      "value": 370.0,
      "unit": "mm",
      "tolerance": {"upper": 0.1, "lower": -0.1},
      "bbox": {...},
      "confidence": 0.88
    }
  ],
  "gdt": [
    {
      "symbol": "⊥",
      "type": "perpendicularity",
      "tolerance": 0.05,
      "datum": "A",
      "bbox": {...},
      "confidence": 0.85
    }
  ],
  "text": {
    "drawing_number": "A12-311197-9",
    "revision": "Rev.2",
    "title": "Interm Shaft-Acc",
    "material": "Steel"
  }
}
```

### KPI

| 지표 | 목표 | 현재 (Mock) | 통합 후 |
|------|------|-------------|---------|
| **dimensions.length** | > 5 | 0 | 10-20 |
| **gdt.length** | > 2 | 0 | 3-8 |
| **F1 Score** | > 80% | 0% | 85-90% |
| **처리 시간** | < 10초 | 2초 (가짜) | 5-8초 |

---

## 🔗 관련 문서

- `docs/opensource/COMPARISON_REPORT.md`: eDOCr v1/v2 성능 비교
- `docs/opensource/SOLUTION.md`: 복구 가이드
- `docs/opensource/README.md`: 15개 오픈소스 저장소 조사
- `edocr2-api/api_server.py`: 현재 Mock 구현

---

## 🎯 Action Items

### 즉시 실행 (1시간 내)

- [ ] `/home/uproot/ax/dev/edocr2` 존재 여부 확인
- [ ] 존재하면 테스트 실행
- [ ] 작동하면 통합 시작
- [ ] 작동 안 하면 Option B 준비

### 1일차

- [ ] edocr2-api/api_server.py 실제 구현으로 교체
- [ ] Dockerfile 수정 (의존성 추가)
- [ ] 로컬 테스트 통과

### 2일차

- [ ] Docker 이미지 빌드
- [ ] 컨테이너 재시작
- [ ] Gateway 통합 테스트
- [ ] 정확도 측정

### 3일차

- [ ] 문서화
- [ ] 성능 보고서 작성
- [ ] README 업데이트

---

**다음 단계**: `/home/uproot/ax/dev/edocr2` 디렉토리 검증
