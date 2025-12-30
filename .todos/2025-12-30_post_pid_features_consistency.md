# PID Features 커밋 이후 일관성 작업 (2025-12-30)

> **목적**: 최근 6개 커밋(b22f9e1~7bfaf9a) 분석 후 발견된 일관성 문제 해결
> **작성자**: Claude Code (Opus 4.5)
> **우선순위**: P0(긴급) > P1(중요) > P2(권장) > P3(선택)

---

## 요약

| 카테고리 | 항목 수 | 우선순위 | 상태 |
|----------|---------|----------|------|
| Dockerfile 일관성 | 11개 API | P0 | ✅ 완료 |
| 테스트 커버리지 | 4개 라우터 | P1 | ✅ 완료 |
| Feature 정의 불일치 | 5개 항목 | P1 | ✅ 완료 |
| usePIDFeaturesHandlers 훅 사용 | 1개 | P1 | ✅ 완료 |
| Feature 의존성 누락 | 5개 feature | P2 | ✅ 완료 |

---

## 1. [P0] Dockerfile routers/ COPY 누락 (11개 API)

### 문제
`routers/` 디렉토리가 있지만 Dockerfile에서 COPY하지 않는 API가 11개 존재.
Docker 이미지 빌드 시 routers가 포함되지 않아 런타임 에러 발생 가능.

### 영향받는 API

| API | routers/ 존재 | COPY 여부 | 수정 필요 |
|-----|--------------|-----------|----------|
| design-checker-api | ✅ | ❌ | **필요** |
| doctr-api | ✅ | ❌ | **필요** |
| easyocr-api | ✅ | ❌ | **필요** |
| esrgan-api | ✅ | ❌ | **필요** |
| knowledge-api | ✅ | ❌ | **필요** |
| line-detector-api | ✅ | ❌ | **필요** |
| ocr-ensemble-api | ✅ | ❌ | **필요** |
| pid-analyzer-api | ✅ | ❌ | **필요** |
| surya-ocr-api | ✅ | ❌ | **필요** |
| tesseract-api | ✅ | ❌ | **필요** |
| trocr-api | ✅ | ❌ | **필요** |

### 수정 패턴

```dockerfile
# Dockerfile에 추가 (api_server.py COPY 전에)
COPY routers/ /app/routers/
COPY services/ /app/services/  # services가 있는 경우
```

### 작업 체크리스트 (2025-12-30 완료)

- [x] design-checker-api Dockerfile 수정 ✅
- [x] doctr-api Dockerfile 수정 ✅
- [x] easyocr-api Dockerfile 수정 ✅
- [x] esrgan-api Dockerfile 수정 ✅
- [x] knowledge-api Dockerfile 수정 ✅
- [x] line-detector-api Dockerfile 수정 ✅
- [x] ocr-ensemble-api Dockerfile 수정 ✅
- [x] pid-analyzer-api Dockerfile 수정 ✅
- [x] surya-ocr-api Dockerfile 수정 ✅
- [x] tesseract-api Dockerfile 수정 ✅
- [x] trocr-api Dockerfile 수정 ✅

---

## 2. [P0] Dockerfile services/ COPY 누락 (10개 API)

### 문제
`services/` 디렉토리가 있지만 Dockerfile에서 COPY하지 않는 API가 10개 존재.

### 영향받는 API

| API | services/ 존재 | COPY 여부 | 수정 필요 |
|-----|---------------|-----------|----------|
| doctr-api | ✅ | ❌ | **필요** |
| easyocr-api | ✅ | ❌ | **필요** |
| esrgan-api | ✅ | ❌ | **필요** |
| knowledge-api | ✅ | ❌ | **필요** |
| line-detector-api | ✅ | ❌ | **필요** |
| ocr-ensemble-api | ✅ | ❌ | **필요** |
| pid-analyzer-api | ✅ | ❌ | **필요** |
| surya-ocr-api | ✅ | ❌ | **필요** |
| tesseract-api | ✅ | ❌ | **필요** |
| trocr-api | ✅ | ❌ | **필요** |

### 작업 체크리스트 (2025-12-30 완료)

- [x] 위 API들의 Dockerfile에 `COPY services/ /app/services/` 추가 ✅

---

## 3. [P1] pid_features_router.py 테스트 누락

### 문제
새로 추가된 `blueprint-ai-bom/backend/routers/pid_features_router.py` (1,101줄)에 대한 테스트가 없음.
다른 라우터(longterm_router.py)는 테스트가 있음.

### 테스트 필요 엔드포인트

```
POST /{session_id}/valve/detect         # Valve Signal List 검출
POST /{session_id}/equipment/detect     # Equipment List 검출
POST /{session_id}/checklist/check      # BWMS Checklist 검증
POST /{session_id}/deviation/analyze    # Deviation 분석
GET  /{session_id}/verify/queue         # 검증 큐 조회
POST /{session_id}/verify               # 단일 항목 검증
POST /{session_id}/verify/bulk          # 대량 검증
POST /{session_id}/export               # Excel 내보내기
```

### 작업 체크리스트 (2025-12-30 완료)

- [x] `tests/test_pid_features_api.py` 생성 ✅
- [x] Valve Signal 검출 테스트 작성 ✅
- [x] Equipment 검출 테스트 작성 ✅
- [x] Checklist 검증 테스트 작성 ✅
- [x] Deviation 분석 테스트 작성 ✅
- [x] 검증 큐/워크플로우 테스트 작성 ✅
- [x] Export 테스트 작성 ✅

---

## 4. [P1] Feature 정의 불일치 (web-ui ↔ blueprint-ai-bom)

### 문제
`web-ui/src/config/features/featureDefinitions.ts`의 `implementationLocation` 필드가
실제 파일명과 불일치.

### 불일치 항목

| Feature Key | implementationLocation (현재) | 실제 파일 | 수정 필요 |
|-------------|------------------------------|-----------|----------|
| techcross_valve_signal | `blueprint-ai-bom/techcross_router.py` | `pid_features_router.py` | **필요** |
| techcross_equipment | `blueprint-ai-bom/techcross_router.py` | `pid_features_router.py` | **필요** |
| techcross_checklist | `blueprint-ai-bom/techcross_router.py` | `pid_features_router.py` | **필요** |
| techcross_deviation | `blueprint-ai-bom/techcross_router.py (향후 구현)` | `pid_features_router.py` | **필요** |
| industry_equipment_detection | `pid-analyzer-api/equipment_analyzer.py` | (확인 필요) | 검토 |

### 작업 체크리스트 (2025-12-30 완료)

- [x] featureDefinitions.ts의 implementationLocation 필드 수정 ✅
  - `techcross_*` → `blueprint-ai-bom/routers/pid_features_router.py`
- [x] 동기화 대상 확인: blueprint-ai-bom에 동일 파일 존재 여부 ✅

---

## 5. [P2] Feature 의존성 누락 (sectionConfig.ts)

### 문제
일부 features에 의존성이 정의되지 않음. 사용자가 해당 feature를 선택해도
필수 의존성 없이 동작하여 혼란 초래 가능.

### 의존성 미정의 Features

| Feature | 필요한 의존성 (추정) | 현재 상태 |
|---------|---------------------|----------|
| industry_equipment_detection | `symbol_detection` 또는 `pid_connectivity` | ✅ 추가됨 |
| equipment_list_export | `industry_equipment_detection` | ✅ 추가됨 |
| gt_comparison | `symbol_detection` | ✅ 추가됨 |
| bom_generation | `symbol_detection` | ✅ 추가됨 |
| title_block_ocr | (없음 - 독립 기능) | OK |
| quantity_extraction | `dimension_ocr` | ✅ 추가됨 |

### 추가된 의존성 (2025-12-30)

```typescript
// sectionConfig.ts의 FEATURE_DEPENDENCIES에 추가됨
industry_equipment_detection: { requiresAtLeastOne: ['symbol_detection', 'pid_connectivity'] },
equipment_list_export: { requires: ['industry_equipment_detection'] },
gt_comparison: { requires: ['symbol_detection'] },
bom_generation: { requires: ['symbol_detection'] },
quantity_extraction: { requires: ['dimension_ocr'] },
```

### 작업 체크리스트 (2025-12-30 완료)

- [x] FEATURE_DEPENDENCIES에 위 의존성 추가 ✅
- [x] 의존성 추가 후 빌드 확인 ✅

---

## 6. [P2] API 테스트 디렉토리 일관성

### 현재 상태

| 디렉토리 | tests/ 존재 | 테스트 수 |
|----------|-------------|----------|
| models/line-detector-api | ✅ | 16개 |
| models/pid-analyzer-api | ✅ | 446줄 (신규) |
| blueprint-ai-bom/backend | ✅ | 74개 |
| 기타 15개 API | ❌ | 0 |

### 권장 사항

P3 우선순위로 점진적 테스트 추가:
1. yolo-api (핵심 검출)
2. edocr2-v2-api (핵심 OCR)
3. design-checker-api (BWMS 검증)

---

## 7. [P3] BWMS Rules 동기화 검토

### 문제
`design-checker-api/bwms_rules.py`와 `pid-analyzer-api/region_rules.yaml`에
BWMS 관련 규칙이 별도로 존재. 규칙 변경 시 양쪽 동기화 필요.

### 현재 구조

```
design-checker-api/
├── bwms_rules.py          # Python 기반 BWMS 규칙 (209줄 추가됨)
└── rule_loader.py         # YAML 기반 동적 규칙

pid-analyzer-api/
├── region_rules.yaml      # 영역 추출 규칙 (35줄 추가됨)
└── region_extractor.py    # 영역 추출 로직 (221줄 추가됨)
```

### 검토 필요 사항

- [ ] bwms_rules.py와 region_rules.yaml 간 규칙 중복 여부 확인
- [ ] 규칙 SSOT(Single Source of Truth) 결정
- [ ] 향후 규칙 변경 시 동기화 프로세스 문서화

---

## 8. [P1] usePIDFeaturesHandlers.ts 훅 미사용 확인

### 문제
새로 추가된 `usePIDFeaturesHandlers.ts` (356줄)가 WorkflowPage.tsx에서
실제로 사용되는지 확인 필요.

### 확인 사항

```typescript
// WorkflowPage.tsx에서 import 및 사용 확인
import { usePIDFeaturesHandlers } from './workflow';

// 실제 호출 확인
const pidHandlers = usePIDFeaturesHandlers(sessionId, ...);
```

### 작업 체크리스트 (2025-12-30 완료)

- [x] WorkflowPage.tsx에서 usePIDFeaturesHandlers 사용 여부 확인 ✅
  - `WorkflowPage.tsx:39`에서 import됨
  - `WorkflowPage.tsx:108`에서 `const pidFeatures = usePIDFeaturesHandlers();`로 호출됨
- [x] 미사용 시 PIDFeaturesSection에 연결 → 정상 사용 중으로 확인됨 ✅

---

## 실행 순서 권장

1. **즉시 (P0)**: Dockerfile routers/services COPY 수정 (빌드 실패 방지)
2. **이번 주 (P1)**: pid_features_router.py 테스트 작성, Feature 정의 수정
3. **다음 주 (P2)**: Feature 의존성 추가, BWMS 규칙 검토
4. **향후 (P3)**: 기타 API 테스트 추가

---

## 관련 커밋

| 해시 | 설명 |
|------|------|
| b22f9e1 | feat: PID Features 워크플로우 및 Feature 의존성 검증 시스템 |
| b92672d | feat: PID Analyzer texts/regions 통합 및 BWMS 규칙 확장 |
| 138c3c3 | fix: edgnet-api 및 vl-api Dockerfile/import 수정 |
| f935cad | docs: 프로젝트 아키텍처 개요 및 향후 작업 권장사항 문서 추가 |
| 0584637 | fix: edocr2-v2-api Dockerfile.gpu에 routers/ COPY 추가 |
| 7bfaf9a | fix: Dockerfile에 routers/, schemas.py COPY 추가 |

---

**마지막 업데이트**: 2025-12-30 23:30 KST
