# PaddleOCR 2.x API Dockerfile
# PP-OCRv4: CPU compatible, 80+ languages
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
COPY routers/ ./routers/
COPY models/ ./models/
COPY services/ ./services/
COPY utils/ ./utils/

# PaddleOCR 모델 다운로드를 위한 디렉토리 생성
# PP-OCRv4 모델은 자동 다운로드됨
RUN mkdir -p /root/.paddleocr

# 포트 노출
EXPOSE 5006

# 헬스체크 (모델 로드 시간 고려하여 start-period 90초)
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:5006/api/v1/health || exit 1

# 서버 실행
CMD ["python", "api_server.py"]
