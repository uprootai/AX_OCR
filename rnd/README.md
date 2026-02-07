# AX POC - R&D (Research & Development)

> **최종 업데이트**: 2026-02-06
> **목적**: 프로젝트 관련 연구 개발, SOTA 논문 수집, 실험 및 벤치마크 관리

---

## 현재 시스템 현황

| 항목 | 값 |
|------|-----|
| **API 서비스** | 21개 |
| **테스트** | 549개 (gateway 364 + web-ui 185) |
| **노드 정의** | 29개 |
| **SOTA 부합도** | ~82% |
| **DSE Bearing 배치 분석** | 53/53 세션 완료 (2,710 치수) |

---

## 디렉토리 구조

```
rnd/
├── README.md                 # 이 파일
├── SOTA_GAP_ANALYSIS.md     # ⭐ SOTA vs 현재 시스템 Gap 분석
├── IMPLEMENTATION_DETAILS.md # SOTA 세부 파라미터 설정
├── TRAINING_GUIDES.md        # API별 커스텀 학습 가이드
├── YOLOV12_UPGRADE_PLAN.md  # ⏳ YOLOv12 업그레이드 계획 (신규)
├── papers/                   # 논문 수집 및 정리
│   └── README.md            # 49개 SOTA 논문 인덱스
├── experiments/             # 실험 기록
│   ├── doclayout_yolo/      # ✅ DocLayout-YOLO 테스트 (2025-12-31)
│   ├── bwms_pipeline_improvement/  # ✅ BWMS 파이프라인 개선 (2026-01-20)
│   └── pid2graph_benchmark_analysis.md  # ✅ PID2Graph 벤치마크 (2026-01-19)
├── benchmarks/              # 성능 벤치마크
│   └── pid2graph/           # ✅ PID2Graph 벤치마크 결과
└── models/                  # 모델 실험 및 가중치
    └── pid2graph_yolo11n_finetuned.pt  # ✅ Fine-tuned 모델 (16MB)
```

---

## SOTA Gap 분석 결과 요약

**현재 시스템 SOTA 부합도: ~82%** (2026-02-06 업데이트)

| 영역 | 부합도 | 현재 | SOTA | Gap |
|------|--------|------|------|-----|
| Object Detection | ✅ 100% | YOLOv11 | YOLOv11 | 없음 |
| OCR/Document | ✅ 95% | **6엔진 가중 투표** | PaddleOCR 3.0 | ✅ 앙상블 완료 |
| GD&T Recognition | ✅ 85% | YOLO 기반 | YOLO + PARSeq | 텍스트 인식 |
| VLM | ✅ 80% | **CoT 추론 (v1.1)** | LLaVA-CoT | ✅ 업그레이드 완료 |
| Layout Analysis | ⚠️ 70% | **DocLayout-YOLO 테스트** | SCAN | Fine-tuning 필요 |
| P&ID Analysis | ⚠️ 65% | **PID2Graph Fine-tuned** | Relationformer | End-to-End |

**상세 분석**: [SOTA_GAP_ANALYSIS.md](SOTA_GAP_ANALYSIS.md)

---

## 논문 수집 현황

**총 49개 논문** (2025-12-31 v2 심층 조사)

| 카테고리 | 수량 | 핵심 기술 | 적용 상태 |
|----------|------|-----------|----------|
| Object Detection | 12 | **YOLOv12**, YOLO26, RT-DETRv3, RF-DETR | ✅ YOLOv11 적용 |
| OCR & Document | 7 | PaddleOCR 3.0, TrOCR, DocTR | ✅ 6엔진 앙상블 |
| P&ID Analysis | 6 | Relationformer, PID2Graph | ✅ PID2Graph Fine-tuned |
| Vision-Language | 10 | **Qwen3-VL**, InternVL3.5, LLaVA-o1 | ✅ CoT 추론 적용 |
| Layout Analysis | 10 | **DocLayout-YOLO**, SCAN, SFDLA | ✅ 테스트 완료 |
| GD&T Recognition | 4 | YOLOv8/v11 기반 | ✅ YOLO 기반 적용 |

자세한 논문 목록: [papers/README.md](papers/README.md)

---

## R&D 로드맵 (GPU 제약 반영, RTX 3080 8GB)

### 완료 ✅
| 연구 주제 | 적용 대상 API | 상태 | 완료일 |
|-----------|--------------|------|--------|
| YOLOv11 아키텍처 | YOLO (5005) | ✅ 적용됨 | 2025-12 |
| PaddleOCR 3.0 업그레이드 | PaddleOCR (5006) | ✅ 완료 | 2025-12-31 |
| LLaVA-CoT 단계별 추론 | VL (5004) | ✅ 완료 | 2025-12-31 |
| DocLayout-YOLO 테스트 | Layout Analysis | ✅ 완료 (4GB VRAM, 40ms/img) | 2025-12-31 |
| **PID2Graph Fine-tuning** | YOLO (5005) | ✅ 완료 (mAP50: 68.5%, Recall: 66.0%) | 2026-01-19 |
| **BWMS 파이프라인 개선** | Design Checker | ✅ 완료 (4개 실험) | 2026-01-20 |
| **OCR 6엔진 가중 투표** | dimension_service | ✅ 완료 (`_merge_multi_engine()`) | 2026-02-06 |
| **Table Detector 후처리** | Table Detector | ✅ 완료 (crop upscale, reocr) | 2026-02-06 |
| **DSE Bearing BOM 워크플로우** | Blueprint AI BOM | ✅ Phase 1-3 완료 | 2026-02-04 |
| **템플릿 버전 관리** | Blueprint AI BOM | ✅ 완료 (히스토리, 롤백, 비교) | 2026-02-06 |

### 실현 가능 (P1)
| 연구 주제 | GPU 요구 | 상태 |
|-----------|----------|------|
| DocLayout-YOLO Fine-tuning | ~2-4GB | 📋 도면 전용 클래스 학습 필요 |
| PP-StructureV3 | ~1-2GB | 📋 진행 가능 |

### 대기
| 연구 주제 | 상태 | 비고 |
|-----------|------|------|
| YOLOv12 | ⏳ 미출시 | Ultralytics 릴리스 대기 |

### GPU 제약으로 제외
| 연구 주제 | GPU 요구 | 대안 |
|-----------|----------|------|
| ~~Qwen3-VL~~ | 14GB+ | GPT-4o-mini API |
| ~~InternVL3.5~~ | 16GB+ | GPT-4o-mini API |
| ~~Relationformer~~ | 6-8GB | 현재 파이프라인 |
| ~~RF-DETR~~ | 6-8GB | YOLOv11 |

### 장기 참조
| 연구 주제 | 용도 |
|-----------|------|
| Drawing2CAD | 2D→3D 연구 |
| PID2Graph | ✅ 벤치마크 완료 |

---

## 실험 계획

### 2025-Q1 계획

1. **YOLOv11 vs YOLOv8 비교 실험**
   - 대상: P&ID 심볼 검출
   - 지표: mAP, 추론 속도, VRAM 사용량
   - 데이터: TECHCROSS 샘플 도면

2. **PaddleOCR 3.0 업그레이드 테스트**
   - 대상: 치수 텍스트 인식
   - 지표: CER, WER, 처리 속도
   - 비교: 현재 버전 vs 3.0

3. **LLaVA-o1 도면 분류 테스트**
   - 대상: 도면 타입 분류 (기계, P&ID, 조립도)
   - 지표: 정확도, 추론 시간
   - 비교: 현재 VL API vs LLaVA-o1

---

## 데이터셋 수집 계획

| 데이터셋 | 출처 | 용도 | 수집 상태 |
|----------|------|------|----------|
| PID2Graph | arXiv 2411.13929 | P&ID 학습 | ✅ 완료 (9.3GB, 1000장 학습) |
| DocLayNet | arXiv 2206.01062 | 레이아웃 학습 | 📋 계획 |
| TECHCROSS 도면 | 고객 제공 | BWMS 특화 | ✅ 일부 확보 |
| 기계 도면 (사내) | 기존 데이터 | GD&T 학습 | 📋 계획 |

---

## 관련 링크

- **논문 인덱스**: [papers/README.md](papers/README.md)
- **프로젝트 메인**: [../CLAUDE.md](../CLAUDE.md)
- **아키텍처 문서**: [../web-ui/public/docs/architecture/](../web-ui/public/docs/architecture/)
- **기존 인사이트**: [../docs/insights/](../docs/insights/)

---

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| **2026-02-06** | **R&D 문서 갱신**: 시스템 현황 업데이트 (21 API, 549 테스트, 29 노드), OCR 6엔진 앙상블 반영 |
| 2026-02-06 | **OCR 6엔진 가중 투표 완료**: paddleocr, edocr2, easyocr, trocr, suryaocr, doctr 통합 |
| 2026-02-06 | **Table Detector 후처리 강화**: crop upscale, cell reocr 기본 활성화 |
| 2026-02-06 | **템플릿 버전 관리 완료**: 스냅샷, 롤백, 버전 비교 기능 |
| 2026-02-05 | **DSE Bearing 배치 분석 100%**: 53/53 세션, 2,710 치수 추출 |
| 2026-02-04 | **BOM 계층 워크플로우 Phase 1-3 완료**: PDF 파싱, 도면 매칭, 견적 집계 |
| 2026-01-20 | **BWMS 파이프라인 개선 완료**: YOLO 신뢰도, Line Detector 노이즈, Design Checker 규칙 최적화 |
| 2026-01-19 | **PID2Graph Fine-tuning 완료**: YOLOv11n 기반, mAP50 68.5%, Recall 66.0% |
| 2025-12-31 | **DocLayout-YOLO 테스트 완료**: 4GB VRAM, 40ms 추론 속도 |
| 2025-12-31 | **SOTA 심층 조사**: 49개 논문 수집, YOLOv12/Qwen3-VL 등 후보 발견 |
| 2025-12-31 | VL API v1.1.0: LLaVA-CoT 스타일 다단계 추론 추가 |
| 2025-12-31 | PaddleOCR 3.0 업그레이드 완료 (PP-OCRv5) |
| 2025-12-31 | R&D 디렉토리 생성, 35개 논문 수집 |

---

*작성자*: Claude Code (Opus 4.5)
*최종 업데이트*: 2026-02-06
