FROM python:3.10-slim

WORKDIR /app

# 시스템 의존성 설치 (OpenCV용)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 포트 노출
EXPOSE 5016

# 환경변수
ENV PYTHONUNBUFFERED=1
ENV LINE_DETECTOR_PORT=5016

# 실행
CMD ["python", "api_server.py"]
