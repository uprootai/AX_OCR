# Feature Implication 시스템 동기화 작업

> 생성일: 2026-01-05
> 관련 파일: featureDefinitions.ts, sectionConfig.ts

## 개요

Feature 간 의존 관계를 정의하는 새로운 시스템이 추가되었습니다:
- `implies`: 이 feature 활성화 시 자동으로 활성화되는 features
- `impliedBy`: 이 feature를 활성화하는 트리거 features
- `isPrimary`: 사용자가 직접 선택 가능한 feature (true만 UI에서 선택)

---

## 1. 변경된 파일들

### 1.1 `web-ui/src/config/features/featureDefinitions.ts`

**추가된 인터페이스 속성:**
```typescript
export interface FeatureDefinition {
  // ... 기존 속성들

  // === Feature 관계 정의 (자동 활성화) ===
  implies?: string[];      // 자동 활성화 대상
  impliedBy?: string[];    // 트리거 features
  isPrimary?: boolean;     // UI에서 선택 가능 여부
}
```

**적용된 관계:**
```typescript
symbol_detection: {
  isPrimary: true,
  implies: ['symbol_verification', 'gt_comparison'],
}
symbol_verification: {
  impliedBy: ['symbol_detection'],
}
dimension_ocr: {
  isPrimary: true,
  implies: ['dimension_verification'],
}
dimension_verification: {
  impliedBy: ['dimension_ocr'],
}
gt_comparison: {
  impliedBy: ['symbol_detection'],
  implementationStatus: 'implemented',  // partial → implemented 변경
}
```

### 1.2 `blueprint-ai-bom/frontend/src/config/features/featureDefinitions.ts`

**동기화 필요:** web-ui와 동일한 변경 적용됨

**TODO:**
- [x] 동일한 implies/impliedBy/isPrimary 속성 추가 완료
- [ ] **검증**: 두 파일의 내용이 정확히 일치하는지 diff 확인

### 1.3 `blueprint-ai-bom/frontend/src/pages/workflow/config/sectionConfig.ts`

**추가된 상수:**
```typescript
export const FEATURE_IMPLICATIONS: Record<string, string[]> = {
  symbol_detection: ['symbol_verification', 'gt_comparison'],
  dimension_ocr: ['dimension_verification'],
  pid_connectivity: ['techcross_valve_signal', 'techcross_equipment', 'techcross_checklist', 'techcross_deviation'],
  industry_equipment_detection: ['equipment_list_export'],
};

export const FEATURE_IMPLIED_BY: Record<string, string[]> = {
  symbol_verification: ['symbol_detection'],
  gt_comparison: ['symbol_detection'],
  dimension_verification: ['dimension_ocr'],
  techcross_valve_signal: ['pid_connectivity'],
  techcross_equipment: ['pid_connectivity'],
  techcross_checklist: ['pid_connectivity'],
  techcross_deviation: ['pid_connectivity'],
  equipment_list_export: ['industry_equipment_detection'],
};
```

**변경된 함수:**
```typescript
const hasFeature = (key: string): boolean => {
  // 1. 직접 활성화된 경우
  if (normalized.includes(key) || features.includes(key)) {
    return true;
  }

  // 2. impliedBy로 자동 활성화되는 경우
  const impliers = FEATURE_IMPLIED_BY[key];
  if (impliers) {
    return impliers.some(implier =>
      normalized.includes(implier) || features.includes(implier)
    );
  }

  return false;
};
```

### 1.4 `web-ui/src/config/nodes/inputNodes.ts`

**기본값 변경:**
```diff
- default: ['dimension_ocr', 'dimension_verification', 'gt_comparison'],
+ // Primary features만 선택하면 impliedBy로 하위 기능 자동 활성화
+ // symbol_detection → symbol_verification, gt_comparison
+ // dimension_ocr → dimension_verification
+ default: ['symbol_detection', 'dimension_ocr'],
```

---

## 2. 동기화 필요한 작업들

### 2.1 featureDefinitions.ts 동기화

**확인 필요:**
- [ ] `web-ui/src/config/features/featureDefinitions.ts`
- [ ] `blueprint-ai-bom/frontend/src/config/features/featureDefinitions.ts`

**검증 명령:**
```bash
diff -u web-ui/src/config/features/featureDefinitions.ts \
     blueprint-ai-bom/frontend/src/config/features/featureDefinitions.ts
```

### 2.2 아직 isPrimary가 설정되지 않은 features

**설정 필요 (web-ui 기준):**

| Feature | 현재 | 권장 |
|---------|------|------|
| `gdt_recognition` | isPrimary: true | 유지 |
| `line_detection` | isPrimary: true | 유지 |
| `pid_connectivity` | isPrimary: true | 유지 |
| `text_layer_extraction` | 미설정 | `isPrimary: true` 추가 필요 |
| `vlm_auto_classification` | 미설정 | `isPrimary: true` 추가 필요 |
| `bom_generation` | 미설정 | `isPrimary: true` 추가 필요 |
| `active_learning` | 미설정 | `isPrimary: true` 추가 필요 |
| `export_yolo_format` | 미설정 | `impliedBy: ['active_learning']` 추가 필요 |

### 2.3 sectionConfig.ts와 featureDefinitions.ts 일치 확인

**FEATURE_IMPLICATIONS vs implies 일치:**
```
sectionConfig.ts                     featureDefinitions.ts
─────────────────────────────────    ──────────────────────────────
symbol_detection: [                  symbol_detection.implies: [
  'symbol_verification',               'symbol_verification',
  'gt_comparison'                      'gt_comparison'
]                                    ]
```

**TODO:**
- [ ] FEATURE_IMPLICATIONS와 featureDefinitions.implies가 완전히 일치하는지 검증
- [ ] 불일치 시 featureDefinitions.ts를 SSOT로 하여 sectionConfig.ts 자동 생성 고려

---

## 3. 추가 구현 필요 항목

### 3.1 web-ui에 Feature Implication 로직 적용

**현재:** blueprint-ai-bom에만 `hasFeature()` 함수에 impliedBy 로직 구현

**필요:** web-ui의 BlueprintFlow에서도 feature 활성화 시 implies 자동 처리

**적용 위치:**
- [ ] `web-ui/src/store/workflowStore.ts` - feature 선택 시 implies 자동 추가
- [ ] `web-ui/src/hooks/useNodeDefinitions.ts` - 노드 파라미터 기본값 계산 시

### 3.2 테스트 추가

- [ ] `web-ui/src/config/features/featureDefinitions.test.ts` - implication 관계 테스트
- [ ] `blueprint-ai-bom/frontend/src/config/features/featureDefinitions.test.ts` - 동일

**테스트 케이스:**
```typescript
describe('Feature Implication', () => {
  it('symbol_detection should imply symbol_verification', () => {
    const def = FEATURE_DEFINITIONS['symbol_detection'];
    expect(def.implies).toContain('symbol_verification');
  });

  it('symbol_verification should be impliedBy symbol_detection', () => {
    const def = FEATURE_DEFINITIONS['symbol_verification'];
    expect(def.impliedBy).toContain('symbol_detection');
  });

  it('implies and impliedBy should be consistent', () => {
    // 모든 implies 관계가 impliedBy에도 반영되어 있는지 검증
  });
});
```

---

## 4. UI 변경 검토

### 4.1 ActiveFeaturesSection 배지 표시

**현재:** 모든 활성화된 feature 배지 표시
**제안:** isPrimary=true인 것만 강조 표시, 나머지는 작은 글씨 또는 숨김

### 4.2 Feature 선택 UI

**현재:** 체크박스로 모든 feature 선택 가능
**제안:** isPrimary=true만 체크박스, 나머지는 자동 활성화 표시

---

## 5. 우선순위

| 순위 | 작업 | 영향도 |
|------|------|--------|
| P0 | featureDefinitions.ts 두 파일 동기화 검증 | 일관성 |
| P0 | 누락된 isPrimary 설정 추가 | 기능 완성 |
| P1 | web-ui에 implication 로직 구현 | 기능 일관성 |
| P1 | 테스트 추가 | 안정성 |
| P2 | UI 개선 (Primary 강조) | UX |
