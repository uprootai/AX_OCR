# S05: BlueprintFlow 테크로스 프리셋 템플릿

> **Epic**: E02 — 테크로스 P&ID 자동 설계 검증
> **상태**: ✅ Done
> **예상**: 1h (실제 0.5h — 4개 템플릿 이미 존재, 파이프라인 보정)
> **의존**: S03 ✅, S04 ✅

---

## 설명

BlueprintFlow에 테크로스 P&ID 분석 전용 프리셋 템플릿을 등록한다.
**발견**: 4개 템플릿 이미 존재, S03 결과에 맞게 OCR Ensemble 노드 추가.

## 완료 조건

- [x] 테크로스 프리셋 템플릿 4개 확인 (1-1~1-4)
- [x] S03 검증 파이프라인에 맞게 OCR Ensemble 노드 추가
- [x] web-ui 빌드 성공 (tsc + build 에러 0)

## 변경 내용

| 템플릿 | 수정 |
|--------|------|
| 1-1 BWMS Checklist | OCR Ensemble 노드 추가, 규칙 96개 반영 |
| 1-2 Valve Signal | OCR Ensemble + Line Detector 영역 추출로 재구성 |
| 1-3 Equipment List | OCR Ensemble 기반으로 변경 (YOLO 의존 제거) |
| 1-4 Deviation | 변경 없음 |
