# 레이아웃 디텍션 실험 보고서

> **날짜**: 2026-03-24
> **목적**: 기계도면 레이아웃 디텍션이 OD/ID/W 추출 파이프라인을 개선할 수 있는지 검증
> **결론**: 원 검출 가이드 효과는 미미하나, 비베어링 필터링 + 영역 제외로 실질적 가치 확인

---

## 실험 구성

### Phase 1: Grounding DINO 제로샷 (학습 없음)

| 항목 | 설정 |
|------|------|
| 모델 | `IDEA-Research/grounding-dino-base` |
| 대상 | GT-1, GT-2 + 샘플 3개 (총 5개) |
| 프롬프트 | 4세트 (layout_basic, layout_detailed, engineering, structural) |
| 신뢰도 | 0.25~0.69 (낮음, 기계도면 미학습) |

**결과**: 타이틀 블록, 메인 도면, 테이블, 원형 구조 검출 가능 확인. 신뢰도 낮아 프로덕션 불가.

### Phase 2: YOLO v11s 커스텀 파인튜닝

| 항목 | 설정 |
|------|------|
| Pre-label | Grounding DINO 결과 (87개 도면, 1196 bbox) |
| 모델 | YOLO v11s (9.4M params) |
| 학습 | 10 epochs, 640px, batch=8 |
| 학습 시간 | **54초** |

**클래스 (6개)**:

| ID | 클래스 | 검출 수 | AP50 |
|:--:|--------|:------:|:----:|
| 0 | title_block | 218 | 0.822 |
| 1 | main_view | 169 | 0.921 |
| 2 | section_view | 167 | 0.951 |
| 3 | table | 225 | 0.957 |
| 4 | notes | 67 | 0.980 |
| 5 | circle_feature | 350 | 0.939 |

**전체 mAP50: 0.929, mAP50-95: 0.844, 추론속도: 3.8ms/이미지**

### Phase 3: 파이프라인 통합 PoC

| 시나리오 | TD0062037 오차 | TD0062055 오차 | TD0060700 |
|---------|:---:|:---:|:---:|
| 기존 K 방법 (전체 이미지) | **0.134** | **0.031** | 판정 불가 |
| 레이아웃 가이드 (크롭) | 0.168 | 0.053 | **비베어링 정확 판정** |

---

## 핵심 발견

### 1. 원 검출 가이드는 효과 미미

기존 K 방법의 컨투어+타원피팅이 전체 이미지에서도 충분히 정확.
레이아웃 크롭은 마진 계산, bbox 부정확 등으로 오히려 미세한 노이즈 추가.

### 2. 비베어링 자동 판정 — 즉시 적용 가능

`circle_feature` 검출 수 = 0 → 비베어링 즉시 판정.
TD0060700 (BOLT TORQUE TABLE): `table` 4개, `circle_feature` 0개 → 정확 판정.
기존 방식은 OCR 실행 후 soft filter로만 판정 가능 (11초 소요).

### 3. 영역 제외 — 토크값 오인식 방지

`notes`, `table` 영역의 OCR 결과를 치수 후보에서 제외하면
Fix 4 (NM/토크 필터)가 불필요해짐.

### 4. title_block OCR — 부품명 자동 추출

`title_block` 영역만 OCR하면 도면 제목(BEARING, CASING 등) 정확 추출 가능.
현재 soft filter의 `title_missing_bearing` penalty를 hard evidence로 대체.

---

## 파일 구조

```
rnd/experiments/grounding_dino_layout/
├── REPORT.md                    # 이 보고서
├── test_grounding_dino.py       # Phase 1: 제로샷 테스트
├── batch_prelabel.py            # Phase 2: 87개 pre-label 생성
├── train_yolo.py                # Phase 2: YOLO 학습
├── inference_demo.py            # Phase 2: 추론 시각화
├── test_layout_pipeline.py      # Phase 3: 통합 PoC
├── dataset/                     # YOLO 학습 데이터
│   ├── data.yaml
│   ├── images/train/ (87 symlinks)
│   └── labels/train/ (87 txt)
├── runs/layout_v1*/             # 학습 결과
│   └── weights/best.pt          # best 모델 (19.2MB)
└── results/                     # 시각화 결과
    ├── summary.json
    ├── TD0062037/               # 제로샷 결과
    ├── yolo_inference/          # YOLO 추론 결과
    └── pipeline_test/           # 통합 비교 결과
```

## 모델 경로

```
runs/layout_v12/weights/best.pt  (19.2MB, YOLO v11s, 6 classes)
```

---

## 적용 권장 사항

| 우선순위 | 적용 | 구현 | 효과 |
|:---:|------|------|------|
| 1 | 비베어링 필터 | `circle_feature` 0개 → 스킵 | 25개 도면 처리 불요, 배치 ~30% 시간 절감 |
| 2 | notes/table 영역 제외 | OCR 결과에서 해당 bbox 내 텍스트 필터 | NM/토크 오인식 원천 차단 |
| 3 | title_block OCR | 해당 영역만 OCR → 부품명 추출 | 베어링 유형 hard classification |
| 4 | 어노테이션 정제 + 재학습 | CVAT에서 pre-label 수정 → medium 모델 | mAP 0.93 → 0.95+ |

## 참고 논문

- [DocLayout-YOLO (arXiv:2410.12628)](https://arxiv.org/abs/2410.12628) — 문서 레이아웃 YOLO
- [Florence-2 Engineering Drawing (arXiv:2411.03707)](https://arxiv.org/abs/2411.03707) — 400장 GD&T 파인튜닝
- [From Drawings to Decisions (arXiv:2506.17374)](https://arxiv.org/abs/2506.17374) — YOLOv11-OBB + VLM 파이프라인
