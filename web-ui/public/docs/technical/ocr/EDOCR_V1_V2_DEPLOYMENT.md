# eDOCr v1/v2 이중 배포 가이드

**작성일**: 2025-10-29
**버전**: 1.1
**상태**: ✅ v1 완료, ✅ v2 완료 및 운영 중

---

## 📋 개요

eDOCr OCR 서비스를 v1과 v2로 분리하여 각각 다른 포트에서 실행합니다.

### 주요 차이점

| 항목 | v1 | v2 |
|------|----|----|
| **포트** | 5001 | 5002 |
| **엔드포인트** | `/api/v1/*` | `/api/v2/*` |
| **라이브러리** | eDOCr v1 | edocr2 v2 |
| **모델 파일** | `.h5` (Keras 2.x) | `.keras` (Keras 3.x) |
| **테이블 OCR** | ❌ | ✅ |
| **세그멘테이션** | `box_tree.findrect` | `layer_segm.segment_img` |
| **처리 시간** | ~36초 (CPU) | ~45-60초 (CPU) |
| **모델 크기** | 200MB | 136MB |

---

## 🚀 배포 상태

### ✅ v1 - 완전 작동 중

**파일**:
- `api_server_edocr_v1.py`
- `Dockerfile.v1`
- `requirements_v1.txt`

**Docker 이미지**: `edocr-api:v1` (5.63GB)

**Health Check**:
```bash
curl http://localhost:5001/api/v1/health
```

**응답 예시**:
```json
{
  "status": "healthy",
  "service": "eDOCr v1 API",
  "version": "1.0.0",
  "edocr_available": true,
  "models_loaded": true
}
```

**주요 기능**:
- ✅ 치수 추출 (Dimensions)
- ✅ GD&T 추출
- ✅ 텍스트 인포블록 추출
- ✅ 시각화
- ✅ UI 형식 변환 완료

### ✅ v2 - 완전 작동 중

**파일**:
- `api_server_edocr_v2.py` ✅
- `Dockerfile.v2` ✅
- `requirements_v2.txt` ✅

**Docker 이미지**: `edocr-api:v2` (11GB) ✅

**Health Check**:
```bash
curl http://localhost:5002/api/v2/health
```

**응답 예시**:
```json
{
  "status": "healthy",
  "service": "eDOCr v2 API",
  "version": "2.0.0",
  "edocr2_available": true,
  "models_loaded": true
}
```

**주요 기능**:
- ✅ 치수 추출 (Dimensions)
- ✅ GD&T 추출
- ✅ 텍스트 인포블록 추출
- ✅ **테이블 OCR** (v2 전용)
- ✅ 고급 세그멘테이션
- ✅ UI 형식 변환 완료

---

## 📦 모델 파일

**위치**: `/home/uproot/ax/poc/edocr2-api/models/`

### v1 모델 (자동 다운로드)
```
~/.keras-ocr/recognizer_infoblock.h5 (67MB)
~/.keras-ocr/recognizer_dimensions.h5 (67MB)
~/.keras-ocr/recognizer_gdts.h5 (67MB)
```

**다운로드**: 컨테이너 시작 시 자동 (GitHub Releases)

### v2 모델 (수동 다운로드 완료)
```
models/recognizer_dimensions_2.keras (68MB) ✅
models/recognizer_dimensions_2.txt (42 bytes) ✅
models/recognizer_gdts.keras (68MB) ✅
models/recognizer_gdts.txt (85 bytes) ✅
```

**출처**: https://github.com/javvi51/edocr2/releases/tag/v1.0.0

**다운로드 명령어**:
```bash
cd /home/uproot/ax/poc/edocr2-api/models
curl -L -O https://github.com/javvi51/edocr2/releases/download/v1.0.0/recognizer_dimensions_2.keras
curl -L -O https://github.com/javvi51/edocr2/releases/download/v1.0.0/recognizer_dimensions_2.txt
curl -L -O https://github.com/javvi51/edocr2/releases/download/v1.0.0/recognizer_gdts.keras
curl -L -O https://github.com/javvi51/edocr2/releases/download/v1.0.0/recognizer_gdts.txt
```

**중요**: v2는 `.keras` 모델 파일과 함께 alphabet 정의 `.txt` 파일이 반드시 필요합니다.

---

## 🐳 Docker 배포

### 단일 버전 실행

**v1만 실행**:
```bash
cd /home/uproot/ax/poc/edocr2-api
docker-compose up -d  # 기본 docker-compose.yml 사용
```

**v2만 실행** (빌드 완료 후):
```bash
docker run -d \
  --name edocr2-api-v2 \
  -p 5002:5002 \
  -v $(pwd)/models:/app/models:ro \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/results:/app/results \
  edocr-api:v2
```

### 이중 버전 실행 (v1 + v2)

```bash
cd /home/uproot/ax/poc/edocr2-api
docker-compose -f docker-compose-dual.yml up -d
```

**포트**:
- v1: http://localhost:5001
- v2: http://localhost:5002

---

## 🧪 API 테스트

### v1 API 테스트

```bash
curl -X POST "http://localhost:5001/api/v1/ocr" \
  -F "file=@test.jpg" \
  -F "extract_dimensions=true" \
  -F "extract_gdt=true" \
  -F "extract_text=true"
```

### v2 API 테스트 (빌드 완료 후)

```bash
curl -X POST "http://localhost:5002/api/v2/ocr" \
  -F "file=@test.jpg" \
  -F "extract_dimensions=true" \
  -F "extract_gdt=true" \
  -F "extract_text=true" \
  -F "extract_tables=true"
```

**v2 추가 파라미터**:
- `extract_tables`: 테이블 OCR 활성화
- `language`: Tesseract 언어 코드 (기본: 'eng')

---

## 📊 응답 형식

### UI 호환 형식 (v1/v2 공통)

```json
{
  "status": "success",
  "data": {
    "dimensions": [
      {
        "type": "linear|diameter|radius",
        "value": 50.5,
        "unit": "mm",
        "tolerance": "+0.1/-0.05",
        "location": {"x": 100, "y": 200}
      }
    ],
    "gdt": [
      {
        "type": "⏤",
        "value": 0.05,
        "datum": "A",
        "location": {"x": 150, "y": 250}
      }
    ],
    "text": {
      "drawing_number": "DWG-001",
      "revision": "A",
      "title": "Part Drawing",
      "material": "Steel",
      "notes": ["Note 1", "Note 2"],
      "total_blocks": 5,
      "tables": []  // v2만 제공
    }
  },
  "processing_time": 36.5,
  "file_id": "20251029_120000_test.jpg",
  "version": "v1"  // or "v2"
}
```

---

## 🎮 GPU 지원

### 현재 상태
- GPU 하드웨어: ✅ NVIDIA GeForce (8GB VRAM, CUDA 12.6)
- Docker GPU 지원: ❌ 미설정

### GPU 활성화 방법 (향후)

**1. nvidia-docker 설치**:
```bash
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

**2. docker-compose 수정**:
```yaml
services:
  edocr2-v1:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

**3. 성능 향상 예상**:
- v1: 36초 → 10-15초 (3배 빠름)
- v2: 45-60초 → 15-20초 (3-4배 빠름)

---

## 🌐 Web UI 통합

### 현재 v1 연동 완료

**URL**: http://localhost:5173/test/edocr2

**UI 수정사항**:
- ✅ "eDOCr v1" 레이블 추가
- ✅ Version 1 뱃지 표시
- ✅ API 응답 형식 호환

### v2 연동 (향후)

**필요 작업**:
1. v2 전용 UI 페이지 생성 또는
2. 버전 선택 드롭다운 추가

**예시**:
```tsx
<select onChange={(e) => setVersion(e.target.value)}>
  <option value="v1">eDOCr v1 (빠름)</option>
  <option value="v2">eDOCr v2 (테이블 지원)</option>
</select>
```

---

## 📝 디렉토리 구조

```
edocr2-api/
├── models/                         # v2 모델 (공유)
│   ├── recognizer_dimensions_2.keras
│   └── recognizer_gdts.keras
├── uploads/                        # 업로드 파일 (임시)
├── results/                        # 결과 파일
├── api_server_edocr_v1.py         # v1 API 서버
├── api_server_edocr_v2.py         # v2 API 서버
├── requirements_v1.txt            # v1 의존성
├── requirements_v2.txt            # v2 의존성
├── Dockerfile.v1                  # v1 Docker 이미지
├── Dockerfile.v2                  # v2 Docker 이미지
├── docker-compose.yml             # v1 단독 실행
└── docker-compose-dual.yml        # v1 + v2 동시 실행
```

---

## 🐛 문제 해결

### v1 문제

**문제**: Pydantic 검증 오류
**해결**: ✅ `transform_edocr_to_ui_format()` 함수로 형식 변환

**문제**: NumPy 타입 JSON 직렬화 오류
**해결**: ✅ `convert_to_serializable()` 함수 추가

### v2 문제

**문제**: Alphabet 파일 없음 오류
```
FileNotFoundError: [Errno 2] No such file or directory: '/app/models/recognizer_gdts.txt'
```
**원인**: v2 모델은 `.keras` 파일 외에 alphabet 정의 `.txt` 파일이 필요
**해결**: ✅ GitHub Releases에서 `.txt` 파일 다운로드 (위의 "v2 모델" 섹션 참조)

**문제**: Tesseract 없음
**해결**: ✅ Dockerfile에 `tesseract-ocr` 포함됨

**문제**: Docker 빌드 시 패키지 오류
**해결**: ✅ Debian 패키지명 업데이트 (libgl1 사용)

---

## 📌 다음 단계

### ✅ 완료된 작업 (2025-10-29)

1. ✅ **v2 Docker 빌드 완료** - 11GB 이미지 생성
2. ✅ **v2 모델 다운로드** - .keras + .txt alphabet 파일
3. ✅ **v2 컨테이너 실행** - 포트 5002에서 정상 작동
4. ✅ **Docker Compose 이중 배포** - v1 + v2 동시 운영
5. ✅ **Health Check 통과** - 두 서비스 모두 정상

**현재 상태**:
```bash
# v1: http://localhost:5001/api/v1/health - healthy ✅
# v2: http://localhost:5002/api/v2/health - healthy ✅
```

**실행 명령어**:
```bash
cd /home/uproot/ax/poc/edocr2-api
docker-compose -f docker-compose-dual.yml up -d
```

### 단기 (1-2일)

- [ ] Web UI에 v2 통합
- [ ] 버전 선택 UI 추가
- [ ] 테이블 OCR 결과 표시

### 중기 (1주일)

- [ ] GPU 지원 활성화
- [ ] 성능 벤치마크 (CPU vs GPU)
- [ ] API Gateway 통합

### 장기

- [ ] 모델 최적화
- [ ] 배치 처리 지원
- [ ] 웹소켓 기반 실시간 진행률

---

## 📚 참고 자료

- **eDOCr v1**: https://github.com/javvi51/eDOCr
- **edocr2 v2**: https://github.com/javvi51/edocr2
- **논문 (v1)**: https://www.frontiersin.org/articles/10.3389/fmtec.2023.1154132/full
- **논문 (v2)**: http://dx.doi.org/10.2139/ssrn.5045921

---

**작성자**: Claude Code
**최종 수정**: 2025-10-29 03:15 UTC
**상태**: ✅ v1 + v2 이중 배포 완료 및 운영 중

## 🎯 배포 완료 요약

**Docker 이미지**:
- `edocr-api:v1` - 5.63GB (eDOCr v1, Keras 2.x)
- `edocr-api:v2` - 11GB (edocr2 v2, Keras 3.x)

**운영 중인 서비스**:
- v1 API: http://localhost:5001 (치수, GD&T, 텍스트)
- v2 API: http://localhost:5002 (치수, GD&T, 텍스트, 테이블)

**Docker Compose 관리**:
```bash
# 시작
docker-compose -f docker-compose-dual.yml up -d

# 상태 확인
docker-compose -f docker-compose-dual.yml ps

# 로그 확인
docker-compose -f docker-compose-dual.yml logs -f

# 중지
docker-compose -f docker-compose-dual.yml down
```
