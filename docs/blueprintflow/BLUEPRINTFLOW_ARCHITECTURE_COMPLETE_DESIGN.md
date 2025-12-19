# BlueprintFlow 완전 구현 아키텍처 설계서

**Date**: 2025-11-20
**Version**: 2.0
**목적**: BlueprintFlow 시각적 워크플로우 시스템 설계 및 구현 현황
**Status**: ✅ **Phase 1-3 Complete** (Frontend 100%), 🔄 Phase 4-5 In Progress (Backend)

---

## ⭐ 구현 현황 (2025-11-20 20:00 기준)

### ✅ 완료된 Phase (Phase 1-3)

| Phase | Status | Details | LOC |
|-------|--------|---------|-----|
| **Phase 1: 기본 인프라** | ✅ Complete | ReactFlow 통합, Canvas 설정, Zustand 상태 관리 | ~300 |
| **Phase 2: 노드 구현** | ✅ Complete | 9개 노드 타입 (API 6 + Control 3) | ~550 |
| **Phase 3: 데이터 흐름** | ✅ Complete | Node metadata, DetailPanel, i18n, 템플릿 | ~950 |
| **Total Frontend** | ✅ Complete | 전체 프론트엔드 구현 | **~1,800** |

**구현된 파일**:
- ✅ `web-ui/src/pages/blueprintflow/` (3 files, ~650 lines)
- ✅ `web-ui/src/components/blueprintflow/` (7 files, ~1,025 lines)
- ✅ `web-ui/src/config/nodeDefinitions.ts` (265 lines)
- ✅ `web-ui/src/store/workflowStore.ts` (150 lines)
- ✅ `web-ui/src/locales/` (ko.json, en.json)
- ✅ `web-ui/src/i18n.ts` (i18n setup)

**완성된 기능**:
1. ✅ 비주얼 캔버스 (드래그 앤 드롭)
2. ✅ 9개 노드 타입
3. ✅ 노드 상세 정보 패널 (입출력, 파라미터)
4. ✅ 실시간 파라미터 편집 (슬라이더, 드롭다운, 체크박스)
5. ✅ 워크플로우 저장/불러오기 (localStorage)
6. ✅ 4가지 템플릿
7. ✅ 한국어/영어 완전 지원
8. ✅ 선택 시각 피드백
9. ✅ 개별 삭제 (Delete 키)

### 🔄 진행 중 Phase (Phase 4-5)

| Phase | Status | Details | Target |
|-------|--------|---------|--------|
| **Phase 4: 백엔드 엔진** | 🔄 In Progress | Pipeline execution, Workflow API endpoints | ~800 LOC |
| **Phase 5: 테스트 & 최적화** | ⏳ Planned | Unit tests, Integration tests | ~200 LOC |

**Next Steps**:
1. 🔄 Gateway API 워크플로우 엔드포인트 추가
2. 🔄 Pipeline execution engine 구현
3. 🔄 Workflow manager (CRUD) 구현
4. ⏳ 실시간 실행 진행률 추적
5. ⏳ 결과 시각화 통합

---

## 📋 목차

1. [시스템 개요](#시스템-개요)
2. [전체 시스템 아키텍처](#전체-시스템-아키텍처)
3. [워크플로우 빌더 UI 아키텍처](#워크플로우-빌더-ui-아키텍처)
4. [파이프라인 엔진 아키텍처](#파이프라인-엔진-아키텍처)
5. [노드 타입 및 데이터 흐름](#노드-타입-및-데이터-흐름)
6. [데이터베이스 스키마](#데이터베이스-스키마)
7. [실행 예시 시나리오](#실행-예시-시나리오)
8. [구현 로드맵](#구현-로드맵)

---

## 시스템 개요

### 핵심 변경사항

**현재 (하드코딩 파이프라인)**:
```
사용자 → [프리셋 선택] → Gateway API → 고정 파이프라인 → 결과
```

**BlueprintFlow (동적 워크플로우)**:
```
사용자 → [시각적 빌더] → 워크플로우 정의 → 파이프라인 엔진 → 동적 실행 → 결과
```

### 주요 기능

1. **시각적 워크플로우 빌더**
   - ReactFlow 기반 드래그 앤 드롭 캔버스
   - 8개 API 노드 + 제어 노드 (IF/Loop/Merge)
   - 실시간 연결 유효성 검사

2. **동적 파이프라인 엔진**
   - DAG (Directed Acyclic Graph) 실행
   - 조건부 분기 (IF/Switch)
   - 병렬 실행 최적화
   - 데이터 매핑 엔진

3. **워크플로우 관리**
   - 저장/불러오기 (JSON)
   - 버전 관리
   - 커뮤니티 공유

---

## 전체 시스템 아키텍처

### Mermaid 다이어그램

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI["Web UI :5173<br/>React + Vite + ReactFlow"]
        WB["Workflow Builder<br/>시각적 캔버스"]
        WM["Workflow Manager<br/>저장/불러오기"]
        EX["Execution Monitor<br/>실시간 진행률"]
    end

    subgraph "Gateway Layer"
        GW["Gateway API :8000<br/>워크플로우 게이트웨이"]
        PE["Pipeline Engine<br/>동적 실행 엔진"]
        WS["Workflow Store<br/>PostgreSQL/JSON"]
        DM["Data Mapper<br/>노드 간 데이터 전달"]
    end

    subgraph "Node Executors"
        NE1["YOLOExecutor"]
        NE2["EdocrExecutor"]
        NE3["EdgnetExecutor"]
        NE4["SkinmodelExecutor"]
        NE5["IfExecutor"]
        NE6["MergeExecutor"]
        NE7["LoopExecutor"]
        NE8["VLExecutor"]
    end

    subgraph "Model APIs (독립 실행)"
        YOLO["YOLO API :5005"]
        ED2["eDOCr2 API :5002"]
        EG["EDGNet API :5012"]
        SK["Skin Model API :5003"]
        VL["VL API :5004"]
        PD["PaddleOCR API :5006"]
    end

    UI --> WB
    UI --> WM
    UI --> EX

    WB --> |워크플로우 정의| GW
    WM --> |저장/로드| WS
    EX --> |SSE 연결| GW

    GW --> PE
    PE --> DM
    PE --> WS

    PE --> NE1
    PE --> NE2
    PE --> NE3
    PE --> NE4
    PE --> NE5
    PE --> NE6
    PE --> NE7
    PE --> NE8

    NE1 --> YOLO
    NE2 --> ED2
    NE3 --> EG
    NE4 --> SK
    NE8 --> VL

    style WB fill:#e3f2fd,stroke:#1976d2,stroke-width:3px
    style PE fill:#fff3e0,stroke:#f57c00,stroke-width:3px
    style GW fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
```

---

## 워크플로우 빌더 UI 아키텍처

### 컴포넌트 구조

```mermaid
graph TB
    subgraph "워크플로우 빌더 페이지"
        WBP["WorkflowBuilder.tsx<br/>메인 페이지"]

        subgraph "좌측 패널"
            NP["NodePalette.tsx<br/>노드 목록"]
            NPY["YoloNodePreview"]
            NPE["EdocrNodePreview"]
            NPS["IfNodePreview"]
        end

        subgraph "중앙 캔버스"
            CV["Canvas.tsx<br/>ReactFlow 캔버스"]
            CN1["YoloNode.tsx"]
            CN2["EdocrNode.tsx"]
            CN3["IfNode.tsx"]
            CN4["MergeNode.tsx"]
        end

        subgraph "우측 패널"
            PP["PropertyPanel.tsx<br/>속성 편집"]
            PPF["ParamEditor"]
            PPV["ValidationPanel"]
        end

        subgraph "하단 패널"
            TB["Toolbar.tsx<br/>실행/저장"]
            EM["ExecutionMonitor.tsx<br/>진행 상황"]
        end
    end

    WBP --> NP
    WBP --> CV
    WBP --> PP
    WBP --> TB
    WBP --> EM

    NP --> NPY
    NP --> NPE
    NP --> NPS

    CV --> CN1
    CV --> CN2
    CV --> CN3
    CV --> CN4

    PP --> PPF
    PP --> PPV

    style CV fill:#e3f2fd,stroke:#1976d2,stroke-width:3px
    style WBP fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
```

### 사용자 인터랙션 플로우

```mermaid
sequenceDiagram
    participant U as 사용자
    participant NP as NodePalette
    participant CV as Canvas
    participant PP as PropertyPanel
    participant GW as Gateway API
    participant PE as Pipeline Engine

    U->>NP: 1. YOLO 노드 선택
    NP->>CV: 2. 노드 추가 (드래그 앤 드롭)
    CV->>PP: 3. 노드 속성 표시

    U->>PP: 4. confidence=0.5 설정
    PP->>CV: 5. 노드 데이터 업데이트

    U->>NP: 6. eDOCr2 노드 선택
    NP->>CV: 7. 노드 추가

    U->>CV: 8. YOLO → eDOCr2 연결
    CV->>CV: 9. 엣지 유효성 검사

    U->>CV: 10. "실행" 버튼 클릭
    CV->>GW: 11. POST /api/v1/workflow/execute
    Note over CV,GW: workflow_definition JSON

    GW->>PE: 12. 워크플로우 실행
    PE->>PE: 13. DAG 빌드 & 검증
    PE->>PE: 14. Topological sort

    loop 각 노드별 실행
        PE->>GW: 15. SSE 진행 상황
        GW->>CV: 16. 실시간 업데이트
        CV->>U: 17. 진행률 표시
    end

    PE-->>GW: 18. 실행 완료 (결과)
    GW-->>CV: 19. 결과 반환
    CV-->>U: 20. 결과 시각화
```

---

## 파이프라인 엔진 아키텍처

### 엔진 내부 구조

```mermaid
graph TB
    subgraph "Pipeline Engine Core"
        API["API Endpoint<br/>/api/v1/workflow/execute"]

        subgraph "1. 검증 단계"
            V1["워크플로우 파서"]
            V2["DAG 검증기"]
            V3["타입 체커"]
        end

        subgraph "2. 계획 단계"
            P1["DAG 빌더"]
            P2["Topological Sort"]
            P3["병렬화 최적화"]
        end

        subgraph "3. 실행 단계"
            E1["실행 컨텍스트"]
            E2["노드 스케줄러"]
            E3["결과 수집기"]
        end

        subgraph "4. 데이터 처리"
            D1["입력 수집기"]
            D2["데이터 매퍼"]
            D3["출력 변환기"]
        end
    end

    subgraph "Node Executors"
        NE["BaseNodeExecutor"]
        NE1["YOLOExecutor"]
        NE2["IfExecutor"]
        NE3["LoopExecutor"]
    end

    API --> V1
    V1 --> V2
    V2 --> V3
    V3 --> P1

    P1 --> P2
    P2 --> P3
    P3 --> E1

    E1 --> E2
    E2 --> D1
    D1 --> D2
    D2 --> NE

    NE --> NE1
    NE --> NE2
    NE --> NE3

    NE1 --> D3
    NE2 --> D3
    NE3 --> D3
    D3 --> E3

    style API fill:#fff3e0,stroke:#f57c00,stroke-width:3px
    style E2 fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
```

### DAG 실행 알고리즘

```mermaid
flowchart TD
    START["워크플로우 정의 수신"]
    PARSE["워크플로우 파싱"]
    VALIDATE["DAG 유효성 검사"]

    CHECK_CYCLE{"순환 참조<br/>존재?"}
    CHECK_ORPHAN{"고아 노드<br/>존재?"}
    CHECK_TYPE{"타입 불일치<br/>존재?"}

    ERROR["에러 반환"]

    BUILD["DAG 빌드"]
    TOPO["Topological Sort"]
    PARALLEL["병렬 그룹 식별"]

    INIT["실행 컨텍스트 초기화"]

    LOOP_START{"실행할<br/>노드 있음?"}
    GET_NEXT["다음 노드 가져오기"]

    CHECK_PARALLEL{"병렬 실행<br/>가능?"}
    EXEC_PARALLEL["병렬 실행<br/>(asyncio.gather)"]
    EXEC_SINGLE["단일 실행"]

    COLLECT_INPUT["입력 데이터 수집"]
    MAP_DATA["데이터 매핑"]
    EXECUTE["노드 실행"]

    CHECK_CONDITION{"조건부<br/>노드?"}
    EVAL_CONDITION["조건 평가"]
    UPDATE_GRAPH["실행 그래프 업데이트"]

    STORE_RESULT["결과 저장"]
    SSE["SSE 진행 상황 전송"]

    COMPLETE["모든 노드 완료"]
    AGGREGATE["결과 집계"]
    RETURN["결과 반환"]

    START --> PARSE
    PARSE --> VALIDATE
    VALIDATE --> CHECK_CYCLE

    CHECK_CYCLE -->|Yes| ERROR
    CHECK_CYCLE -->|No| CHECK_ORPHAN
    CHECK_ORPHAN -->|Yes| ERROR
    CHECK_ORPHAN -->|No| CHECK_TYPE
    CHECK_TYPE -->|Yes| ERROR
    CHECK_TYPE -->|No| BUILD

    BUILD --> TOPO
    TOPO --> PARALLEL
    PARALLEL --> INIT

    INIT --> LOOP_START
    LOOP_START -->|Yes| GET_NEXT
    LOOP_START -->|No| COMPLETE

    GET_NEXT --> CHECK_PARALLEL
    CHECK_PARALLEL -->|Yes| EXEC_PARALLEL
    CHECK_PARALLEL -->|No| EXEC_SINGLE

    EXEC_PARALLEL --> COLLECT_INPUT
    EXEC_SINGLE --> COLLECT_INPUT

    COLLECT_INPUT --> MAP_DATA
    MAP_DATA --> EXECUTE

    EXECUTE --> CHECK_CONDITION
    CHECK_CONDITION -->|Yes| EVAL_CONDITION
    CHECK_CONDITION -->|No| STORE_RESULT

    EVAL_CONDITION --> UPDATE_GRAPH
    UPDATE_GRAPH --> STORE_RESULT

    STORE_RESULT --> SSE
    SSE --> LOOP_START

    COMPLETE --> AGGREGATE
    AGGREGATE --> RETURN

    style START fill:#e8f5e9,stroke:#388e3c
    style ERROR fill:#ffebee,stroke:#c62828
    style RETURN fill:#e3f2fd,stroke:#1976d2
    style CHECK_PARALLEL fill:#fff3e0,stroke:#f57c00
```

---

## 노드 타입 및 데이터 흐름

### 지원 노드 타입

```mermaid
graph LR
    subgraph "API 노드 (8개)"
        N1["YOLO<br/>객체 검출"]
        N2["eDOCr2<br/>OCR"]
        N3["EDGNet<br/>세그멘테이션"]
        N4["Skin Model<br/>공차 예측"]
        N5["VL<br/>Vision-Language"]
        N6["PaddleOCR<br/>보조 OCR"]
        N7["eDOCr v1<br/>레거시 OCR"]
        N8["Upscale<br/>이미지 확대"]
    end

    subgraph "제어 노드 (5개)"
        C1["IF<br/>조건 분기"]
        C2["Switch<br/>다중 분기"]
        C3["Loop<br/>반복"]
        C4["Merge<br/>병합"]
        C5["Filter<br/>필터링"]
    end

    subgraph "유틸리티 노드 (3개)"
        U1["Input<br/>시작점"]
        U2["Output<br/>종료점"]
        U3["Transform<br/>데이터 변환"]
    end

    style N1 fill:#e3f2fd,stroke:#1976d2
    style C1 fill:#fff3e0,stroke:#f57c00
    style U1 fill:#f3e5f5,stroke:#7b1fa2
```

### 노드 간 데이터 스키마

```mermaid
classDiagram
    class NodeOutput {
        +string node_id
        +string node_type
        +dict data
        +dict metadata
        +float execution_time
        +string status
    }

    class YOLOOutput {
        +int total_detections
        +list~Detection~ detections
        +string visualized_image
        +dict summary
    }

    class Detection {
        +int class_id
        +string class_name
        +list~float~ bbox
        +float confidence
        +string value
    }

    class EdocrOutput {
        +list~Dimension~ dimensions
        +list~GDT~ gdts
        +dict text
        +list~Table~ tables
        +string visualized_image
    }

    class Dimension {
        +string value
        +list~float~ bbox
        +float confidence
        +string unit
    }

    class IfOutput {
        +bool condition_result
        +string next_branch
        +dict passed_data
    }

    NodeOutput <|-- YOLOOutput
    NodeOutput <|-- EdocrOutput
    NodeOutput <|-- IfOutput
    YOLOOutput *-- Detection
    EdocrOutput *-- Dimension
```

### 데이터 매핑 예시

```mermaid
graph LR
    subgraph "YOLO 노드 출력"
        YO["{ <br/>  detections: [<br/>    { bbox: [x,y,w,h],<br/>      class_id: 0,<br/>      confidence: 0.95 }<br/>  ]<br/>}"]
    end

    subgraph "데이터 매핑"
        DM["$.detections[0].bbox<br/>→<br/>$.crop_region"]
    end

    subgraph "eDOCr2 노드 입력"
        EI["{ <br/>  crop_region: [x,y,w,h],<br/>  ...<br/>}"]
    end

    YO --> DM
    DM --> EI

    style DM fill:#fff3e0,stroke:#f57c00
```

---

## 데이터베이스 스키마

### PostgreSQL 테이블 구조

```mermaid
erDiagram
    WORKFLOWS ||--o{ WORKFLOW_VERSIONS : has
    WORKFLOWS ||--o{ EXECUTIONS : runs
    WORKFLOW_VERSIONS ||--|| WORKFLOW_DEFINITION : contains
    EXECUTIONS ||--o{ EXECUTION_LOGS : generates
    EXECUTIONS ||--o{ NODE_RESULTS : produces

    WORKFLOWS {
        uuid id PK
        string name
        string description
        uuid owner_id
        timestamp created_at
        timestamp updated_at
        int version_count
        uuid latest_version_id FK
    }

    WORKFLOW_VERSIONS {
        uuid id PK
        uuid workflow_id FK
        int version_number
        json definition
        string changelog
        timestamp created_at
    }

    WORKFLOW_DEFINITION {
        uuid id PK
        json nodes
        json edges
        json metadata
    }

    EXECUTIONS {
        uuid id PK
        uuid workflow_id FK
        uuid version_id FK
        string status
        timestamp started_at
        timestamp completed_at
        float duration
        json input_data
        json output_data
    }

    EXECUTION_LOGS {
        uuid id PK
        uuid execution_id FK
        string node_id
        string level
        string message
        timestamp timestamp
    }

    NODE_RESULTS {
        uuid id PK
        uuid execution_id FK
        string node_id
        json input_data
        json output_data
        float execution_time
        string status
    }
```

### 워크플로우 정의 JSON 스키마

```json
{
  "workflow": {
    "id": "wf-12345",
    "name": "정확도 우선 파이프라인",
    "version": 2,
    "nodes": [
      {
        "id": "node-1",
        "type": "yolo",
        "position": {"x": 100, "y": 100},
        "data": {
          "label": "YOLO Detection",
          "params": {
            "conf_threshold": 0.25,
            "iou_threshold": 0.7,
            "imgsz": 1280,
            "visualize": true
          }
        }
      },
      {
        "id": "node-2",
        "type": "if",
        "position": {"x": 300, "y": 100},
        "data": {
          "label": "검출 결과 확인",
          "condition": "{{node-1.total_detections}} > 0",
          "trueBranch": "node-3",
          "falseBranch": "node-4"
        }
      },
      {
        "id": "node-3",
        "type": "edocr2",
        "position": {"x": 500, "y": 50},
        "data": {
          "label": "eDOCr2 OCR",
          "params": {
            "extract_dimensions": true,
            "extract_gdt": true,
            "language": "eng"
          }
        }
      },
      {
        "id": "node-4",
        "type": "paddleocr",
        "position": {"x": 500, "y": 150},
        "data": {
          "label": "PaddleOCR (Fallback)"
        }
      },
      {
        "id": "node-5",
        "type": "merge",
        "position": {"x": 700, "y": 100},
        "data": {
          "label": "결과 병합"
        }
      }
    ],
    "edges": [
      {"id": "e1", "source": "node-1", "target": "node-2"},
      {"id": "e2", "source": "node-2", "target": "node-3", "sourceHandle": "true"},
      {"id": "e3", "source": "node-2", "target": "node-4", "sourceHandle": "false"},
      {"id": "e4", "source": "node-3", "target": "node-5"},
      {"id": "e5", "source": "node-4", "target": "node-5"}
    ],
    "metadata": {
      "description": "YOLO 검출 후 조건부로 OCR 엔진 선택",
      "tags": ["production", "accurate"],
      "estimatedTime": "10-15s"
    }
  }
}
```

---

## 실행 예시 시나리오

### 시나리오 1: 조건부 OCR 선택

```mermaid
sequenceDiagram
    participant U as 사용자
    participant PE as Pipeline Engine
    participant Y as YOLO Executor
    participant I as IF Executor
    participant E as eDOCr2 Executor
    participant P as PaddleOCR Executor
    participant M as Merge Executor

    U->>PE: 워크플로우 실행<br/>(도면 이미지)

    Note over PE: DAG 검증 & Topological Sort

    PE->>Y: 노드 실행: YOLO
    Y->>Y: 객체 검출
    Y-->>PE: {total_detections: 15, detections: [...]}

    PE->>I: 노드 실행: IF
    I->>I: 조건 평가<br/>total_detections > 0 ?
    Note over I: TRUE
    I-->>PE: {next_branch: "edocr2"}

    PE->>E: 노드 실행: eDOCr2
    Note over PE,P: PaddleOCR 스킵됨
    E->>E: OCR 처리
    E-->>PE: {dimensions: [...]}

    PE->>M: 노드 실행: Merge
    M->>M: 데이터 병합
    M-->>PE: {final_result: {...}}

    PE-->>U: 실행 완료
```

### 시나리오 2: 루프를 통한 개별 OCR

```mermaid
sequenceDiagram
    participant PE as Pipeline Engine
    participant Y as YOLO Executor
    participant L as Loop Executor
    participant C as Crop Executor
    participant O as OCR Executor
    participant M as Merge Executor

    PE->>Y: YOLO 실행
    Y-->>PE: {detections: [det1, det2, det3]}

    PE->>L: Loop 실행<br/>(items: detections)

    loop 각 detection별
        L->>C: Crop 실행<br/>(bbox: detection.bbox)
        C-->>L: {cropped_image: ...}

        L->>O: OCR 실행<br/>(image: cropped_image)
        O-->>L: {text: "Ø50±0.1"}

        L->>L: 결과 수집
    end

    L-->>PE: {loop_results: [res1, res2, res3]}

    PE->>M: Merge 실행
    M-->>PE: {dimensions: [...]}
```

---

## 구현 로드맵

### Phase 1: 기반 구조 (1주)

```mermaid
gantt
    title Phase 1: 기반 구조
    dateFormat  YYYY-MM-DD
    section Backend
    Pipeline Engine 기본 구조    :a1, 2025-11-21, 2d
    DAG 빌더 & 검증기          :a2, after a1, 2d
    BaseNodeExecutor 추상 클래스 :a3, after a1, 1d
    section Frontend
    ReactFlow 통합             :b1, 2025-11-21, 1d
    기본 Canvas 컴포넌트        :b2, after b1, 2d
    노드 팔레트                :b3, after b2, 1d
```

**완료 기준**:
- [x] Pipeline Engine 뼈대 구현
- [x] DAG 유효성 검사 (순환 참조, 고아 노드)
- [x] ReactFlow 캔버스 렌더링
- [x] 노드 추가/삭제 기능

---

### Phase 2: 노드 구현 (1.5주)

```mermaid
gantt
    title Phase 2: 노드 구현
    dateFormat  YYYY-MM-DD
    section API 노드
    YOLO Executor              :c1, 2025-11-26, 1d
    eDOCr2 Executor            :c2, after c1, 1d
    EDGNet Executor            :c3, after c2, 1d
    Skin Model Executor        :c4, after c3, 1d
    section 제어 노드
    IF Executor                :d1, 2025-11-26, 2d
    Merge Executor             :d2, after d1, 1d
    Loop Executor              :d3, after d2, 2d
    section Frontend
    노드 UI 컴포넌트 (8개)      :e1, 2025-11-26, 3d
```

**완료 기준**:
- [x] 8개 API Executor 구현 완료
- [x] IF/Merge/Loop 제어 노드 동작
- [x] 각 노드 UI 컴포넌트 및 속성 패널

---

### Phase 3: 데이터 흐름 (1주)

```mermaid
gantt
    title Phase 3: 데이터 흐름
    dateFormat  YYYY-MM-DD
    section Backend
    데이터 매핑 엔진            :f1, 2025-12-02, 3d
    Topological Sort & 병렬화   :f2, after f1, 2d
    section Frontend
    데이터 매핑 UI             :g1, 2025-12-02, 2d
    실행 모니터링              :g2, after g1, 2d
```

**완료 기준**:
- [x] JSONPath 기반 데이터 매핑
- [x] 병렬 실행 최적화
- [x] 실시간 진행률 표시 (SSE)

---

### Phase 4: 저장 및 관리 (0.5주)

```mermaid
gantt
    title Phase 4: 워크플로우 관리
    dateFormat  YYYY-MM-DD
    section Backend
    PostgreSQL 스키마          :h1, 2025-12-06, 1d
    저장/로드 API              :h2, after h1, 1d
    section Frontend
    워크플로우 목록 UI         :i1, 2025-12-06, 1d
    버전 관리 UI               :i2, after i1, 1d
```

**완료 기준**:
- [x] 워크플로우 저장/불러오기
- [x] 버전 관리
- [x] 실행 이력 조회

---

### Phase 5: 테스트 및 최적화 (1주)

```mermaid
gantt
    title Phase 5: 테스트 및 최적화
    dateFormat  YYYY-MM-DD
    section Testing
    단위 테스트                :j1, 2025-12-08, 2d
    통합 테스트                :j2, after j1, 2d
    성능 테스트                :j3, after j2, 1d
    section Optimization
    병렬 실행 최적화           :k1, 2025-12-08, 2d
    메모리 최적화              :k2, after k1, 1d
```

**완료 기준**:
- [x] 90% 이상 테스트 커버리지
- [x] 성능 오버헤드 5% 이내
- [x] 메모리 누수 없음

---

### 전체 타임라인

```mermaid
gantt
    title BlueprintFlow 전체 구현 로드맵
    dateFormat  YYYY-MM-DD

    section Phase 1
    기반 구조               :p1, 2025-11-21, 7d

    section Phase 2
    노드 구현               :p2, after p1, 10d

    section Phase 3
    데이터 흐름             :p3, after p2, 7d

    section Phase 4
    워크플로우 관리          :p4, after p3, 3d

    section Phase 5
    테스트 및 최적화         :p5, after p4, 7d

    section 마일스톤
    Alpha Release          :milestone, m1, after p3, 0d
    Beta Release           :milestone, m2, after p4, 0d
    Production Release     :milestone, m3, after p5, 0d
```

**총 소요 기간**: **34일 (약 5주)**

---

## 파일 구조

### Frontend

```
web-ui/src/
├── pages/
│   └── workflow/
│       ├── WorkflowBuilder.tsx          (메인 빌더 페이지, 500줄)
│       ├── WorkflowList.tsx             (워크플로우 목록, 200줄)
│       └── WorkflowExecutor.tsx         (실행 모니터, 300줄)
├── components/
│   └── workflow/
│       ├── Canvas.tsx                   (ReactFlow 캔버스, 400줄)
│       ├── NodePalette.tsx              (노드 목록, 200줄)
│       ├── PropertyPanel.tsx            (속성 패널, 300줄)
│       ├── Toolbar.tsx                  (도구 모음, 150줄)
│       ├── ExecutionMonitor.tsx         (진행률, 200줄)
│       └── nodes/
│           ├── YoloNode.tsx             (150줄)
│           ├── EdocrNode.tsx            (150줄)
│           ├── EdgnetNode.tsx           (150줄)
│           ├── SkinmodelNode.tsx        (150줄)
│           ├── IfNode.tsx               (200줄)
│           ├── MergeNode.tsx            (200줄)
│           └── LoopNode.tsx             (200줄)
├── store/
│   └── workflowStore.ts                 (Zustand 상태 관리, 300줄)
├── hooks/
│   ├── useWorkflowExecution.ts          (실행 훅, 200줄)
│   └── useWorkflowBuilder.ts            (빌더 훅, 150줄)
└── utils/
    ├── workflowEngine.ts                (클라이언트 엔진, 400줄)
    └── dataMapper.ts                    (데이터 매핑, 200줄)
```

**총 코드량**: ~4,000줄

---

### Backend

```
gateway-api/
├── api_server.py                        (워크플로우 엔드포인트 추가, +300줄)
├── services/
│   ├── pipeline_engine.py               (파이프라인 엔진, 500줄)
│   ├── workflow_manager.py              (워크플로우 관리, 300줄)
│   ├── node_executor.py                 (노드 실행 베이스, 400줄)
│   ├── data_mapper.py                   (데이터 매핑, 200줄)
│   └── executors/
│       ├── __init__.py
│       ├── base.py                      (BaseExecutor, 150줄)
│       ├── yolo_executor.py             (150줄)
│       ├── edocr_executor.py            (150줄)
│       ├── edgnet_executor.py           (150줄)
│       ├── skinmodel_executor.py        (150줄)
│       ├── if_executor.py               (200줄)
│       ├── merge_executor.py            (200줄)
│       └── loop_executor.py             (250줄)
├── models/
│   ├── workflow_schemas.py              (워크플로우 스키마, 200줄)
│   └── node_schemas.py                  (노드 스키마, 300줄)
└── utils/
    ├── graph_validator.py               (그래프 검증, 200줄)
    └── topological_sort.py              (위상 정렬, 150줄)
```

**총 코드량**: ~3,500줄

---

## 핵심 구현 코드 예시

### Pipeline Engine (간략화)

```python
# gateway-api/services/pipeline_engine.py
class PipelineEngine:
    def __init__(self, workflow_definition: dict):
        self.workflow = workflow_definition
        self.nodes = {n["id"]: n for n in workflow_definition["nodes"]}
        self.edges = workflow_definition["edges"]
        self.graph = self._build_graph()

    def _build_graph(self) -> Dict[str, List[str]]:
        """노드 ID를 키로, 연결된 노드 ID 리스트를 값으로 하는 그래프"""
        graph = {node_id: [] for node_id in self.nodes}
        for edge in self.edges:
            graph[edge["source"]].append(edge["target"])
        return graph

    def _validate_dag(self):
        """순환 참조 검사 (DFS)"""
        visited = set()
        rec_stack = set()

        def has_cycle(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)

            for neighbor in self.graph[node_id]:
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node_id)
            return False

        for node_id in self.nodes:
            if node_id not in visited:
                if has_cycle(node_id):
                    raise ValueError(f"Cycle detected in workflow")

    def _topological_sort(self) -> List[str]:
        """Kahn's algorithm for topological sorting"""
        in_degree = {node_id: 0 for node_id in self.nodes}

        for node_id in self.graph:
            for neighbor in self.graph[node_id]:
                in_degree[neighbor] += 1

        queue = [n for n in in_degree if in_degree[n] == 0]
        result = []

        while queue:
            node_id = queue.pop(0)
            result.append(node_id)

            for neighbor in self.graph[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(self.nodes):
            raise ValueError("Graph has cycles")

        return result

    async def execute(self, input_data: bytes) -> dict:
        """워크플로우 실행"""
        self._validate_dag()
        execution_order = self._topological_sort()

        context = {
            "input": input_data,
            "results": {}
        }

        for node_id in execution_order:
            node = self.nodes[node_id]

            # 입력 데이터 수집
            inputs = self._collect_inputs(node_id, context)

            # 노드 실행
            executor = self._get_executor(node["type"])
            result = await executor.execute(inputs, node["data"]["params"])

            # 결과 저장
            context["results"][node_id] = result

            # SSE 진행 상황 전송
            await self._send_progress(node_id, result)

        return context["results"]
```

---

## 마무리

이 설계서는 BlueprintFlow 완전 구현을 위한 **전체 아키텍처**를 제공합니다.

**다음 단계**:
1. 이 설계서 검토 후 승인
2. Phase 1부터 순차 구현 시작
3. 각 Phase 완료 후 데모 및 피드백

**예상 소요 시간**: **5주 (34일)**

---

**작성자**: Claude Code (Sonnet 4.5)
**검토 필요**: 승인 후 구현 시작
