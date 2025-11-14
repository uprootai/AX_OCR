# 🎮 AX 시스템 웹 대시보드 사용 가이드

## 🚀 빠른 시작

### 1. 웹 대시보드 접속

```bash
# 브라우저에서 다음 주소 열기
http://localhost:9000
```

### 2. 메인 화면에서 확인할 수 있는 정보

- ✅ 모든 API 상태 (실시간)
- 📊 GPU 사용량 (메모리, 활용률)
- 💻 시스템 리소스 (CPU, 메모리, 디스크)
- 🔄 5초마다 자동 갱신

---

## 📱 주요 기능

### 🔧 모델 관리 탭

**할 수 있는 일**:
- Skin Model 파일 목록 확인
- EDGNet 모델 파일 목록 확인
- 모델 메타데이터 조회

**사용법**:
1. "모델 관리" 탭 클릭
2. "Skin Model" 또는 "EDGNet" 버튼 클릭
3. 모델 파일 목록 확인

### 🎓 학습 탭

**할 수 있는 일**:
- Skin Model XGBoost 재학습
- EDGNet 모델 재학습
- 학습 진행 상황 실시간 확인

**사용법**:
1. "학습" 탭 클릭
2. "Skin Model 학습" 또는 "EDGNet 학습" 버튼 클릭
3. 학습 로그 실시간 확인
4. 완료 후 결과 확인

**예시**:
```
Skin Model 학습 → 약 14초 소요
- Flatness R²: 0.8691
- Cylindricity R²: 0.9550
- Position R²: 0.7126
```

### 🧪 추론 테스트 탭

**할 수 있는 일**:
- 실제 이미지로 추론 테스트
- YOLO 객체 탐지
- eDOCr2 OCR 처리
- Skin Model 예측

**사용법**:
1. "추론 테스트" 탭 클릭
2. API 선택 (YOLO, eDOCr2, Skin Model)
3. 파일 선택 (이미지 업로드)
4. "테스트 실행" 버튼 클릭
5. 결과 JSON 확인

**지원 파일 형식**:
- YOLO: JPG, PNG, PDF
- eDOCr2: JPG, PNG, PDF
- Skin Model: JSON (특징 데이터)

### 📋 로그 탭

**할 수 있는 일**:
- 모든 서비스 로그 조회
- 에러 추적
- 디버깅

**사용법**:
1. "로그" 탭 클릭
2. 서비스 선택 (eDOCr2, YOLO, Skin Model, etc.)
3. 최근 200줄 로그 확인

### 🐳 Docker 관리 탭

**할 수 있는 일**:
- 컨테이너 시작/중지/재시작
- 웹에서 원클릭 관리

**사용법**:
1. "Docker 관리" 탭 클릭
2. 서비스 선택
3. 작업 선택 (시작/중지/재시작)
4. 실행 버튼 클릭

**관리 가능한 서비스**:
- eDOCr2
- EDGNet
- Skin Model
- VL API
- YOLO
- Gateway

---

## 💡 실전 사용 시나리오

### 시나리오 1: 새로운 도면 분석

1. **메인 화면**에서 모든 API가 "healthy" 인지 확인
2. **추론 테스트 탭**으로 이동
3. "eDOCr2" 선택
4. 도면 이미지 업로드
5. 결과 확인 (OCR 텍스트)

### 시나리오 2: 모델 성능 개선

1. **학습 탭**으로 이동
2. "Skin Model 학습" 클릭
3. 학습 완료 대기 (~14초)
4. **로그 탭**에서 학습 결과 확인
5. R² 점수 확인

### 시나리오 3: 시스템 문제 해결

1. **메인 화면**에서 "unhealthy" API 확인
2. **로그 탭**에서 해당 서비스 로그 조회
3. 에러 메시지 확인
4. **Docker 관리 탭**에서 서비스 재시작
5. 문제 해결 확인

### 시나리오 4: GPU 메모리 모니터링

1. **메인 화면**에서 GPU 상태 확인
2. 사용량이 높으면 (>80%) 주의
3. **Docker 관리 탭**에서 불필요한 서비스 중지
4. GPU 메모리 확보

---

## 🎯 대시보드 API 엔드포인트

웹 UI 외에도 직접 API를 호출할 수 있습니다:

### 시스템 상태 조회

```bash
curl http://localhost:9000/api/status
```

**응답 예시**:
```json
{
  "apis": [
    {
      "name": "edocr2",
      "url": "http://localhost:5001",
      "status": "healthy",
      "response_time": 0.0035
    }
  ],
  "gpu": {
    "available": true,
    "device_name": "NVIDIA GeForce RTX 3080 Laptop GPU",
    "total_memory": 8192,
    "used_memory": 1715,
    "free_memory": 6477,
    "utilization": 8.0
  },
  "system": {
    "cpu_percent": 3.2,
    "memory_percent": 50.1,
    "disk_percent": 35.2
  }
}
```

### GPU 통계 조회

```bash
curl http://localhost:9000/api/gpu/stats
```

### 모델 파일 목록 조회

```bash
# Skin Model
curl http://localhost:9000/api/models/skinmodel

# EDGNet
curl http://localhost:9000/api/models/edgnet
```

### 학습 트리거

```bash
# Skin Model 학습
curl -X POST http://localhost:9000/api/train/skinmodel

# EDGNet 학습
curl -X POST http://localhost:9000/api/train/edgnet
```

### 로그 조회

```bash
# eDOCr2 로그
curl http://localhost:9000/api/logs/edocr2

# YOLO 로그
curl http://localhost:9000/api/logs/yolo
```

### Docker 컨테이너 제어

```bash
# 시작
curl -X POST http://localhost:9000/api/docker/start/edocr2

# 중지
curl -X POST http://localhost:9000/api/docker/stop/edocr2

# 재시작
curl -X POST http://localhost:9000/api/docker/restart/edocr2
```

---

## ⚙️ 대시보드 관리

### 시작

```bash
cd /home/uproot/ax/poc/admin-dashboard
./start.sh
```

### 중지

```bash
pkill -f dashboard.py
```

### 재시작

```bash
pkill -f dashboard.py
cd /home/uproot/ax/poc/admin-dashboard
./start.sh
```

### 로그 확인

```bash
tail -f /home/uproot/ax/poc/admin-dashboard/dashboard.log
```

---

## 🔧 문제 해결

### 대시보드가 응답하지 않을 때

```bash
# 프로세스 확인
ps aux | grep dashboard.py

# 포트 확인
netstat -tlnp | grep 9000

# 재시작
pkill -f dashboard.py
cd /home/uproot/ax/poc/admin-dashboard
./start.sh
```

### API 상태가 "unhealthy"일 때

1. **로그 탭**에서 해당 서비스 로그 확인
2. **Docker 관리 탭**에서 서비스 재시작
3. 여전히 문제가 있으면 터미널에서:

```bash
# 컨테이너 상태 확인
docker-compose ps

# 컨테이너 로그 확인
docker-compose logs edocr2-api

# 재시작
docker-compose restart edocr2-api
```

### GPU 메모리 부족

```bash
# GPU 상태 확인
nvidia-smi

# 프로세스 확인
nvidia-smi | grep python

# 불필요한 컨테이너 중지
docker-compose stop vl-api  # 예시
```

---

## 📊 성능 지표

### 정상 범위

- **GPU 메모리**: 15-30% (유휴 시)
- **GPU 활용률**: 5-20% (유휴 시)
- **CPU**: 5-15%
- **메모리**: 30-60%

### 주의 필요

- **GPU 메모리**: >80%
- **GPU 활용률**: >90% (지속 시)
- **CPU**: >80%
- **메모리**: >85%

### API 응답 시간

- **정상**: <50ms
- **느림**: 50-200ms
- **문제**: >200ms

---

## 🎉 요약

AX 웹 대시보드를 통해:

✅ **모든 시스템을 한 곳에서 관리**
✅ **실시간 모니터링 (5초 자동 갱신)**
✅ **원클릭 학습 및 추론**
✅ **Docker 컨테이너 제어**
✅ **로그 조회 및 디버깅**

**접속 주소**: http://localhost:9000

즐거운 개발 되세요! 🚀
