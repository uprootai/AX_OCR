# SkinModel API Parameters

**Complete parameter reference for nodeDefinitions.ts**

---

## 🎯 Current vs Required

| Parameter | Current | Required | Priority |
|-----------|---------|----------|----------|
| material | ❌ Missing | ✅ | HIGH |
| manufacturing_process | ❌ Missing | ✅ | HIGH |
| correlation_length | ❌ Missing | ✅ | MEDIUM |
| task | ❌ Missing | ✅ | HIGH |

**Current Coverage**: 0% (0/4 parameters) ❌ CRITICAL

---

## 📋 Required Parameters

### 1. material (NEW - HIGH PRIORITY)
```typescript
{
  name: 'material',
  type: 'select',
  options: ['aluminum', 'steel', 'stainless', 'titanium', 'plastic'],
  default: 'steel',
  description: '재질 선택 (공차 계산에 영향)'
}
```

### 2. manufacturing_process (NEW - HIGH PRIORITY)
```typescript
{
  name: 'manufacturing_process',
  type: 'select',
  options: ['machining', 'casting', '3d_printing', 'welding', 'sheet_metal'],
  default: 'machining',
  description: '제조 공정 (공차 허용 범위 결정)'
}
```

### 3. correlation_length (NEW - MEDIUM PRIORITY)
```typescript
{
  name: 'correlation_length',
  type: 'number',
  default: 1.0,
  min: 0.1,
  max: 10.0,
  step: 0.1,
  description: 'Random Field 상관 길이 (불확실성 모델링, 기본값 1.0)'
}
```

### 4. task (NEW - HIGH PRIORITY)
```typescript
{
  name: 'task',
  type: 'select',
  options: ['tolerance', 'validate', 'manufacturability'],
  default: 'tolerance',
  description: '분석 작업 (공차 예측 vs GD&T 검증 vs 제조성 분석)'
}
```

---

## 🚀 Implementation

**File**: `web-ui/src/config/nodeDefinitions.ts`
**Line**: ~162 (SkinModel section)

Replace `parameters: []` with above 4 parameters.

**Lines of Code**: +40 lines

---

**See Also**:
- [materials.md](materials.md) - Material properties
- [overview.md](overview.md) - API overview
