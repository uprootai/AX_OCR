# Vision Language API (VL API)

멀티모달 LLM 기반 도면 분석 마이크로서비스

## 개요

Claude/GPT-4V 기반의 독립 API 서버로, 공학 도면에서 다음 정보를 추출합니다:
- **Information Block 추출**: 도면 번호, 재질, 축척, 무게 등
- **치수 추출**: 시각적 치수 인식
- **제조 공정 추론**: 제조 방법 및 순서 분석
- **QC Checklist 생성**: 품질 검사 항목 자동 생성

## 기능

### 핵심 기능
- **Info Block 추출**: Title block에서 메타데이터 추출
- **치수 추출**: Vision Language Model 기반 치수 인식
- **제조 공정 분석**: 제조 순서 및 방법 추론
- **QC Checklist**: 검사 항목 자동 생성

### 지원 모델
**Claude (Anthropic)**:
- claude-3-5-sonnet-20241022 (권장)
- claude-3-opus-20240229
- claude-3-haiku-20240307

**GPT (OpenAI)**:
- gpt-4o
- gpt-4-turbo
- gpt-4-vision-preview

### 지원 형식
- PNG, JPG, JPEG
- TIFF, BMP

## 빠른 시작

### 🆕 단독 실행 (Standalone)

```bash
# 독립 실행 (docker-compose.single.yml 사용)
cd /home/uproot/ax/poc/models/vl-api
docker-compose -f docker-compose.single.yml up -d

# 로그 확인
docker logs vl-api-standalone -f

# 헬스체크
curl http://localhost:5004/api/v1/health

# API 문서
# http://localhost:5004/docs
```

**주의**: API 키 필요
- `ANTHROPIC_API_KEY` 또는 `OPENAI_API_KEY` 환경 변수 설정 필요

### Docker로 실행 (권장)

```bash
# 1. 빌드
cd /home/uproot/ax/poc/models/vl-api
docker build -t vl-api .

# 2. 실행 (Anthropic Claude 사용)
docker run -d \
  -p 5004:5004 \
  --name vl-api \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  vl-api

# 또는 OpenAI GPT-4V 사용
docker run -d \
  -p 5004:5004 \
  --name vl-api \
  -e OPENAI_API_KEY=sk-... \
  vl-api

# 3. 로그 확인
docker logs -f vl-api

# 4. 헬스체크
curl http://localhost:5004/api/v1/health
```

### Docker Compose로 실행

```bash
# .env 파일 생성
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

# 실행
docker-compose -f docker-compose.single.yml up -d

# 로그 확인
docker-compose logs -f

# 중지
docker-compose down
```

## API 사용법

### 1. 헬스체크

```bash
curl http://localhost:5004/api/v1/health
```

**응답**:
```json
{
  "status": "healthy",
  "service": "vl-api",
  "version": "1.0.0",
  "timestamp": "2025-11-20T12:34:56",
  "available_models": [
    "claude-3-5-sonnet-20241022",
    "gpt-4o"
  ]
}
```

### 2. Information Block 추출

```bash
curl -X POST http://localhost:5004/api/v1/extract_info_block \
  -F "file=@/path/to/drawing.jpg" \
  -F 'query_fields=["name", "part number", "material", "scale", "weight"]' \
  -F "model=claude-3-5-sonnet-20241022"
```

**응답 예시**:
```json
{
  "status": "success",
  "data": {
    "name": "Intermediate Shaft",
    "part number": "A12-311197-9",
    "material": "STS304",
    "scale": "1:2",
    "weight": "5.2kg"
  },
  "processing_time": 2.5,
  "model_used": "claude-3-5-sonnet-20241022"
}
```

### 3. 치수 추출

```bash
curl -X POST http://localhost:5004/api/v1/extract_dimensions \
  -F "file=@/path/to/drawing.jpg" \
  -F "model=claude-3-5-sonnet-20241022"
```

**응답 예시**:
```json
{
  "status": "success",
  "data": [
    "Ø392 +0.1/-0",
    "163 ±0.2",
    "45° chamfer 1x45°",
    "M20 (4 places)"
  ],
  "processing_time": 3.2,
  "model_used": "claude-3-5-sonnet-20241022"
}
```

### 4. 제조 공정 추론

```bash
curl -X POST http://localhost:5004/api/v1/infer_manufacturing \
  -F "file=@/path/to/drawing.jpg" \
  -F "model=claude-3-5-sonnet-20241022"
```

**응답 예시**:
```json
{
  "status": "success",
  "data": {
    "processes": [
      {
        "order": 1,
        "process": "Turning",
        "description": "Turn outer diameter to Ø392",
        "equipment": "CNC Lathe"
      },
      {
        "order": 2,
        "process": "Drilling",
        "description": "Drill Ø17.5 holes (4 places)",
        "equipment": "Drill Press"
      }
    ],
    "estimated_time": "4.5 hours",
    "difficulty": "Medium"
  },
  "processing_time": 4.1,
  "model_used": "claude-3-5-sonnet-20241022"
}
```

### 5. QC Checklist 생성

```bash
curl -X POST http://localhost:5004/api/v1/generate_qc_checklist \
  -F "file=@/path/to/drawing.jpg" \
  -F "model=claude-3-5-sonnet-20241022"
```

**응답 예시**:
```json
{
  "status": "success",
  "data": {
    "checklist_items": [
      {
        "category": "Dimension",
        "item": "Check Ø392 (+0.1/-0)",
        "tolerance": "±0.05",
        "method": "Caliper or CMM"
      },
      {
        "category": "GD&T",
        "item": "Check flatness 0.05",
        "tolerance": "0.05",
        "method": "CMM"
      }
    ]
  },
  "processing_time": 3.8,
  "model_used": "claude-3-5-sonnet-20241022"
}
```

### 6. Python 클라이언트

```python
import requests

# API URL
url = "http://localhost:5004/api/v1/extract_info_block"

# 파일 업로드
with open("drawing.jpg", "rb") as f:
    files = {"file": f}
    data = {
        "query_fields": '["name", "part number", "material"]',
        "model": "claude-3-5-sonnet-20241022"
    }

    response = requests.post(url, files=files, data=data)
    result = response.json()

    print(f"Status: {result['status']}")
    print(f"Extracted Data: {result['data']}")
    print(f"Model: {result['model_used']}")
```

### 7. JavaScript/TypeScript 클라이언트

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('query_fields', '["name", "part number", "material"]');
formData.append('model', 'claude-3-5-sonnet-20241022');

const response = await fetch('http://localhost:5004/api/v1/extract_info_block', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log('Info Block:', result);
```

## API 문서

서버 실행 후 다음 URL에서 상세 API 문서 확인:

- **Swagger UI**: http://localhost:5004/docs
- **ReDoc**: http://localhost:5004/redoc
- **OpenAPI JSON**: http://localhost:5004/openapi.json

## 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `VL_API_PORT` | 5004 | API 서버 포트 |
| `ANTHROPIC_API_KEY` | - | Anthropic Claude API 키 |
| `OPENAI_API_KEY` | - | OpenAI GPT-4V API 키 |
| `VL_LOG_LEVEL` | INFO | 로그 레벨 |

**Note**: `ANTHROPIC_API_KEY` 또는 `OPENAI_API_KEY` 중 최소 하나 필요

## 성능

- **처리 속도**:
  - Info Block 추출: ~2-3초/요청
  - 치수 추출: ~3-4초/요청
  - 제조 공정 추론: ~4-6초/요청
  - QC Checklist: ~3-5초/요청
- **정확도**: 모델 및 도면 품질에 따라 변동
- **비용**: API 사용량에 따라 과금 (Claude/GPT 요금제 참조)

## 제한 사항

- **API 키 필요**: Anthropic 또는 OpenAI API 키 필수
- **파일 크기**: 최대 20MB (Claude 제한)
- **지원 형식**: PNG, JPG, JPEG, TIFF, BMP
- **비용**: API 호출당 과금 (외부 API 사용)

## 문제 해결

### API 키 오류

```bash
# API 키 확인
docker logs vl-api | grep "API key"

# API 키 설정
docker run -e ANTHROPIC_API_KEY=sk-ant-... vl-api
```

### 포트 충돌

```bash
# 포트 사용 확인
sudo lsof -i :5004

# 다른 포트 사용
docker run -p 5040:5004 vl-api
```

### 로그 확인

```bash
# 실시간 로그
docker logs -f vl-api

# 최근 100줄
docker logs --tail 100 vl-api
```

### 컨테이너 재시작

```bash
docker restart vl-api
```

## 개발

### 로컬 실행 (개발용)

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
export ANTHROPIC_API_KEY=sk-ant-...

# 개발 서버 실행 (hot reload)
uvicorn api_server:app --reload --port 5004
```

### 테스트

```bash
# 헬스체크
curl http://localhost:5004/api/v1/health

# Info Block 추출 테스트
curl -X POST http://localhost:5004/api/v1/extract_info_block \
  -F "file=@test_drawing.jpg" \
  -F 'query_fields=["name", "part number"]'
```

## 아키텍처

```
Client (HTTP POST)
    ↓
FastAPI Server (Uvicorn)
    ↓
File Validation
    ↓
Image Processing
    ↓
VL Model Selection
    ├── Claude API (Anthropic)
    └── GPT-4V API (OpenAI)
    ↓
Prompt Engineering
    ↓
Response Parsing
    ↓
JSON Response
```

## 기술 스택

- **웹 프레임워크**: FastAPI 0.104
- **ASGI 서버**: Uvicorn 0.24
- **VL Models**: Claude 3.5 Sonnet, GPT-4V
- **이미지 처리**: Pillow
- **HTTP Client**: httpx
- **컨테이너**: Docker

## 모델 비교

| 모델 | 속도 | 정확도 | 비용 | 추천 용도 |
|------|------|--------|------|-----------|
| Claude 3.5 Sonnet | 빠름 | 높음 | 중간 | **일반 추천** |
| Claude 3 Opus | 느림 | 매우 높음 | 높음 | 고정밀 작업 |
| Claude 3 Haiku | 매우 빠름 | 보통 | 낮음 | 대량 처리 |
| GPT-4o | 빠름 | 높음 | 중간 | Claude 대안 |
| GPT-4 Turbo | 중간 | 높음 | 중간 | 긴 문서 |

## API 키 획득

### Anthropic Claude
1. https://console.anthropic.com 방문
2. 계정 생성 및 로그인
3. API Keys 섹션에서 키 생성
4. `sk-ant-`로 시작하는 키 복사

### OpenAI GPT-4V
1. https://platform.openai.com 방문
2. 계정 생성 및 로그인
3. API Keys 섹션에서 키 생성
4. `sk-`로 시작하는 키 복사

## 라이선스

MIT License

## 문의

- 기술 문의: dev@uproot.com
- 이슈 리포트: https://github.com/uproot/ax-poc/issues
