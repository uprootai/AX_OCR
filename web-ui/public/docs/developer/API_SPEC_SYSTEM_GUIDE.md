# API 스펙 시스템 개발자 가이드

> YAML 기반 API 표준화 및 자동 통합 시스템

## 개요

API 스펙 시스템은 YAML 파일 하나로 새 API를 BlueprintFlow에 자동 통합하는 표준화 시스템입니다.

```
YAML 스펙 → ExecutorRegistry → GenericAPIExecutor → BlueprintFlow 노드
     ↓
Frontend specService → useNodeDefinitions 훅 → NodePalette (동적 로딩)
```

## 빠른 시작

### 새 API 생성 (스캐폴딩)

```bash
# 기본 사용법
python scripts/create_api.py my-detector --port 5015 --category detection

# 생성되는 파일:
# - models/my-detector-api/api_server.py
# - models/my-detector-api/Dockerfile
# - models/my-detector-api/requirements.txt
# - gateway-api/api_specs/my-detector.yaml
```

### 수동 생성

1. `gateway-api/api_specs/{api-id}.yaml` 파일 생성
2. `models/{api-id}-api/api_server.py` 구현
3. Gateway 재시작 → 자동 인식

## YAML 스펙 구조

```yaml
# gateway-api/api_specs/my-api.yaml
apiVersion: v1
kind: APISpec

metadata:
  id: my-api              # 고유 ID (kebab-case)
  name: My API            # 표시 이름
  version: 1.0.0
  port: 5015              # API 포트
  description: API 설명
  author: AX Team
  tags:
    - detection
    - custom

server:
  endpoint: /api/v1/process    # 메인 엔드포인트
  method: POST
  contentType: multipart/form-data  # 또는 application/json
  timeout: 60                  # 초
  healthEndpoint: /health

blueprintflow:
  category: detection          # input, detection, ocr, segmentation,
                               # preprocessing, analysis, knowledge, ai, control
  color: "#10b981"            # 노드 색상 (hex)
  icon: Target                # Lucide 아이콘 이름
  requiresImage: true         # 이미지 필수 여부
  recommendedInputs:          # 추천 연결 (선택)
    - from: yolo
      field: detections
      reason: YOLO 검출 결과를 입력으로 사용

inputs:
  - name: image
    type: Image
    required: true
    description: 입력 이미지

outputs:
  - name: result
    type: object
    description: 처리 결과

parameters:
  - name: confidence
    type: number
    default: 0.5
    min: 0.1
    max: 1.0
    step: 0.1
    description: 신뢰도 임계값

  - name: model_type
    type: select
    default: standard
    options:
      - standard
      - advanced
    description: 모델 타입

  - name: visualize
    type: boolean
    default: false
    description: 시각화 활성화

mappings:
  input:
    image: file              # 노드 입력 → API 파라미터 매핑
  output:
    result: data             # API 응답 → 노드 출력 매핑

i18n:
  ko:
    label: 내 API
    description: 한국어 설명
    parameters:
      confidence: 신뢰도 임계값
      model_type: 모델 타입
  en:
    label: My API
    description: English description

examples:
  - 사용 예시 1
  - 사용 예시 2

usageTips:
  - 팁 1
  - 팁 2
```

## 파라미터 타입

| 타입 | UI 렌더링 | 예시 |
|------|----------|------|
| `number` | 슬라이더/입력 | `min`, `max`, `step` 지정 |
| `select` | 드롭다운 | `options` 배열 필수 |
| `boolean` | 토글 스위치 | `default: true/false` |
| `string` | 텍스트 입력 | 자유 입력 |

## 카테고리

| 카테고리 | 설명 | 아이콘 색상 |
|----------|------|------------|
| `input` | 입력 노드 | orange |
| `detection` | 객체 검출 | green |
| `ocr` | 텍스트 인식 | blue |
| `segmentation` | 이미지 분할 | purple |
| `preprocessing` | 전처리 | amber |
| `analysis` | 분석 | yellow |
| `knowledge` | 지식 엔진 | violet |
| `ai` | AI/LLM | pink |
| `control` | 제어 흐름 | red |

## 시스템 아키텍처

### Backend 흐름

```
1. Gateway 시작
   ↓
2. ExecutorRegistry.load_spec(api_id)
   - gateway-api/api_specs/*.yaml 스캔
   - 스펙 캐싱
   ↓
3. 워크플로우 실행 시
   - ExecutorRegistry.create(node_type)
   - 우선순위: 등록된 Executor → YAML 스펙 → Custom API
   ↓
4. GenericAPIExecutor 생성
   - spec_to_api_config() 변환
   - HTTP 호출 수행
```

### Frontend 흐름

```
1. specService.fetchAllSpecs()
   - GET /api/v1/specs
   ↓
2. specToNodeDefinition(spec, lang)
   - YAML → NodeDefinition 변환
   ↓
3. useNodeDefinitions() 훅
   - 정적 + 동적 정의 병합
   - categorizedNodes 제공
   ↓
4. NodePalette 렌더링
   - 카테고리별 노드 표시
```

## API 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/v1/specs` | GET | 모든 스펙 조회 |
| `/api/v1/specs/{api_id}` | GET | 특정 스펙 조회 |
| `/api/v1/specs/{api_id}/parameters` | GET | 파라미터만 조회 |
| `/api/v1/specs/{api_id}/blueprintflow` | GET | 노드 메타데이터 조회 |

## 스캐폴딩 스크립트 옵션

```bash
python scripts/create_api.py <api-id> [옵션]

옵션:
  --port PORT        API 포트 (기본: 자동 할당)
  --category CAT     카테고리 (기본: detection)
  --description DESC 설명
  --no-docker        Dockerfile 생성 안함
  --no-spec          YAML 스펙 생성 안함
```

## 기존 API에 스펙 추가하기

기존 API가 있고 스펙만 추가하려면:

```bash
# 1. 스펙 파일만 생성
python scripts/create_api.py existing-api --port 5015 --no-docker

# 2. 또는 직접 YAML 작성
vi gateway-api/api_specs/existing-api.yaml
```

## 검증 및 테스트

```bash
# 스펙 로드 테스트
curl http://localhost:8000/api/v1/specs

# 특정 스펙 확인
curl http://localhost:8000/api/v1/specs/yolo

# BlueprintFlow 메타데이터
curl http://localhost:8000/api/v1/specs/yolo/blueprintflow
```

## 트러블슈팅

### 스펙이 로드되지 않음
```bash
# 1. YAML 문법 확인
python -c "import yaml; yaml.safe_load(open('gateway-api/api_specs/my-api.yaml'))"

# 2. kind가 APISpec인지 확인
grep "kind:" gateway-api/api_specs/my-api.yaml
```

### 노드가 팔레트에 안 보임
1. Gateway 재시작
2. 브라우저 새로고침
3. 콘솔에서 `fetchAllSpecs()` 응답 확인

### Executor 생성 실패
```python
# ExecutorRegistry 우선순위:
# 1. 등록된 전용 Executor (yolo, edocr2 등)
# 2. YAML 스펙 기반 GenericAPIExecutor
# 3. Custom API Config 기반

# 로그 확인
docker logs gateway-api 2>&1 | grep "스펙"
```

## 파일 위치 요약

```
gateway-api/
├── api_specs/              # YAML 스펙 파일
│   ├── yolo.yaml
│   ├── edocr2.yaml
│   └── ...
├── utils/
│   └── spec_loader.py      # 스펙 로더 유틸리티
└── blueprintflow/
    └── executors/
        └── executor_registry.py  # 스펙 기반 Executor 생성

web-ui/src/
├── services/
│   └── specService.ts      # 스펙 API 클라이언트
└── hooks/
    └── useNodeDefinitions.ts  # 동적 노드 정의 훅

scripts/
└── create_api.py           # 스캐폴딩 스크립트
```

## 관련 문서

- [BlueprintFlow 개요](/docs/blueprintflow/README.md)
- [전체 API 파라미터 가이드](/docs/API_PARAMETERS_DETAILED_GUIDE.md)
- [동적 API 시스템 가이드](/DYNAMIC_API_SYSTEM_GUIDE.md)
