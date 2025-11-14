# AI Drawing Analysis System - 관리자 매뉴얼

## 목차

1. [시스템 개요](#1-시스템-개요)
2. [접속 및 인증](#2-접속-및-인증)
3. [대시보드 사용법](#3-대시보드-사용법)
4. [모델 관리](#4-모델-관리)
5. [API 서비스 관리](#5-api-서비스-관리)
6. [Docker 컨테이너 관리](#6-docker-컨테이너-관리)
7. [시스템 모니터링](#7-시스템-모니터링)
8. [로그 관리](#8-로그-관리)
9. [백업 및 복구](#9-백업-및-복구)
10. [보안 관리](#10-보안-관리)
11. [문제 해결](#11-문제-해결)
12. [FAQ](#12-faq)

---

## 1. 시스템 개요

### 1.1 시스템 구성

AI Drawing Analysis System은 엔지니어링 도면에서 치수 정보를 자동으로 추출하는 AI 기반 시스템입니다.

**주요 구성 요소:**

- **Web UI**: 사용자 인터페이스 (포트: 5173)
- **Admin Dashboard**: 관리자 대시보드 (포트: 8007)
- **API Gateway**: API 요청 라우팅 (포트: 8000)
- **AI 모델 서비스**:
  - eDOCr2: 도면 OCR (포트: 8001)
  - YOLO: 객체 탐지 (포트: 8002)
  - EDGNet: 그래프 네트워크 (포트: 8003)
  - Skin Model: 치수 예측 (포트: 8004)
  - VL: 비전-언어 모델 (포트: 8005)
  - PaddleOCR: OCR 보조 (포트: 8006)

### 1.2 시스템 아키텍처

```
사용자
  ↓
Web UI (5173)
  ↓
API Gateway (8000)
  ↓
┌─────────┬─────────┬─────────┬──────────┬─────┬───────────┐
eDOCr2   YOLO     EDGNet  SkinModel   VL   PaddleOCR
(8001)   (8002)   (8003)    (8004)   (8005)  (8006)
```

---

## 2. 접속 및 인증

### 2.1 최초 접속

1. 웹 브라우저를 열고 다음 주소로 접속:
   ```
   http://localhost:5173
   ```

2. 관리자 페이지 접속:
   ```
   http://localhost:5173/admin
   ```

### 2.2 기본 계정 정보

**⚠️ 보안 경고**: 최초 설치 후 반드시 비밀번호를 변경하세요!

```
Username: admin
Password: changeme123
```

### 2.3 비밀번호 변경

1. Admin Dashboard 접속
2. 상단 메뉴에서 "사용자 관리" 클릭
3. "admin" 계정 선택
4. "비밀번호 변경" 버튼 클릭
5. 새 비밀번호 입력 및 확인

**비밀번호 요구사항:**
- 최소 8자 이상
- 영문 대/소문자, 숫자, 특수문자 조합 권장

---

## 3. 대시보드 사용법

### 3.1 메인 대시보드

Admin Dashboard는 4개의 주요 탭으로 구성됩니다:

#### ① Status (상태 확인)
- 모든 서비스 상태 실시간 확인
- GPU 메모리 사용량
- 시스템 리소스 모니터링

#### ② Models (모델 관리)
- AI 모델 정보 조회
- 모델 버전 확인
- 학습 메타데이터 확인

#### ③ Training (학습 관리)
- 모델 재학습 시작
- 학습 진행 상황 확인
- 학습 로그 확인

#### ④ Logs (로그 관리)
- 서비스별 로그 조회
- 실시간 로그 스트리밍
- 로그 다운로드

### 3.2 대시보드 탐색

**상단 네비게이션:**
- 홈: 메인 대시보드로 이동
- 모니터링: Grafana 대시보드 링크
- 사용자: 계정 설정 및 로그아웃

**사이드바 메뉴:**
- 서비스 선택: 각 API 서비스 개별 관리
- Docker 관리: 컨테이너 제어
- 시스템 설정: 전역 설정 변경

---

## 4. 모델 관리

### 4.1 모델 상태 확인

1. Admin Dashboard → "Models" 탭
2. 각 모델의 정보 확인:
   - 모델 파일 크기
   - 학습 날짜
   - 정확도 메트릭
   - 파라미터 수

### 4.2 모델 재학습

#### 4.2.1 EDGNet Large 학습

**요구사항:**
- GPU 메모리: 6GB 이상
- 학습 시간: 약 2-3시간
- 데이터셋: `/home/uproot/ax/poc/edgnet_dataset_large`

**실행 방법:**

1. Training 탭 → "EDGNet Large" 선택
2. 학습 파라미터 설정:
   - Epochs: 100 (기본값)
   - Batch Size: 8 (기본값)
3. "학습 시작" 버튼 클릭
4. 진행 상황 모니터링:
   - Progress Bar: 전체 진행률
   - Current Epoch: 현재 에폭
   - Logs: 실시간 학습 로그

#### 4.2.2 YOLO Custom 학습

**요구사항:**
- GPU 메모리: 4GB 이상
- 학습 시간: 약 1-2시간
- 데이터셋: `/home/uproot/ax/poc/datasets/real_drawings_yolo`

**실행 방법:**

1. Training 탭 → "YOLO Custom" 선택
2. "학습 시작" 버튼 클릭
3. 학습 완료 후 모델 자동 배포

#### 4.2.3 Skin Model 학습

**요구사항:**
- CPU 기반 (GPU 불필요)
- 학습 시간: 약 10-20초

**실행 방법:**

1. Training 탭 → "Skin Model (XGBoost)" 선택
2. "학습 시작" 버튼 클릭

#### 4.2.4 EDGNet Simple 학습

**요구사항:**
- GPU 메모리: 2GB 이상
- 학습 시간: 약 5분

**실행 방법:**

1. Training 탭 → "EDGNet Simple" 선택
2. "학습 시작" 버튼 클릭

### 4.3 학습 작업 관리

**진행 중인 작업 확인:**
```
Training 탭에서 실시간 확인:
- Job ID
- 모델 타입
- 상태 (pending/running/completed/failed)
- 진행률 (%)
- 현재 에폭
```

**학습 로그 확인:**
- 각 학습 작업 카드 하단에서 "Show Logs" 클릭
- 최근 10줄의 로그 확인 가능

**학습 작업 취소:**
- 현재 구현 중 (TODO)

---

## 5. API 서비스 관리

### 5.1 서비스 상태 확인

**방법 1: Admin Dashboard**

1. Status 탭
2. 각 서비스 상태 확인:
   - 🟢 초록색: 정상
   - 🔴 빨간색: 오류
   - ⚪ 회색: 중지됨

**방법 2: CLI 명령어**

```bash
# 모든 서비스 상태 확인
docker-compose ps

# 특정 서비스 상태 확인
docker-compose ps gateway
```

### 5.2 서비스 재시작

**Admin Dashboard 사용:**

1. Docker 관리 메뉴
2. 재시작할 서비스 선택
3. "Restart" 버튼 클릭

**CLI 사용:**

```bash
# 특정 서비스 재시작
docker-compose restart gateway

# 모든 서비스 재시작
docker-compose restart
```

### 5.3 API 테스트

**방법 1: Admin Dashboard Inference 탭**

1. Inference 탭 선택
2. API 서비스 선택 (eDOCr2, YOLO 등)
3. 테스트 이미지 업로드
4. "Analyze" 버튼 클릭
5. 결과 확인

**방법 2: cURL 명령어**

```bash
# Gateway를 통한 하이브리드 분석
curl -X POST http://localhost:8000/analyze/hybrid \
  -F "file=@test_drawing.png"

# eDOCr2 직접 호출
curl -X POST http://localhost:8001/analyze \
  -F "image=@test_drawing.png"
```

---

## 6. Docker 컨테이너 관리

### 6.1 컨테이너 상태 확인

```bash
# 실행 중인 컨테이너 확인
docker ps

# 모든 컨테이너 확인 (중지된 것 포함)
docker ps -a

# 특정 컨테이너 로그 확인
docker logs -f <container_name>
```

### 6.2 컨테이너 제어

**시작:**
```bash
# 모든 서비스 시작
docker-compose up -d

# 특정 서비스만 시작
docker-compose up -d gateway
```

**중지:**
```bash
# 모든 서비스 중지
docker-compose down

# 특정 서비스만 중지
docker-compose stop gateway
```

**재시작:**
```bash
# 특정 서비스 재시작
docker-compose restart gateway
```

### 6.3 리소스 사용량 확인

```bash
# 컨테이너별 리소스 사용량 (CPU, 메모리)
docker stats

# 특정 컨테이너만 확인
docker stats gateway
```

---

## 7. 시스템 모니터링

### 7.1 Prometheus 모니터링

**접속:**
```
http://localhost:9090
```

**주요 쿼리:**

```promql
# API 요청률
rate(http_requests_total[5m])

# 에러율
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# 응답 시간 (P95)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# GPU 온도
dcgm_gpu_temp

# GPU 메모리 사용률
dcgm_fb_used / dcgm_fb_total * 100
```

### 7.2 Grafana 대시보드

**접속:**
```
http://localhost:3000
```

**기본 계정:**
```
Username: admin
Password: admin
```

**대시보드 종류:**

1. **Operations Dashboard**: 운영자용
   - 서비스 상태 개요
   - 요청률 및 에러율
   - 응답 시간
   - GPU 상태
   - 학습 작업 모니터링

2. **Technical Dashboard**: 기술자용
   - 상세 성능 메트릭
   - 모델 인퍼런스 성능
   - 네트워크/디스크 I/O
   - Docker 컨테이너 통계

3. **Executive Dashboard**: 경영진용
   - 시스템 헬스 스코어
   - 일일 요청 수
   - 성공률
   - 리소스 활용도

### 7.3 헬스 체크

**자동 헬스 체크 실행:**

```bash
bash /home/uproot/ax/poc/scripts/health_check.sh
```

**출력 예시:**
```
============================================
🏥 시스템 헬스 체크
============================================

1. Docker 서비스 상태
✅ PASS: Docker 데몬 실행 중

2. Docker 컨테이너 상태
✅ PASS: web-ui (running, no health check)
✅ PASS: gateway (running, no health check)
...

📊 헬스 체크 결과
PASS: 45
WARN: 2
FAIL: 0
시스템 상태 점수: 96%
✅ 시스템이 정상적으로 작동하고 있습니다!
```

---

## 8. 로그 관리

### 8.1 로그 확인

**Admin Dashboard:**

1. Logs 탭 선택
2. 서비스 선택 (Gateway, eDOCr2, YOLO 등)
3. 로그 자동 로드 (최근 100줄)
4. 실시간 로그 스트리밍 (Auto-refresh 활성화)

**CLI 명령어:**

```bash
# 실시간 로그 확인
docker-compose logs -f gateway

# 최근 100줄만 확인
docker-compose logs --tail=100 gateway

# 모든 서비스 로그
docker-compose logs -f
```

### 8.2 로그 다운로드

**방법 1: Admin Dashboard**

1. Logs 탭
2. "Download Logs" 버튼 클릭
3. 로그 파일 저장

**방법 2: CLI**

```bash
# 로그를 파일로 저장
docker-compose logs gateway > gateway.log

# 타임스탬프 포함
docker-compose logs -t gateway > gateway_with_timestamp.log
```

### 8.3 로그 정리

```bash
# Docker 로그 정리
docker system prune -a

# 오래된 로그 파일 삭제 (30일 이상)
find /home/uproot/ax/poc/logs -mtime +30 -delete
```

---

## 9. 백업 및 복구

### 9.1 백업 생성

**전체 시스템 백업:**

```bash
# 백업 스크립트 실행
bash /home/uproot/ax/poc/scripts/backup.sh
```

**백업 내용:**
- Docker 설정 (docker-compose.yml, .env)
- 모니터링 설정 (Prometheus, Grafana)
- AI 모델 파일 (.pth, .pt, .pkl, .h5)
- 학습 메타데이터
- 로그 (최근 7일)
- 업로드 파일 (선택)

**백업 위치:**
```
/home/uproot/ax/poc/backups/backup_YYYYMMDD_HHMMSS/
```

**백업 압축:**
```bash
# 백업 후 압축 선택 시
backup_YYYYMMDD_HHMMSS.tar.gz
backup_YYYYMMDD_HHMMSS.tar.gz.sha256  # 체크섬
```

### 9.2 시스템 복구

**복구 절차:**

```bash
# 복구 스크립트 실행
bash /home/uproot/ax/poc/scripts/restore.sh /path/to/backup

# 압축된 백업 복구
bash /home/uproot/ax/poc/scripts/restore.sh /path/to/backup.tar.gz
```

**복구 단계:**
1. 체크섬 검증
2. Docker 컨테이너 중지
3. 설정 파일 복구
4. 모델 파일 복구
5. 메타데이터 복구
6. Docker 컨테이너 재시작
7. 서비스 상태 확인

### 9.3 백업 자동화

**Cron 작업 설정:**

```bash
# Cron 편집기 열기
crontab -e

# 매일 새벽 2시에 자동 백업
0 2 * * * /home/uproot/ax/poc/scripts/backup.sh >> /home/uproot/ax/poc/logs/backup.log 2>&1
```

---

## 10. 보안 관리

### 10.1 사용자 관리 (RBAC)

**사용자 역할:**

- **Admin**: 전체 시스템 관리자 (모든 권한)
- **Operator**: 시스템 운영자 (학습, 배포, 로그)
- **Developer**: 개발자 (API 테스트, 로그 확인)
- **Viewer**: 읽기 전용 사용자

**사용자 생성:**

Python CLI:
```python
from admin_dashboard.rbac import get_rbac_manager, Role

rbac = get_rbac_manager()

# 운영자 계정 생성
rbac.create_user(
    username="operator1",
    password="secure_password",
    role=Role.OPERATOR,
    full_name="John Operator",
    email="operator@company.com"
)
```

**사용자 목록 조회:**
```python
users = rbac.list_users()
for user in users:
    print(f"{user['username']} - {user['role']}")
```

**비밀번호 변경:**
```python
rbac.change_password("operator1", "new_secure_password")
```

### 10.2 감사 로그

**감사 로그 조회:**

```python
from admin_dashboard.audit_log import get_audit_logger

audit = get_audit_logger()

# 오늘의 로그 조회
logs = audit.query(limit=50)

# 특정 사용자의 로그
logs = audit.query(username="admin", limit=100)

# 보안 이벤트만 조회
logs = audit.query(level="security", limit=100)
```

**감사 로그 통계:**
```python
stats = audit.get_statistics()
print(f"총 이벤트: {stats['total_events']}")
print(f"보안 이벤트: {stats['security_events']}")
print(f"실패 횟수: {stats['failure_count']}")
```

**CSV 내보내기:**
```python
audit.export_to_csv(
    output_file="audit_report.csv",
    start_date="2025-01-01",
    end_date="2025-01-31"
)
```

### 10.3 네트워크 보안

**방화벽 설정 (Ubuntu/Debian):**

```bash
# UFW 활성화
sudo ufw enable

# 필요한 포트 열기
sudo ufw allow 5173/tcp  # Web UI
sudo ufw allow 8000/tcp  # Gateway
sudo ufw allow 8007/tcp  # Admin Dashboard

# 외부 접근 차단 (내부 네트워크만 허용)
sudo ufw allow from 192.168.1.0/24 to any port 9090  # Prometheus
sudo ufw allow from 192.168.1.0/24 to any port 3000  # Grafana
```

**방화벽 설정 (CentOS/RHEL):**

```bash
# Firewalld 활성화
sudo systemctl start firewalld
sudo systemctl enable firewalld

# 포트 열기
sudo firewall-cmd --add-port=5173/tcp --permanent
sudo firewall-cmd --add-port=8000/tcp --permanent
sudo firewall-cmd --reload
```

---

## 11. 문제 해결

### 11.1 서비스가 시작되지 않음

**문제:** Docker 컨테이너가 실행되지 않음

**해결 방법:**

1. 로그 확인:
```bash
docker-compose logs gateway
```

2. 포트 충돌 확인:
```bash
lsof -i :8000
```

3. 컨테이너 재생성:
```bash
docker-compose down
docker-compose up -d
```

### 11.2 GPU 메모리 부족

**문제:** CUDA out of memory 에러

**해결 방법:**

1. GPU 메모리 사용량 확인:
```bash
nvidia-smi
```

2. 배치 크기 줄이기 (학습 시):
   - Training 탭에서 Batch Size 감소 (8 → 4)

3. 다른 프로세스 종료:
```bash
# GPU 사용 중인 프로세스 확인
fuser -v /dev/nvidia*

# 프로세스 종료
kill -9 <PID>
```

### 11.3 API 응답 느림

**문제:** API 요청 응답 시간이 5초 이상

**원인 진단:**

1. Grafana에서 Response Time 대시보드 확인
2. 병목 지점 파악

**해결 방법:**

- CPU 사용률 높음: 컨테이너 재시작 또는 리소스 증설
- GPU 사용률 낮음: 배치 처리 설정 확인
- 네트워크 지연: 로컬 테스트로 확인

### 11.4 모델 학습 실패

**문제:** Training job failed

**해결 방법:**

1. 학습 로그 확인:
   - Training 탭에서 실패한 작업의 로그 확인

2. 데이터셋 확인:
```bash
ls -la /home/uproot/ax/poc/edgnet_dataset_large
```

3. GPU 메모리 확인:
```bash
nvidia-smi
```

4. 학습 재시작

### 11.5 디스크 공간 부족

**문제:** No space left on device

**해결 방법:**

1. 디스크 사용량 확인:
```bash
df -h
```

2. 불필요한 Docker 리소스 정리:
```bash
docker system prune -a
```

3. 오래된 로그 삭제:
```bash
find /home/uproot/ax/poc/logs -mtime +30 -delete
```

4. 오래된 백업 삭제:
```bash
find /home/uproot/ax/poc/backups -mtime +90 -delete
```

---

## 12. FAQ

### Q1. 기본 관리자 비밀번호를 잊어버렸습니다.

**A:** RBAC 사용자 파일을 수동으로 초기화하세요.

```bash
# 사용자 파일 삭제
rm /home/uproot/ax/poc/admin-dashboard/users.json

# Admin Dashboard 재시작 (기본 계정 자동 생성)
docker-compose restart admin-dashboard

# 기본 계정으로 로그인
Username: admin
Password: changeme123
```

### Q2. 학습 진행률이 0%로 표시됩니다.

**A:** Admin Dashboard가 재시작되어 메모리 내 학습 상태가 초기화되었습니다.

- 학습은 정상적으로 진행 중입니다.
- CLI로 로그 확인: `docker-compose logs -f admin-dashboard`

### Q3. VL API를 온프레미스에서 사용할 수 없나요?

**A:** VL API는 OpenAI/Anthropic 외부 API를 사용합니다. 온프레미스 환경에서는:

1. VL API 비활성화
2. 로컬 LLM으로 대체 (Llama 3.2 Vision 권장)
3. Hybrid 모드 사용 (VL 제외)

자세한 내용은 `ONPREMISE_DEPLOYMENT_GUIDE.md` 참조

### Q4. Prometheus/Grafana가 작동하지 않습니다.

**A:** 아직 활성화되지 않았습니다.

설정 방법:
1. `docker-compose.yml`에 Prometheus/Grafana 서비스 추가
2. 설정 파일 복사: `/home/uproot/ax/poc/monitoring/`
3. 컨테이너 시작: `docker-compose up -d prometheus grafana`

### Q5. 모델 파일은 어디에 저장되나요?

**A:** 각 API의 `models/` 디렉토리:

```
/home/uproot/ax/poc/edocr2-api/models/
/home/uproot/ax/poc/yolo-api/models/
/home/uproot/ax/poc/edgnet-api/models/
/home/uproot/ax/poc/skinmodel-api/models/
```

### Q6. 시스템 성능을 개선하려면?

**A:** 성능 개선 방법:

1. **GPU 사용**: 모든 모델에 GPU 할당
2. **배치 처리**: 여러 요청을 배치로 처리
3. **캐싱**: 자주 사용되는 결과 캐싱
4. **리소스 증설**: CPU, RAM, GPU 메모리 증설

### Q7. 백업은 얼마나 자주 해야 하나요?

**A:** 권장 백업 주기:

- **일일 백업**: Cron으로 자동화 (새벽 2시)
- **주간 백업**: 매주 일요일 전체 백업
- **월간 백업**: 매월 1일 장기 보관용 백업
- **모델 학습 후**: 새 모델 학습 완료 시 즉시 백업

### Q8. 원격에서 접속하려면?

**A:** 보안 고려사항:

1. **VPN 사용 권장**: 직접 노출보다 VPN 터널 사용
2. **HTTPS 설정**: Nginx 리버스 프록시 + SSL 인증서
3. **방화벽 설정**: 특정 IP만 허용
4. **강력한 인증**: 복잡한 비밀번호 + 2FA (추후 구현)

```bash
# Nginx 리버스 프록시 예시
sudo apt install nginx

# /etc/nginx/sites-available/drawing-analysis
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5173;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /admin {
        proxy_pass http://localhost:5173/admin;
        allow 192.168.1.0/24;  # 내부 네트워크만 허용
        deny all;
    }
}
```

---

## 지원 및 문의

**시스템 관련 문의:**
- 이메일: support@company.com
- 전화: 02-XXXX-XXXX

**긴급 장애 신고:**
- 긴급 핫라인: 010-XXXX-XXXX

**문서 업데이트:**
- 버전: 1.0
- 최종 수정: 2025-01-14

---

© 2025 AI Drawing Analysis System. All rights reserved.
