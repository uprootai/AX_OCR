# 코드 리팩토링 및 개선 계획서

> **작성일**: 2025-11-18
> **목적**: 코드 유지보수성, 확장성, 성능 개선
> **예상 기간**: 1주일 (단계별 진행)

---

## 📊 현재 상태 분석

### 🔴 심각한 문제들
1. **gateway-api/api_server.py** - **2,510 라인** (단일 파일 모놀리스)
2. **중복 코드** - 8개 API 서버에 동일한 CORS, Health Check 코드
3. **console.log** - 13개 파일에 프로덕션 로그 남아있음
4. **문서 부족** - API 레퍼런스, 배포 가이드 없음

### ⚠️ 개선 필요
5. **TestGateway.tsx** - 714 라인 (UI + 로직 혼재)
6. **api.ts** - 460 라인 (8개 API 클라이언트 단일 파일)
7. **통합 테스트** - End-to-end 파이프라인 테스트 없음

---

## 🎯 개선 목표

### 1단계: 긴급 (1-2일)
- [x] 프로젝트 전체 구조 분석 완료
- [ ] Gateway API 모듈 분리 (2,510 → 200 라인/파일)
- [ ] 공통 베이스 클래스 생성
- [ ] console.log → 로거 교체

### 2단계: 중요 (3-5일)
- [ ] React 컴포넌트 분리 (TestGateway.tsx)
- [ ] API 클라이언트 모듈화
- [ ] TODO 항목 구현 (3개)
- [ ] 통합 테스트 추가

### 3단계: 보강 (6-7일)
- [ ] 문서 업데이트 (API Ref, 배포 가이드)
- [ ] UI/UX 개선 (실시간 진행률, 비교 뷰)
- [ ] 성능 최적화 (캐싱, 배칭)

---

## 📋 상세 작업 계획

## Phase 1: Gateway API 리팩토링 ⚠️ CRITICAL

### 현재 구조 (문제점)
```
gateway-api/
└── api_server.py (2,510 lines)
    ├── 49개 함수 (26개 async)
    ├── 23개 Pydantic 모델
    ├── 10개 엔드포인트 핸들러
    └── 모든 로직이 한 파일에...
```

### 목표 구조 (개선 후)
```
gateway-api/
├── api_server.py (200 lines)        # FastAPI app + 엔드포인트만
├── config.py (50 lines)             # 환경변수, 상수
├── models/                          # Pydantic 모델
│   ├── __init__.py
│   ├── request.py (150 lines)       # 요청 모델
│   └── response.py (150 lines)      # 응답 모델
├── services/                        # 비즈니스 로직
│   ├── __init__.py
│   ├── base.py (100 lines)          # BaseService
│   ├── ocr.py (400 lines)           # OCR 관련 (eDOCr, ensemble)
│   ├── yolo.py (200 lines)          # YOLO 관련
│   ├── segmentation.py (150 lines)  # EDGNet
│   ├── tolerance.py (150 lines)     # Skin Model
│   └── quote.py (200 lines)         # 견적 생성
└── utils/                           # 유틸리티
    ├── __init__.py
    ├── image.py (200 lines)         # 이미지 처리
    ├── filters.py (100 lines)       # False Positive 필터
    └── progress.py (100 lines)      # ProgressTracker
```

### 예상 효과
- ✅ **파일당 평균 150-200 라인** (LLM 컨텍스트 효율성 ↑)
- ✅ **단일 책임 원칙** (Single Responsibility)
- ✅ **테스트 용이성** (각 서비스별 유닛 테스트)
- ✅ **병렬 개발 가능** (충돌 최소화)

### 작업 순서
1. **models/ 디렉토리 생성** → Pydantic 모델 이동
2. **services/ 디렉토리 생성** → 비즈니스 로직 이동
3. **utils/ 디렉토리 생성** → 유틸리티 함수 이동
4. **api_server.py 축소** → 엔드포인트만 남김
5. **테스트** → 모든 API 정상 작동 확인

---

## Phase 2: 공통 베이스 클래스 생성

### 목적
8개 API 서버의 중복 코드 제거 (CORS, Health Check, Startup 등)

### 생성할 공통 모듈
```
common/                              # 새 디렉토리
├── __init__.py
├── base_api.py (150 lines)          # BaseAPIServer 클래스
├── middleware.py (80 lines)         # CORS, 로깅
├── health.py (50 lines)             # 표준 Health Check
├── file_utils.py (100 lines)        # 파일 업로드/검증
└── types.py (80 lines)              # 공통 Pydantic 모델
```

### 예시: BaseAPIServer
```python
# common/base_api.py
from fastapi import FastAPI
from typing import Callable, Optional
import logging

class BaseAPIServer:
    """모든 API 서버의 베이스 클래스"""

    def __init__(
        self,
        name: str,
        version: str,
        port: int,
        load_model_fn: Optional[Callable] = None
    ):
        self.name = name
        self.version = version
        self.port = port
        self.app = FastAPI(
            title=f"{name} API",
            version=version,
            description=f"{name} Service for Drawing Analysis"
        )

        if load_model_fn:
            @self.app.on_event("startup")
            async def startup():
                logger.info(f"🚀 {self.name} Starting...")
                await load_model_fn()
                logger.info(f"✅ {self.name} Ready on port {self.port}")

        # 공통 middleware 자동 추가
        self._setup_middleware()

    def _setup_middleware(self):
        from .middleware import add_cors_middleware, add_logging_middleware
        add_cors_middleware(self.app)
        add_logging_middleware(self.app)

    def add_health_check(self):
        from .health import create_health_endpoint
        create_health_endpoint(self.app, self.name, self.version)
```

### 사용 예시 (yolo-api)
```python
# yolo-api/api_server.py (Before: 673 lines → After: 300 lines)
from common.base_api import BaseAPIServer

server = BaseAPIServer(
    name="YOLO Detection",
    version="1.0.0",
    port=5005,
    load_model_fn=load_yolo_model
)

app = server.app

@app.post("/api/v1/detect")
async def detect(file: UploadFile, ...):
    # 엔드포인트 로직만
    ...

server.add_health_check()
```

---

## Phase 3: Web UI 개선

### 3.1 console.log 제거 (13개 파일)

**Before**:
```typescript
console.log("Processing file:", file.name);
console.error("API Error:", error);
```

**After**:
```typescript
// utils/logger.ts
export const logger = {
  debug: (msg: string, data?: any) => {
    if (import.meta.env.DEV) console.log(`[DEBUG] ${msg}`, data);
  },
  info: (msg: string, data?: any) => {
    if (import.meta.env.DEV) console.log(`[INFO] ${msg}`, data);
  },
  error: (msg: string, error?: any) => {
    console.error(`[ERROR] ${msg}`, error);
    // TODO: 프로덕션에서는 Sentry 등으로 전송
  }
};

// 사용
import { logger } from '@/utils/logger';
logger.debug("Processing file", { fileName: file.name });
```

### 3.2 TestGateway.tsx 분리 (714 → 300 lines)

**Before**: UI + 로직 + 상태 모두 한 파일
**After**: 관심사 분리

```typescript
// hooks/useGatewayTest.ts (200 lines)
export function useGatewayTest() {
  const [file, setFile] = useState<File | null>(null);
  const [options, setOptions] = useState<AnalysisOptions>({...});

  const mutation = useMutation({
    mutationFn: (params: AnalysisParams) =>
      gatewayAPI.processDrawing(params),
    onSuccess: (data) => {...},
    onError: (error) => {...}
  });

  return {
    file, setFile,
    options, setOptions,
    analyze: mutation.mutate,
    result: mutation.data,
    isLoading: mutation.isLoading,
    error: mutation.error
  };
}

// components/test/GatewayResultViewer.tsx (200 lines)
export function GatewayResultViewer({ result }: Props) {
  return (
    <div>
      <YOLOResultCard data={result.yolo_results} />
      <OCRResultCard data={result.ocr_results} />
      {/* ... */}
    </div>
  );
}

// TestGateway.tsx (300 lines - UI만)
export default function TestGateway() {
  const {
    file, setFile,
    options, setOptions,
    analyze, result, isLoading, error
  } = useGatewayTest();

  return (
    <div>
      <FileUploader file={file} onFileChange={setFile} />
      <OptionsPanel options={options} onChange={setOptions} />
      <Button onClick={() => analyze({ file, options })} disabled={isLoading}>
        분석 실행
      </Button>
      {result && <GatewayResultViewer result={result} />}
    </div>
  );
}
```

### 3.3 API 클라이언트 모듈화 (460 → 50 lines/file)

**Before**: 단일 파일 `lib/api.ts`
**After**: 모듈별 분리

```
lib/
├── api.ts (50 lines)                # 통합 export
├── clients/
│   ├── gateway.ts (100 lines)       # Gateway API
│   ├── edocr2.ts (100 lines)        # eDOCr2 API
│   ├── yolo.ts (80 lines)           # YOLO API
│   ├── edgnet.ts (80 lines)         # EDGNet API
│   └── skinmodel.ts (50 lines)      # Skinmodel API
└── types.ts (50 lines)              # 공통 타입
```

---

## Phase 4: UI/UX 창의적 개선

### 4.1 실시간 진행률 (WebSocket)

**현재 문제**: 가짜 진행률 (setInterval로 시뮬레이션)
**개선안**: WebSocket으로 실제 진행률 전달

```python
# gateway-api/api_server.py
from fastapi import WebSocket

@app.websocket("/api/v1/progress/{job_id}")
async def progress_websocket(websocket: WebSocket, job_id: str):
    await websocket.accept()
    tracker = progress_trackers.get(job_id)

    while True:
        if tracker:
            await websocket.send_json({
                "percent": tracker.get_progress_percent(),
                "stage": tracker.current_stage,
                "message": tracker.get_latest_message()
            })
        await asyncio.sleep(0.5)
```

```typescript
// web-ui/src/hooks/useRealtimeProgress.ts
export function useRealtimeProgress(jobId: string) {
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState("");

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/api/v1/progress/${jobId}`);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setProgress(data.percent);
      setStage(data.stage);
    };
    return () => ws.close();
  }, [jobId]);

  return { progress, stage };
}
```

### 4.2 결과 비교 뷰 (Side-by-side)

**목적**: 여러 OCR 전략 결과 비교

```typescript
// components/comparison/ComparisonView.tsx
interface ComparisonItem {
  label: string;
  strategy: "full" | "crop" | "ensemble";
  dimensions: Dimension[];
  accuracy?: number;
}

export function ComparisonView({ results }: { results: ComparisonItem[] }) {
  return (
    <div className="grid grid-cols-3 gap-4">
      {results.map(item => (
        <Card key={item.strategy}>
          <CardHeader>
            <h3>{item.label}</h3>
            {item.accuracy && (
              <Badge variant="success">{item.accuracy}% 정확도</Badge>
            )}
          </CardHeader>
          <CardContent>
            <DimensionTable dimensions={item.dimensions} />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
```

### 4.3 인터랙티브 시각화

**현재**: 정적 이미지
**개선**: 클릭 가능한 캔버스

```typescript
// components/visualization/InteractiveCanvas.tsx
import { Stage, Layer, Image, Rect, Text } from 'react-konva';

export function InteractiveCanvas({
  imageUrl,
  detections
}: Props) {
  const [selectedDetection, setSelectedDetection] = useState<Detection | null>(null);

  return (
    <div>
      <Stage width={1920} height={1080}>
        <Layer>
          <KonvaImage src={imageUrl} />
          {detections.map(det => (
            <Group key={det.id}>
              <Rect
                x={det.bbox.x}
                y={det.bbox.y}
                width={det.bbox.width}
                height={det.bbox.height}
                stroke={getColorByClass(det.class_name)}
                strokeWidth={2}
                onClick={() => setSelectedDetection(det)}
                onTap={() => setSelectedDetection(det)}
              />
              <Text
                text={`${det.class_name}: ${det.value || ''}`}
                x={det.bbox.x}
                y={det.bbox.y - 20}
                fill="white"
                fontSize={14}
              />
            </Group>
          ))}
        </Layer>
      </Stage>

      {selectedDetection && (
        <DetailPanel detection={selectedDetection} />
      )}
    </div>
  );
}
```

### 4.4 드래그 앤 드롭 파일 업로드

```typescript
// components/upload/DragDropUpload.tsx
export function DragDropUpload({ onFileSelect }: Props) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      onFileSelect(file);
    }
  };

  return (
    <div
      className={cn(
        "border-2 border-dashed rounded-lg p-8 text-center transition",
        isDragging ? "border-blue-500 bg-blue-50" : "border-gray-300"
      )}
      onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
    >
      <Upload className="mx-auto h-12 w-12 text-gray-400" />
      <p className="mt-2 text-sm text-gray-600">
        이미지를 드래그하거나 클릭하여 업로드
      </p>
      <input type="file" className="hidden" accept="image/*" />
    </div>
  );
}
```

### 4.5 모바일 반응형

```typescript
// tailwind.config.js 활용
<div className="
  grid
  grid-cols-1        /* 모바일: 1열 */
  md:grid-cols-2     /* 태블릿: 2열 */
  lg:grid-cols-3     /* 데스크톱: 3열 */
  gap-4
">
  {/* 카드 목록 */}
</div>
```

---

## Phase 5: 성능 최적화

### 5.1 Redis 캐싱

```python
# gateway-api/api_server.py
import redis
import hashlib

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

def get_file_hash(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()

async def call_yolo_detect_cached(file_bytes: bytes, ...):
    file_hash = get_file_hash(file_bytes)
    cache_key = f"yolo:{file_hash}:{conf_threshold}:{iou_threshold}"

    # 캐시 확인
    cached = redis_client.get(cache_key)
    if cached:
        logger.info(f"Cache hit for {cache_key}")
        return json.loads(cached)

    # 실제 호출
    result = await call_yolo_detect(file_bytes, ...)

    # 캐시 저장 (1시간)
    redis_client.setex(cache_key, 3600, json.dumps(result))
    return result
```

### 5.2 YOLO 배치 처리

```python
# gateway-api/services/yolo.py
async def process_yolo_crops_batch(crops: List[bytes]) -> List[OCRResult]:
    """배치 처리로 성능 향상 (2-3배)"""

    # 모든 crop을 한번에 전송
    form_data = aiohttp.FormData()
    for i, crop in enumerate(crops):
        form_data.add_field(
            f'files',
            crop,
            filename=f'crop_{i}.jpg',
            content_type='image/jpeg'
        )

    async with session.post(f"{EDOCR_URL}/api/v1/batch_ocr", data=form_data) as resp:
        return await resp.json()
```

### 5.3 병렬 처리 극대화

```python
# gateway-api/api_server.py
async def process_drawing_optimized(...):
    # 모든 독립적인 작업을 병렬로
    tasks = []

    # YOLO + eDOCr + EDGNet + Skinmodel 동시 실행 가능한 것들
    if use_yolo:
        tasks.append(call_yolo_detect(...))
    if use_ocr:
        tasks.append(call_edocr2_ocr(...))
    if use_segmentation:
        tasks.append(call_edgnet_segment(...))

    # 한번에 실행
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Skinmodel은 OCR 결과 필요하므로 이후 실행
    if use_tolerance and ocr_results:
        tolerance_result = await call_skinmodel_predict(ocr_results)
```

---

## Phase 6: 문서 업데이트

### 6.1 생성할 문서
1. **API_REFERENCE.md** - 모든 엔드포인트 상세 설명
2. **DEPLOYMENT_GUIDE.md** - 프로덕션 배포 가이드
3. **PERFORMANCE_TUNING.md** - 성능 최적화 가이드
4. **SECURITY_GUIDE.md** - 보안 Best Practices

### 6.2 업데이트할 문서
1. **README.md** - 새로운 기능, 아키텍처 반영
2. **CLAUDE.md** - 리팩토링된 구조 반영
3. **PROJECT_STRUCTURE.md** - 최신 디렉토리 구조

---

## ✅ 검증 체크리스트

### 리팩토링 후 확인 사항
- [ ] 모든 API 엔드포인트 정상 작동 (Postman 테스트)
- [ ] Web UI에서 전체 파이프라인 실행 성공
- [ ] YOLO Crop OCR 정상 작동
- [ ] 앙상블 전략 정상 작동
- [ ] 시각화 이미지 정상 표시
- [ ] 성능 저하 없음 (처리 시간 비교)
- [ ] 메모리 사용량 증가 없음
- [ ] 에러 핸들링 정상 작동
- [ ] 로그 출력 정상
- [ ] 문서 최신 상태 유지

### 성능 목표
- Gateway 처리 시간: **8-12초 → <8초**
- YOLO inference: **1-2초 유지**
- eDOCr2 OCR: **3-5초 유지**
- 전체 파이프라인: **40-50초 → 30-40초** (하이브리드 모드)

---

## 🚀 실행 계획

### Day 1-2: Gateway API 리팩토링
```bash
# 1. 백업
git checkout -b refactor/gateway-api
cp -r gateway-api gateway-api.backup

# 2. 모듈 생성
mkdir -p gateway-api/{models,services,utils}

# 3. 코드 이동 (단계별)
# - models/ 먼저
# - utils/ 다음
# - services/ 마지막
# - api_server.py 축소

# 4. 테스트
python gateway-api/api_server.py  # 서버 시작 확인
curl localhost:8000/api/v1/health  # Health check
# Web UI에서 전체 테스트

# 5. 커밋
git add gateway-api
git commit -m "refactor: Split gateway-api into modules (2510 → ~200 lines/file)"
```

### Day 3: 공통 베이스 클래스
```bash
# 1. common/ 디렉토리 생성
mkdir common
touch common/{__init__.py,base_api.py,middleware.py,health.py}

# 2. BaseAPIServer 구현

# 3. 한 서비스에 적용 (yolo-api)

# 4. 테스트 후 나머지 서비스 적용

git commit -m "feat: Add common base classes for all API servers"
```

### Day 4: Web UI 개선
```bash
cd web-ui

# 1. Logger 유틸리티
mkdir src/utils
touch src/utils/logger.ts

# 2. console.log 교체 (13개 파일)

# 3. TestGateway.tsx 분리
mkdir src/hooks src/components/test
touch src/hooks/useGatewayTest.ts
touch src/components/test/GatewayResultViewer.tsx

# 4. 빌드 & 테스트
npm run build
npm run dev

git commit -m "refactor: Improve web-ui structure and remove console.log"
```

### Day 5-6: UI/UX 개선
```bash
# 1. WebSocket 진행률
# 2. 비교 뷰
# 3. 인터랙티브 캔버스
# 4. 드래그 앤 드롭

git commit -m "feat: Add creative UI/UX improvements"
```

### Day 7: 문서화 & 마무리
```bash
# 1. 문서 업데이트
# 2. 최종 테스트
# 3. 성능 벤치마크
# 4. PR 생성

git commit -m "docs: Update all documentation for refactored codebase"
git push origin refactor/gateway-api
```

---

## 🎯 기대 효과

### 코드 품질
- ✅ 파일당 평균 라인수: **2,510 → ~200** (93% 감소)
- ✅ 코드 중복: **~500 라인 제거** (8개 서버 공통 코드)
- ✅ 테스트 커버리지: **0% → 60%+** (단위 테스트 추가)

### 개발 생산성
- ✅ LLM 컨텍스트 효율: **10배 향상**
- ✅ 신규 기능 추가 시간: **50% 단축**
- ✅ 버그 수정 시간: **40% 단축**

### 사용자 경험
- ✅ 실시간 진행률: **사용자 대기 불안감 감소**
- ✅ 인터랙티브 시각화: **결과 이해도 향상**
- ✅ 드래그 앤 드롭: **업로드 편의성 향상**
- ✅ 모바일 지원: **접근성 향상**

### 성능
- ✅ 처리 시간: **20-30% 단축** (캐싱, 배칭)
- ✅ 응답 속도: **캐시 히트 시 즉시 응답**
- ✅ 메모리 사용: **최적화로 10% 감소**

---

## ⚠️ 주의사항

### 리팩토링 중 유의점
1. **한 번에 하나씩** - 큰 변경을 작은 단계로 나눔
2. **테스트 우선** - 변경 후 즉시 테스트
3. **백업 필수** - Git 브랜치 활용
4. **문서 동기화** - 코드 변경 시 문서도 함께 업데이트

### 롤백 계획
만약 문제 발생 시:
```bash
# 백업 브랜치로 복구
git checkout main
git merge --abort  # 머지 중이었다면

# 또는 특정 커밋으로
git reset --hard <commit-hash>
```

---

## 📞 질문 & 피드백

이 계획서를 검토해주시고:
1. **우선순위 조정**이 필요한가요?
2. **추가/삭제**할 작업이 있나요?
3. **일정**이 적절한가요?

승인해주시면 즉시 작업을 시작하겠습니다! 🚀
