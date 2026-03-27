# S06: BlueprintFlow 템플릿 생성

> 검증된 파이프라인을 BlueprintFlow 빌더에 "BMT TAG 추출" 템플릿으로 등록

| 항목 | 값 |
|------|---|
| 상태 | ✅ Done |
| 의존성 | S01~S04 완료 후 |

---

## 템플릿 노드 구성 (예상)

```
ImageInput → [최적 OCR 노드] → TAG Filter → Part List Lookup → BOM Check → Report Export
```

기존 "OCR Comparison" 템플릿을 참고하되, BMT 전용 후처리 노드 추가.

---

## 결과 (2026-03-25)

- `templates.bmt.ts` 생성 — "BMT GVU: GAR 배치도 TAG 추출 + BOM 누락 확인" 템플릿
- 7개 노드: ImageInput → View Splitter → PaddleOCR → TAG Filter → Excel Lookup → BOM Check → Report
- `types.ts`, `templateDefinitions.ts`, `BlueprintFlowTemplates.tsx` 수정
- i18n ko/en 추가
- TypeScript 빌드 에러 0

## 완료 조건

- [x] BlueprintFlow 빌더에서 템플릿 로드 가능 (BMT 카테고리 탭 추가)
- [ ] 이미지 업로드 → 누락 리포트 자동 생성 데모 (executor 구현 필요 — 후속 Epic)
