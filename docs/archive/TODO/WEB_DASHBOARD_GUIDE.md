# 🌐 AX 웹 통합 관리 대시보드 가이드

**생성 일시**: 2025-11-14
**대시보드 URL**: http://localhost:9000
**포트**: 9000

---

## 📊 개요

AX 시스템의 모든 기능을 웹 브라우저에서 관리할 수 있는 통합 관리 대시보드입니다.

### 주요 기능

1. ✅ **API 상태 모니터링** - 실시간 헬스체크
2. ✅ **GPU 모니터링** - VRAM 사용량, 온도, 활용도
3. ✅ **모델 관리** - 모델 파일 조회, 다운로드
4. ✅ **학습 관리** - 웹에서 직접 모델 학습 실행
5. ✅ **추론 테스트** - 파일 업로드로 즉시 추론 테스트
6. ✅ **로그 확인** - 실시간 서비스 로그 조회
7. ✅ **Docker 관리** - 컨테이너 start/stop/restart

---

## 🚀 시작하기

### 1. 대시보드 시작

```bash
cd /home/uproot/ax/poc/admin-dashboard
./start.sh
```

또는 수동 실행:

```bash
cd /home/uproot/ax/poc/admin-dashboard
python3 dashboard.py
```

### 2. 웹 브라우저 접속

```
http://localhost:9000
```

### 3. 대시보드 종료

```bash
# 프로세스 찾기
ps aux | grep dashboard.py

# 종료
kill [PID]
```

---

## 📋 기능별 사용 가이드

### 1. API 상태 모니터링 📡

**위치**: 메인 대시보드 상단 왼쪽

**기능**:
- 모든 API 실시간 상태 확인
- 응답 시간 측정
- 헬스체크 자동 갱신 (5초마다)

**표시 정보**:
- API 이름 (eDOCr2, YOLO, Skin Model 등)
- URL
- 상태 (healthy/unhealthy/error)
- 응답 시간

**색상 코드**:
- 🟢 녹색 테두리: 정상 작동 (healthy)
- 🔴 빨간 테두리: 비정상 (unhealthy)
- 🟡 노란 테두리: 오류 (error)

---

### 2. GPU 모니터링 🎮

**위치**: 메인 대시보드 상단 중앙

**기능**:
- GPU 디바이스 정보
- VRAM 사용량 (실시간)
- 사용률 (%)
- 프로그레스 바 시각화

**표시 정보**:
- GPU 모델명 (e.g., NVIDIA GeForce RTX 3080 Laptop)
- 사용 중 메모리 / 전체 메모리
- 사용률 퍼센트
- 시각적 프로그레스 바

**색상**:
- 그라데이션 프로그레스 바 (보라색)

---

### 3. 시스템 리소스 💻

**위치**: 메인 대시보드 상단 오른쪽

**기능**:
- CPU 사용률
- 메모리 사용률
- 디스크 사용률

**표시 형식**:
- 2x2 그리드
- 각 리소스별 퍼센트 표시

---

### 4. 모델 관리 📦

**위치**: 탭 메뉴 - "모델 관리"

**기능**:
- 모델 파일 목록 조회
- 모델 타입 선택 (Skin Model, EDGNet, YOLO)
- 파일 정보 확인

**사용 방법**:
1. 모델 타입 선택 (드롭다운)
2. 모델 목록 자동 로드
3. 각 모델 정보 확인:
   - 파일명
   - 크기 (MB)
   - 마지막 수정 시간

**지원 모델 타입**:
- **Skin Model**: `flatness_predictor_xgboost.pkl`, `cylindricity_predictor_xgboost.pkl` 등
- **EDGNet**: `edgnet_simple.pth`, `graphsage_dimension_classifier.pth` 등
- **YOLO**: `yolo11n.pt`, `best.pt` 등

---

### 5. 학습 관리 🎓

**위치**: 탭 메뉴 - "학습"

**기능**:
- 웹에서 직접 모델 학습 실행
- 학습 로그 실시간 확인
- 학습 결과 확인

**사용 방법**:

#### Skin Model 학습
```
1. "Skin Model 학습" 버튼 클릭
2. 학습 시작 (약 14초 소요)
3. 학습 로그 자동 표시
4. 완료 후 결과 확인:
   - R² 점수
   - MAE, RMSE
   - 학습 시간
```

#### EDGNet 학습
```
1. "EDGNet 학습" 버튼 클릭
2. 학습 시작 (약 1초 소요, GPU)
3. 학습 로그 자동 표시
4. 완료 후 결과 확인:
   - Validation Accuracy
   - 에폭별 성능
```

**학습 출력 형식**:
- ✅ 성공: 녹색 알림 + 학습 로그
- ❌ 실패: 빨간 알림 + 에러 로그

**학습 로그 예시**:
```
============================================================
Skin Model XGBoost 업그레이드
============================================================

📊 학습 데이터 생성...
  샘플 수: 5000
  특징 수: 6

🚀 XGBoost 모델 학습 시작...
📦 Flatness 모델:     R²=0.8691, MAE=0.000566
📦 Cylindricity 모델:  R²=0.9550, MAE=0.004286
📦 Position 모델:     R²=0.7126, MAE=0.003132

✅ 학습 완료: 13.8초
평균 R² 점수: 0.8456
```

---

### 6. 추론 테스트 🔬

**위치**: 탭 메뉴 - "추론 테스트"

**기능**:
- 파일 업로드로 즉시 추론
- 다양한 API 테스트 (YOLO, eDOCr2, Skin Model)
- 결과 JSON 확인

**사용 방법**:

#### YOLO 추론
```
1. API 선택: YOLO
2. 이미지 파일 업로드 (JPG, PNG)
3. 자동 추론 실행
4. 결과 확인:
   - 검출된 객체 수
   - 각 객체의 클래스, 신뢰도, 위치
   - 처리 시간
```

**결과 예시**:
```json
{
  "status": "success",
  "total_detections": 76,
  "processing_time": 0.31,
  "detections": [
    {
      "class": "diameter_dim",
      "confidence": 0.95,
      "bbox": [100, 200, 150, 250]
    },
    ...
  ]
}
```

#### eDOCr2 추론
```
1. API 선택: eDOCr2
2. 도면 파일 업로드 (PDF, JPG)
3. 자동 OCR 실행
4. 결과 확인:
   - 추출된 치수
   - GD&T 기호
   - 텍스트 정보
```

**결과 예시**:
```json
{
  "status": "success",
  "data": {
    "dimensions": [
      {"value": 50.0, "unit": "mm", "type": "diameter"},
      {"value": 100.0, "unit": "mm", "type": "length"}
    ],
    "gdt": [
      {"type": "flatness", "value": 0.01}
    ],
    "text": {
      "drawing_number": "A12-311197-9",
      "revision": "Rev.2"
    }
  },
  "processing_time": 21.5
}
```

#### Skin Model 추론
```
1. API 선택: Skin Model
2. 입력 데이터 파일 업로드 (JSON)
3. 자동 예측 실행
4. 결과 확인:
   - Flatness 예측값
   - Cylindricity 예측값
   - Position 예측값
```

---

### 7. 로그 확인 📜

**위치**: 탭 메뉴 - "로그"

**기능**:
- 실시간 서비스 로그 조회
- 서비스별 로그 선택
- 로그 새로고침

**사용 방법**:
```
1. 서비스 선택 (드롭다운):
   - eDOCr2
   - EDGNet
   - Skin Model
   - YOLO
   - Gateway

2. "새로고침" 버튼 클릭 (또는 자동 로드)

3. 로그 확인:
   - 최근 200줄 표시
   - 타임스탬프 포함
   - 스크롤 가능
```

**로그 형식**:
```
[서비스명       |] 2025-11-14 10:41:31,870 - ml_predictor - INFO - ✅ XGBoost 모델 로드 성공
[서비스명       |] 2025-11-14 10:41:33,258 - __mp_main__ - INFO - ML Predictor initialized: True
[서비스명       |] INFO:     Uvicorn running on http://0.0.0.0:5003
```

**유용한 로그 패턴**:
- `✅` : 성공 메시지
- `❌` : 에러 메시지
- `⚠️` : 경고 메시지
- `INFO` : 정보 로그
- `ERROR` : 에러 로그

---

### 8. Docker 관리 🐳

**위치**: 탭 메뉴 - "Docker 관리"

**기능**:
- 컨테이너 시작 (Start)
- 컨테이너 정지 (Stop)
- 컨테이너 재시작 (Restart)

**사용 방법**:

#### 컨테이너 재시작
```
1. 서비스 선택 (예: eDOCr2)
2. "Restart" 버튼 클릭
3. 실행 로그 확인
4. 완료 메시지 대기 (✅)
5. API 상태 자동 갱신 (2초 후)
```

**지원 서비스**:
- eDOCr2 API
- Skin Model API
- YOLO API
- Gateway API

**주의사항**:
- Stop 후 자동으로 Start 되지 않음
- Restart는 컨테이너를 재시작하지만 이미지를 재빌드하지 않음
- 이미지 재빌드가 필요하면 터미널 사용:
  ```bash
  docker-compose build [서비스명]
  docker-compose up -d [서비스명]
  ```

---

## 🎨 UI 구성

### 색상 스킴

**메인 색상**:
- 보라색 그라데이션: `#667eea` → `#764ba2`
- 배경: `#f5f7fa`
- 카드 배경: 흰색
- 텍스트: `#333`

**상태 색상**:
- 성공: `#10b981` (녹색)
- 에러: `#ef4444` (빨간색)
- 경고: `#f59e0b` (노란색)

### 레이아웃

**헤더**:
- 그라데이션 배경
- 제목: "AX Admin Dashboard"
- 부제: "통합 관리 시스템"

**메인 대시보드**:
- 3열 그리드 (API 상태, GPU, 시스템)
- 반응형 디자인 (최소 300px)
- 자동 새로고침 (5초)

**탭 메뉴**:
- 5개 탭 (모델, 학습, 추론, 로그, Docker)
- 활성 탭 강조 (보라색 밑줄)
- 탭 전환 시 자동 로드

---

## 📊 API 엔드포인트

대시보드 백엔드 API:

### GET /api/status
**기능**: 전체 시스템 상태 조회

**응답**:
```json
{
  "apis": [
    {
      "name": "edocr2",
      "url": "http://localhost:5001",
      "status": "healthy",
      "response_time": 0.05
    },
    ...
  ],
  "gpu": {
    "available": true,
    "device_name": "NVIDIA GeForce RTX 3080 Laptop",
    "total_memory": 8192,
    "used_memory": 5622,
    "free_memory": 2570,
    "utilization": 68.6
  },
  "system": {
    "cpu_percent": 15.2,
    "memory_percent": 45.8,
    "disk_percent": 62.3
  },
  "timestamp": "2025-11-14T10:45:30"
}
```

### GET /api/models/{model_type}
**기능**: 모델 목록 조회

**파라미터**:
- `model_type`: skinmodel, edgnet, yolo

**응답**:
```json
{
  "models": [
    {
      "name": "flatness_predictor_xgboost.pkl",
      "path": "/home/uproot/ax/poc/skinmodel-api/models/flatness_predictor_xgboost.pkl",
      "size": 1458240,
      "modified": "2025-11-14T10:39:45",
      "type": "skinmodel"
    },
    ...
  ]
}
```

### GET /api/logs/{service}
**기능**: 서비스 로그 조회

**파라미터**:
- `service`: edocr2-api, skinmodel-api, yolo-api, gateway-api
- `lines`: 로그 줄 수 (기본 100)

**응답**:
```json
{
  "service": "skinmodel-api",
  "logs": "[서비스 로그 내용...]"
}
```

### POST /api/train/{model_type}
**기능**: 모델 학습 트리거

**파라미터**:
- `model_type`: skinmodel, edgnet

**응답**:
```json
{
  "status": "completed",
  "stdout": "[학습 로그...]",
  "stderr": ""
}
```

### POST /api/inference/{api_name}
**기능**: 추론 테스트

**파라미터**:
- `api_name`: yolo, edocr2, skinmodel
- `file`: 업로드 파일

**응답**:
```json
{
  "status": "success",
  "data": {...},
  "processing_time": 0.31
}
```

### POST /api/docker/{action}/{service}
**기능**: Docker 컨테이너 제어

**파라미터**:
- `action`: start, stop, restart
- `service`: edocr2-api, skinmodel-api, yolo-api, gateway-api

**응답**:
```json
{
  "action": "restart",
  "service": "skinmodel-api",
  "status": "success",
  "output": "[docker-compose 출력...]"
}
```

### GET /api/gpu/stats
**기능**: GPU 상세 통계

**응답**:
```json
{
  "index": 0,
  "name": "NVIDIA GeForce RTX 3080 Laptop GPU",
  "temperature": 45,
  "gpu_utilization": 68.6,
  "memory_utilization": 68.7,
  "memory_total": 8192,
  "memory_used": 5622,
  "memory_free": 2570
}
```

---

## 🔧 설정 및 커스터마이징

### 포트 변경

**환경 변수**:
```bash
export DASHBOARD_PORT=9000
python3 dashboard.py
```

**코드 수정**:
```python
# dashboard.py 마지막 부분
port = int(os.getenv("DASHBOARD_PORT", 9000))  # 기본값 변경
```

### API URL 변경

**코드 수정**:
```python
# dashboard.py
API_URLS = {
    "edocr2": "http://localhost:5001",  # 변경
    "edgnet": "http://localhost:5012",
    ...
}
```

### 자동 새로고침 간격 변경

**코드 수정**:
```javascript
// templates/dashboard.html
setInterval(loadStatus, 5000);  // 5000ms = 5초
```

---

## 🐛 트러블슈팅

### 대시보드가 시작되지 않음

**확인 사항**:
1. 포트 9000이 사용 중인지 확인
   ```bash
   lsof -i :9000
   ```

2. 의존성 설치 확인
   ```bash
   pip3 list | grep fastapi
   pip3 list | grep uvicorn
   ```

3. 로그 확인
   ```bash
   tail -f /home/uproot/ax/poc/admin-dashboard/dashboard.log
   ```

### API 상태가 "error"로 표시됨

**원인**:
- API 컨테이너가 실행되지 않음
- 포트가 열려있지 않음
- 헬스체크 엔드포인트 응답 없음

**해결**:
1. Docker 컨테이너 상태 확인
   ```bash
   docker-compose ps
   ```

2. API 직접 테스트
   ```bash
   curl http://localhost:5001/api/v1/health
   ```

3. Docker 로그 확인
   ```bash
   docker-compose logs [서비스명]
   ```

### GPU 상태가 "not available"로 표시됨

**원인**:
- nvidia-smi 실행 실패
- GPU 드라이버 미설치

**해결**:
```bash
nvidia-smi
```

### 학습이 실패함

**확인 사항**:
1. 스크립트 경로 확인
   ```bash
   ls /home/uproot/ax/poc/scripts/upgrade_skinmodel_xgboost.py
   ```

2. Python 의존성 확인
   ```bash
   python3 -c "import xgboost; print(xgboost.__version__)"
   ```

3. 수동 실행 테스트
   ```bash
   cd /home/uproot/ax/poc
   python3 scripts/upgrade_skinmodel_xgboost.py
   ```

---

## 📖 사용 시나리오

### 시나리오 1: 새로운 모델 학습

```
1. 대시보드 접속 (http://localhost:9000)
2. "학습" 탭 클릭
3. "Skin Model 학습" 버튼 클릭
4. 학습 진행 상황 확인 (약 14초)
5. 학습 완료 후 결과 확인 (R² 점수)
6. "모델 관리" 탭으로 이동
7. Skin Model 선택
8. 새로 생성된 XGBoost 모델 확인
9. "Docker 관리" 탭으로 이동
10. Skin Model API 재시작
11. 메인 대시보드에서 API 상태 확인 (healthy)
```

### 시나리오 2: 추론 테스트

```
1. "추론 테스트" 탭 클릭
2. API 선택 (예: YOLO)
3. 테스트 이미지 업로드
4. 자동 추론 실행
5. 결과 JSON 확인
6. "로그" 탭으로 이동
7. YOLO 서비스 선택
8. 추론 로그 확인 (처리 시간, 검출 결과 등)
```

### 시나리오 3: 시스템 모니터링

```
1. 대시보드 메인 화면 유지
2. 자동 새로고침으로 실시간 모니터링:
   - API 상태 (5초마다)
   - GPU 사용률 (5초마다)
   - 시스템 리소스 (5초마다)
3. 문제 발견 시:
   - API 상태가 unhealthy → "로그" 탭에서 확인
   - GPU 사용률 100% → "GPU 상세" API로 확인
   - 필요 시 "Docker 관리"에서 재시작
```

### 시나리오 4: 문제 해결

```
1. API 상태가 "error"로 표시됨
2. "로그" 탭 클릭
3. 해당 서비스 선택
4. 에러 로그 확인
5. "Docker 관리" 탭으로 이동
6. 서비스 재시작
7. 메인 대시보드에서 상태 확인
8. 여전히 문제 시 터미널에서 재빌드:
   docker-compose build [서비스명]
   docker-compose up -d [서비스명]
```

---

## 🎯 핵심 기능 요약

### 웹에서 할 수 있는 모든 작업

1. ✅ **모니터링**
   - API 상태 실시간 확인
   - GPU 사용량 모니터링
   - 시스템 리소스 모니터링

2. ✅ **모델 관리**
   - 모델 파일 목록 조회
   - 모델 정보 확인 (크기, 날짜)
   - 모델 타입별 분류

3. ✅ **학습**
   - Skin Model XGBoost 학습
   - EDGNet 학습
   - 학습 로그 실시간 확인
   - 학습 결과 확인

4. ✅ **추론**
   - YOLO 추론 (이미지 → 객체 검출)
   - eDOCr2 추론 (도면 → OCR)
   - Skin Model 추론 (데이터 → 공차 예측)
   - 결과 JSON 확인

5. ✅ **로그**
   - 서비스별 로그 조회
   - 실시간 로그 새로고침
   - 최근 200줄 표시

6. ✅ **Docker**
   - 컨테이너 시작/정지/재시작
   - 작업 결과 확인
   - 자동 상태 갱신

---

## 📁 파일 구조

```
admin-dashboard/
├── dashboard.py              # 백엔드 API 서버
├── requirements.txt          # Python 의존성
├── start.sh                  # 시작 스크립트
├── dashboard.log            # 로그 파일
└── templates/
    └── dashboard.html       # 웹 UI
```

---

## 🚀 배포 및 운영

### 개발 모드 (현재)

```bash
cd /home/uproot/ax/poc/admin-dashboard
python3 dashboard.py
```

**특징**:
- 로컬호스트만 접근 (0.0.0.0:9000)
- 로그 파일로 출력
- 수동 재시작 필요

### 프로덕션 모드 (권장)

**systemd 서비스 등록**:

```bash
# /etc/systemd/system/ax-dashboard.service 생성
[Unit]
Description=AX Admin Dashboard
After=network.target

[Service]
Type=simple
User=uproot
WorkingDirectory=/home/uproot/ax/poc/admin-dashboard
ExecStart=/usr/bin/python3 dashboard.py
Restart=always

[Install]
WantedBy=multi-user.target
```

**서비스 시작**:
```bash
sudo systemctl enable ax-dashboard
sudo systemctl start ax-dashboard
sudo systemctl status ax-dashboard
```

### Nginx 리버스 프록시 (선택)

```nginx
# /etc/nginx/sites-available/ax-dashboard
server {
    listen 80;
    server_name ax-dashboard.local;

    location / {
        proxy_pass http://localhost:9000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 💡 팁 & 베스트 프랙티스

### 1. 효율적인 모니터링

- 대시보드를 항상 열어두고 모니터링
- GPU 사용률이 높을 때 학습 스케줄링
- API 응답 시간 추적하여 성능 저하 감지

### 2. 안전한 학습

- 학습 전 현재 모델 백업
- 학습 로그 저장 및 분석
- 학습 후 추론 테스트로 검증

### 3. 로그 활용

- 에러 발생 시 즉시 로그 확인
- 정기적으로 로그 검토하여 패턴 파악
- 로그를 기반으로 시스템 최적화

### 4. Docker 관리

- 변경사항 반영 시 재시작 사용
- 재시작으로 해결 안 되면 재빌드
- 재빌드 전 로그 확인

---

## 🎉 결론

**AX 웹 통합 관리 대시보드**로 모든 시스템을 한 곳에서 관리할 수 있습니다!

### 주요 장점

1. ✅ **편의성**: 터미널 명령 없이 모든 작업 가능
2. ✅ **가시성**: 실시간 시스템 상태 한눈에 확인
3. ✅ **효율성**: 웹 브라우저에서 즉시 작업 실행
4. ✅ **안정성**: 로그와 모니터링으로 문제 빠르게 해결

### 다음 단계

- 대시보드 사용하여 시스템 모니터링
- 정기적으로 모델 재학습
- 추론 테스트로 성능 검증
- 로그 분석하여 최적화

---

**접속**: http://localhost:9000

**작성일**: 2025-11-14
**버전**: 1.0.0

**웹에서 모든 것을 관리하세요!** 🚀
