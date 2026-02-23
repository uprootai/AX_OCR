# Section 10: DevOps & Infrastructure / DevOps 및 인프라

## Pages (5)
1. **DevOps Overview** - DevOps 체계 개요
2. **Docker Compose** - 컨테이너 오케스트레이션
3. **CI Pipeline** - 지속적 통합
4. **CD Pipeline** - 지속적 배포
5. **GPU Configuration** - GPU 설정 및 할당

---

## Mermaid Diagrams

### 1. Docker Architecture Graph
```mermaid
graph TD
    subgraph Host[Host Machine]
        DC[Docker Compose]
        subgraph GPU[GPU Services]
            YOLO[YOLO :5005]
            EDOCR[eDOCr2 :5002]
            VL[VL :5004]
            TROCR[TrOCR :5009]
            ESRGAN[ESRGAN :5010]
            ENS[Ensemble :5011]
            BOM[BOM :5020]
            TABLE[Table :5022]
        end

        subgraph CPU[CPU Services]
            PADDLE[PaddleOCR :5006]
            TESS[Tesseract :5008]
            SURYA[Surya :5013]
            DOCTR[DocTR :5014]
            EASY[EasyOCR :5015]
            LINE[Line Det :5016]
            PID[PID :5018]
            DCHK[Design :5019]
            COMP[Composer :5021]
            SKIN[SkinModel :5003]
            KN[Knowledge :5007]
        end

        subgraph Infra[Infrastructure]
            GW[Gateway :8000]
            WEB[Web UI :5173]
            BOM_FE[BOM FE :3000]
            NEO[Neo4j :7687]
        end
    end

    DC --> GPU & CPU & Infra

    style GPU fill:#fff3e0
    style CPU fill:#e8f5e9
    style Infra fill:#e1f5fe
```

### 2. CI Pipeline TD
```mermaid
flowchart TD
    PUSH[Git Push/PR] --> CI[CI Workflow]

    CI --> FE[Frontend Jobs]
    CI --> BE[Backend Jobs]

    FE --> LINT[ESLint]
    FE --> BUILD[npm run build]
    FE --> TEST_FE[Vitest 185 tests]

    BE --> RUFF[Ruff Linter]
    BE --> PYTEST[Pytest 364 tests]

    LINT --> SUM[Summary]
    BUILD --> SUM
    TEST_FE --> SUM
    RUFF --> SUM
    PYTEST --> SUM

    SUM --> |All Pass| READY[Ready to Merge]
    SUM --> |Fail| BLOCK[Block PR]

    style READY fill:#4caf50,color:#fff
    style BLOCK fill:#f44336,color:#fff
```

### 3. CD Pipeline TD
```mermaid
flowchart TD
    TRIGGER[CI Success / Manual] --> PRE[Pre-check]
    PRE --> BUILD[Build Images x6]
    BUILD --> STAGE[Staging Deploy]
    STAGE --> SMOKE[Smoke Tests]
    SMOKE --> |Pass| PROD[Production Deploy<br/>Manual Approval]
    SMOKE --> |Fail| ROLLBACK[Rollback]
    PROD --> VERIFY[Health Checks]
    VERIFY --> |Pass| DONE[✅ Deployed]
    VERIFY --> |Fail| ROLLBACK

    style DONE fill:#4caf50,color:#fff
    style ROLLBACK fill:#f44336,color:#fff
```

### 4. GPU Allocation TD
```mermaid
flowchart TD
    GPU0[GPU 0] --> YOLO[YOLO v11]
    GPU0 --> EDOCR[eDOCr2]
    GPU1[GPU 1] --> VL[Vision-Language]
    GPU1 --> TROCR[TrOCR]
    DYNAMIC[Dynamic Config] --> |Dashboard| GPU0 & GPU1

    style GPU0 fill:#ff9800,color:#fff
    style GPU1 fill:#2196f3,color:#fff
    style DYNAMIC fill:#9c27b0,color:#fff
```

---

## React Components

### CIPipelineViewer
```typescript
interface CIPipelineViewerProps {
  pipeline: CIStep[];
  currentRun?: CIRun;
  history: CIRun[];
}

// Visual CI pipeline with step status
// Click step → see logs, duration, test results
// History timeline
```

### ServicePortMap
```typescript
interface ServicePortMapProps {
  services: ServicePort[];
  groupBy?: 'category' | 'gpu' | 'status';
}

// Visual grid showing port allocation
// Color-coded by category
// Status indicators (running/stopped)
```

### DeploymentTimeline (Recharts)
```typescript
interface DeploymentTimelineProps {
  deployments: Deployment[];
  timeRange: [Date, Date];
}

// Timeline chart showing deployment history
// Mark success/failure/rollback events
// Duration metrics
```

---

## Content Outline

### Page 1: DevOps Overview
- Docker-based microservice architecture
- GitHub Actions CI/CD
- GPU resource management
- Monitoring and health checks

### Page 2: Docker Compose
- 21 containerized services
- Network: ax_poc_network (bridge)
- Volume mounts for model persistence
- GPU device reservation
- docker-compose.override.yml for local development

### Page 3: CI Pipeline
- Trigger: push to main/develop, PRs
- Frontend: ESLint → build → Vitest (185 tests)
- Backend: Ruff → Pytest (364 tests)
- Total: 549 tests
- Summary report generation

### Page 4: CD Pipeline
- Pre-check → Build → Staging → Production
- 6 Docker images built
- Smoke test suite
- Manual production approval gate
- Automatic rollback on failure

### Page 5: GPU Configuration
- Dynamic GPU allocation via Dashboard
- docker-compose.override.yml for GPU mapping
- Memory limit configuration
- Multi-GPU support

---

## Data Sources
- `docker-compose.yml`
- `.github/workflows/ci.yml`
- `.github/workflows/cd.yml`
- `gateway-api/routers/gpu_config_router.py`
- `gateway-api/routers/docker_router.py`

## Maintenance Triggers
- Docker service added/removed → update Docker page
- CI/CD workflow changed → update pipeline pages
- GPU config changes → update GPU page
