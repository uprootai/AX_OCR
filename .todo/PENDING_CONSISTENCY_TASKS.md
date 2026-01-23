# 일관성 유지 필요 작업 목록

> **작성일**: 2026-01-22
> **기준 커밋**: 마지막 커밋 대비 변경사항 분석
> **상태**: 검토 및 작업 필요

---

## 1. SVG Common 모듈 일관성

### 현황
`svg_common.py`가 4개 모델에 추가됨 (공통 유틸리티 추출):
- ✅ `models/yolo-api/services/svg_common.py`
- ✅ `models/edocr2-v2-api/services/svg_common.py`
- ✅ `models/paddleocr-api/services/svg_common.py`
- ✅ `models/line-detector-api/services/svg_common.py`

### 미적용 대상
- [ ] `models/pid-composer-api/services/svg_generator.py`
  - 현재 자체 `_escape_html` 함수 없음 (확인 필요)
  - svg_common.py 도입 검토

### 작업 내용
```python
# 공통 유틸리티:
- escape_html()      # HTML 특수문자 이스케이프
- create_svg_header() # SVG 헤더 생성
- create_svg_footer() # SVG 푸터 생성
- create_label_element() # 라벨 엘리먼트 생성
- DEFAULT_COLORS     # 기본 색상 정의
- get_color()        # 카테고리별 색상 반환
```

### 작업 항목
- [ ] pid-composer-api에 svg_common.py 필요 여부 검토
- [ ] 다른 API (tesseract, trocr 등)에서 SVG 생성 여부 확인
- [ ] 중복 코드 제거 완료 확인

---

## 2. useLayerToggle 훅 일관성

### 현황
새로운 공통 훅 `useLayerToggle.ts` 추가:
- ✅ `web-ui/src/components/debug/YOLOVisualization.tsx` - 적용됨
- ✅ `web-ui/src/components/debug/OCRVisualization.tsx` - 적용됨

### 미적용 대상
- [ ] `web-ui/src/components/pid/PIDOverlayViewer.tsx`
  - **현재 자체 구현된 레이어 토글 로직 있음 (116행)**
  - `visibility`, `setVisibility` useState 사용 중
  - `useLayerToggle` 훅으로 리팩토링 가능

### 작업 내용
```typescript
// 훅 제공 기능:
- visibility: Record<T, boolean>  // 레이어 표시 상태
- toggleLayer(layer: T)           // 토글 함수
- showLabels, toggleLabels()      // 라벨 토글
- layerConfigs                    // UI 렌더링용 설정
- visibleCount, totalCount        // 통계
```

### 작업 항목
- [ ] PIDOverlayViewer에 useLayerToggle 훅 적용 검토
- [ ] 기존 visibility 로직을 훅으로 마이그레이션
- [ ] PID_LAYER_CONFIG 활용 (이미 정의됨)

---

## 3. DSE Bearing 노드 정의 일관성

### 현황
5개 DSE Bearing 노드가 추가됨:

| 노드 | apiRegistry | analysisNodes | api_spec | executor |
|------|-------------|---------------|----------|----------|
| titleblock | ✅ | ✅ | ✅ | ✅ |
| partslist | ✅ | ✅ | ✅ | ✅ |
| dimensionparser | ✅ | ✅ | ✅ | ✅ |
| bommatcher | ✅ | ✅ | ✅ | ✅ |
| quotegenerator | ✅ | ✅ | ✅ | ✅ |

### 검토 필요 사항
- [ ] `nodeDefinitions.ts` 메인 파일에 노드 등록 확인
- [ ] 프론트엔드 BlueprintFlow에서 노드 드래그 가능 여부
- [ ] 각 노드의 inputs/outputs 타입 일관성

### 작업 항목
- [ ] nodeDefinitions.ts에서 analysisNodes import 확인
- [ ] BlueprintFlowBuilder에서 DSE Bearing 노드 표시 테스트
- [ ] 노드 연결 호환성 테스트 (Image → TitleBlock 등)

---

## 4. API Registry 일관성

### 현황
apiRegistry.ts에 5개 API 추가:
```typescript
// 추가된 API:
- titleblock (port: 8000, gateway 내부)
- partslist (port: 8000, gateway 내부)
- dimensionparser (port: 8000, gateway 내부)
- bommatcher (port: 8000, gateway 내부)
- quotegenerator (port: 8000, gateway 내부)
```

### 검토 필요 사항
- [ ] 기존 API와 port 충돌 없음 확인 (모두 8000 gateway)
- [ ] containerName: 'gateway-api' 설정 일관성
- [ ] Dashboard API 목록에 표시 여부

### 작업 항목
- [ ] Dashboard에서 DSE Bearing API 상태 표시 확인
- [ ] 헬스체크 로직에 포함 여부 확인
- [ ] API 문서(/docs)에 엔드포인트 노출 확인

---

## 5. 프론트엔드 컴포넌트 일관성

### 추가된 컴포넌트
```
web-ui/src/components/dsebearing/
├── QuotePreview.tsx    # 견적서 미리보기/편집
└── index.ts            # 모듈 export
```

### 검토 필요 사항
- [ ] 다크 모드 지원 확인
- [ ] 반응형 디자인 확인
- [ ] i18n 지원 확인 (현재 한국어 하드코딩)

### 작업 항목
- [ ] QuotePreview에 i18n 적용 (useTranslation)
- [ ] locales/en.json, ko.json에 번역 키 추가
- [ ] 다른 페이지에서 QuotePreview 사용 예시 추가

---

## 6. 훅 일관성

### 추가된 훅
```
web-ui/src/hooks/
├── useLayerToggle.ts    # 레이어 토글 공통 훅 (YOLOVisualization, OCRVisualization에서 사용 중)
└── useCanvasDrawing.ts  # 캔버스 드로잉 훅 (생성됨, 아직 미사용!)
```

### 검토 결과
- ✅ `useLayerToggle.ts`: YOLOVisualization, OCRVisualization에서 사용 중
- ⚠️ `useCanvasDrawing.ts`: **생성만 되고 아직 사용되지 않음**
  - 제공 기능: 이미지 로딩, 캔버스 렌더링, 스케일 계산
  - 적용 대상: YOLOVisualization, OCRVisualization, PIDOverlayViewer

### 작업 항목
- [ ] **useCanvasDrawing 훅 적용** (P1)
  - [ ] YOLOVisualization에 적용 (현재 자체 canvas 로직)
  - [ ] OCRVisualization에 적용
  - [ ] PIDOverlayViewer에 적용
- [ ] 중복 코드 제거 후 테스트

---

## 7. 테스트 일관성

### 추가된 테스트
```
gateway-api/tests/
├── e2e/
│   └── test_dsebearing_all_drawings.py
└── unit/
    └── test_dsebearing_services.py (59개 테스트)
```

### 검토 필요 사항
- [ ] 기존 테스트 스위트와 통합 여부
- [ ] CI/CD 파이프라인에서 실행 여부
- [ ] 테스트 커버리지 측정

### 작업 항목
- [ ] pytest.ini 또는 conftest.py 설정 확인
- [ ] GitHub Actions에서 테스트 실행 확인
- [ ] 테스트 리포트 생성 설정

---

## 8. 삭제된 아카이브 파일

### 삭제된 파일 (28개)
```
.todo/archive/ 하위 파일들 삭제됨:
- 00_SUMMARY.md ~ 14_NODE_PROFILES_INTEGRATION.md
- AUDIT_PHASE1_CORE.md ~ AUDIT_PHASE6_MISC.md
- DIRECTORY_AUDIT_PLAN.md
- E2E_TESTS_ORGANIZATION.md
- FILE_INVENTORY.md, FILE_INVENTORY_DETAILED.md
- TOAST_MIGRATION_ANALYSIS.md
- UX_IMPROVEMENT_TOAST_LOADING.md
- 2026-01-22_DSE_BEARING_TEMPLATE_FIXES.md
```

### 검토 필요 사항
- [ ] 삭제 의도적인지 확인 (정리 목적?)
- [ ] 필요한 정보가 다른 곳에 보존되었는지 확인

---

## 9. Locales 일관성

### 변경 사항
```json
// en.json, ko.json에 추가된 키:
- 신규 DSE Bearing 관련 번역 (확인 필요)
```

### 작업 항목
- [ ] 누락된 번역 키 확인
- [ ] 새 컴포넌트(QuotePreview)의 텍스트 i18n 적용

---

## 10. Gateway SVG Utils

### 추가된 파일
```
gateway-api/utils/svg_utils.py
```

### 검토 결과
- **역할**: 레퍼런스 구현 (각 API에서 복사하여 사용)
- **기능 비교**:

| 기능 | gateway/utils/svg_utils.py | models/*/services/svg_common.py |
|------|---------------------------|--------------------------------|
| escape_html | ✅ | ✅ |
| create_svg_header | ✅ (스타일 포함 옵션) | ✅ (기본) |
| create_svg_footer | ✅ | ✅ |
| create_bbox_element | ✅ | ❌ |
| create_line_element | ✅ | ❌ |
| create_text_element | ✅ | ❌ |
| create_label_element | ❌ | ✅ |
| DEFAULT_COLORS | ✅ (확장됨) | ✅ (기본) |

### 작업 항목
- [ ] **기능 동기화 검토** (P2)
  - gateway/utils/svg_utils.py가 더 완전함
  - models/*/svg_common.py에 필요한 기능 추가 여부 결정
- [ ] 또는 **중앙 집중화** 검토
  - 공통 패키지로 추출 가능성
  - Docker 이미지 간 공유 방법

---

## 우선순위 정리

### P0 (즉시)
1. nodeDefinitions.ts에서 DSE Bearing 노드 등록 확인
2. Dashboard에서 API 상태 표시 확인

### P1 (이번 주)
3. PIDOverlayViewer에 useLayerToggle 훅 적용
4. pid-composer-api svg_common.py 검토
5. QuotePreview i18n 적용

### P2 (다음 주)
6. 테스트 CI/CD 통합
7. useCanvasDrawing 사용처 확인
8. 삭제된 아카이브 파일 검토

---

## 참고: 변경된 파일 요약 (48개)

### 수정됨 (20개)
- `.claude/skills/README.md`
- `.todo/ACTIVE.md`, `BACKLOG.md`, `COMPLETED.md`
- `CLAUDE.md`
- `gateway-api/api_server.py`
- `gateway-api/api_specs/tabledetector.yaml`
- `gateway-api/blueprintflow/executors/__init__.py`
- `gateway-api/routers/__init__.py`
- `models/*/services/svg_generator.py` (4개)
- `models/*/tests/test_svg_generator.py` (2개)
- `web-ui/src/components/debug/*.tsx` (2개)
- `web-ui/src/config/apiRegistry.ts`
- `web-ui/src/config/nodeDefinitions.test.ts`
- `web-ui/src/config/nodes/analysisNodes.ts`
- `web-ui/src/lib/api.ts`
- `web-ui/src/locales/*.json` (2개)
- `web-ui/src/pages/blueprintflow/BlueprintFlowTemplates.tsx`

### 삭제됨 (28개)
- `.todo/archive/*.md` (전체)

### 추가됨 (30개+)
- `.claudeignore`
- `apply-company/dsebearing/` (전체)
- `gateway-api/api_specs/*.yaml` (DSE Bearing 6개)
- `gateway-api/blueprintflow/executors/*_executor.py` (5개)
- `gateway-api/routers/dsebearing_router.py`
- `gateway-api/services/*.py` (4개)
- `gateway-api/tests/e2e/`, `tests/unit/`
- `gateway-api/utils/svg_utils.py`
- `models/*/services/svg_common.py` (4개)
- `web-ui/src/components/dsebearing/`
- `web-ui/src/hooks/*.ts` (2개)

---

---

## 11. 구체적인 작업 계획

### Phase 1: 즉시 검증 (1일)

#### 1.1 DSE Bearing 노드 통합 확인
```bash
# BlueprintFlow에서 노드 표시 테스트
1. http://localhost:5173/blueprintflow/builder 접속
2. 노드 팔레트에서 DSE Bearing 노드 5개 확인:
   - Title Block Parser
   - Parts List Parser
   - Dimension Parser
   - BOM Matcher
   - Quote Generator
3. 각 노드 드래그하여 캔버스에 추가 가능 여부
4. 노드 연결 테스트 (Image → TitleBlock → PartsListParser 등)
```

#### 1.2 Dashboard API 상태 확인
```bash
# API 상태 표시 확인
1. http://localhost:5173/dashboard 접속
2. API Status Monitor에서 DSE Bearing 관련 API 표시 확인
3. 헬스체크 동작 확인
```

### Phase 2: 훅 마이그레이션 (2-3일)

#### 2.1 PIDOverlayViewer에 useLayerToggle 적용
```typescript
// 변경 전 (현재 코드):
const [visibility, setVisibility] = useState<LayerVisibility>({
  symbols: true,
  lines: true,
  texts: true,
  regions: true,
});

// 변경 후:
import { useLayerToggle, PID_LAYER_CONFIG } from '../../hooks/useLayerToggle';

const {
  visibility,
  toggleLayer,
  showLabels,
  toggleLabels,
  layerConfigs,
} = useLayerToggle({
  layers: PID_LAYER_CONFIG,
});
```

#### 2.2 useCanvasDrawing 훅 적용 (신규)
```typescript
// YOLOVisualization.tsx에 적용 예시:
import { useCanvasDrawing } from '../../hooks/useCanvasDrawing';

const {
  canvasRef,
  imageSize,
  scaleFactor,
  isLoading,
  redraw,
} = useCanvasDrawing({
  imageSource: imageFile,
  enabled: renderMode === 'canvas',
  onImageLoad: (img, ctx) => {
    // 기존 드로잉 로직
  },
});
```

### Phase 3: 일관성 정리 (3-5일)

#### 3.1 SVG Common 통합
```bash
# 옵션 A: 각 모델에 기능 추가
models/*/services/svg_common.py에 gateway/utils/svg_utils.py의
추가 함수들 복사

# 옵션 B: 공통 패키지화 (장기)
gateway-api/libs/svg_common/ 으로 추출
각 모델에서 import 경로 수정
```

#### 3.2 i18n 적용
```typescript
// QuotePreview.tsx에 적용:
import { useTranslation } from 'react-i18next';

// 하드코딩된 한국어 → 번역 키로 변경
'견적서 (Quotation)' → t('dsebearing.quote.title')
'발행일' → t('dsebearing.quote.issueDate')
'소계' → t('dsebearing.quote.subtotal')
```

### Phase 4: 테스트 정비 (2일)

#### 4.1 CI/CD 통합
```yaml
# .github/workflows/ci.yml에 추가:
- name: Run DSE Bearing Tests
  run: |
    cd gateway-api
    pytest tests/unit/test_dsebearing_services.py -v
```

#### 4.2 E2E 테스트 정비
```bash
# 테스트 구조 정리
gateway-api/tests/
├── conftest.py          # 공통 fixture
├── e2e/
│   ├── __init__.py
│   └── test_dsebearing_all_drawings.py
└── unit/
    ├── __init__.py
    └── test_dsebearing_services.py
```

---

## 체크리스트 요약

### 필수 (이번 커밋 전)
- [ ] DSE Bearing 노드 BlueprintFlow 표시 확인
- [ ] Dashboard API 상태 표시 확인
- [ ] 기본 E2E 테스트 통과 확인

### 권장 (이번 주)
- [ ] PIDOverlayViewer에 useLayerToggle 적용
- [ ] useCanvasDrawing 훅 적용 시작
- [ ] QuotePreview i18n 적용
- [ ] pid-composer-api svg_common.py 추가

### 선택 (다음 주 이후)
- [ ] SVG Utils 통합/표준화
- [ ] 삭제된 아카이브 파일 복구 검토
- [ ] 테스트 커버리지 측정 및 개선

---

*작성: Claude Code (Opus 4.5)*
