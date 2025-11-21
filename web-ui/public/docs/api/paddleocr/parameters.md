# PaddleOCR API Parameters

**Complete parameter reference for nodeDefinitions.ts**

---

## 🎯 Current vs Required

| Parameter | Current | Required | Priority |
|-----------|---------|----------|----------|
| lang | ✅ Has | ✅ | - |
| det_db_thresh | ❌ Missing | ✅ | HIGH |
| det_db_box_thresh | ❌ Missing | ✅ | MEDIUM |
| use_angle_cls | ❌ Missing | ✅ | MEDIUM |
| min_confidence | ❌ Missing | ✅ | LOW |

**Current Coverage**: 20% (1/5 parameters)

---

## 📋 Required Parameters

### 1. lang (EXISTING)
```typescript
{
  name: 'lang',
  type: 'select',
  options: ['en', 'ch', 'korean', 'japan', 'french'],
  default: 'en',
  description: '인식 언어'
}
```

### 2. det_db_thresh (NEW - HIGH PRIORITY)
```typescript
{
  name: 'det_db_thresh',
  type: 'number',
  default: 0.3,
  min: 0,
  max: 1,
  step: 0.05,
  description: '텍스트 검출 임계값 (낮을수록 더 많이 검출)'
}
```

### 3. det_db_box_thresh (NEW - MEDIUM PRIORITY)
```typescript
{
  name: 'det_db_box_thresh',
  type: 'number',
  default: 0.5,
  min: 0,
  max: 1,
  step: 0.05,
  description: '박스 임계값 (높을수록 정확한 박스만)'
}
```

### 4. use_angle_cls (NEW - MEDIUM PRIORITY)
```typescript
{
  name: 'use_angle_cls',
  type: 'boolean',
  default: true,
  description: '회전된 텍스트 감지 여부 (90도, 180도, 270도)'
}
```

### 5. min_confidence (NEW - LOW PRIORITY)
```typescript
{
  name: 'min_confidence',
  type: 'number',
  default: 0.5,
  min: 0,
  max: 1,
  step: 0.05,
  description: '최소 신뢰도 (이 값 이하는 필터링)'
}
```

---

## 🚀 Implementation

**File**: `web-ui/src/config/nodeDefinitions.ts`
**Line**: ~190-198 (PaddleOCR section)

Replace existing lang parameter with above 5 parameters.

**Lines of Code**: +40 lines

---

**See Also**:
- [languages.md](languages.md) - Supported languages
- [overview.md](overview.md) - API overview
