# 테스트 커버리지 확대 계획

> 현재 테스트 현황 및 확장 계획
> 목표: 핵심 기능 80%+ 커버리지

---

## 현재 테스트 현황

### 전체 통계
| 영역 | 테스트 수 | 상태 |
|------|----------|------|
| Gateway API | 364개 | ✅ 통과 |
| Web-UI | 141개 | ✅ 통과 |
| **총계** | **505개** | **✅ 통과** |

### 영역별 상세

#### Gateway API (364개)
```
tests/
├── test_executor_registry.py     # Executor 레지스트리
├── test_yolo_executor.py         # YOLO Executor
├── test_ocr_executor.py          # OCR Executor
├── test_health_router.py         # 헬스체크
├── test_spec_router.py           # API 스펙
├── test_admin_router.py          # 관리자 API
├── test_docker_router.py         # Docker 관리
├── test_results_router.py        # 결과 조회
└── test_gpu_config_router.py     # GPU 설정
```

#### Web-UI (141개)
```
src/
├── config/nodeDefinitions.test.ts  # 노드 정의 검증
├── store/apiConfigStore.test.ts    # API 설정 스토어
├── store/workflowStore.test.ts     # 워크플로우 스토어
└── components/**/*.test.tsx        # 컴포넌트 테스트
```

---

## 신규 생성 API 테스트 현황

### PID Composer API
**파일**: `models/pid-composer-api/tests/test_composer.py`
**상태**: ✅ 생성됨

```python
# 테스트 클래스 (10개)
class TestHealth          # 헬스체크
class TestInfo            # 서비스 정보
class TestComposeSVG      # SVG 생성
class TestCompose         # 이미지 합성
class TestComposeLayers   # 레이어 합성
class TestPreview         # 미리보기
class TestLayerValidation # 레이어 검증
class TestStyleOptions    # 스타일 옵션
class TestEdgeCases       # 엣지 케이스
class TestPerformance     # 성능 테스트
```

---

## 테스트 확대 대상

### 우선순위 P0: 핵심 기능 테스트

#### 1. Blueprint AI BOM 테스트 확장
**현재**: 59개
**목표**: 80개+

```python
# 추가 필요 테스트
tests/
├── test_valve_signal.py      # Valve Signal 검출
├── test_equipment.py         # Equipment 검출
├── test_checklist.py         # Checklist 검증
├── test_verification_queue.py # 검증 큐
└── test_export.py            # Excel 내보내기
```

#### 2. YOLO API 테스트 확장
**현재**: 기본 테스트만
**목표**: 모델별 테스트

```python
# 추가 필요 테스트
tests/
├── test_model_types.py       # 모델 타입별 테스트
│   ├── test_engineering      # engineering 모델
│   ├── test_pid_symbol       # P&ID 심볼
│   ├── test_pid_class_aware  # P&ID 분류
│   └── test_bom_detector     # BOM 검출
├── test_sahi_integration.py  # SAHI 연동
└── test_model_registry.py    # 레지스트리 검증
```

---

### 우선순위 P1: 통합 테스트

#### 1. BlueprintFlow 워크플로우 테스트
**위치**: `gateway-api/tests/integration/`

```python
# 워크플로우 시나리오 테스트
test_workflow_scenarios.py
├── test_simple_detection     # 단순 검출 워크플로우
├── test_ocr_pipeline         # OCR 파이프라인
├── test_pid_analysis         # P&ID 분석 전체 흐름
└── test_bom_generation       # BOM 생성 워크플로우
```

#### 2. API 간 연동 테스트
```python
test_api_integration.py
├── test_yolo_to_ocr          # YOLO → OCR 연동
├── test_detection_to_analyzer # 검출 → 분석기
└── test_full_pipeline        # 전체 파이프라인
```

---

### 우선순위 P2: 프론트엔드 테스트

#### 1. 컴포넌트 테스트 확장
**위치**: `web-ui/src/components/**/*.test.tsx`

```typescript
// 추가 필요 테스트
components/
├── blueprintflow/
│   ├── NodePalette.test.tsx    # 노드 팔레트
│   ├── CanvasArea.test.tsx     # 캔버스
│   └── NodeEditor.test.tsx     # 노드 편집기
├── monitoring/
│   ├── APIStatusMonitor.test.tsx # API 상태
│   └── ServiceHealth.test.tsx    # 서비스 헬스
└── pid/
    └── PIDOverlayViewer.test.tsx # PID 뷰어
```

#### 2. 스토어 테스트 확장
```typescript
// 추가 필요 테스트
store/
├── monitoringStore.test.ts   # 모니터링 스토어
├── executionStore.test.ts    # 실행 스토어
└── settingsStore.test.ts     # 설정 스토어
```

---

### 우선순위 P3: E2E 테스트

#### 1. Playwright E2E 테스트
**위치**: `e2e/`

```typescript
// 시나리오별 E2E 테스트
e2e/
├── ui/
│   ├── dashboard.spec.ts     # Dashboard 테스트
│   ├── blueprintflow.spec.ts # BlueprintFlow 테스트
│   └── api-detail.spec.ts    # API 상세 테스트
└── api/
    ├── health.spec.ts        # 헬스체크 E2E
    └── workflow.spec.ts      # 워크플로우 E2E
```

---

## 테스트 작성 가이드

### Python (pytest)
```python
import pytest
from fastapi.testclient import TestClient

class TestFeature:
    """기능 테스트"""

    @pytest.fixture
    def client(self):
        from api_server import app
        return TestClient(app)

    def test_success_case(self, client):
        """정상 케이스"""
        response = client.post("/api/v1/feature", json={...})
        assert response.status_code == 200
        assert "result" in response.json()

    def test_validation_error(self, client):
        """유효성 검증 에러"""
        response = client.post("/api/v1/feature", json={})
        assert response.status_code == 422

    def test_edge_case(self, client):
        """엣지 케이스"""
        # 빈 입력, 큰 입력, 특수문자 등
        pass
```

### TypeScript (Vitest)
```typescript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';

describe('Component', () => {
  it('renders correctly', () => {
    render(<Component />);
    expect(screen.getByText('Expected Text')).toBeInTheDocument();
  });

  it('handles user interaction', async () => {
    const { user } = render(<Component />);
    await user.click(screen.getByRole('button'));
    expect(screen.getByText('Updated')).toBeInTheDocument();
  });
});
```

---

## 커버리지 목표

| 영역 | 현재 | 목표 | 비고 |
|------|------|------|------|
| Gateway Executors | 90% | 95% | 핵심 로직 |
| Gateway Routers | 80% | 90% | API 엔드포인트 |
| Web-UI Stores | 70% | 85% | 상태 관리 |
| Web-UI Components | 50% | 70% | UI 컴포넌트 |
| E2E | 30% | 50% | 주요 워크플로우 |

---

## 테스트 실행 명령

```bash
# 프론트엔드
cd web-ui
npm run test:run          # 단일 실행
npm run test:coverage     # 커버리지 리포트

# 백엔드
cd gateway-api
pytest tests/ -v                    # 전체 테스트
pytest tests/ -v --cov=.           # 커버리지
pytest tests/test_specific.py -v   # 특정 파일

# 개별 API
cd models/{api-id}-api
pytest tests/ -v
```

---

## 우선순위 정리

| 작업 | 우선순위 | 예상 테스트 수 | 비고 |
|------|----------|----------------|------|
| Blueprint AI BOM 확장 | P0 | +20개 | TECHCROSS 기능 |
| YOLO 모델별 테스트 | P0 | +15개 | 모델 타입 검증 |
| BlueprintFlow 통합 | P1 | +10개 | 워크플로우 시나리오 |
| 프론트엔드 컴포넌트 | P2 | +30개 | UI 테스트 |
| E2E 시나리오 | P3 | +10개 | 전체 흐름 |

**총 추가 예상**: +85개 테스트 → 총 590개 목표
