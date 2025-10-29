# AX 웹 UI - 디버깅 & 모니터링 중심 설계

**목적**: 각 API의 성능을 육안으로 확인하고, 문제 발생 시 즉시 디버깅 가능한 웹 인터페이스

---

## 🎯 핵심 요구사항

1. **각 API 성능 실시간 모니터링**
   - 응답 시간 (ms)
   - 성공/실패 상태
   - 처리 속도

2. **디버깅 가능성**
   - 요청/응답 원본 데이터
   - 에러 메시지 상세
   - API 호출 타임라인
   - 로그 뷰어

3. **개별 API 테스트**
   - eDOCr2 단독 실행
   - EDGNet 단독 실행
   - Skin Model 단독 실행
   - Gateway 통합 실행

---

## 📊 수정된 페이지 구조

```
/                          → 랜딩 (간단한 소개)
/dashboard                 → 통합 대시보드 (NEW)
  ├─ API 상태 모니터링
  ├─ 실시간 성능 차트
  └─ 최근 요청 타임라인

/test                      → API 테스트 허브 (NEW)
  ├─ /test/edocr2          → eDOCr2 단독 테스트
  ├─ /test/edgnet          → EDGNet 단독 테스트
  ├─ /test/skinmodel       → Skin Model 단독 테스트
  └─ /test/gateway         → Gateway 통합 테스트

/analyze                   → 실제 분석 (프로덕션)
  └─ 디버그 패널 포함

/monitor                   → 상세 모니터링 (NEW)
  ├─ API 성능 히스토리
  ├─ 에러 로그
  └─ 시스템 메트릭

/debug/:requestId          → 특정 요청 디버깅 (NEW)
```

---

## 🔍 주요 컴포넌트

### 1. API Status Monitor
```
┌─────────────────────────────────────────────────────┐
│ 🔧 API 상태 모니터                                    │
├─────────────────────────────────────────────────────┤
│                                                      │
│ ┌──────────────┬──────────┬──────────┬────────────┐ │
│ │ Service      │ Status   │ Latency  │ Last Check │ │
│ ├──────────────┼──────────┼──────────┼────────────┤ │
│ │ ● eDOCr2     │ Healthy  │ 23ms     │ 2s ago    │ │
│ │ ● EDGNet     │ Healthy  │ 45ms     │ 2s ago    │ │
│ │ ● Skin Model │ Healthy  │ 18ms     │ 2s ago    │ │
│ │ ● Gateway    │ Healthy  │ 12ms     │ 2s ago    │ │
│ └──────────────┴──────────┴──────────┴────────────┘ │
│                                                      │
│ [🔄 Refresh] [⚙️ Settings] [📊 Details]             │
└─────────────────────────────────────────────────────┘
```

**표시 정보**:
- 실시간 상태 (● 녹색: Healthy, ● 빨강: Error, ● 노랑: Degraded)
- 평균 응답 시간 (ms)
- 마지막 체크 시간
- 성공률 (%)

### 2. Request Timeline Viewer
```
┌─────────────────────────────────────────────────────┐
│ ⏱️ Request Timeline                                  │
├─────────────────────────────────────────────────────┤
│                                                      │
│ Total: 4.55s                                         │
│                                                      │
│ ┌──────────────────────────────────────────────────┐│
│ │ Upload        │███░░░░░░░░░░░░░│ 0.5s            ││
│ │ eDOCr2 API   │░░░███████░░░░░░│ 2.0s            ││
│ │ EDGNet API   │░░░████████████░│ 3.0s            ││
│ │ Skin Model   │░░░░░░░░░░░███░│ 1.5s            ││
│ │ Response     │░░░░░░░░░░░░░░█│ 0.05s           ││
│ └──────────────────────────────────────────────────┘│
│                                                      │
│ 🔍 병렬 실행: eDOCr2 + EDGNet (max: 3.0s)           │
│ 🔍 순차 실행: Skin Model (depends on eDOCr2)        │
└─────────────────────────────────────────────────────┘
```

**기능**:
- 각 단계별 소요 시간 시각화
- 병렬/순차 실행 구분
- 병목 구간 하이라이트
- 클릭 시 상세 정보

### 3. Request/Response Inspector
```
┌─────────────────────────────────────────────────────┐
│ 🔍 Request/Response Inspector                        │
├─────────────────────────────────────────────────────┤
│                                                      │
│ [Request] [Response] [Headers] [Timing]             │
│ ━━━━━━━                                             │
│                                                      │
│ POST http://edocr2-api:5001/api/v1/ocr              │
│                                                      │
│ ┌────────────────────┬────────────────────────────┐ │
│ │ Request Body       │ Response Body              │ │
│ ├────────────────────┼────────────────────────────┤ │
│ │ {                  │ {                          │ │
│ │   "file": "...",   │   "status": "success",     │ │
│ │   "extract_dims":  │   "data": {                │ │
│ │     true,          │     "dimensions": [        │ │
│ │   "extract_gdt":   │       {                    │ │
│ │     true           │         "value": 392.0,    │ │
│ │ }                  │         "unit": "mm",      │ │
│ │                    │         "tolerance": "±0.1"│ │
│ │                    │       }                    │ │
│ │                    │     ]                      │ │
│ │                    │   }                        │ │
│ │                    │ }                          │ │
│ └────────────────────┴────────────────────────────┘ │
│                                                      │
│ [📋 Copy] [⤓ Download JSON] [🔗 cURL Command]       │
└─────────────────────────────────────────────────────┘
```

**기능**:
- JSON 포매팅 및 신택스 하이라이트
- 요청/응답 비교
- cURL 명령어 생성
- 데이터 복사/다운로드

### 4. Error Details Panel
```
┌─────────────────────────────────────────────────────┐
│ ⚠️ Error Details                                     │
├─────────────────────────────────────────────────────┤
│                                                      │
│ Service: Skin Model API                              │
│ Status Code: 422 Unprocessable Entity                │
│ Timestamp: 2025-10-27 14:23:45                       │
│                                                      │
│ ┌────────────────────────────────────────────────┐  │
│ │ Error Message:                                 │  │
│ │                                                │  │
│ │ Validation failed for field 'tolerance'        │  │
│ │ Expected: float                                │  │
│ │ Received: string "±0.1"                        │  │
│ │                                                │  │
│ │ Location: gateway-api:api_server.py:189        │  │
│ └────────────────────────────────────────────────┘  │
│                                                      │
│ 🔍 Possible Causes:                                  │
│ • Data type mismatch                                 │
│ • Missing tolerance parsing logic                    │
│                                                      │
│ 💡 Suggested Fix:                                    │
│ • Convert string "±0.1" to float 0.1                 │
│ • Add tolerance parser in Gateway                    │
│                                                      │
│ [📋 Copy Stack Trace] [🔗 Related Logs]             │
└─────────────────────────────────────────────────────┘
```

**기능**:
- 에러 메시지 상세
- 스택 트레이스
- 원인 분석
- 해결 제안

### 5. Performance Chart
```
┌─────────────────────────────────────────────────────┐
│ 📈 API Performance (Last 10 Requests)                │
├─────────────────────────────────────────────────────┤
│                                                      │
│  5s ┤                                                │
│     │           ╭─╮                                  │
│  4s ┤         ╭─╯ ╰╮                                 │
│     │       ╭─╯     ╰─╮                              │
│  3s ┤     ╭─╯         ╰─╮    ╭─╮                     │
│     │   ╭─╯             ╰──╮─╯ ╰─╮                   │
│  2s ┤ ╭─╯                  ╰─────╰─╮                 │
│     │─╯                            ╰─                │
│  1s ┤                                                │
│     └────────────────────────────────────            │
│      #1  #2  #3  #4  #5  #6  #7  #8  #9  #10        │
│                                                      │
│ ━ Total  ━ eDOCr2  ━ EDGNet  ━ Skin Model          │
│                                                      │
│ Avg: 4.2s  Min: 3.8s  Max: 5.1s  StdDev: 0.4s      │
└─────────────────────────────────────────────────────┘
```

**기능**:
- 실시간 성능 차트
- 각 API별 색상 구분
- 통계 정보 (평균, 최소, 최대)
- 이상치 탐지

### 6. Individual API Test Panel
```
┌─────────────────────────────────────────────────────┐
│ 🧪 eDOCr2 API Test                                   │
├─────────────────────────────────────────────────────┤
│                                                      │
│ Endpoint: http://localhost:5001/api/v1/ocr          │
│                                                      │
│ 📤 Upload File                                       │
│ ┌──────────────────────────────────────────────────┐│
│ │ [📁 Select File or Drag & Drop]                  ││
│ └──────────────────────────────────────────────────┘│
│                                                      │
│ ⚙️ Options                                           │
│ ☑ Extract Dimensions                                 │
│ ☑ Extract GD&T                                       │
│ ☑ Extract Text                                       │
│ ☐ Use VL Model                                       │
│                                                      │
│ [🚀 Run Test]                                        │
│                                                      │
│ ─────────────────────────────────────────────────   │
│                                                      │
│ ✅ Status: Success                                   │
│ ⏱️ Response Time: 2.03s                              │
│                                                      │
│ 📊 Results:                                          │
│ • Dimensions Found: 2                                │
│ • GD&T Found: 2                                      │
│ • Processing Time: 2.0s                              │
│                                                      │
│ [View Detailed Results] [View Request/Response]     │
└─────────────────────────────────────────────────────┘
```

**기능**:
- 개별 API 단독 테스트
- 파라미터 커스터마이징
- 즉시 결과 확인
- 요청/응답 인스펙터 연동

### 7. Log Viewer
```
┌─────────────────────────────────────────────────────┐
│ 📜 Live Logs                                         │
├─────────────────────────────────────────────────────┤
│                                                      │
│ [All] [Info] [Warning] [Error] | 🔍 Search          │
│                                                      │
│ ┌──────────────────────────────────────────────────┐│
│ │ 14:23:45 [INFO] Gateway: Processing request      ││
│ │ 14:23:45 [INFO] Calling eDOCr2 API               ││
│ │ 14:23:47 [INFO] eDOCr2 response: 200 OK          ││
│ │ 14:23:47 [INFO] Calling EDGNet API               ││
│ │ 14:23:50 [INFO] EDGNet response: 200 OK          ││
│ │ 14:23:50 [INFO] Calling Skin Model API           ││
│ │ 14:23:50 [ERROR] Skin Model: 422 Validation Error││
│ │ 14:23:50 [ERROR] Detail: tolerance field invalid ││
│ │ 14:23:50 [ERROR] Expected float, got string      ││
│ └──────────────────────────────────────────────────┘│
│                                                      │
│ [Pause] [Clear] [⤓ Download Logs]                   │
└─────────────────────────────────────────────────────┘
```

**기능**:
- 실시간 로그 스트림
- 레벨별 필터링
- 검색 기능
- 로그 다운로드

---

## 🎨 메인 레이아웃

```
┌────────────────────────────────────────────────────────────────┐
│ [Logo] AX Debug Console  [Dashboard][Test][Analyze][Monitor]  │
├────────┬───────────────────────────────────────────────────────┤
│        │                                                        │
│ 🏠 Home│  ┌──────────────────────────────────────────────────┐ │
│ 🧪 Test│  │ 🔧 API Health Status                              │ │
│ 📊 Mon │  │ ● eDOCr2: 23ms  ● EDGNet: 45ms  ● Skin: 18ms    │ │
│ ⚙️ Set │  └──────────────────────────────────────────────────┘ │
│        │                                                        │
│ ━━━━━━ │  ┌──────────────────────────────────────────────────┐ │
│        │  │ 📈 Performance Chart                              │ │
│ 🚀 Quick│  │                                                   │ │
│  Test  │  │   [Performance graph here]                        │ │
│        │  │                                                   │ │
│ eDOCr2 │  └──────────────────────────────────────────────────┘ │
│ EDGNet │                                                        │
│ Skin M │  ┌──────────────────────────────────────────────────┐ │
│ Gateway│  │ 📜 Recent Activity                                │ │
│        │  │                                                   │ │
│        │  │ #12: A12-311197.jpg - ✅ Success (4.5s)          │ │
│        │  │ #11: Shaft-Rev2.png - ✅ Success (4.2s)          │ │
│        │  │ #10: Drawing-03.pdf - ⚠️ Partial (5.1s)          │ │
│        │  │                                                   │ │
│        │  └──────────────────────────────────────────────────┘ │
│        │                                                        │
└────────┴────────────────────────────────────────────────────────┘
```

---

## 🛠️ 기술 스택 (디버깅 중심)

```javascript
{
  // 기본
  "framework": "React 18 + Vite + TypeScript",
  "styling": "Tailwind CSS",
  "ui": "Shadcn/ui + Radix UI",

  // 상태 관리
  "state": "Zustand",
  "serverState": "TanStack Query",

  // 디버깅 특화
  "jsonViewer": "react-json-view",           // JSON 포매팅
  "codeHighlight": "prism-react-renderer",   // 신택스 하이라이트
  "chart": "Recharts",                       // 성능 차트
  "timeline": "react-chrono",                // 타임라인
  "logging": "loglevel",                     // 로깅

  // 개발 도구
  "devTools": {
    "reactQuery": "@tanstack/react-query-devtools",
    "zustand": "zustand/middleware/devtools"
  }
}
```

---

## 📝 구현 우선순위

### Phase 1: 기본 인프라 (2-3시간)
- [x] 프로젝트 생성
- [ ] UI 라이브러리 설정
- [ ] 라우팅 구조
- [ ] API 클라이언트

### Phase 2: 모니터링 컴포넌트 (4-5시간)
- [ ] API Status Monitor
- [ ] Request Timeline Viewer
- [ ] Performance Chart
- [ ] Health Check 실시간 업데이트

### Phase 3: 디버깅 컴포넌트 (4-5시간)
- [ ] Request/Response Inspector
- [ ] Error Details Panel
- [ ] Log Viewer
- [ ] JSON Diff Viewer

### Phase 4: 테스트 페이지 (4-5시간)
- [ ] Individual API Test Panels (x4)
- [ ] Gateway Integration Test
- [ ] Batch Test Runner

### Phase 5: 통합 분석 페이지 (3-4시간)
- [ ] File Upload
- [ ] Analysis Execution
- [ ] Results Display (with debug panel)

### Phase 6: Docker & 배포 (2시간)
- [ ] Dockerfile
- [ ] Nginx 설정
- [ ] docker-compose 통합

---

## 🎯 핵심 기능

### 1. 실시간 API 헬스 모니터링
```typescript
// 30초마다 자동 체크
useQuery({
  queryKey: ['health'],
  queryFn: healthCheck,
  refetchInterval: 30000
})
```

### 2. 요청 추적 (Request Tracking)
```typescript
interface RequestTrace {
  id: string
  timestamp: Date
  endpoint: string
  method: string
  status: number
  duration: number
  request: any
  response: any
  error?: string
  timeline: {
    upload: number
    edocr2?: number
    edgnet?: number
    skinmodel?: number
    response: number
  }
}

// 모든 요청을 추적
const [traces, setTraces] = useState<RequestTrace[]>([])
```

### 3. 에러 캡처 및 분석
```typescript
function analyzeError(error: APIError) {
  return {
    service: detectService(error.url),
    statusCode: error.status,
    message: error.message,
    possibleCauses: inferCauses(error),
    suggestedFixes: inferFixes(error)
  }
}
```

### 4. 성능 메트릭 수집
```typescript
interface PerformanceMetrics {
  avgResponseTime: number
  minResponseTime: number
  maxResponseTime: number
  successRate: number
  errorRate: number
  p50: number
  p90: number
  p99: number
}
```

---

## 🚀 시작하기

바로 Phase 1을 시작하겠습니다:

1. ✅ 프로젝트 생성
2. ✅ 기본 설정
3. ✅ 첫 번째 컴포넌트 구현

이제 코드를 작성하겠습니다!
