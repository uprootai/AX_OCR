# EDGNet API Parameters

**Complete parameter reference for nodeDefinitions.ts**

---

## 🎯 Current vs Required

| Parameter | Current | Required | Priority |
|-----------|---------|----------|----------|
| model | ❌ Missing | ✅ | HIGH |
| num_classes | ❌ Missing | ✅ | HIGH |
| visualize | ❌ Missing | ✅ | LOW |
| save_graph | ❌ Missing | ✅ | LOW |
| vectorize | ❌ Missing | ✅ | MEDIUM |

**Current Coverage**: 0% (threshold parameter exists but doesn't match API)

---

## 📋 Required Parameters

### 1. model (NEW - HIGH PRIORITY)
```typescript
{
  name: 'model',
  type: 'select',
  options: ['graphsage', 'unet'],
  default: 'graphsage',
  description: '세그멘테이션 모델 (GraphSAGE: 빠름, UNet: 정확)'
}
```

### 2. num_classes (NEW - HIGH PRIORITY)
```typescript
{
  name: 'num_classes',
  type: 'select',
  options: ['2', '3'],
  default: '3',
  description: '분류 클래스 수 (2: Text/Non-text, 3: Contour/Text/Dimension)'
}
```

### 3. visualize (NEW - LOW PRIORITY)
```typescript
{
  name: 'visualize',
  type: 'boolean',
  default: true,
  description: '세그멘테이션 결과 시각화 생성'
}
```

### 4. save_graph (NEW - LOW PRIORITY)
```typescript
{
  name: 'save_graph',
  type: 'boolean',
  default: false,
  description: '그래프 구조 JSON 저장 (디버깅용)'
}
```

### 5. vectorize (NEW - MEDIUM PRIORITY)
```typescript
{
  name: 'vectorize',
  type: 'boolean',
  default: false,
  description: '도면 벡터화 (DXF 출력용, Bezier 곡선)'
}
```

---

## 🚀 Implementation

**File**: `web-ui/src/config/nodeDefinitions.ts`
**Line**: ~126-136 (EDGNet section)

Replace existing threshold parameter with above 5 parameters.

**Lines of Code**: +40 lines

---

**See Also**:
- [graphsage_vs_unet.md](graphsage_vs_unet.md) - Model comparison
- [overview.md](overview.md) - API overview
