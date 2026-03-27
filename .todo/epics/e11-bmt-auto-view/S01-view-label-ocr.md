# S01: 뷰 라벨 OCR 검출

> "FRONT VIEW", "TOP VIEW", "RIGHT VIEW" 등 뷰 라벨 텍스트의 위치(bbox) 추출

| 항목 | 값 |
|------|---|
| 상태 | ✅ Done |
| 의존성 | 없음 |

---

## 접근법

E10 S01에서 PaddleOCR이 이미 검출한 텍스트 중 뷰 라벨 확인:

```
PaddleOCR 158개 텍스트 중:
  "FRONT VIEW" → bbox 있음
  "TOP VIEW" → bbox 있음
  "BOTTOM VIEW" → bbox 있음
  "'A' VIEW" → bbox 있음
  "RIGHT VIEW" → bbox 있음
  "BOTTOM VIEW BOLTING HOLE" → bbox 있음
```

이 bbox 좌표를 뷰 라벨로 식별하는 규칙:
- 텍스트에 "VIEW" 포함
- 또는 "BOTTOM", "TOP", "FRONT", "RIGHT" + "VIEW" 조합

---

## 완료 조건

- [ ] GAR 이미지에서 뷰 라벨 5~6개 bbox 추출
- [ ] 라벨명 → 뷰 타입 매핑 (FRONT/TOP/RIGHT/BOTTOM/A)
- [ ] bbox 좌표 정확성 검증 (이미지에서 시각 확인)
