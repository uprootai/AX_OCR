# EDGNet API

그래프 신경망 기반 도면 세그멘테이션 마이크로서비스

## 개요

GraphSAGE 기반의 독립 API 서버로, 공학 도면을 다음 컴포넌트로 분류합니다:
- **Contour** (윤곽선): 부품의 외형선
- **Text** (텍스트): 도면 번호, 주석 등
- **Dimension** (치수): 치수선 및 치수값

## 기능

### 핵심 기능
- **세그멘테이션**: 3-class 분류 (Contour/Text/Dimension, 정확도 90.82%)
- **벡터화**: 래스터 이미지 → Bezier 곡선 변환
- **그래프 구성**: 19차원 특징 추출 및 그래프 구축
- **시각화**: 분류 결과 컬러 이미지 생성

### 처리 파이프라인
```
Raster Image → Vectorization → Graph Construction → GraphSAGE → Classification
     ↓              ↓                  ↓                ↓              ↓
  PNG/JPG      Bezier Curves      19-D Features    GNN Layers    3 Classes
```

### 지원 형식
- PNG, JPG, JPEG
- TIFF, BMP

## 빠른 시작

### Docker로 실행 (권장)

```bash
# 1. 빌드
cd /home/uproot/ax/poc/edgnet-api
docker build -t edgnet-api .

# 2. 실행
docker run -d \
  -p 5002:5002 \
  --name edgnet \
  -v $(pwd)/../dev/edgnet:/app/edgnet:ro \
  -v $(pwd)/../dev/test_results/sample_tests/graphsage_models:/models:ro \
  edgnet-api

# 3. 로그 확인
docker logs -f edgnet

# 4. 헬스체크
curl http://localhost:5002/api/v1/health
```

### Docker Compose로 실행

```bash
cd /home/uproot/ax/poc/edgnet-api
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 중지
docker-compose down
```

## API 사용법

### 1. 헬스체크

```bash
curl http://localhost:5002/api/v1/health
```

**응답**:
```json
{
  "status": "healthy",
  "service": "EDGNet API",
  "version": "1.0.0",
  "timestamp": "2025-10-27T12:34:56"
}
```

### 2. 도면 세그멘테이션

```bash
curl -X POST http://localhost:5002/api/v1/segment \
  -F "file=@/path/to/drawing.png" \
  -F "visualize=true" \
  -F "num_classes=3" \
  -F "save_graph=true"
```

**응답 예시**:
```json
{
  "status": "success",
  "data": {
    "num_components": 150,
    "classifications": {
      "contour": 80,
      "text": 30,
      "dimension": 40
    },
    "graph": {
      "nodes": 150,
      "edges": 280,
      "avg_degree": 3.73
    },
    "vectorization": {
      "num_bezier_curves": 150,
      "total_length": 12450.5
    },
    "visualization_url": "/api/v1/result/drawing_segment.png"
  },
  "processing_time": 12.3,
  "file_id": "1698765432_drawing.png"
}
```

### 3. 도면 벡터화

```bash
curl -X POST http://localhost:5002/api/v1/vectorize \
  -F "file=@/path/to/drawing.png" \
  -F "save_bezier=true"
```

**응답 예시**:
```json
{
  "status": "success",
  "data": {
    "num_curves": 150,
    "curve_types": {
      "line": 85,
      "arc": 45,
      "bezier": 20
    },
    "total_length": 12450.5,
    "bezier_file": "/api/v1/result/drawing_curves.json"
  },
  "processing_time": 10.5,
  "file_id": "1698765432_drawing.png"
}
```

### 4. Python 클라이언트

```python
import requests

# API URL
url = "http://localhost:5002/api/v1/segment"

# 파일 업로드
with open("drawing.png", "rb") as f:
    files = {"file": f}
    data = {
        "visualize": True,
        "num_classes": 3,
        "save_graph": True
    }

    response = requests.post(url, files=files, data=data)
    result = response.json()

    print(f"Status: {result['status']}")
    print(f"Components: {result['data']['num_components']}")
    print(f"Contours: {result['data']['classifications']['contour']}")
    print(f"Text: {result['data']['classifications']['text']}")
    print(f"Dimensions: {result['data']['classifications']['dimension']}")
```

### 5. JavaScript/TypeScript 클라이언트

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('visualize', 'true');
formData.append('num_classes', '3');

const response = await fetch('http://localhost:5002/api/v1/segment', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log('Segmentation Result:', result);

// 시각화 이미지 다운로드
if (result.data.visualization_url) {
  const imgUrl = `http://localhost:5002${result.data.visualization_url}`;
  console.log('Visualization:', imgUrl);
}
```

## API 문서

서버 실행 후 다음 URL에서 상세 API 문서 확인:

- **Swagger UI**: http://localhost:5002/docs
- **ReDoc**: http://localhost:5002/redoc
- **OpenAPI JSON**: http://localhost:5002/openapi.json

## 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `EDGNET_PORT` | 5002 | API 서버 포트 |
| `EDGNET_WORKERS` | 2 | Uvicorn 워커 수 |
| `EDGNET_MODEL_PATH` | /models/graphsage_dimension_classifier.pth | GraphSAGE 모델 경로 |
| `EDGNET_LOG_LEVEL` | INFO | 로그 레벨 |

## 성능

- **처리 속도**:
  - 세그멘테이션: ~10-15초/장
  - 벡터화만: ~5-8초/장
- **정확도**:
  - 2-class (Text/Non-text): 98.48%
  - 3-class (Contour/Text/Dimension): 90.82%
- **동시 처리**: 워커 2개 기준 최대 2개 동시 처리

## 제한 사항

- **파일 크기**: 최대 50MB
- **지원 형식**: PNG, JPG, JPEG, TIFF, BMP
- **임시 파일**: 24시간 후 자동 삭제
- **최소 해상도**: 300 DPI 권장

## 문제 해결

### 포트 충돌
```bash
# 포트 사용 확인
sudo lsof -i :5002

# 다른 포트 사용
docker run -p 5020:5002 edgnet-api
```

### 모델 파일 없음
```bash
# GraphSAGE 모델 학습 필요
cd /home/uproot/ax/dev/test_results/sample_tests
python train_graphsage.py

# 볼륨 마운트 확인
docker run -v /path/to/models:/models edgnet-api
```

### 로그 확인
```bash
# 실시간 로그
docker logs -f edgnet

# 최근 100줄
docker logs --tail 100 edgnet
```

### 컨테이너 재시작
```bash
docker restart edgnet
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
uvicorn api_server:app --reload --port 5002
```

### 테스트

```bash
# 헬스체크
curl http://localhost:5002/api/v1/health

# 샘플 도면 세그멘테이션
curl -X POST http://localhost:5002/api/v1/segment \
  -F "file=@/home/uproot/ax/reference/02. 수요처 및 도메인 자료/2. 도면(샘플)/A12-311197-9 Rev.2 Interm Shaft-Acc_y_1.jpg"
```

## 아키텍처

```
Client (HTTP POST)
    ↓
FastAPI Server (Uvicorn)
    ↓
Image Processing
    ↓
Vectorization Pipeline
    ├── Skeletonization (Datta & Parui)
    ├── Trajectory Tracing
    └── Bezier Curve Fitting
    ↓
Graph Construction
    ├── Node Feature Extraction (19-D)
    └── Edge Creation
    ↓
GraphSAGE Model (PyTorch)
    ↓
Classification Output
    ↓
Response (JSON + Visualization)
```

## 기술 스택

- **웹 프레임워크**: FastAPI 0.104
- **ASGI 서버**: Uvicorn 0.24
- **딥러닝**: PyTorch 2.1, PyTorch Geometric 2.4
- **그래프**: NetworkX 3.1
- **이미지 처리**: OpenCV, scikit-image, Pillow
- **컨테이너**: Docker

## 알고리즘

### 벡터화
1. **Skeletonization**: Datta & Parui 방법
2. **Trajectory Tracing**: 연결된 픽셀 추적
3. **Bezier Fitting**: Cubic Bezier 곡선 근사

### 그래프 특징 (19-D)
- Shape: XY 좌표 (8차원)
- Length: 길이 정보 (4차원)
- Angle: 각도 정보 (2차원)
- Curvature: 곡률 정보 (4차원)

### GraphSAGE
- 5-layer GNN
- Aggregation: Mean
- Activation: ReLU
- Output: 3-class softmax

## 라이선스

MIT License

## 문의

- 기술 문의: dev@uproot.com
- 이슈 리포트: https://github.com/uproot/ax-poc/issues
