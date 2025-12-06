# BlueprintFlow에 Analyze 기능 통합

> 작성일: 2025-12-06
> 완료일: 2025-12-06
> 목표: /analyze 페이지의 상세 시각화 기능을 BlueprintFlow에 통합

---

## 현재 상태 분석

### /analyze에 있고 BlueprintFlow에 없는 기능

| 기능 | 설명 | 우선순위 | 상태 |
|------|------|:--------:|:----:|
| OCR 시각화 | 이미지 위에 바운딩박스 오버레이 | P1 | ✅ |
| 공차 분석 상세 UI | 제조 가능성 점수, 예측 공차 표시 | P1 | ✅ |
| GD&T 카운트 | Dimensions, GD&T, Text Blocks 개수 | P2 | ✅ |
| 결과 탭 UI | Overview/OCR/Segmentation/Tolerance 탭 | P2 | ⏭️ 선택 |
| JSON 다운로드 | 전체 결과 JSON 내보내기 | P3 | ✅ |

---

## Phase 1: 결과 시각화 컴포넌트 통합 ✅

### Task 1.1: OCRVisualization 컴포넌트 통합 ✅
- [x] `BlueprintFlowBuilder.tsx`에서 eDOCr2 노드 결과에 OCRVisualization 추가
- [x] 기존 `src/components/debug/OCRVisualization.tsx` 재사용
- [x] 이미지 + 바운딩박스 오버레이 표시
- [x] `imageBase64` prop 추가 (BlueprintFlow 호환)
- [x] `compact` prop 추가 (인라인 표시용)

**수정된 파일:**
```
web-ui/src/components/debug/OCRVisualization.tsx
  - imageBase64 prop 추가
  - compact mode 지원

web-ui/src/pages/blueprintflow/BlueprintFlowBuilder.tsx
  - eDOCr2 노드 output 섹션에 OCRVisualization 컴포넌트 추가
  - dimensions, gdt, text 데이터 전달
```

### Task 1.2: SegmentationVisualization 컴포넌트 통합 ✅
- [x] EDGNet 노드 결과에 SegmentationVisualization 추가
- [x] 기존 `src/components/debug/SegmentationVisualization.tsx` 재사용
- [x] `imageBase64` prop 추가 (BlueprintFlow 호환)
- [x] `compact` mode 추가 (요약 표시용)

**수정된 파일:**
```
web-ui/src/components/debug/SegmentationVisualization.tsx
  - imageBase64 prop 추가
  - compact mode 추가 (contour/text/dimension 개수, graph 정보)

web-ui/src/pages/blueprintflow/BlueprintFlowBuilder.tsx
  - EDGNet 노드 output 섹션에 SegmentationVisualization 컴포넌트 추가
```

---

## Phase 2: 공차 분석 상세 UI ✅

### Task 2.1: ToleranceVisualization 컴포넌트 생성 ✅
- [x] 새 컴포넌트 `src/components/debug/ToleranceVisualization.tsx` 생성
- [x] 제조 가능성 점수 Progress Bar
- [x] 난이도 Badge (Easy/Medium/Hard)
- [x] 예측 공차 값 그리드 (Flatness, Cylindricity, Position, Perpendicularity, Concentricity, Runout)
- [x] compact mode 및 full Card mode 지원

**신규 파일:**
```typescript
// src/components/debug/ToleranceVisualization.tsx
interface ToleranceVisualizationProps {
  toleranceData: {
    manufacturability?: {
      score: number;
      difficulty: string;
    };
    predicted_tolerances?: {
      flatness?: number;
      cylindricity?: number;
      position?: number;
      perpendicularity?: number;
      concentricity?: number;
      runout?: number;
    };
    analysis?: Record<string, any>;
  };
  compact?: boolean;
}
```

### Task 2.2: SkinModel 노드 결과에 적용 ✅
- [x] `BlueprintFlowBuilder.tsx`에서 SkinModel 노드에 ToleranceVisualization 추가

---

## Phase 3: 통계 및 요약 UI ✅

### Task 3.1: ResultSummaryCard 컴포넌트 생성 ✅
- [x] 새 컴포넌트 `src/components/blueprintflow/ResultSummaryCard.tsx` 생성
- [x] OCR: Dimensions 개수, GD&T 개수, Text Blocks 개수
- [x] Segmentation: Components 개수, Graph Nodes 개수
- [x] Tolerance: 제조 가능성 점수
- [x] 실행 상태 (success/error/pending) 표시
- [x] 총 실행 시간 표시

**신규 파일:**
```typescript
// src/components/blueprintflow/ResultSummaryCard.tsx
interface NodeResult {
  nodeId: string;
  nodeType: string;
  status: 'success' | 'error' | 'pending' | 'running';
  executionTime?: number;
  output?: any;
}

interface ResultSummaryCardProps {
  results: NodeResult[];
  totalExecutionTime?: number;
}
```

### Task 3.2: Pipeline Results 상단에 요약 표시 ✅
- [x] 전체 실행 완료 후 요약 카드 표시
- [x] 총 처리 시간, 성공/실패 노드 수

---

## Phase 4: 결과 탭 UI (선택적) ⏭️

### Task 4.1: 결과 패널 탭 모드 추가
- [ ] 현재 인라인 표시 외에 탭 모드 추가
- [ ] Overview, OCR, Segmentation, Tolerance 탭
- [ ] 토글 버튼으로 모드 전환

> **참고**: 현재 인라인 표시로 충분히 사용 가능. 필요시 향후 구현.

---

## Phase 5: 유틸리티 기능 ✅

### Task 5.1: JSON 다운로드 버튼 추가 ✅
- [x] 실행 완료 후 "JSON 다운로드" 버튼 표시
- [x] 전체 executionResult를 JSON 파일로 내보내기
- [x] 파일명 형식: `blueprintflow-result-YYYYMMDDHHMMSS.json`

### Task 5.2: 결과 공유 기능 (선택적) ⏭️
- [ ] 결과 URL 생성
- [ ] 클립보드 복사

> **참고**: JSON 다운로드로 충분히 공유 가능. 필요시 향후 구현.

---

## 구현 순서

```
Phase 1 (필수) ✅
├── Task 1.1: OCRVisualization 통합 ✅
└── Task 1.2: SegmentationVisualization 통합 ✅

Phase 2 (필수) ✅
├── Task 2.1: ToleranceVisualization 컴포넌트 ✅
└── Task 2.2: SkinModel 노드에 적용 ✅

Phase 3 (권장) ✅
├── Task 3.1: ResultSummaryCard 컴포넌트 ✅
└── Task 3.2: 요약 표시 ✅

Phase 4 (선택) ⏭️
└── Task 4.1: 탭 모드

Phase 5 (선택)
├── Task 5.1: JSON 다운로드 ✅
└── Task 5.2: 결과 공유 ⏭️
```

---

## 예상 작업량

| Phase | 예상 복잡도 | 상태 |
|-------|:-----------:|:----:|
| Phase 1 | 중 | ✅ 완료 |
| Phase 2 | 중 | ✅ 완료 |
| Phase 3 | 하 | ✅ 완료 |
| Phase 4 | 중 | ⏭️ 선택 |
| Phase 5 | 하 | ✅ 완료 (5.1) |

---

## 참고 파일

- `/analyze` 페이지: `web-ui/src/pages/analyze/Analyze.tsx`
- OCR 시각화: `web-ui/src/components/debug/OCRVisualization.tsx`
- Segmentation 시각화: `web-ui/src/components/debug/SegmentationVisualization.tsx`
- Tolerance 시각화: `web-ui/src/components/debug/ToleranceVisualization.tsx` (신규)
- ResultSummaryCard: `web-ui/src/components/blueprintflow/ResultSummaryCard.tsx` (신규)
- BlueprintFlow: `web-ui/src/pages/blueprintflow/BlueprintFlowBuilder.tsx`

---

## 완료 기준

- [x] eDOCr2 노드 실행 시 이미지 위에 바운딩박스 표시
- [x] EDGNet 노드 실행 시 세그멘테이션 요약 정보 표시
- [x] SkinModel 노드 실행 시 제조 가능성 점수/예측 공차 표시
- [x] 전체 파이프라인 실행 후 요약 통계 표시
- [x] JSON 다운로드 버튼
- [x] 빌드 성공 및 ESLint 에러 0개

---

## 결과 요약

**완료 작업:**
1. OCRVisualization - base64 이미지 및 compact mode 지원 추가
2. SegmentationVisualization - base64 이미지 및 compact mode 지원 추가
3. ToleranceVisualization - 신규 컴포넌트 생성
4. ResultSummaryCard - 신규 컴포넌트 생성
5. JSON 다운로드 버튼 - BlueprintFlowBuilder에 추가

**빌드 결과:** ✅ 성공 (14.14s)
