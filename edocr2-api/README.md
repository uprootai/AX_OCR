# eDOCr2 API

공학 도면 OCR 처리 마이크로서비스

## 개요

eDOCr2 기반의 독립 API 서버로, 공학 도면에서 다음 정보를 추출합니다:
- 치수 정보 (Dimensions)
- 기하 공차 (GD&T - Geometric Dimensioning and Tolerancing)
- 텍스트 정보 (도면 번호, 리비전, 재질 등)

## 기능

### 핵심 기능
- **치수 추출**: 직경, 길이, 각도 등 자동 인식 (재현율 93.75%, CER 0.7%)
- **GD&T 인식**: ISO 1101/ASME Y14.5 기호 인식 (재현율 100%, CER 5.7%)
- **텍스트 추출**: 도면 번호, 리비전, 재질, 표면처리 등
- **Vision Language 통합**: GPT-4o/Qwen2-VL-7B 선택적 사용

### 지원 형식
- PDF
- PNG, JPG, JPEG
- TIFF

## 빠른 시작

### Docker로 실행 (권장)

```bash
# 1. 빌드
cd /home/uproot/ax/poc/edocr2-api
docker build -t edocr2-api .

# 2. 실행
docker run -d \
  -p 5001:5001 \
  --name edocr2 \
  -v $(pwd)/../dev/edocr2/edocr2:/app/edocr2:ro \
  -v $(pwd)/../dev/edocr2/models:/models:ro \
  edocr2-api

# 3. 로그 확인
docker logs -f edocr2

# 4. 헬스체크
curl http://localhost:5001/api/v1/health
```

### Docker Compose로 실행

```bash
cd /home/uproot/ax/poc/edocr2-api
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 중지
docker-compose down
```

## API 사용법

### 1. 헬스체크

```bash
curl http://localhost:5001/api/v1/health
```

**응답**:
```json
{
  "status": "healthy",
  "service": "eDOCr2 API",
  "version": "1.0.0",
  "timestamp": "2025-10-27T12:34:56"
}
```

### 2. 도면 OCR 처리

```bash
curl -X POST http://localhost:5001/api/v1/ocr \
  -F "file=@/path/to/drawing.pdf" \
  -F "extract_dimensions=true" \
  -F "extract_gdt=true" \
  -F "extract_text=true" \
  -F "use_vl_model=false"
```

**응답 예시**:
```json
{
  "status": "success",
  "data": {
    "dimensions": [
      {
        "value": 392.0,
        "unit": "mm",
        "type": "diameter",
        "tolerance": "±0.1",
        "location": {"x": 450, "y": 320}
      }
    ],
    "gdt": [
      {
        "type": "flatness",
        "value": 0.05,
        "datum": "A",
        "location": {"x": 200, "y": 150}
      }
    ],
    "text": {
      "drawing_number": "A12-311197-9",
      "revision": "Rev.2",
      "title": "Intermediate Shaft",
      "material": "Steel",
      "notes": ["M20 (4 places)", "Top & ø17.5 Drill, thru."]
    }
  },
  "processing_time": 8.5,
  "file_id": "1698765432_drawing.pdf"
}
```

### 3. Python 클라이언트

```python
import requests

# API URL
url = "http://localhost:5001/api/v1/ocr"

# 파일 업로드
with open("drawing.pdf", "rb") as f:
    files = {"file": f}
    data = {
        "extract_dimensions": True,
        "extract_gdt": True,
        "extract_text": True,
        "use_vl_model": False
    }

    response = requests.post(url, files=files, data=data)
    result = response.json()

    print(f"Status: {result['status']}")
    print(f"Processing time: {result['processing_time']}s")
    print(f"Dimensions: {len(result['data']['dimensions'])}")
    print(f"GD&T: {len(result['data']['gdt'])}")
```

### 4. JavaScript/TypeScript 클라이언트

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('extract_dimensions', 'true');
formData.append('extract_gdt', 'true');
formData.append('extract_text', 'true');

const response = await fetch('http://localhost:5001/api/v1/ocr', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log('OCR Result:', result);
```

## API 문서

서버 실행 후 다음 URL에서 상세 API 문서 확인:

- **Swagger UI**: http://localhost:5001/docs
- **ReDoc**: http://localhost:5001/redoc
- **OpenAPI JSON**: http://localhost:5001/openapi.json

## 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `EDOCR2_PORT` | 5001 | API 서버 포트 |
| `EDOCR2_WORKERS` | 4 | Uvicorn 워커 수 |
| `EDOCR2_MODEL_PATH` | /models | 모델 파일 경로 |
| `EDOCR2_LOG_LEVEL` | INFO | 로그 레벨 |

## 성능

- **처리 속도**:
  - 일반 모드: ~8-10초/장
  - VL 모델 사용: ~20-30초/장
- **정확도**:
  - 치수 재현율: 93.75%
  - GD&T 재현율: 100%
  - 문자 오류율(CER): 0.7% (치수), 5.7% (GD&T)
- **동시 처리**: 워커 4개 기준 최대 4개 동시 처리

## 제한 사항

- **파일 크기**: 최대 50MB
- **지원 형식**: PDF, PNG, JPG, JPEG, TIFF
- **임시 파일**: 24시간 후 자동 삭제

## 문제 해결

### 포트 충돌
```bash
# 포트 사용 확인
sudo lsof -i :5001

# 다른 포트 사용
docker run -p 5010:5001 edocr2-api
```

### 모델 파일 없음
```bash
# 모델 파일 다운로드
cd /home/uproot/ax/dev/edocr2
bash download_models.sh

# 볼륨 마운트 확인
docker run -v /path/to/models:/models edocr2-api
```

### 로그 확인
```bash
# 실시간 로그
docker logs -f edocr2

# 최근 100줄
docker logs --tail 100 edocr2
```

### 컨테이너 재시작
```bash
docker restart edocr2
```

## 개발

### 로컬 실행 (개발용)

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 개발 서버 실행 (hot reload)
uvicorn api_server:app --reload --port 5001
```

### 테스트

```bash
# 헬스체크
curl http://localhost:5001/api/v1/health

# 샘플 도면 테스트
curl -X POST http://localhost:5001/api/v1/ocr \
  -F "file=@/home/uproot/ax/reference/02. 수요처 및 도메인 자료/2. 도면(샘플)/A12-311197-9 Rev.2 Interm Shaft-Acc_y_1.jpg"
```

## 아키텍처

```
Client (HTTP POST)
    ↓
FastAPI Server (Uvicorn)
    ↓
File Validation
    ↓
eDOCr2 Pipeline
    ├── Table Pipeline (Pytesseract)
    ├── FCF Pipeline (CRNN)
    └── Dimension Pipeline (CRAFT + CRNN)
    ↓
Response (JSON)
```

## 기술 스택

- **웹 프레임워크**: FastAPI 0.104
- **ASGI 서버**: Uvicorn 0.24
- **OCR 엔진**: eDOCr2, Tesseract
- **딥러닝**: TensorFlow 2.13, Keras 2.13
- **이미지 처리**: OpenCV, Pillow, scikit-image
- **컨테이너**: Docker

## 라이선스

MIT License

## 문의

- 기술 문의: dev@uproot.com
- 이슈 리포트: https://github.com/uproot/ax-poc/issues
