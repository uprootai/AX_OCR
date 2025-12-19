# 🔄 API 교체 가이드

> 기존 API를 새로운 구현체로 완전히 교체하는 방법

---

## 📋 목차

1. [교체 방법 비교](#교체-방법-비교)
2. [물리적 교체 (컨테이너 교체)](#물리적-교체)
3. [논리적 교체 (Dashboard 추가)](#논리적-교체)
4. [자주 묻는 질문](#자주-묻는-질문)

---

## 🎯 교체 방법 비교

### 1️⃣ 물리적 교체 (컨테이너 교체)

**언제 사용:**
- 기존 YOLO API를 완전히 다른 구현체로 교체
- API 엔드포인트는 동일하게 유지 (`/api/v1/detect`)
- 기존 시스템과의 완전한 호환성 유지

**장점:**
- ✅ 기존 시스템 수정 불필요
- ✅ Gateway API가 자동으로 인식
- ✅ BlueprintFlow에서 기존 노드 그대로 사용

**단점:**
- ⚠️ Docker 재빌드 필요 (5-10분)
- ⚠️ API 호환성 유지 필요
- ⚠️ 서비스 재시작 필요

### 2️⃣ 논리적 교체 (Dashboard 추가)

**언제 사용:**
- 기존 API와 새 API를 동시에 사용
- 완전히 다른 엔드포인트/포트 사용
- 실험적 모델 테스트

**장점:**
- ✅ 코드 수정 없음
- ✅ 1분 내 즉시 사용
- ✅ 기존 API 유지 (롤백 용이)

**단점:**
- ⚠️ 새 API 서버 별도 구축 필요
- ⚠️ 포트 추가 필요

---

## 🔧 물리적 교체 (컨테이너 교체)

### 대상 디렉토리 구조

```
/home/uproot/ax/poc/models/
├── yolo-api/              ← YOLO API 교체 시
│   ├── Dockerfile         ← 새 도커 이미지 정의
│   ├── api_server.py      ← FastAPI 엔드포인트 (형식 유지)
│   ├── services/
│   │   └── inference.py   ← 새 추론 로직
│   ├── models/
│   │   └── best.pt        ← 새 모델 가중치
│   ├── requirements.txt   ← 새 의존성
│   └── docker-compose.single.yml
│
├── paddleocr-api/         ← PaddleOCR API 교체 시
│   ├── Dockerfile
│   ├── api_server.py
│   ├── services/
│   │   └── ocr.py         ← 새 OCR 로직
│   └── ...
│
├── edgnet-api/            ← EDGNet API 교체 시
├── skinmodel-api/         ← SkinModel API 교체 시
└── ...                    ← 나머지 API들
```

---

## 📝 교체 절차 (예: YOLO API)

### Step 1: 백업

현재 작동 중인 API를 백업합니다.

**명령어:**
```bash
cd /home/uproot/ax/poc/models
cp -r yolo-api yolo-api.backup
```

**결과:** `yolo-api.backup` 디렉토리에 원본 보관

---

### Step 2: 서비스 중지

교체할 API 컨테이너를 중지합니다.

**전체 시스템 실행 중인 경우:**
```bash
cd /home/uproot/ax/poc
docker-compose stop yolo-api
```

**개별 실행 중인 경우:**
```bash
cd /home/uproot/ax/poc/models/yolo-api
docker-compose -f docker-compose.single.yml down
```

**확인:** 컨테이너 목록에서 yolo-api가 사라졌는지 확인

---

### Step 3: 파일 교체

새로운 도커라이징된 API를 해당 디렉토리에 복사합니다.

**방법 1: 파일 직접 교체**
```bash
cd /home/uproot/ax/poc/models/yolo-api

# 새 파일들을 복사
cp /path/to/new/api/* ./

# 또는 전체 디렉토리 교체
cd /home/uproot/ax/poc/models
rm -rf yolo-api
cp -r /path/to/new/yolo-api ./
```

**방법 2: USB/외장 HDD에서 복사**
```bash
# USB 마운트 확인
ls /mnt/usb/

# 압축 파일인 경우
cd /home/uproot/ax/poc/models
tar -xzf /mnt/usb/yolo-api-new.tar.gz
mv yolo-api-new yolo-api
```

---

### Step 4: API 호환성 확인

새 API가 기존 엔드포인트 형식을 준수하는지 확인합니다.

**필수 요구사항:**

#### ✅ YOLO API 엔드포인트
```
POST /api/v1/detect
POST /api/v1/health (헬스체크)
```

**요청 형식:**
- Content-Type: `multipart/form-data`
- 파라미터: `file` (이미지 파일), `conf`, `iou`, `imgsz` 등

**응답 형식:**
```json
{
  "success": true,
  "detections": [...],
  "processing_time": 1.23,
  "visualization": "base64_string"
}
```

#### ✅ PaddleOCR API 엔드포인트
```
POST /api/v1/ocr
POST /health (헬스체크)
```

**요청 형식:**
- Content-Type: `multipart/form-data`
- 파라미터: `file` (이미지 파일), `lang`, `use_angle_cls` 등

---

### Step 5: Docker 이미지 재빌드

새로운 Dockerfile로 이미지를 빌드합니다.

**캐시 없이 빌드 (권장):**
```bash
cd /home/uproot/ax/poc/models/yolo-api
docker build --no-cache -t yolo-api:latest .
```

**또는 전체 시스템 재빌드:**
```bash
cd /home/uproot/ax/poc
docker-compose build yolo-api
```

**예상 소요 시간:** 5-10분

---

### Step 6: 서비스 재시작

새로운 이미지로 컨테이너를 시작합니다.

**전체 시스템:**
```bash
cd /home/uproot/ax/poc
docker-compose up -d yolo-api
```

**개별 실행:**
```bash
cd /home/uproot/ax/poc/models/yolo-api
docker-compose -f docker-compose.single.yml up -d
```

**로그 확인:**
```bash
docker logs yolo-api -f
```

**성공 메시지:** "Application startup complete"

---

### Step 7: 동작 확인

새 API가 정상적으로 작동하는지 테스트합니다.

**헬스체크:**
```bash
curl http://localhost:5005/api/v1/health
```

**예상 응답:**
```json
{
  "status": "healthy",
  "model": "새로운 모델명",
  "version": "x.x.x"
}
```

**추론 테스트:**
```bash
curl -X POST http://localhost:5005/api/v1/detect \
  -F "file=@/path/to/test-image.jpg" \
  -F "conf=0.25"
```

**Gateway 통합 테스트:**
```bash
curl http://localhost:8000/api/v1/health
```

Gateway API 응답에서 yolo 서비스가 "healthy"로 표시되어야 합니다.

---

### Step 8: 롤백 (문제 발생 시)

새 API에 문제가 있으면 백업으로 복원합니다.

**백업 복원:**
```bash
cd /home/uproot/ax/poc/models

# 현재 실행 중지
docker-compose -f docker-compose.single.yml down

# 백업 복원
rm -rf yolo-api
cp -r yolo-api.backup yolo-api

# 재시작
docker-compose -f docker-compose.single.yml up -d
```

---

## 🆕 논리적 교체 (Dashboard 추가)

### 개요

기존 API를 유지하면서 새로운 API를 추가하여 사용하는 방법입니다.

**상세 가이드:** `DYNAMIC_API_SYSTEM_GUIDE.md` 참조

### 간단 요약

1. **새 API 서버 구축**
   - 다른 포트에서 실행 (예: 5007)
   - Docker로 독립 실행

2. **Dashboard에서 추가**
   - `http://localhost:5173/dashboard` 접속
   - "Add Custom API" 클릭
   - API Config JSON 입력

3. **BlueprintFlow에서 사용**
   - 노드 팔레트에 자동 추가
   - 기존 YOLO 노드 대신 새 노드 사용

---

## ❓ 자주 묻는 질문

### Q1: PaddleOCR API도 동일한 방법으로 교체하나요?

**A:** 네, 완전히 동일합니다.

**디렉토리:**
```
/home/uproot/ax/poc/models/paddleocr-api/
```

**엔드포인트 유지:**
- `POST /api/v1/ocr`
- `POST /health`

**재빌드 및 재시작:**
```bash
cd /home/uproot/ax/poc
docker-compose build paddleocr-api
docker-compose up -d paddleocr-api
```

---

### Q2: 모델 가중치만 교체하려면?

**A:** 훨씬 간단합니다. 재빌드 불필요!

**YOLO 모델 교체:**
```bash
# 1. 모델 디렉토리로 이동
cd /home/uproot/ax/poc/models/yolo-api/models

# 2. 새 모델 복사 (best.pt 이름 유지)
cp /path/to/new-model.pt ./best.pt

# 3. 컨테이너만 재시작
docker-compose restart yolo-api
```

**PaddleOCR:** 모델 자동 다운로드되므로 교체 불필요

---

### Q3: 여러 버전을 동시에 사용하려면?

**A:** 3가지 방법이 있으며, 각각 다른 상황에 적합합니다.

#### 📊 방법 비교

| 방법 | 사용 사례 | 난이도 | 시간 | 메모리 |
|------|----------|--------|------|--------|
| **방법 1: 여러 포트 분리** | 완전히 다른 YOLO 버전 (v8, v11) | ⭐⭐⭐ | 30분 | 높음 |
| **방법 2: Dashboard 등록** | 실험용 모델 추가 테스트 | ⭐ | 1분 | 중간 |
| **방법 3: 모델 파일 교체** | 같은 버전, 다른 학습 가중치 | ⭐ | 즉시 | 낮음 |

---

#### ✅ **방법 1: 여러 포트로 분리 실행 (권장)**

**언제 사용**: YOLOv8, YOLOv11처럼 완전히 다른 버전을 동시에 유지하고 싶을 때

**디렉토리 구조**:
```
/home/uproot/ax/poc/models/
├── yolo-api/              ← YOLOv11 (기본, 포트 5005)
├── yolo-v8-api/           ← YOLOv8 (추가, 포트 5007)
└── yolo-nano-api/         ← YOLO Nano (경량, 포트 5008)
```

**절차 요약**:
1. 기존 yolo-api 디렉토리를 복사하여 새 이름으로 생성
2. docker-compose.single.yml에서 포트 번호 변경 (5007, 5008 등)
3. container_name을 고유하게 변경
4. 각 디렉토리에서 독립적으로 Docker Compose 실행
5. Dashboard에서 각 API를 등록하거나 Gateway 설정에 추가

**결과**:
- BlueprintFlow에서 "YOLO v11", "YOLO v8", "YOLO Nano" 노드 각각 사용 가능
- 속도 vs 정확도 트레이드오프 테스트 가능

**장점**: 각 모델 완전 독립, 버전별 의존성 충돌 없음
**단점**: 메모리 사용량 증가 (각 모델이 별도 메모리 차지)

---

#### ⚡ **방법 2: Dashboard 동적 등록 (가장 쉬움)**

**언제 사용**: 임시로 새 모델을 추가하거나, 코드 수정 없이 빠르게 테스트하고 싶을 때

**절차 요약**:
1. 새 YOLO API 서버를 다른 포트에서 실행 (예: 5009)
2. Dashboard 접속 → "Add Custom API" 클릭
3. API Config JSON 입력 (endpoint, parameters 등)
4. BlueprintFlow 노드 팔레트에 자동 추가

**API Config 예시**:
```
이름: YOLO-Nano-Fast
엔드포인트: http://host.docker.internal:5009/api/v1/detect
설명: 초경량 YOLO Nano 모델 - 빠른 속도
파라미터: conf, iou 등
```

**장점**: 1분 내 즉시 추가, 코드 수정 불필요
**단점**: 별도 API 서버 필요

**상세 가이드**: DYNAMIC_API_SYSTEM_GUIDE.md 참조

---

#### 🔧 **방법 3: 모델 가중치만 교체 (동일 버전)**

**언제 사용**: YOLO 버전은 같은데, 다른 데이터셋으로 학습된 여러 모델을 번갈아 사용하고 싶을 때

**예시 시나리오**:
- 일반 물체 감지용 모델 (best.pt)
- 도면 전용 학습 모델 (drawing-best.pt)
- 특정 산업용 모델 (industrial-best.pt)

**절차 요약**:
1. models/ 디렉토리에 여러 .pt 파일 보관
2. 현재 best.pt를 백업
3. 사용하려는 모델을 best.pt로 이름 변경
4. Docker 컨테이너 재시작 (10초 소요)

**장점**: 가장 빠르고 간단, 재빌드 불필요, 메모리 절약
**단점**: 동시에 여러 모델 사용 불가, 수동 교체 필요

---

#### 🎯 추천 시나리오

**시나리오 1: 프로덕션 + 실험**
- 방법 1: YOLOv11 (프로덕션, 포트 5005) ← 안정적 운영
- 방법 2: 새 모델 (실험, Dashboard 등록) ← 빠른 테스트

**시나리오 2: 속도 vs 정확도 선택**
- 방법 1: YOLO Nano (포트 5007) ← 실시간 처리용
- 방법 1: YOLO v11 Large (포트 5005) ← 고정밀 분석용

**시나리오 3: 용도별 특화 모델**
- 일반 물체 감지 (포트 5005)
- 도면 전용 모델 (포트 5007)
- 결함 검출 모델 (포트 5008)

**핵심**: 새 API 추가 = 새 포트 할당 = 독립적인 마이크로서비스

---

### Q4: API 호환성을 어떻게 확인하나요?

**A:** Swagger UI로 확인

```bash
# 브라우저에서 접속
http://localhost:5005/docs  # YOLO API
http://localhost:5006/docs  # PaddleOCR API
```

**확인 사항:**
- 엔드포인트 경로 동일
- 요청 파라미터 타입 동일
- 응답 구조 동일

---

### Q5: 교체 후 BlueprintFlow 워크플로우는?

**A:** 자동으로 계속 작동합니다.

**이유:**
- API 엔드포인트가 동일하면 호환성 유지
- Gateway API가 자동으로 새 API 사용
- 저장된 워크플로우 수정 불필요

**확인:**
```bash
# BlueprintFlow 워크플로우 테스트
curl -X POST http://localhost:8000/api/v1/workflow/execute \
  -F "workflow=@my-workflow.json" \
  -F "file=@test.jpg"
```

---

### Q6: 교체 실패 시 시스템이 멈추나요?

**A:** 아니요, 다른 API는 정상 작동합니다.

**이유:**
- 마이크로서비스 아키텍처
- 각 API 독립 실행
- Gateway가 실패한 API 자동 감지

**확인:**
```bash
curl http://localhost:8000/api/v1/health
```

**응답 예시:**
```json
{
  "status": "degraded",
  "services": {
    "yolo": "unhealthy",      ← 교체 실패
    "edocr2": "healthy",
    "edgnet": "healthy",
    "skinmodel": "healthy"
  }
}
```

---

## 📚 관련 문서

- **DYNAMIC_API_SYSTEM_GUIDE.md** - Dashboard를 통한 API 추가
- **DEPLOYMENT_GUIDE.md** - 개별 API 배포 방법
- **TROUBLESHOOTING.md** - API 관련 문제 해결

---

## 🎯 요약

### 빠른 참조

| 교체 대상 | 디렉토리 | 엔드포인트 | 포트 |
|----------|---------|-----------|------|
| YOLO | `/models/yolo-api/` | `/api/v1/detect` | 5005 |
| PaddleOCR | `/models/paddleocr-api/` | `/api/v1/ocr` | 5006 |
| eDOCr2 v1 | `/models/edocr2-api/` | `/api/v1/ocr` | 5001 |
| eDOCr2 v2 | `/models/edocr2-v2-api/` | `/api/v2/ocr` | 5002 |
| EDGNet | `/models/edgnet-api/` | `/api/v1/segment` | 5012 |
| SkinModel | `/models/skinmodel-api/` | `/api/v1/predict` | 5003 |
| VL API | `/models/vl-api/` | `/api/v1/analyze` | 5004 |

### 교체 체크리스트

- [ ] 백업 생성 완료
- [ ] 서비스 중지 완료
- [ ] 파일 교체 완료
- [ ] API 호환성 확인 완료
- [ ] Docker 이미지 재빌드 완료
- [ ] 서비스 재시작 완료
- [ ] 헬스체크 통과
- [ ] 추론 테스트 통과
- [ ] Gateway 통합 테스트 통과

---

**작성일:** 2025-11-21
**버전:** 1.0.0
