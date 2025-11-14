# PaddleOCR API Dockerfile
FROM python:3.10-slim

WORKDIR /app

# 시스템 패키지 설치 (OpenCV 및 PaddlePaddle 의존성)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY api_server.py .

# PaddleOCR 모델 다운로드를 위한 디렉토리 생성
RUN mkdir -p /root/.paddleocr

# 포트 노출
EXPOSE 5006

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5006/api/v1/health || exit 1

# 서버 실행
CMD ["python", "api_server.py"]
