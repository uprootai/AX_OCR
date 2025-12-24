# Blueprint AI BOM v8.0 일관성 점검 체크리스트

> **생성일**: 2025-12-23
> **목적**: v8.0 Feedback Loop Pipeline 커밋 후 코드베이스 전체 일관성 확보
> **상태**: ✅ 모든 항목 완료

---

## 개요

v8.0에서 Feedback Loop Pipeline이 구현되었으나, 일부 파일들이 업데이트되지 않아 버전 불일치 및 패턴 불일치가 발생했습니다. 이 문서는 향후 작업 시 반드시 확인해야 할 항목들을 정리합니다.

---

## 1. 버전 불일치 (Version Inconsistency)

### 🔴 즉시 수정 필요

| 파일 | 현재 버전 | 정확한 버전 | 상태 |
|------|----------|------------|------|
| `blueprint-ai-bom/README.md` | v8.0 | v8.0 | ✅ 수정됨 |
| `gateway-api/api_specs/blueprint-ai-bom.yaml` | v8.0.0 | v8.0.0 | ✅ 수정됨 |
| `.todos/README.md` | v8.0 | v8.0 반영 | ✅ 수정됨 |

### 수정 내용

#### `blueprint-ai-bom/README.md`
```diff
- | **상태** | ✅ 구현 완료 (v5.0) |
+ | **상태** | ✅ 구현 완료 (v8.0) |
```

추가해야 할 섹션:
- Feedback Loop Pipeline 기능 설명
- 온프레미스 배포 방법 (docker-compose.onprem.yml 참조)

#### `gateway-api/api_specs/blueprint-ai-bom.yaml`
```yaml
metadata:
  version: 8.0.0  # 3.0.0 → 8.0.0
  tags:
    - feedback    # 추가
    - export      # 추가
```

---

## 2. 스키마 리팩토링 (Schema Refactoring) ✅ 완료

### ✅ 수정 완료

`feedback_router.py`의 인라인 Pydantic 모델이 `schemas/feedback.py`로 분리되었습니다.

#### 현재 상태 (feedback_router.py 내부)
```python
class ExportRequest(BaseModel):
    output_name: Optional[str] = None
    include_rejected: bool = False
    min_approved_rate: float = 0.5
    days_back: Optional[int] = None

class ExportResponse(BaseModel):
    success: bool
    output_path: str
    image_count: int
    label_count: int
    class_distribution: dict
    timestamp: str
    error: Optional[str] = None

class FeedbackStatsResponse(BaseModel):
    total_sessions: int
    total_detections: int
    approved_count: int
    rejected_count: int
    modified_count: int
    approval_rate: float
    rejection_rate: float
    modification_rate: float
```

#### 권장 구조
```
backend/schemas/
├── feedback.py          # 신규 생성 필요
│   ├── ExportRequest
│   ├── ExportResponse
│   ├── FeedbackStatsResponse
│   └── VerifiedSessionResponse
└── __init__.py          # feedback 스키마 export 추가
```

#### schemas/__init__.py에 추가
```python
from .feedback import (
    ExportRequest,
    ExportResponse,
    FeedbackStatsResponse,
    VerifiedSessionResponse,
)
```

---

## 3. Gateway API 스펙 업데이트

### 🔴 필수 수정

`gateway-api/api_specs/blueprint-ai-bom.yaml`에 Feedback 관련 정보가 없습니다.

#### 추가해야 할 내용

```yaml
# parameters 섹션에 추가
parameters:
  - name: features
    type: array
    default:
      - verification
      - feedback_export  # 추가
    items:
      enum:
        - verification
        - gt_comparison
        - dimension_extraction
        - relation_analysis
        - feedback_export  # 추가
    options:
      - value: feedback_export
        label: Feedback Loop 내보내기
        description: 검증된 데이터를 YOLO 재학습용 데이터셋으로 내보냅니다.

# 새 섹션 추가
feedbackEndpoints:
  - path: /feedback/stats
    method: GET
    description: 피드백 통계 조회
  - path: /feedback/sessions
    method: GET
    description: 검증 완료 세션 목록
  - path: /feedback/export/yolo
    method: POST
    description: YOLO 데이터셋 내보내기
  - path: /feedback/exports
    method: GET
    description: 내보내기 목록
  - path: /feedback/health
    method: GET
    description: 서비스 상태
```

---

## 4. 프론트엔드 API 통합 ✅ 완료

### ✅ 수정 완료

`frontend/src/lib/api.ts`에 Feedback API 클라이언트가 추가되었습니다.

#### 필요한 파일

```
frontend/src/
├── lib/
│   └── api.ts           # Feedback API 함수 추가
├── components/
│   └── FeedbackStats.tsx  # 피드백 통계 UI (선택)
└── pages/
    └── AdminPage.tsx      # 관리자 페이지에 내보내기 UI (선택)
```

#### api.ts에 추가할 함수
```typescript
// Feedback API
export const getFeedbackStats = (daysBack?: number) =>
  api.get('/feedback/stats', { params: { days_back: daysBack } });

export const getVerifiedSessions = (minApprovedRate = 0.5, daysBack?: number) =>
  api.get('/feedback/sessions', { params: { min_approved_rate: minApprovedRate, days_back: daysBack } });

export const exportYoloDataset = (data: {
  output_name?: string;
  include_rejected?: boolean;
  min_approved_rate?: number;
  days_back?: number;
}) => api.post('/feedback/export/yolo', data);

export const getExports = () => api.get('/feedback/exports');

export const getFeedbackHealth = () => api.get('/feedback/health');
```

---

## 5. Docker 볼륨 설정 ✅ 완료

### ✅ 수정 완료

`docker-compose.yml` 및 `docker-compose.onprem.yml`에 볼륨이 추가되었습니다.

#### 현재 docker-compose.yml
```yaml
volumes:
  - ./uploads:/app/uploads
  - ./results:/app/results
  - ./config:/app/config
  - ./models:/app/models:ro
```

#### 추가 필요 (선택)
```yaml
volumes:
  - ./feedback:/data/feedback         # 피드백 데이터
  - ./yolo_training:/data/yolo_training  # YOLO 내보내기
```

**참고**: 현재 컨테이너 내부 경로로 동작하므로 즉시 필요하지 않음. 데이터 영속성이 필요한 경우 추가.

---

## 6. 단위 테스트 추가 ✅ 완료

### ✅ 수정 완료

`backend/tests/test_feedback_pipeline.py`가 생성되었습니다.

#### 추가해야 할 테스트 파일

```
backend/tests/
├── test_feedback_pipeline.py   # 신규
└── test_feedback_router.py     # 신규 (선택)
```

#### test_feedback_pipeline.py 예시
```python
import pytest
from unittest.mock import Mock, patch
from services.feedback_pipeline import FeedbackPipelineService

class TestFeedbackPipeline:
    def test_collect_verified_sessions_empty(self):
        """검증 완료 세션이 없는 경우"""
        mock_session_service = Mock()
        mock_session_service.list_sessions.return_value = []

        service = FeedbackPipelineService(mock_session_service)
        result = service.collect_verified_sessions()

        assert result == []

    def test_get_feedback_stats_no_sessions(self):
        """세션이 없을 때 통계"""
        mock_session_service = Mock()
        mock_session_service.list_sessions.return_value = []

        service = FeedbackPipelineService(mock_session_service)
        stats = service.get_feedback_stats()

        assert stats["total_sessions"] == 0
        assert stats["approval_rate"] == 0

    def test_export_yolo_dataset_creates_files(self, tmp_path):
        """YOLO 데이터셋 내보내기 테스트"""
        # 구현 필요
        pass
```

---

## 7. .todos/README.md 업데이트

### 🔴 필수 수정

현재 `.todos/README.md`에서 "피드백 루프"가 "향후 계획"으로 표시되어 있습니다.

#### 수정 내용

```diff
## 향후 작업 우선순위

### 🟢 낮음 (향후 검토)
- 1. **GNN 기반 관계 분석** - 연구 단계
- 2. **피드백 루프** - 모델 재학습 파이프라인 (Active Learning 로그 활용)
+ 2. ~~**피드백 루프**~~ - ✅ v8.0에서 구현 완료
- 3. **VLM 자동 분류** - GPT-4V/Claude 비용 분석 후 결정
```

#### 완료된 작업 섹션에 추가
```markdown
| Feedback Loop Pipeline (v8.0) | ✅ 완료 | YOLO 재학습 데이터셋 내보내기 |
| 온프레미스 배포 | ✅ 완료 | docker-compose.onprem.yml |
```

---

## 8. ESLint 패턴 - 다른 컴포넌트 점검

### ✅ 완료됨

v8.0 커밋에서 다음 ESLint 수정이 적용되었습니다:

| 파일 | 수정 내용 |
|------|----------|
| `tooltipContent.ts` | 상수 분리 (Fast Refresh) |
| `Tooltip.tsx` | 불필요한 re-export 제거 |
| `DetectionCard.tsx` | setState-in-useEffect 수정 |
| `ConnectivityDiagram.tsx` | useMemo 의존성 배열 수정 |
| `WorkflowPage.tsx` | useEffect 의존성 배열 수정 |
| `RegionEditor.tsx` | 불필요한 의존성 제거 |

**검증**: `npm run lint` 통과 ✅

---

## 작업 체크리스트

### 커밋 전 필수
- [x] `blueprint-ai-bom/README.md` 버전 v8.0으로 업데이트 ✅
- [x] `gateway-api/api_specs/blueprint-ai-bom.yaml` 버전 8.0.0으로 업데이트 ✅
- [x] `.todos/README.md` 피드백 루프 완료 표시 ✅

### 권장 (향후) - ✅ 모두 완료
- [x] `schemas/feedback.py` 분리 ✅
- [x] `schemas/__init__.py` 업데이트 ✅
- [x] 프론트엔드 Feedback API 클라이언트 추가 ✅
- [x] Docker 볼륨 영속화 설정 ✅
- [x] `test_feedback_pipeline.py` 단위 테스트 추가 ✅

---

## 관련 파일 목록

| 카테고리 | 파일 경로 |
|----------|----------|
| **Backend** | `backend/routers/feedback_router.py` |
| **Backend** | `backend/services/feedback_pipeline.py` |
| **Backend** | `backend/api_server.py` (라우터 등록) |
| **Docs** | `docs/features/feedback_pipeline.md` |
| **Docs** | `docs/api/reference.md` (Feedback 섹션) |
| **DevOps** | `docker-compose.onprem.yml` |
| **DevOps** | `scripts/deploy_onprem.sh` |

---

**작성자**: Claude Code (Opus 4.5)
**최종 업데이트**: 2025-12-23
