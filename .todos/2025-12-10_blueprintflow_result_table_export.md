# BlueprintFlow 결과 테이블 뷰 및 내보내기 기능 구현

> **작성일**: 2025-12-10
> **우선순위**: 높음 (사용성 필수 기능)
> **예상 작업량**: 중간 규모

---

## 1. 배경 및 목적

### 1.1 현재 상황
- BlueprintFlow에서 파이프라인 실행 후 결과가 JSON 형태로만 표시됨
- `ResultActions.tsx` 컴포넌트가 존재하지만 BlueprintFlow에 통합되어 있지 않음
- OCR 치수, BOM, 밸브 리스트 등 구조화된 데이터를 테이블로 볼 수 없음
- 시각화 이미지(base64)가 인라인으로 표시되지 않음

### 1.2 필요성
- 도면 분석 결과를 **즉시 확인**하고 **활용**할 수 있어야 함
- 고객/현장에서 Excel/CSV로 데이터를 내보내 후처리해야 하는 경우 많음
- P&ID 분석 결과(BOM, 연결 관계)를 시각적으로 확인해야 함

---

## 2. 구현 범위

### 2.1 Phase 1: 데이터 테이블 뷰 컴포넌트 (높음)

#### 2.1.1 `DataTableView.tsx` 신규 생성
**위치**: `web-ui/src/components/blueprintflow/DataTableView.tsx`

```typescript
// 컴포넌트 Props 설계
interface DataTableViewProps {
  data: unknown[];           // 배열 데이터
  columns?: ColumnDef[];     // 컬럼 정의 (자동 추론 가능)
  title?: string;            // 테이블 제목
  exportable?: boolean;      // 내보내기 버튼 표시
  searchable?: boolean;      // 검색 기능
  sortable?: boolean;        // 정렬 기능
  pageSize?: number;         // 페이지당 행 수
}

interface ColumnDef {
  key: string;               // 데이터 키
  label: string;             // 표시 레이블
  type?: 'string' | 'number' | 'percentage' | 'badge';
  width?: string;            // 컬럼 너비
  sortable?: boolean;
  render?: (value: unknown, row: unknown) => React.ReactNode;
}
```

#### 2.1.2 지원해야 할 데이터 타입
| 노드 타입 | 출력 필드 | 테이블 컬럼 |
|----------|----------|-------------|
| eDOCr2 | `dimensions` | 번호, 치수텍스트, 값, 공차, 신뢰도 |
| eDOCr2 | `gdt` | 번호, GD&T 기호, 값, 데이텀, 신뢰도 |
| PaddleOCR | `text_results` | 번호, 텍스트, 위치, 신뢰도 |
| YOLO-PID | `detections` | 번호, 클래스, 신뢰도, 바운딩박스 |
| Line Detector | `lines` | 번호, 시작점, 끝점, 색상타입, 스타일 |
| PID Analyzer | `bom` | 번호, 태그, 타입, 수량, 설명 |
| PID Analyzer | `valve_list` | 번호, 밸브ID, 타입, 신호타입, 연결 |
| PID Analyzer | `equipment_list` | 번호, 장비ID, 타입, 위치 |
| PID Analyzer | `connections` | 번호, 소스, 타겟, 라인색상, 스타일 |

#### 2.1.3 자동 컬럼 추론 로직
```typescript
function inferColumns(data: unknown[]): ColumnDef[] {
  if (!data || data.length === 0) return [];

  const sample = data[0];
  const keys = Object.keys(sample);

  return keys.map(key => ({
    key,
    label: formatLabel(key),  // snake_case → 한글 변환
    type: inferType(sample[key]),
    sortable: true,
  }));
}

// 한글 레이블 매핑
const LABEL_MAP = {
  'dimension_text': '치수',
  'confidence': '신뢰도',
  'color_type': '색상 타입',
  'color_type_korean': '색상',
  'line_style': '라인 스타일',
  'signal_type': '신호 타입',
  'source_symbol': '소스 심볼',
  'target_symbol': '타겟 심볼',
  // ...
};
```

---

### 2.2 Phase 2: 내보내기 기능 통합 (높음)

#### 2.2.1 BlueprintFlowBuilder에 ResultActions 통합
**파일**: `web-ui/src/pages/blueprintflow/BlueprintFlowBuilder.tsx`

```typescript
// 기존 JSON 다운로드 버튼 옆에 추가
<div className="flex gap-2">
  <Button onClick={handleDownloadJSON}>
    <FileJson /> JSON
  </Button>
  <Button onClick={handleDownloadCSV}>
    <FileSpreadsheet /> CSV
  </Button>
  <Button onClick={handleCopyClipboard}>
    <Copy /> 복사
  </Button>
</div>
```

#### 2.2.2 CSV 내보내기 로직 개선
**현재 문제**: `ResultActions.tsx`가 `ensemble.dimensions`만 지원
**개선 방향**: 모든 배열 데이터 자동 감지 및 내보내기

```typescript
function extractExportableData(result: ExecutionResult): ExportableDataset[] {
  const datasets: ExportableDataset[] = [];

  // 각 노드 결과에서 배열 데이터 추출
  result.node_statuses?.forEach(nodeStatus => {
    const output = nodeStatus.output;
    if (!output) return;

    // 알려진 배열 필드들
    const arrayFields = [
      'dimensions', 'gdt', 'text_results', 'detections',
      'lines', 'intersections', 'bom', 'valve_list',
      'equipment_list', 'connections', 'ocr_instruments'
    ];

    arrayFields.forEach(field => {
      if (Array.isArray(output[field]) && output[field].length > 0) {
        datasets.push({
          name: `${nodeStatus.node_id}_${field}`,
          data: output[field],
          nodeType: nodeStatus.node_type,
        });
      }
    });
  });

  return datasets;
}
```

#### 2.2.3 다중 시트 Excel 내보내기 (선택)
```typescript
// xlsx 라이브러리 사용
import * as XLSX from 'xlsx';

function downloadExcel(datasets: ExportableDataset[]) {
  const workbook = XLSX.utils.book_new();

  datasets.forEach(dataset => {
    const worksheet = XLSX.utils.json_to_sheet(dataset.data);
    XLSX.utils.book_append_sheet(workbook, worksheet, dataset.name);
  });

  XLSX.writeFile(workbook, 'blueprintflow_result.xlsx');
}
```

---

### 2.3 Phase 3: 시각화 이미지 표시 (높음)

#### 2.3.1 Base64 이미지 인라인 렌더링
**파일**: `web-ui/src/components/blueprintflow/VisualizationImage.tsx`

```typescript
interface VisualizationImageProps {
  base64: string;
  title?: string;
  downloadable?: boolean;
}

function VisualizationImage({ base64, title, downloadable }: VisualizationImageProps) {
  const imgSrc = base64.startsWith('data:')
    ? base64
    : `data:image/png;base64,${base64}`;

  return (
    <div className="relative">
      {title && <h4 className="text-sm font-medium mb-2">{title}</h4>}
      <img
        src={imgSrc}
        alt={title || 'Visualization'}
        className="max-w-full rounded border"
      />
      {downloadable && (
        <Button onClick={() => downloadImage(imgSrc, title)}>
          <Download /> 이미지 저장
        </Button>
      )}
    </div>
  );
}
```

#### 2.3.2 자동 시각화 감지 및 표시
```typescript
// 시각화 필드 자동 감지
const VISUALIZATION_FIELDS = [
  'visualization',
  'annotated_image',
  'result_image',
  'output_image',
  'segmentation_mask',
];

function extractVisualizations(output: Record<string, unknown>): Visualization[] {
  return VISUALIZATION_FIELDS
    .filter(field => output[field] && typeof output[field] === 'string')
    .map(field => ({
      name: field,
      base64: output[field] as string,
    }));
}
```

---

### 2.4 Phase 4: P&ID 전용 결과 패널 (중간)

#### 2.4.1 `PIDResultPanel.tsx` 신규 생성
**위치**: `web-ui/src/components/blueprintflow/PIDResultPanel.tsx`

```typescript
interface PIDResultPanelProps {
  connections: Connection[];
  bom: BOMEntry[];
  valveList: ValveSignal[];
  equipmentList: Equipment[];
  statistics: Statistics;
}

// 탭 기반 UI
<Tabs defaultValue="connections">
  <TabsList>
    <TabsTrigger value="connections">연결 관계 ({connections.length})</TabsTrigger>
    <TabsTrigger value="bom">BOM ({bom.length})</TabsTrigger>
    <TabsTrigger value="valves">밸브 ({valveList.length})</TabsTrigger>
    <TabsTrigger value="equipment">장비 ({equipmentList.length})</TabsTrigger>
  </TabsList>

  <TabsContent value="connections">
    <DataTableView
      data={connections}
      columns={connectionColumns}
      exportable
    />
  </TabsContent>
  {/* ... */}
</Tabs>
```

#### 2.4.2 연결 관계 시각화 (그래프 뷰)
```typescript
// react-flow 또는 cytoscape 활용
<ConnectionGraph
  connections={connections}
  symbols={symbols}
  highlightColorType={selectedColorType}
/>
```

---

### 2.5 Phase 5: 결과 필터링/정렬 (중간)

#### 2.5.1 테이블 필터 UI
```typescript
<DataTableView
  data={data}
  filters={[
    { key: 'color_type', type: 'select', options: colorTypes },
    { key: 'confidence', type: 'range', min: 0, max: 1 },
    { key: 'class_name', type: 'search' },
  ]}
/>
```

#### 2.5.2 전역 검색
```typescript
<SearchInput
  placeholder="테이블 전체 검색..."
  onChange={handleGlobalSearch}
/>
```

---

## 3. 파일 구조

```
web-ui/src/components/
├── blueprintflow/
│   ├── DataTableView.tsx        # [신규] 범용 테이블 뷰
│   ├── VisualizationImage.tsx   # [신규] Base64 이미지 표시
│   ├── PIDResultPanel.tsx       # [신규] P&ID 전용 결과 패널
│   ├── ResultExportButtons.tsx  # [신규] 내보내기 버튼 그룹
│   └── ...
├── results/
│   └── ResultActions.tsx        # [수정] 범용화
└── ui/
    └── DataTable.tsx            # [신규] shadcn/ui 스타일 테이블
```

---

## 4. 의존성 추가

```bash
# 테이블 정렬/필터링
npm install @tanstack/react-table

# Excel 내보내기 (선택)
npm install xlsx

# CSV 파싱 (필요시)
npm install papaparse
```

---

## 5. 구현 순서 (권장)

| 순서 | 작업 | 예상 복잡도 | 의존성 | 상태 |
|------|------|-------------|--------|------|
| 1 | `DataTableView.tsx` 기본 구현 | 중간 | 없음 | ✅ 완료 |
| 2 | BlueprintFlow에 CSV 버튼 추가 | 낮음 | 없음 | ✅ 완료 |
| 3 | `VisualizationImage.tsx` 구현 | 낮음 | 없음 | ✅ 완료 |
| 4 | 시각화 자동 감지 및 표시 | 낮음 | 3 | ✅ 완료 |
| 5 | 자동 컬럼 추론 로직 | 중간 | 1 | ✅ 완료 |
| 6 | 필터링/정렬 기능 | 중간 | 1, 5 | ✅ 완료 |
| 7 | `PIDResultPanel.tsx` 구현 | 중간 | 1 | ⏳ 선택 |
| 8 | Excel 다중 시트 내보내기 | 낮음 | xlsx 패키지 | ⏳ 선택 |
| 9 | 연결 그래프 시각화 | 높음 | 7 | ⏳ 선택 |

---

## 6. 테스트 계획

### 6.1 단위 테스트
```typescript
// DataTableView.test.tsx
describe('DataTableView', () => {
  it('should render table with data', () => {});
  it('should auto-infer columns from data', () => {});
  it('should sort by column', () => {});
  it('should filter by search query', () => {});
  it('should export to CSV', () => {});
});
```

### 6.2 E2E 테스트
```typescript
// e2e/result-table.spec.ts
test('OCR 결과를 테이블로 표시', async ({ page }) => {
  // 1. 파이프라인 실행
  // 2. 결과 패널에서 테이블 확인
  // 3. CSV 다운로드 버튼 클릭
  // 4. 파일 다운로드 확인
});
```

---

## 7. 예상 결과 UI

### 7.1 OCR 결과 테이블
```
┌─────────────────────────────────────────────────────────────┐
│ eDOCr2 치수 추출 결과 (15개)              [CSV] [Excel] [복사] │
├─────┬──────────────┬────────┬──────────┬─────────┬─────────┤
│  #  │ 치수          │ 값     │ 공차      │ 단위    │ 신뢰도  │
├─────┼──────────────┼────────┼──────────┼─────────┼─────────┤
│  1  │ ∅45 H7       │ 45     │ H7       │ mm      │ 92%     │
│  2  │ 100±0.1      │ 100    │ ±0.1     │ mm      │ 88%     │
│  3  │ 25.4         │ 25.4   │ -        │ mm      │ 95%     │
│ ... │ ...          │ ...    │ ...      │ ...     │ ...     │
└─────┴──────────────┴────────┴──────────┴─────────┴─────────┘
                    [이전] 1 / 3 [다음]
```

### 7.2 P&ID BOM 테이블
```
┌─────────────────────────────────────────────────────────────┐
│ P&ID Analyzer - BOM (32개)                [CSV] [Excel] [복사] │
├─────┬────────────┬─────────────┬────────┬──────────────────┤
│  #  │ 태그        │ 타입         │ 수량   │ 설명              │
├─────┼────────────┼─────────────┼────────┼──────────────────┤
│  1  │ V-101      │ ball_valve  │ 3      │ 볼밸브             │
│  2  │ P-001      │ pump        │ 1      │ 원심 펌프          │
│  3  │ HX-201     │ exchanger   │ 2      │ 열교환기           │
│ ... │ ...        │ ...         │ ...    │ ...              │
└─────┴────────────┴─────────────┴────────┴──────────────────┘
```

---

## 8. 성공 기준

- [x] OCR 결과(dimensions, gdt)가 테이블로 표시됨 ✅
- [x] P&ID 결과(BOM, valve_list, connections)가 테이블로 표시됨 ✅
- [x] CSV 다운로드가 모든 테이블 데이터에서 동작함 ✅
- [x] 시각화 이미지가 결과 패널에 인라인 표시됨 ✅
- [x] 테이블 정렬이 동작함 ✅
- [x] 테이블 검색/필터링이 동작함 ✅

## ✅ 완료 현황

**핵심 기능 (Phase 1-6) 모두 완료** - 2025-12-10

### 구현된 파일:
- `web-ui/src/components/blueprintflow/DataTableView.tsx` ✅
- `web-ui/src/components/blueprintflow/VisualizationImage.tsx` ✅
- `web-ui/src/pages/blueprintflow/BlueprintFlowBuilder.tsx` (통합 완료) ✅

### 구현된 기능:
1. **DataTableView**: 범용 테이블 뷰 (정렬, 검색, 페이지네이션, CSV/JSON 내보내기)
2. **VisualizationImage**: Base64 이미지 표시 (전체화면, 줌, 다운로드)
3. **자동 데이터 추출**: `extractArrayData()`, `extractVisualizationImages()`
4. **한글 레이블 매핑**: 67개 필드에 대한 한글 번역

### 선택 기능 (미구현):
- PIDResultPanel.tsx (탭 기반 전용 패널)
- Excel 다중 시트 내보내기 (xlsx)
- 연결 그래프 시각화 (cytoscape)

---

## 9. 참고 자료

- 현재 ResultActions: `web-ui/src/components/results/ResultActions.tsx`
- 현재 ResultSummaryCard: `web-ui/src/components/blueprintflow/ResultSummaryCard.tsx`
- BlueprintFlowBuilder: `web-ui/src/pages/blueprintflow/BlueprintFlowBuilder.tsx`
- @tanstack/react-table 문서: https://tanstack.com/table/latest
- xlsx 라이브러리: https://docs.sheetjs.com/

---

**작성자**: Claude Code (Opus 4.5)
**다음 작업**: Phase 1 - DataTableView.tsx 구현
