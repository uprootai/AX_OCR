"""
eDOCr2 API Server
공학 도면 OCR 처리 마이크로서비스

포트: 5001
기능: 도면에서 치수, GD&T, 텍스트 정보 추출
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

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add edocr2 to path
EDOCR2_PATH = Path(__file__).parent.parent.parent / "dev" / "edocr2"
sys.path.insert(0, str(EDOCR2_PATH))

# Initialize FastAPI
app = FastAPI(
    title="eDOCr2 API",
    description="Engineering Drawing OCR Service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
UPLOAD_DIR = Path("/tmp/edocr2/uploads")
RESULTS_DIR = Path("/tmp/edocr2/results")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'tiff'}


# =====================
# Pydantic Models
# =====================

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str


class OCRRequest(BaseModel):
    extract_dimensions: bool = Field(True, description="치수 정보 추출 여부")
    extract_gdt: bool = Field(True, description="GD&T 정보 추출 여부")
    extract_text: bool = Field(True, description="텍스트 정보 추출 여부")
    use_vl_model: bool = Field(False, description="Vision Language 모델 사용 여부 (GPT-4o/Qwen2-VL)")
    visualize: bool = Field(False, description="시각화 이미지 생성 여부")


class DimensionData(BaseModel):
    value: float
    unit: str
    type: str
    tolerance: Optional[str] = None
    location: Optional[Dict[str, float]] = None


class GDTData(BaseModel):
    type: str
    value: float
    datum: Optional[str] = None
    location: Optional[Dict[str, float]] = None


class TextData(BaseModel):
    drawing_number: Optional[str] = None
    revision: Optional[str] = None
    title: Optional[str] = None
    material: Optional[str] = None
    notes: Optional[List[str]] = None


class OCRResponse(BaseModel):
    status: str
    data: Dict[str, Any]
    processing_time: float
    file_id: str


# =====================
# Helper Functions
# =====================

def allowed_file(filename: str) -> bool:
    """파일 확장자 검증"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
        # from edocr2.keras_ocr import pipeline
        # from edocr2.tools import ocr_pipelines

        logger.info(f"Processing file: {file_path}")
        logger.info(f"Options: dims={extract_dimensions}, gdt={extract_gdt}, text={extract_text}, vl={use_vl_model}")

        # Simulate processing time
        time.sleep(2)

        # Mock result (실제 구현 시 eDOCr2 파이프라인으로 대체)
        result = {
            "dimensions": [],
            "gdt": [],
            "text": {}
        }

        if extract_dimensions:
            result["dimensions"] = [
                {
                    "value": 392.0,
                    "unit": "mm",
                    "type": "diameter",
                    "tolerance": "±0.1",
                    "location": {"x": 450, "y": 320}
                },
                {
                    "value": 320.0,
                    "unit": "mm",
                    "type": "diameter",
                    "tolerance": None,
                    "location": {"x": 480, "y": 350}
                }
            ]

        if extract_gdt:
            result["gdt"] = [
                {
                    "type": "flatness",
                    "value": 0.05,
                    "datum": "A",
                    "location": {"x": 200, "y": 150}
                },
                {
                    "type": "cylindricity",
                    "value": 0.1,
                    "datum": None,
                    "location": {"x": 250, "y": 180}
                }
            ]

        if extract_text:
            result["text"] = {
                "drawing_number": "A12-311197-9",
                "revision": "Rev.2",
                "title": "Intermediate Shaft",
                "material": "Steel",
                "notes": ["M20 (4 places)", "Top & ø17.5 Drill, thru."]
            }

        # Add visualization URL if requested
        if visualize:
            # TODO: Generate actual visualization image
            # For now, return a placeholder URL
            result["visualization_url"] = f"/api/v1/visualization/{file_path.name}"

        return result

    except Exception as e:
        logger.error(f"OCR processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")


def cleanup_old_files(directory: Path, max_age_hours: int = 24):
    """오래된 파일 삭제"""
    try:
        current_time = time.time()
        for file_path in directory.glob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_hours * 3600:
                    file_path.unlink()
                    logger.info(f"Deleted old file: {file_path}")
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")


# =====================
# API Endpoints
# =====================

@app.get("/", response_model=HealthResponse)
async def root():
    """루트 엔드포인트"""
    return {
        "status": "online",
        "service": "eDOCr2 API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """헬스체크"""
    return {
        "status": "healthy",
        "service": "eDOCr2 API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v1/ocr", response_model=OCRResponse)
async def process_drawing(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="도면 파일 (PDF, PNG, JPG)"),
    extract_dimensions: bool = Form(True, description="치수 정보 추출"),
    extract_gdt: bool = Form(True, description="GD&T 정보 추출"),
    extract_text: bool = Form(True, description="텍스트 정보 추출"),
    use_vl_model: bool = Form(False, description="Vision Language 모델 사용"),
    visualize: bool = Form(False, description="시각화 이미지 생성")
):
    """
    도면 OCR 처리

    - **file**: 도면 파일 (PDF, PNG, JPG, JPEG, TIFF)
    - **extract_dimensions**: 치수 정보 추출 여부
    - **extract_gdt**: GD&T 정보 추출 여부
    - **extract_text**: 텍스트 정보 추출 여부
    - **use_vl_model**: Vision Language 모델 사용 여부 (느리지만 정확)
    - **visualize**: 시각화 이미지 생성 여부
    """
    start_time = time.time()

    # 파일 검증
    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # 파일 크기 체크
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )

    # 파일 저장
    file_id = f"{int(time.time())}_{file.filename}"
    file_path = UPLOAD_DIR / file_id

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"File uploaded: {file_id} ({file_size / 1024:.2f} KB)")

        # OCR 처리
        ocr_result = process_ocr(
            file_path,
            extract_dimensions=extract_dimensions,
            extract_gdt=extract_gdt,
            extract_text=extract_text,
            use_vl_model=use_vl_model,
            visualize=visualize
        )

        processing_time = time.time() - start_time

        # 백그라운드 작업: 오래된 파일 삭제
        background_tasks.add_task(cleanup_old_files, UPLOAD_DIR)

        return {
            "status": "success",
            "data": ocr_result,
            "processing_time": round(processing_time, 2),
            "file_id": file_id
        }

    except Exception as e:
        logger.error(f"Error processing file: {e}")
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/result/{file_id}")
async def get_result(file_id: str):
    """처리 결과 조회 (향후 비동기 처리용)"""
    result_path = RESULTS_DIR / f"{file_id}.json"

    if not result_path.exists():
        raise HTTPException(status_code=404, detail="Result not found")

    with open(result_path, 'r') as f:
        result = json.load(f)

    return JSONResponse(content=result)


@app.delete("/api/v1/cleanup")
async def cleanup_files(max_age_hours: int = 24):
    """수동 파일 정리"""
    try:
        cleanup_old_files(UPLOAD_DIR, max_age_hours)
        cleanup_old_files(RESULTS_DIR, max_age_hours)
        return {"status": "success", "message": f"Cleaned up files older than {max_age_hours} hours"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================
# Main
# =====================

if __name__ == "__main__":
    port = int(os.getenv("EDOCR2_PORT", 5001))
    workers = int(os.getenv("EDOCR2_WORKERS", 4))

    logger.info(f"Starting eDOCr2 API on port {port} with {workers} workers")

    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=port,
        workers=workers,
        log_level="info",
        reload=False
    )
