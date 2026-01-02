# 새 API 추가 체크리스트

> PID Composer API 생성 시 사용한 패턴 정리
> 다른 새 API 추가 시 이 체크리스트 사용

---

## 체크리스트 (6단계)

### Step 1: 마이크로서비스 생성
**위치**: `models/{api-id}-api/`

```
models/{api-id}-api/
├── api_server.py           # FastAPI 메인 (lifespan 패턴)
├── Dockerfile              # 컨테이너 설정
├── requirements.txt        # Python 의존성
├── routers/
│   ├── __init__.py
│   └── {feature}_router.py # API 엔드포인트
├── services/
│   ├── __init__.py
│   └── {feature}_service.py # 비즈니스 로직
└── tests/
    ├── __init__.py
    └── test_{feature}.py   # 테스트
```

**필수 엔드포인트**:
- `GET /health` - 헬스체크
- `GET /api/v1/health` - 헬스체크 (v1 경로)
- `GET /api/v1/info` - 서비스 정보
- `POST /api/v1/{main-endpoint}` - 메인 기능

**Dockerfile 템플릿**:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:{PORT}/health || exit 1
EXPOSE {PORT}
CMD ["python", "api_server.py"]
```

---

### Step 2: API 스펙 YAML 생성
**위치**: `gateway-api/api_specs/{api-id}.yaml`

```yaml
api_id: {api_id}
display_name: "{Display Name}"
version: "1.0.0"
category: {detection|ocr|segmentation|preprocessing|analysis|knowledge|ai}
description: "한글 설명"
description_en: "English description"

service:
  port: {PORT}
  base_url: "http://{container-name}:{PORT}"
  health_endpoint: "/health"
  container_name: "{container-name}"

blueprintflow:
  node_type: "{nodetype}"
  icon: "{emoji}"
  color: "#{hex-color}"
  inputs: [...]
  outputs: [...]
  parameters: [...]

endpoints:
  - method: POST
    path: "/api/v1/{endpoint}"
    description: "설명"

resources:
  gpu:
    required: {true|false}
    vram: "~{N}GB"
  cpu:
    ram: "~{N}MB"
    minRam: {N}
    cores: {N}

tags: [...]
```

---

### Step 3: docker-compose.yml 서비스 추가
**위치**: `docker-compose.yml`

```yaml
  # =====================
  # {Display Name} API (포트 {PORT})
  # =====================
  {container-name}:
    build:
      context: ./models/{api-id}-api
      dockerfile: Dockerfile
    container_name: {container-name}
    ports:
      - "{PORT}:{PORT}"
    environment:
      - {API_ID}_PORT={PORT}
      - PYTHONUNBUFFERED=1
    networks:
      - ax_poc_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:{PORT}/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

---

### Step 4: apiRegistry.ts 추가
**위치**: `web-ui/src/config/apiRegistry.ts`

```typescript
  // {Display Name}
  {
    id: '{api_id}',
    nodeType: '{nodetype}',
    displayName: '{Display Name}',
    containerName: '{container-name}',
    specId: '{api-id}',
    port: {PORT},
    category: '{category}',
    description: '한글 설명',
    icon: '{emoji}',
    color: '#{hex-color}',
    gpuEnabled: {true|false},
  },
```

---

### Step 5: Dashboard 모니터링 목록 추가
**위치**: `web-ui/src/components/monitoring/constants.ts`

```typescript
  // {Category Comment}
  { id: '{api_id}', name: '{api_id}', display_name: '{Display Name}',
    base_url: 'http://localhost:{PORT}', port: {PORT},
    status: 'unknown', category: '{category}',
    description: '한글 설명', icon: '{emoji}', color: '#{hex-color}',
    last_check: null },
```

---

### Step 6: nodeDefinitions 노드 정의 추가
**위치**: `web-ui/src/config/nodes/{category}Nodes.ts`

```typescript
  {nodetype}: {
    type: '{nodetype}',
    label: '{Display Name}',
    category: '{category}',
    color: '#{hex-color}',
    icon: '{LucideIconName}',
    description: '한글 설명',
    inputs: [...],
    outputs: [...],
    parameters: [...],
    examples: [...],
    usageTips: [...],
    recommendedInputs: [...],
  },
```

---

## 선택 사항

### CLAUDE.md 업데이트
- API 서비스 개수 업데이트 (19개 → 20개 등)
- API 서비스 테이블에 새 항목 추가
- API 스펙 디렉토리 목록 업데이트

### 테스트 추가
- `models/{api-id}-api/tests/test_{feature}.py`
- 기본 헬스체크, 메인 기능 테스트

---

## 향후 적용 대상

| 예정 API | 포트 | 카테고리 | 설명 |
|----------|------|----------|------|
| pid-editor | 5022 | analysis | P&ID 편집 (Phase 3) |
| drawing-diff | 5023 | analysis | 도면 리비전 비교 |
| report-generator | 5024 | analysis | 리포트 생성 |
