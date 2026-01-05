FROM python:3.10-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY api_server.py .
COPY schemas.py .
COPY constants.py .
COPY checker.py .
COPY bwms_rules.py .
COPY bwms/ ./bwms/
COPY rule_loader.py .
COPY excel_parser.py .
COPY routers/ ./routers/
COPY services/ ./services/
COPY config/ ./config/
COPY templates/ ./templates/

# 포트 노출
EXPOSE 5019

# 환경변수
ENV PYTHONUNBUFFERED=1
ENV DESIGN_CHECKER_PORT=5019

# 실행
CMD ["python", "api_server.py"]
