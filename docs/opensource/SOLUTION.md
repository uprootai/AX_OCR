# 🚨 긴급 해결 방안: edocr2 실제 OCR 활성화

## 문제 요약

**발견된 문제**:
1. ✅ API 서버는 정상 작동
2. ❌ 실제 OCR은 수행되지 않음 (Mock 데이터만 반환)
3. ❌ 모델 파일이 다운로드되지 않음 (`/home/uproot/ax/dev/edocr2/models/` 비어있음)
4. ❌ API 서버와 edocr2 연동 코드가 주석 처리됨

**사용자 증상**: "성능이 안나오는것 같아서요"
**실제 원인**: Mock 데이터만 반환되어 실제 OCR이 작동하지 않음

---

## 즉시 해결 방안

### 🎯 가장 빠른 해결책: eDOCr v1 사용

edocr2가 완전히 설정되지 않았으므로, **eDOCr v1을 먼저 통합**하는 것이 가장 빠릅니다.

#### 장점:
- ✅ 모델이 자동 다운로드됨 (GitHub Releases에서)
- ✅ 설치 간단 (`pip install eDOCr`)
- ✅ 1-2시간 내 통합 가능
- ✅ 프로덕션 준비 완료된 v1

#### 단점:
- ⚠️ v2보다 기능 적음 (테이블 인식, LLM 없음)
- ⚠️ 구버전 아키텍처

---

## Step-by-Step 해결 가이드

### 옵션 A: eDOCr v1 즉시 통합 (권장) ⏱️ 2-3시간

#### Step 1: eDOCr v1 설치 및 테스트 (30분)

```bash
# 1. Conda 환경 생성
conda create -n edocr_v1 python=3.9 -y
conda activate edocr_v1

# 2. eDOCr v1 설치
cd /home/uproot/ax/poc/opensource/01-immediate/eDOCr
pip install -r requirements.txt
pip install .

# 3. 테스트 실행
python eDOCr/ocr_it.py tests/test_samples/Candle_holder.jpg --dest-folder /tmp/edocr_test

# 4. 결과 확인
ls -la /tmp/edocr_test/
# 다음 파일들이 생성되어야 함:
# - Candle_holder_1_process.jpg
# - Candle_holder_1_boxes.jpg
# - Candle_holder_1_mask.jpg
# - Candle_holder_data.json
```

#### Step 2: API 서버 업데이트 (1시간)

**파일**: `/home/uproot/ax/poc/edocr2-api/api_server_edocr_v1.py` (새 파일)

```python
"""
eDOCr v1 API Server
"""
import os
import sys
import json
import time
import shutil
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

import cv2
import numpy as np
from skimage import io

# Add eDOCr to path
EDOCR_PATH = Path("/home/uproot/ax/poc/opensource/01-immediate/eDOCr")
sys.path.insert(0, str(EDOCR_PATH))

# Import eDOCr v1
from eDOCr import tools
from eDOCr.keras_ocr import tools as keras_tools
import string

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="eDOCr v1 API",
    description="Engineering Drawing OCR Service (eDOCr v1)",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Directories
UPLOAD_DIR = Path("/home/uproot/ax/poc/edocr2-api/uploads")
RESULTS_DIR = Path("/home/uproot/ax/poc/edocr2-api/results")
UPLOAD_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

# Load eDOCr v1 models (on startup)
GDT_symbols = '⏤⏥○⌭⌒⌓⏊∠⫽⌯⌖◎↗⌰'
FCF_symbols = 'ⒺⒻⓁⓂⓅⓈⓉⓊ'
Extra = '(),.+-±:/°"⌀'

alphabet_dimensions = string.digits + 'AaBCDRGHhMmnx' + Extra
alphabet_infoblock = string.digits + string.ascii_letters + ',.:-/'
alphabet_gdts = string.digits + ',.⌀ABCD' + GDT_symbols

model_infoblock = None
model_dimensions = None
model_gdts = None

@app.on_event("startup")
async def load_models():
    global model_infoblock, model_dimensions, model_gdts

    logger.info("Loading eDOCr v1 models...")

    # Models auto-download from GitHub Releases
    model_infoblock = keras_tools.download_and_verify(
        url="https://github.com/javvi51/eDOCr/releases/download/v1.0.0/recognizer_infoblock.h5",
        filename="recognizer_infoblock.h5",
        sha256="e0a317e07ce75235f67460713cf1b559e02ae2282303eec4a1f76ef211fcb8e8",
    )

    model_dimensions = keras_tools.download_and_verify(
        url="https://github.com/javvi51/eDOCr/releases/download/v1.0.0/recognizer_dimensions.h5",
        filename="recognizer_dimensions.h5",
        sha256="a1c27296b1757234a90780ccc831762638b9e66faf69171f5520817130e05b8f",
    )

    model_gdts = keras_tools.download_and_verify(
        url="https://github.com/javvi51/eDOCr/releases/download/v1.0.0/recognizer_gdts.h5",
        filename="recognizer_gdts.h5",
        sha256="58acf6292a43ff90a344111729fc70cf35f0c3ca4dfd622016456c0b29ef2a46",
    )

    logger.info("✅ eDOCr v1 models loaded successfully!")


# Models
class OCRRequest(BaseModel):
    extract_dimensions: bool = Field(True)
    extract_gdt: bool = Field(True)
    extract_text: bool = Field(True)
    visualize: bool = Field(False)
    remove_watermark: bool = Field(False)
    cluster_threshold: int = Field(20, description="Pixel distance for clustering")


class OCRResponse(BaseModel):
    status: str
    data: Dict[str, Any]
    processing_time: float
    file_id: str


def process_ocr_v1(
    file_path: Path,
    extract_dimensions: bool = True,
    extract_gdt: bool = True,
    extract_text: bool = True,
    visualize: bool = False,
    remove_watermark: bool = False,
    cluster_threshold: int = 20
) -> Dict[str, Any]:
    """
    eDOCr v1 실제 OCR 처리
    """
    try:
        logger.info(f"Processing with eDOCr v1: {file_path}")

        # Load image
        from pdf2image import convert_from_path

        if file_path.suffix.lower() == '.pdf':
            images = convert_from_path(str(file_path))
            img = np.array(images[0])
        else:
            img = cv2.imread(str(file_path))

        # Remove watermark if requested
        if remove_watermark:
            img = tools.watermark.handle(img)

        # Box detection
        class_list, img_boxes = tools.box_tree.findrect(img)

        # Process rectangles
        boxes_infoblock, gdt_boxes, cl_frame, process_img = tools.img_process.process_rect(class_list, img)

        # Save processed image
        process_img_path = RESULTS_DIR / f"{file_path.stem}_process.jpg"
        io.imsave(str(process_img_path), process_img)

        # OCR infoblock
        infoblock_dict = tools.pipeline_infoblock.read_infoblocks(
            boxes_infoblock, img, alphabet_infoblock, model_infoblock
        )

        # OCR GD&T
        gdt_dict = tools.pipeline_gdts.read_gdtbox1(
            gdt_boxes, alphabet_gdts, model_gdts,
            alphabet_dimensions, model_dimensions
        )

        # OCR dimensions
        dimension_dict = tools.pipeline_dimensions.read_dimensions(
            str(process_img_path), alphabet_dimensions, model_dimensions, cluster_threshold
        )

        # Format results
        result = {
            "dimensions": dimension_dict if extract_dimensions else [],
            "gdt": gdt_dict if extract_gdt else [],
            "text": infoblock_dict if extract_text else {}
        }

        # Visualization
        if visualize:
            color_palette = {
                'infoblock': (180, 220, 250),
                'gdts': (94, 204, 243),
                'dimensions': (93, 206, 175),
                'frame': (167, 234, 82),
                'flag': (241, 65, 36)
            }

            mask_img = tools.output.mask_the_drawing(
                img, infoblock_dict, gdt_dict, dimension_dict, cl_frame, color_palette
            )

            mask_path = RESULTS_DIR / f"{file_path.stem}_mask.jpg"
            io.imsave(str(mask_path), mask_img)
            result["visualization_url"] = f"/api/v1/visualization/{mask_path.name}"

        # Save boxes image
        boxes_path = RESULTS_DIR / f"{file_path.stem}_boxes.jpg"
        io.imsave(str(boxes_path), img_boxes)

        # Save data
        tools.output.record_data(
            str(RESULTS_DIR), file_path.stem,
            infoblock_dict, gdt_dict, dimension_dict
        )

        logger.info("✅ eDOCr v1 processing complete!")
        return result

    except Exception as e:
        logger.error(f"❌ eDOCr v1 processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")


@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "eDOCr v1 API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "models_loaded": all([model_infoblock, model_dimensions, model_gdts])
    }


@app.post("/api/v1/ocr", response_model=OCRResponse)
async def process_drawing(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    extract_dimensions: bool = Form(True),
    extract_gdt: bool = Form(True),
    extract_text: bool = Form(True),
    visualize: bool = Form(False),
    remove_watermark: bool = Form(False),
    cluster_threshold: int = Form(20)
):
    """
    도면 OCR 처리 (eDOCr v1)
    """
    start_time = time.time()

    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    file_ext = file.filename.rsplit('.', 1)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed: {ALLOWED_EXTENSIONS}"
        )

    # Save uploaded file
    file_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    file_path = UPLOAD_DIR / file_id

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    logger.info(f"📁 File saved: {file_path}")

    # Process OCR
    try:
        result = process_ocr_v1(
            file_path,
            extract_dimensions=extract_dimensions,
            extract_gdt=extract_gdt,
            extract_text=extract_text,
            visualize=visualize,
            remove_watermark=remove_watermark,
            cluster_threshold=cluster_threshold
        )

        processing_time = time.time() - start_time

        # Cleanup in background
        background_tasks.add_task(lambda: file_path.unlink(missing_ok=True))

        return OCRResponse(
            status="success",
            data=result,
            processing_time=processing_time,
            file_id=file_id
        )

    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/visualization/{filename}")
async def get_visualization(filename: str):
    """시각화 이미지 반환"""
    file_path = RESULTS_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Visualization not found")

    return FileResponse(file_path)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)
```

#### Step 3: Docker 업데이트 (30분)

**파일**: `/home/uproot/ax/poc/edocr2-api/Dockerfile.v1` (새 파일)

```dockerfile
FROM python:3.9-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libleptonica-dev \
    poppler-utils \
    libgl1-mesa-glx \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy eDOCr v1
COPY ../opensource/01-immediate/eDOCr /app/eDOCr
RUN cd /app/eDOCr && pip install -r requirements.txt && pip install .

# Copy API server
COPY api_server_edocr_v1.py /app/api_server.py
COPY requirements_v1.txt /app/requirements.txt

# Install API dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create directories
RUN mkdir -p /app/uploads /app/results

# Expose port
EXPOSE 5001

CMD ["python", "api_server.py"]
```

**파일**: `/home/uproot/ax/poc/edocr2-api/requirements_v1.txt` (새 파일)

```
# API
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
pydantic==2.5.0
aiofiles==23.2.1

# eDOCr v1 dependencies (from eDOCr/requirements.txt)
opencv-python
tensorflow>=2.0.0
Pillow
shapely
anytree
scikit-image
scikit-learn
tqdm
validators
essential_generators
imgaug
fonttools
editdistance
pyclipper
efficientnet==1.0.0
pdf2image
```

#### Step 4: 배포 및 테스트 (30분)

```bash
# 1. 백업
cd /home/uproot/ax/poc/edocr2-api
cp api_server.py api_server_mock.py.backup

# 2. v1 API 서버로 교체
cp api_server_edocr_v1.py api_server.py

# 3. Docker 이미지 빌드
docker build -f Dockerfile.v1 -t edocr-api:v1 .

# 4. Docker Compose 업데이트
# docker-compose.yml에서 image: edocr-api:v1 로 변경

# 5. 재시작
docker-compose down
docker-compose up -d

# 6. 로그 확인
docker-compose logs -f edocr2

# 예상 로그:
# "Loading eDOCr v1 models..."
# "Downloading recognizer_infoblock.h5..."
# "Downloading recognizer_dimensions.h5..."
# "Downloading recognizer_gdts.h5..."
# "✅ eDOCr v1 models loaded successfully!"

# 7. Health check
curl http://localhost:5001/api/v1/health

# 8. OCR 테스트
curl -X POST "http://localhost:5001/api/v1/ocr" \
  -F "file=@/home/uproot/ax/poc/opensource/01-immediate/eDOCr/tests/test_samples/Candle_holder.jpg" \
  -F "extract_dimensions=true" \
  -F "extract_gdt=true" \
  -F "extract_text=true" \
  -F "visualize=true"

# 9. 결과 확인
# Mock 데이터가 아닌 실제 OCR 결과가 나와야 함!
```

---

### 옵션 B: edocr2 v2 완전 설정 (시간 더 필요) ⏱️ 1-2일

edocr2가 더 많은 기능을 제공하지만 설정이 복잡합니다.

#### Step 1: 모델 다운로드

```bash
cd /home/uproot/ax/dev/edocr2

# GitHub Releases에서 모델 다운로드
# https://github.com/javvi51/edocr2/releases

# 모델 파일 위치 확인 (Release 페이지 확인 필요)
# - recognizer_gdts.keras
# - recognizer_dimensions_2.keras
# - (선택) detector_*.keras

# models/ 디렉토리에 저장
```

#### Step 2: 환경 설정

```bash
# Conda 환경
conda create -n edocr2 python=3.11 -y
conda activate edocr2

# TensorFlow + CUDA
pip install tensorflow[and-cuda]

# eDOCr2 requirements
cd /home/uproot/ax/dev/edocr2
pip install -r requirements.txt

# Tesseract OCR
sudo apt-get install libleptonica-dev tesseract-ocr libtesseract-dev \
  python3-pil tesseract-ocr-eng tesseract-ocr-script-latn
pip install tesseract pytesseract
```

#### Step 3: 테스트

```bash
# 테스트 실행
python test_drawing.py

# 예상 출력:
# "Loading session took X seconds..."
# "Processing..."
# "✅ Complete!"
```

#### Step 4: API 통합 (옵션 A와 유사하게 진행)

---

## 권장 사항

### 즉시 조치 (오늘)
1. ✅ **eDOCr v1 통합** (옵션 A)
   - 가장 빠르고 안정적
   - 2-3시간 내 완료 가능
   - 실제 OCR 작동 확인

### 중기 계획 (1-2주)
2. ⚠️ **edocr2 v2 환경 완전 설정** (옵션 B)
   - 추가 기능 활용 (테이블, LLM)
   - v1 백업으로 유지하면서 진행

### 장기 계획 (1개월)
3. 🔬 **v1 vs v2 성능 비교**
   - 실제 도면으로 벤치마크
   - 최적 버전 선택
   - 프로덕션 배포

---

## 예상 결과

### 현재 (Mock 데이터)
```json
{
  "dimensions": [],
  "gdt": [],
  "text": {
    "drawing_number": "MOCK-001",
    "title": "Test Drawing"
  }
}
```

### eDOCr v1 적용 후 (실제 OCR)
```json
{
  "dimensions": [
    {
      "value": "50.5",
      "tolerance": "+0.1/-0.05",
      "location": [245, 180]
    },
    {
      "value": "Ø12",
      "tolerance": "±0.05",
      "location": [320, 250]
    }
  ],
  "gdt": [
    {
      "symbol": "⏤",
      "value": "0.02",
      "location": [150, 300]
    }
  ],
  "text": {
    "drawing_number": "DRW-2024-001",
    "title": "Candle Holder Base",
    "material": "Aluminum 6061"
  }
}
```

---

## 문서 참조

- 전체 분석: `/home/uproot/ax/poc/opensource/README.md`
- 비교 보고서: `/home/uproot/ax/poc/opensource/COMPARISON_REPORT.md`
- 본 해결 가이드: `/home/uproot/ax/poc/opensource/SOLUTION.md`

---

**다음 단계**: eDOCr v1 통합 시작 (Step 1부터)
