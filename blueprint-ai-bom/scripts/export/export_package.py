"""Export Package - Blueprint AI BOM 납품 패키지 생성 스크립트

고객 온프레미스 환경에 배포할 standalone 패키지를 생성합니다.

사용법:
    python export_package.py --customer "고객명" --output ./export

생성 결과:
    export/
    ├── config/           # 설정 파일
    ├── frontend/         # 빌드된 프론트엔드
    ├── backend/          # 백엔드 서비스
    ├── docker/           # Docker Compose 설정
    ├── scripts/          # 설치/시작/중지 스크립트
    └── docs/             # 사용자 문서
"""

import argparse
import json
import os
import shutil
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class PackageExporter:
    """납품 패키지 생성기"""

    VERSION = "1.0.0"

    # 기본 포함 API 목록
    DEFAULT_APIS = ["yolo-api", "blueprint-ai-bom-backend"]

    # 프로젝트 루트 경로 (상대 경로 기준)
    PROJECT_ROOT = Path(__file__).parent.parent.parent

    def __init__(
        self,
        customer_name: str,
        output_dir: str,
        include_apis: Optional[List[str]] = None,
        include_models: bool = True,
        include_docs: bool = True,
        skip_frontend_build: bool = False,
    ):
        self.customer_name = customer_name
        self.customer_slug = self._slugify(customer_name)
        self.output_dir = Path(output_dir)
        self.include_apis = include_apis or self.DEFAULT_APIS
        self.include_models = include_models
        self.include_docs = include_docs
        self.skip_frontend_build = skip_frontend_build
        self.created_at = datetime.now().isoformat()

    def _slugify(self, text: str) -> str:
        """문자열을 URL-safe slug로 변환"""
        import re
        text = text.lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text)
        return text

    def export(self) -> Path:
        """전체 Export 프로세스 실행"""
        logger.info("=" * 60)
        logger.info(f"Blueprint AI BOM 납품 패키지 생성")
        logger.info(f"고객: {self.customer_name}")
        logger.info(f"버전: {self.VERSION}")
        logger.info("=" * 60)

        try:
            # 1. 출력 디렉토리 설정
            self._setup_directories()

            # 2. 설정 파일 생성
            logger.info("\n[1/6] 설정 파일 생성...")
            self._generate_configs()

            # 3. Frontend 빌드 또는 복사
            logger.info("\n[2/6] Frontend 패키징...")
            self._package_frontend()

            # 4. Backend 패키징
            logger.info("\n[3/6] Backend 패키징...")
            self._package_backend()

            # 5. Docker 설정 생성
            logger.info("\n[4/6] Docker 설정 생성...")
            self._generate_docker_config()

            # 6. 스크립트 생성
            logger.info("\n[5/6] 실행 스크립트 생성...")
            self._generate_scripts()

            # 7. 문서 생성
            if self.include_docs:
                logger.info("\n[6/6] 문서 생성...")
                self._generate_docs()

            # 8. 최종 패키지 생성
            logger.info("\n패키지 압축...")
            package_path = self._create_final_package()

            logger.info("\n" + "=" * 60)
            logger.info(f"패키지 생성 완료!")
            logger.info(f"위치: {package_path}")
            logger.info("=" * 60)

            return package_path

        except Exception as e:
            logger.error(f"\n패키지 생성 실패: {e}")
            raise

    def _setup_directories(self):
        """출력 디렉토리 구조 생성"""
        dirs = ['config', 'frontend', 'backend', 'docker', 'scripts', 'docs', 'data']
        for d in dirs:
            (self.output_dir / d).mkdir(parents=True, exist_ok=True)
        logger.info(f"  출력 디렉토리: {self.output_dir}")

    def _generate_configs(self):
        """설정 파일 생성"""
        config_dir = self.output_dir / 'config'

        # 1. 템플릿 설정
        template_config = {
            "meta": {
                "id": f"{self.customer_slug}-blueprint-bom",
                "name": f"{self.customer_name} Blueprint AI BOM",
                "version": self.VERSION,
                "created_at": self.created_at,
                "description": "전력 설비 단선도 BOM 자동 생성 시스템"
            },
            "workflow": {
                "steps": [
                    {"id": "upload", "name": "도면 업로드", "type": "input"},
                    {"id": "detect", "name": "부품 검출", "type": "yolo"},
                    {"id": "verify", "name": "검증", "type": "verification"},
                    {"id": "bom", "name": "BOM 생성", "type": "output"}
                ],
                "require_verification": True,
                "auto_approve_threshold": 0.95
            },
            "required_apis": [
                {"id": "yolo-api", "port": 5005, "required": True},
                {"id": "blueprint-ai-bom-backend", "port": 5020, "required": True}
            ]
        }
        with open(config_dir / 'template.json', 'w', encoding='utf-8') as f:
            json.dump(template_config, f, ensure_ascii=False, indent=2)

        # 2. API 설정
        api_config = {
            "yolo_api": {
                "url": "http://yolo-api:5005",
                "port": 5005,
                "model_type": "bom_detector",
                "confidence": 0.40,
                "iou": 0.50
            },
            "bom_api": {
                "url": "http://blueprint-ai-bom-backend:5020",
                "port": 5020
            }
        }
        with open(config_dir / 'api_config.json', 'w', encoding='utf-8') as f:
            json.dump(api_config, f, ensure_ascii=False, indent=2)

        # 3. 가격 데이터 복사
        pricing_src = self.PROJECT_ROOT / 'backend' / 'classes_info_with_pricing.json'
        if pricing_src.exists():
            shutil.copy2(pricing_src, config_dir / 'classes_info_with_pricing.json')
            logger.info("    가격 데이터 복사 완료")

        logger.info(f"    생성된 설정 파일: template.json, api_config.json")

    def _package_frontend(self):
        """Frontend 패키징"""
        frontend_src = self.PROJECT_ROOT / 'frontend'
        frontend_dst = self.output_dir / 'frontend'

        if self.skip_frontend_build:
            # 기존 빌드 결과 복사
            dist_src = frontend_src / 'dist'
            if dist_src.exists():
                shutil.copytree(dist_src, frontend_dst / 'dist', dirs_exist_ok=True)
                logger.info("    기존 빌드 결과 복사")
            else:
                logger.warning("    빌드된 frontend 없음 - 스킵")
        else:
            # 새로 빌드 (npm run build)
            try:
                subprocess.run(
                    ['npm', 'run', 'build'],
                    cwd=str(frontend_src),
                    check=True,
                    capture_output=True
                )
                dist_src = frontend_src / 'dist'
                if dist_src.exists():
                    shutil.copytree(dist_src, frontend_dst / 'dist', dirs_exist_ok=True)
                logger.info("    Frontend 빌드 및 복사 완료")
            except subprocess.CalledProcessError as e:
                logger.warning(f"    Frontend 빌드 실패: {e}")
                logger.info("    기존 빌드 결과 복사 시도...")
                dist_src = frontend_src / 'dist'
                if dist_src.exists():
                    shutil.copytree(dist_src, frontend_dst / 'dist', dirs_exist_ok=True)

        # nginx 설정 생성
        nginx_config = """server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://blueprint-ai-bom-backend:5020/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
"""
        with open(frontend_dst / 'nginx.conf', 'w') as f:
            f.write(nginx_config)

    def _package_backend(self):
        """Backend 패키징"""
        backend_src = self.PROJECT_ROOT / 'backend'
        backend_dst = self.output_dir / 'backend'

        # 필요한 파일만 복사
        files_to_copy = [
            'api_server.py',
            'requirements.txt',
            'Dockerfile',
            'classes_info_with_pricing.json',
        ]

        dirs_to_copy = [
            'routers',
            'schemas',
            'services',
        ]

        for f in files_to_copy:
            src = backend_src / f
            if src.exists():
                shutil.copy2(src, backend_dst / f)

        for d in dirs_to_copy:
            src = backend_src / d
            if src.exists():
                shutil.copytree(
                    src, backend_dst / d,
                    dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.pytest_cache')
                )

        logger.info(f"    Backend 파일 복사 완료")

    def _generate_docker_config(self):
        """Docker Compose 설정 생성"""
        docker_dir = self.output_dir / 'docker'

        # docker-compose.yml
        compose_content = f"""version: '3.8'

services:
  # Frontend (Nginx)
  web:
    image: nginx:alpine
    container_name: {self.customer_slug}-web
    ports:
      - "${{WEB_PORT:-3001}}:80"
    volumes:
      - ../frontend/dist:/usr/share/nginx/html:ro
      - ../frontend/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - {self.customer_slug}-network

  # Backend API
  backend:
    build:
      context: ../backend
      dockerfile: Dockerfile
    container_name: {self.customer_slug}-backend
    ports:
      - "${{API_PORT:-5020}}:5020"
    volumes:
      - ../config:/app/config:ro
      - ../data:/app/data
    environment:
      - YOLO_API_URL=http://yolo-api:5005
      - PRICING_DB_PATH=/app/config/classes_info_with_pricing.json
    depends_on:
      - yolo-api
    restart: unless-stopped
    networks:
      - {self.customer_slug}-network

  # YOLO Detection API
  yolo-api:
    image: uproot/yolo-api:latest
    container_name: {self.customer_slug}-yolo
    ports:
      - "${{YOLO_PORT:-5005}}:5005"
    environment:
      - DEVICE=${{DEVICE:-cuda}}
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped
    networks:
      - {self.customer_slug}-network

networks:
  {self.customer_slug}-network:
    driver: bridge

volumes:
  data:
"""
        with open(docker_dir / 'docker-compose.yml', 'w') as f:
            f.write(compose_content)

        # .env.example
        env_content = f"""# {self.customer_name} Blueprint AI BOM 환경 설정

# 포트 설정
WEB_PORT=3001
API_PORT=5020
YOLO_PORT=5005

# GPU 설정 (cuda 또는 cpu)
DEVICE=cuda
"""
        with open(docker_dir / '.env.example', 'w') as f:
            f.write(env_content)

        # .env (기본값)
        with open(docker_dir / '.env', 'w') as f:
            f.write(env_content)

        logger.info("    Docker Compose 설정 생성 완료")

    def _generate_scripts(self):
        """실행 스크립트 생성"""
        scripts_dir = self.output_dir / 'scripts'

        # install.sh
        install_script = f"""#!/bin/bash
# {self.customer_name} Blueprint AI BOM 설치 스크립트

set -e

echo "=================================================="
echo "{self.customer_name} Blueprint AI BOM 설치"
echo "=================================================="

# Docker 확인
if ! command -v docker &> /dev/null; then
    echo "Error: Docker가 설치되어 있지 않습니다."
    exit 1
fi

# Docker Compose 확인
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Error: Docker Compose가 설치되어 있지 않습니다."
    exit 1
fi

# GPU 확인
if command -v nvidia-smi &> /dev/null; then
    echo "GPU 감지됨: $(nvidia-smi --query-gpu=name --format=csv,noheader)"
else
    echo "Warning: NVIDIA GPU가 감지되지 않습니다. CPU 모드로 실행됩니다."
    sed -i 's/DEVICE=cuda/DEVICE=cpu/' ../docker/.env
fi

# Backend 이미지 빌드
echo ""
echo "Docker 이미지 빌드 중..."
cd ../docker
docker compose build

echo ""
echo "설치 완료!"
echo "실행: ./start.sh"
"""
        with open(scripts_dir / 'install.sh', 'w') as f:
            f.write(install_script)

        # start.sh
        start_script = f"""#!/bin/bash
# {self.customer_name} Blueprint AI BOM 시작

cd "$(dirname "$0")/../docker"

echo "서비스 시작 중..."
docker compose up -d

echo ""
echo "서비스 상태:"
docker compose ps

echo ""
echo "=================================================="
echo "웹 UI: http://localhost:${{WEB_PORT:-3001}}"
echo "API: http://localhost:${{API_PORT:-5020}}"
echo "=================================================="
"""
        with open(scripts_dir / 'start.sh', 'w') as f:
            f.write(start_script)

        # stop.sh
        stop_script = f"""#!/bin/bash
# {self.customer_name} Blueprint AI BOM 중지

cd "$(dirname "$0")/../docker"

echo "서비스 중지 중..."
docker compose down

echo "서비스가 중지되었습니다."
"""
        with open(scripts_dir / 'stop.sh', 'w') as f:
            f.write(stop_script)

        # logs.sh
        logs_script = f"""#!/bin/bash
# 로그 확인

cd "$(dirname "$0")/../docker"

docker compose logs -f "$@"
"""
        with open(scripts_dir / 'logs.sh', 'w') as f:
            f.write(logs_script)

        # 실행 권한 부여
        for script in ['install.sh', 'start.sh', 'stop.sh', 'logs.sh']:
            os.chmod(scripts_dir / script, 0o755)

        logger.info("    실행 스크립트 생성 완료")

    def _generate_docs(self):
        """문서 생성"""
        docs_dir = self.output_dir / 'docs'

        # INSTALL.md
        install_md = f"""# {self.customer_name} Blueprint AI BOM 설치 가이드

## 시스템 요구사항

- **OS**: Ubuntu 20.04+ / Windows 10+ (WSL2)
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **GPU**: NVIDIA GPU (CUDA 11.0+) - 권장
- **RAM**: 8GB 이상
- **디스크**: 10GB 이상

## 설치 절차

### 1. 패키지 압축 해제

```bash
tar -xzf {self.customer_slug}-blueprint-bom-v{self.VERSION}.tar.gz
cd {self.customer_slug}-blueprint-bom
```

### 2. 설치 스크립트 실행

```bash
cd scripts
./install.sh
```

### 3. 서비스 시작

```bash
./start.sh
```

### 4. 웹 UI 접속

브라우저에서 `http://localhost:3001` 접속

## 포트 설정

| 서비스 | 기본 포트 | 환경 변수 |
|--------|----------|-----------|
| Web UI | 3001 | WEB_PORT |
| API | 5020 | API_PORT |
| YOLO | 5005 | YOLO_PORT |

포트 변경은 `docker/.env` 파일을 수정하세요.

## 문제 해결

### GPU가 인식되지 않는 경우

1. NVIDIA 드라이버 설치 확인: `nvidia-smi`
2. NVIDIA Container Toolkit 설치: [설치 가이드](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
3. Docker 재시작: `sudo systemctl restart docker`

### 서비스가 시작되지 않는 경우

로그 확인:
```bash
cd scripts
./logs.sh backend
```

---

*생성일: {self.created_at}*
"""
        with open(docs_dir / 'INSTALL.md', 'w', encoding='utf-8') as f:
            f.write(install_md)

        # USER_MANUAL.md
        user_md = f"""# {self.customer_name} Blueprint AI BOM 사용자 매뉴얼

## 개요

전력 설비 단선도에서 부품을 자동으로 검출하고 BOM(Bill of Materials)을 생성하는 시스템입니다.

## 워크플로우

```
1. 도면 업로드 → 2. AI 부품 검출 → 3. 검증/수정 → 4. BOM 생성/다운로드
```

## 사용 방법

### 1. 도면 업로드

- 지원 형식: PNG, JPG, PDF
- 최대 크기: 50MB
- 해상도: 300 DPI 이상 권장

### 2. AI 부품 검출

업로드 후 자동으로 부품 검출이 시작됩니다.
- 검출 시간: 이미지당 약 2-5초
- 검출 대상: 27종 전력 설비 부품

### 3. 검증/수정

AI가 검출한 결과를 검토하고 수정합니다:

- **승인 (Approve)**: 검출이 정확한 경우
- **수정 (Modify)**: 클래스명이나 위치 수정
- **거부 (Reject)**: 오검출 제거
- **수동 추가**: 누락된 부품 직접 추가

### 4. BOM 생성

검증 완료 후 BOM을 생성합니다:

- **Excel**: 상세 가격 정보 포함
- **PDF**: 인쇄용 문서
- **CSV**: 시스템 연동용

## 검출 가능 부품 목록

| 클래스 | 설명 |
|--------|------|
| CT | 변류기 |
| PT | 계기용변압기 |
| TR | 변압기 |
| CB | 차단기 |
| DS | 단로기 |
| LA/SA | 피뢰기 |
| GIS | 가스절연개폐기 |
| ... | 총 27종 |

## 단축키

| 키 | 기능 |
|----|------|
| A | 승인 |
| R | 거부 |
| M | 수정 |
| N | 다음 |
| P | 이전 |

---

*버전: {self.VERSION}*
"""
        with open(docs_dir / 'USER_MANUAL.md', 'w', encoding='utf-8') as f:
            f.write(user_md)

        logger.info("    문서 생성 완료")

    def _create_final_package(self) -> Path:
        """최종 패키지 생성 (.tar.gz)"""
        package_name = f"{self.customer_slug}-blueprint-bom-v{self.VERSION}"
        package_path = self.output_dir.parent / f"{package_name}.tar.gz"

        # tar.gz 생성
        shutil.make_archive(
            str(self.output_dir.parent / package_name),
            'gztar',
            root_dir=self.output_dir.parent,
            base_dir=self.output_dir.name
        )

        return package_path


def main():
    parser = argparse.ArgumentParser(
        description='Blueprint AI BOM 납품 패키지 생성',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
    python export_package.py --customer "테크크로스" --output ./export
    python export_package.py --customer "삼성전자" --output ./export --skip-build
        """
    )

    parser.add_argument(
        '--customer', '-c',
        required=True,
        help='고객사 이름'
    )
    parser.add_argument(
        '--output', '-o',
        default='./export',
        help='출력 디렉토리 (기본: ./export)'
    )
    parser.add_argument(
        '--skip-build',
        action='store_true',
        help='Frontend 빌드 스킵 (기존 빌드 사용)'
    )
    parser.add_argument(
        '--no-docs',
        action='store_true',
        help='문서 생성 스킵'
    )

    args = parser.parse_args()

    exporter = PackageExporter(
        customer_name=args.customer,
        output_dir=args.output,
        skip_frontend_build=args.skip_build,
        include_docs=not args.no_docs,
    )

    exporter.export()


if __name__ == '__main__':
    main()
