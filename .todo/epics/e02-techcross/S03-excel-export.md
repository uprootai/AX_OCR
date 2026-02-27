# S03: Excel 출력 (Equipment List + Valve Signal List)

> **Epic**: E02 — 테크로스 P&ID 자동 설계 검증
> **상태**: ⬜ Todo
> **예상**: 3h
> **의존**: S02 (BWMS 태그 인식 필요)

---

## 설명

PID Analyzer의 기존 Valve Signal + Equipment 엔드포인트를 디버깅하여 실제 동작시킨다.
**S01 발견**: 엔드포인트(`/valve-signal/extract`, `/equipment/export-excel`)는 존재하나 매칭 0건.

## 완료 조건

- [ ] Valve Signal 규칙 매칭 수정 ("SIGNAL FOR BWMS" 텍스트 + 영역 연동)
- [ ] Equipment List 추출 동작 확인
- [ ] 샘플 P&ID(page 4, 5)로 Excel 출력물 2종 생성 검증
- [ ] Maker Supply (★) 필터링 확인

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
