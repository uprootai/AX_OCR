# S02: BWMS 장비 인식 파이프라인 수정

> **Epic**: E02 — 테크로스 P&ID 자동 설계 검증
> **상태**: ⬜ Todo
> **예상**: 2h
> **의존**: S01 ✅

---

## 설명

PID Analyzer BWMS detect-equipment 에러 수정 + OCR 태그 인식률 개선.
**S01 발견**: 11종 장비 정의는 이미 구현됨, `/bwms/detect-equipment` 실행 시 NoneType 에러.
OCR에서 10개 중 4개(ANU, GDS, FMU, CPC) 미인식 — 전처리 또는 엔진 조합 개선 필요.

## 완료 조건

- [ ] `/bwms/detect-equipment` NoneType 에러 원인 파악 + 수정
- [ ] OCR 누락 태그(ANU-5T, GDS, FMU, CPC, PDE) 인식 개선
- [ ] 샘플 P&ID(page 5)로 BWMS 장비 검출 8/10 이상

## 변경 범위

| 파일 | 작업 |
|------|------|
| `models/pid-analyzer-api/services/analysis_service.py` | BWMS 태그 패턴 추가 |
| `models/pid-analyzer-api/tests/test_bwms_tags.py` | 단위 테스트 추가 |

## 에이전트 지시

```
이 Story를 구현하세요.
- S01 테스트 결과의 OCR 출력을 참고하여 실제 태그 형식 파악
- 정규식 패턴: ECU-\d{3}, HGU-\d{3}, ANU-\d{3} 등
- 기존 analysis_service.py의 태그 파싱 로직에 BWMS 패턴 통합
- 단위 테스트 작성 + pytest 통과 확인
- 완료 시: 이 파일의 상태를 ✅ Done으로 변경
```

## 구현 노트

BWMS 장비 11종 (ECS + HYCHLOR 통합):
```
ECU (전해조), PRU (정류기), ANU (중화장치), TSU-S (TRO 센서),
APU (공기펌프), FMU (유량계), CSU (전도도 센서), GDS (가스감지),
HGU (차아염소산염), DMU (탈기모듈), NIU (중화주입)
```
