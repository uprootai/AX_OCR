# edocr2 비교 분석 보고서

**분석 날짜**: 2025-10-29
**분석자**: Claude Code POC Team

---

## 🚨 핵심 발견사항

### **현재 POC는 실제 eDOCr2를 사용하지 않고 Mock 데이터를 반환하고 있습니다!**

---

## 1. 현재 시스템 구조

### 1.1 경로 구조
```
/home/uproot/ax/
├── poc/
│   └── edocr2-api/          # API 서버 (Mock 데이터만)
│       ├── api_server.py    # FastAPI 서버
│       ├── requirements.txt # API 서버 종속성만
│       └── Dockerfile
│
├── dev/
│   └── edocr2/              # 실제 eDOCr2 구현
│       ├── edocr2/          # Python 패키지
│       ├── test_drawing.py  # 테스트 스크립트
│       └── requirements.txt # 완전한 종속성
│
└── opensource/
    └── 01-immediate/
        └── edocr2/          # GitHub 최신 버전 (방금 클론)
```

### 1.2 현재 API 서버 분석

**파일**: `/home/uproot/ax/poc/edocr2-api/api_server.py`

**Line 33**:
```python
EDOCR2_PATH = Path(__file__).parent.parent.parent / "dev" / "edocr2"
sys.path.insert(0, str(EDOCR2_PATH))
```
→ `/home/uproot/ax/dev/edocr2`를 참조하려 했으나...

**Line 122-149**: `process_ocr()` 함수
```python
def process_ocr(
    file_path: Path,
    extract_dimensions: bool = True,
    extract_gdt: bool = True,
    extract_text: bool = True,
    use_vl_model: bool = False,
    visualize: bool = False
) -> Dict[str, Any]:
    """
    OCR 처리 로직 (실제 eDOCr2 연동)

    TODO: 실제 eDOCr2 파이프라인 연동
    현재는 Mock 데이터 반환
    """
    try:
        # Import eDOCr2 components
        # from edocr2.keras_ocr import pipeline    # ❌ 주석 처리됨
        # from edocr2.tools import ocr_pipelines   # ❌ 주석 처리됨

        logger.info(f"Processing file: {file_path}")

        # Simulate processing time
        time.sleep(2)  # 🚨 단순히 2초 대기

        # Mock result (실제 구현 시 eDOCr2 파이프라인으로 대체)
        result = {
            "dimensions": [],  # 🚨 빈 배열
            "gdt": [],         # 🚨 빈 배열
            "text": {          # 🚨 Mock 데이터
                "drawing_number": "MOCK-001",
                "revision": "A",
                "title": "Test Drawing",
                "material": "Steel",
                "notes": ["This is mock data"],
                "total_blocks": 1
            }
        }

        if visualize:
            result["visualization_url"] = f"/api/v1/visualization/{file_path.name}"

        return result
```

**결론**:
- ✅ API 서버는 작동 중
- ❌ 실제 OCR은 수행하지 않음
- ❌ Mock 데이터만 반환
- ❌ 이것이 "성능이 안나온다"고 느낀 원인

---

## 2. 버전 비교

### 2.1 현재 사용 중인 버전

| 경로 | Git 상태 | 커밋 |
|------|----------|------|
| `/home/uproot/ax/poc/edocr2-api/` | Git 저장소 | `1a4b3f7` "Initial commit: AX 실증산단 마이크로서비스 API 시스템" |
| `/home/uproot/ax/dev/edocr2/` | Git 저장소 | (확인 필요) |

### 2.2 GitHub 최신 버전

| 경로 | Git 상태 | 최신 커밋 |
|------|----------|-----------|
| `/home/uproot/ax/poc/opensource/01-immediate/edocr2/` | Git 저장소 | `f6f9651` "gpt_results" |

**최근 5개 커밋**:
```
f6f9651 gpt_results
801b7e8 upload_docs
414bf4b docs1
d44eadf docs1
a077927 ocr_final?
```

### 2.3 종속성 비교

#### POC API 서버 (`/home/uproot/ax/poc/edocr2-api/requirements.txt`)
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
pydantic==2.5.0
aiofiles==23.2.1
pillow==10.1.0
numpy==1.24.3

# Note: Full eDOCr2 dependencies will be loaded from mounted volume
# 🚨 실제 OCR 종속성들이 주석 처리됨:
# opencv-python==4.8.1.78
# tensorflow==2.15.0
# keras==2.15.0
# pytesseract==0.3.10
# pdf2image==1.16.3
```

#### GitHub edocr2 (`/home/uproot/ax/poc/opensource/01-immediate/edocr2/requirements.txt`)
```
pdf2image
opencv-python
pandas
validators
imgaug
scikit-image
scikit-learn
tqdm
efficientnet == 1.0.0
essential_generators
editdistance
pyclipper
python-dotenv
accelerate
tf-keras
sentence-transformers
```

**차이점**:
- POC API: API 서버 종속성만 (FastAPI, Uvicorn)
- GitHub: 완전한 OCR 종속성 (TensorFlow, OpenCV, Tesseract 등)

---

## 3. 문제 원인 분석

### 3.1 왜 Mock 데이터만 반환하는가?

1. **의도적 설계**:
   - API 서버를 먼저 구축하고 실제 OCR 연동을 나중에 하려는 계획
   - `api_server.py`의 TODO 주석이 이를 명시

2. **종속성 문제**:
   - API 컨테이너에 TensorFlow, OpenCV 등이 설치되지 않음
   - Docker 이미지 크기를 줄이기 위한 의도적 선택일 수 있음

3. **마운트 볼륨 계획**:
   - requirements.txt의 주석: "Full eDOCr2 dependencies will be loaded from mounted volume"
   - 별도 컨테이너 또는 볼륨에서 실제 OCR 실행을 계획했을 가능성

### 3.2 성능 문제의 진짜 원인

**사용자 보고**: "성능이 안나오는것 같아서요"

**실제 상황**:
- ✅ API 응답 속도는 정상 (2초 고정)
- ❌ 하지만 실제 OCR이 수행되지 않음
- ❌ 항상 같은 Mock 데이터 반환
- ❌ 파일 내용과 무관하게 동일한 결과

**증상**:
- 어떤 도면을 업로드해도 같은 결과
- "MOCK-001", "Test Drawing" 등의 고정된 텍스트
- dimensions, gdt 배열이 항상 비어있음

---

## 4. 해결 방안

### 4.1 즉시 조치 (1-2일)

#### Option A: `/home/uproot/ax/dev/edocr2` 연동 (권장)

**현재 상태 확인 필요**:
```bash
cd /home/uproot/ax/dev/edocr2
git log --oneline -5
ls -la edocr2/
python test_drawing.py  # 작동 여부 확인
```

**통합 단계**:
1. `/home/uproot/ax/dev/edocr2`가 작동하는지 확인
2. `api_server.py`의 주석 해제:
   ```python
   from edocr2.keras_ocr import pipeline
   from edocr2.tools import ocr_pipelines
   ```
3. `process_ocr()` 함수를 실제 eDOCr2 파이프라인으로 교체
4. Docker 컨테이너에 필요한 종속성 추가

**장점**:
- ✅ 빠른 해결 (이미 설치된 코드 활용)
- ✅ 테스트된 환경

**단점**:
- ⚠️ `/home/uproot/ax/dev/edocr2`의 상태 불명확

---

#### Option B: GitHub 최신 버전 사용

**통합 단계**:
1. GitHub 최신 버전 검증:
   ```bash
   cd /home/uproot/ax/poc/opensource/01-immediate/edocr2
   pip install -r requirements.txt
   python test_drawing.py tests/test_samples/Candle_holder.jpg
   ```

2. 작동 확인 후 `/home/uproot/ax/dev/edocr2`를 GitHub 버전으로 교체:
   ```bash
   cd /home/uproot/ax/dev
   mv edocr2 edocr2.backup
   cp -r /home/uproot/ax/poc/opensource/01-immediate/edocr2 ./
   ```

3. 모델 다운로드 (GitHub Releases에서):
   ```bash
   # https://github.com/javvi51/edocr2/releases
   # recognizer_gdts.keras
   # recognizer_dimensions_2.keras
   ```

4. API 서버 업데이트

**장점**:
- ✅ 최신 코드 사용
- ✅ 최신 기능 및 버그 수정

**단점**:
- ⚠️ 새로운 환경 설정 필요
- ⚠️ 모델 다운로드 시간

---

### 4.2 단계별 통합 계획

#### Step 1: 환경 검증 (1일)
```bash
# 1. dev edocr2 상태 확인
cd /home/uproot/ax/dev/edocr2
git status
git log --oneline -5

# 2. 테스트 실행
python test_drawing.py tests/test_samples/Candle_holder.jpg

# 3. GitHub 버전 테스트
cd /home/uproot/ax/poc/opensource/01-immediate/edocr2
conda create -n edocr2_test python=3.11 -y
conda activate edocr2_test
pip install -r requirements.txt
python test_drawing.py
```

#### Step 2: API 서버 업데이트 (1일)
```python
# api_server.py 수정

# 1. Import 추가
from edocr2.tools import layer_segm, ocr_pipelines, output_tools
from edocr2.keras_ocr.recognition import Recognizer
from edocr2.keras_ocr.detection import Detector
import tensorflow as tf

# 2. 모델 로드 (앱 시작 시)
@app.on_event("startup")
async def load_models():
    global recognizer_gdt, recognizer_dim, detector

    # Configure GPU
    gpus = tf.config.list_physical_devices('GPU')
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)

    # Load models
    gdt_model = 'edocr2/models/recognizer_gdts.keras'
    dim_model = 'edocr2/models/recognizer_dimensions_2.keras'

    recognizer_gdt = Recognizer(alphabet=ocr_pipelines.read_alphabet(gdt_model))
    recognizer_gdt.model.load_weights(gdt_model)

    recognizer_dim = Recognizer(alphabet=ocr_pipelines.read_alphabet(dim_model))
    recognizer_dim.model.load_weights(dim_model)

    detector = Detector()

    logger.info("Models loaded successfully")

# 3. process_ocr() 함수 교체
def process_ocr(
    file_path: Path,
    extract_dimensions: bool = True,
    extract_gdt: bool = True,
    extract_text: bool = True,
    use_vl_model: bool = False,
    visualize: bool = False
) -> Dict[str, Any]:
    """실제 eDOCr2 파이프라인 실행"""
    import cv2
    from pdf2image import convert_from_path

    # 이미지 로드
    if file_path.suffix.lower() == '.pdf':
        img = convert_from_path(file_path)
        img = np.array(img[0])
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, img = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        img = cv2.merge([img, img, img])
    else:
        img = cv2.imread(str(file_path))

    # Segmentation
    img_boxes, frame, gdt_boxes, tables, dim_boxes = layer_segm.segment_img(
        img, autoframe=True, frame_thres=0.7, GDT_thres=0.02, binary_thres=127
    )

    # OCR Tables
    process_img = img.copy()
    table_results, updated_tables, process_img = ocr_pipelines.ocr_tables(
        tables, process_img, language='eng'
    )

    # OCR GD&T
    gdt_results, updated_gdt_boxes, process_img = ocr_pipelines.ocr_gdt(
        process_img, gdt_boxes, recognizer_gdt
    )

    # OCR Dimensions
    if frame:
        process_img = process_img[frame.y : frame.y + frame.h, frame.x : frame.x + frame.w]

    dimensions, other_info, process_img, dim_tess = ocr_pipelines.ocr_dimensions(
        process_img, detector, recognizer_dim,
        ocr_pipelines.read_alphabet(dim_model),
        frame, dim_boxes, cluster_thres=20, max_img_size=1048,
        language='eng', backg_save=False
    )

    # Format results
    result = {
        "dimensions": dimensions,
        "gdt": gdt_results,
        "text": {
            "drawing_number": table_results.get('drawing_number'),
            "revision": table_results.get('revision'),
            "title": table_results.get('title'),
            "material": table_results.get('material'),
            "notes": other_info,
            "total_blocks": len(tables)
        }
    }

    if visualize:
        mask_img = output_tools.mask_img(
            img, updated_gdt_boxes, updated_tables, dimensions, frame, other_info
        )
        vis_path = RESULTS_DIR / f"{file_path.stem}_visualization.jpg"
        cv2.imwrite(str(vis_path), mask_img)
        result["visualization_url"] = f"/api/v1/visualization/{vis_path.name}"

    return result
```

#### Step 3: Docker 업데이트 (반나절)
```dockerfile
# Dockerfile 수정
FROM python:3.11-slim

# 시스템 종속성
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    libleptonica-dev \
    poppler-utils \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python 종속성
COPY requirements_full.txt .
RUN pip install --no-cache-dir -r requirements_full.txt

# eDOCr2 코드 복사
COPY ../dev/edocr2 /app/edocr2

# API 서버
COPY api_server.py .

CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "5001"]
```

```txt
# requirements_full.txt 생성
# API 서버
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
pydantic==2.5.0
aiofiles==23.2.1

# eDOCr2
pdf2image
opencv-python
pandas
validators
imgaug
scikit-image
scikit-learn
tqdm
efficientnet==1.0.0
essential_generators
editdistance
pyclipper
python-dotenv
accelerate
tf-keras
sentence-transformers
pytesseract
pillow
numpy
```

#### Step 4: 테스트 및 검증 (1일)
```bash
# 1. 로컬 테스트
cd /home/uproot/ax/poc/edocr2-api
python api_server.py  # 직접 실행 테스트

# 2. Docker 빌드
docker-compose build edocr2

# 3. Docker 실행
docker-compose up -d edocr2

# 4. API 테스트
curl -X POST "http://localhost:5001/api/v1/ocr" \
  -F "file=@test_drawing.jpg" \
  -F "extract_dimensions=true" \
  -F "extract_gdt=true" \
  -F "extract_text=true"

# 5. 결과 확인
# Mock 데이터가 아닌 실제 OCR 결과가 나오는지 확인
```

---

### 4.3 eDOCr v1 백업 시스템 (선택사항)

**목적**: edocr2에 문제가 있을 경우 eDOCr v1을 사용

**설치**:
```bash
cd /home/uproot/ax/poc/opensource/01-immediate/eDOCr
conda create -n edocr_v1 python=3.9 -y
conda activate edocr_v1
pip install -r requirements.txt
pip install .

# 테스트
python eDOCr/ocr_it.py tests/test_samples/Candle_holder.jpg --dest-folder tests/test_Results
```

**v1 vs v2 차이점**:
| 기능 | eDOCr v1 | edocr2 (v2) |
|------|----------|-------------|
| 테이블 인식 | ❌ | ✅ |
| LLM 통합 | ❌ | ✅ (Qwen2-VL, GPT-4o) |
| 레이어 세그멘테이션 | 기본 | 향상됨 |
| 커스텀 학습 | ✅ | ✅ |
| Python 버전 | 3.6+ | 3.11 |
| TensorFlow | 2.0+ | CUDA 11.8 |

---

## 5. 예상 결과

### 5.1 수정 전 (현재)
```json
{
  "status": "success",
  "data": {
    "dimensions": [],
    "gdt": [],
    "text": {
      "drawing_number": "MOCK-001",
      "revision": "A",
      "title": "Test Drawing",
      "material": "Steel",
      "notes": ["This is mock data"],
      "total_blocks": 1
    }
  },
  "processing_time": 2.0
}
```

### 5.2 수정 후 (실제 OCR)
```json
{
  "status": "success",
  "data": {
    "dimensions": [
      {
        "type": "linear",
        "value": 50.5,
        "unit": "mm",
        "tolerance": "+0.1/-0.05",
        "location": {"x": 245, "y": 180}
      },
      {
        "type": "diameter",
        "value": 12.0,
        "unit": "mm",
        "tolerance": "±0.05",
        "location": {"x": 320, "y": 250}
      }
    ],
    "gdt": [
      {
        "type": "flatness",
        "value": 0.02,
        "datum": null,
        "location": {"x": 150, "y": 300}
      },
      {
        "type": "perpendicularity",
        "value": 0.05,
        "datum": "A",
        "location": {"x": 180, "y": 320}
      }
    ],
    "text": {
      "drawing_number": "DRW-2024-001",
      "revision": "B",
      "title": "Candle Holder Base",
      "material": "Aluminum 6061-T6",
      "notes": [
        "All dimensions in mm",
        "Surface finish: Ra 3.2",
        "Deburr all edges"
      ],
      "total_blocks": 3
    },
    "visualization_url": "/api/v1/visualization/drawing_mask.jpg"
  },
  "processing_time": 8.5
}
```

---

## 6. 타임라인

### Week 1 (현재 주)
- [x] 문제 원인 파악 ✅
- [x] 저장소 비교 분석 ✅
- [ ] `/home/uproot/ax/dev/edocr2` 상태 확인
- [ ] GitHub edocr2 테스트
- [ ] 통합 방법 결정 (Option A 또는 B)

### Week 2
- [ ] API 서버 업데이트
- [ ] Docker 이미지 재빌드
- [ ] 로컬 테스트
- [ ] 프로덕션 배포

### Week 3
- [ ] eDOCr v1 백업 시스템 구축
- [ ] v1 vs v2 성능 비교 테스트
- [ ] 최종 성능 보고서 작성

---

## 7. 체크리스트

### 즉시 확인 사항
- [ ] `/home/uproot/ax/dev/edocr2`가 작동하는가?
- [ ] 모델 파일이 있는가? (`recognizer_*.keras`)
- [ ] GitHub edocr2를 테스트할 수 있는가?
- [ ] TensorFlow + CUDA가 설치되어 있는가?

### 통합 전 준비
- [ ] 백업 생성 (`/home/uproot/ax/poc/edocr2-api.backup`)
- [ ] 테스트 이미지 준비
- [ ] 예상 결과 정의
- [ ] 롤백 계획 수립

### 통합 후 검증
- [ ] Mock 데이터가 아닌 실제 결과 반환
- [ ] 다양한 도면으로 테스트
- [ ] 처리 시간 측정 (2초 → 5-10초)
- [ ] 메모리 사용량 모니터링
- [ ] GPU 활용 확인

---

## 8. 참고 자료

### 문서
- eDOCr v1 논문: https://www.frontiersin.org/articles/10.3389/fmtec.2023.1154132/full
- edocr2 논문: http://dx.doi.org/10.2139/ssrn.5045921
- GitHub edocr2: https://github.com/javvi51/edocr2

### 주요 파일 위치
- API 서버: `/home/uproot/ax/poc/edocr2-api/api_server.py`
- dev edocr2: `/home/uproot/ax/dev/edocr2/`
- GitHub edocr2: `/home/uproot/ax/poc/opensource/01-immediate/edocr2/`
- 테스트 이미지: `/home/uproot/ax/poc/opensource/01-immediate/edocr2/tests/test_samples/`

---

**다음 단계**: `/home/uproot/ax/dev/edocr2` 상태 확인 및 테스트 실행

