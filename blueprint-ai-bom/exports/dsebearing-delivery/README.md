# Blueprint AI BOM - 동서기연 터빈 베어링 납품 패키지

## 개요

동서기연 터빈 베어링 프로젝트의 도면 분석 결과를 조회할 수 있는 시스템입니다.

| 항목 | 내용 |
|------|------|
| 프로젝트 | 동서기연 터빈 베어링 |
| 분석 세션 | 53개 도면 |
| BOM 아이템 | 326개 |
| 총 견적가 | ₩100,679,708 |

## 시스템 요구사항

| 항목 | 최소 사양 |
|------|----------|
| Docker | Docker Desktop 4.0+ 또는 Docker Engine 20.10+ |
| RAM | 8GB 이상 |
| 디스크 | 10GB 이상 여유 공간 |
| OS | Windows 10/11, macOS 12+, Ubuntu 20.04+ |

## 패키지 구성

```
dsebearing-delivery/
├── images/
│   ├── blueprint-ai-bom-backend.tar.gz    (백엔드 이미지, ~4.4GB)
│   └── blueprint-ai-bom-frontend.tar.gz   (프론트엔드 이미지, ~24MB)
├── data/
│   └── project_dsebearing.json            (프로젝트 데이터)
├── docker-compose.yml                      (서비스 구성)
├── setup.sh                                (Linux/macOS 설치)
├── setup.ps1                               (Windows 설치)
└── README.md                               (이 문서)
```

## 설치 방법

### Linux / macOS

```bash
chmod +x setup.sh
./setup.sh
```

### Windows (PowerShell)

```powershell
.\setup.ps1
```

설치 스크립트가 자동으로 다음을 수행합니다:
1. Docker 이미지 로드
2. 서비스 시작
3. 프로젝트 데이터 Import
4. 결과 검증

## 접속

| 서비스 | URL |
|--------|-----|
| 웹 UI | http://localhost:3000 |
| API 서버 | http://localhost:5020 |
| API 문서 | http://localhost:5020/docs |

## 사용 방법

1. 브라우저에서 http://localhost:3000 접속
2. 프로젝트 목록에서 **동서기연 터빈 베어링** 선택
3. 세션 목록에서 개별 도면 분석 결과 확인
4. BOM 탭에서 326개 부품 목록 조회
5. 견적 탭에서 총 견적가 확인

## 서비스 관리

```bash
# 서비스 시작
docker compose up -d

# 서비스 중지
docker compose down

# 로그 확인
docker logs blueprint-ai-bom-backend -f
docker logs blueprint-ai-bom-frontend -f

# 상태 확인
docker compose ps
```

## 트러블슈팅

### Docker가 설치되어 있지 않은 경우

- Windows/macOS: [Docker Desktop](https://www.docker.com/products/docker-desktop/) 설치
- Linux: `curl -fsSL https://get.docker.com | sh`

### 포트 충돌

다른 서비스가 5020 또는 3000 포트를 사용 중인 경우, `docker-compose.yml`에서 포트를 변경하세요:

```yaml
ports:
  - "5021:5020"  # 백엔드: 5021로 변경
  - "3001:80"    # 프론트엔드: 3001로 변경
```

### 이미지 로드 실패

```bash
# 수동 이미지 로드
docker load < images/blueprint-ai-bom-backend.tar.gz
docker load < images/blueprint-ai-bom-frontend.tar.gz

# 이미지 확인
docker images | grep blueprint-ai-bom
```

### 백엔드가 시작되지 않는 경우

```bash
# 로그 확인
docker logs blueprint-ai-bom-backend

# 메모리 확인 (최소 8GB 필요)
docker info | grep "Total Memory"
```

### 프로젝트 수동 Import

```bash
curl -X POST http://localhost:5020/projects/import \
  -F "file=@data/project_dsebearing.json"
```

## 기술 지원

문제 발생 시 아래 정보와 함께 문의하세요:

```bash
# 시스템 정보 수집
docker version
docker compose version
docker compose ps
docker logs blueprint-ai-bom-backend --tail 50
```
