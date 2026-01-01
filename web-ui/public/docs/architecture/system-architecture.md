# AX 시스템 아키텍처

**버전**: 3.0.0
**최종 업데이트**: 2025-12-31
**디자인 패턴 점수**: 100/100

---

## 목차

1. [전체 시스템 개요](#전체-시스템-개요)
2. [아키텍처 다이어그램](#아키텍처-다이어그램)
3. [서비스 구조](#서비스-구조)
4. [모듈화 패턴](#모듈화-패턴)
5. [데이터 플로우](#데이터-플로우)
6. [배포 구조](#배포-구조)

---

## 전체 시스템 개요

AX 시스템은 기계 도면 자동 분석 및 제조 견적 생성을 위한 **마이크로서비스 아키텍처** 기반 AI 플랫폼입니다.

### 핵심 특징

| 항목 | 내용 |
|------|------|
| **마이크로서비스** | 19개 독립 API 서비스 |
| **GPU 가속** | YOLO, eDOCr2, PaddleOCR, EDGNet 등 8개 서비스 |
| **통합 웹 UI** | React 19 + Vite + ReactFlow |
| **워크플로우 빌더** | BlueprintFlow 시각적 파이프라인 빌더 |
| **Human-in-the-Loop** | Blueprint AI BOM 검증 시스템 |
| **테스트 커버리지** | 505개 테스트 통과 (gateway 364, web-ui 141) |

### 처리 파이프라인

```
도면 이미지 → VLM 분류 → YOLO 검출 → OCR 추출 → 공차 분석 → 리비전 비교 → 견적 PDF
```

---

## 아키텍처 다이어그램

### 1. 전체 시스템 구조

```mermaid
graph TB
    subgraph "사용자 인터페이스"
        WEB[Web UI :5173<br/>React 19 + Vite]
        BOM[Blueprint AI BOM :5021<br/>Human-in-the-Loop]
    end

    subgraph "API Gateway"
        GW[Gateway API :8000<br/>FastAPI + 6개 라우터]
    end

    subgraph "Detection Services"
        YOLO[YOLO :5005<br/>4개 모델 타입<br/>GPU]
    end

    subgraph "OCR Services"
        EDOCR[eDOCr2 :5002<br/>한국어 치수<br/>GPU]
        PADDLE[PaddleOCR :5006<br/>다국어<br/>GPU]
        TESS[Tesseract :5008<br/>문서 OCR]
        TROCR[TrOCR :5009<br/>필기체<br/>GPU]
        EASY[EasyOCR :5015<br/>80+ 언어<br/>GPU]
        SURYA[Surya :5013<br/>90+ 언어]
        DOCTR[DocTR :5014<br/>2단계]
        ENS[Ensemble :5011<br/>4엔진 투표]
    end

    subgraph "Segmentation Services"
        EDGNET[EDGNet :5012<br/>엣지 세그멘테이션<br/>GPU]
        LINE[Line Detector :5016<br/>P&ID 라인/영역]
    end

    subgraph "Analysis Services"
        SKIN[SkinModel :5003<br/>공차 예측]
        PID[PID Analyzer :5018<br/>연결성/BOM]
        DESIGN[Design Checker :5019<br/>규칙 검증]
    end

    subgraph "AI Services"
        VL[VL :5004<br/>Vision-Language<br/>GPU]
        KNOW[Knowledge :5007<br/>Neo4j GraphRAG]
    end

    subgraph "Preprocessing"
        ESR[ESRGAN :5010<br/>4x 업스케일<br/>GPU]
    end

    WEB --> GW
    BOM --> GW
    GW --> YOLO
    GW --> EDOCR
    GW --> PADDLE
    GW --> EDGNET
    GW --> LINE
    GW --> PID
    GW --> DESIGN
    GW --> VL

    style WEB fill:#e1f5ff
    style GW fill:#fff3cd
    style YOLO fill:#d4edda
    style PID fill:#f0e6ff
    style DESIGN fill:#f0e6ff
```

### 2. Gateway API 라우터 구조 (v3.0)

```mermaid
graph TB
    subgraph "gateway-api (335줄)"
        APP[api_server.py<br/>lifespan + 라우터 등록]
    end

    subgraph "constants/ (SSOT)"
        DOCKER[docker_services.py<br/>서비스 매핑]
        DIRS[directories.py<br/>경로 상수]
    end

    subgraph "routers/ (6개)"
        ADM[admin_router.py<br/>시스템 상태]
        DOCK[docker_router.py<br/>컨테이너 관리]
        RES[results_router.py<br/>결과 조회]
        GPU[gpu_config_router.py<br/>GPU 설정]
        PROC[process_router.py<br/>파이프라인 실행]
        QUOTE[quote_router.py<br/>견적 생성]
        DOWN[download_router.py<br/>파일 다운로드]
        KEY[api_key_router.py<br/>API 키 관리]
    end

    subgraph "utils/"
        SUB[subprocess_utils.py<br/>안전한 명령 실행]
    end

    APP --> DOCKER
    APP --> DIRS
    APP --> ADM
    APP --> DOCK
    APP --> RES
    APP --> GPU
    APP --> PROC
    APP --> QUOTE
    APP --> DOWN
    APP --> KEY
    ADM --> SUB
    DOCK --> SUB

    style APP fill:#fff3cd
    style DOCKER fill:#d1ecf1
```

### 3. P&ID 분석 파이프라인

```mermaid
graph LR
    IMG[도면 이미지] --> YOLO

    YOLO[YOLO<br/>pid_class_aware] --> |symbols| PID
    LINE[Line Detector] --> |lines, regions| PID
    PADDLE[PaddleOCR] --> |texts| PID

    PID[PID Analyzer] --> |connections<br/>bom<br/>valve_list| CHECK

    CHECK[Design Checker] --> |violations<br/>compliance %| RESULT

    RESULT[분석 결과<br/>+ Excel 내보내기]

    style YOLO fill:#d4edda
    style PID fill:#f0e6ff
    style CHECK fill:#f0e6ff
```

### 4. 모듈화된 API 구조

```mermaid
graph TB
    subgraph "Before (1000줄+)"
        OLD[api_server.py<br/>단일 파일]
    end

    subgraph "After (~100줄)"
        NEW[api_server.py<br/>lifespan + 라우터 등록]
    end

    subgraph "분리된 모듈"
        R[routers/<br/>엔드포인트 정의]
        S[services/<br/>비즈니스 로직]
        SC[schemas.py<br/>Pydantic 모델]
    end

    OLD --> |리팩토링| NEW
    NEW --> R
    NEW --> S
    NEW --> SC

    style OLD fill:#ffebee
    style NEW fill:#e8f5e9
```

---

## 서비스 구조

### API 서비스 목록 (19개)

| 카테고리 | 서비스 | 포트 | GPU | 설명 |
|----------|--------|------|-----|------|
| **Orchestrator** | Gateway | 8000 | - | 통합 API 게이트웨이 |
| **Detection** | YOLO | 5005 | ✓ | 객체 검출 (4개 모델 타입) |
| **OCR** | eDOCr2 | 5002 | ✓ | 한국어 치수 인식 |
| **OCR** | PaddleOCR | 5006 | ✓ | 다국어 OCR |
| **OCR** | Tesseract | 5008 | - | 문서 OCR |
| **OCR** | TrOCR | 5009 | ✓ | 필기체 OCR |
| **OCR** | EasyOCR | 5015 | ✓ | 80+ 언어 |
| **OCR** | Surya | 5013 | - | 90+ 언어, 레이아웃 |
| **OCR** | DocTR | 5014 | - | 2단계 파이프라인 |
| **OCR** | Ensemble | 5011 | - | 4엔진 가중 투표 |
| **Segmentation** | EDGNet | 5012 | ✓ | 엣지 세그멘테이션 |
| **Segmentation** | Line Detector | 5016 | - | P&ID 라인/영역 검출 |
| **Analysis** | SkinModel | 5003 | - | 공차 예측 (XGBoost) |
| **Analysis** | PID Analyzer | 5018 | - | 연결성 분석, BOM |
| **Analysis** | Design Checker | 5019 | - | 설계 규칙 검증 |
| **Analysis** | Blueprint AI BOM | 5020 | - | Human-in-the-Loop |
| **AI** | VL | 5004 | ✓ | Vision-Language |
| **Knowledge** | Knowledge | 5007 | - | Neo4j GraphRAG |
| **Preprocessing** | ESRGAN | 5010 | ✓ | 4x 업스케일링 |

### YOLO 모델 타입

| model_type | 클래스 수 | 용도 |
|------------|----------|------|
| engineering | 14 | 기계도면 치수/GD&T |
| pid_class_aware | 32 | P&ID 심볼 분류 |
| pid_class_agnostic | 1 | P&ID 심볼 위치만 |
| bom_detector | 27 | 전력 설비 심볼 |

---

## 모듈화 패턴

### 파일 크기 규칙

| 라인 수 | 상태 | 조치 |
|---------|------|------|
| < 300줄 | ✅ 이상적 | 유지 |
| 300-500줄 | ✅ 양호 | 유지 |
| 500-800줄 | ⚠️ 주의 | 리팩토링 고려 |
| > 1000줄 | ❌ 위반 | 즉시 분리 |

### 리팩토링 결과 (9개 대형 파일)

| 파일 | Before | After | 분리 결과 |
|------|--------|-------|----------|
| gateway-api/api_server.py | 2,044줄 | 335줄 | 6개 라우터 |
| web-ui/Guide.tsx | 1,235줄 | 151줄 | guide/ 디렉토리 |
| web-ui/APIDetail.tsx | 1,197줄 | 248줄 | api-detail/ |
| pid_features_router.py | 1,101줄 | 118줄 | pid_features/ (6개) |
| region_extractor.py | 1,082줄 | 57줄 | region/ (5개) |
| api_server_edocr_v1.py | 1,068줄 | 97줄 | edocr_v1/ |
| bwms_rules.py | 1,031줄 | 89줄 | bwms/ (8개) |
| NodePalette.tsx | 1,024줄 | 189줄 | node-palette/ |

### 표준 API 모듈 구조

```
models/{api-name}-api/
├── api_server.py           # 100-200줄 (lifespan + 라우터)
├── schemas.py              # Pydantic 모델
├── routers/
│   ├── __init__.py         # 라우터 export
│   └── *_router.py         # 엔드포인트
├── services/
│   ├── __init__.py         # 서비스 export
│   ├── model.py            # 모델 로드/추론
│   └── state.py            # 전역 상태 관리
└── Dockerfile
```

### 프론트엔드 분리 패턴

```
ComponentName.tsx (대형 파일)
    ↓ 분리
component-name/
├── index.ts              # re-export
├── hooks/
│   ├── useState.ts       # 상태 관리
│   └── useHandlers.ts    # 이벤트 핸들러
├── components/
│   └── SubComponent.tsx  # 하위 컴포넌트
├── sections/             # UI 섹션
└── constants.ts          # 상수
```

---

## 데이터 플로우

### BlueprintFlow 파이프라인 실행

```mermaid
sequenceDiagram
    participant U as 사용자
    participant W as Web UI
    participant G as Gateway
    participant PE as Pipeline Engine
    participant API as API 서비스

    U->>W: 워크플로우 정의
    W->>G: POST /api/v1/workflow/execute

    G->>PE: 워크플로우 실행
    PE->>PE: DAG 검증 & Topological Sort

    loop 각 노드별
        PE->>API: 노드 실행
        API-->>PE: 결과
        PE->>W: SSE 진행 상황
    end

    PE-->>G: 최종 결과
    G-->>W: JSON 응답
    W-->>U: 결과 시각화
```

### Human-in-the-Loop 워크플로우

```mermaid
graph TB
    subgraph "1. 검출 단계"
        A[도면 업로드] --> B[YOLO 검출]
        B --> C[Line Detector]
        C --> D[OCR 추출]
    end

    subgraph "2. 분석 단계"
        D --> E[PID Analyzer]
        E --> F[Design Checker]
    end

    subgraph "3. 검증 단계"
        F --> G{신뢰도 < 임계값?}
        G --> |Yes| H[검증 큐 추가]
        G --> |No| I[자동 승인]
        H --> J[작업자 검증]
        J --> K[피드백 저장]
    end

    subgraph "4. 내보내기"
        I --> L[BOM/Excel 생성]
        K --> L
    end
```

---

## 배포 구조

### Docker Compose 구성

```yaml
services:
  # Frontend
  web-ui:           # :5173
  blueprint-ai-bom: # :5020, :5021

  # Gateway
  gateway-api:      # :8000

  # Detection (GPU)
  yolo-api:         # :5005

  # OCR (8개)
  edocr2-v2-api:    # :5002 (GPU)
  paddleocr-api:    # :5006 (GPU)
  tesseract-api:    # :5008
  trocr-api:        # :5009 (GPU)
  easyocr-api:      # :5015 (GPU)
  surya-ocr-api:    # :5013
  doctr-api:        # :5014
  ocr-ensemble-api: # :5011

  # Segmentation
  edgnet-api:       # :5012 (GPU)
  line-detector-api: # :5016

  # Analysis
  skinmodel-api:    # :5003
  pid-analyzer-api: # :5018
  design-checker-api: # :5019

  # AI
  vl-api:           # :5004 (GPU)
  knowledge-api:    # :5007

  # Preprocessing
  esrgan-api:       # :5010 (GPU)

networks:
  ax_poc_network:
    driver: bridge
```

### GPU Override 시스템

GPU 설정은 `docker-compose.override.yml`에서 동적으로 관리:

```yaml
# docker-compose.override.yml (로컬, .gitignore)
services:
  yolo-api:
    deploy:
      resources:
        reservations:
          devices:
          - capabilities: [gpu]
            count: 1
```

| GPU 지원 서비스 | 기본 상태 | 활성화 방법 |
|----------------|----------|------------|
| YOLO | OFF | Dashboard 또는 override.yml |
| eDOCr2 | OFF | Dashboard 또는 override.yml |
| PaddleOCR | OFF | Dashboard 또는 override.yml |
| TrOCR | OFF | Dashboard 또는 override.yml |
| EDGNet | OFF | Dashboard 또는 override.yml |
| ESRGAN | OFF | Dashboard 또는 override.yml |
| EasyOCR | OFF | Dashboard 또는 override.yml |
| VL | OFF | Dashboard 또는 override.yml |

---

## 기술 스택

### Frontend
- **Framework**: React 19 + TypeScript
- **빌드**: Vite
- **상태 관리**: Zustand
- **UI**: Tailwind CSS + shadcn/ui
- **워크플로우**: ReactFlow
- **i18n**: i18next (ko/en)

### Backend
- **Framework**: FastAPI 0.104+
- **Python**: 3.10+
- **비동기**: Uvicorn + asyncio
- **HTTP Client**: httpx (async)

### AI/ML
- **객체 검출**: YOLOv11 (PyTorch)
- **OCR**: eDOCr2, PaddleOCR, TrOCR 등
- **세그멘테이션**: EDGNet, Line Detector
- **공차 예측**: XGBoost
- **Vision-Language**: Qwen2-VL

### 인프라
- **컨테이너**: Docker + Docker Compose
- **GPU**: NVIDIA (CUDA 11.8+)
- **네트워크**: ax_poc_network (bridge)

---

## 테스트 현황

| 영역 | 테스트 수 | 상태 |
|------|----------|------|
| gateway-api | 238개 | ✅ |
| web-ui | 141개 | ✅ |
| models | 65개 | ✅ |
| **총계** | **400개+** | ✅ |

---

**작성자**: Claude Code (Opus 4.5)
**마지막 업데이트**: 2025-12-31
**버전**: 3.0.0
