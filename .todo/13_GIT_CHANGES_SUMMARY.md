# Git 변경사항 요약 (마지막 커밋 이후)

> **생성일**: 2026-01-19
> **기준 커밋**: 5b6b0e0 (chore: P2/P3 코드 정리 작업 완료)
> **변경 파일 수**: 수정 100+, 삭제 150+, 신규 90+

---

## 1. 주요 변경 카테고리

### 1.1 Blueprint AI BOM (v10.5) - 신규 기능

**신규 서비스 (3개)**:
| 파일 | 크기 | 기능 |
|------|------|------|
| `bom_table_extractor.py` | 18KB | BOM 테이블 추출 |
| `detectron2_service.py` | 11KB | Detectron2 통합 |
| `table_structure_recognizer.py` | 28KB | 테이블 구조 인식 |

**프론트엔드 변경**:
- `AnalysisOptions.tsx`: 분석 옵션 컴포넌트 (+77줄)
- `IntegratedOverlay.tsx`: 통합 오버레이 (+186줄)
- `DetectionResultsSection.tsx`: 검출 결과 섹션 (+123줄)
- `GTComparisonSection.tsx`: GT 비교 섹션 (+130줄)

**테스트 추가**:
- `test_bom_table_extractor.py`
- `test_detectron2_service.py`
- `test_table_structure_recognizer.py`

### 1.2 디렉토리 정리

**삭제된 디렉토리**:
- `.todos/` → `.todo/`로 통합
- `experiments/PID_Symbol_Detection/`
- `experiments/pid-symbol-detection/`
- `experiments/pid_analysis_improvement/`
- `models/*/training/` (각 API로 이동)
- `web-ui/playwright-report/`

**신규 디렉토리**:
- `.claude/hooks/`
- `.claude/skills/` (5개 스킬 파일)
- `models/shared/`
- `gateway-api/config/`
- `rnd/benchmarks/`

### 1.3 문서 재배치

**루트 → docs/**:
- `API_AUTOMATION_COMPLETE_GUIDE.md`
- `ARCHITECTURE.md`
- `KNOWN_ISSUES.md`
- `QUICK_START.md`
- `ROADMAP.md`
- `WORKFLOWS.md`

**루트 → apply-company/techloss/**:
- `TECHCROSS_BWMS_Analysis_Report.xlsx`
- `TECHCROSS_BWMS_Analysis_Report_v2.xlsx`

### 1.4 Training Scripts 재배치

| 원본 위치 | 이동 위치 |
|-----------|-----------|
| `scripts/*.py` (YOLO) | `models/yolo-api/training/scripts/` |
| `scripts/*.py` (EDGNet) | `models/edgnet-api/training/scripts/` |
| `scripts/*.py` (SkinModel) | `models/skinmodel-api/training/scripts/` |

### 1.5 Config 디렉토리 추가

**새로 추가된 API config/**:
- `models/doctr-api/config/`
- `models/easyocr-api/config/`
- `models/edgnet-api/config/`
- `models/ocr-ensemble-api/config/`
- `models/paddleocr-api/config/`
- `models/surya-ocr-api/config/`
- `models/tesseract-api/config/`
- `models/trocr-api/config/`

---

## 2. Zone.Identifier 파일 정리

**삭제된 파일**: 50+ 개
**위치**: `apply-company/techloss/` 하위
**원인**: Windows → WSL 파일 복사 시 생성되는 메타데이터

---

## 3. API 스펙 변경

### 이름 변경 (kebab-case → lowercase)
| 이전 | 현재 |
|------|------|
| `design-checker.yaml` | `designchecker.yaml` |
| `line-detector.yaml` | `linedetector.yaml` |
| `pid-composer.yaml` | `pidcomposer.yaml` |
| `ocr-ensemble.yaml` | `ocr_ensemble.yaml` |

### 신규 API 스펙
- `excelexport.yaml`
- `gtcomparison.yaml`
- `pdfexport.yaml`
- `pidfeatures.yaml`
- `verificationqueue.yaml`

---

## 4. 인프라 파일 추가

| 파일 | 용도 |
|------|------|
| `.editorconfig` | 코드 스타일 통일 |
| `.pre-commit-config.yaml` | Pre-commit 훅 |
| `.github/CODEOWNERS` | 코드 소유자 정의 |
| `.github/dependabot.yml` | 의존성 자동 업데이트 |
| `.github/workflows/cd.yml` | CD 파이프라인 |
| `Makefile` | 빌드 자동화 |

---

## 5. 후속 작업 필요

### P1 (높은 우선순위)
1. **Blueprint AI BOM 테스트**: 새 서비스 통합 테스트
2. **models/shared/ 완성**: 공유 유틸리티 정리

### P2 (중간 우선순위)
1. **config/ 일관성**: 누락된 API에 config 추가
   - 상세: `.todo/11_CONFIG_DIRECTORY_CONSISTENCY.md`
2. **문서 업데이트**: 재배치된 문서 링크 검증

### P3 (낮은 우선순위)
1. **edocr2-api 삭제**: edocr2-v2-api로 완전 대체
2. **API 스펙 문서화**: 신규 API 스펙 docs/ 추가

---

## 6. 커밋 준비 체크리스트

- [x] Zone.Identifier 파일 삭제
- [x] 중복 스크립트 정리
- [x] 문서 재배치
- [x] .gitignore 업데이트
- [ ] Blueprint AI BOM 테스트 완료
- [ ] 전체 테스트 실행 확인
- [ ] 린트 검사 통과

---

*마지막 업데이트: 2026-01-19*
