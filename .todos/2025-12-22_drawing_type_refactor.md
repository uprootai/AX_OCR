# Drawing Type 리팩토링 구현 계획

> 작성일: 2025-12-22
> 목표: drawing_type을 ImageInput으로 이동하고, 도면 타입별 노드 추천 기능 추가

---

## 1. 개요

### 현재 문제점
```
ImageInput → YOLO → AI BOM (drawing_type 선택)
                         ↑
                    여기서 도면 타입 선택해봤자
                    이미 YOLO를 선택한 후라 의미 없음
```

### 개선 방향
```
ImageInput (drawing_type 선택) → 추천 노드 표시 → 사용자가 적절한 노드 연결
                ↓
        도면 타입에 따라
        YOLO vs YOLO-PID vs 기타 추천
```

---

## 2. 도면 타입별 추천 노드

| 도면 타입 | 추천 검출 노드 | 추천 분석 노드 | 추천 OCR |
|----------|--------------|--------------|----------|
| **mechanical** (기계 부품도) | YOLO (14클래스) | SkinModel (공차) | eDOCr2 |
| **mechanical_part** (기계 상세도) | YOLO (14클래스) | SkinModel (공차) | eDOCr2 |
| **pid** (P&ID) | YOLO-PID (60클래스) | PID Analyzer, Line Detector | PaddleOCR |
| **assembly** (조립도) | YOLO (14클래스) | - | eDOCr2 |
| **electrical** (전기 회로도) | 별도 모델 필요 (미지원) | - | PaddleOCR |
| **architectural** (건축 도면) | 별도 모델 필요 (미지원) | - | Tesseract |
| **auto** (자동) | VL (분류) → 분류 결과에 따라 추천 | - | - |

---

## 3. 파일별 변경 사항

### 3.1 `web-ui/src/config/nodes/inputNodes.ts`

**추가 내용:**
```typescript
imageinput: {
  // 기존 내용 유지...
  parameters: [
    {
      name: 'drawing_type',
      type: 'select',
      default: 'auto',
      options: [
        { value: 'auto', label: '🤖 자동 감지', ... },
        { value: 'mechanical', label: '⚙️ 기계 부품도', ... },
        { value: 'mechanical_part', label: '🔧 기계 상세도', ... },
        { value: 'pid', label: '🔬 P&ID (배관계장도)', ... },
        { value: 'assembly', label: '🔩 조립도', ... },
        { value: 'electrical', label: '⚡ 전기 회로도', ... },
        { value: 'architectural', label: '🏗️ 건축 도면', ... },
      ],
      description: '📐 도면 타입 선택',
      tooltip: '도면 타입에 따라 최적의 분석 노드를 추천합니다.',
    }
  ],
  // 도면 타입별 추천 노드 매핑
  recommendedPipelines: {
    auto: {
      description: 'VL 노드로 도면 타입을 먼저 분류합니다',
      nodes: ['vl'],
      tips: 'VL 출력을 확인 후 적절한 검출 노드를 선택하세요',
    },
    mechanical: {
      description: '기계 부품 검출 및 치수 분석',
      nodes: ['yolo', 'edocr2', 'skinmodel', 'blueprint-ai-bom'],
      tips: 'YOLO → eDOCr2 → SkinModel → AI BOM 순서 권장',
    },
    mechanical_part: {
      description: '기계 상세도 분석 (치수 중심)',
      nodes: ['yolo', 'edocr2', 'skinmodel', 'blueprint-ai-bom'],
      tips: 'YOLO → eDOCr2 → SkinModel → AI BOM 순서 권장',
    },
    pid: {
      description: 'P&ID 심볼 및 라인 분석',
      nodes: ['yolo-pid', 'line-detector', 'pid-analyzer', 'design-checker'],
      tips: 'YOLO-PID → Line Detector → PID Analyzer 순서 권장',
    },
    assembly: {
      description: '조립도 부품 검출',
      nodes: ['yolo', 'edocr2', 'blueprint-ai-bom'],
      tips: 'YOLO → eDOCr2 → AI BOM 순서 권장',
    },
    electrical: {
      description: '전기 회로도 (현재 제한적 지원)',
      nodes: ['paddleocr'],
      tips: '전용 검출 모델 개발 중',
      warning: '현재 전기 회로도 전용 검출 모델이 없습니다',
    },
    architectural: {
      description: '건축 도면 (현재 제한적 지원)',
      nodes: ['tesseract'],
      tips: '전용 검출 모델 개발 중',
      warning: '현재 건축 도면 전용 검출 모델이 없습니다',
    },
  }
}
```

### 3.2 `web-ui/src/config/nodes/bomNodes.ts`

**변경 내용:**
```typescript
'blueprint-ai-bom': {
  // 기존 내용 유지, 단 parameters 변경
  parameters: [
    // drawing_type 제거
    {
      name: 'features',
      type: 'multiselect',
      default: ['verification'],
      options: [
        {
          value: 'verification',
          label: '✅ Human-in-the-Loop 검증',
          description: '검출 결과를 수동으로 확인하고 수정합니다',
        },
        {
          value: 'gt_comparison',
          label: '📊 GT 비교 (Precision/Recall/F1)',
          description: 'Ground Truth와 비교하여 성능 메트릭을 표시합니다',
        },
        {
          value: 'dimension_extraction',
          label: '📏 치수 추출 (Phase 2)',
          description: 'OCR로 치수 텍스트를 추출합니다',
          disabled: true,  // Phase 2
        },
        {
          value: 'relation_analysis',
          label: '🔗 심볼-치수 관계 분석 (Phase 2)',
          description: '심볼과 치수 간의 관계를 분석합니다',
          disabled: true,  // Phase 2
        },
      ],
      description: '🛠️ 활성화할 기능 선택',
      tooltip: '검증 UI에서 사용할 기능을 선택합니다. Phase 2 기능은 향후 지원 예정입니다.',
    },
  ],
}
```

### 3.3 `web-ui/src/components/blueprintflow/NodePalette.tsx`

**추가 내용:**
- drawing_type 선택 시 추천 노드 패널 표시
- 추천 노드 클릭 시 자동으로 캔버스에 추가
- 추천 파이프라인 힌트 표시

```typescript
// 추천 노드 패널 컴포넌트
const RecommendedNodesPanel = ({ drawingType, onAddNode }) => {
  const recommendations = DRAWING_TYPE_RECOMMENDATIONS[drawingType];

  return (
    <div className="recommended-nodes-panel">
      <h4>📌 추천 노드</h4>
      <p>{recommendations.description}</p>
      <div className="node-chips">
        {recommendations.nodes.map(nodeType => (
          <button onClick={() => onAddNode(nodeType)}>
            + {nodeType}
          </button>
        ))}
      </div>
      <p className="tip">💡 {recommendations.tips}</p>
      {recommendations.warning && (
        <p className="warning">⚠️ {recommendations.warning}</p>
      )}
    </div>
  );
};
```

### 3.4 `gateway-api/api_specs/blueprint-ai-bom.yaml`

**변경 내용:**
```yaml
parameters:
  # drawing_type 제거
  - name: features
    type: array
    default: ['verification']
    required: false
    description: 활성화할 기능 목록
    items:
      type: string
      enum:
        - verification
        - gt_comparison
        - dimension_extraction
        - relation_analysis
```

### 3.5 `gateway-api/blueprintflow/executors/bom_executor.py`

**변경 내용:**
```python
async def execute(self, inputs: Dict[str, Any], context: Any = None):
    # drawing_type은 더 이상 여기서 처리하지 않음
    # ImageInput에서 이미 설정되어 context에 전달됨

    # features 파라미터 처리
    features = self.parameters.get("features", ["verification"])

    # 세션 생성 시 features 전달
    session_id = await self._create_session(image_data, features)
```

---

## 4. 구현 순서

1. **inputNodes.ts** - drawing_type 추가 + recommendedPipelines 정의
2. **bomNodes.ts** - drawing_type 제거 + features 추가
3. **blueprint-ai-bom.yaml** - 스펙 업데이트
4. **NodePalette.tsx** - 추천 노드 UI 구현
5. **bom_executor.py** - features 처리 로직
6. **빌드 및 테스트**

---

## 5. UI 목업

### ImageInput 노드 선택 시
```
┌─────────────────────────────────────┐
│ 📄 Image Input                      │
├─────────────────────────────────────┤
│ 파라미터                            │
│                                     │
│ 📐 도면 타입                        │
│ ┌─────────────────────────────────┐ │
│ │ ⚙️ 기계 부품도              ▼ │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ 📌 추천 노드                    │ │
│ │                                 │ │
│ │ 기계 부품 검출 및 치수 분석     │ │
│ │                                 │ │
│ │ [+ YOLO] [+ eDOCr2]            │ │
│ │ [+ SkinModel] [+ AI BOM]       │ │
│ │                                 │ │
│ │ 💡 YOLO → eDOCr2 → SkinModel   │ │
│ │    → AI BOM 순서 권장          │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### AI BOM 노드 선택 시
```
┌─────────────────────────────────────┐
│ 📊 Blueprint AI BOM                 │
├─────────────────────────────────────┤
│ 파라미터                            │
│                                     │
│ 🛠️ 활성화할 기능                   │
│ ┌─────────────────────────────────┐ │
│ │ ☑ ✅ Human-in-the-Loop 검증   │ │
│ │ ☐ 📊 GT 비교 (Precision/...)  │ │
│ │ ☐ 📏 치수 추출 (Phase 2) 🔒   │ │
│ │ ☐ 🔗 관계 분석 (Phase 2) 🔒   │ │
│ └─────────────────────────────────┘ │
│                                     │
│ 💡 YOLO 노드 연결 필수             │
└─────────────────────────────────────┘
```

---

## 6. 추가 고려사항

### 6.1 Context 전달
- ImageInput에서 설정한 drawing_type이 downstream 노드에 전달되어야 함
- workflowStore에서 context 관리 필요

### 6.2 동적 노드 추천
- 이후 확장: 실제로 노드를 자동 배치하는 기능
- 현재: 추천 노드 버튼 클릭 시 수동 추가

### 6.3 호환성
- 기존 워크플로우 (drawing_type이 AI BOM에 있는 경우) 처리
- 마이그레이션 로직 필요 시 추가
