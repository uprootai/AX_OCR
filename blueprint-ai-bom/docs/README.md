# Blueprint AI BOM 문서

> **최종 업데이트**: 2025-12-27
> **버전**: v10.3 (장기 로드맵 전체 완료)

---

## 문서 구조

```
docs/
├── README.md              # 이 파일
├── api/                   # API 문서
│   └── reference.md       # API 레퍼런스
├── features/              # 기능 문서
│   ├── active_learning.md # Active Learning 검증 큐
│   ├── feedback_pipeline.md # Feedback Loop Pipeline
│   ├── gdt_parser.md      # GD&T 파서
│   ├── longterm_features.md # 장기 로드맵 기능 (v9.0) 🆕
│   ├── ocr_optimization.md# OCR 최적화 (과거 분석)
│   └── ocr_performance.md # OCR 성능 분석 (과거 분석)
├── deployment/            # 배포 문서
│   ├── setup.md           # 설치 가이드
│   ├── on-premises.md     # 온프레미스 배포
│   └── model_download.md  # 모델 다운로드
├── migration/             # 마이그레이션 문서
│   ├── overview_comparison.md
│   ├── step_by_step.md
│   └── ...
└── archive/               # 구식 문서 보관
    └── README.md
```

---

## 빠른 링크

### 기능 문서

| 문서 | 설명 | 버전 |
|------|------|------|
| [Active Learning](features/active_learning.md) | 검증 큐 시스템 | v5.0 |
| [Feedback Pipeline](features/feedback_pipeline.md) | YOLO 재학습 데이터셋 내보내기 | v8.0 |
| [GD&T Parser](features/gdt_parser.md) | 기하공차 파싱 | v4.0 |
| **[장기 로드맵 기능](features/longterm_features.md)** | ✅ 영역 세분화, ✅ 노트 추출, ✅ 리비전 비교, ✅ VLM 분류 (전체 완료) | **v10.3** |
| [OCR Optimization](features/ocr_optimization.md) | OCR 최적화 결과 | - |
| [OCR Performance](features/ocr_performance.md) | OCR 성능 분석 | - |

### API 문서

| 문서 | 설명 |
|------|------|
| [API Reference](api/reference.md) | 전체 API 레퍼런스 |
| Swagger UI | http://localhost:5020/docs |
| ReDoc | http://localhost:5020/redoc |

### 배포 문서

| 문서 | 설명 |
|------|------|
| [Setup](deployment/setup.md) | 설치 가이드 |
| [On-Premises](deployment/on-premises.md) | 온프레미스 배포 |
| [Model Download](deployment/model_download.md) | 모델 다운로드 |

---

## 핵심 기능 요약

### 1. AI 심볼 검출
- YOLO v11 기반 27개 클래스 자동 검출
- 신뢰도 필터링 및 NMS

### 2. OCR 치수 인식
- eDOCr2 기반 한국어 치수 인식
- 단위 및 공차 파싱

### 3. GD&T 분석
- 기하공차 심볼 파싱 (⌀, ⊥, ∥, ⊙, ⌖)
- 데이텀 검출 (A, B, C)

### 4. Active Learning
- 신뢰도 기반 우선순위 검증 큐
- 자동/일괄 승인 기능
- 재학습용 로그 저장

### 5. Human-in-the-Loop
- 바운딩 박스 편집
- 클래스 변경
- 승인/반려/수정 워크플로우

### 6. BOM 생성
- 검증된 검출 집계
- Excel/CSV/JSON/PDF 내보내기

### 7. Feedback Loop Pipeline
- 검증된 데이터 YOLO 형식 내보내기
- 모델 재학습용 데이터셋 생성
- 클래스별 분포 분석

### 8. ✅ 장기 로드맵 기능 (v10.3 전체 완료)

#### 8.1 🗺️ 도면 영역 세분화 ✅ 완전 구현
- 휴리스틱 + VLM 하이브리드 방식으로 11개 영역 타입 자동 구분
- 표제란, 메인 뷰, BOM 테이블, 노트 영역, 상세도, 단면도 등 검출
- **지원 방식**: 휴리스틱 (기본) + VLM (선택, GPT-4o-mini)

#### 8.2 📋 주석/노트 추출 ✅ 완전 구현
- 재료 사양, 열처리, 표면 처리, 일반 공차 추출
- **GPT-4o-mini 기반 LLM 분류** + 정규식 폴백
- 10개 카테고리 자동 분류

#### 8.3 🔄 리비전 비교 ✅ 완전 구현
- **SSIM 이미지 비교**: 두 이미지의 구조적 유사도 측정
- **세션 데이터 비교**: 심볼, 치수, 노트 변경 추적
- **VLM 지능형 비교**: GPT-4o-mini로 변경점 분석 (선택)
- 추가/삭제/수정 항목 하이라이트, 차이 이미지 생성

#### 8.4 🤖 VLM 자동 분류 ✅ 완전 구현
- 도면 타입, 산업 분야, 복잡도 AI 분류
- 기능 자동 추천
- **지원 모델**: GPT-4o-mini (기본), GPT-4o, Claude Vision, 로컬 VL API
- **환경변수**: `OPENAI_API_KEY`, `OPENAI_MODEL`

---

## 버전 히스토리

| 버전 | 날짜 | 변경 |
|------|------|------|
| **v10.3** | **2025-12-27** | **장기 로드맵 전체 완료**: 리비전 비교 구현 (SSIM + 데이터 + VLM), 4/4 기능 완료 |
| v10.2 | 2025-12-27 | 영역 세분화 완전 구현: 휴리스틱 + VLM 하이브리드, 11개 영역 타입 자동 검출 |
| v10.1 | 2025-12-27 | 노트 추출 완전 구현: GPT-4o-mini LLM + 정규식 폴백, 10개 카테고리 자동 분류 |
| v10.0 | 2025-12-27 | VLM 자동 분류 완전 구현: GPT-4o-mini 기본, OpenAI/Anthropic/로컬 멀티 프로바이더 지원 |
| v9.0 | 2025-12-24 | 장기 로드맵 API 스텁: 영역 세분화, 노트 추출, 리비전 비교, VLM 자동 분류 |
| v8.1 | 2025-12-24 | 18개 기능 체크박스 툴팁 추가, UI 개선 |
| v8.0 | 2025-12-23 | Feedback Loop Pipeline, 온프레미스 배포 |
| v5.0 | 2025-12-23 | Active Learning, TypedDict |
| v4.0 | 2025-12-19 | GD&T 파서, 치수-심볼 관계 |
| v3.0 | 2025-12-14 | React 전환 완료 |
| v2.0 | 2025-09-30 | 모듈러 아키텍처 |
| v1.0 | 2025-09-01 | 초기 버전 |

---

## 관련 링크

| 리소스 | URL |
|--------|-----|
| 메인 README | [../README.md](../README.md) |
| 로드맵 | [../ROADMAP.md](../ROADMAP.md) |
| AX POC 가이드 | [../../CLAUDE.md](../../CLAUDE.md) |
| 작업 추적 | [../../.todos/README.md](../../.todos/README.md) |
