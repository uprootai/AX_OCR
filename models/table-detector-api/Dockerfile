FROM python:3.10-slim

WORKDIR /app

# 시스템 의존성 설치 (OpenCV, Tesseract)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    tesseract-ocr \
    tesseract-ocr-kor \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY api_server.py .
COPY routers/ ./routers/
COPY services/ ./services/

# 업로드/결과 디렉토리 생성
RUN mkdir -p /tmp/table-detector/uploads /tmp/table-detector/results

# 포트 노출
EXPOSE 5022

# 환경변수
ENV PYTHONUNBUFFERED=1
ENV TABLE_DETECTOR_PORT=5022
ENV FLAGS_use_mkldnn=0

# 실행
CMD ["python", "api_server.py"]
