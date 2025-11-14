#!/usr/bin/env python3
"""
AX 시스템 통합 관리 대시보드

모든 API, 모델, 학습, 추론을 웹에서 관리
- API 상태 모니터링
- 모델 관리 (학습, 업로드, 다운로드)
- GPU 모니터링
- 추론 테스트
- 로그 확인
"""

import os
import json
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import psutil

# Training manager
from training_manager import (
    create_training_job,
    get_training_job,
    list_training_jobs,
    cancel_training_job
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="AX Admin Dashboard",
    description="AX 시스템 통합 관리 대시보드",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates
templates = Jinja2Templates(directory="templates")

# Configuration
API_URLS = {
    "edocr2": "http://localhost:5001",
    "edgnet": "http://localhost:5012",
    "skinmodel": "http://localhost:5003",
    "vl": "http://localhost:5004",
    "yolo": "http://localhost:5005",
    "paddleocr": "http://localhost:5006",
    "gateway": "http://localhost:8000"
}

MODELS_DIR = Path("/home/uproot/ax/poc")


# =====================
# Pydantic Models
# =====================

class APIStatus(BaseModel):
    name: str
    url: str
    status: str
    response_time: Optional[float] = None
    details: Optional[Dict] = None


class GPUStatus(BaseModel):
    available: bool
    device_name: Optional[str] = None
    total_memory: Optional[int] = None
    used_memory: Optional[int] = None
    free_memory: Optional[int] = None
    utilization: Optional[float] = None


class ModelInfo(BaseModel):
    name: str
    path: str
    size: int
    modified: str
    type: str


class TrainingJob(BaseModel):
    job_id: str
    model_type: str
    status: str
    started_at: str
    completed_at: Optional[str] = None
    metrics: Optional[Dict] = None


# =====================
# Helper Functions
# =====================

async def check_api_health(name: str, url: str) -> APIStatus:
    """API 헬스체크"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            start = datetime.now()
            response = await client.get(f"{url}/api/v1/health")
            elapsed = (datetime.now() - start).total_seconds()

            if response.status_code == 200:
                return APIStatus(
                    name=name,
                    url=url,
                    status="healthy",
                    response_time=elapsed,
                    details=response.json()
                )
            else:
                return APIStatus(
                    name=name,
                    url=url,
                    status="unhealthy",
                    response_time=elapsed,
                    details={"error": f"Status code: {response.status_code}"}
                )
    except Exception as e:
        return APIStatus(
            name=name,
            url=url,
            status="error",
            details={"error": str(e)}
        )


def get_gpu_status() -> GPUStatus:
    """GPU 상태 확인"""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            parts = result.stdout.strip().split(", ")
            return GPUStatus(
                available=True,
                device_name=parts[0],
                total_memory=int(parts[1]),
                used_memory=int(parts[2]),
                free_memory=int(parts[3]),
                utilization=float(parts[4])
            )
    except Exception as e:
        logger.warning(f"GPU status check failed: {e}")

    return GPUStatus(available=False)


def get_system_stats() -> Dict:
    """시스템 통계"""
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent
    }


def list_models(model_type: str) -> List[ModelInfo]:
    """모델 목록 조회"""
    models = []

    if model_type == "skinmodel":
        models_path = MODELS_DIR / "skinmodel-api" / "models"
    elif model_type == "edgnet":
        models_path = MODELS_DIR / "edgnet-api" / "models"
    elif model_type == "yolo":
        models_path = MODELS_DIR / "yolo-api" / "models"
    else:
        return models

    if models_path.exists():
        for file in models_path.glob("*.pkl"):
            stat = file.stat()
            models.append(ModelInfo(
                name=file.name,
                path=str(file),
                size=stat.st_size,
                modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                type=model_type
            ))

        for file in models_path.glob("*.pth"):
            stat = file.stat()
            models.append(ModelInfo(
                name=file.name,
                path=str(file),
                size=stat.st_size,
                modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                type=model_type
            ))

    return models


def get_docker_logs(service_name: str, lines: int = 100) -> str:
    """Docker 로그 조회"""
    try:
        result = subprocess.run(
            ["docker-compose", "logs", "--tail", str(lines), service_name],
            capture_output=True,
            text=True,
            cwd=MODELS_DIR
        )
        return result.stdout
    except Exception as e:
        return f"Error: {e}"


# =====================
# API Endpoints
# =====================

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """메인 대시보드"""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/api/status")
async def get_status():
    """전체 시스템 상태"""
    # API 상태 확인
    api_statuses = []
    for name, url in API_URLS.items():
        status = await check_api_health(name, url)
        api_statuses.append(status.dict())

    # GPU 상태
    gpu_status = get_gpu_status()

    # 시스템 통계
    system_stats = get_system_stats()

    return {
        "apis": api_statuses,
        "gpu": gpu_status.dict(),
        "system": system_stats,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/models/{model_type}")
async def get_models(model_type: str):
    """모델 목록"""
    models = list_models(model_type)
    return {"models": [m.dict() for m in models]}


@app.get("/api/logs/{service}")
async def get_logs(service: str, lines: int = 100):
    """서비스 로그"""
    logs = get_docker_logs(service, lines)
    return {"service": service, "logs": logs}


@app.post("/api/train/{model_type}")
async def trigger_training(model_type: str):
    """모델 학습 트리거"""
    try:
        if model_type == "skinmodel":
            script_path = MODELS_DIR / "scripts" / "upgrade_skinmodel_xgboost.py"
            result = subprocess.run(
                ["python3", str(script_path)],
                capture_output=True,
                text=True,
                cwd=MODELS_DIR
            )

            return {
                "status": "completed" if result.returncode == 0 else "failed",
                "stdout": result.stdout,
                "stderr": result.stderr
            }

        elif model_type == "edgnet":
            script_path = MODELS_DIR / "scripts" / "train_edgnet_simple.py"
            result = subprocess.run(
                ["python3", str(script_path)],
                capture_output=True,
                text=True,
                cwd=MODELS_DIR
            )

            return {
                "status": "completed" if result.returncode == 0 else "failed",
                "stdout": result.stdout,
                "stderr": result.stderr
            }

        else:
            raise HTTPException(status_code=400, detail=f"Unknown model type: {model_type}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/inference/{api_name}")
async def test_inference(
    api_name: str,
    file: UploadFile = File(...)
):
    """추론 테스트"""
    try:
        # 임시 파일 저장
        temp_path = Path(f"/tmp/test_{api_name}_{file.filename}")
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # API 호출
        url = API_URLS.get(api_name)
        if not url:
            raise HTTPException(status_code=400, detail=f"Unknown API: {api_name}")

        async with httpx.AsyncClient(timeout=60.0) as client:
            with open(temp_path, "rb") as f:
                files = {"file": (file.filename, f, file.content_type)}

                if api_name == "yolo":
                    response = await client.post(f"{url}/api/v1/detect", files=files)
                elif api_name == "edocr2":
                    response = await client.post(f"{url}/api/v1/ocr", files=files)
                elif api_name == "skinmodel":
                    response = await client.post(f"{url}/api/v1/predict", files=files)
                else:
                    raise HTTPException(status_code=400, detail=f"API {api_name} does not support file upload")

        # 임시 파일 삭제
        temp_path.unlink()

        return response.json()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/gpu/stats")
async def get_gpu_stats():
    """GPU 상세 통계"""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,name,temperature.gpu,utilization.gpu,utilization.memory,memory.total,memory.used,memory.free",
             "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            parts = result.stdout.strip().split(", ")
            return {
                "index": int(parts[0]),
                "name": parts[1],
                "temperature": int(parts[2]),
                "gpu_utilization": float(parts[3]),
                "memory_utilization": float(parts[4]),
                "memory_total": int(parts[5]),
                "memory_used": int(parts[6]),
                "memory_free": int(parts[7])
            }
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/docker/{action}/{service}")
async def docker_action(action: str, service: str):
    """Docker 컨테이너 제어"""
    try:
        if action not in ["start", "stop", "restart"]:
            raise HTTPException(status_code=400, detail=f"Invalid action: {action}")

        if action == "restart":
            result = subprocess.run(
                ["docker-compose", "restart", service],
                capture_output=True,
                text=True,
                cwd=MODELS_DIR
            )
        elif action == "stop":
            result = subprocess.run(
                ["docker-compose", "stop", service],
                capture_output=True,
                text=True,
                cwd=MODELS_DIR
            )
        elif action == "start":
            result = subprocess.run(
                ["docker-compose", "start", service],
                capture_output=True,
                text=True,
                cwd=MODELS_DIR
            )

        return {
            "action": action,
            "service": service,
            "status": "success" if result.returncode == 0 else "failed",
            "output": result.stdout,
            "error": result.stderr
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================
# Training Management
# =====================

class TrainingConfig(BaseModel):
    """학습 설정"""
    epochs: int = 100
    batch_size: int = 8
    learning_rate: float = 0.001


@app.get("/api/training/list")
async def list_all_training_jobs():
    """모든 학습 작업 목록"""
    return {"jobs": list_training_jobs()}


@app.post("/api/training/start")
async def start_training(model_type: str, config: Optional[TrainingConfig] = None):
    """학습 작업 시작"""
    try:
        config_dict = config.dict() if config else {}
        job_id = create_training_job(model_type, config_dict)
        return {
            "job_id": job_id,
            "status": "started",
            "message": f"Training job {job_id} started"
        }
    except Exception as e:
        logger.error(f"Failed to start training: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/training/{job_id}")
async def get_training_status(job_id: str):
    """학습 진행 상태 조회"""
    job = get_training_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.post("/api/training/{job_id}/cancel")
async def cancel_training(job_id: str):
    """학습 작업 취소"""
    success = cancel_training_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found or not running")
    return {"job_id": job_id, "status": "cancelled"}


@app.get("/health")
async def health():
    """Dashboard health check"""
    return {"status": "healthy", "service": "admin-dashboard"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("DASHBOARD_PORT", 9000))
    logger.info(f"Starting Admin Dashboard on port {port}")

    uvicorn.run(
        "dashboard:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )
