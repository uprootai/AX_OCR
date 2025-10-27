# 빠른 시작 가이드

AX 실증산단 마이크로서비스 API 시스템 - 5분 안에 시작하기

## 📋 사전 요구사항

- Docker 20.10+ 설치
- Docker Compose 2.0+ 설치
- 최소 8GB RAM
- 샘플 도면 파일 (선택사항)

## 🚀 1단계: 전체 시스템 실행

```bash
# POC 디렉토리로 이동
cd /home/uproot/ax/poc

# 전체 시스템 빌드 및 실행 (최초 1회, 5-10분 소요)
docker-compose up -d --build

# 또는 이미 빌드된 경우
docker-compose up -d
```

## ⏱️ 2단계: 서비스 준비 대기

```bash
# 로그 확인 (모든 서비스가 "Application startup complete" 표시될 때까지 대기)
docker-compose logs -f

# Ctrl+C로 로그 종료
```

**예상 대기 시간**: 약 1-2분

## ✅ 3단계: 헬스체크

```bash
# 전체 시스템 상태 확인
curl http://localhost:8000/api/v1/health
```

**성공 응답**:
```json
{
  "status": "healthy",
  "services": {
    "edocr2": "healthy",
    "edgnet": "healthy",
    "skinmodel": "healthy"
  }
}
```

## 🧪 4단계: 자동 테스트 실행

### 방법 1: Bash 스크립트 (권장)

```bash
./test_apis.sh
```

### 방법 2: Python 스크립트

```bash
python3 test_apis.py
```

**예상 결과**:
```
=========================================
AX 실증산단 API 시스템 테스트
=========================================

1. Health Check Tests
-------------------------------------------
Testing eDOCr2 API... ✓ PASS (HTTP 200)
Testing EDGNet API... ✓ PASS (HTTP 200)
Testing Skin Model API... ✓ PASS (HTTP 200)
Testing Gateway API... ✓ PASS (HTTP 200)

...

✓ 모든 테스트 통과!
```

## 📝 5단계: API 문서 확인

브라우저에서 다음 URL 접속:

- **Gateway API (통합)**: http://localhost:8000/docs
- **eDOCr2 API (OCR)**: http://localhost:5001/docs
- **EDGNet API (세그멘테이션)**: http://localhost:5002/docs
- **Skin Model API (공차 예측)**: http://localhost:5003/docs

## 🎨 6단계: 실제 도면 처리

### 샘플 도면 준비

```bash
# 샘플 도면 경로
DRAWING="/home/uproot/ax/reference/02. 수요처 및 도메인 자료/2. 도면(샘플)/A12-311197-9 Rev.2 Interm Shaft-Acc_y_1.jpg"
```

### 전체 파이프라인 실행

```bash
curl -X POST http://localhost:8000/api/v1/process \
  -F "file=@$DRAWING" \
  -F "use_segmentation=true" \
  -F "use_ocr=true" \
  -F "use_tolerance=true" \
  -F "visualize=true" \
  > result.json

# 결과 확인
cat result.json | python3 -m json.tool
```

### 견적서 생성

```bash
curl -X POST http://localhost:8000/api/v1/quote \
  -F "file=@$DRAWING" \
  -F "material_cost_per_kg=5.0" \
  -F "machining_rate_per_hour=50.0" \
  > quote.json

# 견적 확인
cat quote.json | python3 -m json.tool
```

## 🛠️ 문제 해결

### 서비스가 시작되지 않을 때

```bash
# 모든 컨테이너 중지
docker-compose down

# 볼륨까지 삭제 (완전 초기화)
docker-compose down -v

# 다시 시작
docker-compose up -d --build
```

### 특정 서비스 오류 확인

```bash
# 개별 서비스 로그
docker logs edocr2-api
docker logs edgnet-api
docker logs skinmodel-api
docker logs gateway-api
```

### 포트 충돌

```bash
# 사용 중인 포트 확인
sudo lsof -i :5001
sudo lsof -i :5002
sudo lsof -i :5003
sudo lsof -i :8000

# 프로세스 종료
sudo kill -9 <PID>
```

## 📊 시스템 상태 모니터링

### 실시간 로그 확인

```bash
# 전체 시스템
docker-compose logs -f

# 특정 서비스만
docker-compose logs -f gateway-api
```

### 리소스 사용량

```bash
docker stats
```

### 컨테이너 상태

```bash
docker-compose ps
```

## 🛑 시스템 중지

```bash
# 컨테이너 중지 (데이터 보존)
docker-compose stop

# 컨테이너 삭제 (데이터 보존)
docker-compose down

# 완전 삭제 (볼륨까지)
docker-compose down -v
```

## 🔄 시스템 재시작

```bash
# 중지 후 재시작
docker-compose restart

# 특정 서비스만 재시작
docker-compose restart gateway-api
```

## 📚 다음 단계

1. **API 문서 탐색**: http://localhost:8000/docs
2. **개별 README 읽기**:
   - `edocr2-api/README.md`
   - `edgnet-api/README.md`
   - `skinmodel-api/README.md`
   - `gateway-api/README.md`
3. **Python/JavaScript 클라이언트 작성**: 각 README의 예제 코드 참고
4. **실제 도면으로 테스트**: 자체 도면 파일 업로드

## ⚡ 빠른 명령어 모음

```bash
# 시스템 시작
docker-compose up -d

# 상태 확인
curl http://localhost:8000/api/v1/health

# 테스트
./test_apis.sh

# 로그 확인
docker-compose logs -f

# 중지
docker-compose stop

# 재시작
docker-compose restart
```

## 💡 팁

1. **처음 빌드는 시간이 걸립니다** (5-10분): 캐시 후에는 빠름
2. **모든 서비스가 healthy 상태**가 될 때까지 기다리세요
3. **샘플 도면으로 먼저 테스트**해보세요
4. **Swagger UI**에서 대화형으로 API 테스트 가능

## 🆘 도움이 필요하신가요?

- **이슈**: https://github.com/uproot/ax-poc/issues
- **이메일**: dev@uproot.com
- **문서**: 각 서비스 디렉토리의 README.md

---

**준비 완료!** 🎉

이제 `docker-compose up -d` 명령어 하나로 전체 시스템을 실행하고,
`curl http://localhost:8000/docs`에서 API를 탐색할 수 있습니다.
