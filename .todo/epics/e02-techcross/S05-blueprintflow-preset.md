# S05: BlueprintFlow 테크로스 프리셋 템플릿

> **Epic**: E02 — 테크로스 P&ID 자동 설계 검증
> **상태**: ⬜ Todo
> **예상**: 1h
> **의존**: S03, S04 (Excel 출력 + BWMS 규칙)

---

## 설명

BlueprintFlow에 테크로스 P&ID 분석 전용 프리셋 템플릿을 등록한다.
ImageInput → YOLO → Line Detector → OCR Ensemble → PID Analyzer → Design Checker 파이프라인.

## 완료 조건

- [ ] 테크로스 프리셋 템플릿 JSON 작성
- [ ] `nodeDefinitions.ts` 템플릿 목록에 등록
- [ ] BlueprintFlow Builder에서 프리셋 로드 확인
- [ ] 파이프라인 실행 가능 확인

## 변경 범위

| 파일 | 작업 |
|------|------|
| `web-ui/src/config/nodeDefinitions.ts` | 템플릿 추가 |
| `gateway-api/blueprintflow/templates/` | 백엔드 템플릿 추가 (필요 시) |

## 에이전트 지시

```
이 Story를 구현하세요.
- 기존 프리셋 템플릿 패턴 확인 (nodeDefinitions.ts의 templates 배열)
- 테크로스 P&ID 분석 워크플로: ImageInput → YOLO(pid_class_aware) → LineDetector → OCR Ensemble → PID Analyzer → Design Checker
- 각 노드 파라미터는 api_specs/*.yaml 기준으로만 설정
- YOLO: model_type=pid_class_aware, confidence=0.4
- Design Checker: bwms_rules=enabled
- 완료 시: 이 파일의 상태를 ✅ Done으로 변경
```
