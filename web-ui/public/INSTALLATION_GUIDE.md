# AX 도면 분석 시스템 - 설치 가이드

> 온프레미스 납품용 설치 및 운영 매뉴얼
> 버전: 1.0.0
> 작성일: 2025-11-13

---

## 📋 목차

1. [시스템 요구사항](#시스템-요구사항)
2. [사전 준비사항](#사전-준비사항)
3. [설치 절차](#설치-절차)
4. [초기 설정](#초기-설정)
5. [서비스 시작/중지](#서비스-시작중지)
6. [포트 설정 변경](#포트-설정-변경)
7. [GPU 설정](#gpu-설정)
8. [백업 및 복원](#백업-및-복원)
9. [업그레이드](#업그레이드)
10. [문제 해결](#문제-해결)

---

## 🖥️ 시스템 요구사항

### 최소 사양
- **OS**: Ubuntu 20.04 LTS / CentOS 8 / RHEL 8 이상
- **CPU**: 4 Core 이상
- **RAM**: 16GB 이상
- **디스크**: 100GB 이상 (SSD 권장)
- **네트워크**: 1Gbps 이상

### 권장 사양 (GPU 사용 시)
- **OS**: Ubuntu 22.04 LTS
- **CPU**: 8 Core 이상 (Intel Xeon / AMD EPYC)
- **RAM**: 32GB 이상
- **GPU**: NVIDIA GPU (CUDA 11.8 이상 지원)
  - VRAM 8GB 이상 (RTX 3070 / A4000 이상)
- **디스크**: 200GB 이상 (NVMe SSD)
- **네트워크**: 10Gbps

### 소프트웨어 요구사항
- Docker 24.0 이상
- Docker Compose 2.20 이상
- (GPU 사용 시) NVIDIA Docker Runtime

---

## 🔧 사전 준비사항

### 1. Docker 설치

#### Ubuntu/Debian

**기존 Docker 제거**: 시스템에 이전 버전의 Docker가 설치되어 있는 경우 먼저 제거합니다. 이는 버전 충돌을 방지하기 위함입니다.

**필수 패키지 설치**: Docker 설치에 필요한 인증서 관리 도구(`ca-certificates`), 다운로드 도구(`curl`), GPG 키 관리 도구(`gnupg`), 배포판 정보 도구(`lsb-release`)를 설치합니다.

**Docker GPG 키 추가**: Docker 패키지의 무결성을 검증하기 위한 공식 GPG 키를 다운로드하여 시스템에 등록합니다. 이 키는 `/etc/apt/keyrings/` 디렉토리에 안전하게 저장됩니다.

**Docker 저장소 추가**: 시스템의 패키지 관리자가 Docker 공식 저장소를 인식하도록 APT 소스 목록에 추가합니다. 현재 Ubuntu 버전에 맞는 stable 버전 저장소가 자동으로 선택됩니다.

**Docker 설치**: Docker Engine, Docker CLI, Container Runtime, Build 플러그인, Compose 플러그인을 포함한 전체 Docker 패키지를 설치합니다.

**설치 확인**: `docker --version` 및 `docker compose version` 명령어로 설치된 Docker와 Docker Compose의 버전을 확인합니다. 정상적으로 버전 정보가 표시되면 설치가 완료된 것입니다.

#### CentOS/RHEL

**기존 Docker 제거**: 시스템에 설치된 모든 이전 버전의 Docker 관련 패키지를 제거합니다.

**Docker 저장소 설정**: YUM 저장소 관리 도구를 설치한 후, Docker 공식 CentOS 저장소를 추가합니다.

**Docker 설치**: Docker Engine, CLI, Container Runtime 및 관련 플러그인을 설치합니다.

**Docker 시작**: systemd를 통해 Docker 서비스를 시작하고, 시스템 부팅 시 자동으로 시작되도록 설정합니다.

**설치 확인**: Docker와 Docker Compose의 버전 정보를 확인하여 설치가 정상적으로 완료되었는지 검증합니다.

### 2. NVIDIA Docker 설치 (GPU 사용 시)

**NVIDIA Driver 확인**: `nvidia-smi` 명령어로 NVIDIA 그래픽 드라이버가 정상적으로 설치되어 있는지 확인합니다. GPU 정보와 드라이버 버전이 표시되어야 합니다.

**NVIDIA Container Toolkit 설치**: Docker 컨테이너 내에서 GPU를 사용할 수 있도록 NVIDIA Container Toolkit을 설치합니다. 먼저 배포판 정보를 확인하고, NVIDIA 공식 저장소 GPG 키와 패키지 목록을 추가합니다. 그 다음 `nvidia-container-toolkit` 패키지를 설치합니다.

**Docker 재시작**: NVIDIA Container Toolkit 설정을 적용하기 위해 Docker 서비스를 재시작합니다.

**테스트**: NVIDIA CUDA 공식 이미지를 사용하여 컨테이너 내에서 `nvidia-smi`를 실행해봅니다. GPU 정보가 정상적으로 표시되면 설정이 완료된 것입니다.

### 3. 방화벽 설정

**Ubuntu UFW**: Ubuntu 방화벽에서 각 서비스별로 필요한 TCP 포트를 허용합니다:
- 5173: 웹 UI 접속용
- 8000: Gateway API (메인 오케스트레이터)
- 5002: eDOCr2 API (OCR 서비스)
- 5003: Skin Model API (공차 분석)
- 5005: YOLO API (객체 감지)
- 5006: PaddleOCR API (보조 OCR)
- 5012: EDGNet API (세그멘테이션)

**CentOS/RHEL firewalld**: CentOS/RHEL 방화벽에서 동일한 포트들을 영구적으로 허용하고, 설정을 즉시 적용합니다.

---

## 📦 설치 절차

### 1. 시스템 파일 압축 해제

**설치 디렉토리 생성**: 시스템 설치를 위한 표준 디렉토리(`/opt/ax-drawing-analysis`)를 생성합니다.

**압축 파일 해제**: 납품받은 tar.gz 압축 파일을 지정된 디렉토리에 압축 해제합니다. 파일 경로는 실제 납품 파일 위치에 따라 조정이 필요합니다.

**권한 설정**: 압축 해제된 모든 파일과 디렉토리에 대해 현재 사용자의 소유권을 설정합니다. 이는 향후 파일 수정 및 관리를 용이하게 합니다.

### 2. 디렉토리 구조 확인

설치된 시스템은 다음과 같은 구조로 구성됩니다:

- `docker-compose.yml`: 모든 서비스의 컨테이너 설정을 정의하는 Docker Compose 파일
- `.env.example`: 환경변수 설정 템플릿
- `web-ui/`: React 기반 웹 사용자 인터페이스 소스 코드
- `services/`: 각 AI 모델 서비스별 디렉토리 (gateway-api, yolo-api, edocr2-api 등)
- `models/`: 학습된 AI 모델 가중치 파일 저장소
- `data/`: 사용자 업로드 파일 및 분석 결과 저장소
- `logs/`: 각 서비스별 로그 파일 저장소
- `docs/`: 시스템 관련 문서 모음

### 3. 환경 설정 파일 생성

**환경 변수 파일 복사**: 템플릿 파일(`.env.example`)을 실제 설정 파일(`.env`)로 복사합니다.

**설정 파일 편집**: 텍스트 에디터(`vi`, `nano` 등)로 `.env` 파일을 열어 시스템 환경에 맞게 수정합니다.

#### .env 파일 주요 설정 항목

**기본 설정**:
- `COMPOSE_PROJECT_NAME`: Docker Compose 프로젝트 이름 (기본값: ax-drawing-analysis)
- `NODE_ENV`: 실행 환경 (production/development)

**포트 설정**: 각 서비스가 사용할 포트 번호를 지정합니다. 기본값은 5173(웹UI), 8000(Gateway), 5005(YOLO), 5001(eDOCr2), 5012(EDGNet), 5006(PaddleOCR), 5003(SkinModel)입니다.

**GPU 설정**: `USE_GPU`를 true로 설정하면 GPU를 사용하고, false로 설정하면 CPU만 사용합니다.

**메모리 제한**: 각 서비스별 메모리 사용 상한선을 설정합니다. GPU 메모리는 별도로 지정할 수 있으며, 시스템 리소스에 따라 조정이 필요합니다.

**로그 레벨**: 로그 상세도를 조정합니다 (debug, info, warn, error 중 선택).

---

## 🚀 초기 설정

### 1. 모델 파일 배치

`models/` 디렉토리에 필요한 AI 모델 가중치 파일들이 올바르게 배치되어 있는지 확인합니다. 필수 파일은 `yolo11_best.pt` (YOLO 모델), `edocr2_v2.pth` (OCR 모델), `edgnet_weights.pth` (세그멘테이션 모델)입니다. `ls -lh models/` 명령어로 파일 목록과 크기를 확인할 수 있습니다.

### 2. 도커 이미지 빌드

설치 디렉토리로 이동한 후, `docker compose build` 명령어로 모든 서비스의 Docker 이미지를 빌드합니다. 이 과정은 최초 1회만 수행하면 되며, 시스템 사양에 따라 약 10~20분이 소요됩니다.

빌드 완료 후 `docker images | grep ax-drawing` 명령어로 생성된 이미지 목록을 확인할 수 있습니다.

---

## ▶️ 서비스 시작/중지

### 전체 서비스 시작

설치 디렉토리에서 `docker compose up -d` 명령어를 실행하여 모든 서비스를 백그라운드 모드로 시작합니다. `-d` 옵션은 detached 모드를 의미하며, 터미널을 종료해도 서비스가 계속 실행됩니다.

실시간 로그를 확인하려면 `docker compose logs -f` 명령어를 사용합니다. 특정 서비스의 로그만 보려면 서비스 이름을 추가합니다 (예: `docker compose logs -f web-ui`).

### 서비스 상태 확인

`docker compose ps` 명령어로 현재 실행 중인 컨테이너의 상태를 확인할 수 있습니다. 각 컨테이너의 이름, 상태, 사용 포트가 표시됩니다.

헬스체크는 웹 브라우저나 `curl` 명령어로 각 서비스의 `/health` 엔드포인트에 접속하여 확인합니다. 정상적인 경우 JSON 형식의 상태 정보가 반환됩니다.

### 서비스 중지

`docker compose down` 명령어는 모든 서비스를 중지하고 컨테이너를 제거합니다. 데이터는 보존됩니다.

`docker compose stop` 명령어는 컨테이너를 중지만 하고 제거하지 않습니다. 빠른 재시작이 필요할 때 유용합니다.

특정 서비스만 재시작하려면 `docker compose restart <서비스명>` 명령어를 사용합니다.

### 서비스 재시작

전체 재시작은 `docker compose restart` 명령어로 수행합니다.

설정 파일(`.env` 또는 `docker-compose.yml`)을 변경한 경우에는 먼저 `docker compose down`으로 완전히 중지한 후 `docker compose up -d`로 다시 시작해야 변경사항이 반영됩니다.

---

## 🔧 포트 설정 변경

### 방법 1: .env 파일 수정 (권장)

`.env` 파일을 편집기로 열어 원하는 포트 번호로 변경합니다. 예를 들어 웹 UI 포트를 5173에서 8080으로 변경하려면 `WEB_UI_PORT=8080`으로 수정합니다.

변경 후에는 서비스를 완전히 중지했다가 다시 시작해야 합니다.

### 방법 2: docker-compose.yml 직접 수정

`docker-compose.yml` 파일에서 각 서비스의 `ports` 섹션을 직접 수정할 수 있습니다. 포트 매핑 형식은 "호스트포트:컨테이너포트"입니다. 예를 들어 "8080:5173"은 호스트의 8080포트를 컨테이너의 5173포트로 연결합니다.

---

## 🎮 GPU 설정

### GPU 사용 활성화

`.env` 파일에서 `USE_GPU=true`로 설정하면 GPU 가속이 활성화됩니다. 각 서비스별 GPU 메모리 할당량도 조정할 수 있습니다 (예: `YOLO_GPU_MEMORY=4g`).

### GPU 사용 확인

특정 컨테이너에서 `nvidia-smi` 명령어를 실행하여 GPU가 정상적으로 인식되는지 확인합니다. `docker exec -it yolo-api nvidia-smi` 형식으로 사용합니다.

GPU 사용률을 실시간으로 모니터링하려면 호스트에서 `watch -n 1 nvidia-smi` 명령어를 실행합니다. 1초마다 GPU 상태가 갱신되어 표시됩니다.

### CPU 전용 모드로 변경

GPU를 사용하지 않으려면 `.env` 파일에서 `USE_GPU=false`로 변경하고 서비스를 재시작합니다. 처리 속도는 느려지지만 GPU가 없는 환경에서도 동작합니다.

---

## 💾 백업 및 복원

### 설정 백업

백업 디렉토리를 생성하고 현재 날짜를 폴더명에 포함시킵니다. `.env` 설정 파일과 `data/` 디렉토리를 백업 위치로 복사합니다.

웹 UI의 브라우저 설정은 브라우저의 localStorage에 저장되므로, Settings 페이지에서 "백업" 버튼을 클릭하여 JSON 파일로 다운로드할 수 있습니다.

### 데이터베이스 백업 (향후 DB 추가 시)

PostgreSQL 데이터베이스를 사용하게 되는 경우, `pg_dump` 명령어를 통해 데이터베이스 전체를 SQL 파일로 덤프할 수 있습니다. 컨테이너 내부에서 명령어를 실행하고 결과를 호스트 파일 시스템에 저장합니다.

### 복원

백업된 설정 파일과 데이터를 원래 위치로 복사한 후, 서비스를 완전히 재시작하여 복원을 완료합니다.

---

## 🔄 업그레이드

### 마이너 버전 업그레이드 (1.0.0 → 1.1.0)

**1단계**: 백업 스크립트를 실행하여 현재 설정을 안전하게 보존합니다.

**2단계**: 모든 서비스를 중지합니다.

**3단계**: 새 버전의 압축 파일을 압축 해제합니다.

**4단계**: `diff` 명령어로 새 버전의 `.env.example`과 현재 `.env` 파일을 비교하여 새로 추가된 설정 항목을 확인하고 병합합니다.

**5단계**: 변경된 코드를 반영하기 위해 Docker 이미지를 재빌드합니다.

**6단계**: 서비스를 시작합니다.

**7단계**: 헬스체크 엔드포인트에서 버전 정보를 확인하여 업그레이드가 정상적으로 완료되었는지 검증합니다.

### 메이저 버전 업그레이드 (1.x → 2.x)

메이저 버전 업그레이드는 구조적 변경이 포함될 수 있으므로 별도의 업그레이드 가이드 문서(`docs/UPGRADE_GUIDE.md`)를 참조해야 합니다.

---

## 🔍 문제 해결

### 1. 서비스가 시작되지 않을 때

먼저 `docker compose logs` 명령어로 전체 로그를 확인합니다. 특정 서비스에 문제가 있는 경우 `docker compose logs --tail=100 <서비스명>` 명령어로 최근 100줄의 로그를 상세히 확인합니다.

컨테이너 상태는 `docker compose ps`로 확인하고, 더 자세한 정보가 필요한 경우 `docker inspect <컨테이너명>` 명령어를 사용합니다.

### 2. 포트 충돌

특정 포트를 이미 다른 프로세스가 사용 중인 경우 발생합니다. `lsof` 또는 `netstat` 명령어로 해당 포트를 사용하는 프로세스를 찾아 종료하거나, `.env` 파일에서 다른 포트로 변경합니다.

### 3. GPU 인식 안 됨

호스트에서 `nvidia-smi` 명령어가 정상적으로 작동하는지 먼저 확인합니다. Docker에서 GPU를 사용할 수 있는지는 NVIDIA CUDA 공식 이미지를 실행하여 테스트합니다.

문제가 계속되면 `nvidia-container-toolkit`을 재설치하고 Docker 서비스를 재시작합니다.

### 4. 메모리 부족

`docker stats` 명령어로 각 컨테이너의 실시간 메모리 사용량을 확인합니다. 메모리 부족이 확인되면 `.env` 파일에서 각 서비스의 메모리 제한을 줄입니다. 예를 들어 `YOLO_MEMORY`를 4g에서 2g로 감소시킵니다.

### 5. 웹 UI 접속 불가

웹 서버 컨테이너의 로그를 확인합니다. 방화벽 설정이 올바른지 확인하고, `curl`로 로컬에서 접속을 테스트해봅니다. 브라우저 캐시를 삭제한 후 다시 시도합니다.

### 6. API 응답 느림

`nvidia-smi`로 GPU 사용률을 확인하고, `top` 명령어로 CPU 사용률을 확인합니다. 네트워크 대역폭은 `iftop`으로 모니터링할 수 있습니다. 로그가 너무 많이 생성되어 느려지는 경우 `.env`에서 `LOG_LEVEL`을 info에서 warn으로 변경합니다.

---

## 📚 참고 문서

- [API 문서](./API_REFERENCE.md)
- [트러블슈팅 가이드](./TROUBLESHOOTING.md)
- [성능 튜닝 가이드](./PERFORMANCE_TUNING.md)
- [보안 가이드](./SECURITY_GUIDE.md)

---

**AX 도면 분석 시스템 v1.0.0**
© 2025 All Rights Reserved
