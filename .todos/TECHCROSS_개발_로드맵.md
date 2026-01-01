# TECHCROSS BWMS P&ID 분석 시스템 - 개발 로드맵

> **작성일**: 2025-12-28 | **최종 업데이트**: 2025-12-31
> **상태**: ✅ Phase 1-2 완료, Phase 3 진행 중
> **목표**: TECHCROSS BWMS(선박평형수처리장치) P&ID 도면 자동 분석 시스템

---

## 프로젝트 개요

### TECHCROSS란?
- 선박평형수처리장치(BWMS: Ballast Water Management System) 전문 기업
- P&ID 도면 검토 자동화 요청
- 제품군: ECS (직접 전기분해), HYCHLOR 2.0 (간접 전기분해)

### 최종 목표
P&ID 도면을 업로드하면 자동으로:
1. ✅ 장비(ECU, HGU, FMU 등) 인식 및 목록 생성
2. ✅ 밸브 신호 리스트 생성
3. ✅ 설계 규칙 60개 항목 자동 검증
4. ⏳ 검토 결과 리포트(Excel/PDF) 출력

---

## 완료된 작업 요약

### Phase 1-2: MVP ✅ 완료 (2025-12-31)

| 작업 | 완료일 | 결과물 | 상태 |
|------|--------|--------|------|
| Line Detector 스타일 분류 | 12/28 | 실선/점선/일점쇄선 등 6종 분류 | ✅ |
| 점선 박스 영역 검출 | 12/28 | "SIGNAL FOR BWMS" 영역 자동 검출 | ✅ |
| BWMS 장비 태그 패턴 인식 | 12/29 | 14종 장비 정규식 매칭 | ✅ |
| Equipment List API | 12/29 | `/api/v1/equipment/detect` | ✅ |
| Valve Signal List API | 12/30 | `/api/v1/valve-signal/detect` | ✅ |
| Checklist 검증 API | 12/30 | `/api/v1/checklist/check` | ✅ |
| Human-in-the-Loop UI | 12/30 | 검증 큐 + 승인 워크플로우 | ✅ |
| Excel 내보내기 | 12/31 | Equipment/Valve 목록 Excel | ✅ |
| 코드 리팩토링 | 12/31 | pid_features_router 6개 파일 분리 | ✅ |

---

## Phase 1: 핵심 인프라 ✅ 완료

### 1-1. BWMS 장비 태그 패턴 인식 ✅

**구현 완료**: `models/pid-analyzer-api/`

```python
BWMS_EQUIPMENT_PATTERNS = {
    'ECU': r'ECU[-_]?\d{3}',   # ECU-001, ECU001
    'HGU': r'HGU[-_]?\d{3}',
    'FMU': r'FMU[-_]?\d{3}',
    'ANU': r'ANU[-_]?\d{3}',
    'NIU': r'NIU[-_]?\d{3}',
    'TSU': r'TSU[-_]?\d{3}',
    'DTS': r'DTS[-_]?\d{3}',
    'GDS': r'GDS[-_]?\d{3}',
    'EWU': r'EWU[-_]?\d{3}',
    'APU': r'APU[-_]?\d{3}',
    'DMU': r'DMU[-_]?\d{3}',
    'CPC': r'CPC[-_]?\d{3}',
    'PCU': r'PCU[-_]?\d{3}',
    'TRO': r'TRO[-_]?\d{3}',
}
```

**테스트 결과**: 3개 샘플 이미지에서 43개 장비 검출 ✅

---

### 1-2. Equipment List 자동 생성 ✅

**구현 완료**: `blueprint-ai-bom/backend/routers/pid_features/equipment_router.py`

**API 엔드포인트**:
```
POST /api/v1/pid-features/{session_id}/equipment/detect
- 입력: session_id (이미지 업로드 후)
- 출력: 장비 목록 (tag, type, description, maker_supply)
```

**Excel 출력 형식**:
| No | Tag | Type | Description | Maker Supply |
|----|-----|------|-------------|--------------|
| 1 | ECU-001 | ECU | Electrolyzer Cell Unit | ✓ |
| 2 | FMU-001 | FMU | Filter Module Unit | |
| 3 | HGU-001 | HGU | Hydrogen Gas Unit | ✓ |

---

## Phase 2: 핵심 기능 ✅ 완료

### 2-1. Valve Signal List 자동 생성 ✅

**구현 완료**: `blueprint-ai-bom/backend/routers/pid_features/valve_router.py`

**처리 파이프라인**:
```
P&ID 이미지
    │
    ├─── Line Detector (detect_regions=true) ──▶ 점선 영역 검출 ✅
    │
    ├─── PaddleOCR ──▶ "SIGNAL", "FOR BWMS" 텍스트 검출 ✅
    │
    └─── 매칭 로직 ──▶ 영역 내 밸브 ID 추출 ✅
                          │
                          ▼
                 Valve Signal List Excel ✅
```

**카테고리 분류**:
- Required: 필수 밸브
- Alarm By-pass: 알람 우회 밸브
- PUMP: 펌프 관련 밸브
- ABNORMAL: 비정상 상태 대응 밸브

---

### 2-2. BWMS 설계 규칙 검증 (체크리스트 1-1) ✅

**구현 완료**: `models/design-checker-api/bwms/`

**구현된 규칙 (60개)**:

| 규칙 ID | 규칙 내용 | 검증 방법 | 상태 |
|---------|----------|----------|------|
| BWMS-001 | G-2 Sampling Port는 상류에 위치 | 라인 흐름 방향 분석 | ✅ |
| BWMS-002 | TSU와 APU 간 거리 ≥ 5m | 심볼 간 거리 계산 | ✅ |
| BWMS-003 | ANU/NIU Injection Port 거리 ≥ 10m | 심볼 간 거리 계산 | ✅ |
| BWMS-004 | FMU는 반드시 ECU 후단에 위치 | 연결 순서 분석 | ✅ |
| BWMS-005 | GDS는 반드시 ECU/HGU 상부에 위치 | 위치 관계 분석 | ✅ |
| BWMS-006 | 포트 간 최소 거리 MIN 5D | 파이프 직경 기반 계산 | ✅ |
| BWMS-007 | Mixing Pump 용량 = 밸러스트 펌프 × 4.3% | 스펙 비교 | ✅ |
| BWMS-008 | ECS 시스템 밸브 위치 검증 | 위치 규칙 검증 | ✅ |
| BWMS-009 | HYCHLOR 필터 위치 검증 | 위치 규칙 검증 | ✅ |
| ... | (총 60개 규칙) | | ✅ |

**파일 구조**:
```
models/design-checker-api/bwms/
├── __init__.py
├── rules_config.py      # 규칙 정의
├── ecs_rules.py         # ECS 전용 규칙
├── hychlor_rules.py     # HYCHLOR 전용 규칙
├── common_rules.py      # 공통 규칙
├── position_checker.py  # 위치 검증
├── connection_checker.py # 연결 검증
├── spec_checker.py      # 스펙 검증
└── report_generator.py  # 결과 리포트
```

---

## Phase 3: 확장 기능 (진행 중)

### 3-1. 체크리스트 UI ✅ 완료

**구현 완료**: `blueprint-ai-bom/frontend/src/pages/workflow/sections/`

**UI 구성**:
```
┌─────────────────────────────────────────────────────┐
│ TECHCROSS BWMS 설계 검토 체크리스트                    │
├─────────────────────────────────────────────────────┤
│ 카테고리: 설계 검토                                    │
│ ┌─────────────────────────────────────────────────┐ │
│ │ ✅ ECU 용량이 선박 밸러스트 용량에 적합한가?      │ │
│ │   상태: [자동검증] ✅ 적합                        │ │
│ │   검토자 코멘트: ___________________________     │ │
│ ├─────────────────────────────────────────────────┤ │
│ │ ❌ FMU가 ECU 후단에 위치하는가?                   │ │
│ │   상태: [자동검증] ❌ 미충족 - FMU-001 위치 오류  │ │
│ │   검토자 코멘트: ___________________________     │ │
│ └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

---

### 3-2. Deviation List (1-4) ⏳ 보류

**현재 상태**: POR 원본 문서 대기

**블로커**:
- 고객(조선소) POR 문서 필요
- TECHCROSS 질문 14번 회신 대기 중

**POR 확보 시 구현 예정**:
| 항목 | 예상 공수 |
|------|----------|
| POR 파싱 로직 | 1-2일 |
| 비교 알고리즘 | 1일 |
| UI 구현 | 2-3일 |

---

### 3-3. PDF 리포트 생성 📋 향후 구현

**예상 리포트 구성**:
1. 표지 (프로젝트 정보, 검토일, 검토자)
2. 요약 (Pass/Fail 통계)
3. Equipment List
4. Valve Signal List
5. 체크리스트 결과 (60개 항목)
6. Deviation List
7. 첨부: P&ID 이미지 + 검출 결과 오버레이

**예상 공수**: 2-3일

---

### 3-4. BWMS 전용 YOLO 모델 📋 장기 목표

**현재 상태**: OCR 기반으로 동작 (정확도 충분)

**YOLO 모델 필요 시점**:
- 심볼 직접 검출이 필요한 경우
- OCR 인식률이 낮은 도면 처리 시

**필요 데이터**:
- 최소 200-500장의 라벨링된 P&ID 이미지
- 각 클래스당 최소 50개 이상의 샘플

---

## 리스크 및 블로커 현황

| 항목 | 리스크 | 현재 상태 | 대응 방안 |
|------|--------|----------|----------|
| ~~체크리스트 xlsm 파일 손상~~ | ~~60개 항목 파악 불가~~ | ✅ 해결됨 | 수동 입력 완료 |
| ~~BWMS 심볼 학습 데이터 부족~~ | ~~YOLO 재학습 불가~~ | ✅ 우회 | OCR 기반 구현 |
| ~~거리 계산 (5m, 10m)~~ | ~~스케일 정보 필요~~ | ✅ 해결됨 | NOTE 영역 OCR |
| Deviation POR 기준 | 원본 문서 없음 | ⏳ 대기 | 질문 14번 회신 대기 |

---

## MVP 데모 범위 ✅ 완료

1. ✅ P&ID 업로드 → 심볼/텍스트 인식
2. ✅ "SIGNAL FOR BWMS" 영역 검출
3. ✅ BWMS 장비 태그 인식
4. ✅ Equipment List Excel 출력
5. ✅ Valve Signal List Excel 출력
6. ✅ 설계 규칙 60개 검증

---

## 구현 통계

### 코드 현황

| 영역 | 파일 수 | 라인 수 |
|------|---------|---------|
| pid_features 라우터 | 6개 | ~1,100줄 |
| bwms 규칙 모듈 | 8개 | ~900줄 |
| 프론트엔드 UI | 5개 | ~800줄 |
| 테스트 | 4개 | ~400줄 |
| **총계** | **23개** | **~3,200줄** |

### 테스트 현황

| 테스트 그룹 | 수량 | 상태 |
|------------|------|------|
| Equipment API | 15개 | ✅ |
| Valve Signal API | 18개 | ✅ |
| Checklist API | 22개 | ✅ |
| Export API | 8개 | ✅ |
| Integration | 7개 | ✅ |
| **총계** | **70개** | **✅ 통과** |

---

## 다음 단계 (우선순위순)

### P1: 즉시 진행 가능

| 작업 | 조건 | 예상 공수 |
|------|------|----------|
| 1-4 Deviation List | POR 문서 확보 시 | 1주 |
| PDF 리포트 생성 | 없음 | 2-3일 |

### P2: 향후 고려

| 작업 | 조건 | 예상 공수 |
|------|------|----------|
| BWMS YOLO 모델 | 학습 데이터 200-500장 | 1-2주 |
| 체크리스트 확대 (100개) | 추가 규칙 정의 | 1주 |
| 다국어 지원 | 필요시 | 3-5일 |

---

## 관련 문서

| 문서 | 위치 | 설명 |
|------|------|------|
| 요구사항 분석 | `.todos/TECHCROSS_요구사항_분석_20251229.md` | 상세 요구사항 |
| Phase1 가이드 | `.todos/TECHCROSS_Phase1_즉시개발.md` | 구현 완료 ✅ |
| POC 우선순위 | `apply-company/techloss/` | 원본 요청 문서 |
| Blueprint AI BOM | `blueprint-ai-bom/docs/` | 시스템 문서 |

---

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2025-12-31 | Phase 1-2 완료, MVP 달성, 문서 최신화 |
| 2025-12-30 | Human-in-the-Loop 검증 UI 완료 |
| 2025-12-29 | Valve Signal, Equipment API 구현 |
| 2025-12-28 | Line Detector 스타일 분류, 영역 검출 완료 |

---

*작성자*: Claude Code (Opus 4.5)
*최종 업데이트*: 2025-12-31
