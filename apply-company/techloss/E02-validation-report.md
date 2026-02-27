# E02 테크로스 P&ID 자동 설계 검증 — 검증 리포트

> **날짜**: 2026-02-27
> **샘플**: ECS P&ID (16 pages, Sheet 1=page4, Sheet 2=page5)
> **환경**: Docker Compose (21 services)

---

## 1. E2E 테스트 결과

### ECS P&ID Sheet 2 (page 5) — 주요 장비 배치도

| 파이프라인 | 결과 | 상세 |
|-----------|------|------|
| **Equipment Detection** | 6개 | ANU-5T, APU, ECU, EWU, TRO, TSU-S |
| **Valve Signal** | 2개 | Bwv3 (0.57), BWV6 (0.82) |
| **Design Check** | 96규칙 / 1위반 | BWMS-006 TSU-APU 거리 제한 |
| **Equipment Excel** | ✅ 6행 7열 | 5.9KB |
| **Valve Signal Excel** | ✅ 2행 5열 | 5.4KB |

### ECS P&ID Sheet 1 (page 4) — 시스템 개요도

| 파이프라인 | 결과 | 상세 |
|-----------|------|------|
| **Equipment Detection** | 1개 | APU |
| **Valve Signal** | 2개 | BAV1O (0.26), BAV7 (0.77) |

---

## 2. 버그 수정 사항 (S02~S03)

| # | 파일 | 버그 | 수정 |
|---|------|------|------|
| 1 | bwms_router.py | NoneType 에러 (response.json() → None) | `or {}` + 다중 키 폴백 |
| 2 | schemas.py (OCR Ensemble) | `bbox: List[int]` → PaddleOCR float 좌표 거부 | `bbox: list` |
| 3 | clients.py (OCR Ensemble) | PaddleOCR 임계값 과다 (0.3/0.6) | 0.15/0.3 |
| 4 | extractor.py | 가상 영역 폴백: `len(regions)==0` 조건만 | criteria 통과 0개도 발동 |
| 5 | extractor.py | `unknown` line_style 거부 | 허용으로 변경 |
| 6 | extractor.py | exclude_texts에 밸브 태그 오포함 | 밸브 패턴 safe_excludes |
| 7 | region_router.py | PaddleOCR만 호출 (23개 텍스트) | OCR Ensemble 전환 (157개) |
| 8 | equipment_router.py | PaddleOCR만 호출 | OCR Ensemble 전환 |
| 9 | region_rules.yaml | `^[A-Z]{2,4}-?\d{1,4}[A-Z]?$` 너무 넓음 | 밸브 접미 V 필수 |

---

## 3. 체크리스트 자동화 커버리지

### Design Checker 규칙 96개 분류

| 카테고리 | 등록 | auto=True | auto=False | 커버리지 |
|----------|------|-----------|------------|----------|
| Builtin (BWMS-xxx) | 7 | 7 | 0 | 100% |
| Common (COM-xxx) | 19 | 4 | 15 | 21% |
| ECS (ECS-xxx) | 35 | 22 | 13 | 63% |
| HYCHLOR (HYC-xxx) | 24 | 8 | 16 | 33% |
| Class-specific | 11 | 3 | 8 | 27% |
| **총계** | **96** | **44** | **52** | **46%** |

### 자동화 가능 항목 (auto_checkable=True): 44/96 = **46%**

> 목표 30% 대비 **+16%p** 초과 달성

### 자동화 불가 사유 (52개)

| 사유 | 개수 | 예시 |
|------|------|------|
| 수동 확인 필요 (사양/메이커/CLASS) | 28 | COM-BP-001 Ballast Pump 용량 |
| 외부 문서 참조 필요 | 12 | COM-SAMP-001 최신 도면 확인 |
| OCR 정밀도 부족 | 8 | ECS-PRU-002 냉각수 유량 표기 |
| 거리 측정 필요 (스케일 미입력) | 4 | BWMS-006 TSU-APU 5m |

---

## 4. 남은 한계 + Phase 2 백로그

| 항목 | 현재 | Phase 2 목표 |
|------|------|-------------|
| 밸브 OCR 인식률 | ~20% (2/~10개) | ESRGAN 전처리 + ROI 크롭 → 60%+ |
| "BWMS" 텍스트 인식 | 0% | 전용 OCR 모델 또는 VLM 보조 |
| YOLO P&ID 심볼 | 서비스 다운 | GPU 할당 + 모델 경량화 |
| 거리 측정 규칙 | 미구현 (스케일 필요) | P&ID 스케일 자동 감지 |
| HYCHLOR 테스트 | 미실시 (샘플 없음) | HYCHLOR P&ID 샘플 확보 |

---

## 5. 변경 파일 전체 목록

| 파일 | Story |
|------|-------|
| `models/pid-analyzer-api/routers/bwms_router.py` | S02 |
| `models/ocr-ensemble-api/schemas.py` | S02 |
| `models/ocr-ensemble-api/services/clients.py` | S02 |
| `models/pid-analyzer-api/region/extractor.py` | S03 |
| `models/pid-analyzer-api/routers/region_router.py` | S03 |
| `models/pid-analyzer-api/routers/equipment_router.py` | S03 |
| `models/pid-analyzer-api/region_rules.yaml` | S03 |
| `web-ui/src/pages/blueprintflow/templates/templateDefinitions.ts` | S05 |
