"""
Segment Router - EDGNet Segmentation Endpoints
"""
import os
import time
import shutil
import logging
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from models.schemas import SegmentResponse, VectorizeResponse
from models.schemas import (
    UNetSegmentResponse,
    APIInfoResponse,
    ParameterSchema,
    IOSchema,
    BlueprintFlowMetadata
)
from services.state import get_edgnet_service, get_unet_service
from utils.helpers import allowed_file, cleanup_old_files

logger = logging.getLogger(__name__)

# Configuration
UPLOAD_DIR = Path("/tmp/edgnet/uploads")
RESULTS_DIR = Path("/tmp/edgnet/results")
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'tiff', 'bmp'}

router = APIRouter(prefix="/api/v1", tags=["segmentation"])


@router.get("/info", response_model=APIInfoResponse)
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


@router.post("/segment", response_model=SegmentResponse)
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
    edgnet_service = get_edgnet_service()
    unet_service = get_unet_service()

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


@router.post("/vectorize", response_model=VectorizeResponse)
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
    edgnet_service = get_edgnet_service()

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


@router.get("/result/{filename}")
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


@router.post("/segment_unet", response_model=UNetSegmentResponse)
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

    **Parameters**:
    - **file**: 도면 이미지 파일
    - **threshold**: 세그멘테이션 임계값 (0.0~1.0, 기본값: 0.5)
    - **visualize**: 시각화 이미지 생성 여부
    - **return_mask**: 세그멘테이션 마스크 반환 여부
    """
    start_time = time.time()
    unet_service = get_unet_service()

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


@router.delete("/cleanup")
async def cleanup_files(max_age_hours: int = 24):
    """Manual file cleanup"""
    try:
        cleanup_old_files(UPLOAD_DIR, max_age_hours)
        cleanup_old_files(RESULTS_DIR, max_age_hours)
        return {"status": "success", "message": f"Cleaned up files older than {max_age_hours} hours"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
