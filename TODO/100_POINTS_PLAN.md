# 🎯 100점 달성 플랜

**현재 점수**: 92-95/100
**목표 점수**: 100/100
**점수 갭**: 5-8점

---

## 📊 점수 손실 원인 분석

### 1. 대규모 데이터 학습 부재 (-5점)

**현재 상태**:
- ✅ Skin Model: XGBoost로 업그레이드 완료
- ✅ eDOCr2: GPU 전처리 완료
- ❌ **EDGNet**: 소규모 샘플 데이터만 사용 (25KB 모델)
- ❌ **YOLO**: Synthetic 데이터로만 학습 (5.3MB 모델)

**데이터셋 현황**:
```
/datasets/synthetic_test/     - 5개 파일 (테스트용)
/datasets/synthetic_random/   - 5개 파일 (소규모)
/edgnet_dataset/             - 5개 파일 (실제 도면)
/edgnet_dataset_augmented/   - 증강 데이터 (일부)
```

**문제점**:
1. EDGNet 모델이 25KB로 매우 작음 → 실제 프로덕션에서 정확도 낮음
2. YOLO 모델이 synthetic 데이터로만 학습 → 실제 도면에서 성능 저하
3. 학습 데이터셋이 5-10개 파일 수준 → 과소적합 위험

**해결 방안** (+5점):
1. **EDGNet 대규모 학습**:
   - 현재: 25KB 모델 (toy model)
   - 목표: 500MB+ 모델 (실제 프로덕션 급)
   - 데이터: 실제 도면 100+ 이미지로 학습

2. **YOLO 커스텀 데이터셋 학습**:
   - 현재: Synthetic 데이터
   - 목표: 실제 도면 데이터셋
   - 클래스: 치수선, 치수값, 기호, 표 등

3. **데이터 증강 파이프라인**:
   - Rotation, Flip, Brightness, Contrast
   - 5개 이미지 → 50+ 증강 이미지

### 2. 프로덕션 준비도 부족 (-2-3점)

**현재 상태**:
- ✅ Docker Compose 구성
- ✅ 환경 변수 관리
- ✅ 설정 기반 아키텍처
- ❌ **CI/CD 파이프라인 없음**
- ❌ **프로덕션 환경 설정 없음**
- ❌ **성능 모니터링 부족**

**문제점**:
1. Docker 이미지가 최적화되지 않음 (대용량)
2. 빌드/배포 자동화 없음
3. 로그 수집 시스템 없음
4. 메트릭 모니터링 없음

**해결 방안** (+2-3점):
1. **Docker 이미지 최적화**:
   - Multi-stage build 개선
   - 불필요한 레이어 제거
   - 이미지 크기 50% 감소

2. **성능 최적화**:
   - Nginx gzip 압축 활성화 ✅ (이미 완료)
   - API 응답 캐싱
   - 데이터베이스 연결 풀링

3. **환경 분리**:
   - `.env.development`
   - `.env.production`
   - `.env.test`

---

## 🚀 100점 달성 전략

### Phase 1: 대규모 데이터 학습 (+5점) - **핵심**

#### 1.1 EDGNet 대규모 학습

**작업 내용**:
```bash
# 1. 데이터 증강
cd /home/uproot/ax/poc/edgnet_dataset/
python augment_dataset.py --source edgnet_dataset/ \
                          --output edgnet_dataset_large/ \
                          --augment 10

# 2. 대규모 학습
cd /home/uproot/ax/poc/edgnet-api/
python train_large.py --data edgnet_dataset_large/ \
                      --epochs 100 \
                      --batch-size 16 \
                      --model-size large

# 예상 결과:
# - 모델 크기: 25KB → 500MB+
# - 정확도: 향상
# - 학습 시간: ~2-3시간 (GPU)
```

**검증 방법**:
- 모델 파일 크기 확인: `ls -lh models/edgnet_large.pth`
- 정확도 메트릭: `mIoU > 0.85`
- 실제 도면 테스트: 5개 이미지로 검증

#### 1.2 YOLO 커스텀 데이터셋 학습

**작업 내용**:
```bash
# 1. 실제 도면 데이터셋 준비
cd /home/uproot/ax/poc/datasets/
mkdir real_drawings/
# 도면 이미지 100+ 준비 및 라벨링

# 2. YOLO 학습
cd /home/uproot/ax/poc/yolo-api/
python train.py --data real_drawings/dataset.yaml \
                --epochs 100 \
                --batch-size 16 \
                --imgsz 640

# 예상 결과:
# - mAP@0.5: > 0.7
# - 학습 시간: ~1-2시간 (GPU)
```

**검증 방법**:
- mAP 메트릭 확인
- 실제 도면에서 치수선 감지 테스트

#### 1.3 학습 자동화 스크립트

**파일**: `/home/uproot/ax/poc/scripts/train_all_models.sh`

```bash
#!/bin/bash
# 모든 모델 자동 학습

echo "🚀 Starting large-scale training..."

# Skin Model (이미 완료)
echo "✅ Skin Model - Already trained with XGBoost"

# EDGNet
echo "📊 Training EDGNet with large dataset..."
cd /home/uproot/ax/poc/edgnet-api/
python train_large.py

# YOLO
echo "🎯 Training YOLO with real drawings..."
cd /home/uproot/ax/poc/yolo-api/
python train.py --data real_drawings.yaml --epochs 100

echo "✅ All models trained successfully!"
```

### Phase 2: 프로덕션 최적화 (+2-3점) - **선택**

#### 2.1 Docker 이미지 최적화

**현재 이미지 크기 확인**:
```bash
docker images | grep poc_
# poc_web-ui       latest    2.5GB
# poc_edocr2-api   latest    4.2GB
# poc_yolo-api     latest    5.8GB
```

**최적화 방안**:
1. **Alpine 기반 이미지 사용**:
   ```dockerfile
   FROM python:3.10-alpine AS builder
   ```

2. **Multi-stage build 개선**:
   ```dockerfile
   # Build stage
   FROM node:20-alpine AS builder
   WORKDIR /app
   COPY package*.json ./
   RUN npm ci --only=production
   COPY . .
   RUN npm run build

   # Production stage
   FROM nginx:alpine
   COPY --from=builder /app/dist /usr/share/nginx/html
   # 이미지 크기: 2.5GB → 200MB
   ```

3. **.dockerignore 최적화**:
   ```
   node_modules/
   .git/
   *.log
   __pycache__/
   *.pyc
   .pytest_cache/
   ```

#### 2.2 환경 분리

**파일 구조**:
```
web-ui/
├── .env.development
├── .env.production
├── .env.test
└── docker-compose.yml
```

**.env.production**:
```env
VITE_GATEWAY_URL=https://api.production.com
VITE_EDOCR2_URL=https://edocr2.production.com
# ... production URLs
```

**docker-compose.yml** 개선:
```yaml
services:
  web-ui:
    build:
      context: ./web-ui
      args:
        - NODE_ENV=${NODE_ENV:-production}
    env_file:
      - .env.${ENV:-production}
```

#### 2.3 성능 모니터링 (선택사항)

**구성 요소**:
1. **Prometheus**: 메트릭 수집
2. **Grafana**: 시각화 대시보드
3. **Loki**: 로그 수집

**docker-compose.monitoring.yml**:
```yaml
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

---

## 📋 실행 체크리스트

### 필수 (100점 달성)

- [ ] **EDGNet 대규모 학습**
  - [ ] 데이터 증강 (5개 → 50+ 이미지)
  - [ ] 대규모 모델 학습 (25KB → 500MB+)
  - [ ] 정확도 검증 (mIoU > 0.85)
  - [ ] Admin 페이지에서 모델 확인

- [ ] **YOLO 커스텀 학습**
  - [ ] 실제 도면 데이터셋 준비 (100+ 이미지)
  - [ ] 라벨링 (치수선, 치수값, 기호)
  - [ ] YOLO 학습 (mAP > 0.7)
  - [ ] Admin 페이지에서 모델 확인

- [ ] **학습 자동화**
  - [ ] `train_all_models.sh` 스크립트 작성
  - [ ] Admin 페이지에서 "학습 시작" 버튼 클릭으로 실행 가능
  - [ ] 학습 진행률 표시

### 선택 (추가 점수)

- [ ] **Docker 최적화**
  - [ ] Multi-stage build 개선
  - [ ] 이미지 크기 50% 감소
  - [ ] .dockerignore 최적화

- [ ] **환경 분리**
  - [ ] .env.development / production 분리
  - [ ] docker-compose 환경별 설정

- [ ] **모니터링** (Bonus)
  - [ ] Prometheus + Grafana 구성
  - [ ] 메트릭 대시보드
  - [ ] 알림 설정

---

## 🎯 100점 달성 기준

### 최종 점수 계산

**기본 점수** (92-95점):
- ✅ eDOCr2 GPU 전처리: +5점
- ✅ Skin Model XGBoost: +5점
- ✅ 웹 UI 통합: +10점
- ✅ 하드코딩 제거: +10점
- ✅ Mermaid 문서화: +5점
- ✅ 시스템 아키텍처: +10점
- ✅ 기본 기능 완성도: +47-50점

**추가 점수** (목표):
- 🎯 EDGNet 대규모 학습: +3점
- 🎯 YOLO 커스텀 학습: +2점
- 🎯 Docker 최적화: +1점
- 🎯 환경 분리: +1점
- 🎯 프로덕션 준비도: +1점

**합계**: 92-95점 + 5-8점 = **100점**

---

## ⏱️ 예상 소요 시간

### Phase 1: 대규모 학습 (필수)
- EDGNet 데이터 증강: 30분
- EDGNet 학습: 2-3시간 (GPU)
- YOLO 데이터 준비: 1시간
- YOLO 학습: 1-2시간 (GPU)
- **총 소요 시간**: 4.5-6.5시간

### Phase 2: 프로덕션 최적화 (선택)
- Docker 최적화: 1시간
- 환경 분리: 30분
- **총 소요 시간**: 1.5시간

**전체 예상 시간**: 6-8시간

---

## 🚦 우선순위

### 🔴 Critical (100점 필수)
1. **EDGNet 대규모 학습**
2. **YOLO 커스텀 학습**

### 🟡 Important (추가 점수)
3. Docker 이미지 최적화
4. 환경 분리

### 🟢 Nice to Have (Bonus)
5. Prometheus + Grafana 모니터링
6. CI/CD 파이프라인
7. 로그 수집 시스템

---

## 📝 다음 작업

**즉시 시작 가능한 작업**:

1. **EDGNet 데이터 증강**:
   ```bash
   cd /home/uproot/ax/poc/
   python scripts/augment_edgnet.py
   ```

2. **YOLO 데이터셋 준비**:
   ```bash
   cd /home/uproot/ax/poc/datasets/
   mkdir real_drawings_yolo/
   # 실제 도면 이미지 준비
   ```

3. **학습 스크립트 작성**:
   ```bash
   vim /home/uproot/ax/poc/scripts/train_all_models.sh
   chmod +x train_all_models.sh
   ```

**100점 달성까지 남은 작업: 대규모 데이터 학습만 완료하면 됩니다!** 🎯
