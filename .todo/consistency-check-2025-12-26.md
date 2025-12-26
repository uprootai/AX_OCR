# Blueprint AI BOM - 일관성 검토 및 작업 목록

> 생성일: 2025-12-26
> 목적: git status 변경사항 분석 및 코드베이스 일관성 검토
> 우선순위: High (P1), Medium (P2), Low (P3)

---

## 1. 변경사항 요약 (마지막 커밋 대비)

### 1.1 수정된 파일

| 파일 | 변경 유형 | 핵심 변경 내용 |
|------|----------|---------------|
| `blueprint-ai-bom/backend/api_server.py` | 리팩토링 | analysis_router → 5개 모듈 패키지로 분할 |
| `blueprint-ai-bom/frontend/src/pages/WorkflowPage.tsx` | 대규모 리팩토링 | 4447줄 삭제, 443줄 추가 → 섹션별 컴포넌트로 분리 |
| `blueprint-ai-bom/backend/routers/__init__.py` | 수정 | 삭제된 analysis_router.py 대신 analysis 패키지 import |

### 1.2 신규 생성 파일 (Untracked)

| 디렉토리/파일 | 목적 |
|--------------|------|
| `backend/routers/analysis/` | analysis_router.py를 5개 모듈로 분할 |
| `├── __init__.py` | 패키지 초기화 및 export |
| `├── core_router.py` | 프리셋, 옵션, 분석 실행 |
| `├── dimension_router.py` | 치수 관리 API |
| `├── line_router.py` | 선 검출, 연결성 분석 |
| `├── region_router.py` | 영역 분할 (Phase 5) |
| `└── gdt_router.py` | GD&T 파싱, 표제란 OCR |
| `backend/routers/midterm_router.py` | 중기 로드맵 API (용접, 거칠기, 수량, 벌룬) |
| `backend/routers/longterm_router.py` | 장기 로드맵 API (영역, 노트, 리비전, VLM) |
| `frontend/src/pages/workflow/` | WorkflowPage.tsx 모듈화 |
| `├── index.ts` | export |
| `├── components/` | 공통 컴포넌트 |
| `├── sections/` | 17개 섹션 컴포넌트 |
| `├── config/` | 설정 |
| `├── hooks/` | 커스텀 훅 |
| `└── types/` | TypeScript 타입 |

### 1.3 삭제된 파일

| 파일 | 대체 |
|------|-----|
| `backend/routers/analysis_router.py` | `backend/routers/analysis/` 패키지 |

---

## 2. 일관성 문제 (Consistency Issues)

### 2.1 [P1] Features 아이콘 불일치

세 곳에서 동일한 feature의 아이콘이 다름:

| Feature | inputNodes.ts (BOM_FEATURES) | inputNodes.ts (checkboxGroup) | ActiveFeaturesSection.tsx |
|---------|------------------------------|-------------------------------|---------------------------|
| `gdt_parsing` | 📐 | 🔧 | 📐 |
| `pid_connectivity` | 🔗 | 🔀 | 🔗 |
| `welding_symbol_parsing` | 🔩 | ⚡ | ⚡ |

**작업 필요**:
1. 아이콘 표준 정의 (어느 것을 기준으로 할지 결정)
2. 세 곳 모두 동기화

**권장 표준**:
```
gdt_parsing: 📐 (기하공차 아이콘으로 적합)
pid_connectivity: 🔀 (연결/분기 의미로 적합)
welding_symbol_parsing: ⚡ (용접 = 에너지/열 연상)
```

### 2.2 [P1] Features 키 이름 불일치

| 위치 | 키 이름 | 문제 |
|------|--------|-----|
| inputNodes.ts BOM_FEATURES | `welding_symbol_parsing` | O |
| ActiveFeaturesSection.tsx | `welding_symbol` + `welding_symbol_parsing` | 중복! |
| inputNodes.ts BOM_FEATURES | `surface_roughness_parsing` | O |
| ActiveFeaturesSection.tsx | `surface_roughness` + `surface_roughness_parsing` | 중복! |

**작업 필요**:
1. `welding_symbol` → 삭제 또는 `welding_symbol_parsing`으로 통일
2. `surface_roughness` → 삭제 또는 `surface_roughness_parsing`으로 통일

### 2.3 [P2] bomNodes.ts features 누락

`bomNodes.ts`의 features 옵션에서 누락된 항목:

```typescript
// inputNodes.ts에는 있지만 bomNodes.ts에는 없음:
- symbol_verification      // 심볼 검증
- dimension_verification   // 치수 검증
- gt_comparison           // GT 비교
- bom_generation          // BOM 생성 (자기 자신 노드의 기능인데 없음!)
- drawing_region_segmentation  // 영역 세분화
- notes_extraction        // 노트 추출
- revision_comparison     // 리비전 비교
- vlm_auto_classification // VLM 자동 분류
```

**작업 필요**:
1. bomNodes.ts에 누락된 8개 features 추가
2. 또는 bomNodes.ts 목적 재정의 (왜 다른지 명시)

### 2.4 [P2] relation_extraction 위치 불일치

| 위치 | 존재 여부 |
|------|----------|
| inputNodes.ts BOM_FEATURES | X (없음) |
| inputNodes.ts checkboxGroup | X (없음) |
| bomNodes.ts features | O (있음) |
| ActiveFeaturesSection.tsx | O (있음) |

**결정 필요**:
- `relation_extraction`을 inputNodes.ts에 추가할 것인가?
- 아니면 bomNodes.ts에서만 사용하는 것으로 유지?

### 2.5 [P2] BOM_FEATURES vs checkboxGroup 불일치

`inputNodes.ts` 내부에서도 불일치:

```typescript
// BOM_FEATURES (line 16-38)
gdt_parsing: { label: 'GD&T 파싱', icon: '📐' }

// checkboxGroup options (line 163)
{ value: 'gdt_parsing', label: 'GD&T 파싱', icon: '🔧', ... }
```

**작업 필요**:
1. BOM_FEATURES 상수 사용 여부 재검토
2. checkboxGroup에서 BOM_FEATURES를 참조하도록 리팩토링 또는
3. BOM_FEATURES 삭제하고 checkboxGroup만 사용

### 2.6 [P3] Group 이름 표준화

| Group | inputNodes.ts | bomNodes.ts |
|-------|--------------|-------------|
| 기본 | '기본 검출' | '기본 검출' |
| 기계 | 'GD&T / 기계' | 'GD&T / 기계' |
| P&ID | 'P&ID' | 'P&ID' |
| BOM | 'BOM 생성' | 'BOM 생성' |
| 장기 | '장기 로드맵' | (누락) |

**작업 필요**:
1. bomNodes.ts에 '장기 로드맵' 그룹 추가

---

## 3. 코드 품질 작업

### 3.1 [P1] 삭제된 파일 정리

```bash
# 삭제된 파일이 git에서 여전히 'D' 상태
git rm blueprint-ai-bom/backend/routers/analysis_router.py
```

### 3.2 [P2] 신규 파일 git add

```bash
# Untracked 파일들 추가
git add blueprint-ai-bom/backend/routers/analysis/
git add blueprint-ai-bom/backend/routers/midterm_router.py
git add blueprint-ai-bom/backend/routers/longterm_router.py
git add blueprint-ai-bom/frontend/src/pages/workflow/
```

### 3.3 [P2] routers/__init__.py 업데이트

현재 `__init__.py`에 `midterm_router`, `longterm_router` export 누락:

```python
# 추가 필요:
from .midterm_router import router as midterm_router
from .longterm_router import router as longterm_router

__all__ = [
    ...
    "midterm_router",
    "longterm_router",
]
```

---

## 4. 작업 체크리스트

### Phase 1: 긴급 수정 (P1)

- [ ] 아이콘 표준 결정 및 3곳 동기화
  - [ ] inputNodes.ts BOM_FEATURES
  - [ ] inputNodes.ts checkboxGroup
  - [ ] ActiveFeaturesSection.tsx FEATURE_CONFIG
- [ ] welding_symbol / surface_roughness 키 이름 통일
- [ ] 삭제된 analysis_router.py git rm 처리

### Phase 2: 일관성 개선 (P2)

- [ ] bomNodes.ts에 누락된 8개 features 추가
- [ ] relation_extraction 위치 결정
- [ ] BOM_FEATURES 상수 활용 여부 결정
- [ ] routers/__init__.py에 midterm/longterm 라우터 추가
- [ ] 신규 파일 git add

### Phase 3: 리팩토링 (P3)

- [ ] inputNodes.ts에서 BOM_FEATURES → checkboxGroup 참조로 리팩토링
- [ ] Group 이름 상수화 (GROUP_NAMES enum)
- [ ] features 정의 단일 소스 (Single Source of Truth) 구축

---

## 5. 권장 최종 아이콘 표준

```typescript
const FEATURE_ICONS = {
  // 기본 검출
  symbol_detection: '🎯',
  symbol_verification: '✅',
  dimension_ocr: '📏',
  dimension_verification: '✅',
  gt_comparison: '📊',

  // GD&T / 기계
  gdt_parsing: '📐',           // 기하공차 → 삼각자
  line_detection: '📐',
  welding_symbol_parsing: '⚡', // 용접 → 에너지
  surface_roughness_parsing: '🔲',
  relation_extraction: '🔗',

  // P&ID
  pid_connectivity: '🔀',       // 연결 → 분기 화살표

  // BOM 생성
  bom_generation: '📋',
  title_block_ocr: '📝',
  quantity_extraction: '🔢',
  balloon_matching: '🎈',

  // 장기 로드맵
  drawing_region_segmentation: '🗺️',
  notes_extraction: '📋',
  revision_comparison: '🔄',
  vlm_auto_classification: '🤖',
};
```

---

## 6. 참고 파일 경로

| 파일 | 역할 |
|------|------|
| `web-ui/src/config/nodes/inputNodes.ts` | ImageInput 노드 features 정의 (빌더) |
| `web-ui/src/config/nodes/bomNodes.ts` | Blueprint AI BOM 노드 features 정의 (빌더) |
| `blueprint-ai-bom/frontend/src/pages/workflow/sections/ActiveFeaturesSection.tsx` | 워크플로우 페이지 배지 표시 |
| `blueprint-ai-bom/backend/routers/__init__.py` | 백엔드 라우터 export |
| `blueprint-ai-bom/backend/api_server.py` | 백엔드 라우터 등록 |

---

**작성자**: Claude Code (Opus 4.5)
**다음 작업**: Phase 1 긴급 수정 진행
