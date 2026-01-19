# Phase 5: 실험 및 임시 조사 결과

> **조사일**: 2026-01-17
> **총 용량**: 657MB
> **디렉토리 수**: 4개

---

## 📊 요약

| 디렉토리 | 용량 | 판정 | 조치 |
|----------|------|------|------|
| `experiments/` | 656MB | ⚠️ 검토 | 실험 코드/모델, 아카이브 후보 |
| `backend/` | 4KB | 🗑️ 삭제 | 빈 디렉토리 |
| `test-results/` | 8KB | ✅ 유지 | Playwright 테스트 출력 디렉토리 |
| `api-guide-sample/` | 716KB | ⚠️ 검토 | 문서 패키지, docs/로 통합 고려 |

---

## 1. experiments/ (656MB)

### 기본 정보

| 항목 | 값 |
|------|-----|
| 경로 | `/home/uproot/ax/poc/experiments/` |
| 용량 | 656MB |
| 최종 수정 | 2025-12-28 |
| 하위 디렉토리 | 3개 |

### 구조

```
experiments/
├── pid-symbol-detection/     # 358MB - 별도 Git 저장소
│   ├── .git/
│   ├── best_model.pt         # 371MB (YOLO 모델)
│   ├── test_detection.py
│   ├── output/
│   └── output_low_conf/
│
├── PID_Symbol_Detection/     # 289MB - 별도 Git 저장소
│   ├── .git/
│   ├── models/               # 115MB
│   │   ├── stage1/           # class_aware, class_agnostic YOLO
│   │   ├── stage2/           # few_shot 모델 (92MB)
│   │   └── base_yolo_models/ # yolov8n, yolo11n
│   ├── data/                 # 16MB
│   ├── media/                # 5.4MB
│   └── src/
│
└── pid_analysis_improvement/ # 9.4MB - 실험 스크립트 & 결과
    ├── phase1_*.py           # 실험 스크립트
    ├── *.json                # 결과 데이터
    └── *.jpg, *.png          # 시각화 결과
```

### 세부 분석

#### pid-symbol-detection (358MB)
- **출처**: GitHub 외부 저장소 클론
- **내용**: PID 심볼 검출 YOLO 모델 및 데이터셋
- **주요 파일**: `best_model.pt` (371MB)
- **Git 커밋**: 3개 (최근: chore: add gitignore)
- **참조**: 없음 (메인 프로젝트에서 미사용)

#### PID_Symbol_Detection (289MB)
- **출처**: GitHub 외부 저장소 클론
- **내용**: 2-stage PID 심볼 검출 (YOLO + Few-shot)
- **주요 파일**:
  - `models/stage2/few_shot/best_fewshot_model.pth` (92MB)
  - `models/stage1/*/best.pt` (6.1MB x 2)
- **Git 커밋**: 3개 (최근: demo stage2 model uploaded)
- **참조**: 없음 (메인 프로젝트에서 미사용)

#### pid_analysis_improvement (9.4MB)
- **출처**: 내부 실험 코드
- **내용**: P&ID 분석 개선 실험 (Phase 1 시리즈)
- **주요 파일**:
  - `phase1_confidence_tuning.py` (최근 수정: 2025-12-28)
  - `phase1_3_*.py` 시리즈
  - 결과 이미지 및 JSON
- **참조**:
  - `web-ui/public/samples/` 이미지 참조
  - 실험 결과만 포함, 운영 코드에서 미사용

### 판정

| 항목 | 판정 |
|------|------|
| **결론** | ⚠️ 검토 (아카이브 후보) |
| **사유** | 메인 프로젝트에서 참조 없음. 연구/실험 목적으로만 사용 |
| **비고** | 별도 Git 저장소 2개 포함 |

### 정리 옵션

1. **전체 삭제**: 656MB 절감 (연구 데이터 손실)
2. **아카이브**: 별도 저장소로 이동 또는 압축
3. **선택적 삭제**:
   - `pid-symbol-detection/best_model.pt` 삭제: 371MB 절감
   - `PID_Symbol_Detection/models/` 삭제: 115MB 절감
   - `pid_analysis_improvement/` 결과 이미지 삭제: ~8MB 절감

---

## 2. backend/ (4KB)

### 기본 정보

| 항목 | 값 |
|------|-----|
| 경로 | `/home/uproot/ax/poc/backend/` |
| 용량 | 4KB (디렉토리만) |
| 소유자 | root |
| 파일 수 | 0 |

### 구조

```
backend/
└── (빈 디렉토리)
```

### 판정

| 항목 | 판정 |
|------|------|
| **결론** | 🗑️ 삭제 |
| **사유** | 완전히 빈 디렉토리. 참조 없음. 레거시로 추정 |
| **조치** | `rmdir /home/uproot/ax/poc/backend` |

---

## 3. test-results/ (8KB)

### 기본 정보

| 항목 | 값 |
|------|-----|
| 경로 | `/home/uproot/ax/poc/test-results/` |
| 용량 | 8KB |
| 최종 수정 | 2025-12-28 |
| 파일 수 | 1 |

### 구조

```
test-results/
└── .last-run.json    # 45 bytes - Playwright 테스트 상태
```

### 용도

- **목적**: Playwright E2E 테스트의 스크린샷 저장 디렉토리
- **참조**: 10개 이상의 E2E 테스트 파일에서 참조
  - `dashboard-api-add.spec.ts`
  - `blueprint-ai-bom.spec.ts`
  - `template-execution.spec.ts` 등

### 판정

| 항목 | 판정 |
|------|------|
| **결론** | ✅ 유지 |
| **사유** | E2E 테스트 인프라 필수. .gitignore에 포함 권장 |
| **비고** | 내용은 임시 파일이므로 정기 정리 가능 |

---

## 4. api-guide-sample/ (716KB)

### 기본 정보

| 항목 | 값 |
|------|-----|
| 경로 | `/home/uproot/ax/poc/api-guide-sample/` |
| 용량 | 716KB |
| 생성일 | 2025-12-18 |
| Git 커밋 | 1개 |

### 구조

```
api-guide-sample/
├── .git/
├── README.md         # BlueprintFlow API 커스터마이징 가이드
├── docs/             # 문서
├── samples/          # 샘플 코드
└── specs/            # API 스펙 예제
```

### 용도

- **목적**: BlueprintFlow API 커스터마이징 가이드 패키지
- **내용**:
  - 기존 API 교체 방법
  - 신규 API 추가 방법
  - YAML 스펙 작성법
- **참조**: 메인 프로젝트에서 직접 참조 없음

### 판정

| 항목 | 판정 |
|------|------|
| **결론** | ⚠️ 검토 |
| **사유** | 독립 문서 패키지. `docs/` 디렉토리와 중복 가능성 |
| **조치** | `docs/api-guide/`로 통합 고려 |

---

## 📈 Phase 5 최종 요약

### 용량 분석

| 상태 | 용량 | 비율 |
|------|------|------|
| ✅ 필수 유지 | 8KB | 0.001% |
| ⚠️ 검토 필요 | 656.7MB | 99.9% |
| 🗑️ 즉시 삭제 가능 | 4KB | 0.001% |

### 정리 가능 용량

| 항목 | 용량 | 조건 |
|------|------|------|
| `backend/` | 4KB | 즉시 삭제 가능 |
| `experiments/` | 656MB | 아카이브/삭제 결정 필요 |
| `api-guide-sample/` | 716KB | docs/로 통합 시 |

### 권장사항

1. **즉시 가능**:
   - `backend/` 삭제 (빈 디렉토리)

2. **결정 필요**:
   - `experiments/`: 연구 자료 보존 여부 결정
     - 보존 시: 별도 저장소로 이동
     - 불필요 시: 656MB 절감

3. **통합 고려**:
   - `api-guide-sample/` → `docs/api-guide/`로 이동

---

**다음**: Phase 6 (기타) 조사
