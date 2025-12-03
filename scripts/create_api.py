#!/usr/bin/env python3
"""
API Scaffolding Script
새 API 서비스를 표준 구조로 빠르게 생성

Usage:
    python scripts/create_api.py my-custom-api --port 5015 --category detection

생성되는 파일:
    - models/my-custom-api/
        - api_server.py
        - Dockerfile
        - requirements.txt
    - gateway-api/api_specs/my-custom-api.yaml
    - docker-compose.yml에 서비스 추가 (선택)
"""

import argparse
import os
import re
import sys
from pathlib import Path
from datetime import datetime

# 프로젝트 루트 디렉토리
PROJECT_ROOT = Path(__file__).parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
SPECS_DIR = PROJECT_ROOT / "gateway-api" / "api_specs"


def to_snake_case(name: str) -> str:
    """kebab-case나 PascalCase를 snake_case로 변환"""
    name = name.replace("-", "_")
    name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
    return name


def to_pascal_case(name: str) -> str:
    """kebab-case나 snake_case를 PascalCase로 변환"""
    return "".join(word.capitalize() for word in re.split(r'[-_]', name))


def to_title_case(name: str) -> str:
    """kebab-case를 Title Case로 변환"""
    return " ".join(word.capitalize() for word in re.split(r'[-_]', name))


API_SERVER_TEMPLATE = '''"""
{title} API Server
{description}

포트: {port}
"""
import os
import time
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_PORT = int(os.getenv("{env_var}_PORT", "{port}"))


# =====================
# Schemas
# =====================

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str


class ProcessResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    processing_time: float
    error: Optional[str] = None


# =====================
# FastAPI App
# =====================

app = FastAPI(
    title="{title} API",
    description="{description}",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================
# API Endpoints
# =====================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스체크"""
    return HealthResponse(
        status="healthy",
        service="{api_id}-api",
        version="1.0.0",
        timestamp=datetime.now().isoformat()
    )


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check_v1():
    """헬스체크 (v1 경로)"""
    return await health_check()


@app.get("/api/v1/info")
async def get_info():
    """API 정보 (BlueprintFlow 메타데이터)"""
    return {{
        "id": "{api_id}",
        "name": "{title}",
        "display_name": "{title}",
        "version": "1.0.0",
        "description": "{description}",
        "base_url": f"http://localhost:{{API_PORT}}",
        "endpoint": "/api/v1/process",
        "method": "POST",
        "requires_image": {requires_image},
        "blueprintflow": {{
            "category": "{category}",
            "color": "{color}",
            "icon": "{icon}"
        }},
        "inputs": [
            {{"name": "image", "type": "Image", "required": True, "description": "입력 이미지"}}
        ],
        "outputs": [
            {{"name": "result", "type": "object", "description": "처리 결과"}}
        ],
        "parameters": []
    }}


@app.post("/api/v1/process", response_model=ProcessResponse)
async def process(
    file: UploadFile = File(..., description="입력 이미지"),
    # TODO: 필요한 파라미터 추가
):
    """
    메인 처리 엔드포인트

    TODO: 실제 처리 로직 구현
    """
    start_time = time.time()

    try:
        # 이미지 로드
        image_bytes = await file.read()
        logger.info(f"Processing image: {{file.filename}}, size: {{len(image_bytes)}} bytes")

        # TODO: 실제 처리 로직 구현
        result = {{
            "message": "Processing completed",
            "filename": file.filename,
            "size": len(image_bytes)
        }}

        processing_time = time.time() - start_time

        return ProcessResponse(
            success=True,
            data=result,
            processing_time=round(processing_time, 3)
        )

    except Exception as e:
        logger.error(f"Processing error: {{e}}")
        return ProcessResponse(
            success=False,
            data={{}},
            processing_time=time.time() - start_time,
            error=str(e)
        )


# =====================
# Main
# =====================

if __name__ == "__main__":
    logger.info(f"Starting {title} API on port {{API_PORT}}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=API_PORT,
        log_level="info"
    )
'''


DOCKERFILE_TEMPLATE = '''FROM python:3.10-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y --no-install-recommends \\
    libgl1-mesa-glx \\
    libglib2.0-0 \\
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 포트 노출
EXPOSE {port}

# 환경변수
ENV PYTHONUNBUFFERED=1
ENV {env_var}_PORT={port}

# 실행
CMD ["python", "api_server.py"]
'''


REQUIREMENTS_TEMPLATE = '''fastapi>=0.104.0
uvicorn>=0.24.0
python-multipart>=0.0.6
pydantic>=2.5.0
httpx>=0.25.0
Pillow>=10.0.0
numpy>=1.24.0
'''


SPEC_TEMPLATE = '''# {title} API Specification
apiVersion: v1
kind: APISpec

metadata:
  id: {api_id}
  name: {title}
  version: 1.0.0
  port: {port}
  description: {description}
  author: AX Team
  tags:
    - {category}

server:
  endpoint: /api/v1/process
  method: POST
  contentType: multipart/form-data
  timeout: 60
  healthEndpoint: /health

blueprintflow:
  category: {category}
  color: "{color}"
  icon: {icon}
  requiresImage: {requires_image_yaml}

inputs:
  - name: image
    type: Image
    required: true
    description: 입력 이미지

outputs:
  - name: result
    type: object
    description: 처리 결과

parameters: []

i18n:
  ko:
    label: {title}
    description: {description}
  en:
    label: {title}
    description: {description}
'''


DOCKER_COMPOSE_SERVICE = '''
  {service_name}:
    build: ./models/{api_id}-api
    container_name: {api_id}-api
    ports:
      - "{port}:{port}"
    environment:
      - {env_var}_PORT={port}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:{port}/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
'''


# 카테고리별 기본 색상
CATEGORY_COLORS = {
    "detection": "#10b981",
    "ocr": "#3b82f6",
    "segmentation": "#8b5cf6",
    "preprocessing": "#f59e0b",
    "analysis": "#ef4444",
    "knowledge": "#9333ea",
    "ai": "#ec4899",
    "control": "#64748b",
}

# 카테고리별 기본 아이콘
CATEGORY_ICONS = {
    "detection": "Target",
    "ocr": "FileText",
    "segmentation": "Network",
    "preprocessing": "Wand2",
    "analysis": "Calculator",
    "knowledge": "Database",
    "ai": "Brain",
    "control": "GitBranch",
}


def create_api(
    api_id: str,
    port: int,
    category: str,
    description: str = "",
    icon: str = None,
    color: str = None,
    requires_image: bool = True,
    add_to_compose: bool = False
):
    """새 API 서비스 생성"""

    # 이름 변환
    title = to_title_case(api_id)
    env_var = to_snake_case(api_id).upper()
    service_name = f"{api_id}-api"

    # 기본값 설정
    if not description:
        description = f"{title} 처리 API"
    if not color:
        color = CATEGORY_COLORS.get(category, "#6366f1")
    if not icon:
        icon = CATEGORY_ICONS.get(category, "Box")

    print(f"\n{'='*60}")
    print(f"🚀 새 API 생성: {title}")
    print(f"{'='*60}")
    print(f"  ID: {api_id}")
    print(f"  Port: {port}")
    print(f"  Category: {category}")
    print(f"  Color: {color}")
    print(f"  Icon: {icon}")
    print(f"{'='*60}\n")

    # API 디렉토리 생성
    api_dir = MODELS_DIR / f"{api_id}-api"
    if api_dir.exists():
        print(f"⚠️  디렉토리가 이미 존재합니다: {api_dir}")
        response = input("덮어쓰시겠습니까? (y/N): ")
        if response.lower() != 'y':
            print("취소되었습니다.")
            return False

    api_dir.mkdir(parents=True, exist_ok=True)

    # api_server.py 생성
    api_server_content = API_SERVER_TEMPLATE.format(
        title=title,
        description=description,
        port=port,
        env_var=env_var,
        api_id=api_id,
        category=category,
        color=color,
        icon=icon,
        requires_image=str(requires_image)
    )
    (api_dir / "api_server.py").write_text(api_server_content)
    print(f"✅ 생성됨: {api_dir / 'api_server.py'}")

    # Dockerfile 생성
    dockerfile_content = DOCKERFILE_TEMPLATE.format(
        port=port,
        env_var=env_var
    )
    (api_dir / "Dockerfile").write_text(dockerfile_content)
    print(f"✅ 생성됨: {api_dir / 'Dockerfile'}")

    # requirements.txt 생성
    (api_dir / "requirements.txt").write_text(REQUIREMENTS_TEMPLATE)
    print(f"✅ 생성됨: {api_dir / 'requirements.txt'}")

    # API 스펙 파일 생성
    SPECS_DIR.mkdir(parents=True, exist_ok=True)
    spec_content = SPEC_TEMPLATE.format(
        title=title,
        api_id=api_id,
        port=port,
        description=description,
        category=category,
        color=color,
        icon=icon,
        requires_image_yaml="true" if requires_image else "false"
    )
    spec_file = SPECS_DIR / f"{api_id}.yaml"
    spec_file.write_text(spec_content)
    print(f"✅ 생성됨: {spec_file}")

    # docker-compose.yml에 추가 (선택)
    if add_to_compose:
        compose_file = PROJECT_ROOT / "docker-compose.yml"
        if compose_file.exists():
            compose_service = DOCKER_COMPOSE_SERVICE.format(
                service_name=service_name,
                api_id=api_id,
                port=port,
                env_var=env_var
            )
            print(f"\n📋 docker-compose.yml에 추가할 서비스 정의:")
            print(compose_service)
            print("\n(수동으로 docker-compose.yml의 services 섹션에 추가해주세요)")

    print(f"\n{'='*60}")
    print(f"🎉 API 생성 완료!")
    print(f"{'='*60}")
    print(f"\n다음 단계:")
    print(f"  1. {api_dir / 'api_server.py'} 에서 process() 함수 구현")
    print(f"  2. 필요한 의존성을 requirements.txt에 추가")
    print(f"  3. docker-compose.yml에 서비스 추가")
    print(f"  4. docker-compose up --build {service_name}")
    print(f"\n테스트:")
    print(f"  curl http://localhost:{port}/health")
    print(f"  curl http://localhost:{port}/api/v1/info")
    print()

    return True


def main():
    parser = argparse.ArgumentParser(
        description="새 API 서비스를 표준 구조로 생성합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python scripts/create_api.py my-detector --port 5015 --category detection
  python scripts/create_api.py text-parser --port 5016 --category ocr --description "텍스트 파싱 API"
  python scripts/create_api.py image-enhancer --port 5017 --category preprocessing --icon ZoomIn
        """
    )

    parser.add_argument("api_id", help="API ID (예: my-detector, text-parser)")
    parser.add_argument("--port", "-p", type=int, required=True, help="API 포트 번호")
    parser.add_argument(
        "--category", "-c",
        choices=list(CATEGORY_COLORS.keys()),
        default="detection",
        help="BlueprintFlow 카테고리"
    )
    parser.add_argument("--description", "-d", default="", help="API 설명")
    parser.add_argument("--icon", help="Lucide 아이콘 이름")
    parser.add_argument("--color", help="노드 색상 (hex, 예: #10b981)")
    parser.add_argument("--no-image", action="store_true", help="이미지 입력 불필요")
    parser.add_argument("--add-to-compose", action="store_true", help="docker-compose.yml에 추가")

    args = parser.parse_args()

    # API ID 검증
    if not re.match(r'^[a-z][a-z0-9-]*$', args.api_id):
        print("오류: API ID는 소문자로 시작하고, 소문자/숫자/하이픈만 사용 가능합니다.")
        sys.exit(1)

    # 포트 검증
    if args.port < 1000 or args.port > 65535:
        print("오류: 포트는 1000-65535 범위여야 합니다.")
        sys.exit(1)

    success = create_api(
        api_id=args.api_id,
        port=args.port,
        category=args.category,
        description=args.description,
        icon=args.icon,
        color=args.color,
        requires_image=not args.no_image,
        add_to_compose=args.add_to_compose
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
