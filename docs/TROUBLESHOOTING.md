# AX 도면 분석 시스템 - 트러블슈팅 가이드

> 온프레미스 환경 문제 해결 매뉴얼
> 버전: 1.0.0
> 작성일: 2025-11-13

---

## 📋 목차

1. [시스템 시작 문제](#시스템-시작-문제)
2. [성능 문제](#성능-문제)
3. [GPU 관련 문제](#gpu-관련-문제)
4. [네트워크 문제](#네트워크-문제)
5. [메모리 문제](#메모리-문제)
6. [데이터 손실 문제](#데이터-손실-문제)
7. [로그 수집 방법](#로그-수집-방법)
8. [FAQ](#faq)

---

## 🚨 시스템 시작 문제

### 문제 1: `docker compose up` 실패

#### 증상
```bash
$ docker compose up -d
Error response from daemon: driver failed programming external connectivity
```

#### 원인
- 포트가 이미 사용 중

#### 해결 방법

```bash
# 1. 포트 사용 중인 프로세스 확인
sudo lsof -i :8000
sudo lsof -i :5173

# 2. 프로세스 종료
sudo kill -9 <PID>

# 3. 또는 .env에서 포트 변경
vi .env
# WEB_UI_PORT=5174  # 변경

# 4. 재시작
docker compose down
docker compose up -d
```

---

### 문제 2: 컨테이너가 계속 재시작됨

#### 증상
```bash
$ docker compose ps
NAME                STATUS
gateway-api         Restarting (1) 5 seconds ago
```

#### 원인
- 메모리 부족
- 환경 변수 설정 오류
- 모델 파일 누락

#### 해결 방법

```bash
# 1. 로그 확인
docker compose logs gateway-api

# 2. 메모리 부족 시
# .env 파일에서 메모리 제한 증가
GATEWAY_MEMORY=4g  # 2g → 4g

# 3. 모델 파일 확인
ls -lh models/
# yolo11_best.pt (필수)
# edocr2_v2.pth (필수)
# edgnet_weights.pth (필수)

# 4. 환경 변수 확인
docker compose config | grep -A 10 environment
```

---

### 문제 3: "Cannot connect to Docker daemon" 오류

#### 증상
```bash
Cannot connect to the Docker daemon at unix:///var/run/docker.sock
```

#### 원인
- Docker 서비스 미실행
- 권한 문제

#### 해결 방법

```bash
# 1. Docker 서비스 상태 확인
sudo systemctl status docker

# 2. Docker 시작
sudo systemctl start docker

# 3. 자동 시작 설정
sudo systemctl enable docker

# 4. 사용자를 docker 그룹에 추가 (권한 문제 시)
sudo usermod -aG docker $USER
newgrp docker

# 5. 확인
docker ps
```

---

## ⚡ 성능 문제

### 문제 4: API 응답 시간 느림 (>10초)

#### 증상
- YOLO 추론 시간 >5초
- eDOCr2 OCR 시간 >10초

#### 원인
- CPU 모드 사용 (GPU 미활성화)
- GPU 메모리 부족
- 입력 이미지 크기 과다

#### 해결 방법

```bash
# 1. GPU 사용 확인
docker exec yolo-api nvidia-smi

# 2. GPU 미인식 시 .env 확인
vi .env
USE_GPU=true  # 설정 확인

# 3. GPU 메모리 부족 시
# .env에서 메모리 증가
YOLO_GPU_MEMORY=6g  # 4g → 6g

# 4. 이미지 크기 조정
# Settings 페이지에서:
# YOLO imgsz: 1920 → 1280 (성능 우선)
# 또는 640 (빠른 처리)

# 5. 서비스 재시작
docker compose restart yolo-api
```

---

### 문제 5: 웹 UI 로딩 느림

#### 증상
- 초기 페이지 로드 >10초

#### 원인
- 번들 파일 크기 과다
- 네트워크 대역폭 부족

#### 해결 방법

```bash
# 1. 브라우저 캐시 확인
# F12 → Network → Disable cache 해제

# 2. 프로덕션 빌드 확인
docker compose exec web-ui sh
ls -lh dist/

# 3. nginx gzip 압축 활성화 (web-ui/nginx.conf)
# 이미 활성화되어 있어야 함

# 4. 로컬 네트워크 확인
ping <서버IP>
iperf3 -c <서버IP>
```

---

## 🎮 GPU 관련 문제

### 문제 6: GPU 인식 안 됨

#### 증상
```bash
$ docker exec yolo-api nvidia-smi
OCI runtime exec failed: exec failed: unable to find user : no matching entries in passwd file
```

#### 원인
- NVIDIA Docker Runtime 미설치
- NVIDIA Driver 미설치 또는 버전 불일치

#### 해결 방법

```bash
# 1. 호스트에서 GPU 확인
nvidia-smi

# 2. NVIDIA Driver 미설치 시
sudo apt-get install nvidia-driver-535
sudo reboot

# 3. nvidia-container-toolkit 설치
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# 4. Docker 재시작
sudo systemctl restart docker

# 5. 테스트
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# 6. AX 시스템 재시작
docker compose down
docker compose up -d
```

---

### 문제 7: CUDA Out of Memory 오류

#### 증상
```bash
RuntimeError: CUDA out of memory. Tried to allocate 2.00 GiB
```

#### 원인
- GPU 메모리 부족
- 다중 모델 동시 실행

#### 해결 방법

```bash
# 1. GPU 메모리 사용량 확인
nvidia-smi

# 2. 사용하지 않는 서비스 비활성화
# Settings 페이지에서:
# - EDGNet: 활성화 OFF (segmentation 불필요 시)
# - PaddleOCR: 활성화 OFF (중국어/일본어 불필요 시)

# 3. 배치 크기 감소 (코드 수정 필요)
# 또는 입력 이미지 크기 감소
# YOLO imgsz: 1280 → 640

# 4. GPU 메모리 할당량 조정
vi .env
YOLO_GPU_MEMORY=3g  # 4g → 3g
EDOCR2_GPU_MEMORY=4g  # 6g → 4g
EDGNET_GPU_MEMORY=3g  # 4g → 3g

# 5. 재시작
docker compose down
docker compose up -d
```

---

## 🌐 네트워크 문제

### 문제 8: 외부에서 웹 UI 접속 안 됨

#### 증상
- 로컬(localhost)에서는 접속 가능
- 다른 PC에서 접속 불가

#### 원인
- 방화벽 차단
- 0.0.0.0 바인딩 미설정

#### 해결 방법

```bash
# 1. 방화벽 상태 확인
sudo ufw status
sudo firewall-cmd --list-all

# 2. 포트 열기 (Ubuntu)
sudo ufw allow 5173/tcp
sudo ufw allow 8000/tcp

# 3. 포트 열기 (CentOS/RHEL)
sudo firewall-cmd --permanent --add-port=5173/tcp
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload

# 4. docker-compose.yml 확인
# ports:
#   - "5173:5173"  # 모든 인터페이스
#   - "127.0.0.1:5173:5173"  # 로컬만 (X)

# 5. 네트워크 연결 테스트
telnet <서버IP> 5173
curl http://<서버IP>:5173
```

---

### 문제 9: API 간 통신 실패

#### 증상
```bash
Gateway API → YOLO API: Connection refused
```

#### 원인
- 컨테이너 네트워크 문제
- 서비스 시작 순서

#### 해결 방법

```bash
# 1. 컨테이너 네트워크 확인
docker network ls
docker network inspect ax-drawing-analysis_default

# 2. 컨테이너 간 ping 테스트
docker exec gateway-api ping yolo-api

# 3. DNS 해석 확인
docker exec gateway-api nslookup yolo-api

# 4. 재시작 (의존성 순서대로)
docker compose down
docker compose up -d

# 5. 헬스체크
curl http://localhost:8000/health
curl http://localhost:5005/health
```

---

## 💾 메모리 문제

### 문제 10: "Cannot allocate memory" 오류

#### 증상
```bash
Cannot allocate memory: fork failed
```

#### 원인
- 시스템 메모리 부족
- Docker 메모리 제한 초과

#### 해결 방법

```bash
# 1. 시스템 메모리 확인
free -h
top

# 2. Docker 메모리 사용량 확인
docker stats

# 3. 불필요한 컨테이너 제거
docker container prune
docker image prune -a

# 4. 메모리 제한 조정
vi .env
# 전체 메모리 사용량을 시스템 RAM의 80% 이하로
YOLO_MEMORY=2g  # 4g → 2g
EDOCR2_MEMORY=2g  # 4g → 2g

# 5. 스왑 메모리 설정 (임시 조치)
sudo dd if=/dev/zero of=/swapfile bs=1G count=8
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 📊 데이터 손실 문제

### 문제 11: 설정이 초기화됨

#### 증상
- Settings 페이지에서 저장한 설정이 사라짐

#### 원인
- 브라우저 localStorage 삭제
- 브라우저 시크릿 모드 사용

#### 해결 방법

```bash
# 1. 백업 파일 확인
# Settings 페이지에서 "복원" 버튼 클릭
# 이전에 백업한 JSON 파일 선택

# 2. 브라우저 데이터 보존 설정
# Chrome: Settings → Privacy → Site Settings → Cookies
# "Clear cookies and site data when you quit Chrome" OFF

# 3. 정기 백업 설정
# Settings 페이지에서 "백업" 버튼으로 주기적으로 저장

# 4. 시스템 레벨 백업 (선택)
# /var/lib/docker/volumes/ 에서 localStorage 볼륨 백업
```

---

### 문제 12: 업로드한 파일이 사라짐

#### 증상
- 분석한 도면 이미지가 재시작 후 사라짐

#### 원인
- 컨테이너 볼륨 미설정

#### 해결 방법

```bash
# 1. docker-compose.yml에서 볼륨 확인
# volumes:
#   - ./data:/app/data  # 영구 저장

# 2. 데이터 백업
cp -r data/ /opt/ax-backups/data_$(date +%Y%m%d)/

# 3. 볼륨 복원
docker compose down
cp -r /opt/ax-backups/data_20251113/ ./data/
docker compose up -d
```

---

## 📝 로그 수집 방법

### 전체 로그 수집

```bash
#!/bin/bash
# collect_logs.sh

BACKUP_DIR="/tmp/ax-logs-$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# Docker 로그
docker compose logs --no-color > $BACKUP_DIR/docker-compose.log
docker compose logs --no-color gateway-api > $BACKUP_DIR/gateway-api.log
docker compose logs --no-color yolo-api > $BACKUP_DIR/yolo-api.log
docker compose logs --no-color edocr2-api > $BACKUP_DIR/edocr2-api.log
docker compose logs --no-color edgnet-api > $BACKUP_DIR/edgnet-api.log
docker compose logs --no-color paddleocr-api > $BACKUP_DIR/paddleocr-api.log
docker compose logs --no-color skinmodel-api > $BACKUP_DIR/skinmodel-api.log
docker compose logs --no-color web-ui > $BACKUP_DIR/web-ui.log

# 시스템 정보
docker compose ps > $BACKUP_DIR/containers_status.txt
docker stats --no-stream > $BACKUP_DIR/containers_stats.txt
df -h > $BACKUP_DIR/disk_usage.txt
free -h > $BACKUP_DIR/memory_usage.txt
nvidia-smi > $BACKUP_DIR/gpu_status.txt 2>/dev/null || echo "No GPU" > $BACKUP_DIR/gpu_status.txt

# 환경 설정
cp .env $BACKUP_DIR/
cp docker-compose.yml $BACKUP_DIR/

# 압축
tar -czf $BACKUP_DIR.tar.gz -C /tmp $(basename $BACKUP_DIR)
echo "로그 수집 완료: $BACKUP_DIR.tar.gz"
```

실행:
```bash
chmod +x collect_logs.sh
./collect_logs.sh
```

---

## ❓ FAQ

### Q1: 설정 저장 시 20초 이상 걸리는데 정상인가요?

**A**: 예, 정상입니다. 설정 저장 시:
1. localStorage에 저장 (즉시)
2. Docker 컨테이너 재시작 필요 (수동)

설정 저장 자체는 1초 미만이지만, 실제 적용을 위해서는 컨테이너 재시작이 필요합니다.
```bash
docker compose restart
```

---

### Q2: GPU가 2개인데 특정 GPU만 사용하려면?

**A**: docker-compose.yml에서 GPU 지정:
```yaml
services:
  yolo-api:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ['0']  # GPU 0번만 사용
              capabilities: [gpu]
```

---

### Q3: 여러 사용자가 동시에 사용 가능한가요?

**A**: 가능합니다. 단, Settings 페이지는 사용자별로 독립적입니다 (브라우저 localStorage 사용). API는 다중 사용자 동시 요청 지원합니다.

---

### Q4: 오프라인(폐쇄망) 환경에서 사용 가능한가요?

**A**: 네, 가능합니다. 사전 준비사항:
1. Docker 이미지 사전 빌드
2. 모델 가중치 파일 사전 배포
3. 외부 의존성 없음

---

### Q5: 백업 주기는 어떻게 하나요?

**A**: 권장 백업 주기:
- 설정 파일(.env): 변경 시마다
- 데이터 디렉토리: 주 1회
- 로그 파일: 월 1회 (선택)

자동 백업 스크립트:
```bash
# /etc/cron.weekly/ax-backup.sh
#!/bin/bash
BACKUP_DIR=/opt/ax-backups/$(date +%Y%m%d)
mkdir -p $BACKUP_DIR
cp /opt/ax-drawing-analysis/.env $BACKUP_DIR/
cp -r /opt/ax-drawing-analysis/data/ $BACKUP_DIR/
tar -czf $BACKUP_DIR.tar.gz -C /opt/ax-backups $(basename $BACKUP_DIR)
rm -rf $BACKUP_DIR
```

---

## 📞 추가 지원

위의 해결 방법으로 문제가 해결되지 않을 경우:

1. **로그 수집**: `collect_logs.sh` 실행
2. **지원 요청**: support@example.com으로 로그 파일 전송
3. **긴급 지원**: 010-1234-5678 (24/7)

---

**문제 해결 시 체크리스트**

- [ ] 로그 확인 완료
- [ ] 시스템 리소스 확인 (CPU, RAM, GPU)
- [ ] 네트워크 연결 확인
- [ ] 방화벽 설정 확인
- [ ] 환경 설정 파일(.env) 확인
- [ ] Docker 서비스 정상 작동
- [ ] 백업 파일 확보

---

**AX 도면 분석 시스템 v1.0.0**
© 2025 All Rights Reserved
