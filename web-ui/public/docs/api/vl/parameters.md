# VL API Parameters

**Complete parameter reference for nodeDefinitions.ts**

---

## 🎯 Current vs Required

| Parameter | Current | Required | Priority |
|-----------|---------|----------|----------|
| model | ❌ Missing | ✅ | HIGH |
| task | ❌ Missing | ✅ | HIGH |
| query_fields | ❌ Missing | ✅ | MEDIUM |
| temperature | ❌ Missing | ✅ | LOW |

**Current Coverage**: 0% (0/4 parameters) ❌ CRITICAL

---

## 📋 Required Parameters

### 1. model (NEW - HIGH PRIORITY)
```typescript
{
  name: 'model',
  type: 'select',
  options: [
    'claude-3-5-sonnet-20241022',
    'gpt-4o',
    'gpt-4-turbo-2024-04-09',
    'gemini-1.5-pro'
  ],
  default: 'claude-3-5-sonnet-20241022',
  description: 'Vision Language 모델 선택 (Claude: 정확, GPT-4o: 빠름)'
}
```

### 2. task (NEW - HIGH PRIORITY)
```typescript
{
  name: 'task',
  type: 'select',
  options: [
    'extract_info_block',
    'extract_dimensions',
    'infer_manufacturing_process',
    'generate_qc_checklist'
  ],
  default: 'extract_info_block',
  description: 'VL 작업 종류 (Info Block vs 치수 vs 제조공정 vs QC)'
}
```

### 3. query_fields (NEW - MEDIUM PRIORITY)
```typescript
{
  name: 'query_fields',
  type: 'string',
  default: '["name", "part number", "material", "scale", "weight"]',
  description: '추출할 정보 필드 (Info Block 작업 시, JSON 배열)'
}
```

### 4. temperature (NEW - LOW PRIORITY)
```typescript
{
  name: 'temperature',
  type: 'number',
  default: 0.0,
  min: 0,
  max: 1,
  step: 0.1,
  description: '생성 다양성 (0=정확/일관성, 1=창의적/다양)'
}
```

---

## 🚀 Implementation

**File**: `web-ui/src/config/nodeDefinitions.ts`
**Line**: ~225 (VL section)

Replace `parameters: []` with above 4 parameters.

**Lines of Code**: +40 lines

---

**See Also**:
- [models.md](models.md) - Model comparison (Claude vs GPT-4o vs Gemini)
- [tasks.md](tasks.md) - 4 tasks explained
- [overview.md](overview.md) - API overview
