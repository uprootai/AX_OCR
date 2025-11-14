# 📋 남은 작업 및 개선 계획

**작성일**: 2025-11-14
**현재 점수**: 90/100
**목표 점수**: 95-100/100

---

## ✅ 현재 시스템 상태 (확인 완료)

### GPU 상태
```
✅ GPU: RTX 3080 Laptop (정상 작동)
✅ VRAM: 1688 MB / 8192 MB (20.6% 사용)
✅ 온도: 38°C (안정)
✅ YOLO GPU 가속 활성화
```

### API 상태 (모두 정상)
```
✅ eDOCr2 API      - 5001 포트 (정상)
✅ EDGNet API      - 5012 포트 (정상)
✅ Skin Model API  - 5003 포트 (정상)
✅ VL API          - 5004 포트 (정상)
✅ YOLO API        - 5005 포트 (정상, GPU 활성화)
✅ Gateway API     - 8000 포트 (정상)
```

### YOLO 성능 (GPU 가속 확인됨)
```
✅ 처리 시간: 0.31초 ⚡ (매우 빠름!)
✅ 검출 개수: 76개
✅ GPU 사용: 활성화됨
```

---

## 🚀 남은 개선 작업 (우선순위별)

### Priority 1: 즉시 실행 가능 (+10점) - EDGNet 재학습

**목표**: 75점 → 85점 (+10점)
**소요 시간**: 1-2시간
**난이도**: ⭐⭐ (중간)

#### 작업 순서

**1단계: 그래프 데이터 증강 스크립트 수정**
```bash
# 현재 문제: 스크립트가 drawings/*.json을 찾지만 실제는 루트에 있음
# 해결: 스크립트 수정 필요

# 필요 작업:
# - edgnet_dataset/*.json 파일을 drawings/ 폴더와 매칭
# - 그래프 구조를 7가지 변형으로 복제
# - 메타데이터 업데이트
```

**2단계: 데이터 증강 실행**
```bash
cd /home/uproot/ax/poc
python3 scripts/augment_edgnet_dataset.py

# 예상 결과:
# - 원본: 2개 도면
# - 증강 후: 14개 도면 (7배)
# - 165 노드 → 1,155 노드
```

**3단계: GPU 재학습**
```bash
python3 scripts/retrain_edgnet_gpu.py

# 예상:
# - 학습 시간: 10-20분 (GPU)
# - 모델 크기: ~50 MB
# - VRAM 사용: +1200 MB
```

**4단계: EDGNet API 업데이트**
```bash
# 새 모델을 EDGNet API에 적용
# edgnet-api/api_server.py 수정
# docker-compose restart edgnet-api
```

**예상 효과**:
- EDGNet: 75 → 85점 (+10점)
- 전체: 90 → 92점 (+2점)

---

### Priority 2: 1주일 내 (+10점) - 추가 최적화

#### A. eDOCr2 GPU 전처리 (+5점)

**목표**: 95점 → 100점
**소요 시간**: 1-2일
**난이도**: ⭐⭐⭐ (어려움)

**필요 작업**:
```bash
# 1. cuPy 설치
pip3 install cupy-cuda12x

# 2. GPU 이미지 전처리 구현
# edocr2-api/gpu_preprocessing.py 생성:
# - CLAHE (대비 향상)
# - Gaussian blur (노이즈 제거)
# - Adaptive thresholding
# - GPU 메모리 관리

# 3. API 통합
# edocr2-api/api_server.py 수정

# 4. Docker GPU 설정
# docker-compose.yml에 eDOCr2 GPU 추가
```

**예상 효과**:
- 처리 시간: 23초 → 5-8초 (3-5배)
- 점수: 95 → 100점 (+5점)
- VRAM 사용: +3500 MB

---

#### B. Skin Model XGBoost 업그레이드 (+5점)

**목표**: 85점 → 90-95점
**소요 시간**: 1일
**난이도**: ⭐⭐ (중간)

**필요 작업**:
```bash
# 1. XGBoost 설치
pip3 install xgboost

# 2. 업그레이드 스크립트 작성
# scripts/upgrade_skinmodel_xgboost.py:
# - RandomForest 모델 로드
# - 학습 데이터 추출
# - XGBoost GPU 학습
# - 모델 저장

# 3. API 업데이트
# skinmodel-api/ml_predictor.py 수정
# XGBoost 모델 로드

# 4. 테스트
# 정확도 비교 (R² score)
```

**예상 효과**:
- 학습 시간: 2분 → 20초 (6배)
- 정확도: R²=0.90 → R²=0.95
- 점수: 85 → 90점 (+5점)

---

#### C. Gateway 모니터링 추가 (+2점)

**목표**: 90점 → 92점
**소요 시간**: 3-4시간
**난이도**: ⭐⭐ (중간)

**필요 작업**:
```bash
# 1. docker-compose.monitoring.yml 생성
# Prometheus + Grafana 컨테이너 추가

# 2. Gateway API에 메트릭 엔드포인트 추가
# - /metrics (Prometheus 형식)
# - 요청 수, 응답 시간, 에러율 등

# 3. Grafana 대시보드 설정
# - API 성능 모니터링
# - GPU 사용률 모니터링
```

**예상 효과**:
- 운영 가시성 향상
- 성능 병목 지점 파악
- 점수: 90 → 92점 (+2점)

---

### Priority 3: 장기 계획 (+10점) - 대규모 학습

#### A. 실측 데이터 수집 (Skin Model)

**목표**: 85점 → 95-100점
**소요 시간**: 2-3주
**난이도**: ⭐⭐⭐⭐ (매우 어려움)

**필요 데이터**:
- 실제 가공 부품: 20-50개
- 측정 항목:
  - 평탄도 (flatness)
  - 원통도 (cylindricity)
  - 위치도 (position)
  - 수직도 (perpendicularity)

**데이터 예시**:
```csv
diameter,length,material,process,flatness_measured,cylindricity_measured
50.0,100.0,Steel,machining,0.015,0.018
75.0,150.0,Aluminum,machining,0.012,0.014
...
```

**효과**: 합성 데이터 → 실측 데이터로 정확도 크게 향상

---

#### B. 대규모 EDGNet 학습

**목표**: 85점 → 95-100점
**소요 시간**: 1-2개월
**난이도**: ⭐⭐⭐⭐⭐ (매우 어려움)

**필요 데이터**:
- 실제 공학 도면: 50-100개
- 각 도면의 그래프 구조 생성
- YOLO로 자동 라벨링 가능

**효과**: 범용성과 정확도 대폭 향상

---

## 📊 단계별 점수 로드맵

```
현재 (Day 0):
├─ 점수: 90/100
├─ YOLO GPU 완료
└─ 모든 시스템 정상

Week 1 (EDGNet 재학습):
├─ 점수: 92/100 (+2점)
├─ EDGNet: 75 → 85점
└─ 소요 시간: 2시간

Week 2 (추가 최적화):
├─ 점수: 95/100 (+3점)
├─ eDOCr2 GPU: +5점
├─ Skin Model XGBoost: +5점
├─ Gateway 모니터링: +2점
└─ 소요 시간: 3-4일

Month 1 (대규모 학습):
├─ 점수: 98-100/100 (+3-5점)
├─ 실측 데이터 수집
├─ 대규모 EDGNet 학습
└─ 소요 시간: 2-4주
```

---

## 💡 빠른 승리 (Quick Wins)

### 오늘 중 (30분)

**1. YOLO 추가 테스트**
```bash
# 여러 도면으로 성능 확인
for img in /home/uproot/ax/poc/edgnet_dataset/drawings/*.jpg; do
  echo "Testing: $(basename "$img")"
  curl -s -X POST http://localhost:5005/api/v1/detect \
    -F "file=@$img" -F "visualize=false" | \
    python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  검출: {d[\"total_detections\"]}개, 시간: {d[\"processing_time\"]:.2f}초')"
done
```

**2. GPU 메모리 모니터링 설정**
```bash
# 실시간 모니터링
watch -n 1 nvidia-smi

# 로그 저장
nvidia-smi dmon -s pucvmet -o TD > gpu_usage.log &
```

---

### 내일 (2-3시간)

**EDGNet 증강 스크립트 수정**
```python
# scripts/augment_edgnet_dataset.py 수정
# - drawings/*.json 대신 루트 *.json 사용
# - 이미지와 그래프 데이터 매칭
# - 7가지 변형 생성
```

---

## 🎯 권장 실행 순서

### 최소 노력으로 최대 효과

**Week 1**:
1. ✅ EDGNet 재학습 (+10점) → **92점**
2. Gateway 모니터링 (+2점) → **94점**

**Week 2**:
3. Skin Model XGBoost (+5점) → **97점**

**Optional**:
4. eDOCr2 GPU (+5점) → **100점**
5. 실측 데이터 수집 (정확도 향상)

---

## 📁 필요한 파일 현황

### ✅ 이미 생성됨
- `scripts/retrain_edgnet_gpu.py` - EDGNet GPU 학습
- `scripts/augment_edgnet_dataset.py` - 데이터 증강 (수정 필요)
- `edgnet_dataset/drawings/` - 2개 이미지 준비됨

### ⏳ 생성 필요
- `scripts/upgrade_skinmodel_xgboost.py` - XGBoost 업그레이드
- `docker-compose.monitoring.yml` - 모니터링 스택
- `edocr2-api/gpu_preprocessing.py` - GPU 전처리

---

## 🔍 확인 사항

### 현재 시스템 검증 ✅

```bash
# 1. GPU 정상 작동
nvidia-smi
# ✅ RTX 3080 Laptop, 1688 MB / 8192 MB

# 2. YOLO GPU 활성화
docker-compose logs yolo-api | grep GPU
# ✅ GPU available: NVIDIA GeForce RTX 3080 Laptop GPU

# 3. 모든 API 정상
curl -s http://localhost:5005/api/v1/health | grep healthy
# ✅ {"status":"healthy"}

# 4. 성능 확인
# ✅ 0.31초 (매우 빠름!)
```

---

## 🏆 최종 목표

### 2주 내 95점 달성

**Phase 1 (완료)**: YOLO GPU → **90점** ✅
**Phase 2 (1주)**: EDGNet + 최적화 → **95점**
**Phase 3 (선택)**: 대규모 학습 → **100점**

---

## 📞 다음 단계

### 지금 바로 할 수 있는 것

1. **시스템 사용 시작**
   - YOLO API는 이미 6배 빠름
   - 모든 기능 정상 작동

2. **추가 테스트**
   - 다양한 도면으로 YOLO 테스트
   - 성능 벤치마크 수집

3. **문서 검토**
   - `FINAL_GPU_OPTIMIZATION_REPORT.md` 읽기
   - 향후 계획 검토

### 다음 작업 시작하려면

"EDGNet 재학습을 진행하겠습니다" 라고 말씀해주세요.

---

**현재 상태**: ✅ **안정적으로 작동 중**
**점수**: 90/100
**다음 목표**: 92점 (EDGNet 재학습)
**예상 소요**: 2시간

**모든 시스템이 정상 작동하고 있으며, 원하시는 때에 추가 작업을 진행할 수 있습니다!** 🚀
