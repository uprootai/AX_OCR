"""
EDGNet API Server
그래프 신경망 기반 도면 세그멘테이션 마이크로서비스

포트: 5002
기능: 도면을 Contour/Text/Dimension 컴포넌트로 분류
"""

import os
import time
import shutil
import logging
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import torch

# Import from modules
from trained_models.schemas import (
    HealthResponse,
    SegmentRequest,
    SegmentResponse,
    VectorizeRequest,
    VectorizeResponse
)
from models.schemas import (
    UNetSegmentRequest,
    UNetSegmentResponse,
    APIInfoResponse,
    ParameterSchema,
    IOSchema,
    BlueprintFlowMetadata
)
from services.inference import (
    EDGNetInferenceService,
    check_edgnet_availability,
    check_model_exists
)
from services.unet_inference import (
    UNetInferenceService,
    check_unet_model_exists
)
from utils.helpers import allowed_file, cleanup_old_files

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =====================
# Configuration
# =====================

UPLOAD_DIR = Path("/tmp/edgnet/uploads")
RESULTS_DIR = Path("/tmp/edgnet/results")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'tiff', 'bmp'}

# Model paths
GRAPHSAGE_MODEL_PATH = Path("/trained_models/graphsage_dimension_classifier.pth")
UNET_MODEL_PATH = Path("/app/models/edgnet_large.pth")

# =====================
# FastAPI App
# =====================

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

# Global inference services
edgnet_service: EDGNetInferenceService = None
unet_service: UNetInferenceService = None


# =====================
# Startup Event
# =====================

@app.on_event("startup")
async def startup_event():
    """Validate EDGNet pipeline and UNet model on startup"""
    global edgnet_service, unet_service

    logger.info("Starting EDGNet API...")

    # Auto-detect GPU availability
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    logger.info(f"Using device: {device}")
    if device == 'cuda':
        logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
        logger.info(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

    # ====== EDGNet (GraphSAGE) Initialization ======
    logger.info("Validating EDGNet pipeline...")
    edgnet_available = check_edgnet_availability()
    graphsage_exists = check_model_exists(str(GRAPHSAGE_MODEL_PATH))

    if not edgnet_available:
        logger.error("EDGNet pipeline NOT available")
        logger.error("   Install EDGNet from: https://github.com/[repository_url]")
        logger.error("   EDGNet API will return 503 errors until pipeline is installed")
    else:
        logger.info("EDGNet pipeline available")

        if not graphsage_exists:
            logger.error(f"GraphSAGE model NOT found: {GRAPHSAGE_MODEL_PATH}")
            logger.error("   Download model from: [model_url]")
            logger.error("   /api/v1/segment endpoint will return 503 errors")
        else:
            logger.info(f"GraphSAGE model found: {GRAPHSAGE_MODEL_PATH}")

            # Initialize EDGNet service
            edgnet_service = EDGNetInferenceService(
                model_path=str(GRAPHSAGE_MODEL_PATH),
                device=device
            )

            # Load the model
            try:
                edgnet_service.load_model()
                logger.info("✅ EDGNet GraphSAGE model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load EDGNet model: {e}")
                edgnet_service = None

    # ====== UNet Initialization ======
    logger.info("Validating UNet model...")
    unet_exists = check_unet_model_exists(str(UNET_MODEL_PATH))

    if not unet_exists:
        logger.warning(f"UNet model NOT found: {UNET_MODEL_PATH}")
        logger.warning("   /api/v1/segment_unet endpoint will return 503 errors")
    else:
        logger.info(f"UNet model found: {UNET_MODEL_PATH}")

        # Initialize UNet service
        unet_service = UNetInferenceService(
            model_path=str(UNET_MODEL_PATH),
            device=device,
            image_size=512
        )

        # Load the model
        try:
            unet_service.load_model()
            logger.info("✅ UNet model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load UNet model: {e}")
            unet_service = None

    logger.info("EDGNet API startup complete")


# =====================
# API Endpoints
# =====================

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint"""
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
    Health check endpoint

    Returns the current health status of the EDGNet API service.
    Checks both GraphSAGE and UNet models availability.
    """
    graphsage_ready = check_edgnet_availability() and check_model_exists(str(GRAPHSAGE_MODEL_PATH))
    unet_ready = check_unet_model_exists(str(UNET_MODEL_PATH))

    # Service is healthy if at least one model is available
    is_ready = graphsage_ready or unet_ready
    status = "healthy" if is_ready else "degraded"

    return {
        "status": status,
        "service": "EDGNet API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/v1/info", response_model=APIInfoResponse)
async def get_api_info():
    """
    API 메타데이터 엔드포인트

    BlueprintFlow 및 Dashboard에서 API를 자동으로 등록하기 위한 메타데이터를 제공합니다.
    """
    port = int(os.getenv("EDGNET_PORT", 5012))
    return APIInfoResponse(
        id="edgnet",
        name="EDGNet API",
        display_name="EDGNet 세그멘테이션",
        version="1.0.0",
        description="Engineering Drawing Graph Neural Network - 도면 컴포넌트 세그멘테이션 API",
        openapi_url="/openapi.json",
        base_url=f"http://localhost:{port}",
        endpoint="/api/v1/segment",
        method="POST",
        requires_image=True,
        inputs=[
            IOSchema(
                name="file",
                type="file",
                description="분석할 도면 이미지 파일 (PNG, JPG, TIFF, BMP)",
                required=True
            )
        ],
        outputs=[
            IOSchema(
                name="segments",
                type="array",
                description="세그멘테이션된 컴포넌트 목록 (Contour/Text/Dimension 분류)"
            ),
            IOSchema(
                name="classification_stats",
                type="object",
                description="클래스별 컴포넌트 개수 통계"
            ),
            IOSchema(
                name="visualized_image",
                type="string",
                description="세그멘테이션 결과 시각화 이미지 (base64)"
            ),
            IOSchema(
                name="processing_time",
                type="float",
                description="처리 시간 (초)"
            )
        ],
        parameters=[
            ParameterSchema(
                name="model",
                type="select",
                default="graphsage",
                description="세그멘테이션 모델 선택",
                required=False,
                options=["graphsage", "unet"]
            ),
            ParameterSchema(
                name="visualize",
                type="boolean",
                default=True,
                description="세그멘테이션 결과 시각화 생성",
                required=False
            ),
            ParameterSchema(
                name="num_classes",
                type="select",
                default="3",
                description="분류 클래스 수 (2: Text/Non-text, 3: Contour/Text/Dimension)",
                required=False,
                options=["2", "3"]
            ),
            ParameterSchema(
                name="save_graph",
                type="boolean",
                default=False,
                description="그래프 구조 JSON 저장 (GraphSAGE만)",
                required=False
            ),
            ParameterSchema(
                name="vectorize",
                type="boolean",
                default=False,
                description="도면 벡터화 (Bezier 곡선, DXF 출력용)",
                required=False
            )
        ],
        blueprintflow=BlueprintFlowMetadata(
            icon="🎨",
            color="#f59e0b",
            category="segmentation"
        ),
        output_mappings={
            "segments": "data.segments",
            "classification_stats": "data.classification_stats",
            "visualized_image": "data.visualized_image",
            "processing_time": "processing_time"
        }
    )


@app.post("/api/v1/segment", response_model=SegmentResponse)
async def segment_drawing(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="도면 이미지 (PNG, JPG)"),
    model: str = Form("graphsage", description="모델 선택 (graphsage: 빠름, unet: 정확)"),
    visualize: bool = Form(True, description="시각화 생성"),
    num_classes: int = Form(3, description="분류 클래스 수 (2 or 3)"),
    save_graph: bool = Form(False, description="그래프 저장"),
    vectorize: bool = Form(False, description="도면 벡터화 (DXF 출력용)")
):
    """
    도면 세그멘테이션 - 컴포넌트 분류

    - **file**: 도면 이미지 (PNG, JPG, TIFF)
    - **model**: 모델 선택 (graphsage or unet)
    - **visualize**: 분류 결과 시각화 이미지 생성 여부
    - **num_classes**: 2 (Text/Non-text) 또는 3 (Contour/Text/Dimension)
    - **save_graph**: 그래프 구조 JSON 저장 여부
    - **vectorize**: 도면 벡터화 (Bezier 곡선, DXF 출력용)
    """
    start_time = time.time()

    # Validate file
    if not allowed_file(file.filename, ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Check file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )

    # Save file
    file_id = f"{int(time.time())}_{file.filename}"
    file_path = UPLOAD_DIR / file_id

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"File uploaded: {file_id} ({file_size / 1024:.2f} KB)")

        # Select model based on parameter
        if model.lower() == "unet":
            # Use UNet model
            if unet_service is None:
                raise HTTPException(
                    status_code=503,
                    detail="UNet inference service not initialized"
                )
            segment_result = unet_service.process_segmentation(
                file_path,
                visualize=visualize
                # Note: UNet doesn't support results_dir or vectorize parameters
            )
        elif model.lower() == "graphsage":
            # Use GraphSAGE model (default)
            if edgnet_service is None:
                raise HTTPException(
                    status_code=503,
                    detail="EDGNet GraphSAGE service not initialized"
                )
            segment_result = edgnet_service.process_segmentation(
                file_path,
                visualize=visualize,
                num_classes=num_classes,
                save_graph=save_graph,
                results_dir=RESULTS_DIR
                # Note: GraphSAGE doesn't support vectorize yet
            )
            if vectorize:
                logger.warning("Vectorize not yet supported for GraphSAGE model")
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid model: {model}. Choose 'graphsage' or 'unet'"
            )

        processing_time = time.time() - start_time

        # Background task: cleanup old files
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

    # Validate file
    if not allowed_file(file.filename, ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Save file
    file_id = f"{int(time.time())}_{file.filename}"
    file_path = UPLOAD_DIR / file_id

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"File uploaded for vectorization: {file_id}")

        # Process vectorization
        if edgnet_service is None:
            raise HTTPException(
                status_code=503,
                detail="EDGNet inference service not initialized"
            )

        vectorize_result = edgnet_service.process_vectorization(
            file_path,
            save_bezier=save_bezier
        )

        processing_time = time.time() - start_time

        # Background task
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
    """Download result file"""
    file_path = RESULTS_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        media_type='application/octet-stream',
        filename=filename
    )


@app.post("/api/v1/segment_unet", response_model=UNetSegmentResponse)
async def segment_unet(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="도면 이미지 (PNG, JPG, JPEG, TIFF, BMP)"),
    threshold: float = Form(0.5, description="세그멘테이션 임계값 (0.0~1.0)", ge=0.0, le=1.0),
    visualize: bool = Form(True, description="시각화 이미지 생성 여부"),
    return_mask: bool = Form(False, description="세그멘테이션 마스크 반환 여부 (base64)")
):
    """
    UNet 기반 도면 엣지 세그멘테이션

    **UNet (U-Shaped Network)**:
    - Encoder-Decoder 구조의 픽셀 단위 세그멘테이션 모델
    - 도면에서 선/윤곽선/엣지를 감지하여 마스크 생성
    - GraphSAGE 기반 segment 엔드포인트와 달리 픽셀 레벨로 동작

    **사용 사례**:
    - 도면의 선/경계 추출
    - 전처리 단계로 사용 (노이즈 제거, 엣지 강조)
    - 스캔 품질이 낮은 도면의 개선
    - 도면 벡터화 전처리

    **Parameters**:
    - **file**: 도면 이미지 파일
    - **threshold**: 세그멘테이션 임계값 (0.0~1.0, 기본값: 0.5)
      - 높을수록 엣지 감지 엄격 (false positive 감소)
      - 낮을수록 엣지 감지 관대 (recall 증가)
    - **visualize**: 시각화 이미지 생성 여부 (기본값: True)
      - True: 원본 이미지에 감지된 엣지를 오버레이한 시각화 반환
      - False: 통계 정보만 반환
    - **return_mask**: 세그멘테이션 마스크 반환 여부 (기본값: False)
      - True: PNG로 인코딩된 base64 마스크 반환 (추가 처리용)
      - False: 마스크 미반환 (응답 크기 감소)

    **Returns**:
    ```json
    {
      "status": "success",
      "data": {
        "mask_shape": [height, width],
        "edge_pixel_count": 123456,
        "edge_percentage": 12.34,
        "threshold_used": 0.5,
        "model_info": {
          "architecture": "UNet",
          "input_size": 512,
          "parameters": 31042369,
          "device": "cuda"
        },
        "visualized_image": "base64_encoded_jpg...",
        "segmentation_mask": "base64_encoded_png..." // return_mask=True인 경우에만
      },
      "processing_time": 0.87,
      "file_id": "1234567890_drawing.png"
    }
    ```

    **모델 정보**:
    - 아키텍처: UNet (Encoder-Decoder with Skip Connections)
    - 파라미터 수: 31,042,369
    - 입력 크기: 512x512 (자동 리사이즈)
    - 학습 데이터: 20장 (증강 포함)
    - 성능: IoU 85.8% (Validation)

    **GraphSAGE /api/v1/segment와의 차이**:
    | 특징 | UNet (/segment_unet) | GraphSAGE (/segment) |
    |------|---------------------|---------------------|
    | 출력 | 픽셀 마스크 | 컴포넌트 분류 |
    | 레벨 | Low-level (엣지) | High-level (의미) |
    | 용도 | 전처리, 엣지 추출 | 컴포넌트 구분 |
    | 속도 | 빠름 (~1초) | 느림 (~5초) |
    """
    start_time = time.time()

    # Validate file
    if not allowed_file(file.filename, ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Check file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )

    # Save file
    file_id = f"{int(time.time())}_{file.filename}"
    file_path = UPLOAD_DIR / file_id

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"File uploaded for UNet segmentation: {file_id} ({file_size / 1024:.2f} KB)")

        # Process UNet segmentation
        if unet_service is None:
            raise HTTPException(
                status_code=503,
                detail="UNet inference service not initialized. Model may not be loaded."
            )

        segment_result = unet_service.process_segmentation(
            file_path,
            threshold=threshold,
            visualize=visualize,
            return_mask=return_mask
        )

        processing_time = time.time() - start_time

        # Background task: cleanup old files
        background_tasks.add_task(cleanup_old_files, UPLOAD_DIR)

        return {
            "status": "success",
            "data": segment_result,
            "processing_time": round(processing_time, 2),
            "file_id": file_id
        }

    except Exception as e:
        logger.error(f"Error processing UNet segmentation: {e}")
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/cleanup")
async def cleanup_files(max_age_hours: int = 24):
    """Manual file cleanup"""
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

    logger.info(f"Starting EDGNet API on port {port}")

    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=False
    )
