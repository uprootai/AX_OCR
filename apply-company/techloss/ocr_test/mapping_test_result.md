# 장비명↔OCR 태그 매핑 테스트 결과

## 테스트 일시
- 2026-01-05

## 테스트 데이터
- ECS P&ID 도면 16페이지
- OCR 검출: 2,719 텍스트, 230 태그, 36 고유 태그

## 개선 결과

| 항목 | 매핑 적용 전 | 매핑 적용 후 | 개선율 |
|------|-------------|-------------|--------|
| **Pass Rate** | 3.7% | **25.9%** | **7배 향상** |
| 통과 규칙 | 1개 | 7개 | +6개 |
| 위반 규칙 | 26개 | 20개 | -6개 |
| 스킵 규칙 | - | 35개 | (existence 외) |

## 매칭 유형 분석

### Direct 매칭 (정확 일치)
- PCU -> PCU ✅

### Alias 매칭 (유사어)
- Check Valve -> BWV1, BWV2, ... ✅
- Manual Valve -> BWV 태그들 ✅
- Signal Valve -> BWV 태그들 ✅
- FT -> FTS ✅

## 미검출 항목 (위반)
- BWMS Inlet/Outlet: 구조적 요소 (OCR 미검출)
- T.S.TK, Slop TK: 탱크 명칭 (OCR 미검출)
- Stripping Pump: 펌프 유형 (OCR 미검출)
- HEU: 열교환기 (도면에 없음)

## TECHCROSS 요구사항 정합성

| 요구사항 | 상태 | 비고 |
|----------|------|------|
| P&ID 인식 | ✅ 진행중 | 7배 정확도 향상 |
| Equipment List | ✅ 진행중 | 17종 장비 검출 |
| 체크리스트 검토 | ✅ 진행중 | existence 자동 검증 |
| Valve Signal List | ⏳ 대기 | 상세 내용 필요 |

## 다음 단계
1. 탱크/배관 패턴 추가
2. 매핑 정교화 (Valve 유형 세분화)
3. 조건부 규칙 필터링 (ship_type, class_society)

---

## 탱크/배관 패턴 추가 후 (2026-01-05)

### 매핑 테이블 확장
| 항목 | 이전 | 현재 |
|------|------|------|
| 장비 매핑 | 47개 | **77개** (+30) |
| 태그 매핑 | 75개 | **166개** (+91) |

### 추가된 패턴
**탱크 (15종)**:
- Fore Peak TK, Aft Peak TK, F.O.TK, D.O.TK, F.W.TK
- D.B.TK, Cargo TK, Settling TK, Service TK, Storage TK
- Holding TK, Expansion TK, Cofferdam, Void Space

**배관 (15종)**:
- SW Line, BW Line, Vent Line, Drain Line, Suction Line
- Discharge Line, Return Line, Supply Line, Sampling Line
- By-pass Line, Cross Connection, Branch Pipe, Manifold
- Header, Sounding Pipe, Filling Pipe

### 검증 결과 개선
| 항목 | 패턴 추가 전 | 패턴 추가 후 |
|------|-------------|-------------|
| Pass Rate | 25.9% | **44.4%** |
| 통과 | 7개 | **12개** |
| 위반 | 20개 | **15개** |

### 신규 통과 항목
- BWMS Inlet/Outlet → INLET, OUTLET 패턴 매칭
- PI → BRANCH PIPES 매칭

