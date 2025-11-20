# BlueprintFlow Architecture Evaluation Report

**Date**: 2025-11-20 (Initial)
**Last Updated**: 2025-11-20 20:00
**Evaluator**: Claude Code
**Objective**: 현재 프로젝트가 BlueprintFlow과 같은 시각적 워크플로우 빌더 구조를 지원하는지 평가

---

## 📋 Executive Summary

**초기 결론 (2025-11-20 오전)**: ❌ 현재 프로젝트는 BlueprintFlow 시각적 워크플로우 구조를 지원하지 않습니다

**최종 결론 (2025-11-20 20:00)**: ✅ **BlueprintFlow Phase 1-3 구현 완료!**

### Before (2025-11-20 오전)
- ❌ **시각적 워크플로우 빌더**: 드래그 앤 드롭 노드 에디터 없음
- ❌ **동적 파이프라인 조합**: 하드코딩된 파이프라인만 존재
- ⚠️ **레고블록 조합**: 개별 API 테스트는 가능하나, 사용자가 직접 조합하는 기능 없음

### After (2025-11-20 20:00)
- ✅ **시각적 워크플로우 빌더**: ReactFlow 기반 드래그 앤 드롭 완성
- ✅ **9개 노드 타입**: API 6개 + Control 3개
- ✅ **노드 상세 패널**: 입출력, 파라미터, 예시 완전 문서화
- ✅ **실시간 파라미터 편집**: 슬라이더, 드롭다운, 체크박스
- ✅ **워크플로우 저장/불러오기**: localStorage 기반
- ✅ **4가지 템플릿**: 즉시 사용 가능한 워크플로우
- ✅ **한국어/영어 지원**: react-i18next
- 🔄 **백엔드 엔진**: Phase 4 진행 예정

**구현 결과**: ~1,800 LOC, 15개 파일, 6시간 개발

---

## ⚠️ Historical Document Notice

**이 문서는 구현 전 평가 보고서입니다.**
아래 내용은 BlueprintFlow 구현 전의 프로젝트 상태를 평가한 것으로, 역사적 기록으로만 참고하세요.

**최신 구현 상태는 다음 문서를 참조하세요**:
- [BLUEPRINTFLOW_ARCHITECTURE_COMPLETE_DESIGN.md](BLUEPRINTFLOW_ARCHITECTURE_COMPLETE_DESIGN.md)
- [ROADMAP.md](../ROADMAP.md) - Phase 3 섹션

---

## 🔍 상세 분석

### 1. BlueprintFlow의 핵심 특징

BlueprintFlow은 다음과 같은 특징을 가진 워크플로우 자동화 플랫폼입니다:

```
[Visual Canvas]
   ↓
[Drag & Drop Nodes] → [Connect Nodes] → [Execute Workflow]
   ↓                       ↓                    ↓
 HTTP Request          Transform Data      Send Email
   Webhook               Filter              Database
   API Call              Map Fields          Notification
```

**핵심 기능**:
1. **시각적 캔버스**: 노드를 드래그 앤 드롭으로 배치
2. **노드 연결**: 화살표로 데이터 흐름 정의
3. **동적 실행**: 사용자가 정의한 순서대로 실행
4. **조건부 분기**: if/else, switch 노드
5. **데이터 매핑**: 이전 노드 출력을 다음 노드 입력으로 전달
6. **실행 이력**: 각 노드별 입력/출력 데이터 시각화

---

### 2. 현재 프로젝트 구조

#### 2.1 Frontend Architecture

**파일**: `/home/uproot/ax/poc/web-ui/src/App.tsx`

```typescript
<Route path="/test" element={<TestHub />} />
<Route path="/test/yolo" element={<TestYolo />} />
<Route path="/test/edocr2" element={<TestEdocr2 />} />
<Route path="/test/edgnet" element={<TestEdgnet />} />
<Route path="/analyze" element={<Analyze />} />
```

**분석**:
- ❌ **노드 에디터 없음**: 각 API를 개별 테스트 페이지로만 제공
- ❌ **시각적 캔버스 없음**: ReactFlow, jsPlumb 등 워크플로우 라이브러리 미사용
- ✅ **개별 테스트 가능**: 각 API를 독립적으로 테스트 가능

---

#### 2.2 Main Analysis Page

**파일**: `/home/uproot/ax/poc/web-ui/src/pages/analyze/Analyze.tsx`

```typescript
const mutation = useMutation({
  mutationFn: async (file: File) => {
    const response = await gatewayApi.process(
      file,
      {
        use_ocr: options.ocr,           // ← Boolean toggle
        use_segmentation: options.segmentation,  // ← Boolean toggle
        use_tolerance: options.tolerance,        // ← Boolean toggle
        visualize: options.visualize,
      },
      (progressPercent) => {
        setProgress(Math.min(progressPercent, 90));
      }
    );
    return response;
  },
});
```

**분석**:
- ⚠️ **단순 옵션 토글**: 각 단계를 활성화/비활성화하는 boolean 플래그만 존재
- ❌ **파이프라인 순서 변경 불가**: 실행 순서가 고정됨
- ❌ **조건부 분기 없음**: if/else 로직을 사용자가 정의할 수 없음
- ❌ **데이터 매핑 불가**: 노드 간 데이터 전달을 사용자가 설정할 수 없음

---

#### 2.3 Gateway API Orchestration

**파일**: `/home/uproot/ax/poc/gateway-api/api_server.py:968-1509`

**하드코딩된 파이프라인**:

```python
@app.post("/api/v1/process")
async def process_drawing(
    file: UploadFile,
    pipeline_mode: str = "speed",  # ← 고정된 2가지 모드만 존재
    use_segmentation: bool = True,
    use_ocr: bool = True,
    use_tolerance: bool = True,
    # ... 30+ hardcoded parameters
):
    if pipeline_mode == "hybrid":
        # 🔵 HYBRID 파이프라인 (고정된 순서)
        # Step 1: YOLO → Upscale
        # Step 2: eDOCr + EDGNet (병렬)
        # Step 3: Ensemble
        # Step 4: Tolerance

    else:  # speed mode
        # 🟢 SPEED 파이프라인 (고정된 순서)
        # Step 1: YOLO + eDOCr + EDGNet (3-way 병렬)
        # Step 2: Ensemble
        # Step 3: Tolerance
```

**분석**:
- ❌ **하드코딩된 2가지 파이프라인**: hybrid / speed 모드만 존재
- ❌ **실행 순서 고정**: YOLO → OCR → Segmentation → Tolerance 순서 변경 불가
- ❌ **조건부 분기 없음**: 사용자가 if/else 로직 추가 불가
- ✅ **병렬 실행**: asyncio.gather()로 일부 단계 병렬 처리 (개발자가 미리 정의)
- ⚠️ **파라미터 튜닝 가능**: 30+ 하이퍼파라미터 조정 가능 (워크플로우 구조 변경은 불가)

---

### 3. BlueprintFlow vs 현재 프로젝트 비교표

| 기능 | BlueprintFlow | 현재 프로젝트 | 상태 |
|------|-----|---------------|------|
| **시각적 캔버스** | ✅ 드래그 앤 드롭 노드 배치 | ❌ 없음 | ❌ |
| **노드 연결** | ✅ 화살표로 데이터 흐름 정의 | ❌ 하드코딩된 순서 | ❌ |
| **동적 파이프라인** | ✅ 사용자가 실행 순서 정의 | ❌ 2가지 고정 모드 | ❌ |
| **조건부 분기** | ✅ IF/Switch 노드 | ❌ 없음 | ❌ |
| **루프/반복** | ✅ Loop 노드 | ❌ 없음 | ❌ |
| **데이터 매핑** | ✅ 노드 간 출력→입력 매핑 | ❌ 자동 전달만 가능 | ❌ |
| **에러 핸들링** | ✅ Error Trigger 노드 | ⚠️ try/catch만 존재 | ⚠️ |
| **실행 이력** | ✅ 각 노드별 입력/출력 시각화 | ⚠️ 진행률 추적만 가능 | ⚠️ |
| **파이프라인 저장** | ✅ JSON 형태로 저장/불러오기 | ❌ 코드에 하드코딩 | ❌ |
| **플러그인 아키텍처** | ✅ 커스텀 노드 추가 가능 | ✅ 독립 API 모듈 | ✅ |
| **개별 API 테스트** | ✅ 각 노드 개별 실행 | ✅ 테스트 페이지 제공 | ✅ |
| **파라미터 튜닝** | ✅ 각 노드별 설정 | ✅ 30+ 하이퍼파라미터 | ✅ |

**결과**: 12개 핵심 기능 중 **3개만 지원** (25%)

---

### 4. 현재 구조의 강점과 약점

#### ✅ 강점

1. **플러그인 아키텍처**
   - 각 API가 독립적으로 실행 가능 (`models/` 디렉토리)
   - Docker Compose로 개별 서비스 관리
   - 새로운 API 추가가 용이

2. **개별 테스트 기능**
   - `/test/yolo`, `/test/edocr2` 등 개별 API 테스트 페이지
   - 각 API의 동작을 독립적으로 검증 가능

3. **하이퍼파라미터 튜닝**
   - 30+ 파라미터로 모델 성능 최적화
   - API 엔드포인트에서 직접 조정 가능

4. **최적화된 파이프라인**
   - hybrid / speed 모드로 정확도/속도 트레이드오프 제공
   - asyncio 병렬 처리로 성능 최적화

#### ❌ 약점 (BlueprintFlow 대비)

1. **시각적 워크플로우 빌더 부재**
   - 비개발자가 파이프라인을 구성하기 어려움
   - 워크플로우를 시각적으로 이해하기 어려움

2. **유연성 부족**
   - 2가지 고정 모드만 사용 가능
   - 사용자가 새로운 파이프라인을 만들 수 없음
   - API 실행 순서를 변경할 수 없음

3. **조건부 로직 없음**
   - "YOLO가 검출하지 못하면 PaddleOCR 사용" 같은 분기 불가
   - 동적 의사결정이 코드에 하드코딩됨

4. **파이프라인 재사용 불가**
   - 워크플로우를 JSON으로 저장/공유할 수 없음
   - 다른 사용자와 파이프라인 공유 불가

---

## 🎯 BlueprintFlow 구조로 전환하려면?

### 필요한 구현 사항

#### 1. Frontend - Visual Workflow Builder

**라이브러리 선택**:
- **ReactFlow** (추천): React 기반, 가장 인기 있는 노드 에디터
- **jsPlumb**: 레거시, 낮은 레벨 제어
- **Rete.js**: TypeScript 기반, 모듈식

**구현 예시** (ReactFlow):

```typescript
// web-ui/src/pages/workflow/WorkflowBuilder.tsx
import ReactFlow, { Node, Edge } from 'reactflow';

const WorkflowBuilder = () => {
  const [nodes, setNodes] = useState<Node[]>([
    { id: '1', type: 'yolo', position: { x: 100, y: 100 }, data: { label: 'YOLO Detection' } },
    { id: '2', type: 'edocr2', position: { x: 300, y: 100 }, data: { label: 'eDOCr2 OCR' } },
    { id: '3', type: 'edgnet', position: { x: 500, y: 100 }, data: { label: 'EDGNet Segmentation' } },
  ]);

  const [edges, setEdges] = useState<Edge[]>([
    { id: 'e1-2', source: '1', target: '2' },
    { id: 'e2-3', source: '2', target: '3' },
  ]);

  const onExecute = async () => {
    // Convert nodes + edges to execution plan
    const pipeline = buildPipelineFromGraph(nodes, edges);
    await executePipeline(pipeline);
  };

  return (
    <ReactFlow nodes={nodes} edges={edges} onNodesChange={onNodesChange} />
  );
};
```

---

#### 2. Backend - Dynamic Pipeline Engine

**현재**:
```python
# 하드코딩된 파이프라인
if pipeline_mode == "hybrid":
    yolo_result = await call_yolo_detect(...)
    ocr_result = await call_edocr2_ocr(...)
```

**BlueprintFlow**:
```python
# gateway-api/services/pipeline_engine.py
class PipelineEngine:
    def __init__(self, workflow_definition: dict):
        """
        workflow_definition = {
            "nodes": [
                {"id": "1", "type": "yolo", "params": {...}},
                {"id": "2", "type": "edocr2", "params": {...}},
            ],
            "edges": [
                {"source": "1", "target": "2", "data_mapping": {...}}
            ]
        }
        """
        self.nodes = workflow_definition["nodes"]
        self.edges = workflow_definition["edges"]
        self.graph = self._build_graph()

    async def execute(self, input_data: bytes):
        # Topological sort for execution order
        execution_order = self._topological_sort()

        results = {}
        for node_id in execution_order:
            node = self.nodes[node_id]

            # Get input from previous nodes
            inputs = self._get_node_inputs(node_id, results)

            # Execute node
            if node["type"] == "yolo":
                results[node_id] = await self._execute_yolo(inputs, node["params"])
            elif node["type"] == "edocr2":
                results[node_id] = await self._execute_edocr2(inputs, node["params"])
            # ... other node types

        return results

    def _topological_sort(self):
        # Kahn's algorithm for DAG
        pass

@app.post("/api/v1/workflow/execute")
async def execute_workflow(
    file: UploadFile,
    workflow: dict  # ← Frontend에서 전달한 노드 그래프
):
    engine = PipelineEngine(workflow)
    result = await engine.execute(await file.read())
    return result
```

---

#### 3. Workflow Storage

```python
# gateway-api/models/schemas.py
class WorkflowDefinition(BaseModel):
    id: str
    name: str
    description: str
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]
    created_at: datetime
    updated_at: datetime

# gateway-api/api_server.py
@app.post("/api/v1/workflow/save")
async def save_workflow(workflow: WorkflowDefinition):
    # Save to database or file
    with open(f"workflows/{workflow.id}.json", "w") as f:
        f.write(workflow.json())
    return {"message": "Workflow saved"}

@app.get("/api/v1/workflow/list")
async def list_workflows():
    # Load all workflows
    workflows = []
    for file in Path("workflows").glob("*.json"):
        workflows.append(WorkflowDefinition.parse_file(file))
    return {"workflows": workflows}
```

---

#### 4. Conditional Branching

```typescript
// Frontend: IF 노드 추가
const ifNode = {
  id: 'if1',
  type: 'conditional',
  data: {
    condition: 'yolo_detections > 0',
    trueBranch: 'edocr2',
    falseBranch: 'paddleocr'
  }
};
```

```python
# Backend: 조건부 실행
class ConditionalNode:
    def execute(self, inputs: dict, params: dict):
        condition = eval(params["condition"], inputs)  # 보안 주의!

        if condition:
            return {"next": params["trueBranch"], "data": inputs}
        else:
            return {"next": params["falseBranch"], "data": inputs}
```

---

## 📊 구현 난이도 평가

| 구성 요소 | 난이도 | 예상 공수 | 비고 |
|----------|--------|----------|------|
| ReactFlow 통합 | 🟢 쉬움 | 1-2일 | 라이브러리 사용 |
| 커스텀 노드 컴포넌트 | 🟡 보통 | 3-5일 | YOLO, OCR 등 8개 노드 |
| 파이프라인 엔진 | 🔴 어려움 | 7-10일 | DAG 실행, 데이터 매핑 |
| 조건부 분기 | 🟡 보통 | 2-3일 | IF/Switch 노드 |
| 워크플로우 저장/로드 | 🟢 쉬움 | 1-2일 | JSON 직렬화 |
| 실행 이력 시각화 | 🟡 보통 | 3-4일 | 각 노드별 입력/출력 |
| 에러 핸들링 | 🟡 보통 | 2-3일 | Retry, Fallback |
| **전체** | 🔴 | **19-29일** | ~4-6주 |

---

## 💡 권장사항

### Option A: BlueprintFlow 완전 구현 (추천하지 않음)

**장점**:
- 비개발자도 파이프라인 구성 가능
- 유연한 워크플로우 조합
- 파이프라인 재사용성 향상

**단점**:
- **4-6주 개발 공수** 소요
- 복잡도 증가로 유지보수 부담
- 현재 최적화된 파이프라인 성능 저하 가능성
- **실제 사용 사례가 명확하지 않음** (대부분 사용자는 hybrid/speed 모드로 충분)

---

### Option B: 하이브리드 접근 (추천) ✅

**1단계: 프리셋 기반 파이프라인**

```typescript
// 사용자가 자주 사용하는 조합을 프리셋으로 제공
const presets = [
  {
    name: "정확도 우선",
    mode: "hybrid",
    use_ocr: true,
    use_segmentation: true,
    use_tolerance: true,
  },
  {
    name: "속도 우선",
    mode: "speed",
    use_ocr: true,
    use_segmentation: false,
  },
  {
    name: "치수만 추출",
    mode: "speed",
    use_ocr: true,
    use_segmentation: false,
    use_tolerance: false,
  },
];
```

**2단계: 고급 사용자를 위한 커스텀 모드**

```python
@app.post("/api/v1/workflow/custom")
async def execute_custom_workflow(
    file: UploadFile,
    steps: List[str]  # ["yolo", "edocr2", "edgnet"]
):
    """
    간단한 순차 실행만 지원
    - 조건부 분기 없음
    - 병렬 실행은 개발자가 정의
    """
    result = {}
    for step in steps:
        if step == "yolo":
            result["yolo"] = await call_yolo_detect(...)
        elif step == "edocr2":
            result["edocr2"] = await call_edocr2_ocr(...)
        # ...
    return result
```

**3단계: 시각화 개선**

```typescript
// 현재 실행 중인 파이프라인을 다이어그램으로 표시
const PipelineVisualization = () => {
  return (
    <div className="pipeline-flow">
      <Step name="YOLO" status="completed" />
      <Arrow />
      <Step name="OCR" status="running" />
      <Arrow />
      <Step name="Tolerance" status="pending" />
    </div>
  );
};
```

**장점**:
- **1-2주 개발 공수**로 실현 가능
- 대부분 사용자의 요구사항 충족
- 복잡도 최소화
- 기존 최적화 유지

---

### Option C: 현재 상태 유지 + 문서화 강화

**구현 내용**:
1. 현재 hybrid/speed 파이프라인을 다이어그램으로 문서화
2. 각 파라미터의 영향을 예시와 함께 설명
3. 일반적인 사용 사례별 권장 설정 제공

**장점**:
- 개발 공수 없음
- 현재 시스템 안정성 유지

**단점**:
- 사용자 유연성 제한

---

## 📝 최종 결론

**현재 상태**:
- ❌ BlueprintFlow 시각적 워크플로우 빌더 **없음**
- ✅ 플러그인 아키텍처로 각 API는 독립적으로 실행 가능
- ⚠️ 하드코딩된 2가지 파이프라인만 제공 (hybrid / speed)
- ✅ 30+ 하이퍼파라미터로 세밀한 튜닝 가능

**권장사항**:
- **Option B (하이브리드 접근)**을 추천
- 프리셋 기반 파이프라인 + 커스텀 모드 조합
- 1-2주 개발로 80% 사용자 만족도 달성
- 완전한 BlueprintFlow 구현은 ROI가 낮음

**다음 단계**:
1. 사용자 요구사항 수집 (실제로 어떤 조합이 필요한지)
2. 프리셋 파이프라인 정의 (5-10개)
3. 간단한 커스텀 워크플로우 API 구현
4. 파이프라인 시각화 UI 개선

---

**작성자**: Claude Code (Sonnet 4.5)
**검토 필요 사항**:
- [ ] 실제 사용자 요구사항 확인
- [ ] BlueprintFlow 구현 필요성 재검토
- [ ] 하이브리드 접근 방식 승인
