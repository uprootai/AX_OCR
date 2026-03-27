# S03: TAG vs 치수 필터링 + 엑셀 교차검증

> OCR 결과에서 TAG만 추출하고, 실제 Part List/ERP BOM과 교차 대조

| 항목 | 값 |
|------|---|
| 상태 | ✅ Done |
| 의존성 | S01 (OCR 결과 확보) |

---

## TAG 식별 규칙 (통화 확인)

박순근 팀장님: "V나 P나 T나 F나 이렇게 시작하는 거는 약어인 거예요"

| 패턴 | 분류 | 예시 |
|------|------|------|
| `^[A-Z]+\d+` | **TAG** | V01, PT07, TT01, FT01, B01, PI02 |
| `^[A-Z]+-[A-Z]+` | **TAG (복합)** | GSO-V02, GSC-V03, CV-V02 |
| `^\d+$` | **치수 (무시)** | 2170, 1450, 850 |
| `^\d+\.\d+` | **치수 (무시)** | 12.5, 25.4 |
| `^ORI$` | **TAG (예외)** | ORI (오리피스) |
| `^Ø\d+` | **치수 (무시)** | Ø50, Ø100 |

---

## 엑셀 교차검증

OCR에서 추출된 TAG 후보를 실제 엑셀과 대조:

1. **VALVE LIST** — TAG 컬럼에 V01~V15, B01~B03 등
2. **SENSOR LIST** — Instrument Code에 PT01~PT07, TT01, FT01, PI02 등
3. **ERP BOM** — Y열(비고)에 V01, V03/V05 등

```python
# 교차검증 로직 (의사코드)
ocr_tags = extract_tags(ocr_results)  # 알파벳 시작 패턴
excel_tags = load_all_tags(valve_list, sensor_list)
erp_tags = load_erp_tags(erp_bom_y_column)

matched = ocr_tags & excel_tags  # 교집합
missed = excel_tags - ocr_tags   # OCR이 놓친 것
extra = ocr_tags - excel_tags    # OCR이 잘못 잡은 것
```

---

## 완료 조건

- [ ] TAG 필터링 규칙 구현 (정규식)
- [ ] Part List 3개 시트에서 GT TAG 목록 추출
- [ ] OCR 결과와 교차 대조 → Recall/Precision 계산
- [ ] False Positive 분석 (치수가 TAG로 잘못 분류된 케이스)
