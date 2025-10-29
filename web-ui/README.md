# AX 도면 분석 시스템 - Web UI

React + Vite + TypeScript 기반의 디버깅 중심 웹 인터페이스입니다.

## 🎉 완성! 전체 구현 완료

모든 Phase (1-7)가 완료되었으며, 프로덕션 배포 준비가 완료되었습니다.

---

## 🎯 구현된 기능

### ✅ Phase 1-3: 기본 인프라 (완료)
- **프로젝트 설정**: React 18 + Vite + TypeScript + Tailwind CSS v3
- **라우팅**: React Router v6 (8개 페이지)
- **레이아웃**: Header, Sidebar, Layout 컴포넌트
- **API 클라이언트**: Gateway, eDOCr2, EDGNet, Skin Model
- **상태 관리**: Zustand (UI, Analysis, Monitoring)
- **서버 상태**: TanStack Query
- **실시간 API 모니터링**: 30초 자동 헬스체크

### ✅ Phase 4: 디버깅 컴포넌트 (완료)
- **FileUploader**: 드래그 앤 드롭, 미리보기, 유효성 검사
- **JSONViewer**: 접을 수 있는 구조, 문법 강조, 복사 기능
- **RequestInspector**: 요청/응답 비교, 타임라인, 에러 상세
- **RequestTimeline**: API 호출 시간순 목록, 상태 표시
- **ErrorPanel**: 상황별 에러 메시지, 해결 제안, 재시도

### ✅ Phase 5: 테스트 페이지 (완료)
- **TestEdocr2** (`/test/edocr2`): OCR 테스트, 치수/GD&T/텍스트 추출
- **TestEdgnet** (`/test/edgnet`): 세그멘테이션, 그래프 구조, 벡터화
- **TestSkinmodel** (`/test/skinmodel`): 공차 예측, 제조 가능성 분석
- **TestGateway** (`/test/gateway`): 통합 파이프라인, 전체 오케스트레이션

### ✅ Phase 6: 통합 분석 페이지 (완료)
- **Analyze** (`/analyze`): 프로덕션 레벨 분석 UI
  - 파일 업로드 (Drag & Drop)
  - 분석 옵션 선택 (OCR/Segmentation/Tolerance/Visualize)
  - 실시간 진행 상황 표시 (Progress Bar with Stages)
  - 탭 기반 결과 시각화 (Overview/OCR/Segmentation/Tolerance)
  - JSON 다운로드 기능

### ✅ Phase 7: Docker 배포 (완료)
- **Dockerfile**: 멀티스테이지 빌드 (Node.js → Nginx)
- **nginx.conf**: SPA 라우팅, Gzip 압축, 캐싱, 보안 헤더
- **.dockerignore**: 빌드 최적화
- **docker-compose.yml**: web-ui 서비스 추가 (포트 5173)

---

## 🚀 빠른 시작

### 개발 모드

```bash
# 의존성 설치
npm install

# 개발 서버 실행
npm run dev

# 브라우저에서 접속
# http://localhost:5173
```

### 프로덕션 빌드

```bash
# 빌드
npm run build

# 빌드 결과 미리보기
npm run preview
```

---

## 🐳 Docker 배포

### 개별 실행

```bash
# Web UI만 Docker로 실행
docker build -t ax-web-ui .
docker run -p 5173:80 ax-web-ui

# 브라우저에서 접속
# http://localhost:5173
```

### 전체 시스템 실행

```bash
# 프로젝트 루트 디렉토리에서 실행
cd /home/uproot/ax/poc

# 전체 시스템 빌드 및 실행
docker-compose up --build

# 백그라운드 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f web-ui

# 중지
docker-compose down
```

### 서비스 포트
- **Web UI**: http://localhost:5173
- **Gateway API**: http://localhost:8000
- **eDOCr2 API**: http://localhost:5001
- **EDGNet API**: http://localhost:5012
- **Skin Model API**: http://localhost:5003

---

## 📁 프로젝트 구조

```
web-ui/
├── src/
│   ├── components/
│   │   ├── ui/              ✅ 기본 UI (Button, Card, Badge)
│   │   ├── layout/          ✅ 레이아웃 (Header, Sidebar, Layout)
│   │   ├── monitoring/      ✅ 모니터링 (ServiceHealthCard, APIStatusMonitor)
│   │   └── debug/           ✅ 디버깅 (FileUploader, JSONViewer, RequestInspector, etc)
│   │
│   ├── pages/
│   │   ├── Landing.tsx             ✅ 랜딩 페이지
│   │   ├── dashboard/Dashboard.tsx ✅ 대시보드 + 실시간 모니터링
│   │   ├── test/
│   │   │   ├── TestHub.tsx         ✅ 테스트 허브
│   │   │   ├── TestEdocr2.tsx      ✅ OCR 테스트
│   │   │   ├── TestEdgnet.tsx      ✅ 세그멘테이션 테스트
│   │   │   ├── TestSkinmodel.tsx   ✅ 공차 분석 테스트
│   │   │   └── TestGateway.tsx     ✅ 통합 파이프라인 테스트
│   │   ├── analyze/Analyze.tsx     ✅ 통합 분석 페이지
│   │   └── monitor/Monitor.tsx     ✅ 모니터링 페이지
│   │
│   ├── lib/api.ts           ✅ API 클라이언트 (4개 서비스 통합)
│   ├── store/               ✅ 상태 관리 (UI, Analysis, Monitoring)
│   └── types/api.ts         ✅ 타입 정의
│
├── Dockerfile               ✅ Docker 이미지 빌드
├── nginx.conf               ✅ Nginx 설정
├── .dockerignore            ✅ Docker 빌드 최적화
├── .env                     ✅ 환경 변수
└── README.md                ✅ 문서
```

---

## 🛠️ API 사용법

```typescript
import { gatewayApi, edocr2Api, edgnetApi, skinmodelApi } from './lib/api';

// 헬스 체크
const health = await gatewayApi.healthCheck();

// 통합 분석 (Gateway API)
const result = await gatewayApi.process(file, {
  use_ocr: true,
  use_segmentation: true,
  use_tolerance: true,
  visualize: false,
});

// 개별 API 호출
const ocrResult = await edocr2Api.ocr(file, {
  extract_dimensions: true,
  extract_gdt: true,
});

const segResult = await edgnetApi.segment(file, {
  visualize: true,
  num_classes: 3,
});

const tolResult = await skinmodelApi.tolerance({
  dimensions: [...],
  material: {...},
});
```

---

## 📊 빌드 결과

```
dist/index.html                   0.45 kB │ gzip:   0.29 kB
dist/assets/index-*.css          20.67 kB │ gzip:   4.52 kB
dist/assets/index-*.js          427.69 kB │ gzip: 124.11 kB
✓ built in 3.77s
```

---

## 🎨 주요 기능 상세

### 1. 실시간 API 모니터링
- 각 서비스의 상태를 30초마다 자동 체크
- 응답 시간, 에러 카운트 표시
- 색상 코드로 상태 표시 (Healthy/Degraded/Error)

### 2. 디버깅 기능
- 모든 API 요청을 추적하여 저장
- 요청/응답 데이터를 상세히 표시
- 에러 발생 시 상황별 해결 제안
- 타임라인으로 API 호출 순서 시각화

### 3. 통합 분석
- 여러 서비스를 한 번에 실행
- 실시간 진행 상황 표시
- 탭 기반 결과 표시 (Overview/OCR/Segmentation/Tolerance)
- JSON 다운로드 지원

### 4. 개별 API 테스트
- 각 API를 독립적으로 테스트
- 옵션 설정 및 결과 확인
- Request/Response Inspector 제공

---

## 📚 기술 스택

### Frontend
- **React 18**: UI 라이브러리
- **Vite**: 빌드 도구
- **TypeScript 5**: 타입 안정성
- **Tailwind CSS v3**: 유틸리티 CSS
- **React Router v6**: 클라이언트 라우팅

### State Management
- **TanStack Query**: 서버 상태 관리 (캐싱, 자동 refetch)
- **Zustand**: 클라이언트 상태 관리 (UI, Analysis, Monitoring)

### HTTP & API
- **Axios**: HTTP 클라이언트
- **RESTful API**: 4개 마이크로서비스 통합

### UI & Icons
- **Lucide React**: 아이콘
- **date-fns**: 날짜 포맷팅

### DevOps
- **Docker**: 컨테이너화
- **Nginx**: 프로덕션 웹 서버
- **Multi-stage Build**: 최적화된 이미지 생성

---

## 🔧 환경 변수

`.env` 파일 설정:

```env
# API URLs
VITE_GATEWAY_URL=http://localhost:8000
VITE_EDOCR2_URL=http://localhost:5001
VITE_EDGNET_URL=http://localhost:5012
VITE_SKINMODEL_URL=http://localhost:5003
```

Docker 환경에서는 `docker-compose.yml`에서 자동 설정됩니다.

---

## 🧪 테스트 가이드

### 1. 대시보드 확인
1. http://localhost:5173 접속
2. Dashboard 메뉴 클릭
3. API Health Status 카드에서 모든 서비스 상태 확인

### 2. 개별 API 테스트
1. Test 메뉴 → 원하는 API 선택
2. 파일 업로드 또는 파라미터 입력
3. 실행 버튼 클릭
4. 결과 및 Request/Response 확인

### 3. 통합 분석
1. Analyze 메뉴 클릭
2. 파일 업로드 (Drag & Drop)
3. 분석 옵션 선택
4. 분석 시작 버튼 클릭
5. 진행 상황 확인
6. 탭으로 결과 확인 (Overview/OCR/Segmentation/Tolerance)

---

## 🎯 핵심 달성 사항

✅ **각각의 API 성능을 확실하게 육안으로 확인 가능**
- 실시간 응답 시간 표시
- 상태 색상 코드
- Request Timeline
- Performance Metrics

✅ **모델 문제 발생 시 충분한 디버깅 가능**
- 요청 페이로드 전체 확인
- 응답 데이터 상세 표시
- 에러 상황별 해결 제안
- 요청 추적 기능
- JSON Viewer로 raw 데이터 검사

---

## 📖 관련 문서

- 기획 문서: `/home/uproot/ax/poc/WEB_UI_PLANNING.md`
- 디버깅 스펙: `/home/uproot/ax/poc/WEB_UI_DEBUGGING_SPEC.md`
- 구현 상태: `/home/uproot/ax/poc/WEB_UI_STATUS.md`

---

## 🚀 프로덕션 배포

### Nginx 설정 포인트
- SPA 라우팅 지원 (`try_files $uri $uri/ /index.html`)
- Gzip 압축 활성화
- 정적 파일 캐싱 (1년)
- 보안 헤더 추가
- Health check 엔드포인트 (`/health`)

### Docker 최적화
- 멀티스테이지 빌드로 이미지 크기 최소화
- Alpine Linux 기반 경량 이미지
- `.dockerignore`로 불필요한 파일 제외
- Health check 설정으로 컨테이너 상태 모니터링

---

**버전**: 1.0.0 (Production Ready)
**작성일**: 2025-10-27
**최종 업데이트**: 2025-10-27

**상태**: ✅ 전체 Phase 완료, 프로덕션 배포 준비 완료
