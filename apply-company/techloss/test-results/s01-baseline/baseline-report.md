# E02-S01: 베이스라인 테스트 결과

> **날짜**: 2026-02-27
> **테스트 이미지**: ECS P&ID (ecs_pnid_page_4.png = Sheet 1, ecs_pnid_page_5.png = Sheet 2)
> **API 상태**: 5/5 정상 (YOLO, OCR Ensemble, Line Detector, PID Analyzer, Design Checker)

---

## 1. YOLO 객체 검출

### Sheet 1 (page 4) — Ballast Pump 영역
- **총 검출**: 102개
- **주요 클래스**: ESDV Valve Ball(18), DB&BBV(14), Control Valve(13), Sensor(9)

### Sheet 2 (page 5) — ECU/TSU/ANU 영역
- **총 검출**: 155개
- **주요 클래스**: Control Valve(33), Line Blindspacer(13), Arrowhead+Triangle(11), Sensor(9)

### Gap
- **BWMS 전용 장비 클래스 없음** — ECU, ANU, TSU, GDS 등은 YOLO 클래스에 미포함
- 일반 심볼(밸브, 센서, 플랜지) 검출은 양호
- BWMS 장비는 OCR 태그 기반 인식으로 우회 가능 (PID Analyzer 이미 지원)

---

## 2. OCR Ensemble

### Sheet 2 (page 5)
- **총 텍스트 블록**: 141개
- **엔진 상태**: tesseract 238개 → ensemble 141개 (edocr2/paddleocr 0개 — P&ID 특화 아님)
- **BWMS 태그 인식**: 6/10 (60%)

| 태그 | 인식 | 신뢰도 |
|------|:----:|--------|
| ECU | ✅ | 1.00 |
| TSU-S | ✅ | 0.84 |
| EWU | ✅ | 1.00 |
| APU | ✅ | 1.00 |
| BWV (밸브) | ✅ | 0.57~0.82 |
| SIGNAL | ✅ | 1.00 |
| ANU-5T | ❌ | — |
| GDS | ❌ | — |
| FMU | ❌ | — |
| CPC | ❌ | — |
| PDE-12A | ❌ | — |
| PCU | ❌ | — |

### 분석
- edocr2(가중치 0.4)와 paddleocr(0.35)가 0개 결과 → **P&ID 도면에 맞는 전처리 필요**
- tesseract만 동작하여 작은 태그(GDS, FMU, CPC 등) 누락
- ANU-5T 미인식은 글자 크기/해상도 문제 추정

---

## 3. Line Detector

### Sheet 2 (page 5)
- **라인**: 1,011개 (pipe 81, signal 930)
- **교차점**: 156개
- **영역(점선 박스)**: 28개

### 분석
- 라인 검출 양호 (1,000+ 라인)
- 점선 박스 28개 검출 — "SIGNAL FOR BWMS" 영역 포함 가능
- 영역 타입이 모두 `unknown` → 라벨링 개선 필요

---

## 4. PID Analyzer (BWMS)

### 기존 구현 현황 (예상 이상!)
- `/bwms/detect-equipment` — 엔드포인트 존재, 실행 시 NoneType 에러
- `/bwms/equipment-types` — **11종 BWMS 장비 정의 완료** ✅
- `/valve-signal/extract` — 엔드포인트 존재, 57~81개 영역 검출하나 매칭 0건
- `/valve-signal/export-excel` — Excel 출력 엔드포인트 존재

### Gap
- BWMS equipment detection: 코드 존재하나 OCR 결과 연동 에러
- Valve Signal: "SIGNAL FOR BWMS" 텍스트 매칭 규칙 미작동 (rules_matched=0)

---

## 5. Design Checker (BWMS)

### 기존 구현 현황 (예상 이상!)
- **BWMS 규칙 7개 등록 완료**: BWMS-001, 004, 005, 006, 007, 008, 009
- **동적 규칙**: COM-BASE-001~003+ (체크리스트 기반)
- `/check/bwms` — `symbols` 파라미터 필요 (YOLO 결과 JSON 전달)
- `/pipeline/validate` — 전체 파이프라인 (이미지 → 검증) 존재하나 타임아웃
- `/checklist/template`, `/checklist/upload` — 체크리스트 관리 엔드포인트 존재

### Gap
- BWMS check 실행 시 YOLO+OCR 결과를 JSON으로 전달해야 함 (통합 부족)
- Pipeline validate 타임아웃 (이미지 → YOLO → OCR → 검증 파이프라인 불안정)

---

## 6. 종합 평가

### 기존 구현 수준: 예상보다 높음 (60-70%)

| 기능 | 예상 | 실제 | 상태 |
|------|------|------|------|
| BWMS 장비 정의 | 미구현 | 11종 정의 완료 | ✅ |
| BWMS 검증 규칙 | 미구현 | 7개 규칙 등록 | ✅ |
| Valve Signal 추출 | 미구현 | 엔드포인트 존재 | 🔄 규칙 매칭 불량 |
| Equipment List | 미구현 | 엔드포인트 존재 | 🔄 OCR 연동 에러 |
| Excel 출력 | 미구현 | 엔드포인트 존재 | 🔄 미검증 |
| YOLO BWMS 클래스 | 미구현 | 미구현 | ❌ (OCR 우회 가능) |

### E02 Story 재조정 필요

기존에 "신규 구현"으로 계획된 S02~S04가 실제로는 "기존 기능 디버깅+개선"입니다:

| Story | 원래 계획 | 수정 필요 |
|-------|----------|----------|
| S02 BWMS 태그 인식 | 정규식 11종 신규 구현 | → **이미 구현됨**, OCR 정확도 개선 |
| S03 Excel 출력 | Equipment + Valve Signal 신규 | → **엔드포인트 존재**, 매칭 규칙 디버깅 |
| S04 BWMS 규칙 | Design Checker 규칙 5개 신규 | → **7개 이미 등록**, 실행 파이프라인 수정 |

---

## 7. 다음 단계 (우선순위)

1. **PID Analyzer BWMS detect-equipment 에러 수정** — NoneType 에러 디버깅
2. **Valve Signal 규칙 매칭 개선** — "SIGNAL FOR BWMS" 텍스트 + 영역 연동
3. **OCR 정확도 향상** — edocr2/paddleocr P&ID 모드 활성화 또는 전처리 추가
4. **Design Checker 파이프라인 안정화** — YOLO→OCR→Check 통합 실행
5. **Excel 출력 E2E 테스트** — Equipment + Valve Signal Excel 생성 확인
