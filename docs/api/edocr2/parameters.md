# eDOCr2 API Parameters

**Complete parameter reference for nodeDefinitions.ts**

---

## 🎯 Current vs Required

| Parameter | Current | Required | Priority |
|-----------|---------|----------|----------|
| version | ❌ Missing | ✅ | HIGH |
| extract_dimensions | ❌ Missing | ✅ | HIGH |
| extract_gdt | ❌ Missing | ✅ | HIGH |
| extract_text | ❌ Missing | ✅ | MEDIUM |
| use_vl_model | ❌ Missing | ✅ | LOW |
| visualize | ❌ Missing | ✅ | LOW |
| use_gpu_preprocessing | ❌ Missing | ✅ | MEDIUM |

**Current Coverage**: 0% (0/7 parameters) ❌ CRITICAL

---

## 📋 Required Parameters

### 1. version (NEW - HIGH PRIORITY)
```typescript
{
  name: 'version',
  type: 'select',
  options: ['v1', 'v2', 'ensemble'],
  default: 'ensemble',
  description: 'eDOCr 버전 (v1: 5001, v2: 5002, ensemble: 가중 평균 0.6/0.4)'
}
```

### 2. extract_dimensions (NEW - HIGH PRIORITY)
```typescript
{
  name: 'extract_dimensions',
  type: 'boolean',
  default: true,
  description: '치수 정보 추출 (φ476, 10±0.5, R20 등)'
}
```

### 3. extract_gdt (NEW - HIGH PRIORITY)
```typescript
{
  name: 'extract_gdt',
  type: 'boolean',
  default: true,
  description: 'GD&T 정보 추출 (평행도, 직각도, 위치도 등)'
}
```

### 4. extract_text (NEW - MEDIUM PRIORITY)
```typescript
{
  name: 'extract_text',
  type: 'boolean',
  default: true,
  description: '텍스트 정보 추출 (도면 번호, 재질, 주석 등)'
}
```

### 5. use_vl_model (NEW - LOW PRIORITY)
```typescript
{
  name: 'use_vl_model',
  type: 'boolean',
  default: false,
  description: 'Vision Language 모델 보조 (느리지만 정확, +2초)'
}
```

### 6. visualize (NEW - LOW PRIORITY)
```typescript
{
  name: 'visualize',
  type: 'boolean',
  default: false,
  description: 'OCR 결과 시각화 이미지 생성'
}
```

### 7. use_gpu_preprocessing (NEW - MEDIUM PRIORITY)
```typescript
{
  name: 'use_gpu_preprocessing',
  type: 'boolean',
  default: false,
  description: 'GPU 전처리 활성화 (CLAHE, denoising, +15% 정확도)'
}
```

---

## 🚀 Implementation

**File**: `web-ui/src/config/nodeDefinitions.ts`
**Line**: ~98-104 (eDOCr2 section)

Replace `parameters: []` with above 7 parameters.

**Lines of Code**: +60 lines

---

**See Also**:
- [v1_vs_v2.md](v1_vs_v2.md) - Version comparison
- [ensemble.md](ensemble.md) - Ensemble strategy
- [overview.md](overview.md) - API overview
