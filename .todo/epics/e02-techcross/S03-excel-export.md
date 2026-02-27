# S03: Excel 출력 (Equipment List + Valve Signal List)

> **Epic**: E02 — 테크로스 P&ID 자동 설계 검증
> **상태**: ✅ Done
> **예상**: 3h
> **의존**: S02 ✅

---

## 설명

PID Analyzer의 기존 Valve Signal + Equipment 엔드포인트를 디버깅하여 실제 동작시킨다.
**S01 발견**: 엔드포인트(`/valve-signal/extract`, `/equipment/export-excel`)는 존재하나 매칭 0건.

## 완료 조건

- [x] Valve Signal 규칙 매칭 수정 ("SIGNAL FOR BWMS" 텍스트 + 영역 연동)
- [x] Equipment List 추출 동작 확인
- [x] 샘플 P&ID(page 4, 5)로 Excel 출력물 2종 생성 검증
- [ ] Maker Supply (★) 필터링 확인 → 현재 OCR이 ★ 기호 미인식, Phase 2로 이관

## 변경 파일 (실제)

| 파일 | 작업 |
|------|------|
| `models/pid-analyzer-api/region/extractor.py` | 가상 영역 폴백 조건 완화 + unknown 스타일 허용 + exclude 로직 개선 |
| `models/pid-analyzer-api/routers/region_router.py` | OCR Ensemble 전환 (PaddleOCR only → Ensemble + 폴백) |
| `models/pid-analyzer-api/routers/equipment_router.py` | OCR Ensemble 전환 |
| `models/pid-analyzer-api/region_rules.yaml` | 밸브 정규식 정밀화 (SUS316L 오인식 방지) |

## 구현 노트

### 발견된 버그 3개

1. **가상 영역 폴백 미작동** (`extractor.py:417`)
   - Line Detector가 57~81개 영역 반환 → `len(regions) == 0` 조건 미충족
   - criteria 통과 0개여도 폴백 미발동
   - 수정: criteria_pass_count 체크 추가

2. **OCR 텍스트 부족** (`region_router.py`, `equipment_router.py`)
   - PaddleOCR만 호출: 23개 텍스트 (SIGNAL FOR BWMS 텍스트 누락)
   - OCR Ensemble 전환: 157개 텍스트 (SIGNAL 포함)

3. **exclude_texts 과잉 필터링** (`extractor.py:235`)
   - `BWV6` 등 밸브 태그가 영역 식별 텍스트로 오분류 → exclude에서 제거됨
   - 수정: 밸브 패턴 매칭되는 짧은 텍스트는 exclude에서 제외

### 테스트 결과

| 항목 | 수정 전 | 수정 후 |
|------|---------|---------|
| OCR 텍스트 수 | 23 | 157 |
| criteria 통과 영역 | 0 | 81 |
| 규칙 매칭 영역 | 0 | 17 |
| Valve Signal 추출 | 0 | 2/page (BWV3, BWV6, BAV7, BAV10) |
| Equipment 검출 | 0 | 6 (ANU, APU, ECU, EWU, TRO, TSU) |
| Equipment Excel | ❌ | ✅ (6행, 7열) |
| Valve Signal Excel | ❌ | ✅ (2행, 5열) |

### 남은 한계 (Phase 2)

- 밸브 태그 OCR 인식률 ~20% (P&ID 텍스트 크기/겹침 문제)
- "BWMS" 텍스트 자체가 OCR 미인식 → 가상 영역 폴백으로 우회
- Maker Supply ★ 기호 인식 미구현
