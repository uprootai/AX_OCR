#!/usr/bin/env python3
"""
학습 관리 모듈
웹 UI에서 대규모 학습을 관리하기 위한 백그라운드 작업 관리
"""

import os
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import threading
import logging

logger = logging.getLogger(__name__)

# 학습 작업 상태 저장
training_jobs: Dict[str, Dict[str, Any]] = {}
training_lock = threading.Lock()


class TrainingJob:
    """학습 작업 클래스"""

    def __init__(self, job_id: str, model_type: str, config: Dict[str, Any]):
        self.job_id = job_id
        self.model_type = model_type
        self.config = config
        self.status = "pending"
        self.progress = 0.0
        self.current_epoch = 0
        self.total_epochs = config.get('epochs', 100)
        self.logs = []
        self.started_at = None
        self.completed_at = None
        self.error = None

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "job_id": self.job_id,
            "model_type": self.model_type,
            "config": self.config,
            "status": self.status,
            "progress": self.progress,
            "current_epoch": self.current_epoch,
            "total_epochs": self.total_epochs,
            "logs": self.logs[-50:],  # 최근 50줄만
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error
        }


def create_training_job(model_type: str, config: Dict[str, Any]) -> str:
    """학습 작업 생성"""
    job_id = f"{model_type}_{int(time.time())}"

    with training_lock:
        job = TrainingJob(job_id, model_type, config)
        training_jobs[job_id] = job

    # 백그라운드로 학습 시작
    thread = threading.Thread(target=run_training, args=(job_id,))
    thread.daemon = True
    thread.start()

    return job_id


def get_training_job(job_id: str) -> Optional[Dict[str, Any]]:
    """학습 작업 상태 조회"""
    with training_lock:
        job = training_jobs.get(job_id)
        return job.to_dict() if job else None


def list_training_jobs() -> list:
    """모든 학습 작업 목록"""
    with training_lock:
        return [job.to_dict() for job in training_jobs.values()]


def run_training(job_id: str):
    """학습 실행 (백그라운드)"""
    with training_lock:
        job = training_jobs.get(job_id)
        if not job:
            return

    try:
        job.status = "running"
        job.started_at = datetime.now().isoformat()
        logger.info(f"Starting training job {job_id}")

        if job.model_type == "edgnet_large":
            run_edgnet_large_training(job)
        elif job.model_type == "yolo_custom":
            run_yolo_custom_training(job)
        elif job.model_type == "skinmodel":
            run_skinmodel_training(job)
        elif job.model_type == "edgnet":
            run_edgnet_simple_training(job)
        else:
            raise ValueError(f"Unknown model type: {job.model_type}")

        job.status = "completed"
        job.progress = 100.0
        logger.info(f"Training job {job_id} completed")

    except Exception as e:
        logger.error(f"Training job {job_id} failed: {e}")
        job.status = "failed"
        job.error = str(e)
        job.logs.append(f"ERROR: {str(e)}")

    finally:
        job.completed_at = datetime.now().isoformat()


def run_edgnet_large_training(job: TrainingJob):
    """EDGNet 대규모 학습 실행"""
    job.logs.append("🚀 EDGNet 대규모 학습 시작...")

    # 데이터셋 확인
    data_path = Path("/home/uproot/ax/poc/edgnet_dataset_large")
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset not found: {data_path}")

    job.logs.append(f"✅ 데이터셋 확인: {data_path}")

    # 학습 스크립트 경로
    script_path = Path("/home/uproot/ax/poc/scripts/train_edgnet_large.py")

    # 학습 파라미터
    epochs = job.config.get('epochs', 100)
    batch_size = job.config.get('batch_size', 8)

    job.logs.append(f"📊 학습 파라미터:")
    job.logs.append(f"   - Epochs: {epochs}")
    job.logs.append(f"   - Batch size: {batch_size}")

    # 학습 실행
    cmd = [
        "python3",
        str(script_path),
        "--data", str(data_path),
        "--epochs", str(epochs),
        "--batch-size", str(batch_size)
    ]

    job.logs.append(f"🔧 실행 명령: {' '.join(cmd)}")

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    # 실시간 로그 및 진행률 업데이트
    import re
    for line in process.stdout:
        line = line.strip()
        if line:
            job.logs.append(line)

            # Epoch 진행률 파싱 - 정규표현식 사용
            # "Epoch 10/100:" 또는 "Epoch 10/100" 형식 파싱
            epoch_match = re.search(r'Epoch\s+(\d+)/(\d+)', line)
            if epoch_match:
                try:
                    current = int(epoch_match.group(1))
                    total = int(epoch_match.group(2))
                    job.current_epoch = current
                    job.total_epochs = total
                    job.progress = (current / total) * 100
                except:
                    pass

    process.wait()

    if process.returncode != 0:
        raise RuntimeError(f"Training failed with exit code {process.returncode}")

    job.logs.append("✅ EDGNet 대규모 학습 완료!")


def run_yolo_custom_training(job: TrainingJob):
    """YOLO 커스텀 학습 실행"""
    job.logs.append("🎯 YOLO 커스텀 학습 시작...")

    # 데이터셋 확인
    data_yaml = Path("/home/uproot/ax/poc/datasets/real_drawings_yolo/dataset.yaml")
    if not data_yaml.exists():
        raise FileNotFoundError(f"Dataset config not found: {data_yaml}")

    job.logs.append(f"✅ 데이터셋 설정 확인: {data_yaml}")

    epochs = job.config.get('epochs', 50)
    batch_size = job.config.get('batch_size', 16)

    cmd = [
        "python3",
        "/home/uproot/ax/poc/yolo-api/train.py",
        "--data", str(data_yaml),
        "--epochs", str(epochs),
        "--batch-size", str(batch_size)
    ]

    job.logs.append(f"🔧 실행 명령: {' '.join(cmd)}")

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    for line in process.stdout:
        line = line.strip()
        if line:
            job.logs.append(line)

            # Epoch 진행률 파싱
            if "Epoch" in line or "epoch" in line:
                try:
                    parts = line.split("/")
                    if len(parts) >= 2:
                        current = int(parts[0].split()[-1])
                        total = int(parts[1].split()[0])
                        job.current_epoch = current
                        job.total_epochs = total
                        job.progress = (current / total) * 100
                except:
                    pass

    process.wait()

    if process.returncode != 0:
        raise RuntimeError(f"Training failed with exit code {process.returncode}")

    job.logs.append("✅ YOLO 커스텀 학습 완료!")


def run_skinmodel_training(job: TrainingJob):
    """Skin Model 학습 실행 (기존)"""
    job.logs.append("🔬 Skin Model 학습 시작...")

    script_path = Path("/home/uproot/ax/poc/scripts/upgrade_skinmodel_xgboost.py")

    cmd = ["python3", str(script_path)]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        cwd="/home/uproot/ax/poc"
    )

    for line in process.stdout:
        line = line.strip()
        if line:
            job.logs.append(line)
            job.progress = min(job.progress + 5, 95)  # 점진적 진행

    process.wait()

    if process.returncode != 0:
        raise RuntimeError(f"Training failed with exit code {process.returncode}")

    job.progress = 100
    job.logs.append("✅ Skin Model 학습 완료!")


def run_edgnet_simple_training(job: TrainingJob):
    """EDGNet 간단 학습 실행 (기존)"""
    job.logs.append("📐 EDGNet 간단 학습 시작...")

    script_path = Path("/home/uproot/ax/poc/scripts/train_edgnet_simple.py")

    cmd = ["python3", str(script_path)]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        cwd="/home/uproot/ax/poc"
    )

    for line in process.stdout:
        line = line.strip()
        if line:
            job.logs.append(line)
            job.progress = min(job.progress + 5, 95)

    process.wait()

    if process.returncode != 0:
        raise RuntimeError(f"Training failed with exit code {process.returncode}")

    job.progress = 100
    job.logs.append("✅ EDGNet 간단 학습 완료!")


def cancel_training_job(job_id: str) -> bool:
    """학습 작업 취소 (TODO: 구현)"""
    with training_lock:
        job = training_jobs.get(job_id)
        if job and job.status == "running":
            job.status = "cancelled"
            job.logs.append("⚠️  사용자에 의해 취소됨")
            return True
    return False
