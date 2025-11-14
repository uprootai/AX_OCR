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
# In Docker container, EDGNet is mounted at /app/edgnet
EDGNET_PATH = Path("/app/edgnet")
if not EDGNET_PATH.exists():
    # Fallback to relative path for local development
    EDGNET_PATH = Path(__file__).parent.parent.parent / "dev" / "edgnet"
sys.path.insert(0, str(EDGNET_PATH))
logger.info(f"EDGNet path: {EDGNET_PATH}")

# Import EDGNet pipeline
try:
    from pipeline import EDGNetPipeline
    EDGNET_AVAILABLE = True
    logger.info("✅ EDGNet pipeline imported successfully")
except ImportError as e:
    EDGNET_AVAILABLE = False
    logger.warning(f"⚠️ EDGNet pipeline import failed: {e}")
    logger.warning("Will use mock data for segmentation")

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


def bezier_to_bbox(bezier_curve, n_samples=50):
    """
    Convert Bezier curve to bounding box

    Args:
        bezier_curve: Bezier curve object with evaluate() method
        n_samples: Number of points to sample for bbox calculation

    Returns:
        dict: {'x': int, 'y': int, 'width': int, 'height': int}
    """
    try:
        t_vals = np.linspace(0, 1, n_samples)
        points = bezier_curve.evaluate(t_vals)

        x_min = int(np.min(points[:, 0]))
        y_min = int(np.min(points[:, 1]))
        x_max = int(np.max(points[:, 0]))
        y_max = int(np.max(points[:, 1]))

        return {
            'x': x_min,
            'y': y_min,
            'width': x_max - x_min,
            'height': y_max - y_min
        }
    except Exception as e:
        logger.error(f"Failed to compute bbox: {e}")
        return {'x': 0, 'y': 0, 'width': 0, 'height': 0}


def process_segmentation(
    file_path: Path,
    visualize: bool = True,
    num_classes: int = 3,
    save_graph: bool = False
) -> Dict[str, Any]:
    """
    도면 세그멘테이션 처리 (실제 EDGNet 파이프라인 사용)
    """
    try:
        logger.info(f"Processing file: {file_path}")
        logger.info(f"Options: visualize={visualize}, num_classes={num_classes}")

        if not EDGNET_AVAILABLE:
            # EDGNet 파이프라인이 없으면 명시적 에러 반환
            logger.error("❌ EDGNet pipeline not available")
            raise HTTPException(
                status_code=503,
                detail="EDGNet pipeline not available. Please install EDGNet dependencies."
            )

        # Initialize EDGNet pipeline with model
        # Model is mounted at /models/ inside the container
        model_path = Path("/models/graphsage_dimension_classifier.pth")

        if not model_path.exists():
            # 모델 파일이 없으면 명시적 에러 반환
            logger.error(f"❌ Model not found: {model_path}")
            raise HTTPException(
                status_code=503,
                detail=f"EDGNet model not found at {model_path}. Please download the model file."
            )

        logger.info(f"Loading model from: {model_path}")

        # Auto-detect GPU availability / GPU 자동 감지
        try:
            import torch
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            logger.info(f"Using device: {device}")
            if device == 'cuda':
                logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
                logger.info(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
        except ImportError:
            device = 'cpu'
            logger.warning("PyTorch not available, using CPU")

        pipeline = EDGNetPipeline(model_path=str(model_path), device=device)

        # Process drawing
        logger.info("Running EDGNet pipeline...")
        output_dir = RESULTS_DIR / file_path.stem if save_graph else None
        pipeline_result = pipeline.process_drawing(
            str(file_path),
            output_dir=output_dir,
            visualize=visualize
        )

        # Extract results
        bezier_curves = pipeline_result['bezier_curves']
        predictions = pipeline_result['predictions']
        G = pipeline_result['graph']

        logger.info(f"✅ Pipeline complete: {len(bezier_curves)} components")

        # Count classifications
        # Class mapping from training: 0=Dimension, 1=Text, 2=Contour, 3=Other
        class_counts = {"dimension": 0, "text": 0, "contour": 0, "other": 0}
        class_map = {0: "dimension", 1: "text", 2: "contour", 3: "other"}

        if predictions is not None:
            unique, counts = np.unique(predictions, return_counts=True)
            for cls, cnt in zip(unique, counts):
                class_name = class_map.get(int(cls), "unknown")
                if class_name in class_counts:
                    class_counts[class_name] = int(cnt)

        # Build components list with bboxes
        components = []
        if predictions is not None:
            for i, (bezier, pred) in enumerate(zip(bezier_curves, predictions)):
                bbox = bezier_to_bbox(bezier)
                classification = class_map.get(int(pred), "unknown")

                components.append({
                    "id": i,
                    "classification": classification,
                    "bbox": bbox,
                    "confidence": 0.9  # EDGNet doesn't provide confidence scores
                })

        # Calculate graph stats
        avg_degree = (2 * G.number_of_edges() / G.number_of_nodes()) if G.number_of_nodes() > 0 else 0

        result = {
            "num_components": len(bezier_curves),
            "classifications": class_counts,
            "graph": {
                "nodes": G.number_of_nodes(),
                "edges": G.number_of_edges(),
                "avg_degree": round(avg_degree, 2)
            },
            "vectorization": {
                "num_bezier_curves": len(bezier_curves),
                "total_length": 0  # Would need to calculate from bezier curves
            },
            "components": components  # NEW: Actual component data with bboxes
        }

        if visualize and output_dir:
            result["visualization_url"] = f"/api/v1/result/{file_path.stem}/predictions.png"

        if save_graph and output_dir:
            result["graph_url"] = f"/api/v1/result/{file_path.stem}/graph.pkl"

        logger.info(f"✅ Segmentation complete: {class_counts}")
        return result

    except Exception as e:
        logger.error(f"❌ Segmentation failed: {e}", exc_info=True)
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
# Startup Event
# =====================

@app.on_event("startup")
async def startup_event():
    """Validate EDGNet pipeline and model on startup"""
    logger.info("🚀 Starting EDGNet API...")
    logger.info("🔍 Validating EDGNet pipeline...")

    if not EDGNET_AVAILABLE:
        logger.error("❌ EDGNet pipeline NOT available")
        logger.error("   Install EDGNet from: https://github.com/[repository_url]")
        logger.error("   EDGNet API will return 503 errors until pipeline is installed")
    else:
        logger.info("✅ EDGNet pipeline available")

        # Check model file
        model_path = Path("/models/graphsage_dimension_classifier.pth")
        if not model_path.exists():
            logger.error(f"❌ Model file NOT found: {model_path}")
            logger.error("   Download model from: [model_url]")
            logger.error("   EDGNet API will return 503 errors until model is available")
        else:
            logger.info(f"✅ Model file found: {model_path}")
            logger.info("✅ EDGNet API ready for segmentation")

    logger.info("✅ EDGNet API startup complete")


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


@app.get("/health", response_model=HealthResponse)
@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint / 헬스체크

    Returns the current health status of the EDGNet API service.
    """
    # Check if pipeline and model are available
    model_path = Path("/models/graphsage_dimension_classifier.pth")
    is_ready = EDGNET_AVAILABLE and model_path.exists()

    status = "healthy" if is_ready else "degraded"

    return {
        "status": status,
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
