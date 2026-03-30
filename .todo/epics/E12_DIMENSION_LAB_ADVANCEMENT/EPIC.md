# E12: Dimension Lab 고도화 — 동서기연 OD/ID/W 검출 정확도 향상

> **목표**: 앙상블 v5 (All-3 71%, GT 100%) → v7 (All-3 85%+, GT n=7+)
> **기간**: 2026.04 ~ 2026.06 (약 8주)
> **우선순위**: HIGH (동서기연 납품 일정 연동)

---

## 현재 상태 (As-Is)

| 지표 | 값 | 비고 |
|---|---|---|
| All-3 검출률 | 71% (62/87) | K+S01+S02+S06 앙상블 |
| GT 정확도 | 100% (6/6) | 2개 ASSY 도면만 GT 확보 |
| 비베어링 도면 | ~25/87 | OD/ID/W 의미 없는 도면 |
| 실질 검출률 | ~84% (52/62) | 베어링 관련 도면만 |
| 처리 시간 | 11초/도면 (v5) | v3은 6.7초 |

### 현재 보유 자산
- ✅ 7개 OCR 엔진 Docker 운영 중
- ✅ 앙상블 v5 코드 (K-priority + 5 fixes)
- ✅ 87도면 전수 분석 완료 (6,790 치수)
- ✅ Dimension Lab UI (배치 평가, 리더보드)
- ✅ S01~S04, S06 실험 코드
- ⏸️ S05 CircleNet (코드 있음, 라벨 부족)
- ⏸️ S07 Florence-2 (코드 있음, GT 부족)

### 미해결 과제
- GT 데이터 2개뿐 (n=2 → n=7+ 필요)
- 비베어링 도면 자동 필터링 미완성
- S01~S07 실험 문서에 캡쳐 이미지 없음
- 고객 단가표/견적 양식 미수령
- Title block OCR 0% (개선 필요)

---

## 로드맵

### Phase 1: GT 확보 + 비베어링 분류 (Week 1~2)

**Story S01: ASSY 도면 GT 5건 추가 확보**
- [ ] 87도면 중 ASSY ~7건 식별 (index/results에서 확인)
- [ ] 각 ASSY 도면의 OD/ID/W 수동 측정 (도면 읽기)
- [ ] GT JSON 파일 생성 (n=2 → n=7)
- [ ] BOM size 필드 ±10% 교차 검증
- [ ] Dimension Lab에서 GT 세트로 배치 평가 실행

**Story S02: 비베어링 도면 자동 분류 강화**
- [ ] 현재 soft filter (confidence penalty) 분석
- [ ] Title keyword 기반 분류 (pin/washer/seal/bolt → 비베어링)
- [ ] OD 범위 필터 (50~2000mm 벗어나면 비베어링)
- [ ] OD≤ID 역전 검출 (비정상)
- [ ] 87도면 전수 재분류 → 베어링/비베어링 라벨링
- [ ] 실질 검출률 재계산 (62 → ? 베어링 도면)

**Story S03: S01~S07 실험 문서 캡쳐 보강**
- [ ] S01 화살촉: 검출 결과 오버레이 캡쳐 (Playwright)
- [ ] S02 Text-First: Ø 심볼 검출 + 방향 분석 캡쳐
- [ ] S03 RHT: 원 검출 비교 (RANSAC vs RHT vs Decomp)
- [ ] S04 Ellipse: 호 분해 + 그룹핑 시각화
- [ ] S06 YOLO-OBB: bbox 검출 결과 오버레이
- [ ] batch-test-report: 87도면 요약 차트
- [ ] codex-validation: 구조 리뷰 다이어그램

---

### Phase 2: 앙상블 v6 — 정확도 향상 (Week 3~4)

**Story S04: K 메서드 원 검출 개선**
- [ ] 좌측 편향 도면 대응 (T5 사례 일반화)
- [ ] ASSY vs Part 도면별 원 검출 파라미터 분리
- [ ] Detail section 영역 제외 로직 (Casing 사례)
- [ ] 원 검출 실패 시 S03 RHT/S04 Ellipse fallback 체계화

**Story S05: W (폭) 검출 정확도 개선**
- [ ] Radial formula `W ≈ (OD-ID)/2 ± 50%` 적용 범위 확대
- [ ] Thrust vs Radial 자동 분류 개선 (ID/OD ratio 임계값 조정)
- [ ] S01 화살촉 W 기여도 분석 + 가중치 최적화
- [ ] 수직 치수선 방향 분석 강화

**Story S06: 앙상블 투표 전략 개선**
- [ ] K-priority → K-validated 전략 (K 결과를 BOM ±10%로 검증)
- [ ] S01/S02 독립 실행 보장 (monkey-patch 의존성 제거)
- [ ] 확신도 기반 가중 투표 (K 높은 가중치, S06 보조)
- [ ] v6 배치 평가 → GT n=7 기준 정확도 측정

**목표**: All-3 71% → 80%+, GT 100% 유지 (n=7)

---

### Phase 3: S05/S07 재개 + 데이터 파이프라인 (Week 5~6)

**Story S07: S05 CircleNet 재시도**
- [ ] 87도면에서 Dense circle mask 라벨 생성 (반자동: HoughCircles + 수동 보정)
- [ ] DLA-34 + COCO pretrain 모델 구축
- [ ] 학습: 70 train / 17 val
- [ ] Radius regression 해결 확인
- [ ] K 원 검출 대비 성능 비교
- [ ] 앙상블 v6에 S05 추가 시 효과 측정

**Story S08: S07 Florence-2 LoRA 파인튜닝**
- [ ] GT n=7 + 87도면 OCR 결과 → LoRA 데이터셋 구축 (100~200쌍)
- [ ] 커스텀 태스크 정의: `<OD_ID_W>` 입력/출력 포맷
- [ ] `<OCR_WITH_REGION>` 강화 학습 (기술 도면 폰트)
- [ ] LoRA 학습 (RTX 3080, ~1시간)
- [ ] Zero-shot vs Fine-tuned 비교
- [ ] 앙상블 v6에 S07 추가 시 효과 측정

**Story S09: HITL 보정 데이터 → GT 자동 축적 파이프라인**
- [ ] Dimension Lab UI에서 사람이 보정한 OD/ID/W 결과 저장 API
- [ ] 보정 결과 → GT JSON 자동 추가
- [ ] 보정 패턴 통계 대시보드 (어떤 도면에서 어떤 값이 보정되었는지)
- [ ] GT n=7 → n=20+ 자동 성장 구조

---

### Phase 4: 앙상블 v7 + 견적 통합 (Week 7~8)

**Story S10: 앙상블 v7 최종 통합**
- [ ] v6 + S05(CircleNet) + S07(Florence-2) 통합
- [ ] GT n=20+ 기준 종합 평가
- [ ] All-3 85%+, GT 정확도 95%+ 목표
- [ ] 비베어링 자동 제외 → 실질 검출률 90%+ 목표
- [ ] 처리 시간 최적화 (병렬 추론)

**Story S11: 견적 자동화 연동**
- [ ] OD/ID/W 추출 → 재질 판별 → 단가 계산 파이프라인
- [ ] 동서기연 단가표 적용 (수령 후)
- [ ] 견적서 자동 생성 (Excel/PDF)
- [ ] 1차 테스트 결과 (₩3,200,466) 대비 정확도 검증
- [ ] 고객 피드백 반영

**Story S12: Title Block OCR 개선**
- [ ] 현재 0% → PaddleOCR 파인튜닝 적용
- [ ] 도면 번호/REV/재질/수량 자동 추출
- [ ] BOM 자동 매핑 (도면번호 → BOM 항목)

---

### Phase 5: 고객 납품 + BMT 연계 (Week 9~10)

**Story S13: 동서기연 2차 납품 패키지**
- [ ] 87도면 전수 OD/ID/W 결과 리포트
- [ ] 견적 자동화 데모 (웹 UI)
- [ ] 정확도 보고서 (GT 기준)
- [ ] 3차 미팅 준비

**Story S14: BMT 프로젝트 연계**
- [ ] 동서기연 Dimension Lab 경험 → BMT 파이프라인 적용
- [ ] OCR 앙상블 전략 공유 (PaddleOCR + Tesseract)
- [ ] HITL UI 공통 컴포넌트 추출
- [ ] Lab 실험 → BMT 도면 유형 적용 테스트

---

## 리스크 관리

| 리스크 | 영향 | 대응 |
|---|---|---|
| GT 데이터 추가 확보 실패 | Phase 2~3 정확도 검증 불가 | BOM ±10% 자동 검증으로 대체 |
| S05 CircleNet 재실패 | Phase 3 지연 | K 원 검출 파라미터 튜닝으로 대체 |
| S07 Florence-2 LoRA 부족 | Phase 3 지연 | S06 YOLO-OBB 고도화로 대체 |
| 동서기연 단가표 미수령 | Phase 4 견적 통합 불가 | 가견적(1차 결과 기준)으로 대체 |
| GPU 자원 부족 | S05/S07 학습 지연 | 클라우드 GPU 임시 활용 |

---

## 성공 지표

| 지표 | 현재 (v5) | Phase 2 (v6) | Phase 4 (v7) |
|---|---|---|---|
| All-3 검출률 | 71% | 80%+ | 85%+ |
| GT 정확도 | 100% (n=2) | 100% (n=7) | 95%+ (n=20+) |
| 비베어링 자동 제외 | soft filter | 90%+ 분류 | 95%+ 분류 |
| 처리 시간 | 11초/도면 | 10초/도면 | 8초/도면 |
| 견적 자동화 | 15% (54/361) | 30%+ | 50%+ |
| 실험 문서 캡쳐 | 10/18 | 18/18 | 18/18 |
