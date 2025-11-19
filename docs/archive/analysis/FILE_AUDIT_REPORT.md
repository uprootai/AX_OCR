# 프로젝트 파일 및 디렉토리 감사 보고서

## 📋 목적
모든 파일과 디렉토리를 검토하여 필요 여부 및 용도를 문서화

---

## ✅ **핵심 프로덕션 파일 (필수)**

### 1. **루트 레벨 설정 파일**

- **`docker-compose.yml`** (8.9KB) - **필수** ✅
  - 전체 마이크로서비스 오케스트레이션 설정
  - 8개 API + Gateway + Web UI 정의

- **`.gitignore`** (1.2KB) - **필수** ✅
  - Git 버전 관리 제외 파일 정의
  - 민감 정보, 빌드 아티팩트 제외

- **`.gitattributes`** (1KB) - **필수** ✅
  - Git LFS 및 파일 속성 관리

- **`README.md`** (5.7KB) - **필수** ✅
  - 프로젝트 메인 문서
  - 설치 및 실행 가이드

### 2. **문서화 파일 (프로덕션)**

#### Claude Code 가이드 (최신)
- **`CLAUDE.md`** (3.2KB) - **필수** ✅
  - LLM 최적화 프로젝트 가이드
  - 빠른 네비게이션 인덱스

#### 핵심 문서
- **`ARCHITECTURE.md`** (6.2KB) - **필수** ✅
  - 시스템 아키텍처 상세 설명
  - 마이크로서비스 구조, 데이터 플로우

- **`WORKFLOWS.md`** (7.5KB) - **필수** ✅
  - 개발 워크플로우 가이드
  - 기능 추가/수정/삭제/디버깅 단계별 가이드

- **`KNOWN_ISSUES.md`** (19.3KB) - **필수** ✅
  - 알려진 문제 추적
  - 사용자 피드백 로그

- **`ROADMAP.md`** (7.3KB) - **필수** ✅
  - 프로젝트 진행 상황
  - 체크박스 기반 진행도 추적

#### 참고 문서
- **`QUICK_START.md`** (2.1KB) - **유지** 📌
  - 5분 빠른 시작 가이드

- **`LLM_USABILITY_GUIDE.md`** (17.7KB) - **유지** 📌
  - LLM 사용성 최적화 가이드

### 3. **API 서비스 디렉토리 (필수)**

#### **`gateway-api/`** - **필수** ✅
- 메인 오케스트레이터 (Port 8000)
- `api_server.py` - 메인 서버 (500+ 라인)
- `models/` - Pydantic 스키마
- `services/` - 비즈니스 로직 (tolerance, ensemble 등)
- `utils/` - 유틸리티 (visualization, progress 등)

#### **`yolo-api/`** - **필수** ✅
- YOLO 객체 검출 서비스 (Port 5005)
- `api_server.py`, `models/`, `services/`, `utils/`
- 치수, GD&T, 텍스트 블록 검출

#### **`edocr2-v2-api/`** - **필수** ✅
- eDOCr v2 OCR 서비스 (Port 5002)
- GPU 가속 전처리 지원
- `api_server.py`, `services/ocr_processor.py`
- `utils/visualization.py` - OCR 시각화

#### **`edgnet-api/`** - **필수** ✅
- EDGNet 세그멘테이션 (Port 5012)
- GraphSAGE 기반 레이어 분류
- `services/inference.py`
- `utils/visualization.py` - EDGNet 시각화

#### **`skinmodel-api/`** - **필수** ✅
- Skin Model 공차 예측 (Port 5003)
- FEM 기반 제조 가능성 분석
- `ml_predictor.py`, `services/tolerance.py`
- `utils/visualization.py` - Tolerance 게이지 시각화

#### **`paddleocr-api/`** - **필수** ✅
- PaddleOCR 보조 서비스 (Port 5006)
- 다국어 OCR 지원
- `services/ocr_processor.py`

#### **`vl-api/`** - **필수** ✅
- Vision-Language 모델 API (Port 5011)
- 멀티모달 LLM 분석
- Claude/GPT-4V 통합

#### **`edocr2-api/`** - **참고용** 📌
- 레거시 eDOCr v1 구현
- v2로 대체되었지만 참고용으로 유지

### 4. **프론트엔드**

#### **`web-ui/`** - **필수** ✅
- React + TypeScript + Vite
- `src/components/` - UI 컴포넌트
  - `upload/FileUploadSection.tsx` - 파일 업로드
  - `debug/PipelineStepsVisualization.tsx` - 파이프라인 시각화
  - `results/` - 결과 표시
- `src/pages/` - 페이지 라우팅
- `public/samples/` - 샘플 이미지

---

## ⚠️ **레거시/중복 파일 (정리 대상)**

### 1. **구형 문서 (삭제 가능)**

- **`README.old.md`** (7.8KB) - **삭제 가능** ❌
  - 구버전 README, README.md로 대체됨

- **`PROJECT_STRUCTURE.md`** (16.6KB) - **병합 후 삭제** ❌
  - ARCHITECTURE.md와 중복
  - 내용을 ARCHITECTURE.md에 병합 후 삭제

- **`QUICKSTART.md`** (5.7KB) - **병합 후 삭제** ❌
  - QUICK_START.md와 중복
  - 내용 확인 후 QUICK_START.md에 병합

### 2. **과거 분석 보고서 (아카이브)**

- **`API_INDIVIDUAL_TEST_REPORT.md`** - **아카이브** 📦
  - 개별 API 테스트 결과 (과거)

- **`COMPREHENSIVE_TEST_REPORT.md`** - **아카이브** 📦
  - 종합 테스트 보고서 (과거)

- **`BUG_FIXES_SUMMARY.md`** - **아카이브** 📦
  - 버그 수정 요약 (과거)

- **`FINAL_BRIEFING.md`** - **아카이브** 📦
  - 최종 브리핑 (과거)

- **`FINAL_SUMMARY.md`** - **아카이브** 📦
  - 최종 요약 (과거)

- **`FINAL_ACCURACY_ANALYSIS.md`** - **아카이브** 📦
  - 정확도 분석 (과거)

**권장사항**: `docs/archive/` 디렉토리로 이동

### 3. **리팩토링 관련 문서 (아카이브)**

- **`REFACTORING_PLAN.md`** (20.1KB) - **아카이브** 📦
- **`REFACTORING_COMPLETE.md`** (9KB) - **아카이브** 📦
- **`REFACTORING_SUMMARY.md`** (8.1KB) - **아카이브** 📦
- **`REFACTORING_SUCCESS_SUMMARY.md`** (11.1KB) - **아카이브** 📦
- **`REFACTORING_METRICS.md`** (10.4KB) - **아카이브** 📦
- **`REMAINING_REFACTORING_GUIDE.md`** (6KB) - **아카이브** 📦

**권장사항**: 리팩토링 완료 후 `docs/archive/refactoring/`로 이동

### 4. **임시 문서 (아카이브)**

- **`DOCUMENTATION_INDEX.md`** - **아카이브** 📦
- **`DOCUMENTATION_IMPROVEMENTS.md`** - **아카이브** 📦
- **`VERIFICATION_REPORT.md`** - **아카이브** 📦
- **`FEATURE_REGRESSION_ANALYSIS.md`** - **아카이브** 📦
- **`FILE_UPLOAD_UI_UPGRADE.md`** - **아카이브** 📦
- **`UI_UX_ANALYSIS.md`** - **아카이브** 📦
- **`QUICK_WINS.md`** - **아카이브** 📦

**권장사항**: `docs/archive/analysis/`로 이동

### 5. **테스트 스크립트 (정리 필요)**

#### 삭제 가능 (일회성 테스트)
- **`test_file_upload.py`** - **삭제** ❌
- **`test_file_selection.py`** - **삭제** ❌
- **`test_file_upload_detailed.py`** - **삭제** ❌
- **`test_upload_section.py`** - **삭제** ❌
- **`test_sample_*.py`** (10개 파일) - **삭제** ❌
- **`test_quick_check.py`** - **삭제** ❌
- **`test_complete_view.py`** - **삭제** ❌
- **`test_scroll_to_samples.py`** - **삭제** ❌

#### 유지 (유용한 테스트)
- **`test_full_pipeline.py`** - **유지** 📌
  - 전체 파이프라인 통합 테스트

- **`test_yolo_api_direct.py`** - **유지** 📌
  - YOLO API 직접 테스트

- **`evaluate_api_accuracy.py`** - **유지** 📌
  - API 정확도 평가

- **`test_api_response.py`** - **유지** 📌
  - API 응답 테스트

**권장사항**: `scripts/tests/` 디렉토리로 이동

### 6. **스크린샷 파일 (아카이브)**

- **`screenshot_*.png`** (10개 파일) - **아카이브** 📦
- **`complete_view.png`** - **아카이브** 📦
- **`final_*.png`** (4개 파일) - **아카이브** 📦
- **`test_*.png`** (7개 파일) - **아카이브** 📦
- **`upload_card_full.png`** - **아카이브** 📦

**권장사항**: `docs/screenshots/archive/`로 이동

### 7. **JSON 결과 파일 (아카이브)**

- **`api_accuracy_evaluation.json`** - **아카이브** 📦
- **`full_pipeline_test_results.json`** - **아카이브** 📦
- **`pid_ocr_test_results.json`** - **아카이브** 📦

**권장사항**: `test_results/archive/`로 이동

---

## 🗂️ **데이터셋 디렉토리**

### **`datasets/`** - **필수 (훈련용)** ✅
- `combined/` - YOLO 훈련 데이터셋
  - `data.yaml` - 데이터셋 설정
  - `images/train/` - 훈련 이미지
  - `images/val/` - 검증 이미지 (150장)
  - `images/test/` - 테스트 이미지 (150장)
  - `labels/` - YOLO 라벨 파일

**용도**: YOLO 모델 재훈련 시 필요
**크기**: 대용량 (수백MB)
**권장사항**: 유지 (모델 개선 시 필요)

### **`edgnet_dataset/`** - **참고용** 📌
- EDGNet 훈련 데이터
- `drawings/` - 도면 이미지 (2장)
- `*.json` - 어노테이션

**권장사항**: 참고용으로 유지

### **`edgnet_dataset_augmented/`** - **참고용** 📌
- 증강된 EDGNet 데이터셋

### **`edgnet_dataset_large/`** - **참고용** 📌
- 대규모 EDGNet 데이터셋

---

## 🛠️ **유틸리티 디렉토리**

### **`scripts/`** - **필수** ✅
- 스크립트 모음
- 데이터셋 생성, 전처리 등

### **`monitoring/`** - **선택** 📊
- Prometheus + Grafana 모니터링 설정
- 프로덕션 환경에서 유용

### **`docs/`** - **필수** ✅
- 추가 문서 및 가이드

### **`TODO/`** - **아카이브** 📦
- 완료된 TODO 리스트
- `docs/archive/`로 이동

---

## 🗑️ **삭제 가능한 파일**

### 임시/테스트 파일
- **`yolo11n.pt`** (5.6MB) - **삭제 가능** ❌
  - YOLO 기본 가중치 파일
  - Ultralytics에서 자동 다운로드 가능

- **`test_yolo_viz.html`** (9.1KB) - **삭제** ❌
  - 일회성 시각화 테스트 HTML

- **`web-ui-dev.log`** (2.1KB) - **삭제** ❌
  - 개발 로그 파일

### 설정 템플릿 (복사본 유지)
- **`.env.example`** - **유지** 📌
- **`.env.template`** - **유지** 📌
- **`docker-compose.enhanced.yml`** - **참고용** 📌
- **`prometheus.yml`** - **유지** 📌
- **`security_config.yaml.template`** - **유지** 📌

---

## 🧹 **정리 계획 요약**

### Phase 1: 문서 아카이브 (즉시)
```bash
mkdir -p docs/archive/{analysis,refactoring,tests,screenshots}
mv *_ANALYSIS.md docs/archive/analysis/
mv REFACTORING_*.md docs/archive/refactoring/
mv screenshot_*.png docs/archive/screenshots/
mv test_*.png docs/archive/screenshots/
```

### Phase 2: 테스트 스크립트 정리 (즉시)
```bash
mkdir -p scripts/tests/archive
mv test_*.py scripts/tests/archive/
# 유용한 것만 scripts/tests/로 복사
cp scripts/tests/archive/test_full_pipeline.py scripts/tests/
cp scripts/tests/archive/test_yolo_api_direct.py scripts/tests/
```

### Phase 3: 중복 문서 병합 (검토 필요)
```bash
# README.old.md → 삭제
# PROJECT_STRUCTURE.md → ARCHITECTURE.md 병합 후 삭제
# QUICKSTART.md → QUICK_START.md 병합 후 삭제
```

### Phase 4: 임시 파일 삭제 (즉시)
```bash
rm yolo11n.pt  # 자동 다운로드 가능
rm test_yolo_viz.html
rm web-ui-dev.log
rm *.json  # 테스트 결과 JSON들
```

---

## 📊 **디스크 사용량 분석**

### 대용량 디렉토리
1. **`datasets/`** - 수백MB
   - 필수: YOLO 훈련 데이터

2. **`.git/`** - 수십MB
   - 필수: Git 히스토리

3. **`runs/`** - 크기 확인 필요
   - YOLO 훈련 결과
   - 아카이브 권장

4. **`node_modules/`** (web-ui 내)
   - 프론트엔드 의존성
   - 필수

### 삭제 시 절약 가능 용량
- 테스트 스크립트: ~50KB
- 스크린샷: ~3MB
- 문서 아카이브: ~200KB
- yolo11n.pt: 5.6MB
- **총 예상 절약**: ~9MB

---

## 🎯 **최종 권장사항**

### 즉시 실행
1. ✅ 테스트 스크립트 아카이브
2. ✅ 스크린샷 아카이브
3. ✅ 과거 분석 문서 아카이브
4. ✅ 임시 파일 삭제 (yolo11n.pt, 로그 등)

### 검토 후 실행
1. 📌 중복 문서 병합 (README.old, PROJECT_STRUCTURE 등)
2. 📌 TODO 디렉토리 아카이브
3. 📌 runs/ 디렉토리 정리

### 유지
1. ✅ 모든 API 디렉토리
2. ✅ datasets/ (훈련용)
3. ✅ 핵심 문서 (CLAUDE.md, ARCHITECTURE.md, WORKFLOWS.md 등)
4. ✅ 설정 파일 (.env.example, docker-compose.yml 등)

---

## 📝 **정리 후 프로젝트 구조 (최적화)**

```
/home/uproot/ax/poc/
├── 📂 API Services (필수)
│   ├── gateway-api/
│   ├── yolo-api/
│   ├── edocr2-v2-api/
│   ├── edgnet-api/
│   ├── skinmodel-api/
│   ├── paddleocr-api/
│   └── vl-api/
│
├── 📂 Frontend (필수)
│   └── web-ui/
│
├── 📂 Datasets (훈련용)
│   ├── datasets/combined/
│   └── edgnet_dataset/ (참고)
│
├── 📂 Scripts (필수)
│   ├── scripts/
│   └── tests/ (정리된 테스트)
│
├── 📂 Documentation (필수)
│   ├── CLAUDE.md ⭐
│   ├── ARCHITECTURE.md
│   ├── WORKFLOWS.md
│   ├── KNOWN_ISSUES.md
│   ├── ROADMAP.md
│   ├── README.md
│   └── docs/
│       └── archive/ (과거 문서)
│
├── 📂 Config (필수)
│   ├── docker-compose.yml
│   ├── .gitignore
│   ├── .env.example
│   └── prometheus.yml
│
└── 📂 Monitoring (선택)
    └── monitoring/
```

---

**보고서 작성일**: 2025-11-19
**작성자**: Claude Code (Sonnet 4.5)
