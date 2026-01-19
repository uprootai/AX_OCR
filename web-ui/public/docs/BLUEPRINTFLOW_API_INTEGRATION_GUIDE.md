# BlueprintFlow와 Dashboard/Settings 연동 가이드

**Date**: 2025-11-20
**Version**: 1.0
**목적**: BlueprintFlow, Dashboard, Settings 간 API 연동 상태 및 신규 API 추가 방법

---

## 📊 현재 연동 상태

### ✅ 완전 연동됨

BlueprintFlow, Dashboard, Settings는 **동일한 API 클라이언트**를 공유합니다.

```
web-ui/src/lib/api.ts (중앙 API 클라이언트)
         ↓
    ┌────┴────┬─────────┬──────────┐
    ↓         ↓         ↓          ↓
Dashboard  Settings  BlueprintFlow  Analyze
```

### 🔗 공유 시스템

| 컴포넌트 | 역할 | 사용 API |
|----------|------|----------|
| **Dashboard** | API 상태 모니터링 | `checkAllServices()` - 모든 API 헬스체크 |
| **Settings** | API 설정 관리 | 각 API별 설정 (추후 구현 예정) |
| **BlueprintFlow** | 워크플로우 빌더 | 노드 메타데이터에서 참조 |
| **Analyze** | 실제 분석 실행 | `gatewayApi.process()` |

---

## 🔍 상세 연동 구조

### 1. Dashboard (`/dashboard`)

**파일**: `web-ui/src/pages/dashboard/Dashboard.tsx`

**기능**:
- API 상태 실시간 모니터링 (30초마다 자동 갱신)
- 8개 API 서비스 상태 표시
- Swagger 문서 링크 제공

**연동 방식**:
```typescript
// web-ui/src/components/monitoring/APIStatusMonitor.tsx
import { checkAllServices } from '../../lib/api';

const { data } = useQuery({
  queryKey: ['health-check'],
  queryFn: checkAllServices,
  refetchInterval: 30000, // 30초마다
});
```

**모니터링 대상 API (8개)**:
1. Gateway API (Port 8000)
2. eDOCr v1 (Port 5001)
3. eDOCr v2 (Port 5002)
4. EDGNet (Port 5012)
5. Skin Model (Port 5003)
6. VL API (Port 5004)
7. YOLO (Port 5005)
8. PaddleOCR (Port 5006)

---

### 2. Settings (`/settings`)

**파일**: `web-ui/src/pages/settings/Settings.tsx`

**기능** (현재):
- 언어 설정 (한국어/English)
- 테마 설정 (라이트/다크 모드)
- ⚠️ API 설정 기능은 아직 구현되지 않음

**향후 연동 계획**:
- API 엔드포인트 URL 변경
- API 키 관리
- 파라미터 기본값 설정

---

### 3. BlueprintFlow (`/blueprintflow`)

**파일**: `web-ui/src/config/nodeDefinitions.ts`

**연동 방식**:
```typescript
// 노드 정의에서 API 메타데이터 참조
export const nodeDefinitions = {
  yolo: {
    type: 'yolo',
    label: 'YOLO Detection',
    // ... 입출력 정의
  },
  edocr2: { ... },
  edgnet: { ... },
  skinmodel: { ... },
  paddleocr: { ... },
  vl: { ... },
};
```

**중요**: BlueprintFlow 노드는 **메타데이터만 정의**하고, 실제 API 호출은 아직 구현 안 됨 (Phase 4 예정)

---

## 🆕 새로운 API 추가 방법

### 전체 프로세스

```
1. Backend API 구현
   ↓
2. web-ui/src/lib/api.ts 업데이트
   ↓
3. web-ui/src/components/monitoring/APIStatusMonitor.tsx 업데이트
   ↓
4. web-ui/src/config/nodeDefinitions.ts 업데이트 (BlueprintFlow용)
   ↓
5. web-ui/src/components/blueprintflow/nodes/ 노드 컴포넌트 추가
   ↓
6. web-ui/src/pages/blueprintflow/BlueprintFlowBuilder.tsx에 nodeTypes 등록
```

---

## 📝 단계별 상세 가이드

### Step 1: Backend API 구현

**예시**: 새로운 "TextClassifier" API 추가

```bash
# 1. API 디렉토리 생성
mkdir -p /home/uproot/ax/poc/textclassifier-api

# 2. 기본 파일 생성
cd textclassifier-api
touch api_server.py
touch requirements.txt
touch Dockerfile
```

**api_server.py** (기본 템플릿):
```python
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Text Classifier API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "textclassifier-api",
        "version": "1.0.0"
    }

@app.post("/api/v1/classify")
async def classify_text(file: UploadFile = File(...)):
    # TODO: 실제 분류 로직 구현
    return {
        "text": "Sample text",
        "category": "technical",
        "confidence": 0.95
    }
```

**Dockerfile**:
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5007
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "5007"]
```

**docker-compose.yml에 추가**:
```yaml
textclassifier-api:
  build: ./textclassifier-api
  ports:
    - "5007:5007"
  networks:
    - ax-network
```

---

### Step 2: web-ui/src/lib/api.ts 업데이트

**파일**: `/home/uproot/ax/poc/web-ui/src/lib/api.ts`

```typescript
// 1. Base URL 추가
const TEXTCLASSIFIER_BASE = import.meta.env.VITE_TEXTCLASSIFIER_URL || 'http://localhost:5007';

// 2. Axios 인스턴스 생성
const textclassifierAPI = axios.create({ baseURL: TEXTCLASSIFIER_BASE });

// 3. API 클라이언트 추가 (파일 끝부분에)
export const textclassifierApi = {
  // Health Check
  healthCheck: async (): Promise<HealthCheckResponse> => {
    const response = await textclassifierAPI.get('/api/v1/health');
    return response.data;
  },

  // Classify Text
  classify: async (
    file: File,
    options?: {
      threshold?: number;
    }
  ): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);
    if (options?.threshold) {
      formData.append('threshold', String(options.threshold));
    }

    const response = await textclassifierAPI.post('/api/v1/classify', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
};

// 4. checkAllServices 함수에 추가
export async function checkAllServices() {
  const results = await Promise.allSettled([
    gatewayApi.healthCheck(),
    edocr2Api.healthCheck(),
    edocr2Api.healthCheckV2(),
    edgnetApi.healthCheck(),
    skinmodelApi.healthCheck(),
    yoloApi.healthCheck(),
    paddleocrApi.healthCheck(),
    vlApi.healthCheck(),
    textclassifierApi.healthCheck(), // ← 새로 추가
  ]);

  return {
    gateway: results[0].status === 'fulfilled' ? results[0].value : null,
    edocr2_v1: results[1].status === 'fulfilled' ? results[1].value : null,
    edocr2_v2: results[2].status === 'fulfilled' ? results[2].value : null,
    edgnet: results[3].status === 'fulfilled' ? results[3].value : null,
    skinmodel: results[4].status === 'fulfilled' ? results[4].value : null,
    yolo: results[5].status === 'fulfilled' ? results[5].value : null,
    paddleocr: results[6].status === 'fulfilled' ? results[6].value : null,
    vl: results[7].status === 'fulfilled' ? results[7].value : null,
    textclassifier: results[8].status === 'fulfilled' ? results[8].value : null, // ← 새로 추가
  };
}
```

---

### Step 3: Dashboard 모니터링 추가

**파일**: `/home/uproot/ax/poc/web-ui/src/components/monitoring/APIStatusMonitor.tsx`

```typescript
// useEffect 안에 추가
useEffect(() => {
  if (data) {
    // ... 기존 코드 ...

    // TextClassifier API 추가
    if (data.textclassifier) {
      updateServiceHealth('textclassifier', {
        name: 'Text Classifier API',
        status: 'healthy',
        latency: Math.random() * 50,
        lastCheck: new Date(),
        swaggerUrl: 'http://localhost:5007/docs',
      });
    }
  }
}, [data, updateServiceHealth]);
```

---

### Step 4: BlueprintFlow 노드 정의 추가

**파일**: `/home/uproot/ax/poc/web-ui/src/config/nodeDefinitions.ts`

```typescript
export const nodeDefinitions: Record<string, NodeDefinition> = {
  // ... 기존 노드들 ...

  textclassifier: {
    type: 'textclassifier',
    label: 'Text Classifier',
    category: 'api',
    color: '#a855f7', // 보라색
    icon: 'Tags',
    description: '도면 속 텍스트를 분류하여 기술 문서, 주석, 치수 등으로 구분합니다.',
    inputs: [
      {
        name: 'text',
        type: 'string | OCRResult[]',
        description: '📝 분류할 텍스트 또는 OCR 결과',
      },
    ],
    outputs: [
      {
        name: 'classification',
        type: 'ClassificationResult',
        description: '🏷️ 텍스트 카테고리 (기술/주석/치수 등)',
      },
    ],
    parameters: [
      {
        name: 'threshold',
        type: 'number',
        default: 0.7,
        min: 0,
        max: 1,
        step: 0.05,
        description: '분류 신뢰도 임계값',
      },
    ],
    examples: [
      'OCR 결과 → TextClassifier → 텍스트 종류별 분류',
      '주석과 치수를 자동으로 구분',
    ],
  },
};
```

---

### Step 5: BlueprintFlow 노드 컴포넌트 추가

**파일**: `/home/uproot/ax/poc/web-ui/src/components/blueprintflow/nodes/ApiNodes.tsx`

```typescript
import { Tags } from 'lucide-react'; // 아이콘 import 추가

// ... 기존 노드들 ...

// TextClassifier Node 추가
export const TextclassifierNode = memo((props: NodeProps) => (
  <BaseNode
    {...props}
    icon={Tags}
    title="Text Classifier"
    color="#a855f7"
    category="api"
  />
));
TextclassifierNode.displayName = 'TextclassifierNode';
```

**파일**: `/home/uproot/ax/poc/web-ui/src/components/blueprintflow/nodes/index.ts`

```typescript
export {
  YoloNode,
  Edocr2Node,
  EdgnetNode,
  SkinmodelNode,
  PaddleocrNode,
  VlNode,
  TextclassifierNode, // ← 추가
} from './ApiNodes';

export { IfNode, LoopNode, MergeNode } from './ControlNodes';
```

---

### Step 6: BlueprintFlowBuilder에 노드 타입 등록

**파일**: `/home/uproot/ax/poc/web-ui/src/pages/blueprintflow/BlueprintFlowBuilder.tsx`

```typescript
import {
  YoloNode,
  Edocr2Node,
  EdgnetNode,
  SkinmodelNode,
  PaddleocrNode,
  VlNode,
  TextclassifierNode, // ← import 추가
  IfNode,
  LoopNode,
  MergeNode,
} from '../../components/blueprintflow/nodes';

// Node type mapping
const nodeTypes = {
  yolo: YoloNode,
  edocr2: Edocr2Node,
  edgnet: EdgnetNode,
  skinmodel: SkinmodelNode,
  paddleocr: PaddleocrNode,
  vl: VlNode,
  textclassifier: TextclassifierNode, // ← 추가
  if: IfNode,
  loop: LoopNode,
  merge: MergeNode,
};
```

---

### Step 7: NodePalette에 표시 추가

**파일**: `/home/uproot/ax/poc/web-ui/src/components/blueprintflow/NodePalette.tsx`

NodePalette는 자동으로 `nodeDefinitions`에서 노드를 읽어오므로, **별도 수정 불필요**합니다!

하지만 순서를 바꾸고 싶다면:

```typescript
const apiNodes = [
  'yolo',
  'edocr2',
  'edgnet',
  'skinmodel',
  'paddleocr',
  'vl',
  'textclassifier', // ← 추가
];
```

---

## ✅ 체크리스트

새로운 API를 추가할 때 다음 항목을 모두 확인하세요:

### Backend (필수)
- [ ] API 서버 구현 (`api_server.py`)
- [ ] Dockerfile 작성
- [ ] `docker-compose.yml`에 서비스 추가
- [ ] 헬스체크 엔드포인트 (`/api/v1/health`) 구현
- [ ] 실제 기능 엔드포인트 구현
- [ ] Swagger 문서 자동 생성 확인

### Frontend - API 클라이언트 (필수)
- [ ] `web-ui/src/lib/api.ts`
  - [ ] Base URL 추가
  - [ ] Axios 인스턴스 생성
  - [ ] API 클라이언트 함수 작성
  - [ ] `checkAllServices()`에 추가

### Frontend - Dashboard (필수)
- [ ] `web-ui/src/components/monitoring/APIStatusMonitor.tsx`
  - [ ] `updateServiceHealth()` 호출 추가
  - [ ] 서비스 이름, Swagger URL 설정

### Frontend - BlueprintFlow (선택)
- [ ] `web-ui/src/config/nodeDefinitions.ts`
  - [ ] 노드 정의 추가 (입출력, 파라미터, 예시)
- [ ] `web-ui/src/components/blueprintflow/nodes/ApiNodes.tsx`
  - [ ] 노드 컴포넌트 추가
  - [ ] 아이콘 import
  - [ ] export 추가
- [ ] `web-ui/src/pages/blueprintflow/BlueprintFlowBuilder.tsx`
  - [ ] nodeTypes에 등록

### 문서화 (권장)
- [ ] API README.md 작성
- [ ] Swagger 문서 확인
- [ ] 사용 예시 작성

---

## 🎯 현재 지원되는 API (20개)

| API | Port | Dashboard | BlueprintFlow | 상태 |
|-----|------|-----------|---------------|------|
| **Gateway** | 8000 | ✅ | - | ✅ Healthy |
| **eDOCr2** | 5002 | ✅ | ✅ | ✅ Healthy |
| **SkinModel** | 5003 | ✅ | ✅ | ✅ Healthy |
| **VL API** | 5004 | ✅ | ✅ | 🔑 API Key 필요 |
| **YOLO** | 5005 | ✅ | ✅ | ✅ Healthy |
| **PaddleOCR** | 5006 | ✅ | ✅ | ✅ Healthy |
| **Knowledge** | 5007 | ✅ | ✅ | ✅ Healthy |
| **Tesseract** | 5008 | ✅ | ✅ | ✅ Healthy |
| **TrOCR** | 5009 | ✅ | ✅ | ✅ Healthy |
| **ESRGAN** | 5010 | ✅ | ✅ | ✅ Healthy |
| **OCR Ensemble** | 5011 | ✅ | ✅ | ✅ Healthy |
| **EDGNet** | 5012 | ✅ | ✅ | ✅ Healthy |
| **Surya OCR** | 5013 | ✅ | ✅ | ✅ Healthy |
| **DocTR** | 5014 | ✅ | ✅ | ✅ Healthy |
| **EasyOCR** | 5015 | ✅ | ✅ | ✅ Healthy |
| **Line Detector** | 5016 | ✅ | ✅ | ✅ Healthy |
| **PID Analyzer** | 5018 | ✅ | ✅ | ✅ Healthy |
| **Design Checker** | 5019 | ✅ | ✅ | ✅ Healthy |
| **Blueprint AI BOM** | 5020 | ✅ | ✅ | ✅ Healthy |

**총 20개 API 모니터링 중**, BlueprintFlow에서 28개 노드 사용 가능

---

## 🔄 연동 플로우 요약

```
[새 API 추가]
    ↓
[Backend 구현 + Docker 배포]
    ↓
[web-ui/src/lib/api.ts 업데이트]
    ↓
┌───────────────┬────────────────────┐
↓               ↓                    ↓
[Dashboard]  [Settings]      [BlueprintFlow]
모니터링      설정 관리         워크플로우 노드
자동 표시     (수동 추가)       (수동 추가)
```

**핵심**: `web-ui/src/lib/api.ts`만 업데이트하면 Dashboard는 **자동으로 모니터링** 시작!

---

## 📞 문제 해결

### Q1: Dashboard에 새 API가 표시되지 않아요
**A**: `web-ui/src/components/monitoring/APIStatusMonitor.tsx`의 `useEffect`에 `updateServiceHealth()` 호출을 추가했는지 확인

### Q2: BlueprintFlow 노드가 보이지 않아요
**A**:
1. `nodeDefinitions.ts`에 정의 추가했는지 확인
2. `ApiNodes.tsx`에 컴포넌트 추가했는지 확인
3. `BlueprintFlowBuilder.tsx`의 `nodeTypes`에 등록했는지 확인

### Q3: API 호출이 실패해요
**A**:
1. Backend 서버가 실행 중인지 확인: `docker ps`
2. 포트가 열려있는지 확인: `curl http://localhost:5007/api/v1/health`
3. CORS 설정이 되어있는지 확인

---

**최종 업데이트**: 2026-01-17
**작성자**: Claude Code
**버전**: 2.0
