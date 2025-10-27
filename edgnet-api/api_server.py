"""
EDGNet API Server
그래프 신경망 기반 도면 세그멘테이션 마이크로서비스

포트: 5002
기능: 도면을 Contour/Text/Dimension 컴포넌트로 분류
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
import numpy as np

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add edgnet to path
EDGNET_PATH = Path(__file__).parent.parent.parent / "dev" / "edgnet"
sys.path.insert(0, str(EDGNET_PATH))

# Initialize FastAPI
app = FastAPI(
    title="EDGNet API",
    description="Engineering Drawing Graph Neural Network Segmentation Service",
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
UPLOAD_DIR = Path("/tmp/edgnet/uploads")
RESULTS_DIR = Path("/tmp/edgnet/results")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'tiff', 'bmp'}


# =====================
# Pydantic Models
# =====================

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str


class SegmentRequest(BaseModel):
    visualize: bool = Field(True, description="시각화 이미지 생성 여부")
    num_classes: int = Field(3, description="분류 클래스 수 (2 or 3)")
    save_graph: bool = Field(False, description="그래프 데이터 저장 여부")


class ClassificationStats(BaseModel):
    contour: int = Field(0, description="윤곽선 컴포넌트 수")
    text: int = Field(0, description="텍스트 컴포넌트 수")
    dimension: int = Field(0, description="치수 컴포넌트 수")


class GraphStats(BaseModel):
    nodes: int
    edges: int
    avg_degree: float


class SegmentResponse(BaseModel):
    status: str
    data: Dict[str, Any]
    processing_time: float
    file_id: str


class VectorizeRequest(BaseModel):
    save_bezier: bool = Field(True, description="Bezier 곡선 저장 여부")


class VectorizeResponse(BaseModel):
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


def process_segmentation(
    file_path: Path,
    visualize: bool = True,
    num_classes: int = 3,
    save_graph: bool = False
) -> Dict[str, Any]:
    """
    도면 세그멘테이션 처리

    TODO: 실제 EDGNet 파이프라인 연동
    현재는 Mock 데이터 반환
    """
    try:
        # Import EDGNet components
        # from edgnet.pipeline import EDGNetPipeline
        # pipeline = EDGNetPipeline(model_path='/models/graphsage.pth')
        # result = pipeline.process(file_path, visualize=visualize)

        logger.info(f"Processing file: {file_path}")
        logger.info(f"Options: visualize={visualize}, num_classes={num_classes}")

        # Simulate processing time
        time.sleep(3)

        # Mock result
        result = {
            "num_components": 150,
            "classifications": {
                "contour": 80,
                "text": 30,
                "dimension": 40
            },
            "graph": {
                "nodes": 150,
                "edges": 280,
                "avg_degree": 3.73
            },
            "vectorization": {
                "num_bezier_curves": 150,
                "total_length": 12450.5
            }
        }

        if visualize:
            result["visualization_url"] = f"/api/v1/result/{file_path.stem}_segment.png"

        if save_graph:
            result["graph_url"] = f"/api/v1/result/{file_path.stem}_graph.json"

        return result

    except Exception as e:
        logger.error(f"Segmentation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Segmentation failed: {str(e)}")


def process_vectorization(
    file_path: Path,
    save_bezier: bool = True
) -> Dict[str, Any]:
    """
    도면 벡터화 처리

    TODO: 실제 벡터화 파이프라인 연동
    """
    try:
        logger.info(f"Vectorizing file: {file_path}")

        # Simulate processing
        time.sleep(2)

        result = {
            "num_curves": 150,
            "curve_types": {
                "line": 85,
                "arc": 45,
                "bezier": 20
            },
            "total_length": 12450.5,
            "processing_steps": {
                "skeletonization": "completed",
                "tracing": "completed",
                "bezier_fitting": "completed"
            }
        }

        if save_bezier:
            result["bezier_file"] = f"/api/v1/result/{file_path.stem}_curves.json"

        return result

    except Exception as e:
        logger.error(f"Vectorization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Vectorization failed: {str(e)}")


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
        "service": "EDGNet API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """헬스체크"""
    return {
        "status": "healthy",
        "service": "EDGNet API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v1/segment", response_model=SegmentResponse)
async def segment_drawing(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="도면 이미지 (PNG, JPG)"),
    visualize: bool = Form(True, description="시각화 생성"),
    num_classes: int = Form(3, description="분류 클래스 수 (2 or 3)"),
    save_graph: bool = Form(False, description="그래프 저장")
):
    """
    도면 세그멘테이션 - 컴포넌트 분류

    - **file**: 도면 이미지 (PNG, JPG, TIFF)
    - **visualize**: 분류 결과 시각화 이미지 생성 여부
    - **num_classes**: 2 (Text/Non-text) 또는 3 (Contour/Text/Dimension)
    - **save_graph**: 그래프 구조 JSON 저장 여부
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

        # 세그멘테이션 처리
        segment_result = process_segmentation(
            file_path,
            visualize=visualize,
            num_classes=num_classes,
            save_graph=save_graph
        )

        processing_time = time.time() - start_time

        # 백그라운드 작업: 오래된 파일 삭제
        background_tasks.add_task(cleanup_old_files, UPLOAD_DIR)

        return {
            "status": "success",
            "data": segment_result,
            "processing_time": round(processing_time, 2),
            "file_id": file_id
        }

    except Exception as e:
        logger.error(f"Error processing file: {e}")
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/vectorize", response_model=VectorizeResponse)
async def vectorize_drawing(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="도면 이미지"),
    save_bezier: bool = Form(True, description="Bezier 곡선 저장")
):
    """
    도면 벡터화

    - **file**: 도면 이미지 (PNG, JPG)
    - **save_bezier**: Bezier 곡선 데이터 JSON 저장 여부
    """
    start_time = time.time()

    # 파일 검증
    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # 파일 저장
    file_id = f"{int(time.time())}_{file.filename}"
    file_path = UPLOAD_DIR / file_id

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"File uploaded for vectorization: {file_id}")

        # 벡터화 처리
        vectorize_result = process_vectorization(
            file_path,
            save_bezier=save_bezier
        )

        processing_time = time.time() - start_time

        # 백그라운드 작업
        background_tasks.add_task(cleanup_old_files, UPLOAD_DIR)

        return {
            "status": "success",
            "data": vectorize_result,
            "processing_time": round(processing_time, 2),
            "file_id": file_id
        }

    except Exception as e:
        logger.error(f"Error vectorizing file: {e}")
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/result/{filename}")
async def get_result_file(filename: str):
    """결과 파일 다운로드"""
    file_path = RESULTS_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        media_type='application/octet-stream',
        filename=filename
    )


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
    port = int(os.getenv("EDGNET_PORT", 5002))
    workers = int(os.getenv("EDGNET_WORKERS", 2))

    logger.info(f"Starting EDGNet API on port {port} with {workers} workers")

    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=port,
        workers=workers,
        log_level="info",
        reload=False
    )
