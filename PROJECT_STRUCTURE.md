# 📁 프로젝트 구조 가이드

> **최종 업데이트**: 2025-11-13
> **버전**: v2.1 (문서 및 스크립트 재정리 완료)

---

## 🎯 **개요**

본 프로젝트는 **마이크로서비스 아키텍처 기반 AI 도면 분석 및 자동 견적 시스템**입니다.
- **정부 지원 사업**: 명지녹산 스마트그린 AX 실증산단 구축사업
- **목표**: 제조 도면 자동 분석 → 견적서 자동 생성 (8~12초)
- **기술 스택**: Python, FastAPI, React 19, Docker, GraphSAGE, CRNN, YOLO

---

## 📂 **최상위 디렉토리 구조**

```
/home/uproot/ax/poc/
├── README.md                           # 프로젝트 메인 소개
├── QUICKSTART.md                       # 5분 빠른 시작 가이드
├── docker-compose.yml                  # 전체 시스템 배포 설정
├── docker-compose.enhanced.yml         # 모니터링 포함 배포
├── prometheus.yml                      # Prometheus 설정
├── security_config.yaml.template       # 보안 설정 템플릿
├── .env.example / .env.template        # 환경 변수 템플릿
├── .gitignore                          # Git 제외 파일 목록
├── yolo11n.pt                          # YOLOv11 Nano 사전학습 모델
│
├── 📁 docs/                            # 📚 전체 문서 통합 디렉토리
├── 📁 scripts/                         # 🔧 테스트 & 유틸리티 스크립트
├── 📁 logs/                            # 📊 로그 파일 (Git ignore)
│
├── 📁 edgnet-api/                      # GraphSAGE 세그멘테이션 API
├── 📁 edocr2-api/                      # 멀티 OCR API (v1+v2)
├── 📁 gateway-api/                     # 통합 게이트웨이 API
├── 📁 skinmodel-api/                   # 공차 예측 API
├── 📁 yolo-api/                        # YOLO 객체 검출 API
├── 📁 vl-api/                          # VLM API (연구 중)
├── 📁 web-ui/                          # React 프론트엔드
│
├── 📁 TODO/                            # 프로젝트 관리 & 제안서
├── 📁 common/                          # 공통 모듈
├── 📁 datasets/                        # AI 학습 데이터
├── 📁 dev/                             # 개발 도구 & 실험
├── 📁 runs/                            # 실험 결과 (TensorBoard)
└── 📁 test_samples/                    # 테스트 샘플 도면
```

---

## 📚 **docs/ - 문서 디렉토리 (카테고리별 정리)**

```
docs/
├── 📖 user/                            # 사용자 가이드
│   ├── USER_GUIDE.md                   # 상세 사용자 매뉴얼
│   ├── API_USAGE_MANUAL.md             # API 사용법
│   ├── TROUBLESHOOTING_GUIDE.md        # 문제 해결 가이드
│   └── KOREAN_EXECUTION_GUIDE.md       # 한국어 실행 가이드
│
├── 👨‍💻 developer/                        # 개발자 가이드
│   ├── CLAUDE.md                       # Claude AI 활용 (영문)
│   ├── CLAUDE_KR.md                    # Claude AI 활용 (한글)
│   ├── CONTRIBUTING.md                 # 기여 가이드
│   └── GIT_WORKFLOW.md                 # Git 워크플로우
│
├── 🔧 technical/                       # 기술 구현 가이드
│   ├── yolo/
│   │   ├── IMPLEMENTATION_GUIDE.md     # YOLOv11 구현 가이드
│   │   └── QUICKSTART.md               # YOLO 빠른 시작
│   ├── ocr/
│   │   ├── EDOCR_V1_V2_DEPLOYMENT.md   # eDOCr 배포 가이드
│   │   └── OCR_IMPROVEMENT_STRATEGY.md # OCR 성능 개선 전략
│   ├── VL_API_IMPLEMENTATION_GUIDE.md  # VLM API 가이드
│   └── SYNTHETIC_DATA_STRATEGY.md      # 합성 데이터 전략
│
├── 🏗️ architecture/                    # 아키텍처 & 분석
│   ├── PROJECT_STRUCTURE_ANALYSIS.md   # 프로젝트 구조 분석
│   ├── DEPLOYMENT_STATUS.md            # 배포 현황
│   ├── PRODUCTION_READINESS_ANALYSIS.md # 프로덕션 준비도
│   ├── IMPLEMENTATION_STATUS.md        # 구현 진행 상황
│   └── DECISION_MATRIX.md              # 기술 의사결정
│
├── 📋 reports/                         # 최종 보고서
│   ├── FINAL_COMPREHENSIVE_REPORT.md   # 최종 종합 보고서
│   └── COMPREHENSIVE_EVALUATION_REPORT.md # 종합 평가 보고서
│
├── 📦 archive/                         # 과거 완료 문서 (21개)
│   ├── [기존 12개 문서]
│   │   ├── ANALYZE_ISSUE_REPORT.md
│   │   ├── BBOX_VERIFICATION_REPORT.md
│   │   ├── BBOX_INDEX_MISMATCH_FIX.md
│   │   ├── OCR_TEST_CONCLUSION.md
│   │   ├── PAPER_IMPLEMENTATION_GAP_ANALYSIS.md
│   │   ├── PERFORMANCE_VALIDATION_REPORT.md
│   │   ├── FINAL_USER_VALIDATION.md
│   │   ├── FINAL_VALIDATION_RESULT.md
│   │   ├── EDGNET_INTEGRATION_COMPLETE.md
│   │   ├── WEB_UI_PLANNING.md
│   │   ├── WEB_UI_STATUS.md
│   │   └── WEB_UI_DEBUGGING_SPEC.md
│   │
│   └── [2025-11-13 추가: 9개 우선순위 가이드]
│       ├── PRIORITY_1_GDT_DRAWINGS.md
│       ├── PRIORITY_1_VL_API_KEYS.md
│       ├── PRIORITY_2_SECURITY_POLICY.md
│       ├── PRIORITY_2_SKIN_MODEL_DATA.md
│       ├── PRIORITY_3_GPU_SETUP.md
│       ├── PRIORITY_3_PRODUCTION.md
│       ├── FINAL_SUMMARY.md
│       ├── IMPROVEMENT_PROGRESS_REPORT.md
│       └── INTEGRATION_GUIDE.md
│
├── 📁 references/                      # 참고 문서 (2025-11-13 신규)
│   ├── 2025년+명지녹산+스마트그린+AX+실증산단+구축+사업+지원계획+통합공고.pdf
│   └── 이래가꼬_AI 설계도면 분석을 통한 BOM 자동 생성 기술 개발.pdf
│
└── 🔓 opensource/                      # 오픈소스 관련
    ├── README.md
    ├── COMPARISON_REPORT.md
    ├── MODEL_DOWNLOAD_INFO.md
    ├── PROGRESS_REPORT.md
    └── SOLUTION.md
```

---

## 🔧 **scripts/ - 스크립트 디렉토리**

```
scripts/
├── test/                               # 활성 테스트 스크립트
│   ├── test_apis.py                    # 전체 API 테스트
│   ├── test_apis.sh                    # Shell 기반 테스트
│   ├── test_ocr_performance_comparison.py # OCR 성능 비교
│   └── test_cer_calculation.py         # CER 계산
│
├── archive/                            # 아카이브된 스크립트 (13개)
│   ├── demo_full_system.py             # 전체 시스템 데모
│   ├── benchmark_system.py             # 성능 벤치마크
│   ├── test_improvements.py            # 통합 테스트
│   ├── apply_enhancements.sh           # 개선사항 적용
│   ├── test_bbox_mapping_verification.py # BBox 매핑 검증
│   ├── test_edocr2_bbox_detailed.py    # eDOCr BBox 테스트
│   ├── test_ocr_visualization.py       # OCR 시각화
│   ├── test_detailed_analysis.py       # 상세 분석
│   ├── test_pdf_conversion.py          # PDF 변환
│   ├── test_tooltip.py                 # 툴팁 테스트
│   ├── test_yolo_prototype.py          # YOLO 프로토타입
│   └── verify_bbox_api.py              # BBox API 검증
│
├── deploy/                             # 배포 스크립트
└── README.md                           # 스크립트 가이드
```

---

## 🔷 **마이크로서비스 API 디렉토리**

### **1. edgnet-api/ - GraphSAGE 세그멘테이션**

```
Port: 5012
기능: 도면 영역 분할 (Contours/Text/Dimensions)
정확도: 90.82%
```

```
edgnet-api/
├── Dockerfile
├── docker-compose.yml
├── api_server.py               # FastAPI 서버
├── requirements.txt
├── README.md
├── results/                    # 세그멘테이션 결과
└── uploads/                    # 업로드 임시 저장
```

---

### **2. edocr2-api/ - 멀티 OCR 엔진**

```
Port: 5001 (v1), 5002 (v2)
기능: 도면 OCR (치수, GD&T, 텍스트 추출)
v1: Keras 2.x (빠른 처리)
v2: Keras 3.x (테이블 OCR 지원)
```

```
edocr2-api/
├── Dockerfile / Dockerfile.v1 / Dockerfile.v2
├── docker-compose.yml
├── docker-compose-dual.yml     # v1+v2 동시 배포
├── api_server.py               # 통합 서버
├── api_server_edocr_v1.py      # v1 전용
├── api_server_edocr_v2.py      # v2 전용
├── requirements.txt / requirements_v1.txt / requirements_v2.txt
├── README.md
├── enhancers/                  # 이미지 전처리
├── models/                     # OCR 모델 가중치
├── results/
└── uploads/
```

---

### **3. gateway-api/ - 통합 게이트웨이**

```
Port: 8000
기능: 마이크로서비스 오케스트레이션, 견적서 생성
처리 시간: 8~12초 (전체 파이프라인)
```

```
gateway-api/
├── Dockerfile
├── docker-compose.yml
├── api_server.py               # 게이트웨이 서버
├── cost_estimator.py           # 비용 산정 모듈
├── pdf_generator.py            # PDF 견적서 생성
├── requirements.txt
├── README.md
├── __pycache__/
├── results/                    # 최종 견적서 (PDF/Excel)
└── uploads/
```

---

### **4. skinmodel-api/ - 공차 예측**

```
Port: 5003
기능: 제조 공차 자동 예측 (IT 등급, 표면 조도)
상태: 연구 진행 중
```

```
skinmodel-api/
├── Dockerfile
├── docker-compose.yml
├── api_server.py
├── requirements.txt
├── README.md
├── data/                       # 학습 데이터
└── output/                     # 예측 결과
```

---

### **5. yolo-api/ - 객체 검출**

```
Port: 5005
기능: YOLOv11/v8 앙상블 기반 부품 심볼 검출
성과: Precision 100%, Recall 96.2% (파나시아 프로젝트)
```

```
yolo-api/
├── Dockerfile
├── api_server.py
├── requirements.txt
├── models/                     # YOLO 가중치
├── results/
└── uploads/
```

---

### **6. vl-api/ - Vision Language Model (연구 중)**

```
기능: VLM (GPT-4V, Claude Vision) 통합
상태: 연구 진행 중 (API 키 발급 대기)
```

---

### **7. web-ui/ - React 프론트엔드**

```
Port: 5173 (개발), 80 (프로덕션)
기술 스택: React 19, TypeScript, Vite, Tailwind CSS
상태 관리: Zustand
데이터 페칭: TanStack Query
```

```
web-ui/
├── Dockerfile
├── nginx.conf                  # Nginx 설정 (프로덕션)
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.js
├── .env / .env.example
├── index.html
├── README.md
│
├── src/                        # 소스 코드
│   ├── components/             # UI 컴포넌트
│   ├── pages/                  # 페이지 라우팅
│   ├── hooks/                  # 커스텀 훅
│   ├── utils/                  # 유틸리티
│   └── types/                  # TypeScript 타입
│
├── public/                     # 정적 파일
├── dist/                       # 빌드 결과물
└── node_modules/               # npm 패키지
```

---

## 📁 **TODO/ - 프로젝트 관리**

```
TODO/
├── README.md                           # TODO 디렉토리 인덱스
├── USER_ACTION_QUICKSTART.md          # 사용자 작업 빠른 시작
├── QUICK_REFERENCE.md                  # 빠른 참조 카드
├── STARTUP_GUIDE.md                    # 스타트업 가이드
│
├── 2025-11-13-*.md (5개 최신 작업 기록)
│   ├── 100-point-achievement-summary.md
│   ├── enhanced-validation-implementation.md
│   ├── final-verification-report.md
│   ├── schema-driven-refactoring.md
│   └── settings-comprehensive-test.md
│
├── check/                              # 제출용 신청서
│   └── (붙임. 3) 공급기업_신속견적 AI 솔루션 지원_v1.1.pdf
│
└── RnD/                                # 연구개발 자료
```

**참고**:
- PDF 파일(2개)은 `docs/references/`로 이동
- PRIORITY_* 가이드(9개)는 `docs/archive/`로 이동
- scripts/ 디렉토리는 제거됨

---

## 📊 **logs/ - 로그 디렉토리 (Git ignore)**

```
logs/
└── .gitkeep                            # Git 추적용 빈 파일

# 실제 로그는 .gitignore에 의해 Git에서 제외됨
```

---

## 📦 **기타 디렉토리**

### **common/ - 공통 모듈**
- 전체 프로젝트 공유 코드
- 데이터 전처리, 로깅, 에러 핸들링, 타입 정의

### **datasets/ - AI 학습 데이터**
- 도면 이미지 데이터셋
- 라벨링 데이터 (JSON/XML)
- 합성 데이터 (랜덤 배치 증강)
- GD&T 심볼 데이터셋

### **dev/ - 개발 도구 & 실험**
- 실험적 기능 프로토타입
- 성능 최적화 시도

### **runs/ - 실험 결과**
- AI 모델 학습 로그 (TensorBoard)
- 모델 체크포인트
- 하이퍼파라미터 튜닝 결과

### **test_samples/ - 테스트 샘플**
- 기계/조선/건축/플랜트 도면 샘플
- GD&T 포함 도면
- API 테스트용

---

## 🚀 **빠른 시작**

### **1. 전체 시스템 실행**

```bash
# 루트 디렉토리에서
docker-compose up -d

# 헬스 체크
scripts/test/test_apis.sh
```

### **2. 개별 서비스 실행**

```bash
# eDOCr v1+v2 동시 실행
cd edocr2-api
docker-compose -f docker-compose-dual.yml up -d

# Web UI 개발 모드
cd web-ui
npm run dev
```

### **3. 테스트**

```bash
# 전체 API 테스트
python scripts/test/test_apis.py

# OCR 시각화 테스트
python scripts/test/test_ocr_visualization.py
```

---

## 📖 **주요 문서 빠른 링크**

### **시작하기**
- [README.md](../README.md) - 프로젝트 소개
- [QUICKSTART.md](../QUICKSTART.md) - 5분 빠른 시작

### **사용자 가이드**
- [사용자 매뉴얼](docs/user/USER_GUIDE.md)
- [API 사용법](docs/user/API_USAGE_MANUAL.md)
- [문제 해결](docs/user/TROUBLESHOOTING_GUIDE.md)

### **개발자 가이드**
- [Claude AI 활용](docs/developer/CLAUDE_KR.md)
- [기여 가이드](docs/developer/CONTRIBUTING.md)
- [Git 워크플로우](docs/developer/GIT_WORKFLOW.md)

### **기술 가이드**
- [YOLO 구현](docs/technical/yolo/IMPLEMENTATION_GUIDE.md)
- [OCR 배포](docs/technical/ocr/EDOCR_V1_V2_DEPLOYMENT.md)
- [OCR 성능 개선](docs/technical/ocr/OCR_IMPROVEMENT_STRATEGY.md)

### **보고서**
- [최종 종합 보고서](docs/reports/FINAL_COMPREHENSIVE_REPORT.md)
- [종합 평가 보고서](docs/reports/COMPREHENSIVE_EVALUATION_REPORT.md)

---

## 🔧 **구조 정리 내역 (v2.1 - 2025-11-13)**

### **최신 개선 사항 (v2.1)**

1. **문서 재정리** (2025-11-13)
   - TODO/ MD 파일: 18개 → 9개
   - PDF 파일 이동: TODO/ → docs/references/
   - 구버전 가이드 아카이브: PRIORITY_* 9개 → docs/archive/

2. **Python 스크립트 정리**
   - 활성 Python 파일: 47개 → 35개
   - 아카이브: 13개 구버전 스크립트 → scripts/archive/
   - 빈 디렉토리 제거: TODO/scripts/, scripts/utils/
   - __pycache__ 전체 삭제

3. **디렉토리 구조 단순화**
   - scripts/ 구조 개선: test/(4개 활성) + archive/(13개)
   - TODO/ 구조 명확화: 최신 5개 보고서 + 가이드 4개
   - docs/references/ 신규 생성 (2개 PDF)

### **v2.0 개선 사항 (2025-11-12)**

1. **문서 정리** (50개 → 5개 루트 파일)
   - docs/ 디렉토리로 카테고리별 통합
   - user, developer, technical, architecture, reports, archive 분류

2. **스크립트 정리** (10개 → scripts/ 통합)
   - test/, utils/, deploy/ 분류
   - 중복 스크립트 제거

3. **.gitignore 보강**
   - logs/ 디렉토리 추가
   - 날짜 기반 결과 파일 제외
   - Zone.Identifier 제외

---

## 📞 **문의 & 기여**

- **이슈 리포트**: [GitHub Issues](링크 추가 필요)
- **기여 가이드**: [docs/developer/CONTRIBUTING.md](docs/developer/CONTRIBUTING.md)
- **Git 워크플로우**: [docs/developer/GIT_WORKFLOW.md](docs/developer/GIT_WORKFLOW.md)

---

**최종 업데이트**: 2025-11-13
**작성자**: Claude Code
**버전**: v2.1 (문서 및 스크립트 재정리 완료)
