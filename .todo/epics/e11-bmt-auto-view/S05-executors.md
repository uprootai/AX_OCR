# S05: gateway-api executor 4개 구현

> BlueprintFlow 빌더에서 BMT 템플릿을 실제 실행할 수 있도록 executor 구현

| 항목 | 값 |
|------|---|
| 상태 | ⬜ Todo |
| 의존성 | S03 (자동 크롭 로직 확정) |

---

## 필요 executor

| executor | 역할 | 입력 | 출력 |
|----------|------|------|------|
| `view_splitter_executor` | 뷰 라벨 OCR + 경계선 → 자동 크롭 | 이미지 | 크롭 이미지 배열 |
| `tag_filter_executor` | OCR 결과에서 TAG만 필터링 | OCR 텍스트 배열 | TAG 배열 |
| `excel_lookup_executor` | Part List에서 TAG→품목코드 변환 | TAG + 엑셀 | 매핑 결과 |
| `bom_check_executor` | ERP BOM에서 품목코드 존재 확인 | 매핑 + 엑셀 | 누락 리포트 |

---

## 완료 조건

- [ ] 4개 executor 구현 + 단위 테스트
- [ ] BlueprintFlow 빌더에서 BMT 템플릿 실행 가능
- [ ] 이미지 업로드 → 누락 리포트 XLSX 다운로드 데모
