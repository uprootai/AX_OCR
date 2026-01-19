# Blueprint AI BOM - Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 설치 (detectron2 빌드용 gcc, git 포함)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    curl \
    git \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치 (detectron2 제외)
COPY requirements.txt .
RUN grep -v -E '^#|^$|detectron2' requirements.txt > /tmp/reqs.txt && \
    pip install --no-cache-dir -r /tmp/reqs.txt

# Detectron2 설치 (CUDA 11.8 / PyTorch 2.0 기준)
# GPU 버전: 사전 빌드된 wheel 사용 (빠른 설치)
# CPU 버전은 아래 주석 해제:
#   RUN pip install --no-cache-dir 'git+https://github.com/facebookresearch/detectron2.git'
ARG CUDA_VERSION=cu118
ARG TORCH_VERSION=torch2.0
RUN pip install --no-cache-dir detectron2 \
    -f https://dl.fbaipublicfiles.com/detectron2/wheels/${CUDA_VERSION}/${TORCH_VERSION}/index.html \
    || pip install --no-cache-dir 'git+https://github.com/facebookresearch/detectron2.git'

# 소스 코드 복사
COPY . .

# 환경 변수
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# 포트 노출
EXPOSE 5020

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5020/health || exit 1

# 서버 실행
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "5020"]
