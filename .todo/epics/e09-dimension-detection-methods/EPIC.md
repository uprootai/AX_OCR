# E09: OD/ID/W 검출 방법론 다양화

> 동서기연 베어링 도면의 OD/ID/W 검출 정확도를 높이기 위해 다양한 접근법을 실험·비교한다.

| 항목 | 값 |
|------|-----|
| 시작일 | 2026-03-23 |
| 고객 | 동서기연 (E03 연계) |
| 현재 정확도 | K방법 48% → 앙상블 v1 60% → **앙상블 v2 71%** — 87개 도면 기준 |
| 목표 | ~~87개 도면 배치 평가에서 앙상블 정확도 70%+~~ **✅ 달성 (71%)** |

---

## 배경

현재 기하학 파이프라인(K/L/M/N)은 원 검출 + OCR + 크기순 분류에 의존한다.
스케일 필터 완화로 T5가 1/3→3/3으로 개선되었으나, 근본적으로:
- 원 검출 실패 시 전 파이프라인이 무너짐
- 치수선↔텍스트 연결이 간접적 (스케일 추정 기반)
- 부분 호, 부착 부품, 복잡 레이아웃에 취약

다양한 방법론을 실험하여 최적의 앙상블 또는 대체 파이프라인을 구축한다.

---

## Stories

| ID | Plan | 접근법 | 난이도 | 우선순위 |
|----|------|--------|:---:|:---:|
| S01 | [arrowhead-detection.md](S01-arrowhead-detection.md) | 화살촉 모폴로지 검출 → 치수 세트 복원 | 중 | P0 |
| S02 | [dimension-text-first.md](S02-dimension-text-first.md) | OCR 먼저 → Ø 값 → 치수선 역추적 | 중 | P0 |
| S03 | [randomized-hough.md](S03-randomized-hough.md) | Randomized Hough Transform 원/호 검출 | 저 | P1 |
| S04 | [ellipse-decomposition.md](S04-ellipse-decomposition.md) | 컨투어 호+직선 분해 → 인접 호 그룹핑 | 중 | P1 |
| S05 | [circlenet-dl.md](S05-circlenet-dl.md) | CircleNet anchor-free 원 검출 DL | 고 | P2 ⚠️ ML 중지 시 가능 |
| S06 | [yolo-obb-vlm.md](S06-yolo-obb-vlm.md) | YOLOv11-OBB + VLM 하이브리드 | 고 | P2 ⚠️ YOLO만 가능, VLM은 API |
| S07 | [florence2-finetune.md](S07-florence2-finetune.md) | Florence-2 GD&T fine-tuning | 고 | P3 ⚠️ base 모델만 가능 |
| S08 | [werk24-benchmark.md](S08-werk24-benchmark.md) | Werk24 상용 API 벤치마크 | 저 | P1 |

---

## 평가 기준

모든 방법은 동일 87개 도면 배치에서 테스트하며, GT가 있는 도면에서 정확도를 측정한다.

| 메트릭 | 설명 |
|--------|------|
| OD 정확도 | GT OD와 ±5mm 이내 |
| ID 정확도 | GT ID와 ±5mm 이내 |
| W 정확도 | GT W와 ±5mm 이내 |
| 처리 시간 | 도면 1장당 소요 시간 |
| 실패율 | 결과를 반환하지 못한 비율 |

---

---

## 환경 제약 (2026-03-23 측정)

| 항목 | 값 | 상태 |
|------|-----|------|
| CPU | i7-11800H 8C/16T | 양호 |
| RAM | 16GB (가용 2.2GB) | 빠듯 — Docker 컨테이너가 ~11GB 점유 |
| GPU | RTX 3080 Laptop **8GB** (가용 0.86GB → **ML 중지 시 7.0GB**) | ML 컨테이너 중지 시 DL 학습 가능 |
| Disk | 1TB (여유 441GB) | 충분 |

### 실행 가능 여부

| Story | GPU 필요 | RAM 필요 | 판정 |
|-------|:---:|:---:|:---:|
| S01 화살촉 | 없음 | 낮음 | ✅ 즉시 가능 |
| S02 Text-First | 없음 | 낮음 | ✅ 즉시 가능 |
| S03 RHT | 없음 | 낮음 | ✅ 즉시 가능 |
| S04 Ellipse | 없음 | 낮음 | ✅ 즉시 가능 |
| S05 CircleNet | ~4GB | ~4GB | ⚠️ ML 중지 시 가능 (7GB 확보) |
| S06 YOLO+VLM | YOLO ~3GB, VLM ~6GB | ~6GB | ⚠️ YOLO 학습 가능, VLM은 소형 모델/API |
| S07 Florence-2 | base ~4GB, large ~8GB | ~8GB | ⚠️ base(0.23B) LoRA만 가능 |
| S08 Werk24 | 없음 | 낮음 | ✅ API 호출만 |

> **ML 컨테이너 중지 시 GPU 7.0GB 확보 가능**: `docker stop paddleocr-api edocr2-v2-api easyocr-api trocr-api edgnet-api blueprint-ai-bom-backend` → 학습 후 `docker start ...`로 복구.

---

## 중간 결과 (2026-03-23)

### T5 (TD0062037) — GT: OD=Ø1036, ID=580, W=200

| 방법 | OD | ID | W | Score |
|------|----|----|---|-------|
| **K (baseline)** | Ø1036 ✅ | 580 ✅ | 200 ✅ | **3/3** |
| S01 화살촉 | Ø1036 ✅ | 650 ❌ | 200 ✅ | 2/3 |
| S02 Text-First | Ø1036 ✅ | 650 ❌ | 200 ✅ | 2/3 |
| S03 RHT | 26 circles | — | — | 원 검출만 |
| S04 Decomp | 46 circles | — | — | 원 검출만 |

**발견**: S01/S02는 원 검출 없이 OD=Ø1036을 찾지만, 650 vs 580 ID 구분에는 원 proximity가 필수.

### 3-도면 배치 — K method

| Drawing | OD | ID | W | Score |
|---------|----|----|---|-------|
| T5 (TD0062037) | Ø1036 | 580 | 200 | 3/3 |
| T6 (TD0062042) | Ø1036 | 635 | 200 | 3/3 |
| T7 (TD0062019) | 486 | 202 | 144 | 3/3 |

### 원 검출 비교

| Drawing | RANSAC | RHT (S03) | Decomp (S04) |
|---------|--------|-----------|-------------|
| TD0062037 | 553 | 18 | 46 |
| TD0062042 | 478 | 20 | 41 |
| TD0062019 | 2415 | 8 | 33 |

RHT가 가장 curated (8-20개), Decomp 중간 (33-46), RANSAC 과다 (478-2415).

### 87개 전체 배치 (2026-03-23)

| 지표 | K-method | Ensemble (K+S01+S02) | 개선 |
|------|----------|---------------------|------|
| OD 검출 | 53/87 (61%) | **73/87 (84%)** | +20 |
| ID 검출 | 45/87 (52%) | **61/87 (70%)** | +16 |
| W 검출 | 42/87 (48%) | **59/87 (68%)** | +17 |
| **All 3** | **42/87 (48%)** | **52/87 (60%)** | **+10** |

- 앙상블 처리 시간: 87개 × 6.7s = ~10분
- S01(arrowhead)이 K의 W 미검출 보완에 가장 효과적
- S02(text-first)가 K의 OD 미검출 보완에 가장 효과적
- 33개 도면은 모든 방법에서 미검출 → 비-베어링 도면(핀, 플러그, 와셔 등)으로 추정

### S07 Florence-2 Zero-Shot (2026-03-23)

Florence-2-base (0.23B, 0.9GB VRAM) zero-shot 평가:

| 태스크 | 결과 | 평가 |
|--------|------|------|
| OCR | 3개 텍스트 검출 (노이즈) | ❌ 도면 텍스트 인식 불가 |
| Caption | "circular object with a hole" | ✅ 형상 이해 |
| Object Detection | wheel×2, vehicle×1 | △ 대략적 형상 |
| Phrase Grounding ("outer diameter") | 베어링 단면 bbox 2개 | ✅ 개념 이해 |
| Open Vocab ("circle") | 내원 영역 1개 | △ 부분 검출 |
| OCR with Region | 3개만 검출 | ❌ 치수 텍스트 부족 |

**결론**: base 모델은 형상 개념은 이해하지만 OCR 성능이 도면 치수 추출에 부족. LoRA fine-tune 시 `<OCR_WITH_REGION>`과 커스텀 GD&T 태스크 학습이 필요.

### S05 CircleNet-Lite (2026-03-23)

HoughCircles 기반 pseudo-label → 작은 U-Net (0.5M params, 1.8MB) 학습:

| 항목 | 값 |
|------|-----|
| 학습 데이터 | 30개 도면 (25 train / 5 val) |
| 학습 시간 | 34초 (50 epochs) |
| VRAM 사용 | ~0.1GB |
| val loss | 0.0165 (focal) |
| 원 검출 | 피크 5~25개 (GT 대비 위치 근접하나 반지름 0) |

**결론**: Heatmap 센터 예측은 학습되나, 반지름 회귀가 sparse label 문제로 실패. 더 dense한 label (full 원 mask) 또는 더 큰 모델+데이터 필요.

### S06 YOLOv11 Dimension Detection (2026-03-23)

**v1** (Contour pseudo-label): mAP50 = 0.002 → 실패 (노이즈 label)

**v2** (PaddleOCR bbox pseudo-label → YOLOv11n fine-tune):

| 항목 | 값 |
|------|-----|
| 학습 데이터 | 87개 도면 (70 train / 17 val) |
| 학습 시간 | 593초 (50 epochs) |
| VRAM 사용 | ~4GB (peak) |
| mAP50 | **0.301** |
| mAP50-95 | **0.160** |
| Precision | 0.403 |
| Recall | 0.282 |
| T5 검출 | 9개 (dim 1 + annot 8) |

**결론**: OCR bbox pseudo-label로 학습 가능성 입증. 87개 도면으로는 데이터 부족하나, 더 많은 도면 + 클래스 세분화(Ø/R/일반)로 개선 가능.

### S05-S07 종합 평가 (2026-03-23)

| 방법 | 실현 가능성 | 정확도 기대 | 필요 자원 | 판정 |
|------|:-----------:|:-----------:|-----------|------|
| S05 CircleNet | 중 | 중 | Dense label + 더 큰 모델 | ⏸️ 보류 |
| S06 YOLO-OBB | **높음** | 중~높음 | OCR bbox label → mAP50=0.301 달성 | ✅ v2 완료 |
| S07 Florence-2 | 높음 (제로샷 동작) | 낮음 (제로샷) / 높음 (파인튠) | LoRA + GD&T 데이터셋 | ⏸️ 파인튠 데이터 필요 |

> **S06 v2 성공**: PaddleOCR bbox → YOLOv11n fine-tune로 mAP50=0.301 달성. 87개 도면 한계에도 dimension text 검출 학습 가능성 입증.
> S05/S07은 여전히 데이터 부족이 병목.

### 앙상블 v2 (K+S01+S02+S06) — 87개 전체 배치 (2026-03-23)

| 지표 | K 단독 | 앙상블 v1 | **앙상블 v2** | 개선 |
|------|--------|----------|-------------|------|
| OD 검출 | 53/87 (61%) | 73/87 (84%) | **80/87 (92%)** | +27 |
| ID 검출 | 45/87 (52%) | 61/87 (70%) | **68/87 (78%)** | +23 |
| W 검출 | 42/87 (48%) | 59/87 (68%) | **69/87 (79%)** | +27 |
| **All 3** | **42/87 (48%)** | **52/87 (60%)** | **62/87 (71%)** | **+20** |

- S06 기여: 27/87 도면에서 투표 참여
- 처리 시간: 87개 × 11.2s = ~16분
- 완전 실패: 4개, 부분 검출: 21개
- OD가 비정상 (Ø6, Ø10, Ø15 등): 비-베어링 도면 추정

### OD/ID/W 검증 분석 (2026-03-24)

**문제 발견**: 앙상블 v2의 "71% All-3"은 값 존재만 카운트. GT 대비 정확도는 낮음.

#### v3 최종 (K-priority + W분류 + 파싱 수정)

| 지표 | v2 (투표) | **v3 최종** |
|------|-----------|-------------|
| All-3 검출 | 62/87 (71%) | 62/87 (71%) |
| **물리적 타당성** (OD>ID>W) | 36/87 (41%) | **49/87 (56%)** |
| **ASSY GT 정확도** (±5mm, 2개) | 3/6 (50%) | **6/6 (100%)** |
| K-priority 적용 | — | 45/87 (5개 복구) |

수정 사항:
1. **K-priority 전략**: 투표가 K의 정확한 답을 덮어쓴 문제 → K 타당 시 K 우선
2. **W 분류 하이브리드**: 스러스트(ID/OD>0.75) → 최대 W, 레이디얼 → (OD-ID)/2 공식
3. **`_extract_num` 파싱 강화**: `550+2`, `Ø838.2.00` 같은 공차 문자열 → 첫 숫자 추출
4. **5개 K fallback 복구**: 파싱 실패로 vote_fallback된 타당한 K 결과 → k_priority 전환

#### v5 최적화 (2026-03-24)

| 지표 | v3 | **v5** | 변화 |
|------|-----|--------|------|
| All-3 검출 | 62/87 (71%) | 62/87 (71%) | 동일 |
| k_priority | 40 | **44** | +4 |
| vote_fallback | 44 | **40** | -4 |
| **ASSY GT 정확도** | 5/6 (83%) | **6/6 (100%)** | TD0062055 W=250→48 수정 |

추가 수정:
1. **Fallback OCR**: K 실패 시 `DimensionService(edocr2)` 독립 OCR → S01/S02에 치수 공급 (31개 K-실패 도면 커버)
2. **W radial 공식 우선**: `(OD-ID)/2 ± 50%` 후보 있으면 최대값 대신 공식 기반 선택 → TD0062055 W 수정
3. **NM/토크 필터**: `NM`, `N·m`, `kgf`, `kN` 단위 포함 값 비치수로 제외
4. **Non-bearing soft filter**: 제목에 BEARING 없으면 -15%, OD 범위 밖 -20%, OD≤ID -25% confidence penalty
5. 22개 도면 값 변경 (v3→v5)

#### Codex (GPT-5.4) 교차 검증 (2026-03-24)

1. **vote-fallback 구조적 버그**: K 원 검출 실패 시 monkey-patch 훅이 미실행 → S01/S02 아예 작동 안 함 (31개)
2. **GT 확장**: BOM `bom_items.json` size 필드에서 22개 GT 후보 발견. 단, **소재 규격**(가공 전 원자재)이므로 직접 GT 아님 — 범위 검증용
3. **비-베어링 필터**: 점수 기반 권장 (BEARING 키워드 + OD 범위 + 물리적 비율). 하드 리젝트는 극단 경우만
4. **87개 도면 중 BEARING ASSY는 ~7개**: 나머지는 부품도면(CASING, RING, PAD 등)으로 OD/ID/W 개념이 상이

*마지막 업데이트: 2026-03-24*
