# S04: OCR 앙상블 (PaddleOCR + Tesseract)

> 두 엔진의 결과를 합산하여 TAG 검출률 100% 목표

| 항목 | 값 |
|------|---|
| 상태 | ✅ Done |
| 의존성 | S03 (자동 크롭) |

---

## 근거

E10에서 확인된 보완 관계:
- PaddleOCR: V11-2, V15 놓침
- Tesseract: V11-2, V15 검출 (유일하게)
- 합산 시 95.8% → 100% 가능

---

## 완료 조건

- [ ] PaddleOCR + Tesseract 결과 합산 로직 구현
- [ ] TAG Recall 98%+ 달성
- [ ] False positive 증가 없이 Recall 향상 확인
