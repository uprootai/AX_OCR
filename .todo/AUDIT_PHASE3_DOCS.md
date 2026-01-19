# Phase 3: 문서 및 연구 조사 결과

> **조사일**: 2026-01-17
> **총 용량**: 57.9MB
> **디렉토리 수**: 4개

---

## 요약

| 디렉토리 | 용량 | 판정 | 조치 |
|----------|------|------|------|
| `docs/` | 5.8MB | ✅ 유지 | 프로젝트 문서 |
| `rnd/` | 52MB | ⚠️ 검토 | R&D 실험 데이터 (39MB 모델) |
| `notion/` | 20KB | ⚠️ 검토 | 레거시 노션 백업 |
| `idea-thinking/` | 36KB | ✅ 유지 | 아이디어 정리 |

**정리 가능 용량**: ~39MB (rnd/experiments/models)

---

## 1. docs/ (5.8MB)

### 기본 정보

| 항목 | 값 |
|------|-----|
| 경로 | `/home/uproot/ax/poc/docs/` |
| 용량 | 5.8MB |
| 최종 수정 | 2025-12-31 |
| 파일 수 | 다수 |

### 용량 분석

| 디렉토리 | 용량 | 설명 |
|----------|------|------|
| `references/` | 4.8MB | 참조 문서 (PDF 2개) |
| `api/` | 216KB | API 문서 (20개 API) |
| `insights/` | 116KB | 프로젝트 인사이트 |
| `blueprintflow/` | 116KB | BlueprintFlow 문서 |
| `developer/` | 112KB | 개발자 가이드 |
| `papers/` | 104KB | 논문 참조 |
| 기타 | ~300KB | 기타 문서 |

### 구조

```
docs/
├── README.md                     # 6KB
├── ADMIN_MANUAL.md               # 18KB
├── DEPLOYMENT_GUIDE.md           # 8KB
├── DYNAMIC_API_SYSTEM_GUIDE.md   # 22KB
├── GPU_CONFIGURATION_EXPLAINED.md # 7KB
├── INSTALLATION_GUIDE.md         # 11KB
├── ONPREMISE_DEPLOYMENT_GUIDE.md # 36KB
├── TROUBLESHOOTING.md            # 12KB
├── references/                   # 4.8MB - PDF 문서
│   ├── 2025년+명지녹산+...pdf    # 889KB
│   └── 이래가꼬_AI...pdf         # 4MB
├── api/                          # 216KB - API별 문서
├── blueprintflow/                # 116KB
├── insights/                     # 116KB
├── developer/                    # 112KB
├── papers/                       # 104KB
└── ...
```

### references/ 상세

| 파일 | 크기 | 설명 |
|------|------|------|
| 2025년+명지녹산+...pdf | 889KB | 스마트그린 실증산단 공고 |
| 이래가꼬_AI...pdf | 4MB | BOM 자동 생성 기술 제안서 |

### 판정

| 항목 | 판정 |
|------|------|
| **결론** | ✅ 유지 |
| **사유** | 프로젝트 필수 문서. 설치/배포/운영 가이드 포함 |
| **비고** | references/는 외부 참조 문서 |

---

## 2. rnd/ (52MB)

### 기본 정보

| 항목 | 값 |
|------|-----|
| 경로 | `/home/uproot/ax/poc/rnd/` |
| 용량 | 52MB |
| 최종 수정 | 2026-01-02 |
| 용도 | R&D 연구 자료 |

### 용량 분석

| 디렉토리 | 용량 | 설명 |
|----------|------|------|
| `experiments/` | 52MB | 실험 데이터 |
| ├ `doclayout_yolo/` | 52MB | DocLayout YOLO 실험 |
| │ ├ `models/` | 39MB | 학습된 모델 |
| │ ├ `finetuning/` | 11MB | 파인튜닝 스크립트 |
| │ └ `results/` | 2.5MB | 실험 결과 |
| `papers/` | 28KB | 논문 참조 |
| `models/` | 4KB | 모델 정의 |
| `benchmarks/` | 4KB | 벤치마크 |

### 구조

```
rnd/
├── README.md                  # 연구 개요
├── IMPLEMENTATION_DETAILS.md  # 12KB - 구현 상세
├── SOTA_GAP_ANALYSIS.md       # 22KB - SOTA 분석
├── TRAINING_GUIDES.md         # 19KB - 학습 가이드
├── experiments/               # 52MB
│   └── doclayout_yolo/        # DocLayout YOLO 실험
│       ├── models/            # 39MB - 학습 모델 ⚠️
│       ├── finetuning/        # 11MB - 스크립트/데이터
│       └── results/           # 2.5MB - 결과
├── papers/                    # 28KB - 논문 참조
├── models/                    # 4KB - 모델 정의
└── benchmarks/                # 4KB - 벤치마크
```

### 참조 분석

**apply-company에서 참조**:
```python
# rnd/experiments/doclayout_yolo/finetuning/scripts/prepare_data.py
# rnd/experiments/doclayout_yolo/finetuning/scripts/train.py
```

### 판정

| 항목 | 판정 |
|------|------|
| **결론** | ⚠️ 검토 |
| **사유** | R&D 실험 데이터. models/에 39MB 모델 웨이트 |
| **조치** | 실험 완료 시 models/ 아카이브 고려 |

### 정리 옵션

1. **models/ 아카이브**: 39MB 절감
   - 조건: DocLayout YOLO 실험 완료 시
2. **results/ 정리**: 2.5MB 절감
   - 조건: 결과 분석 완료 시

---

## 3. notion/ (20KB)

### 기본 정보

| 항목 | 값 |
|------|-----|
| 경로 | `/home/uproot/ax/poc/notion/` |
| 용량 | 20KB |
| 최종 수정 | 2025-12-28 |
| 파일 수 | 3개 |

### 구조

```
notion/
├── API_도커라이징_템플릿_가이드.md    # 1.5KB
├── AX_POC_진행현황_241219.md          # 5.5KB
└── 다음주_할일_241223.md              # 2.4KB
```

### 내용 분석

| 파일 | 날짜 | 내용 |
|------|------|------|
| API_도커라이징_템플릿_가이드 | 2024-12 | API 도커화 템플릿 |
| AX_POC_진행현황 | 2024-12-19 | 프로젝트 진행 현황 |
| 다음주_할일 | 2024-12-23 | 작업 계획 |

### 판정

| 항목 | 판정 |
|------|------|
| **결론** | ⚠️ 검토 |
| **사유** | 2024년 12월 노션 백업. 현재 미사용 가능성 |
| **조치** | docs/ 또는 .todo/archive/로 통합 고려 |

---

## 4. idea-thinking/ (36KB)

### 기본 정보

| 항목 | 값 |
|------|-----|
| 경로 | `/home/uproot/ax/poc/idea-thinking/` |
| 용량 | 36KB |
| 최종 수정 | 2025-12-31 |
| 용도 | 아이디어 정리 |

### 구조

```
idea-thinking/
├── README.md                              # 2.7KB
├── main/                                  # 메인 아이디어
│   └── 001_doclayout_yolo_integration.md  # 5.2KB
└── sub/                                   # 서브 아이디어
    └── 001_doclayout_yolo_finetuning.md   # 12KB
```

### 내용 분석

| 파일 | 주제 |
|------|------|
| main/001_* | DocLayout YOLO 통합 아이디어 |
| sub/001_* | DocLayout YOLO 파인튜닝 아이디어 |

### 판정

| 항목 | 판정 |
|------|------|
| **결론** | ✅ 유지 |
| **사유** | R&D 아이디어 정리. rnd/와 연계 |
| **비고** | 용량 미미 (36KB) |

---

## Phase 3 최종 요약

### 용량 분석

| 상태 | 용량 | 비율 |
|------|------|------|
| ✅ 필수 유지 | 5.8MB | 10% |
| ⚠️ 검토 필요 | 52MB | 90% |
| 🗑️ 삭제 가능 | 0 | 0% |

### 정리 가능 용량

| 항목 | 용량 | 조건 |
|------|------|------|
| `rnd/experiments/models/` | 39MB | DocLayout 실험 완료 시 |
| `rnd/experiments/results/` | 2.5MB | 결과 분석 완료 시 |
| `notion/` | 20KB | docs/ 통합 시 |
| **합계** | **~41.5MB** | |

### 권장사항

1. **유지**: docs/, idea-thinking/
2. **검토 후 결정**:
   - rnd/experiments/models/ - 실험 상태 확인 후
   - notion/ - docs/로 통합 또는 삭제
3. **문서 업데이트**: docs/README.md 최신화

### rnd/ vs experiments/ 비교

| 항목 | rnd/ (Phase 3) | experiments/ (Phase 5) |
|------|---------------|------------------------|
| 용량 | 52MB | 656MB |
| 위치 | 프로젝트 내 | 프로젝트 내 |
| 상태 | 활성 R&D | 외부 저장소 클론 |
| 참조 | 내부 참조 있음 | 참조 없음 |
| 권장 | 유지 (검토) | 아카이브 권장 |

---

**다음**: 전체 감사 최종 요약 작성
