# AX POC - R&D (Research & Development)

> **최종 업데이트**: 2025-12-31
> **목적**: 프로젝트 관련 연구 개발, SOTA 논문 수집, 실험 및 벤치마크 관리

---

## 디렉토리 구조

```
rnd/
├── README.md                 # 이 파일
├── SOTA_GAP_ANALYSIS.md     # ⭐ SOTA vs 현재 시스템 Gap 분석
├── IMPLEMENTATION_DETAILS.md # SOTA 세부 파라미터 설정
├── TRAINING_GUIDES.md        # API별 커스텀 학습 가이드
├── papers/                   # 논문 수집 및 정리
│   └── README.md            # 49개 SOTA 논문 인덱스
├── experiments/             # 실험 기록
│   └── doclayout_yolo/      # ✅ DocLayout-YOLO 테스트 (2025-12-31)
├── benchmarks/              # 성능 벤치마크
│   └── (향후 벤치마크 결과)
└── models/                  # 모델 실험 및 가중치
    └── (향후 커스텀 모델)
```

---

## SOTA Gap 분석 결과 요약

**현재 시스템 SOTA 부합도: ~81%** (2025-12-31 업데이트)

| 영역 | 부합도 | 현재 | SOTA | Gap |
|------|--------|------|------|-----|
| Object Detection | ✅ 100% | YOLOv11 | YOLOv11 | 없음 |
| OCR/Document | ✅ 95% | **PP-OCRv5 (3.0)** | PaddleOCR 3.0 | ✅ 업그레이드 완료 |
| GD&T Recognition | ✅ 85% | YOLO 기반 | YOLO + PARSeq | 텍스트 인식 |
| VLM | ✅ 80% | **CoT 추론 (v1.1)** | LLaVA-CoT | ✅ 업그레이드 완료 |
| Layout Analysis | ⚠️ 65% | 휴리스틱 | SCAN | 방법론 |
| P&ID Analysis | ⚠️ 60% | 모듈식 | Relationformer | End-to-End |

**상세 분석**: [SOTA_GAP_ANALYSIS.md](SOTA_GAP_ANALYSIS.md)

---

## 논문 수집 현황

**총 49개 논문** (2025-12-31 v2 심층 조사)

| 카테고리 | 수량 | 핵심 기술 |
|----------|------|-----------|
| Object Detection | 12 | **YOLOv12**, YOLO26, RT-DETRv3, RF-DETR |
| OCR & Document | 7 | PaddleOCR 3.0, TrOCR, DocTR |
| P&ID Analysis | 6 | Relationformer, PID2Graph |
| Vision-Language | 10 | **Qwen3-VL**, InternVL3.5, LLaVA-o1 |
| Layout Analysis | 10 | **DocLayout-YOLO**, SCAN, SFDLA |
| GD&T Recognition | 4 | YOLOv8/v11 기반 |

자세한 논문 목록: [papers/README.md](papers/README.md)

---

## R&D 로드맵 (GPU 제약 반영, RTX 3080 8GB)

### 완료 ✅
| 연구 주제 | 적용 대상 API | 상태 |
|-----------|--------------|------|
| YOLOv11 아키텍처 | YOLO (5005) | ✅ 적용됨 |
| PaddleOCR 3.0 업그레이드 | PaddleOCR (5006) | ✅ 완료 |
| LLaVA-CoT 단계별 추론 | VL (5004) | ✅ 완료 |
| **DocLayout-YOLO 테스트** | Layout Analysis | ✅ 완료 (4GB VRAM, 40ms/img) |

### 실현 가능 (P1)
| 연구 주제 | GPU 요구 | 상태 |
|-----------|----------|------|
| DocLayout-YOLO Fine-tuning | ~2-4GB | 📋 도면 전용 클래스 학습 필요 |
| PID2Graph 벤치마크 | 없음 | 📋 진행 가능 |
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
| PID2Graph | 벤치마크 데이터 |

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
| PID2Graph | arXiv 2411.13929 | P&ID 학습 | 📋 계획 |
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
| 2025-12-31 (v3) | **DocLayout-YOLO 테스트 완료**: 4GB VRAM, 40ms 추론 속도, 기계도면/P&ID 6개 이미지 테스트, Fine-tuning 필요성 확인 |
| 2025-12-31 (v2) | **SOTA 심층 조사**: 49개 논문 수집 (14개 신규), YOLOv12/Qwen3-VL/DocLayout-YOLO 등 차기 업그레이드 후보 발견 |
| 2025-12-31 | VL API v1.1.0: LLaVA-CoT 스타일 다단계 추론 추가, SOTA 부합도 80% → 81% |
| 2025-12-31 | PaddleOCR 3.0 업그레이드 완료 (PP-OCRv5), SOTA 부합도 75% → 80% |
| 2025-12-31 | R&D 디렉토리 생성, 35개 논문 수집 |

---

*작성자*: Claude Code (Opus 4.5)
*최종 업데이트*: 2025-12-31
