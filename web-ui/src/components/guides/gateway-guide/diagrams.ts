// Mermaid diagram strings for GatewayGuide

export const systemDiagram = `
flowchart LR
    A[Web UI] --> B[Gateway :8000]
    B --> C{오케스트레이터}

    subgraph Detection["🎯 Detection"]
        G[YOLO :5005]
    end

    subgraph OCR["📝 OCR"]
        D[eDOCr2 :5002]
        P[PaddleOCR :5006]
        EN[Ensemble :5011]
    end

    subgraph Seg["🎨 Segmentation"]
        E[EDGNet :5012]
    end

    subgraph Analysis["📊 Analysis"]
        F[SkinModel :5003]
    end

    subgraph AI["🤖 AI"]
        V[VL :5004]
    end

    subgraph Know["🧠 Knowledge"]
        KN[Knowledge :5007]
    end

    C --> Detection
    C --> OCR
    C --> Seg
    C --> Analysis
    C --> AI
    C --> Know

    Detection --> H[병렬 처리]
    OCR --> H
    Seg --> H
    Analysis --> H
    AI --> H
    Know --> H

    H --> I[결과 통합]
    I --> J[PDF 다운로드]

    style B fill:#1e40af,stroke:#60a5fa,stroke-width:2px,color:#fff
    style C fill:#ea580c,stroke:#fb923c,stroke-width:2px,color:#fff
    style Detection fill:#dbeafe,stroke:#3b82f6,stroke-width:2px
    style OCR fill:#dcfce7,stroke:#22c55e,stroke-width:2px
    style Seg fill:#fae8ff,stroke:#d946ef,stroke-width:2px
    style Analysis fill:#ffe4e6,stroke:#f43f5e,stroke-width:2px
    style AI fill:#e0e7ff,stroke:#6366f1,stroke-width:2px
    style Know fill:#f3e8ff,stroke:#a855f7,stroke-width:2px
    style H fill:#065f46,stroke:#34d399,stroke-width:2px,color:#fff
`;

export const hybridPipelineDiagram = `
sequenceDiagram
    participant User as 사용자
    participant UI as Web UI
    participant GW as Gateway
    participant YOLO as YOLOv11
    participant UP as Upscaler
    participant OCR as eDOCr v2
    participant SEG as EDGNet
    participant SKIN as Skin Model

    User->>UI: 1. 도면 업로드
    UI->>GW: 2. POST /api/v1/process<br/>(mode=hybrid)

    Note over GW: Step 1: 객체 검출
    GW->>YOLO: 3. 치수 영역 검출 요청
    YOLO-->>GW: 4. Bounding Boxes<br/>(mAP50 80.4%)

    par Step 2: 병렬 정밀 분석
        Note over GW,OCR: 2a. 검출된 영역 정밀 OCR
        GW->>UP: 5a. bbox 영역 4x Upscale
        UP-->>GW: 6a. 고해상도 이미지
        GW->>OCR: 7a. 정밀 OCR 요청
        OCR-->>GW: 8a. 치수 값 (92% 정확도)
        and
        Note over GW,SEG: 2b. 전체 구조 분석
        GW->>SEG: 5b. 세그멘테이션 요청
        SEG-->>GW: 6b. 레이어 분리<br/>(90.82% 정확도)
    end

    Note over GW: Step 3: 결과 앙상블
    GW->>GW: 9. YOLO bbox +<br/>eDOCr 값 +<br/>EDGNet 레이어 병합

    Note over GW: Step 4: 공차 예측
    GW->>SKIN: 10. 공차 예측 요청
    SKIN-->>GW: 11. 제조 가능성 분석

    GW->>GW: 12. 견적서 생성
    GW-->>UI: 13. 통합 결과 반환
    UI-->>User: 14. 결과 표시<br/>(예상 정확도 ~95%)

    Note over User,SKIN: 전체 처리 시간: 40-50초
`;

export const speedPipelineDiagram = `
sequenceDiagram
    participant User as 사용자
    participant UI as Web UI
    participant GW as Gateway
    participant YOLO as YOLOv11
    participant OCR as eDOCr v2
    participant SEG as EDGNet
    participant SKIN as Skin Model

    User->>UI: 1. 도면 업로드
    UI->>GW: 2. POST /api/v1/process<br/>(mode=speed)

    Note over GW: Step 1: 3-way 병렬 처리
    par 동시 실행 (최대 속도)
        GW->>YOLO: 3a. 객체 검출
        and
        GW->>OCR: 3b. OCR 분석
        and
        GW->>SEG: 3c. 세그멘테이션
    end

    par 결과 수신
        YOLO-->>GW: 4a. Bounding Boxes<br/>+ 클래스 (mAP50 80.4%)
        and
        OCR-->>GW: 4b. 치수 텍스트<br/>(92% 정확도)
        and
        SEG-->>GW: 4c. 레이어 정보<br/>(90.82% 정확도)
    end

    Note over GW: Step 2: 스마트 병합
    GW->>GW: 5. Confidence 기반 앙상블<br/>- YOLO bbox 우선<br/>- eDOCr 값 우선<br/>- EDGNet 레이어 보조

    Note over GW: Step 3: 공차 예측
    GW->>SKIN: 6. 공차 예측 요청
    SKIN-->>GW: 7. 제조 가능성 분석

    GW->>GW: 8. 견적서 생성
    GW-->>UI: 9. 통합 결과 반환
    UI-->>User: 10. 결과 표시<br/>(예상 정확도 ~93%)

    Note over User,SKIN: 전체 처리 시간: 35-45초
`;
