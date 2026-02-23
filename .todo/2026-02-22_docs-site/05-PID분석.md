# Section 6: P&ID Analysis / P&ID 분석

## Pages (5)
1. **P&ID Overview** - P&ID 분석 파이프라인 소개
2. **Symbol Detection** - 심볼 검출 및 인식
3. **Line Detection** - 라인/배관 검출
4. **Connectivity Analysis** - 연결성 분석
5. **Design Checker** - 설계 규칙 검증

---

## Mermaid Diagrams

### 1. P&ID Pipeline LR
```mermaid
flowchart LR
    IMG[P&ID 도면] --> SYM[심볼 검출<br/>YOLO]
    IMG --> LN[라인 검출<br/>Line Detector]
    SYM --> CONN[연결성 분석<br/>PID Analyzer]
    LN --> CONN
    CONN --> DC[Design Checker]
    CONN --> COMP[PID Composer<br/>SVG 오버레이]
    DC --> REPORT[검증 보고서]

    style SYM fill:#ff9800,color:#fff
    style LN fill:#4caf50,color:#fff
    style CONN fill:#2196f3,color:#fff
    style DC fill:#f44336,color:#fff
```

### 2. Connectivity Graph
```mermaid
graph LR
    V1[Valve V-101] --> P1[Pump P-201]
    P1 --> HX[Heat Exchanger E-301]
    HX --> T1[Tank T-401]
    T1 --> V2[Valve V-102]
    V2 --> V1

    style V1 fill:#ff9800
    style P1 fill:#2196f3
    style HX fill:#4caf50
    style T1 fill:#9c27b0
```

### 3. Design Check Rule Engine TD
```mermaid
flowchart TD
    INPUT[P&ID Connectivity Graph] --> RULES{Rule Engine}
    RULES --> R1[밸브 배치 규칙]
    RULES --> R2[계기 연결 규칙]
    RULES --> R3[안전장치 규칙]
    RULES --> R4[BWMS 장비 규칙]

    R1 --> CHECK[규칙 검증]
    R2 --> CHECK
    R3 --> CHECK
    R4 --> CHECK

    CHECK --> PASS[✅ Pass]
    CHECK --> WARN[⚠️ Warning]
    CHECK --> FAIL[❌ Violation]
```

### 4. BWMS Equipment Sequence
```mermaid
sequenceDiagram
    participant U as User
    participant DC as Design Checker
    participant RB as Rule Base
    participant R as Report

    U->>DC: Submit P&ID
    DC->>DC: Parse connectivity
    DC->>RB: Load BWMS rules
    RB-->>DC: 50+ design rules
    DC->>DC: Evaluate each rule
    DC-->>R: Generate report
    R-->>U: Pass/Warn/Fail results
```

---

## React Components

### PIDPipelineDiagram (React Flow)
```typescript
interface PIDPipelineDiagramProps {
  pipeline: PIDPipelineStep[];
  activeStep?: string;
  results?: PIDAnalysisResult;
}

// Interactive P&ID analysis pipeline
// Click step → see intermediate results
// Highlight active processing step
```

### ConnectivityGraph
```typescript
interface ConnectivityGraphProps {
  nodes: PIDSymbol[];
  edges: PIDConnection[];
  highlightPath?: string[];
}

// Interactive graph showing P&ID connectivity
// Click node → symbol details
// Trace flow path highlighting
```

### DesignCheckerResults
```typescript
interface DesignCheckerResultsProps {
  results: DesignCheckResult[];
  filterSeverity?: 'pass' | 'warning' | 'violation';
}

// Results table with severity badges
// Expandable rule details
// Filter by severity
```

---

## Content Outline

### Page 1: P&ID Overview
- P&ID (Piping and Instrumentation Diagram) analysis pipeline
- Symbol detection + Line detection → Connectivity → Design Check
- BWMS (Ballast Water Management System) specialization

### Page 2: Symbol Detection
- YOLO-based P&ID symbol detection
- Symbol categories: valves, pumps, instruments, tanks
- Detection confidence and NMS

### Page 3: Line Detection
- Line Detector API for pipe routing
- Line type classification (process, instrument, electrical)
- Intersection detection

### Page 4: Connectivity Analysis
- Graph-based connectivity analysis
- Equipment-to-equipment flow tracing
- BOM generation from P&ID

### Page 5: Design Checker
- Rule-based design verification
- BWMS equipment rules (50+)
- Compliance reporting
- Pass/Warning/Violation classification

---

## Data Sources
- `models/pid-analyzer-api/`
- `models/design-checker-api/bwms_rules.py`
- `models/line-detector-api/`
- `blueprint-ai-bom/backend/services/connectivity_analyzer.py`
- `models/pid-composer-api/`

## Maintenance Triggers
- New P&ID rules added → update Design Checker page
- Symbol classes changed → update Symbol Detection page
- Connectivity algorithm updated → update analysis page
