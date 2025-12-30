# 커밋 분석 후 일관성 작업 (2025-12-31)

> **목적**: 최근 6개 커밋(595b281~8ad36ab) 분석 후 발견된 일관성 문제 해결
> **작성자**: Claude Code (Opus 4.5)
> **우선순위**: P0(긴급) > P1(중요) > P2(권장) > P3(선택)

---

## 분석된 커밋 (6개)

| 해시 | 설명 |
|------|------|
| 595b281 | fix: gateway-api registry 테스트 httpx 0.28+ 호환성 수정 |
| 078b6d8 | fix: test_pid_features_api.py 검증 큐 테스트 수정 |
| 91e8570 | fix: P2 Feature 의존성 누락 수정 (sectionConfig.ts) |
| b74fb63 | fix: P1 일관성 작업 완료 - 테스트/Feature 정의 수정 |
| d2145ed | docs: P0 Dockerfile 작업 완료 표시 |
| 8ad36ab | fix(dockerfile): 11개 API Dockerfile에 routers/services 명시적 COPY 추가 |

---

## 요약

| 카테고리 | 항목 수 | 우선순위 | 상태 |
|----------|---------|----------|------|
| featureDefinitions.ts 동기화 | 6개 feature | P1 | ✅ 완료 |
| sectionConfig.ts 동기화 | 1개 파일 | P2 | 검토 필요 |
| edgnet_src/Dockerfile 패턴 | 1개 | P3 | 검토 필요 |

---

## 1. [P1] featureDefinitions.ts 동기화 누락

### 문제

`web-ui/src/config/features/featureDefinitions.ts`가 SSOT(Single Source of Truth)이며,
`blueprint-ai-bom/frontend/src/config/features/featureDefinitions.ts`와 동기화되어야 함.

현재 web-ui에는 있지만 blueprint-ai-bom에는 없는 항목들이 발견됨.

### 파일 비교

| 항목 | web-ui (SSOT) | blueprint-ai-bom |
|------|---------------|------------------|
| 파일 크기 | 571줄 | 484줄 |
| Features 수 | 22개 | 16개 |
| TECHCROSS 그룹 | ✅ 존재 | ❌ 누락 |

### 누락된 FEATURE_GROUPS

```typescript
// blueprint-ai-bom에 추가 필요
export const FEATURE_GROUPS = {
  BASIC_DETECTION: '기본 검출',
  GDT_MECHANICAL: 'GD&T / 기계',
  PID: 'P&ID',
  TECHCROSS: 'TECHCROSS BWMS',  // ❌ 누락
  BOM_GENERATION: 'BOM 생성',
  LONG_TERM: '장기 로드맵',
} as const;
```

### 누락된 Features (6개)

| Feature Key | 그룹 | 라벨 | implementationStatus |
|-------------|------|------|---------------------|
| industry_equipment_detection | P&ID | 장비 태그 인식 | implemented |
| equipment_list_export | P&ID | 장비 목록 내보내기 | implemented |
| techcross_valve_signal | TECHCROSS | Valve Signal List | implemented |
| techcross_equipment | TECHCROSS | Equipment List | implemented |
| techcross_checklist | TECHCROSS | BWMS Checklist | implemented |
| techcross_deviation | TECHCROSS | Deviation List | planned |

### 수정 방법

1. `web-ui/src/config/features/featureDefinitions.ts` 전체 내용을 복사
2. `blueprint-ai-bom/frontend/src/config/features/featureDefinitions.ts`에 붙여넣기
3. 또는 diff 도구로 누락된 부분만 추가

### 작업 체크리스트 (2025-12-31 완료)

- [x] FEATURE_GROUPS에 TECHCROSS 그룹 추가 ✅
- [x] P&ID 그룹에 industry_equipment_detection 추가 ✅
- [x] P&ID 그룹에 equipment_list_export 추가 ✅
- [x] TECHCROSS 그룹에 4개 features 추가 ✅
  - [x] techcross_valve_signal ✅
  - [x] techcross_equipment ✅
  - [x] techcross_checklist ✅
  - [x] techcross_deviation ✅
- [x] 빌드 확인: `cd blueprint-ai-bom/frontend && npm run build` ✅

---

## 2. [P2] sectionConfig.ts 동기화 검토

### 문제

`blueprint-ai-bom/frontend/src/pages/workflow/config/sectionConfig.ts`에는
FEATURE_DEPENDENCIES와 FEATURE_ALIASES가 정의되어 있음.

이 파일이 web-ui의 어떤 파일과 대응되는지 확인 필요.

### 현재 상태

blueprint-ai-bom sectionConfig.ts에 정의된 의존성:
- TECHCROSS features 의존성 포함
- FEATURE_ALIASES에 techcross_* → pid_* 매핑 포함

### 확인 사항

- [ ] web-ui에 동일한 의존성 정의 파일이 있는지 확인
- [ ] 있다면 동기화 상태 검토
- [ ] 없다면 blueprint-ai-bom 전용으로 유지

---

## 3. [P3] edgnet_src/Dockerfile COPY 패턴

### 문제

`models/edgnet-api/edgnet_src/Dockerfile`에서 `COPY . .` 패턴 사용 중.
다른 API들은 명시적 COPY를 사용하도록 수정됨.

### 분석

```dockerfile
# models/edgnet-api/edgnet_src/Dockerfile:28
COPY . .
```

### 결론

이 Dockerfile은 **pipeline 테스트용**으로, API 서버용이 아님:
- `CMD ["python", "pipeline.py", "--help"]`

**메인 API Dockerfile**(`models/edgnet-api/Dockerfile`)은 이미 명시적 COPY 사용 중:
```dockerfile
COPY api_server.py .
COPY routers/ ./routers/
COPY models/ ./models/
COPY services/ ./services/
COPY utils/ ./utils/
```

### 조치

- [ ] 선택적: edgnet_src/Dockerfile도 명시적 COPY로 변경 (일관성)
- [x] API 서버 Dockerfile은 이미 수정됨 - 조치 불필요

---

## 4. [P3] 테스트 스위트 현황

### gateway-api 테스트 (141개 통과)

| 테스트 파일 | 수량 | 상태 |
|-------------|------|------|
| test_registry_endpoints.py | 13개 | ✅ 통과 (httpx 0.28+ 호환성 수정) |
| 기타 테스트 | 128개 | ✅ 통과 |

주요 수정:
- starlette.TestClient → httpx.ASGITransport 변경
- 모든 테스트 async로 변환
- pytest-asyncio 마커 추가

### blueprint-ai-bom 테스트 (98개 통과)

| 테스트 파일 | 수량 | 상태 |
|-------------|------|------|
| test_pid_features_api.py | 30개 | ✅ 통과 (422 응답 허용 추가) |
| 기타 테스트 | 68개 | ✅ 통과 |

### web-ui 테스트 (141개 통과)

모든 프론트엔드 테스트 통과.

---

## 5. [P2] 이전 일관성 작업 완료 확인

### 2025-12-30 작업 (완료됨)

`.todos/2025-12-30_post_pid_features_consistency.md` 참조:

| 카테고리 | 상태 |
|----------|------|
| Dockerfile routers/services COPY | ✅ 완료 |
| pid_features_router.py 테스트 | ✅ 완료 |
| Feature 정의 implementationLocation 수정 | ✅ 완료 |
| Feature 의존성 추가 | ✅ 완료 |
| usePIDFeaturesHandlers 훅 사용 확인 | ✅ 완료 |

---

## 실행 순서 권장

1. **이번 주 (P1)**: featureDefinitions.ts 동기화 (6개 feature 추가)
2. **다음 주 (P2)**: sectionConfig.ts 동기화 검토
3. **향후 (P3)**: edgnet_src/Dockerfile 패턴 일관성 (선택적)

---

## 관련 파일

### 동기화 필요 (web-ui → blueprint-ai-bom)

| web-ui (SSOT) | blueprint-ai-bom (대상) |
|---------------|------------------------|
| `src/config/features/featureDefinitions.ts` | `frontend/src/config/features/featureDefinitions.ts` |

### 테스트 파일 (수정됨)

| 파일 | 수정 내용 |
|------|----------|
| `gateway-api/tests/conftest.py` | httpx.ASGITransport 사용 |
| `gateway-api/tests/test_registry_endpoints.py` | async 변환 |
| `blueprint-ai-bom/backend/tests/test_pid_features_api.py` | 422 응답 허용 |

---

**마지막 업데이트**: 2025-12-31 (분석 완료)
