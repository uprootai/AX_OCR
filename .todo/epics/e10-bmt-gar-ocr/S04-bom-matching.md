# S04: Part List / ERP BOM 자동 매칭

> 추출된 TAG → Part List 품목코드 → ERP BOM 존재 확인 자동화

| 항목 | 값 |
|------|---|
| 상태 | ✅ Done |
| 의존성 | S01 + S03 |

---

## 파이프라인

```
OCR TAG (V01, PT01...)
  → Part List 조회 (VALVE LIST / SENSOR LIST)
    → BMT 품목코드 (노란색 셀, FB2F29-R64A...)
      → ERP BOM 검색 (C열 자품목)
        → 있으면 ✅ / 없으면 ❌ 누락
```

## 이미 확인된 GT 결과 (실데이터 대조)

| 결과 | 건수 | 항목 |
|------|------|------|
| ✅ exact match | 17건 | V01, V02, V03/V05, V04/V15, V07/V14, V08, V09, V11-1, V11-2, B01, B03, FT01, PT01, PT03/04, PT05, PT06, TT01 |
| ⚠️ 불일치 | 2건 | V06 (`-DNV` 누락), PI02 (331↔311) |
| ❓ 미확인 | 2건 | ORI, B02 (Structure에 포함?) |

## 재활용 가능한 기존 코드

- `bmt_excel_utils.py` — Part List 파서 (SimpleXlsxReader)
- `bmt_pipeline.py` — ERP BOM 파서 + 매칭 로직
- `bmt_report.py` — Excel 리포트 생성

---

## 완료 조건

- [ ] TAG → Part List → ERP BOM 자동 매칭 스크립트
- [ ] 누락 리포트 자동 생성 (Excel)
- [ ] 불일치 2건 (V06, PI02) 자동 검출 확인
