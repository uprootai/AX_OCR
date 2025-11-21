# YOLO API Parameters

**Complete parameter reference for nodeDefinitions.ts**

---

## 🎯 Current vs Required

| Parameter | Current | Required | Priority |
|-----------|---------|----------|----------|
| model_type | ❌ Missing | ✅ | HIGH |
| confidence | ✅ Has | ✅ | - |
| iou_threshold | ❌ Missing | ✅ | MEDIUM |
| imgsz | ❌ Missing | ✅ | MEDIUM |
| visualize | ❌ Missing | ✅ | LOW |
| task | ❌ Missing | ✅ | HIGH |

**Current Coverage**: 17% (1/6 parameters)

---

## 📋 Required Parameters

### 1. model_type (NEW - HIGH PRIORITY)
```typescript
{
  name: 'model_type',
  type: 'select',
  options: [
    'symbol-detector-v1',      // 용접/베어링/기어 (F1: 92%)
    'dimension-detector-v1',   // 치수 영역 (F1: 88%)
    'gdt-detector-v1',         // GD&T 심볼 (F1: 85%)
    'text-region-detector-v1', // 텍스트 영역 (F1: 90%)
    'yolo11n-general'          // 범용 (테스트용)
  ],
  default: 'symbol-detector-v1',
  description: '용도별 특화 모델 선택'
}
```

### 2. confidence (EXISTING)
```typescript
{
  name: 'confidence',
  type: 'number',
  default: 0.35,
  min: 0,
  max: 1,
  step: 0.05,
  description: '검출 신뢰도 임계값 (낮을수록 더 많이 검출)'
}
```

### 3. iou_threshold (NEW - MEDIUM PRIORITY)
```typescript
{
  name: 'iou_threshold',
  type: 'number',
  default: 0.45,
  min: 0,
  max: 1,
  step: 0.05,
  description: 'NMS IoU 임계값 (겹침 제거, 높을수록 엄격)'
}
```

### 4. imgsz (NEW - MEDIUM PRIORITY)
```typescript
{
  name: 'imgsz',
  type: 'select',
  options: ['640', '1280', '1920'],
  default: '1280',
  description: '입력 이미지 크기 (클수록 정확하지만 느림)'
}
```

### 5. visualize (NEW - LOW PRIORITY)
```typescript
{
  name: 'visualize',
  type: 'boolean',
  default: true,
  description: '검출 결과 시각화 이미지 생성'
}
```

### 6. task (NEW - HIGH PRIORITY)
```typescript
{
  name: 'task',
  type: 'select',
  options: ['detect', 'extract_dimensions'],
  default: 'detect',
  description: '검출 모드 (전체 검출 vs 치수만 추출)'
}
```

---

## 🚀 Implementation

**File**: `web-ui/src/config/nodeDefinitions.ts`
**Line**: ~55-72 (YOLO section)

Replace existing parameters array with above 6 parameters.

**Lines of Code**: +40 lines

---

**See Also**:
- [models.md](models.md) - 5 specialized models explained
- [examples.md](examples.md) - Usage examples
- [overview.md](overview.md) - API overview
