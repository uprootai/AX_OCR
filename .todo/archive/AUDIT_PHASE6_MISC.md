# Phase 6: 기타 조사 결과

> **조사일**: 2026-01-17
> **총 용량**: 222MB
> **디렉토리 수**: 4개

---

## 요약

| 디렉토리 | 용량 | 판정 | 조치 |
|----------|------|------|------|
| `.todo/` | 168KB | ✅ 유지 | 현재 사용 중인 TODO 시스템 |
| `.todos/` | 300KB | ⚠️ 검토 | 레거시 TODO (2025-12-31 이후 미사용) |
| `apply-company/` | 52MB | ✅ 유지 | 회사 지원 자료 + E2E 테스트 의존 |
| `.git/` | 170MB | ✅ 유지 | Git 저장소 (gc 권장) |

---

## 1. .todo/ (168KB)

### 기본 정보

| 항목 | 값 |
|------|-----|
| 경로 | `/home/uproot/ax/poc/.todo/` |
| 용량 | 168KB |
| 최종 수정 | 2026-01-17 (활발) |
| 파일 수 | 7개 + archive 폴더 |

### 구조

```
.todo/
├── ACTIVE.md                # 현재 진행 중인 작업
├── BACKLOG.md               # 백로그
├── COMPLETED.md             # 완료된 작업
├── DIRECTORY_AUDIT_PLAN.md  # 현재 진행 중 (이 감사)
├── AUDIT_PHASE4_DATA.md     # Phase 4 결과
├── AUDIT_PHASE5_TEMP.md     # Phase 5 결과
└── archive/                 # 15개 아카이브 문서
    ├── 00_SUMMARY.md        # 요약
    ├── 01-10_*.md           # 기능별 계획
    ├── E2E_TESTS_ORGANIZATION.md
    ├── TOAST_MIGRATION_ANALYSIS.md
    └── UX_IMPROVEMENT_TOAST_LOADING.md
```

### 용도

- **목적**: 현재 사용 중인 TODO 관리 시스템
- **Git 추적**: ✅ 추적됨 (일부 파일)
- **참조**: Claude Code 세션에서 활발히 사용

### 판정

| 항목 | 판정 |
|------|------|
| **결론** | ✅ 유지 |
| **사유** | 현재 활발히 사용 중인 프로젝트 관리 시스템 |
| **비고** | archive 폴더에 완료된 계획 문서 보관 |

---

## 2. .todos/ (300KB) - 레거시

### 기본 정보

| 항목 | 값 |
|------|-----|
| 경로 | `/home/uproot/ax/poc/.todos/` |
| 용량 | 300KB |
| 최종 수정 | 2025-12-31 (17일 전) |
| 파일 수 | 9개 + archive 폴더 |

### 구조

```
.todos/
├── README.md
├── REMAINING_WORK_PLAN.md
├── 2025-12-31_*.md              # 3개 파일
├── TECHCROSS_*.md               # 3개 파일 (요구사항, 로드맵, Phase1)
└── archive/                     # 13개 아카이브
    ├── 2025-12-14_export_architecture.md
    ├── 2025-12-19_blueprint_ai_bom_*.md
    ├── 2025-12-24_*.md
    ├── 2025-12-29_*.md          # 4개 파일
    ├── 2025-12-30_*.md
    └── 2025-12-31_*.md          # 2개 파일
```

### 용도

- **목적**: 이전 TODO 시스템 (현재 `.todo/`로 대체됨)
- **Git 추적**: ✅ 추적됨
- **마지막 수정**: 2025-12-31 23:28

### 비교: .todo/ vs .todos/

| 항목 | .todo/ (현재) | .todos/ (레거시) |
|------|---------------|------------------|
| 용량 | 168KB | 300KB |
| 최종 수정 | 2026-01-17 | 2025-12-31 |
| 파일 명명 | 기능 기반 | 날짜 기반 |
| 상태 | 활발 | 미사용 |

### 판정

| 항목 | 판정 |
|------|------|
| **결론** | ⚠️ 검토 |
| **사유** | 17일간 미사용. `.todo/`로 완전 대체됨 |
| **조치** | 삭제 또는 `.todo/archive/legacy/`로 통합 고려 |

### 정리 옵션

1. **삭제**: 300KB 절감 (히스토리는 Git에 보존)
2. **통합**: `.todo/archive/legacy/`로 이동
3. **유지**: 참조용으로 보관

---

## 3. apply-company/ (52MB)

### 기본 정보

| 항목 | 값 |
|------|-----|
| 경로 | `/home/uproot/ax/poc/apply-company/` |
| 용량 | 52MB |
| 최종 수정 | 2026-01-11 |
| 하위 디렉토리 | techloss/ |

### 구조

```
apply-company/
└── techloss/                    # 52MB - TECHCROSS 회사 지원 자료
    ├── 2차 기술 미팅 자료 모음/     # 13MB - 미팅 자료
    ├── test_output/              # 9.7MB - 테스트 출력 (⚠️ E2E 의존)
    │   └── page_1.png            # E2E 테스트에서 참조
    ├── STANDARD/                 # 8.2MB - 표준 문서
    ├── ocr_test/                 # 7.5MB - OCR 테스트
    ├── output/                   # 7.0MB - 출력 결과
    ├── ECS 예시/                  # 3.0MB
    ├── about-email-details/      # 140KB
    ├── Equipment List 표준 파일/  # 44KB
    ├── *.md                      # 계획/분석 문서 (~312KB)
    ├── *.pdf                     # 1.3MB - 프레젠테이션
    └── *.pptx                    # 2.0MB - 프레젠테이션
```

### 용도

- **목적**: TECHCROSS 회사 지원 관련 자료
- **내용**:
  - 기술 미팅 자료
  - P&ID 분석 테스트 데이터
  - 개발 계획 및 로드맵
  - UI 계획 문서

### 참조 분석

**E2E 테스트에서 참조**:
```typescript
// blueprint-ai-bom.spec.ts, blueprint-ai-bom-comprehensive.spec.ts
const SAMPLE_PID_IMAGE = '/home/uproot/ax/poc/apply-company/techloss/test_output/page_1.png';
```

**R&D 스크립트에서 참조**:
- `rnd/experiments/doclayout_yolo/finetuning/scripts/prepare_data.py`
- `rnd/experiments/doclayout_yolo/finetuning/scripts/train.py`

### .gitignore 상태

```
apply-company/techloss/test_output/  # ✅ 무시됨
```

### 판정

| 항목 | 판정 |
|------|------|
| **결론** | ✅ 유지 |
| **사유** | E2E 테스트에서 직접 참조. 회사 지원 중요 자료 |
| **비고** | test_output/는 gitignore 처리됨 |

### 정리 가능 항목

- `output/` (7.0MB) - 테스트 결과물, 필요 시 삭제
- `ocr_test/` (7.5MB) - OCR 테스트 결과, 필요 시 삭제
- 총 ~14.5MB 절감 가능 (단, E2E 테스트 확인 필요)

---

## 4. .git/ (170MB)

### 기본 정보

| 항목 | 값 |
|------|-----|
| 경로 | `/home/uproot/ax/poc/.git/` |
| 용량 | 170MB |
| 총 커밋 | 74개 |
| 객체 수 | 6,574개 |

### 구조

```
.git/
├── objects/      # 170MB (99.9%) - Git 객체 저장소
├── logs/         # 68KB - 참조 로그
├── hooks/        # 64KB - Git 훅
├── refs/         # 28KB - 참조
├── info/         # 8KB - 설정
└── branches/     # 4KB
```

### Git 객체 분석

```
count: 6574        # 총 객체 수
size: 168.09 MiB   # 압축 전 크기
in-pack: 0         # 팩 파일 없음 ⚠️
packs: 0
garbage: 1
```

### 최적화 가능성

**현재 상태**: 모든 객체가 loose 상태 (압축되지 않음)

**권장 조치**:
```bash
git gc --aggressive
```

**예상 효과**: 170MB → ~50-80MB (50-70% 감소 예상)

### 판정

| 항목 | 판정 |
|------|------|
| **결론** | ✅ 유지 |
| **사유** | Git 저장소 필수 |
| **조치** | `git gc --aggressive` 실행 권장 (최대 100MB 절감 가능) |

---

## Phase 6 최종 요약

### 용량 분석

| 상태 | 용량 | 비율 |
|------|------|------|
| ✅ 필수 유지 | 222MB | 99.9% |
| ⚠️ 검토 (레거시) | 300KB | 0.1% |
| 🗑️ 삭제 가능 | 0 | 0% |

### 정리 가능 용량

| 항목 | 용량 | 조건 |
|------|------|------|
| `.todos/` | 300KB | 삭제 또는 아카이브 |
| `.git/` (gc 후) | ~100MB | `git gc --aggressive` |
| `apply-company/output/` | 14.5MB | E2E 확인 후 |

### 권장사항

1. **즉시 가능**:
   - `git gc --aggressive` 실행 (~100MB 절감)

2. **결정 필요**:
   - `.todos/` 처리 방안
     - 삭제: 300KB 절감 (Git 히스토리에 보존됨)
     - 통합: `.todo/archive/legacy/`로 이동

3. **주의 필요**:
   - `apply-company/techloss/test_output/page_1.png` - E2E 테스트 의존
   - 삭제 시 테스트 실패 가능

---

**다음**: Phase 1-3 조사 (핵심 코드, 설정, 문서)
