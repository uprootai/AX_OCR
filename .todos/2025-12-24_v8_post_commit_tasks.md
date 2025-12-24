# Blueprint AI BOM v8.0 커밋 후 일관성 작업

> **생성일**: 2025-12-24
> **목적**: v8.0 변경사항 분석 및 코드베이스 전체 일관성 확보를 위한 향후 작업 정리
> **우선순위**: 🟡 중간 (커밋 후 점진적 개선)

---

## 변경 사항 요약 (마지막 커밋 대비)

### 수정된 파일 (9개)
| 파일 | 변경 유형 | 핵심 내용 |
|------|----------|----------|
| `.todos/README.md` | 문서 | v8.0 완료 항목 추가, Feedback API 문서화 |
| `blueprint-ai-bom/README.md` | 버전 | v5.0 → v8.0 |
| `backend/routers/feedback_router.py` | 리팩토링 | 인라인 Pydantic → schemas import, response_model 추가 |
| `backend/schemas/__init__.py` | 추가 | Feedback 스키마 9개 export |
| `docker-compose.onprem.yml` | 볼륨 | feedback, yolo_training 볼륨 추가 |
| `docker-compose.yml` | 볼륨 | feedback, yolo_training 볼륨 추가 |
| `docs/README.md` | 문서 | v8.0 기능 목록 업데이트 |
| `docs/api/reference.md` | API 문서 | Feedback Loop API 5개 엔드포인트 추가 |
| `gateway-api/api_specs/blueprint-ai-bom.yaml` | 버전/태그 | v3.0.0 → v8.0.0, feedback/yolo-training 태그 |

### 신규 파일 (4개)
| 파일 | 내용 |
|------|------|
| `.todos/2025-12-23_v8_consistency_checklist.md` | 일관성 체크리스트 |
| `backend/schemas/feedback.py` | Feedback Pydantic 스키마 9개 |
| `backend/tests/test_feedback_pipeline.py` | 단위 테스트 16개 |
| `docs/features/feedback_pipeline.md` | 기능 문서 |

---

## 🔴 즉시 수정 필요 (일관성 문제)

### 1. verification_router.py 인라인 모델 분리

**문제**: `feedback_router.py`는 스키마 분리가 완료되었으나, `verification_router.py`에는 여전히 **3개 인라인 Pydantic 모델**이 존재

```python
# verification_router.py:39-57 (현재 상태)
class VerificationAction(BaseModel):
    item_id: str
    item_type: str = Field(default="dimension")
    action: str = Field(description="approved, rejected, modified")
    modified_data: Optional[Dict[str, Any]] = None
    review_time_seconds: Optional[float] = None

class BulkApproveRequest(BaseModel):
    item_ids: List[str]
    item_type: str = "dimension"

class ThresholdUpdateRequest(BaseModel):
    auto_approve_threshold: Optional[float] = Field(None, ge=0.5, le=1.0)
    critical_threshold: Optional[float] = Field(None, ge=0.0, le=0.9)
```

**해결 방안**:
1. `schemas/verification.py` 생성
2. 3개 모델 이동 + Response 모델 추가
3. `schemas/__init__.py`에 export 추가
4. `verification_router.py`에서 import 변경

**예상 작업량**: 30분

---

### 2. verification_router.py response_model 누락

**문제**: `feedback_router.py`는 모든 엔드포인트에 `response_model=` 사용 (5개), `verification_router.py`는 **0개**

| 라우터 | response_model 사용 | 상태 |
|--------|-------------------|------|
| feedback_router.py | 5개 | ✅ 완료 |
| verification_router.py | 0개 | ❌ 수정 필요 |
| analysis_router.py | 14개 | ✅ |
| relation_router.py | 3개 | ✅ |
| session_router.py | 3개 | ✅ |

**해결 방안**: `verification_router.py`의 모든 엔드포인트에 `response_model=` 추가
- `get_verification_queue` → `VerificationQueueResponse`
- `get_verification_stats` → `VerificationStatsResponse`
- `verify_item` → `VerificationResultResponse`
- 등등 (총 10개 엔드포인트)

**예상 작업량**: 1시간

---

### 3. Frontend verificationApi 누락

**문제**: 백엔드에 `verification_router.py`가 있으나, 프론트엔드 `api.ts`에 **verificationApi 없음**

**현재 api.ts의 API 클라이언트**:
- ✅ blueprintFlowApi
- ✅ sessionApi
- ✅ detectionApi
- ✅ bomApi
- ✅ configApi
- ✅ healthApi
- ✅ systemApi
- ✅ testImagesApi
- ✅ modelsApi
- ✅ groundTruthApi
- ✅ feedbackApi (v8.0 추가)
- ❌ **verificationApi** (누락)

**해결 방안**: `api.ts`에 `verificationApi` 추가
```typescript
export const verificationApi = {
  getQueue: async (sessionId: string, itemType = 'dimension') => {...},
  getStats: async (sessionId: string, itemType = 'dimension') => {...},
  verify: async (sessionId: string, action: VerificationAction) => {...},
  bulkApprove: async (sessionId: string, itemIds: string[], itemType = 'dimension') => {...},
  autoApprove: async (sessionId: string, itemType = 'dimension') => {...},
  getLogs: async (sessionId: string, actionFilter?: string) => {...},
  getThresholds: async () => {...},
  updateThresholds: async (thresholds: ThresholdUpdate) => {...},
  getTrainingData: async (sessionId?: string, actionFilter?: string) => {...},
};
```

**예상 작업량**: 45분

---

## 🟡 권장 수정 (테스트 커버리지)

### 4. 서비스 단위 테스트 누락

**현재 테스트 현황**:
| 서비스 | 테스트 파일 | 상태 |
|--------|------------|------|
| bom_service.py | test_bom_service.py | ✅ |
| detection_service.py | test_detection_service.py | ✅ |
| feedback_pipeline.py | test_feedback_pipeline.py | ✅ (v8.0) |
| pricing_utils.py | test_pricing_utils.py | ✅ |
| active_learning_service.py | - | ❌ |
| session_service.py | - | ❌ |
| dimension_service.py | - | ❌ |
| dimension_relation_service.py | - | ❌ |
| line_detector_service.py | - | ❌ |
| connectivity_analyzer.py | - | ❌ |
| region_segmenter.py | - | ❌ |
| gdt_parser.py | - | ❌ |
| vlm_classifier.py | - | ❌ |

**우선순위 테스트 추가**:
1. `test_active_learning_service.py` - Active Learning과 밀접한 관계
2. `test_session_service.py` - 핵심 서비스
3. `test_verification_router.py` - API 레벨 테스트

**예상 작업량**: 각 1-2시간

---

## 🟢 향후 개선 (선택)

### 5. 기능 문서 보완

**현재 docs/features/ 목록**:
- ✅ active_learning.md
- ✅ feedback_pipeline.md (v8.0)
- ✅ gdt_parser.md
- ✅ ocr_optimization.md
- ✅ ocr_performance.md
- ❌ region_segmentation.md (누락)
- ❌ connectivity_analysis.md (누락)
- ❌ dimension_relations.md (누락)
- ❌ vlm_classification.md (누락)

### 6. Frontend TypeScript 타입 동기화

**현재 types/index.ts 상태**:
- Feedback 관련 타입 일부 누락 가능
- `api.ts`에 인라인으로 정의된 타입들을 `types/index.ts`로 이동 검토

### 7. 프론트엔드 Feedback UI 컴포넌트

**현재 상태**: `feedbackApi`는 존재하나, 이를 사용하는 UI 컴포넌트 없음

**향후 추가 가능**:
- `FeedbackDashboard.tsx` - 피드백 통계 대시보드
- `ExportManager.tsx` - YOLO 데이터셋 내보내기 관리
- `AdminPage.tsx`에 통합 또는 별도 페이지

---

## 작업 체크리스트

### 🔴 즉시 (커밋 전 권장) - ✅ 모두 완료
- [x] `schemas/verification.py` 생성 및 모델 이동 ✅
- [x] `schemas/__init__.py` verification export 추가 ✅
- [x] `verification_router.py` 리팩토링 (schemas import + response_model) ✅
- [x] `frontend/src/lib/api.ts`에 `verificationApi` 추가 ✅

### 🟡 단기 (1주 내)
- [ ] `test_active_learning_service.py` 작성
- [ ] `test_session_service.py` 작성
- [ ] `test_verification_router.py` 작성

### 🟢 중장기 (선택)
- [ ] 누락된 기능 문서 작성 (4개)
- [ ] Frontend TypeScript 타입 통합
- [ ] Feedback UI 컴포넌트 개발

---

## 패턴 일관성 가이드

### Router 작성 표준 (feedback_router.py 기준)

```python
# 1. schemas에서 import
from schemas import (
    RequestModel,
    ResponseModel,
)

# 2. 모든 엔드포인트에 response_model 명시
@router.get("/endpoint", response_model=ResponseModel)
async def endpoint():
    ...
    return ResponseModel(...)  # 명시적 모델 반환
```

### 테스트 작성 표준 (test_feedback_pipeline.py 기준)

```python
class TestServiceName:
    def setup_method(self):
        """테스트 설정 - Mock 서비스 주입"""
        self.mock_dependency = Mock()
        self.service = Service(self.mock_dependency)

    def test_empty_case(self):
        """빈 입력 케이스"""
        ...

    def test_normal_case(self):
        """정상 케이스"""
        ...

    def test_edge_case(self):
        """경계 조건"""
        ...
```

---

## 관련 파일 목록

| 카테고리 | 파일 경로 | 상태 |
|----------|----------|------|
| **수정 필요** | `backend/routers/verification_router.py` | 리팩토링 필요 |
| **생성 필요** | `backend/schemas/verification.py` | 신규 |
| **수정 필요** | `backend/schemas/__init__.py` | verification export 추가 |
| **수정 필요** | `frontend/src/lib/api.ts` | verificationApi 추가 |
| **생성 필요** | `backend/tests/test_active_learning_service.py` | 신규 |
| **생성 필요** | `backend/tests/test_session_service.py` | 신규 |

---

## 변경 영향도 분석

### verification_router.py 리팩토링 시 영향

1. **백엔드**: `verification_router.py` 단독 수정 (의존성 없음)
2. **프론트엔드**: 기존 `VerificationQueue.tsx`에서 직접 fetch 사용 중 → `verificationApi` 전환 필요
3. **테스트**: 신규 테스트 추가 필요

### 호환성 유지

- API 엔드포인트 URL 변경 없음
- Request/Response 구조 변경 없음 (타입만 명시)
- 기존 프론트엔드 코드 계속 동작

---

**작성자**: Claude Code (Opus 4.5)
**최종 업데이트**: 2025-12-24
