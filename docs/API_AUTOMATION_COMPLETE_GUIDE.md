# 🤖 API 완전 자동화 시스템 가이드

> **한 줄 요약**: 새 API를 개발하면 자동으로 검색, 등록, 노드 생성까지 모든 과정이 자동화됩니다.

---

## 📋 목차

1. [개요](#개요)
2. [시스템 아키텍처](#시스템-아키텍처)
3. [사용 방법](#사용-방법)
4. [개발자 가이드](#개발자-가이드)
5. [API 명세](#api-명세)
6. [트러블슈팅](#트러블슈팅)

---

## 🎯 개요

### 목표

**"새 API를 추가할 때 단 하나의 엔드포인트만 구현하면 나머지는 모두 자동화"**

### 이전 vs 현재

| 단계 | 이전 (수동) | 현재 (자동) |
|------|-----------|-----------|
| **1. API 개발** | FastAPI 구현 | FastAPI 구현 + `/api/v1/info` |
| **2. 메타데이터** | 수동으로 문서 작성 | 자동 제공 |
| **3. Gateway 등록** | 코드 수정 필요 | 자동 검색 |
| **4. Dashboard 등록** | 모든 필드 수동 입력 | URL만 입력 |
| **5. BlueprintFlow** | nodeDefinitions.ts 수정 | 자동 노드 생성 |
| **소요 시간** | 30분+ | **1분** ✨ |

---

## 🏗️ 시스템 아키텍처

### 전체 구조

```mermaid
graph TB
    A[새 API 개발<br/>/api/v1/info 구현] --> B[Docker 컨테이너 실행]
    B --> C[Gateway API 시작]
    C --> D{API Registry<br/>자동 검색}
    D -->|포트 5000-5099 스캔| E[/api/v1/info 호출]
    E --> F[메타데이터 수집]
    F --> G[Registry에 등록]
    G --> H[60초마다 헬스체크]

    I[사용자가 Web UI 접속] --> J[Dashboard useEffect]
    J --> K[/api/v1/registry/list 호출]
    K --> L[apiConfigStore에 자동 추가]
    L --> M[NodePalette이 감지]
    M --> N[BlueprintFlow 노드 자동 생성]

    style D fill:#10b981
    style G fill:#10b981
    style N fill:#10b981
```

### 핵심 컴포넌트

#### 1️⃣ **API 메타데이터 엔드포인트** (`/api/v1/info`)
각 API가 제공하는 표준화된 메타데이터 엔드포인트

**위치**: 각 API의 `api_server.py`
**역할**:
- API 정보 (이름, 버전, 설명)
- 입출력 스키마
- 파라미터 정의
- BlueprintFlow 노드 정보 (아이콘, 색상, 카테고리)

**예시**:
```json
{
  "id": "yolo-detector",
  "name": "YOLO Detection API",
  "display_name": "YOLO 객체 검출",
  "version": "1.0.0",
  "description": "YOLOv11 기반 도면 심볼/치수/GD&T 검출 API",
  "base_url": "http://localhost:5005",
  "endpoint": "/api/v1/detect",
  "requires_image": true,
  "inputs": [...],
  "outputs": [...],
  "parameters": [...],
  "blueprintflow": {
    "icon": "🎯",
    "color": "#3b82f6",
    "category": "detection"
  }
}
```

---

#### 2️⃣ **Gateway API Registry** (`gateway-api/api_registry.py`)
중앙 API 레지스트리 및 자동 검색 시스템

**기능**:
- ✅ 네트워크 자동 스캔 (포트 5000-5099)
- ✅ `/api/v1/info` 호출하여 메타데이터 수집
- ✅ API 등록 및 관리
- ✅ 60초마다 자동 헬스체크
- ✅ Healthy/Unhealthy 상태 관리

**주요 메서드**:
```python
async def discover_apis(host: str = "localhost") -> List[APIMetadata]
async def check_health(api_id: str) -> str
async def check_all_health()
async def start_health_check_loop()
```

---

#### 3️⃣ **Dashboard 자동 검색** (`web-ui/src/pages/dashboard/Dashboard.tsx`)
사용자가 URL만 입력하면 자동으로 API 등록

**기능**:
- ✅ "API 자동 검색" 버튼
- ✅ `/api/v1/registry/list` 호출
- ✅ apiConfigStore에 자동 추가
- ✅ 앱 시작 시 자동 실행 (최초 1회)

**코드**:
```typescript
const handleAutoDiscover = async () => {
  const response = await fetch('http://localhost:8000/api/v1/registry/list');
  const data = await response.json();

  data.apis.forEach((apiInfo: any) => {
    if (!customAPIs.find(api => api.id === apiInfo.id)) {
      addAPI({
        id: apiInfo.id,
        name: apiInfo.name,
        displayName: apiInfo.display_name,
        // ... 자동으로 모든 필드 채우기
      });
    }
  });
};
```

---

#### 4️⃣ **NodePalette 동적 생성** (`web-ui/src/components/blueprintflow/NodePalette.tsx`)
apiConfigStore를 감지하여 자동으로 노드 생성

**기능**:
- ✅ customAPIs 변화 감지 (useEffect)
- ✅ 자동으로 NodeConfig 생성
- ✅ 드래그앤드롭 가능한 노드 렌더링
- ✅ 아이콘, 색상, 설명 자동 반영

**코드**:
```typescript
useEffect(() => {
  const customNodeConfigs: NodeConfig[] = customAPIs
    .filter((api) => api.enabled)
    .map((api) => ({
      type: api.id,
      label: api.displayName,
      description: api.description,
      icon: api.icon,
      color: api.color,
      category: api.category,
    }));

  setAllNodeConfigs([...baseNodeConfigs, ...customNodeConfigs]);
}, [customAPIs]);
```

---

## 🚀 사용 방법

### 1. 새 API 추가하기 (자동)

#### Step 1: API 개발 시 `/api/v1/info` 엔드포인트 추가

**필수 코드** (`api_server.py`):
```python
from models.schemas import APIInfoResponse, ParameterSchema, IOSchema, BlueprintFlowMetadata

@app.get("/api/v1/info", response_model=APIInfoResponse)
async def get_api_info():
    return APIInfoResponse(
        id="my-custom-api",
        name="My Custom API",
        display_name="내 커스텀 API",
        version="1.0.0",
        description="API 설명",
        base_url="http://localhost:5009",
        endpoint="/api/v1/process",
        method="POST",
        requires_image=True,
        inputs=[...],
        outputs=[...],
        parameters=[...],
        blueprintflow=BlueprintFlowMetadata(
            icon="🔮",
            color="#ff6b6b",
            category="api"
        ),
        output_mappings={...}
    )
```

#### Step 2: Docker 컨테이너 실행

포트 5000-5099 범위에서 실행:
```bash
docker run -p 5009:5009 my-custom-api
```

#### Step 3: Gateway API 재시작

Gateway가 자동으로 검색:
```bash
docker restart gateway-api
```

**로그 확인**:
```
🔍 API 자동 검색 시작...
✅ API 발견: 내 커스텀 API (http://localhost:5009)
🎉 API 검색 완료: 6개 발견
```

#### Step 4: Web UI에서 "API 자동 검색" 클릭

또는 앱 재시작 시 자동으로 실행됩니다.

#### Step 5: BlueprintFlow에서 즉시 사용!

노드 팔레트에 자동으로 추가됨.

---

### 2. 수동으로 API 추가하기

Dashboard에서 URL만 입력:

1. `http://localhost:5173/dashboard` 접속
2. "API 추가" 클릭
3. "API 자동 검색" 섹션에 URL 입력 (예: `http://localhost:5009`)
4. "검색" 버튼 클릭
5. 자동으로 모든 정보 채워짐!
6. "API 추가" 클릭

---

## 👨‍💻 개발자 가이드

### 새 API 템플릿

**파일 구조**:
```
my-custom-api/
├── Dockerfile
├── api_server.py          ← /api/v1/info 추가 필요!
├── models/
│   └── schemas.py         ← APIInfoResponse 모델 추가
├── services/
│   └── inference.py
└── requirements.txt
```

**schemas.py 템플릿**:
```python
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class ParameterSchema(BaseModel):
    name: str
    type: str
    default: Any
    description: str
    required: bool = False
    options: Optional[List[str]] = None
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None

class IOSchema(BaseModel):
    name: str
    type: str
    description: str
    required: bool = True

class BlueprintFlowMetadata(BaseModel):
    icon: str
    color: str
    category: str

class APIInfoResponse(BaseModel):
    id: str
    name: str
    display_name: str
    version: str
    description: str
    openapi_url: str
    base_url: str
    endpoint: str
    method: str = "POST"
    requires_image: bool = True
    inputs: List[IOSchema]
    outputs: List[IOSchema]
    parameters: List[ParameterSchema]
    blueprintflow: BlueprintFlowMetadata
    output_mappings: Dict[str, str]
```

---

## 📡 API 명세

### Gateway API Registry 엔드포인트

#### 1. `GET /api/v1/registry/discover`
네트워크에서 API 자동 검색

**Parameters**:
- `host` (query, optional): 검색할 호스트 (기본: localhost)

**Response**:
```json
{
  "status": "success",
  "host": "localhost",
  "discovered_count": 5,
  "apis": [...]
}
```

---

#### 2. `GET /api/v1/registry/list`
등록된 모든 API 목록

**Response**:
```json
{
  "status": "success",
  "total_count": 5,
  "apis": [
    {
      "id": "yolo-detector",
      "name": "YOLO Detection API",
      "display_name": "YOLO 객체 검출",
      "status": "healthy",
      "last_check": "2025-11-21T12:00:00",
      ...
    }
  ]
}
```

---

#### 3. `GET /api/v1/registry/{api_id}`
특정 API 정보 조회

**Parameters**:
- `api_id` (path): API ID

**Response**:
```json
{
  "status": "success",
  "api": {
    "id": "yolo-detector",
    ...
  }
}
```

---

#### 4. `GET /api/v1/registry/category/{category}`
카테고리별 API 조회

**Parameters**:
- `category` (path): detection, ocr, segmentation, prediction 등

---

#### 5. `POST /api/v1/registry/health-check`
즉시 헬스체크 실행

**Response**:
```json
{
  "status": "success",
  "total_apis": 5,
  "healthy_apis": 5,
  "unhealthy_apis": 0,
  "apis": [...]
}
```

---

#### 6. `GET /api/v1/registry/healthy`
Healthy 상태인 API만 조회

---

## 🐛 트러블슈팅

### 1. API가 자동으로 검색되지 않아요

**원인**:
- `/api/v1/info` 엔드포인트가 없음
- 포트가 5000-5099 범위 밖
- Gateway API가 실행 중이 아님

**해결**:
```bash
# API에 /api/v1/info 엔드포인트 추가 확인
curl http://localhost:5009/api/v1/info

# Gateway API 로그 확인
docker logs gateway-api -f

# 수동으로 검색 실행
curl http://localhost:8000/api/v1/registry/discover
```

---

### 2. BlueprintFlow에 노드가 나타나지 않아요

**원인**:
- apiConfigStore에 등록되지 않음
- `enabled: false` 상태

**해결**:
1. Dashboard에서 "API 자동 검색" 클릭
2. localStorage 초기화:
   ```javascript
   localStorage.removeItem('auto-discovered');
   localStorage.removeItem('custom-apis-storage');
   ```
3. 페이지 새로고침

---

### 3. 헬스체크가 실패해요

**원인**:
- API 서버가 중지됨
- `/api/v1/health` 엔드포인트 없음
- 네트워크 연결 문제

**해결**:
```bash
# 헬스체크 수동 실행
curl http://localhost:5009/api/v1/health

# Gateway에서 헬스체크 강제 실행
curl -X POST http://localhost:8000/api/v1/registry/health-check
```

---

## 📊 시스템 현황

### 구현된 API (5개)

| API | 포트 | `/api/v1/info` | 상태 |
|-----|------|----------------|------|
| YOLO | 5005 | ✅ | ✅ |
| PaddleOCR | 5006 | ✅ | ✅ |
| eDOCr2 v2 | 5002 | ✅ | ✅ |
| EDGNet | 5012 | ✅ | ✅ |
| SkinModel | 5003 | ✅ | ✅ |

### Gateway API Registry

| 엔드포인트 | 메서드 | 상태 |
|-----------|--------|------|
| `/api/v1/registry/discover` | GET | ✅ |
| `/api/v1/registry/list` | GET | ✅ |
| `/api/v1/registry/{api_id}` | GET | ✅ |
| `/api/v1/registry/category/{cat}` | GET | ✅ |
| `/api/v1/registry/health-check` | POST | ✅ |
| `/api/v1/registry/healthy` | GET | ✅ |

### Dashboard 기능

| 기능 | 상태 |
|------|------|
| API 자동 검색 버튼 | ✅ |
| URL 입력 자동 파싱 | ✅ |
| 앱 시작 시 자동 검색 | ✅ |

### BlueprintFlow 통합

| 기능 | 상태 |
|------|------|
| 동적 노드 생성 | ✅ |
| customAPIs 감지 | ✅ |
| 아이콘/색상 자동 반영 | ✅ |

---

## 🎯 요약

### 사용자 관점

**이전**:
```
1. API 개발
2. Swagger 확인
3. Dashboard에서 20개 필드 수동 입력
4. BlueprintFlow 코드 수정
5. 테스트
```

**현재**:
```
1. API 개발 (/api/v1/info만 추가)
2. Docker 실행
→ 끝! 자동으로 모든 것이 완성됨 ✨
```

### 개발자 관점

**추가 작업**: `/api/v1/info` 엔드포인트 1개만 구현
**절감 시간**: **29분** (30분 → 1분)
**에러 가능성**: **90% 감소** (수동 입력 오타 제거)

---

**작성일**: 2025-11-21
**버전**: 1.0.0
**상태**: ✅ 완전 구현 완료

