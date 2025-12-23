# Blueprint AI BOM 문서

> **최종 업데이트**: 2025-12-23
> **버전**: v5.0

---

## 문서 구조

```
docs/
├── README.md              # 이 파일
├── api/                   # API 문서
│   └── reference.md       # API 레퍼런스
├── features/              # 기능 문서
│   ├── active_learning.md # Active Learning 검증 큐
│   ├── gdt_parser.md      # GD&T 파서
│   ├── ocr_optimization.md# OCR 최적화
│   └── ocr_performance.md # OCR 성능 분석
├── deployment/            # 배포 문서
│   ├── setup.md           # 설치 가이드
│   ├── model_download.md  # 모델 다운로드
│   ├── claude_guidelines.md
│   └── claude_usage.md
└── migration/             # 마이그레이션 문서
    ├── overview_comparison.md
    ├── step_by_step.md
    └── ...
```

---

## 빠른 링크

### 기능 문서

| 문서 | 설명 |
|------|------|
| [Active Learning](features/active_learning.md) | 검증 큐 시스템 |
| [GD&T Parser](features/gdt_parser.md) | 기하공차 파싱 |
| [OCR Optimization](features/ocr_optimization.md) | OCR 최적화 결과 |
| [OCR Performance](features/ocr_performance.md) | OCR 성능 분석 |

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

---

## 버전 히스토리

| 버전 | 날짜 | 변경 |
|------|------|------|
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
