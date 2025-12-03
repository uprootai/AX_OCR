# AX POC - 기술 스킬 가이드

> 프로젝트에서 자주 사용되는 패턴, 코드 스니펫, 레시피 모음

---

## 1. 노드 정의 패턴

### nodeDefinitions.ts 구조

```typescript
export const nodeDefinitions: Record<string, NodeDefinition> = {
  yolo: {
    type: 'yolo',
    label: 'YOLO Detection',
    category: 'detection',  // 9개 카테고리 중 하나
    color: '#10b981',
    icon: 'Target',  // lucide-react 아이콘명
    description: '설명',
    inputs: [{ name: 'image', type: 'Image', description: '설명' }],
    outputs: [{ name: 'detections', type: 'DetectionResult[]', description: '설명' }],
    parameters: [
      {
        name: 'confidence',
        type: 'number',  // number | string | boolean | select
        default: 0.5,
        min: 0,
        max: 1,
        step: 0.05,
        description: '설명',
      },
      {
        name: 'model_type',
        type: 'select',
        default: 'symbol-detector-v1',
        options: ['symbol-detector-v1', 'dimension-detector-v1'],
        description: '설명',
      },
    ],
    examples: ['예시 1', '예시 2'],
    usageTips: ['팁 1', '팁 2'],
    recommendedInputs: [
      { from: 'imageinput', field: 'image', reason: '이유' },
    ],
  },
};
```

---

## 2. Executor 패턴

### 기본 Executor 구조 (Python)

```python
"""
{API명} Node Executor
"""
from typing import Dict, Any, Optional
from ..executors.base_executor import BaseNodeExecutor
from ..executors.executor_registry import ExecutorRegistry
from ..executors.image_utils import prepare_image_for_api

class MyExecutor(BaseNodeExecutor):
    """실행기 설명"""

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        # 1. 이미지 준비 (이미지 기반 API인 경우)
        file_bytes = prepare_image_for_api(inputs, context)

        # 2. 파라미터 추출
        param1 = self.parameters.get("param1", default_value)

        # 3. API 호출
        result = await call_api(file_bytes, param1)

        # 4. 결과 반환
        return {
            "output_field": result.get("field", []),
            "processing_time": result.get("processing_time", 0),
        }

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        # 파라미터 검증 로직
        return True, None

# 실행기 등록 (필수!)
ExecutorRegistry.register("my_node_type", MyExecutor)
```

---

## 3. 서비스 레이어 패턴

### API 호출 서비스 (Python)

```python
"""
{API명} Service
"""
import httpx
from typing import Dict, Any

API_URL = "http://api-service:5000"

async def call_my_api(
    file_bytes: bytes,
    param1: str = "default",
    param2: float = 0.5,
) -> Dict[str, Any]:
    """API 호출"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        files = {"file": ("image.jpg", file_bytes, "image/jpeg")}
        data = {"param1": param1, "param2": param2}

        response = await client.post(f"{API_URL}/api/v1/process", files=files, data=data)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API 호출 실패: {response.status_code}")
```

---

## 4. Zustand 스토어 패턴

### 스토어 정의 (TypeScript)

```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface MyState {
  items: Item[];
  addItem: (item: Item) => void;
  removeItem: (id: string) => void;
}

export const useMyStore = create<MyState>()(
  persist(
    (set, get) => ({
      items: [],

      addItem: (item) => set((state) => ({
        items: [...state.items, item],
      })),

      removeItem: (id) => set((state) => ({
        items: state.items.filter((i) => i.id !== id),
      })),
    }),
    { name: 'my-storage' }
  )
);
```

---

## 5. 테스트 패턴

### Vitest 테스트 (TypeScript)

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock 설정
globalThis.fetch = vi.fn(() =>
  Promise.resolve({ ok: true, json: () => Promise.resolve({}) } as Response)
);

describe('TestSuite', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should do something', async () => {
    // Arrange
    const input = {};

    // Act
    const result = await myFunction(input);

    // Assert
    expect(result).toBeDefined();
  });
});
```

### pytest 테스트 (Python)

```python
import pytest

class TestMyFeature:
    def test_basic_functionality(self):
        result = my_function()
        assert result is not None

    @pytest.mark.asyncio
    async def test_async_function(self):
        result = await async_function()
        assert result["status"] == "success"
```

---

## 6. i18n 번역 패턴

### 컴포넌트에서 사용

```typescript
import { useTranslation } from 'react-i18next';

export default function MyComponent() {
  const { t } = useTranslation();

  return (
    <div>
      <h1>{t('page.title')}</h1>
      <p>{t('page.description', { count: 5 })}</p>
    </div>
  );
}
```

### 번역 파일 구조 (ko.json)

```json
{
  "page": {
    "title": "페이지 제목",
    "description": "{{count}}개의 항목이 있습니다"
  },
  "blueprintflow": {
    "nodes": {
      "yolo": {
        "label": "YOLO 검출",
        "description": "객체 검출"
      }
    }
  }
}
```

---

## 7. ESLint 설정 패턴

### any 타입 경고 비활성화 (특정 파일)

```typescript
/* eslint-disable @typescript-eslint/no-explicit-any */
// 파일 전체에 적용

// 또는 특정 라인만
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const data: any = response.data;
```

### eslint.config.js 규칙 설정

```javascript
rules: {
  '@typescript-eslint/no-explicit-any': 'warn',  // error → warn
  '@typescript-eslint/no-unused-vars': ['warn', {
    argsIgnorePattern: '^_',
    varsIgnorePattern: '^_'
  }],
}
```

---

## 8. Vite 코드 분할 패턴

### vite.config.ts

```typescript
build: {
  rollupOptions: {
    output: {
      manualChunks: {
        'vendor-react': ['react', 'react-dom', 'react-router-dom'],
        'vendor-charts': ['recharts', 'mermaid'],
        'vendor-flow': ['reactflow'],
      },
    },
  },
  chunkSizeWarningLimit: 600,
},
```

---

## 9. API 응답 타입 패턴

### 공통 응답 타입

```typescript
interface APIResponse<T> {
  status: 'success' | 'error';
  data: T;
  processing_time: number;
  error?: string;
}

interface DetectionResult {
  class_name: string;
  confidence: number;
  bbox: { x: number; y: number; width: number; height: number };
}

interface OCRResult {
  text: string;
  confidence: number;
  position: { x: number; y: number };
}
```

---

## 10. 카테고리 매핑

### 유효한 카테고리

```typescript
const VALID_CATEGORIES = [
  'input',        // 입력 노드
  'detection',    // 객체 검출
  'ocr',          // 텍스트 인식
  'segmentation', // 영역 분할
  'preprocessing',// 전처리
  'analysis',     // 분석
  'knowledge',    // 지식 엔진
  'ai',           // AI/ML
  'control',      // 제어 흐름
] as const;

type NodeCategory = typeof VALID_CATEGORIES[number];
```

### 카테고리별 색상

```typescript
const CATEGORY_COLORS: Record<NodeCategory, string> = {
  input: '#f97316',        // orange
  detection: '#10b981',    // green
  ocr: '#3b82f6',          // blue
  segmentation: '#8b5cf6', // purple
  preprocessing: '#dc2626',// red
  analysis: '#f59e0b',     // amber
  knowledge: '#9333ea',    // violet
  ai: '#ec4899',           // pink
  control: '#ef4444',      // red
};
```

---

## 11. GitHub Actions 패턴

### CI 워크플로우

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm run lint
      - run: npm run build
      - run: npm run test:run
```

---

## 12. 디버깅 패턴

### 프론트엔드 로깅

```typescript
// 개발 환경에서만 로깅
if (import.meta.env.DEV) {
  console.log('[DEBUG]', data);
}
```

### 백엔드 로깅

```python
import logging
logger = logging.getLogger(__name__)

logger.info(f"Processing: {param}")
logger.error(f"Error: {e}")
```

---

**Last Updated**: 2025-12-03
