# S05: 멀티모달 VLM 실험

> Claude Vision / GPT-4 Vision으로 GAR 이미지에서 TAG 추출 비교

| 항목 | 값 |
|------|---|
| 상태 | ✅ Done |
| 의존성 | S01 (OCR 결과와 비교용) |

---

## 실험 내용

### 실험 A: 전체 이미지 → VLM

프롬프트 예시:
```
이 엔지니어링 도면에서 장비 TAG 라벨을 모두 추출해주세요.
TAG는 알파벳으로 시작하는 식별자입니다 (예: V01, PT07, TT01, FT01).
숫자만 있는 것(치수)은 제외하세요.
```

### 실험 B: 뷰별 크롭 → VLM

각 뷰(Top/Front/Right)를 크롭한 이미지로 개별 요청

### 실험 C: OCR + VLM 하이브리드

1. OCR로 1차 텍스트 추출
2. VLM에 이미지 + OCR 결과를 함께 제공
3. VLM이 OCR 결과를 교정/보완

---

## 비교 대상

| 방식 | TAG Recall | Precision | 비용 | 속도 |
|------|-----------|-----------|------|------|
| OCR 단독 (S01 최적) | ? | ? | 낮음 | 빠름 |
| VLM 단독 | ? | ? | 높음 | 느림 |
| OCR + VLM 하이브리드 | ? | ? | 중간 | 중간 |

---

## 결과 (2026-03-25)

Claude Vision으로 GAR 3페이지를 6개 영역으로 크롭하여 분석. **GT 24개 TAG 확립**.

- 전체 이미지 1장으로는 해상도 부족 → 크롭 필수
- 크롭 후 모든 TAG 식별 성공 (24/24)
- PaddleOCR 대비: Claude Vision 100% vs PaddleOCR 41.7%
- 이미지에 없는 TAG 3개 확인: PT06, PI01, ORI (Part List에만 존재)

## 완료 조건

- [x] Claude Vision으로 전체 이미지 TAG 추출 (크롭 방식으로 24개 확인)
- [x] OCR vs VLM 결과 비교 (PaddleOCR 41.7% vs Claude Vision 100%)
- [ ] ~~하이브리드 방식~~ → S02(뷰별 분리)에서 PaddleOCR 개선 후 진행
