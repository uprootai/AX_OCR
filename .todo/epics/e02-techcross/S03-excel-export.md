# S03: Excel 출력 (Equipment List + Valve Signal List)

> **Epic**: E02 — 테크로스 P&ID 자동 설계 검증
> **상태**: ⬜ Todo
> **예상**: 3h
> **의존**: S02 (BWMS 태그 인식 필요)

---

## 설명

PID Analyzer의 분석 결과를 테크로스 요구 형식의 Excel 파일로 자동 생성한다.
Equipment List(★ 표시 장비 필터링) + Valve Signal List("SIGNAL FOR BWMS" 영역 기반).

## 완료 조건

- [ ] Equipment List Excel 생성 (ID, Type, Spec, Qty 컬럼)
- [ ] Maker Supply (★) 필터링 로직 구현
- [ ] Valve Signal List Excel 생성 (Tag, Type, Position, Signal 컬럼)
- [ ] "SIGNAL FOR BWMS" 점선 박스 영역 기반 밸브 필터링
- [ ] 샘플 P&ID로 Excel 출력 검증

## 변경 범위

| 파일 | 작업 |
|------|------|
| `models/pid-analyzer-api/services/export_service.py` | Excel 출력 로직 (신규 또는 확장) |
| `models/pid-analyzer-api/routers/analysis_router.py` | Excel 다운로드 엔드포인트 추가 |
| `gateway-api/api_specs/pidanalyzer.yaml` | 엔드포인트 스펙 추가 |

## 에이전트 지시

```
이 Story를 구현하세요.
- openpyxl 사용 (이미 의존성에 포함)
- Equipment List: YOLO 검출 + OCR 태그에서 Maker Supply 장비 추출
- Valve Signal List: Line Detector 점선 박스 영역 + 밸브 태그 매칭
- 두 List 모두 /api/v1/analyze 응답에 download_url 필드 추가
- API 스펙(yaml) 업데이트 필수
- 완료 시: 이 파일의 상태를 ✅ Done으로 변경
```
