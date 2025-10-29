# AX 실증산단 웹 UI 기획서

**프로젝트명**: AX 도면 분석 시스템 웹 인터페이스
**기술 스택**: React 18 + Vite + TypeScript
**작성일**: 2025-10-27
**버전**: 1.0

---

## 📑 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [사용자 플로우](#2-사용자-플로우)
3. [페이지 구조](#3-페이지-구조)
4. [컴포넌트 설계](#4-컴포넌트-설계)
5. [기능 명세](#5-기능-명세)
6. [UI/UX 와이어프레임](#6-uiux-와이어프레임)
7. [기술 스택](#7-기술-스택)
8. [상태 관리](#8-상태-관리)
9. [API 통합](#9-api-통합)
10. [구현 로드맵](#10-구현-로드맵)

---

## 1. 프로젝트 개요

### 1.1 목적
공학 도면을 업로드하여 자동으로 분석하고, OCR, 세그멘테이션, 공차 예측, 제조 견적을 제공하는 웹 애플리케이션

### 1.2 타겟 사용자
- 제조업체 엔지니어
- 품질 관리 담당자
- 구매/영업 담당자

### 1.3 핵심 가치
- ⚡ **빠른 분석**: 도면 업로드 후 5초 내 결과 제공
- 🎯 **정확성**: AI 기반 자동 분석
- 💰 **자동 견적**: 즉시 제조 비용 산출
- 📊 **시각화**: 직관적인 결과 표시

---

## 2. 사용자 플로우

### 2.1 메인 플로우

```
시작
 │
 ├─► 랜딩 페이지
 │    │
 │    ├─► [로그인] ──► 대시보드
 │    └─► [둘러보기] ──► 기능 소개
 │
 └─► 대시보드 (메인 작업 공간)
      │
      ├─► 1. 파일 업로드
      │     │
      │     ├─ 드래그 앤 드롭
      │     └─ 파일 선택 버튼
      │
      ├─► 2. 옵션 선택
      │     │
      │     ├─ OCR (치수/GD&T 추출)
      │     ├─ 세그멘테이션 (도면 분석)
      │     └─ 공차 예측 (제조성 분석)
      │
      ├─► 3. 분석 실행
      │     │
      │     ├─ 로딩 (진행률 표시)
      │     └─ 실시간 상태 업데이트
      │
      ├─► 4. 결과 확인
      │     │
      │     ├─ 치수 정보 (테이블)
      │     ├─ GD&T 기호 (시각화)
      │     ├─ 세그멘테이션 이미지
      │     ├─ 공차 분석 차트
      │     └─ 제조 견적
      │
      └─► 5. 액션
            │
            ├─ 결과 다운로드 (JSON/CSV/PDF)
            ├─ 새 분석 시작
            └─ 히스토리 보기
```

### 2.2 서브 플로우

#### A. 히스토리 관리
```
히스토리 페이지
 │
 ├─► 과거 분석 목록 보기
 ├─► 필터링 (날짜, 파일명)
 ├─► 특정 결과 다시 열기
 └─► 결과 비교
```

#### B. 설정
```
설정 페이지
 │
 ├─► API 엔드포인트 설정
 ├─► 기본 옵션 설정
 ├─► 견적 파라미터 조정
 └─► 테마 변경 (라이트/다크)
```

---

## 3. 페이지 구조

### 3.1 라우팅 구조

```
/                          → 랜딩 페이지 (Landing)
/login                     → 로그인 (선택사항)
/dashboard                 → 메인 대시보드
/analyze                   → 분석 페이지
/analyze/:id               → 특정 분석 결과
/history                   → 분석 히스토리
/history/:id               → 히스토리 상세
/settings                  → 설정
/docs                      → API 문서 (Swagger 연동)
/about                     → 소개
```

### 3.2 페이지별 상세

#### 3.2.1 랜딩 페이지 (`/`)
- **목적**: 첫 방문자에게 서비스 소개
- **구성**:
  - Hero Section (메인 문구 + CTA)
  - 주요 기능 소개 (3-4개 섹션)
  - 사용 방법 (3단계)
  - 샘플 결과 미리보기
  - Footer

#### 3.2.2 대시보드 (`/dashboard`)
- **목적**: 메인 작업 공간
- **레이아웃**: 좌측 사이드바 + 메인 컨텐츠
- **구성**:
  - 좌측 사이드바
    - 네비게이션 메뉴
    - 빠른 통계 (오늘 분석 건수 등)
  - 메인 영역
    - 새 분석 시작 버튼 (prominent)
    - 최근 분석 목록 (카드 형식)
    - 시스템 상태 (API health)

#### 3.2.3 분석 페이지 (`/analyze`)
- **목적**: 도면 분석 실행 및 결과 표시
- **레이아웃**: 상단 진행 단계 + 메인 컨텐츠
- **구성**:
  - 상단: 진행 단계 인디케이터 (1→2→3→4)
  - 메인 영역:
    - Step 1: 파일 업로드
    - Step 2: 옵션 선택
    - Step 3: 분석 진행 (로딩)
    - Step 4: 결과 표시

#### 3.2.4 결과 상세 (`/analyze/:id`)
- **목적**: 분석 결과 상세 보기
- **레이아웃**: 탭 기반 다중 뷰
- **구성**:
  - 탭 1: 개요 (요약)
  - 탭 2: OCR 결과
  - 탭 3: 세그멘테이션
  - 탭 4: 공차 분석
  - 탭 5: 견적
  - 우측 패널: 원본 이미지

#### 3.2.5 히스토리 (`/history`)
- **목적**: 과거 분석 기록 관리
- **레이아웃**: 테이블 + 필터
- **구성**:
  - 상단: 검색 + 필터
  - 메인: 분석 목록 (테이블)
  - 액션: 보기, 다운로드, 삭제

---

## 4. 컴포넌트 설계

### 4.1 컴포넌트 계층 구조

```
App
├── Layout
│   ├── Header
│   │   ├── Logo
│   │   ├── Navigation
│   │   └── UserMenu
│   ├── Sidebar (조건부)
│   │   ├── NavMenu
│   │   └── QuickStats
│   └── Footer
│
├── Pages
│   ├── Landing
│   │   ├── Hero
│   │   ├── Features
│   │   ├── HowItWorks
│   │   └── CTA
│   │
│   ├── Dashboard
│   │   ├── WelcomeBanner
│   │   ├── NewAnalysisCard
│   │   ├── RecentAnalysisList
│   │   └── SystemStatus
│   │
│   ├── Analyze
│   │   ├── StepIndicator
│   │   ├── FileUploader
│   │   ├── OptionsSelector
│   │   ├── AnalysisProgress
│   │   └── ResultsDisplay
│   │
│   └── History
│       ├── SearchBar
│       ├── FilterPanel
│       └── AnalysisTable
│
└── Shared Components
    ├── UI
    │   ├── Button
    │   ├── Card
    │   ├── Modal
    │   ├── Table
    │   ├── Tabs
    │   ├── Badge
    │   ├── Alert
    │   └── Spinner
    │
    ├── Forms
    │   ├── Input
    │   ├── Select
    │   ├── Checkbox
    │   ├── Radio
    │   └── FileInput
    │
    ├── Data Display
    │   ├── MetricCard
    │   ├── ChartCard
    │   ├── JsonViewer
    │   └── ImageViewer
    │
    └── Domain Specific
        ├── DimensionTable
        ├── GDTList
        ├── ToleranceChart
        ├── QuoteCard
        └── SegmentationViewer
```

### 4.2 핵심 컴포넌트 상세

#### 4.2.1 FileUploader
```typescript
interface FileUploaderProps {
  onUpload: (file: File) => void;
  acceptedTypes: string[];
  maxSize: number;
  multiple?: boolean;
}

Features:
- Drag & Drop
- 파일 타입 검증
- 파일 크기 검증
- 미리보기 (이미지)
- 진행률 표시
```

#### 4.2.2 AnalysisProgress
```typescript
interface AnalysisProgressProps {
  status: 'idle' | 'uploading' | 'analyzing' | 'complete' | 'error';
  progress: number;
  currentStep: string;
  estimatedTime?: number;
}

Features:
- 실시간 진행률
- 현재 단계 표시
- 예상 완료 시간
- 에러 처리
```

#### 4.2.3 ResultsDisplay
```typescript
interface ResultsDisplayProps {
  data: AnalysisResult;
  onDownload: (format: 'json' | 'csv' | 'pdf') => void;
  onNewAnalysis: () => void;
}

Features:
- 탭 기반 다중 뷰
- 데이터 시각화
- 다운로드 옵션
- 공유 기능
```

---

## 5. 기능 명세

### 5.1 핵심 기능

#### F1. 파일 업로드
- **설명**: 공학 도면 파일 업로드
- **지원 형식**: JPG, PNG, PDF
- **최대 크기**: 10MB
- **UI**: Drag & Drop + 파일 선택 버튼
- **검증**: 파일 타입, 크기, 형식

#### F2. 실시간 분석
- **설명**: Gateway API를 통한 통합 분석
- **옵션**:
  - OCR (치수/GD&T 추출)
  - 세그멘테이션 (도면 분석)
  - 공차 예측 (제조성 분석)
- **UI**: 진행률 바, 로딩 애니메이션
- **에러 처리**: 타임아웃, API 실패

#### F3. 결과 시각화
- **OCR 결과**:
  - 치수 테이블 (정렬, 필터)
  - GD&T 기호 목록
  - 텍스트 정보
- **세그멘테이션**:
  - 원본 vs 분석 이미지 비교
  - 컴포넌트 하이라이트
  - 통계 차트
- **공차 분석**:
  - 예측 값 차트
  - 제조 난이도 게이지
  - 권장사항 리스트

#### F4. 제조 견적
- **입력**:
  - 재료 단가 ($/kg)
  - 가공 시간당 단가 ($/hr)
  - 공차 프리미엄 계수
- **출력**:
  - 재료비
  - 가공비
  - 총 비용
  - 납기 예상
- **UI**: 인터랙티브 계산기

#### F5. 결과 다운로드
- **형식**:
  - JSON (원본 데이터)
  - CSV (치수 테이블)
  - PDF (견적서)
- **UI**: 다운로드 드롭다운 메뉴

#### F6. 히스토리 관리
- **저장**: LocalStorage / IndexedDB
- **기능**:
  - 목록 보기
  - 검색/필터
  - 특정 결과 다시 열기
  - 삭제
- **UI**: 테이블 + 검색바

### 5.2 부가 기능

#### F7. 비교 모드
- 2개 분석 결과 나란히 비교
- 차이점 하이라이트

#### F8. 배치 처리
- 여러 파일 동시 업로드
- 순차 처리
- 진행 상황 추적

#### F9. 다크 모드
- 라이트/다크 테마 전환
- 사용자 설정 저장

#### F10. API 상태 모니터링
- 실시간 health check
- 응답 시간 표시
- 에러 알림

---

## 6. UI/UX 와이어프레임

### 6.1 대시보드 (Desktop)

```
┌────────────────────────────────────────────────────────────────┐
│  [Logo] AX 도면 분석 시스템          [Dashboard] [History] [👤] │
├────────────┬───────────────────────────────────────────────────┤
│            │                                                    │
│  📊 Dashboard│  🎯 새 분석 시작                                  │
│  📁 History  │  ┌──────────────────────────────────────────┐  │
│  ⚙️ Settings │  │                                          │  │
│  📖 Docs     │  │      📤 도면 파일을 업로드하세요          │  │
│            │  │                                          │  │
│            │  │      Drag & Drop or [파일 선택]          │  │
│            │  │                                          │  │
│  ━━━━━━━━  │  │      JPG, PNG, PDF (Max 10MB)           │  │
│            │  │                                          │  │
│  📈 오늘    │  └──────────────────────────────────────────┘  │
│  분석: 12건 │                                                    │
│  성공: 11건 │  📋 최근 분석                                      │
│  실패: 1건  │  ┌──────────────┬──────────┬──────────┬──────┐  │
│            │  │ A12-311197.jpg│ 2분 전   │ ✅ 성공  │ [보기]│  │
│            │  ├──────────────┼──────────┼──────────┼──────┤  │
│            │  │ Shaft-Rev2.png│ 15분 전  │ ✅ 성공  │ [보기]│  │
│            │  ├──────────────┼──────────┼──────────┼──────┤  │
│            │  │ Drawing-03.pdf│ 1시간 전 │ ⚠️ 부분  │ [보기]│  │
│            │  └──────────────┴──────────┴──────────┴──────┘  │
│            │                                                    │
│            │  🔧 시스템 상태                                    │
│            │  ● eDOCr2 API      Healthy    23ms              │
│            │  ● EDGNet API      Healthy    45ms              │
│            │  ● Skin Model API  Healthy    18ms              │
│            │  ● Gateway API     Healthy    12ms              │
│            │                                                    │
└────────────┴────────────────────────────────────────────────────┘
```

### 6.2 분석 페이지 - Step 4: 결과 표시

```
┌────────────────────────────────────────────────────────────────┐
│  ← 대시보드              분석 결과: A12-311197-9 Rev.2           │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [개요] [OCR] [세그멘테이션] [공차분석] [견적]                    │
│  ━━━                                                            │
│                                                                 │
│  ┌─────────────────────────────┬─────────────────────────────┐ │
│  │ 📊 요약                      │ 🖼️ 원본 이미지               │ │
│  │                             │                             │ │
│  │ ✅ OCR 완료 (2.0초)          │  ┌───────────────────────┐ │ │
│  │   • 치수: 2개               │  │                       │ │ │
│  │   • GD&T: 2개               │  │     [도면 이미지]      │ │ │
│  │                             │  │                       │ │ │
│  │ ✅ 세그멘테이션 완료 (3.0초)  │  │                       │ │ │
│  │   • 컴포넌트: 150개         │  │                       │ │ │
│  │   • 분류 완료               │  └───────────────────────┘ │ │
│  │                             │                             │ │
│  │ ✅ 공차 예측 완료 (1.5초)    │  [원본] [분석] [비교]        │ │
│  │   • Flatness: 0.048        │                             │ │
│  │   • 난이도: Medium         │  [🔍 확대] [⤓ 다운로드]      │ │
│  │                             │                             │ │
│  │ 💰 견적: $3,582.50          │                             │ │
│  │   • 납기: 15일              │                             │ │
│  │                             │                             │ │
│  └─────────────────────────────┴─────────────────────────────┘ │
│                                                                 │
│  [📥 JSON 다운로드] [📥 CSV 다운로드] [📄 견적서 PDF] [🔄 재분석] │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 6.3 분석 페이지 - OCR 탭

```
┌────────────────────────────────────────────────────────────────┐
│  ← 대시보드              분석 결과: A12-311197-9 Rev.2           │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [개요] [OCR] [세그멘테이션] [공차분석] [견적]                    │
│        ━━━                                                      │
│                                                                 │
│  📏 치수 정보 (2)                                               │
│  ┌──────────┬────────┬──────────┬────────┬─────────────────┐   │
│  │ 타입     │ 값     │ 단위     │ 공차   │ 위치            │   │
│  ├──────────┼────────┼──────────┼────────┼─────────────────┤   │
│  │ Diameter │ 392.0  │ mm       │ ±0.1   │ (450, 320)     │   │
│  │ Diameter │ 320.0  │ mm       │ -      │ (480, 350)     │   │
│  └──────────┴────────┴──────────┴────────┴─────────────────┘   │
│                                [📋 복사] [⤓ CSV 다운로드]        │
│                                                                 │
│  🎯 GD&T 기호 (2)                                               │
│  ┌────────────┬────────┬────────┬─────────────────┐            │
│  │ 타입       │ 값     │ 기준   │ 위치            │            │
│  ├────────────┼────────┼────────┼─────────────────┤            │
│  │ Flatness   │ 0.05   │ A      │ (200, 150)     │            │
│  │ Cylindricity│ 0.1   │ -      │ (250, 180)     │            │
│  └────────────┴────────┴────────┴─────────────────┘            │
│                                                                 │
│  📝 텍스트 정보                                                  │
│  ┌─────────────────────────────────────────┐                   │
│  │ 도면 번호: A12-311197-9                  │                   │
│  │ 리비전: Rev.2                           │                   │
│  │ 제목: Intermediate Shaft                │                   │
│  │ 재질: Steel                             │                   │
│  │ 비고:                                   │                   │
│  │   • M20 (4 places)                      │                   │
│  │   • Top & ø17.5 Drill, thru.            │                   │
│  └─────────────────────────────────────────┘                   │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 6.4 모바일 뷰

```
┌──────────────────────┐
│ ☰  AX 도면 분석  👤   │
├──────────────────────┤
│                      │
│  🎯 새 분석 시작      │
│  ┌────────────────┐  │
│  │                │  │
│  │  📤 파일 업로드 │  │
│  │                │  │
│  └────────────────┘  │
│                      │
│  📋 최근 분석         │
│  ┌────────────────┐  │
│  │ A12-311197.jpg │  │
│  │ 2분 전  ✅     │  │
│  │ [보기]         │  │
│  └────────────────┘  │
│  ┌────────────────┐  │
│  │ Shaft-Rev2.png │  │
│  │ 15분 전 ✅     │  │
│  │ [보기]         │  │
│  └────────────────┘  │
│                      │
│  [더 보기...]        │
│                      │
└──────────────────────┘
```

---

## 7. 기술 스택

### 7.1 프론트엔드 코어

```javascript
{
  "framework": "React 18",
  "buildTool": "Vite 5",
  "language": "TypeScript 5",
  "styling": "Tailwind CSS 3"
}
```

**선택 이유**:
- **React 18**: 최신 기능 (Suspense, Concurrent Rendering)
- **Vite**: 빠른 개발 서버, HMR, 빌드 최적화
- **TypeScript**: 타입 안정성, 개발 생산성
- **Tailwind CSS**: 유틸리티 우선, 빠른 스타일링

### 7.2 UI 컴포넌트 라이브러리

**옵션 A: Shadcn/ui + Radix UI (추천)**
```bash
✅ 장점:
- 복사 가능한 컴포넌트 (의존성 최소화)
- Radix UI 기반 (접근성 우수)
- Tailwind CSS 통합
- 커스터마이징 쉬움

❌ 단점:
- 초기 설정 필요
```

**옵션 B: Material-UI (MUI)**
```bash
✅ 장점:
- 완성도 높은 컴포넌트
- 풍부한 문서
- 빠른 개발

❌ 단점:
- 번들 크기 큼
- 커스터마이징 복잡
```

**옵션 C: Ant Design**
```bash
✅ 장점:
- 엔터프라이즈 레벨
- 테이블, 폼 컴포넌트 우수
- 중국어/영어 지원

❌ 단점:
- 디자인 스타일 고정적
```

**→ 추천: Shadcn/ui + Radix UI**

### 7.3 상태 관리

**옵션 A: Zustand (추천)**
```typescript
✅ 장점:
- 간단한 API
- 작은 번들 크기 (1KB)
- React 18 Concurrent 지원
- 보일러플레이트 최소

예시:
import create from 'zustand'

interface AnalysisState {
  files: File[]
  results: AnalysisResult[]
  addFile: (file: File) => void
}

const useAnalysisStore = create<AnalysisState>((set) => ({
  files: [],
  results: [],
  addFile: (file) => set((state) => ({
    files: [...state.files, file]
  }))
}))
```

**옵션 B: Redux Toolkit**
```bash
✅ 장점: 강력한 개발자 도구, 미들웨어
❌ 단점: 보일러플레이트 많음
```

**→ 추천: Zustand** (단순하고 효율적)

### 7.4 데이터 페칭

**TanStack Query (React Query) v5**
```typescript
✅ 장점:
- 자동 캐싱
- 백그라운드 리페칭
- 옵티미스틱 업데이트
- 로딩/에러 상태 관리

예시:
import { useQuery } from '@tanstack/react-query'

function useAnalysisResult(id: string) {
  return useQuery({
    queryKey: ['analysis', id],
    queryFn: () => fetch(`/api/v1/analyze/${id}`).then(r => r.json()),
    staleTime: 5 * 60 * 1000 // 5분
  })
}
```

### 7.5 폼 관리

**React Hook Form + Zod**
```typescript
✅ 장점:
- 성능 우수 (리렌더링 최소화)
- Zod 통합 (스키마 검증)
- TypeScript 지원

예시:
import { useForm } from 'react-hook-form'
import { z } from 'zod'

const schema = z.object({
  file: z.instanceof(File),
  options: z.object({
    ocr: z.boolean(),
    segmentation: z.boolean()
  })
})

type FormData = z.infer<typeof schema>

function AnalyzeForm() {
  const { register, handleSubmit } = useForm<FormData>()
  // ...
}
```

### 7.6 라우팅

**React Router v6**
```typescript
import { createBrowserRouter } from 'react-router-dom'

const router = createBrowserRouter([
  {
    path: '/',
    element: <Landing />,
  },
  {
    path: '/dashboard',
    element: <Dashboard />,
    children: [
      { path: 'analyze', element: <Analyze /> },
      { path: 'history', element: <History /> }
    ]
  }
])
```

### 7.7 차트 & 시각화

**Recharts (추천)**
```bash
✅ 장점:
- React 친화적
- 선언적 API
- 반응형
- 커스터마이징 쉬움
```

**대안: Chart.js / D3.js**

### 7.8 기타 라이브러리

```json
{
  "아이콘": "lucide-react",
  "날짜": "date-fns",
  "파일업로드": "react-dropzone",
  "토스트알림": "sonner",
  "모달": "@radix-ui/react-dialog",
  "테이블": "@tanstack/react-table",
  "PDF생성": "jsPDF",
  "CSV다운로드": "papaparse"
}
```

### 7.9 개발 도구

```json
{
  "린터": "ESLint",
  "포매터": "Prettier",
  "타입체크": "TypeScript",
  "테스트": "Vitest + Testing Library",
  "E2E": "Playwright (선택사항)"
}
```

---

## 8. 상태 관리

### 8.1 전역 상태 (Zustand)

```typescript
// stores/analysisStore.ts
interface AnalysisStore {
  // State
  currentFile: File | null
  options: AnalysisOptions
  status: 'idle' | 'uploading' | 'analyzing' | 'complete' | 'error'
  progress: number
  result: AnalysisResult | null
  error: string | null

  // Actions
  setFile: (file: File) => void
  setOptions: (options: AnalysisOptions) => void
  startAnalysis: () => Promise<void>
  reset: () => void
}

// stores/historyStore.ts
interface HistoryStore {
  items: AnalysisHistory[]
  addItem: (item: AnalysisHistory) => void
  removeItem: (id: string) => void
  getItem: (id: string) => AnalysisHistory | undefined
}

// stores/uiStore.ts
interface UIStore {
  theme: 'light' | 'dark'
  sidebarOpen: boolean
  toggleTheme: () => void
  toggleSidebar: () => void
}
```

### 8.2 서버 상태 (React Query)

```typescript
// hooks/useAnalysis.ts
export function useAnalysis(id: string) {
  return useQuery({
    queryKey: ['analysis', id],
    queryFn: () => api.getAnalysis(id)
  })
}

export function useAnalysisMutation() {
  return useMutation({
    mutationFn: (data: AnalysisRequest) => api.analyze(data),
    onSuccess: (data) => {
      // 히스토리에 추가
      historyStore.addItem(data)
    }
  })
}

// hooks/useHealthCheck.ts
export function useHealthCheck() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => api.healthCheck(),
    refetchInterval: 30000 // 30초마다
  })
}
```

### 8.3 로컬 상태 (useState, useReducer)

```typescript
// 컴포넌트 내부 상태만 관리
function FileUploader() {
  const [isDragging, setIsDragging] = useState(false)
  const [preview, setPreview] = useState<string | null>(null)
  // ...
}
```

---

## 9. API 통합

### 9.1 API 클라이언트

```typescript
// lib/api.ts
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = {
  // Health Check
  healthCheck: async () => {
    const response = await axios.get(`${API_BASE}/api/v1/health`)
    return response.data
  },

  // Process (통합 분석)
  analyze: async (data: AnalysisRequest) => {
    const formData = new FormData()
    formData.append('file', data.file)
    formData.append('use_ocr', String(data.options.ocr))
    formData.append('use_segmentation', String(data.options.segmentation))
    formData.append('use_tolerance', String(data.options.tolerance))

    const response = await axios.post(
      `${API_BASE}/api/v1/process`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (e) => {
          // 진행률 업데이트
        }
      }
    )
    return response.data
  },

  // Quote (견적)
  getQuote: async (data: QuoteRequest) => {
    const formData = new FormData()
    formData.append('file', data.file)
    formData.append('material_cost_per_kg', String(data.materialCost))
    formData.append('machining_rate_per_hour', String(data.machiningRate))

    const response = await axios.post(
      `${API_BASE}/api/v1/quote`,
      formData
    )
    return response.data
  }
}
```

### 9.2 타입 정의

```typescript
// types/api.ts

export interface AnalysisOptions {
  ocr: boolean
  segmentation: boolean
  tolerance: boolean
  visualize: boolean
}

export interface AnalysisRequest {
  file: File
  options: AnalysisOptions
}

export interface AnalysisResult {
  status: 'success' | 'error'
  data: {
    segmentation?: SegmentationResult
    ocr?: OCRResult
    tolerance?: ToleranceResult
  }
  processing_time: number
  file_id: string
}

export interface OCRResult {
  dimensions: Dimension[]
  gdt: GDT[]
  text: TextInfo
}

export interface Dimension {
  type: string
  value: number
  unit: string
  tolerance: number | null
  location: { x: number; y: number }
}

export interface GDT {
  type: string
  value: number
  datum: string | null
  location: { x: number; y: number }
}

export interface ToleranceResult {
  predicted_tolerances: {
    flatness: number
    cylindricity: number
    position: number
    perpendicularity?: number
  }
  manufacturability: {
    score: number
    difficulty: 'Easy' | 'Medium' | 'Hard'
    recommendations: string[]
  }
  assemblability: {
    score: number
    clearance: number
    interference_risk: 'Low' | 'Medium' | 'High'
  }
}

// ... more types
```

---

## 10. 구현 로드맵

### Phase 1: 프로젝트 설정 (1-2시간)

**작업 항목:**
- [x] Vite + React + TypeScript 프로젝트 생성
- [x] 폴더 구조 설정
- [x] Tailwind CSS 설정
- [x] ESLint + Prettier 설정
- [x] Git 설정
- [x] 기본 라우팅 구조

```bash
npm create vite@latest web-ui -- --template react-ts
cd web-ui
npm install
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### Phase 2: UI 컴포넌트 라이브러리 (2-3시간)

**작업 항목:**
- [x] Shadcn/ui 설치 및 설정
- [x] 기본 컴포넌트 설치
  - Button, Card, Input, Select
  - Table, Tabs, Dialog, Alert
- [x] 테마 설정 (light/dark)
- [x] 레이아웃 컴포넌트

### Phase 3: 핵심 기능 구현 (8-10시간)

#### 3.1 파일 업로드 (2시간)
- [ ] FileUploader 컴포넌트
- [ ] Drag & Drop 기능
- [ ] 파일 검증
- [ ] 미리보기

#### 3.2 분석 실행 (3시간)
- [ ] API 클라이언트 구현
- [ ] React Query 설정
- [ ] 진행률 표시
- [ ] 에러 처리

#### 3.3 결과 표시 (3시간)
- [ ] ResultsDisplay 컴포넌트
- [ ] 탭 기반 레이아웃
- [ ] 데이터 테이블
- [ ] 차트 시각화

#### 3.4 상태 관리 (2시간)
- [ ] Zustand 스토어 설정
- [ ] 전역 상태 통합

### Phase 4: 페이지 구현 (6-8시간)

- [ ] 랜딩 페이지 (2시간)
- [ ] 대시보드 (2시간)
- [ ] 분석 페이지 (3시간)
- [ ] 히스토리 페이지 (1시간)

### Phase 5: 고급 기능 (4-6시간)

- [ ] 히스토리 저장 (IndexedDB)
- [ ] 결과 다운로드 (JSON/CSV/PDF)
- [ ] 다크 모드
- [ ] 반응형 디자인 (모바일)

### Phase 6: Docker 배포 (2시간)

- [ ] Dockerfile 작성
- [ ] nginx 설정
- [ ] docker-compose.yml 통합
- [ ] 프로덕션 빌드 최적화

### Phase 7: 테스트 & 최적화 (2-3시간)

- [ ] 기능 테스트
- [ ] 성능 최적화
- [ ] 번들 크기 최적화
- [ ] 접근성 개선

---

## 📊 총 예상 시간

```
Phase 1: 프로젝트 설정       2시간
Phase 2: UI 라이브러리       3시간
Phase 3: 핵심 기능          10시간
Phase 4: 페이지 구현         8시간
Phase 5: 고급 기능           6시간
Phase 6: Docker 배포         2시간
Phase 7: 테스트 & 최적화     3시간
────────────────────────────────
합계:                      ~34시간
```

**실제 작업 시간 (버퍼 포함)**: 40-45시간 (약 1주일)

---

## 📝 다음 단계

1. **기획 검토 및 승인**
2. **디자인 시안 작성** (Figma/Sketch - 선택사항)
3. **개발 시작**
4. **지속적 피드백 및 조정**

---

**작성자**: Claude Code
**문서 버전**: 1.0
**최종 수정일**: 2025-10-27
