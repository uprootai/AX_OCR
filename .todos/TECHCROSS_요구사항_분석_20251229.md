# TECHCROSS BWMS P&ID 요구사항 분석

> **작성일**: 2025-12-29 | **최종 업데이트**: 2025-12-31
> **프로젝트**: TECHCROSS 선박평형수처리장치(BWMS) P&ID 도면 자동 검토 시스템
> **담당**: TECHCROSS 기본설계팀
> **상태**: ✅ MVP 완료 (1-1, 1-2, 1-3) | ⏳ 1-4 POR 대기

---

## 1. 요구사항 현황 요약

```
┌─────────────────────────────────────────────────────────────────┐
│  TECHCROSS POC 구현 현황 (2025-12-31)                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1-1 체크리스트 (60개)     ████████████████████ 100% ✅         │
│  1-2 Valve Signal List    ████████████████████ 100% ✅         │
│  1-3 Equipment List       ████████████████████ 100% ✅         │
│  1-4 Deviation List       ░░░░░░░░░░░░░░░░░░░░   0% ⏳         │
│                                                                 │
│  MVP 완성도: 75% (3/4 요구사항 완료)                             │
│  블로커: POR 원본 문서 회신 대기                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 요구사항별 상세 현황

### 2.1 1-1: 체크리스트 자동 검토 ✅ 완료

**목적**: P&ID 설계 규칙 60개 항목을 자동으로 검증

**구현 완료 내역**:
| 항목 | 상태 | 구현 위치 |
|------|------|----------|
| BWMS 규칙 60개 정의 | ✅ | `design-checker-api/bwms/` |
| 체크리스트 검증 API | ✅ | `POST /{session_id}/checklist/check` |
| Human-in-the-Loop 검증 UI | ✅ | `ChecklistSection.tsx` |
| 제품 필터 (ECS/HYCHLOR) | ✅ | `product_type` 파라미터 |

**검증 규칙 예시**:
| 규칙 ID | 검증 내용 | 구현 상태 |
|---------|----------|----------|
| BWMS-001 | G-2 Sampling Port는 상류에 위치 | ✅ 구현됨 |
| BWMS-004 | FMU가 ECU 후단에 위치 | ✅ 구현됨 |
| BWMS-005 | GDS가 ECU/HGU 상부에 위치 | ✅ 구현됨 |
| BWMS-007 | Mixing Pump = Ballast Pump × 4.3% | ✅ 구현됨 |

**API 엔드포인트**:
```
POST /api/v1/pid-features/{session_id}/checklist/check
- 입력: session_id, product_type (ECS/HYCHLOR/ALL)
- 출력: 60개 항목별 pass/fail/warning 결과
- Design Checker API 연동
```

---

### 2.2 1-2: Valve Signal List ✅ 완료

**목적**: "SIGNAL FOR BWMS" 라벨이 붙은 밸브 목록 자동 추출

**구현 완료 내역**:
| 항목 | 상태 | 구현 위치 |
|------|------|----------|
| 밸브 신호 검출 API | ✅ | `POST /{session_id}/valve-signal/detect` |
| 점선 영역 검출 | ✅ | Line Detector 연동 |
| OCR 텍스트 매칭 | ✅ | PaddleOCR 연동 |
| Human-in-the-Loop 검증 | ✅ | 검증 큐 UI |
| Excel 내보내기 | ✅ | `POST /{session_id}/export` |

**처리 파이프라인** (구현됨):
```
P&ID 이미지
    │
    ├─── Line Detector (detect_regions=true) ──▶ 점선 영역 검출 ✅
    │
    ├─── PaddleOCR ──▶ "SIGNAL", "FOR BWMS" 텍스트 검출 ✅
    │
    └─── PID Analyzer ──▶ 영역 내 밸브 ID 추출 ✅
                          │
                          ▼
                 Valve Signal List Excel ✅
```

**테스트 결과 (page_7.png)**:
- Line Detector: 점선 영역 101개 검출 ✅
- PaddleOCR: "SIGNAL FOR BWMS" 22개 텍스트 검출 ✅
- 매칭 결과: 10개 SIGNAL 영역 + 텍스트 매칭 성공 ✅

---

### 2.3 1-3: Equipment List ✅ 완료

**목적**: TECHCROSS 공급 장비 (★ 또는 * 표시) 자동 추출

**구현 완료 내역**:
| 항목 | 상태 | 구현 위치 |
|------|------|----------|
| 장비 검출 API | ✅ | `POST /{session_id}/equipment/detect` |
| BWMS 장비 패턴 14종 | ✅ | 정규식 기반 |
| Human-in-the-Loop 검증 | ✅ | 검증 큐 UI |
| Excel 내보내기 | ✅ | `POST /{session_id}/export` |

**BWMS 장비 패턴 (14종)** - 모두 구현됨:
```
ECS 시스템:
✅ ECU (Electrolyzer Cell Unit)
✅ FMU (Flow Meter Unit)
✅ ANU (Active Neutralization Unit)
✅ TSU (TRO Sensor Unit)
✅ APU (Air Pump Unit)
✅ GDS (Gas Detection Sensor)
✅ EWU (EM Washing Unit)
✅ CPC (Control PC)
✅ PCU (Pump Control Unit)
✅ TRO (Total Residual Oxidant)

HYCHLOR 시스템 추가:
✅ HGU (Hypochlorite Generation Unit)
✅ DMU (Degas Module Unit)
✅ NIU (Neutralization Injection Unit)
✅ DTS (DPD TRO Sensor)
```

**테스트 결과**:
- page_1: 11개 장비 검출 ✅
- page_3: 19개 장비 검출 ✅
- page_5: 13개 장비 검출 ✅
- Excel 출력: `BWMS_Equipment_List.xlsx` 생성 완료 ✅

---

### 2.4 1-4: Deviation List ⏳ 보류

**목적**: 조선소 POR(Purchase Order Requirement) 대비 편차 항목 자동 식별

**현재 상태**: ⏳ **블로킹됨**

**블로커**:
```
┌─────────────────────────────────────────────────────────────────┐
│  ⚠️ POR 원본 문서 필요                                           │
│                                                                 │
│  - TECHCROSS 질문 14번 회신 대기 중                              │
│  - POR 문서 없이는 비교 기준 없음                                 │
│  - 예상 형식: Excel 또는 PDF (스펙 비교 표)                       │
│                                                                 │
│  필요 조치: TECHCROSS 담당자에게 POR 샘플 문서 요청               │
└─────────────────────────────────────────────────────────────────┘
```

**구현 예정 사항** (POR 확보 후):
| 항목 | 설명 |
|------|------|
| POR 파싱 | Excel/PDF에서 요구사항 추출 |
| 자동 비교 | 도면 데이터 vs POR 스펙 비교 |
| 편차 목록 | 항목별 차이점 표시 |
| 승인 워크플로우 | Buyer Decision 기록 |

---

## 3. 구현된 API 엔드포인트 (10개)

### Blueprint AI BOM - PID Features Router

| 그룹 | 엔드포인트 | 설명 | 상태 |
|------|------------|------|------|
| Valve Signal | `POST /{session_id}/valve-signal/detect` | 밸브 신호 검출 | ✅ |
| Equipment | `POST /{session_id}/equipment/detect` | 장비 검출 | ✅ |
| Checklist | `POST /{session_id}/checklist/check` | 체크리스트 검증 | ✅ |
| Verification | `GET /{session_id}/verify/queue` | 검증 큐 조회 | ✅ |
| Verification | `POST /{session_id}/verify` | 단일 항목 검증 | ✅ |
| Verification | `POST /{session_id}/verify/bulk` | 대량 검증 | ✅ |
| Export | `POST /{session_id}/export` | Excel 내보내기 | ✅ |
| Summary | `GET /{session_id}/summary` | 워크플로우 요약 | ✅ |

### 파일 구조 (리팩토링 완료)

```
blueprint-ai-bom/backend/routers/pid_features/
├── __init__.py              # 라우터 통합
├── valve_router.py          # 1-2 Valve Signal
├── equipment_router.py      # 1-3 Equipment
├── checklist_router.py      # 1-1 Checklist
├── verification_router.py   # Human-in-the-Loop
├── export_router.py         # Excel 내보내기
└── summary_router.py        # 요약

총 라인 수: 1,101줄 → 6개 파일로 분리 (평균 ~180줄)
```

---

## 4. 테스트 현황

| 테스트 그룹 | 수량 | 상태 |
|------------|------|------|
| pid_features_api 단위 테스트 | 30개 | ✅ 통과 |
| 검증 큐 테스트 | 12개 | ✅ 통과 |
| Excel 내보내기 테스트 | 8개 | ✅ 통과 |
| Design Checker 연동 테스트 | 20개 | ✅ 통과 |
| **총계** | **70개** | **✅ 통과** |

---

## 5. 향후 작업

### 5.1 즉시 가능 (POR 확보 시)

| 작업 | 예상 공수 | 우선순위 |
|------|----------|----------|
| 1-4 Deviation List API 구현 | 2-3일 | P1 |
| POR 파싱 로직 | 1-2일 | P1 |
| 편차 비교 UI | 2-3일 | P1 |

### 5.2 확장 기능 (선택적)

| 작업 | 예상 공수 | 우선순위 |
|------|----------|----------|
| PDF 리포트 생성 | 2-3일 | P2 |
| BWMS 전용 YOLO 모델 | 1-2주 | P3 |
| 체크리스트 자동화 확대 (60개 → 100개) | 1주 | P3 |

### 5.3 학습 데이터 필요 항목

| 기능 | 필요 데이터 | 비고 |
|------|------------|------|
| BWMS YOLO 모델 | 200-500장 라벨링 이미지 | 현재 OCR 기반으로 동작 |
| 거리 계산 (5m, 10m) | 스케일 정보 | NOTE 영역 OCR로 추출 가능 |

---

## 6. 관련 문서

| 문서 | 위치 | 설명 |
|------|------|------|
| 개발 로드맵 | `.todos/TECHCROSS_개발_로드맵.md` | 전체 개발 계획 |
| Phase1 가이드 | `.todos/TECHCROSS_Phase1_즉시개발.md` | 구현 완료 ✅ |
| POC 우선순위 | `apply-company/techloss/` | 원본 요청 문서 |

---

## 7. 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2025-12-31 | MVP 완료 (1-1, 1-2, 1-3), 문서 최신화 |
| 2025-12-30 | Human-in-the-Loop 검증 UI 완료 |
| 2025-12-29 | Line Detector + OCR 연동 테스트 완료 |
| 2025-12-28 | Line Detector 스타일 분류 완료 |

---

*작성자*: Claude Code (Opus 4.5)
*최종 업데이트*: 2025-12-31
