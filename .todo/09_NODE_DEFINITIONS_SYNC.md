# 노드 정의 동기화 작업

> 생성일: 2026-01-05
> 관련 파일: nodeDefinitions.ts, inputNodes.ts, node-palette/constants.ts

## 개요

BlueprintFlow 노드 정의에 변경이 있었습니다:
1. gtcomparison 노드가 node-palette에 추가됨
2. 노드 카운트가 28 → 29로 변경 (pidcomposer 추가)
3. inputNodes의 features 기본값 변경

---

## 1. 변경된 파일들

### 1.1 `web-ui/src/components/blueprintflow/node-palette/constants.ts`

**추가된 노드:**
```typescript
{
  type: 'gtcomparison',
  label: 'GT Comparison',
  description: 'Ground Truth comparison',
  icon: '📊',
  color: '#f97316',
  category: 'analysis',
},
```

**확인 필요:**
- [ ] gtcomparison이 nodeDefinitions.ts에도 정의되어 있는지
- [ ] 아이콘/색상이 featureDefinitions.ts와 일치하는지

### 1.2 `web-ui/src/config/nodeDefinitions.test.ts`

**변경:**
```diff
- it('should have exactly 28 node types', () => {
+ it('should have exactly 29 node types', () => {
-   expect(Object.keys(nodeDefinitions).length).toBe(28);
+   expect(Object.keys(nodeDefinitions).length).toBe(29);

- expect(categoryCounts['analysis']).toBe(8);
+ expect(categoryCounts['analysis']).toBe(9);  // pidcomposer 추가
```

**TODO:**
- [ ] pidcomposer가 nodeDefinitions에 실제로 있는지 확인
- [ ] 테스트 실행하여 통과 확인

### 1.3 `web-ui/src/config/nodes/inputNodes.ts`

**변경:**
```diff
- default: ['dimension_ocr', 'dimension_verification', 'gt_comparison'],
+ default: ['symbol_detection', 'dimension_ocr'],
```

**이유:** Primary features만 선택하면 implies로 하위 기능 자동 활성화

---

## 2. 일관성 검증 필요

### 2.1 노드 타입 vs Feature 매핑

| 노드 타입 | 관련 Feature | 일치 여부 |
|-----------|--------------|-----------|
| `gtcomparison` | `gt_comparison` | 확인 필요 |
| `pdfexport` | `pdf_export` | 확인 필요 |
| `excelexport` | `excel_export` | 확인 필요 |
| `pidfeatures` | `pid_connectivity` | 확인 필요 |
| `verificationqueue` | `symbol_verification` | 확인 필요 |
| `pidcomposer` | `pid_composer` | 확인 필요 |

### 2.2 node-palette vs nodeDefinitions 일치

**검증 스크립트:**
```bash
# node-palette에 있는 타입들이 nodeDefinitions에도 있는지
grep -o "type: '[^']*'" web-ui/src/components/blueprintflow/node-palette/constants.ts | \
  sed "s/type: '\\([^']*\\)'/\\1/" | sort | uniq
```

**TODO:**
- [ ] 모든 node-palette 타입이 nodeDefinitions에 있는지 검증
- [ ] 누락된 노드 정의 추가

### 2.3 카테고리별 노드 카운트 정확성

| 카테고리 | 예상 | 실제 | 노드들 |
|----------|------|------|--------|
| input | 2 | ? | imageinput, textinput |
| detection | 1 | ? | yolo |
| ocr | 8 | ? | edocr2, paddleocr, tesseract, trocr, ocr_ensemble, suryaocr, doctr, easyocr |
| segmentation | 2 | ? | edgnet, linedetector |
| preprocessing | 1 | ? | esrgan |
| analysis | 9 | ? | skinmodel, pidanalyzer, designchecker, pidcomposer, gtcomparison, pdfexport, excelexport, pidfeatures, verificationqueue |
| knowledge | 1 | ? | knowledge |
| ai | 1 | ? | vl |
| control | 3 | ? | if, loop, merge |
| **합계** | **29** | ? | |

**TODO:**
- [ ] 실제 nodeDefinitions에서 카테고리별 카운트 검증
- [ ] 테스트 업데이트

---

## 3. 신규 노드 정의 확인

### 3.1 pidcomposer 노드

**위치:** `web-ui/src/config/nodes/analysisNodes.ts`

**확인 필요:**
- [ ] pidcomposer 노드 정의 존재 여부
- [ ] 파라미터 정의 완성도
- [ ] API 연동 정보 (base_url, endpoint)

### 3.2 gtcomparison 노드

**node-palette에는 추가됨, nodeDefinitions에도 있는지:**
```typescript
// 예상 정의
gtcomparison: {
  type: 'gtcomparison',
  label: 'GT Comparison',
  description: 'Ground Truth 비교',
  category: 'analysis',
  color: '#f97316',
  icon: Chart,
  parameters: [
    { name: 'threshold', type: 'number', default: 0.5 },
    { name: 'metric', type: 'select', options: ['iou', 'precision', 'recall'] },
  ],
}
```

**TODO:**
- [ ] analysisNodes.ts에서 gtcomparison 정의 확인
- [ ] Blueprint AI BOM의 GT Comparison 기능과 연동 확인

---

## 4. API 스펙 동기화

### 4.1 pidcomposer API

**스펙 파일:** `gateway-api/api_specs/pid-composer.yaml`

**확인:**
- [ ] 스펙 파일이 최신 상태인지
- [ ] nodeDefinitions의 파라미터와 스펙이 일치하는지

### 4.2 design-checker 스펙 업데이트

**추가 필요:**
```yaml
# gateway-api/api_specs/design-checker.yaml에 추가
endpoints:
  - path: /api/v1/pipeline/detect
    method: POST
    description: YOLO 심볼 검출
  - path: /api/v1/pipeline/ocr
    method: POST
    description: OCR 텍스트 추출
  - path: /api/v1/pipeline/validate
    method: POST
    description: 통합 검증
```

---

## 5. 테스트 업데이트

### 5.1 nodeDefinitions.test.ts

**현재 상태:**
- 노드 카운트: 29 (수정됨)
- 카테고리 카운트: analysis=9 (수정됨)

**추가 필요:**
- [ ] pidcomposer 노드 테스트
- [ ] gtcomparison 노드 테스트
- [ ] 신규 노드들의 파라미터 테스트

### 5.2 E2E 테스트

- [ ] pidcomposer 노드 사용 시나리오
- [ ] gtcomparison 노드 사용 시나리오

---

## 6. 우선순위

| 순위 | 작업 | 영향도 |
|------|------|--------|
| P0 | nodeDefinitions 누락 노드 확인 | 기능 |
| P0 | 테스트 실행하여 통과 확인 | 안정성 |
| P1 | node-palette vs nodeDefinitions 동기화 | 일관성 |
| P1 | API 스펙 업데이트 | 문서화 |
| P2 | E2E 테스트 추가 | 검증 |
