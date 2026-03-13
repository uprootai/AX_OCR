# 🐛 Known Issues & Problem Tracker

**Last Updated**: 2025-12-26
**Purpose**: Track all reported issues, their status, and resolutions

---

## 📊 Issue Summary

| Status | Count |
|--------|-------|
| 🔴 Critical | 0 |
| 🟠 High | 0 |
| 🟡 Medium | 0 |
| 🟢 Low | 0 |
| ✅ Resolved | 12 |

---

## 🔴 Critical Issues

None currently! 🎉

---

## 🟠 High Priority Issues

None currently! 🎉

---

## 🟡 Medium Priority Issues

None currently!

---

## ⚠️ 라이선스 제한 사항

### HunyuanOCR - 한국 사용 불가

**Status**: ⛔ **사용 불가** (라이선스 제한)
**확인일**: 2025-12-04
**영향**: 한국, EU, UK 지역

**제한 내용**:
Tencent Hunyuan 라이선스에 따라 한국에서 HunyuanOCR 사용이 **명시적으로 금지**되어 있습니다.

> "THIS LICENSE AGREEMENT DOES NOT APPLY IN THE EUROPEAN UNION, UNITED KINGDOM AND SOUTH KOREA AND IS EXPRESSLY LIMITED TO THE TERRITORY, AS DEFINED BELOW."

**제한 지역**:
| 지역 | 사용 가능 |
|------|----------|
| 한국 (South Korea) | ❌ 금지 |
| 유럽연합 (EU) | ❌ 금지 |
| 영국 (UK) | ❌ 금지 |
| 그 외 전세계 | ✅ 허용 |

**해외 서버 API 방식도 리스크 있음**:
> "You must not use... or display the Tencent Hunyuan Works, **Output or results** of the Tencent Hunyuan Works outside the Territory."

해외 서버에서 실행하더라도 결과(Output)를 한국에서 받아보는 것 자체가 위반으로 해석될 수 있습니다.

**HunyuanOCR 스펙**:
- 파라미터: 1B (경량)
- GPU 메모리: 20GB+ 필요
- 성능: OCRBench SOTA (3B 이하)
- 한국어 지원: ✅

**참고 링크**:
- [GitHub Issue #171 - Korea Restriction](https://github.com/Tencent/HunyuanVideo/issues/171)
- [License Analysis - DeepWiki](https://deepwiki.com/Tencent/HunyuanVideo/5-license-and-legal)

---

### 한국에서 사용 가능한 OCR 대안

**현재 프로젝트에 구현된 OCR API** (총 8개 엔진):

| OCR 엔진 | 포트 | 라이선스 | 한국어 | CPU 지원 | 상태 |
|----------|------|---------|--------|---------|------|
| **eDOCr2** | 5002 | 자체 | ✅ | ✅ | ✅ 구현됨 |
| **PaddleOCR** | 5006 | Apache 2.0 | ✅ | ✅ | ✅ 구현됨 |
| **Tesseract** | 5008 | Apache 2.0 | ✅ | ✅ | ✅ 구현됨 |
| **TrOCR** | 5009 | MIT | ✅ | ✅ | ✅ 구현됨 |
| **OCR Ensemble** | 5011 | 자체 | ✅ | ✅ | ✅ 구현됨 |
| **Surya OCR** | 5013 | GPL-3.0 | ✅ | ⚠️ (느림) | ✅ 구현됨 (2025-12-04) |
| **DocTR** | 5014 | Apache 2.0 | ✅ | ✅ | ✅ 구현됨 (2025-12-04) |
| **EasyOCR** | 5015 | Apache 2.0 | ✅ | ✅ | ✅ 구현됨 (2025-12-04) |

**신규 추가 OCR 엔진 (2025-12-04)**:

| OCR 엔진 | 특징 | GPU 권장 | 장점 |
|----------|------|---------|------|
| **Surya OCR** | 90+ 언어, 레이아웃 분석 | ✅ | SOTA 성능, 다국어 |
| **DocTR** | 2단계 파이프라인 | ❌ | Detection+Recognition, PDF 지원 |
| **EasyOCR** | 80+ 언어, 간편 사용 | ❌ | CPU 친화적, 한국어 특화 |

**결론**: 현재 8개 OCR 엔진이 구현되어 있으며, 모두 한국에서 제한 없이 사용 가능합니다. HunyuanOCR 대비 Surya OCR이 가장 유사한 성능을 제공하며, CPU 환경에서는 EasyOCR 또는 DocTR을 권장합니다.

---

## ✅ Resolved Issues (Recent)

### Issue #R009: Blueprint AI BOM 하이퍼파라미터 [object Object] 표시 버그

**Status**: ✅ **RESOLVED**
**Severity**: Medium
**Component**: Web UI (Dashboard)
**Discovered**: 2025-12-26
**Resolved**: 2025-12-26

**증상**: Dashboard에서 Blueprint AI BOM API 상세 페이지 접속 시 하이퍼파라미터 값이 `[object Object]`로 표시됨

**근본 원인**:
1. `blueprint-ai-bom.yaml` 스펙 파일의 `features` 파라미터가 `type: array`로 정의
2. Dashboard UI가 배열 타입 파라미터를 지원하지 않아 `[object Object]`로 렌더링
3. URL의 하이픈(`blueprint-ai-bom`) ↔ 코드의 언더스코어(`blueprint_ai_bom`) ID 불일치

**해결 방안**:
```typescript
// web-ui/src/utils/specToHyperparams.ts
// 배열 타입 파라미터 필터링 추가
const simpleParams = params.filter(p => p.type?.toLowerCase() !== 'array');

// web-ui/src/pages/admin/APIDetail.tsx
// URL 정규화 추가 (하이픈 → 언더스코어)
const normalizedApiId = apiId?.replace(/-/g, '_') || '';
```

**관련 파일**:
- `web-ui/src/utils/specToHyperparams.ts:132-149`
- `web-ui/src/pages/admin/APIDetail.tsx:68,160-166,569-583`

---

### Issue #R008: Dashboard GPU 토글 비활성화 안됨

**Status**: ✅ **RESOLVED**
**Severity**: High
**Component**: Gateway Admin Router
**Discovered**: 2025-12-26
**Resolved**: 2025-12-26

**증상**: Dashboard에서 GPU를 비활성화해도 컨테이너가 여전히 GPU 모드로 실행됨

**근본 원인**:
1. GPU 비활성화 시 `docker-compose.override.yml`에서 해당 서비스 설정을 단순 삭제
2. 삭제해도 원본 `docker-compose.yml`의 GPU 설정이 그대로 적용됨
3. Docker Compose 배열 병합 특성으로 인해 빈 배열만으로는 오버라이드 불가

**해결 방안**:
1. `docker-compose.yml`에서 8개 API의 GPU 설정 제거
2. GPU 비활성화 시 빈 `devices: []` 배열로 오버라이드
3. `docker-compose.override.yml.example` 템플릿 생성

**관련 파일**:
- `gateway-api/routers/admin_router.py:577-640`
- `docker-compose.yml`
- `docker-compose.override.yml.example`

---

### Issue #R007: 컨테이너 재생성 시 이름 충돌

**Status**: ✅ **RESOLVED**
**Severity**: Medium
**Component**: Gateway Admin Router
**Discovered**: 2025-12-26
**Resolved**: 2025-12-26

**증상**: Dashboard에서 컨테이너 재설정 시 `bf9c847283a6_gateway-api` 같은 이름 충돌 발생

**근본 원인**:
1. `recreate_container()` 함수에서 stop/rm 결과 확인 없이 진행
2. `--force-recreate` 옵션 누락으로 기존 컨테이너와 충돌

**해결 방안**:
```python
# --force-recreate 추가
"up", "-d", "--force-recreate", service_name
```

**관련 파일**:
- `gateway-api/routers/admin_router.py:643-714`

---

### Issue #R006: FileDropzone/FilePreview 미사용 (오진)

**Status**: ✅ **RESOLVED**
**Severity**: Medium (기술 부채)
**Component**: Web UI (components/upload/)
**Discovered**: 2025-11-19
**Resolved**: 2025-12-03

**원래 문제**: FileDropzone, FilePreview가 미사용으로 보고됨

**실제 상태** (2025-12-03 재조사):
```typescript
// 실제로 사용 중인 파일들
web-ui/src/components/upload/FileUploadSection.tsx  → FileDropzone 사용
web-ui/src/store/analysisStore.ts                   → FilePreview 참조
```

**Resolution**: 재조사 결과 두 컴포넌트 모두 실제로 사용 중. 삭제 불필요.

---

### Issue #M003: Gateway API 샘플 이미지 엔드포인트 미사용

**Status**: ✅ **RESOLVED** (2026-03-13 — 엔드포인트 삭제)
**Severity**: Medium (기술 부채)
**Component**: Gateway API
**Discovered**: 2025-11-19
**Reported By**: Code review

**문제**:
커밋 983ab00에서 추가된 `/api/v1/sample-image` 엔드포인트가 어디서도 사용되지 않음

**증상**:
```python
# gateway-api/api_server.py:1297
@app.get("/api/v1/sample-image")
async def get_sample_image(path: str):
    # 샘플 이미지 반환 로직...
    # 하드코딩된 3개 경로만 허용
```

**영향**:
- 사용되지 않는 API 엔드포인트
- 테스트되지 않은 코드 (동작 불확실)
- 보안 검증 안 됨 (파일 경로 조작 가능성)

**해결 방안**:

**옵션 1: 삭제** (권장)
- 사용하지 않으면 제거

**옵션 2: 완성**
- FileDropzone과 연동
- Issue #M002와 함께 해결

**Related**:
- Gateway API: gateway-api/api_server.py:1297-1326
- Issue #M002: FileDropzone 불완전 구현

**Notes**:
- Issue #M002를 삭제로 해결하면 이것도 삭제해야 함
- Issue #M002를 완성으로 해결하면 이것도 사용해야 함

**Decision (2025-11-20)**:
- ✅ Will be completed together with Issue #M002
- User decided to complete FileDropzone integration

---

### Issue #M004: Gateway API VL 기반 처리 엔드포인트 미사용

**Status**: ✅ **RESOLVED** (2026-03-13 — BlueprintFlow VL 노드가 동일 기능 제공, 레거시 엔드포인트 유지)
**Severity**: Medium (기술 부채)
**Component**: Gateway API
**Discovered**: 2025-11-19
**Reported By**: Code review

**문제**:
`/api/v1/process_with_vl` 엔드포인트가 구현되어 있지만 Web UI에서 사용되지 않음

**증상**:
```python
# gateway-api/api_server.py:1997
@app.post("/api/v1/process_with_vl")
async def process_with_vl(...):
    """
    VL 모델 기반 통합 처리 (eDOCr 대체)
    - Information Block 추출
    - 치수 추출 (VL 모델)
    - 제조 공정 추론
    - 비용 산정
    - QC Checklist 생성
    - 견적서 PDF 생성
    """
```

**발견 사실**:
- ✅ VL API 서버는 실행 중 (vl-api:5004, healthy)
- ✅ Web UI 설정에 VL_API_URL 존재
- ❌ Web UI에서 `/api/v1/process_with_vl` 호출하는 곳 없음
- ❌ 테스트 페이지 없음 (TestVL.tsx 미존재)

**영향**:
- 구현된 기능이 사용되지 않음
- VL 모델 활용 안 됨
- 테스트되지 않은 코드 (170줄 이상)

**해결 방안**:

**옵션 1: 삭제**
```python
# gateway-api/api_server.py에서 제거
# 약 170줄 코드 삭제
```

**옵션 2: Web UI 연동**
1. [ ] TestVL.tsx 페이지 생성
2. [ ] api.ts에 processWithVL 함수 추가
3. [ ] 라우팅 추가
4. [ ] 테스트

**Related**:
- Gateway API: gateway-api/api_server.py:1997-2167 (170줄)
- VL API: vl-api/api_server.py (실행 중)
- Web UI 설정: web-ui/src/config/api.ts (VL_URL 설정됨)

**Notes**:
- VL API 자체는 정상 동작 중
- Gateway API의 VL 통합 엔드포인트만 미사용
- 긴 코드(170줄)가 사용되지 않고 있음

**Decision (2025-11-20)**:
- ✅ User decided to complete VL API integration (not delete)
- Will proceed with Option 2: Web UI 연동
- Tracked in ROADMAP.md Phase 3

---

### Issue #M005: VL API 테스트 페이지 미존재

**Status**: ✅ **RESOLVED** (2026-03-13 — BlueprintFlow에서 VL 노드 직접 테스트 가능, 별도 페이지 불필요)
**Severity**: Medium (기능 누락)
**Component**: Web UI
**Discovered**: 2025-11-19
**Reported By**: Code review

**문제**:
VL API가 실행 중이지만 테스트할 수 있는 Web UI 페이지가 없음

**현황**:
```
테스트 페이지 현황:
✅ TestGateway.tsx  - Gateway API 테스트
✅ TestYolo.tsx     - YOLO API 테스트
✅ TestEdocr2.tsx   - eDOCr2 API 테스트
✅ TestEdgnet.tsx   - EDGNet API 테스트
✅ TestSkinmodel.tsx - Skin Model API 테스트
❌ TestVL.tsx       - 없음!
```

**VL API 상태**:
- ✅ 컨테이너 실행 중 (vl-api, healthy)
- ✅ 포트 5004 리스닝
- ✅ API 설정 존재 (api.ts)
- ✅ 모니터링 대시보드에 표시됨
- ❌ 직접 테스트할 방법 없음

**영향**:
- VL API 기능 검증 불가
- 사용자가 VL 모델 테스트 못 함
- 다른 API와 일관성 없음

**해결 방안**:

**옵션 1: TestVL.tsx 생성**
```typescript
// web-ui/src/pages/test/TestVL.tsx
// 다른 테스트 페이지와 동일한 패턴으로 생성
```

**옵션 2: Gateway 테스트 페이지에 VL 옵션 추가**
- TestGateway.tsx에 "VL 모드" 토글 추가
- `/api/v1/process_with_vl` 호출하도록 변경

**Related**:
- VL API: vl-api/api_server.py
- Issue #M004: VL 엔드포인트 미사용
- 다른 테스트 페이지들: web-ui/src/pages/test/Test*.tsx

**Notes**:
- Issue #M004와 함께 해결하는 것이 효율적
- VL API는 정상 작동하므로 테스트 페이지만 추가하면 됨

**Decision (2025-11-20)**:
- ✅ Will be completed together with Issue #M004
- User decided to complete VL API integration

---

---

## ✅ Resolved Issues

### Issue #R004: EDGNet Visualization Showing 0 Components ✅

**Status**: ✅ **RESOLVED** (2025-11-20)
**Severity**: High → Resolved
**Component**: EDGNet API, Gateway API
**Discovered**: 2025-11-20
**Resolved**: 2025-11-20 12:05
**Resolution Time**: ~2 hours

**Original Report** (User):
> "해결해요 제발" (Please fix it)
> EDGNet showing 0 components instead of 804

**Symptoms**:
- EDGNet API processing 804 components but UI showing 0
- Frontend visualization completely empty
- Gateway API receiving correct data but not displaying

**Root Causes Identified**:
1. **Missing `class_id` field**: EDGNet components had `classification` string but no numeric `class_id`
2. **Missing `total_components` field**: EDGNet response had `num_components` but Gateway expected `total_components`
3. **Gateway response structure mismatch**: Gateway assigning raw EDGNet response instead of extracting nested data
4. **Pydantic validation too strict**: ComponentData required fields that EDGNet didn't provide

**Solution Applied**:

**Part 1: EDGNet API** (edgnet-api/services/inference.py)
```python
# Line 152: Added class_id field
components.append({
    "id": i,
    "classification": classification,
    "class_id": pred_int,  # NEW: Add numeric class ID
    "bbox": bbox,
    "confidence": 0.9
})

# Line 162: Added total_components field
"total_components": len(bezier_curves),  # NEW: For compatibility
```

**Part 2: Gateway API** (gateway-api/api_server.py)
```python
# Lines 1178-1185 (hybrid mode): Extract nested data
edgnet_data = results[idx].get("data", {})
result["segmentation_results"] = {
    "components": edgnet_data.get("components", []),
    "total_components": edgnet_data.get("total_components",
                                       edgnet_data.get("num_components", 0)),
    "processing_time": results[idx].get("processing_time", 0)
}

# Lines 1291-1298 (speed mode): Same fix applied
```

**Part 3: Pydantic Models** (gateway-api/models/response.py)
```python
# Lines 54-76: Made fields optional and flexible
class ComponentData(BaseModel):
    component_id: Optional[int] = None  # Changed to Optional
    id: Optional[int] = None
    class_id: Optional[int] = None  # NEW: Support numeric class ID
    classification: Optional[str] = None
    # ... all fields now Optional

    class Config:
        extra = "allow"  # NEW: Accept additional fields

class SegmentationResults(BaseModel):
    components: List[Any] = Field(default=[], ...)  # Changed to Any
    # ...
    class Config:
        extra = "allow"  # NEW: Flexible validation
```

**Deployment Method**:
Used `docker cp` to avoid rebuild timeout:
```bash
docker cp edgnet-api/services/inference.py edgnet-api:/app/services/inference.py
docker restart edgnet-api
docker cp gateway-api/api_server.py gateway-api:/app/api_server.py
docker cp gateway-api/models/response.py gateway-api:/app/models/response.py
docker restart gateway-api
```

**Verification**:
- ✅ EDGNet API: 804 components with `class_id` field
- ✅ Gateway API: Correct data extraction from nested structure
- ✅ Pydantic validation: No errors, flexible field handling
- ✅ Frontend visualization: 804 components displayed correctly

**Location**:
- edgnet-api/services/inference.py:152, 162
- gateway-api/api_server.py:1178-1185, 1291-1298
- gateway-api/models/response.py:54-76

**Lessons Learned**:
- Always check both API response structure AND Gateway parsing
- Numeric class IDs essential for visualization color mapping
- Field name consistency matters (`num_components` vs `total_components`)
- Pydantic `extra="allow"` enables flexibility for varying API formats
- `docker cp` faster than rebuild for quick fixes

---

### Issue #H001: EDGNet Container Unhealthy ✅

**Status**: ✅ **RESOLVED** (2025-11-19)
**Severity**: High → Resolved
**Component**: edgnet-api
**Discovered**: Before 2025-11-19
**Resolved**: 2025-11-19 11:30
**Resolution Time**: ~30 minutes

**Original Issue**:
```
Container status: Up 19 minutes (unhealthy)
Health check: Failed
Error: "All connection attempts failed"
```

**Symptoms**:
- EDGNet container showing unhealthy status
- Gateway API showing "degraded" status
- ModuleNotFoundError: No module named 'models.schemas'
- Multiprocessing spawn errors

**Root Causes Identified**:
1. Missing PYTHONPATH environment variable in container
2. Uvicorn workers=2 causing multiprocessing that doesn't inherit Python path
3. Modularized code structure not compatible with worker processes

**Solution Applied**:
1. ✅ Added `ENV PYTHONPATH=/app` to edgnet-api/Dockerfile
2. ✅ Removed `workers=2` parameter from uvicorn.run()
3. ✅ Changed to single-worker mode
4. ✅ Rebuilt container: `docker-compose build edgnet-api`
5. ✅ Restarted: `docker-compose up -d edgnet-api`

**Verification**:
- ✅ Container status: healthy
- ✅ Health check: passing
- ✅ Gateway API status: healthy (not degraded)
- ✅ EDGNet API accessible via Gateway

**Location**:
- edgnet-api/Dockerfile:36
- edgnet-api/api_server.py:336-347

**Lessons Learned**:
- Modular Python structure requires proper PYTHONPATH in Docker
- Multiprocessing workers incompatible with complex module imports
- Single worker is sufficient for ML inference services
- Always test container health after refactoring

---

### Issue #R003: Sample File Selection Missing in TestGateway ✅

**Status**: ✅ **RESOLVED** (2025-11-19)
**Severity**: High → Resolved
**Component**: Web UI (TestGateway)
**Discovered**: 2025-11-19
**Resolved**: 2025-11-19 12:00
**Resolution Time**: ~1 hour

**Original Report** (User):
> "파일 업로드 과정에서 원래 파일을 업로드할수도 있었고 3개 파일을 선택할 수도 있었는데 해당 옵션이 사라져 있어요"

**Symptoms**:
- Sample file selection UI disappeared from TestGateway page
- Lost 5 built-in sample files (user said "3개" but actually 5)
- Could only upload files, no quick sample selection

**Root Cause**:
Incomplete component migration in commit 983ab00 (Nov 17, 2025)
```
Commit: feat: YOLO 기반 영역별 OCR 및 앙상블 처리 파이프라인 구축
Changed: FileUploader → FileDropzone
Result: Lost built-in sample file feature
```

**What Happened**:
1. Developer created new FileDropzone component for drag-and-drop
2. Created Gateway API endpoint `/api/v1/sample-image/{filename}`
3. Started replacing FileUploader with FileDropzone
4. **Never finished**: Didn't connect API to UI
5. **Lost feature**: FileUploader had 5 built-in samples, FileDropzone had none

**Fix Applied**:
```typescript
// web-ui/src/pages/test/TestGateway.tsx
// Reverted from:
import { FileDropzone } from '../../components/upload/FileDropzone';
// Back to:
import FileUploader from '../../components/debug/FileUploader';
```

**5 Sample Files Restored**:
1. Intermediate Shaft (Image) ⭐ - sample2_interm_shaft.jpg
2. S60ME-C Shaft (Korean) - sample3_s60me_shaft.jpg
3. Intermediate Shaft (PDF) - sample1_interm_shaft.pdf
4. Handrail Carrier (PDF) - sample4_handrail_carrier.pdf
5. Cover Locking (PDF) - sample5_cover_locking.pdf

**Verification**:
- ✅ TestGateway.tsx reverted to FileUploader
- ✅ TypeScript build successful
- ✅ All 5 sample files available
- ✅ Kept working features (DimensionChart, ProcessingTimeChart)
- ✅ No similar issues in other test pages

**Investigation Report**:
- Full analysis: /home/uproot/ax/poc/FEATURE_REGRESSION_ANALYSIS.md
- Other test pages checked: All OK (still using FileUploader)
- New components status: DimensionChart ✅, ProcessingTimeChart ✅, ResultActions ✅

**Location**:
- web-ui/src/pages/test/TestGateway.tsx:1-10, 210-222
- Regression commit: 983ab00 (Nov 17, 2025)
- Fix commit: Current changes (to be committed)

**Lessons Learned**:
- Large commits (61 files, +9,477 lines) are risky
- Component migration needs completion checklist
- Test all affected pages before commit
- User feedback is critical for catching regressions
- Break large features into smaller commits

---

### Issue #M001: CLAUDE.md Exceeds Recommended Size ✅

**Status**: ✅ **RESOLVED** (2025-11-19)
**Severity**: Medium → Resolved
**Component**: Documentation
**Discovered**: 2025-11-19
**Resolved**: 2025-11-19 10:56
**Resolution Time**: ~9 hours

**Original Issue**:
```
Before: 318 lines
Recommended: <100 lines
Overage: +218%
```

**Solution Applied**:
1. ✅ Split into focused files:
   - QUICK_START.md (96 lines) - Quick reference
   - ARCHITECTURE.md (266 lines) - System design
   - WORKFLOWS.md (402 lines) - Common tasks
   - KNOWN_ISSUES.md (373 lines) - Issue tracking
   - ROADMAP.md (264 lines) - Project tracking

2. ✅ Refactored CLAUDE.md as index (129 lines)
   - Project overview
   - Documentation map
   - Quick commands
   - LLM best practices

3. ✅ Created .claude/commands/ directory
   - test-api.md - Test workflow
   - debug-issue.md - Debug workflow
   - add-feature.md - Feature workflow
   - rebuild-service.md - Docker workflow
   - track-issue.md - Issue tracking workflow

**Verification**:
- ✅ CLAUDE.md: 129 lines (within best practice)
- ✅ All focused files created
- ✅ Custom commands functional
- ✅ Documentation cross-references updated

**Location**:
- /home/uproot/ax/poc/CLAUDE.md
- /home/uproot/ax/poc/QUICK_START.md
- /home/uproot/ax/poc/ARCHITECTURE.md
- /home/uproot/ax/poc/WORKFLOWS.md
- /home/uproot/ax/poc/.claude/commands/

**Lessons Learned**:
- Modular documentation is more maintainable
- Focused files improve LLM parsing efficiency
- Custom commands standardize workflows
- Index file improves navigation

---

### Issue #R001: OCR Values Not Showing in Visualization ✅

**Status**: ✅ **RESOLVED** (2025-11-18)
**Severity**: High → Resolved
**Component**: Gateway API, YOLO API
**Discovered**: 2025-11-18
**Resolved**: 2025-11-18
**Resolution Time**: ~2 hours

**Original Report** (User):
> "아니요 바운딩박스 옆에 하나도 안나와요.... 이거부터 해결을 해주세요"

**Symptoms**:
- YOLO visualization showed bounding boxes
- OCR-extracted values not appearing next to boxes
- Expected: "linear_dim: 50±0.1"
- Actual: Only "linear_dim (0.85)"

**Root Cause**:
Data structure mismatch in gateway-api/api_server.py
```python
# Lines 1893, 1957: Incorrect data access
dims_count = len(results[idx].get("data", {}).get("dimensions", []))
# But call_edocr2_ocr() returns edocr_data directly
```

**Fix Applied**:
```python
# Removed nested "data" key access
dims_count = len(results[idx].get("dimensions", []))
ocr_dimensions = ocr_results_data.get("dimensions", [])
```

**Verification**:
- ✅ Logs showed "eDOCr2 완료: 6개 치수 추출"
- ✅ Matching YOLO detections with OCR dimensions working
- ✅ Visualization shows OCR values correctly

**Location**:
- gateway-api/api_server.py:1893
- gateway-api/api_server.py:1957

**Lessons Learned**:
- Always verify data structure before accessing nested keys
- Test with real data, not just mock responses
- User feedback critical for catching integration issues

---

### Issue #R002: Pydantic Validation Error on OCR Tables Field ✅

**Status**: ✅ **RESOLVED** (2025-11-19)
**Severity**: Critical → Resolved
**Component**: Gateway API
**Discovered**: 2025-11-19 01:40 (during testing)
**Resolved**: 2025-11-19 01:42
**Resolution Time**: ~2 minutes

**Symptoms**:
```python
fastapi.exceptions.ResponseValidationError: 1 validation errors:
  {'type': 'dict_type',
   'loc': ('response', 'data', 'ocr_results', 'tables', 0),
   'msg': 'Input should be a valid dictionary',
   'input': [{...}, {...}]}
```

**Root Cause**:
Pydantic model definition mismatch
```python
# gateway-api/models/response.py:49
# Defined as:
tables: List[Dict[str, Any]] = Field(...)

# But eDOCr2 returns:
[[{...}, {...}], [{...}]]  # List of lists!
```

**Fix Applied**:
```python
# Changed to flexible type
tables: List[Any] = Field(default=[], description="테이블 데이터 (nested structure)")
```

**Verification**:
- ✅ Gateway API test passed
- ✅ Processing time: 18.9s (normal)
- ✅ All pipeline components working

**Location**:
- gateway-api/models/response.py:49

**Lessons Learned**:
- Don't assume API response structures
- Use flexible types (`Any`) for variable structures
- Test with real API responses, not mocked data

---

## 🎯 Issue Resolution Workflow

### When User Reports "안된다" (It doesn't work)

**Immediate Actions**:
1. ✅ Acknowledge issue in response
2. ✅ Add to KNOWN_ISSUES.md with details
3. ✅ Investigate root cause
4. ✅ Document symptoms and error messages
5. ✅ Create reproduction steps
6. ✅ Identify affected components

**During Investigation**:
1. ✅ Check relevant logs
2. ✅ Review recent code changes
3. ✅ Test in isolation
4. ✅ Identify root cause
5. ✅ Document findings

**After Fix**:
1. ✅ Apply fix
2. ✅ Verify with original test case
3. ✅ Update KNOWN_ISSUES.md status
4. ✅ Document resolution
5. ✅ Add to lessons learned

### When User Reports "잘된다" (It works)

**Immediate Actions**:
1. ✅ Mark related issue as RESOLVED
2. ✅ Document resolution time
3. ✅ Update ROADMAP.md with [x]
4. ✅ Capture success metrics
5. ✅ Document what worked

**Follow-up**:
1. ✅ Add regression test
2. ✅ Document in verification report
3. ✅ Update user-facing docs

---

## 📈 Issue Metrics

### Resolution Time

| Priority | Target | Average | Best |
|----------|--------|---------|------|
| Critical | <1 hour | 2 min | 2 min |
| High | <4 hours | 45 min | 30 min |
| Medium | <1 day | 9 hours | 9 hours |
| Low | <1 week | - | - |

### Resolution Rate

| Period | Opened | Resolved | Rate |
|--------|--------|----------|------|
| 2025-11-18 | 1 | 1 | 100% |
| 2025-11-19 | 3 | 3 | 100% |
| 2025-11-20 | 1 | 1 | 100% |
| **Total** | **5** | **5** | **100%** |

---

## 🔍 Common Problems & Quick Fixes

### "EDGNet 컴포넌트가 0개로 나와요"
**Quick Check**:
```bash
# Check EDGNet API response structure
docker logs edgnet-api | grep "components"

# Check if class_id field exists
curl http://localhost:5012/api/v1/health

# Verify Gateway is extracting nested data correctly
docker logs gateway-api | grep "segmentation_results"

# Common fix: Check class_id field and total_components field
# See Issue #R004 resolution
```

### "바운딩박스 옆에 값이 안나와요"
**Quick Check**:
```bash
# Check if OCR is returning data
docker logs gateway-api | grep "eDOCr2 완료"

# Should see: "eDOCr2 완료: N개 치수 추출"
# If N=0, check data structure access
```

### "API가 500 error를 반환해요"
**Quick Check**:
```bash
# Check Pydantic validation errors
docker logs gateway-api | grep "ResponseValidationError"

# Look for 'dict_type', 'list_type' errors
# Check model definitions in models/response.py
```

### "Container가 unhealthy해요"
**Quick Check**:
```bash
# Check container status
docker ps | grep unhealthy

# Check logs
docker logs <container-name> --tail 50

# Check health endpoint
curl http://localhost:<port>/api/v1/health

# Common fix: Check PYTHONPATH and remove workers
# See Issue #H001 resolution
```

### "샘플 파일이 안보여요"
**Quick Check**:
```bash
# Check which component is being used
grep "FileUploader\|FileDropzone" web-ui/src/pages/test/*.tsx

# Should use FileUploader for built-in samples:
# import FileUploader from '../../components/debug/FileUploader';

# If using FileDropzone, revert to FileUploader
# See Issue #R003 resolution
```

---

## 📝 Issue Template

When reporting new issues, use this template:

```markdown
### Issue #X: [Title]

**Status**: 🟠 OPEN
**Severity**: [Critical/High/Medium/Low]
**Component**: [API name]
**Discovered**: [Date]
**Reported By**: [User/System]

**Symptoms**:
- [What's happening]
- [Error messages]
- [Expected vs Actual behavior]

**Impact**:
- [Who/what is affected]
- [Severity of impact]

**Root Cause**: [If known]

**Workaround**: [Temporary solution]

**Investigation Steps**:
1. [ ] Step 1
2. [ ] Step 2

**Related**:
- Files: [paths]
- Issues: [links]

**Notes**:
- [Additional context]
```

---

## 🔗 Related Documents

- [ROADMAP.md](ROADMAP.md) - Project roadmap with issue tracking
- [COMPREHENSIVE_TEST_REPORT.md](COMPREHENSIVE_TEST_REPORT.md) - Test results
- [FEATURE_REGRESSION_ANALYSIS.md](FEATURE_REGRESSION_ANALYSIS.md) - Feature regression root cause analysis
- [CLAUDE.md](CLAUDE.md) - Main project guide

---

**Maintained By**: Claude Code (Sonnet 4.5)
**Update Frequency**: Real-time (as issues occur/resolve)
**Review Frequency**: Daily
