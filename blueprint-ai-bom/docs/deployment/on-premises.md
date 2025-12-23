# Blueprint AI BOM - On-Premises Deployment

온프레미스 환경에 Blueprint AI BOM을 배포하기 위한 가이드입니다.

## 시스템 요구사항

| 항목 | 최소 | 권장 |
|------|------|------|
| CPU | 4 cores | 8 cores |
| RAM | 8GB | 16GB |
| Storage | 20GB | 50GB |
| Docker | 20.10+ | Latest |
| Docker Compose | 2.0+ | Latest |

## 빠른 시작

```bash
# 1. 저장소 클론
git clone <repository-url>
cd blueprint-ai-bom

# 2. 배포 스크립트 실행
./scripts/deploy_onprem.sh start

# 3. 접속
# Frontend: http://localhost:3000
# Backend API: http://localhost:5020
```

## 상세 배포

### 1. 환경 변수 설정 (선택)

```bash
# 포트 변경
export BACKEND_PORT=5020
export FRONTEND_PORT=3000

# 외부 API 연동 (선택)
export YOLO_API_URL=http://yolo-api:5005
export EDOCR2_API_URL=http://edocr2-api:5002
```

### 2. Docker Compose로 배포

```bash
# 빌드 및 시작
docker-compose -f docker-compose.onprem.yml up -d --build

# 로그 확인
docker-compose -f docker-compose.onprem.yml logs -f

# 중지
docker-compose -f docker-compose.onprem.yml down
```

### 3. 상태 확인

```bash
# 컨테이너 상태
docker-compose -f docker-compose.onprem.yml ps

# Health check
curl http://localhost:5020/health
```

## 디렉토리 구조

```
blueprint-ai-bom/
├── uploads/           # 업로드된 이미지 저장
├── results/           # 분석 결과 저장
├── config/            # 설정 파일
├── test_drawings/     # 테스트 도면 (읽기 전용)
├── class_examples/    # 클래스 예시 이미지 (읽기 전용)
└── models/            # YOLO 모델 파일 (읽기 전용)
```

## 볼륨 마운트

| 호스트 경로 | 컨테이너 경로 | 설명 |
|-------------|---------------|------|
| `./uploads` | `/app/uploads` | 업로드 이미지 |
| `./results` | `/app/results` | 분석 결과 |
| `./config` | `/app/config` | 설정 파일 |
| `./models` | `/app/models` | YOLO 모델 (ro) |
| `./test_drawings` | `/app/test_drawings` | 테스트 도면 (ro) |
| `./class_examples` | `/app/class_examples` | 클래스 예시 (ro) |

## 네트워크

온프레미스 배포는 `blueprint-network` 내부 네트워크를 사용합니다.

| 서비스 | 컨테이너명 | 내부 포트 |
|--------|------------|-----------|
| Backend | blueprint-ai-bom-backend | 5020 |
| Frontend | blueprint-ai-bom-frontend | 80 |

## 문제 해결

### 컨테이너가 시작되지 않음

```bash
# 로그 확인
docker logs blueprint-ai-bom-backend

# 이미지 재빌드
docker-compose -f docker-compose.onprem.yml build --no-cache
```

### 포트 충돌

```bash
# 다른 포트 사용
BACKEND_PORT=5021 FRONTEND_PORT=3001 ./scripts/deploy_onprem.sh start
```

### Health check 실패

```bash
# Backend health 확인
curl -v http://localhost:5020/health

# 컨테이너 재시작
docker-compose -f docker-compose.onprem.yml restart blueprint-ai-bom-backend
```

## 업데이트

```bash
# 최신 코드 가져오기
git pull

# 컨테이너 재빌드
./scripts/deploy_onprem.sh restart
```

## 백업

```bash
# 데이터 백업
tar -czvf backup-$(date +%Y%m%d).tar.gz uploads results config

# 복원
tar -xzvf backup-YYYYMMDD.tar.gz
```
