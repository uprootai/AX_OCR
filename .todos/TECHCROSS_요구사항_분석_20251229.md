# TECHCROSS BWMS P&ID 요구사항 심층 분석

> **작성일**: 2025-12-29
> **프로젝트**: TECHCROSS 선박평형수처리장치(BWMS) P&ID 도면 자동 검토 시스템
> **담당**: TECHCROSS 기본설계팀
> **상태**: 분석 완료, 개발 착수 대기

---

## 1. TECHCROSS 핵심 요구사항 (1-1 ~ 1-4)

### 1-1: 체크리스트 자동 검토 (60개 항목)

**목적**: P&ID 설계 규칙 60개 항목을 자동으로 검증

**검증 규칙 예시**:
| 규칙 ID | 검증 내용 | 필요 데이터 | 난이도 |
|---------|----------|-------------|--------|
| BWMS-001 | G-2 Sampling Port는 상류(upstream)에 위치 | 라인 흐름 방향 | ⭐⭐⭐⭐ |
| BWMS-004 | FMU가 ECU 후단에 위치 | 심볼 연결 순서 | ⭐⭐⭐ |
| BWMS-005 | GDS가 ECU/HGU 상부에 위치 | 심볼 좌표 비교 | ⭐⭐⭐ |
| BWMS-002 | TSU-APU 거리 ≤ 5m | 스케일 정보 필요 | ⭐⭐⭐⭐⭐ |
| BWMS-003 | ANU Injection Port ≤ 10m | 스케일 정보 필요 | ⭐⭐⭐⭐⭐ |
| BWMS-007 | Mixing Pump = Ballast Pump × 4.3% | OCR 수치 파싱 | ⭐⭐⭐⭐ |

**현재 구현 상태**:
- Design Checker: 17개 일반 규칙만 존재
- BWMS 전용 규칙: 없음
- 거리 계산: 스케일 추출 로직 없음

**구현 방안**:
1. Design Checker에 BWMS 규칙 프레임워크 추가
2. 위치 관계 분석 로직 (upstream/downstream)
3. 스케일 기반 거리 계산 (P&ID NOTE 영역에서 추출)

---

### 1-2: Valve Signal List 자동 생성

**목적**: "SIGNAL FOR BWMS" 라벨이 붙은 밸브 목록 자동 추출

**처리 파이프라인**:
```
P&ID 이미지
    │
    ├─── Line Detector (detect_regions=true) ──▶ 점선 영역 검출
    │
    ├─── PaddleOCR ──▶ "SIGNAL", "FOR BWMS" 텍스트 검출
    │
    └─── 매칭 로직 ──▶ 영역 내 밸브 ID 추출 (BWV2, BAV34 등)
                          │
                          ▼
                 Valve Signal List Excel
                 ┌────────────────────────────────┐
                 │ Valve ID | Type | Category     │
                 │ BWV2     | Ball | Required     │
                 │ BAV34    | Gate | Alarm By-pass│
                 └────────────────────────────────┘
```

**2025-12-29 테스트 결과** (page_7.png):
- Line Detector: 점선 영역 101개 검출 ✅
- PaddleOCR: "SIGNAL FOR BWMS" 22개 텍스트 검출 ✅
- 매칭 결과: 10개 SIGNAL 영역 + 텍스트 매칭 성공 ✅

**현재 Gap**:
- 영역 내 밸브 ID 추출 로직 필요
- PID Analyzer API 확장: `/api/v1/valve-signal/detect`

**구현 난이도**: ⭐⭐⭐ (중간) - 기존 기능 조합으로 구현 가능

---

### 1-3: Equipment List 자동 생성

**목적**: TECHCROSS 공급 장비 (★ 또는 * 표시) 자동 추출

**BWMS 장비 패턴 (14종)**:
```
ECS 시스템:
- ECU (Electrolyzer Cell Unit) - 전해조 유닛
- FMU (Flow Meter Unit) - 유량계
- ANU (Active Neutralization Unit) - 자동 중화 장치
- TSU (TRO Sensor Unit) - TRO 센서
- APU (Air Pump Unit) - 공기 펌프
- GDS (Gas Detection Sensor) - 가스 감지 센서
- EWU (EM Washing Unit) - 전극 세척 유닛
- CPC (Control PC) - 제어 PC
- PCU (Pump Control Unit) - 펌프 제어 유닛
- TRO (Total Residual Oxidant) - 잔류산화물

HYCHLOR 시스템 추가:
- HGU (Hypochlorite Generation Unit) - 차아염소산 생성
- DMU (Degas Module Unit) - 탈기 모듈
- NIU (Neutralization Injection Unit) - 중화 주입 유닛
- DTS (DPD TRO Sensor) - DPD TRO 센서
```

**2025-12-29 테스트 결과**:
- PID Analyzer `/api/v1/equipment/detect` (profile=bwms)
- page_1: 11개, page_3: 19개, page_5: 13개 장비 검출 ✅
- Excel 출력: `BWMS_Equipment_List.xlsx` 생성 완료 ✅

**현재 상태**: ✅ **이미 구현됨** - 빌더에서 바로 사용 가능

---

### 1-4: Deviation List 자동 생성

**목적**: 조선소 POR(Purchase Order Requirement) 대비 편차 항목 자동 식별

**비교 항목 예시**:
| 항목 | TECHCROSS 표준 | 조선소 POR | 편차 |
|------|----------------|------------|------|
| 해수 유속 | 3m/s | 2.5m/s | -0.5m/s |
| Mixing Pump 비율 | 4.3% | 4.0% | -0.3% |
| 필터 재질 | SUS316L | SUS304 | 재질 변경 |

**현재 상태**: ⏳ **보류**
- 블로커: POR 원본 문서 확보 필요
- 질문 14번 회신 대기 중

---

## 2. 요구사항별 구현 현황

| 요구사항 | 구현 상태 | 완성도 | 다음 단계 |
|----------|----------|--------|----------|
| **1-1 체크리스트** | ⚠️ 부분 | 20% | BWMS 규칙 9개 추가 |
| **1-2 Valve Signal List** | ✅ **완료** | 100% | UI 규칙 편집기 (선택사항) |
| **1-3 Equipment List** | ✅ **완료** | 100% | - |
| **1-4 Deviation List** | ⏳ 보류 | 0% | POR 문서 확보 |

### 2.1 Valve Signal List API 구현 완료 (2025-12-29)

**새로운 API 엔드포인트**:
- `GET /api/v1/region-rules` - 규칙 목록 조회
- `POST /api/v1/region-rules` - 규칙 생성
- `PUT /api/v1/region-rules/{id}` - 규칙 수정
- `DELETE /api/v1/region-rules/{id}` - 규칙 삭제
- `POST /api/v1/region-text/extract` - 영역 기반 텍스트 추출
- `POST /api/v1/valve-signal/extract` - 이미지에서 직접 밸브 시그널 추출
- `POST /api/v1/valve-signal/export-excel` - Excel 내보내기

**기본 제공 규칙**:
| 규칙 ID | 이름 | 용도 |
|---------|------|------|
| `valve_signal_bwms` | Valve Signal List (BWMS) | SIGNAL FOR BWMS 영역 |
| `alarm_bypass` | Alarm By-pass Valves | ALARM BY-PASS 영역 |
| `signal_region_general` | Signal Region (General) | 일반 SIGNAL 영역 |
| `required_signal` | Required Signal (BWMS) | REQUIRED 표시 영역 |

**UI 규칙 편집 지원**: YAML 기반 규칙 파일로 UI에서 쉽게 수정 가능

---

## 3. Line Detector 테스트 결과 (2025-12-29)

### 3.1 테스트 환경
- **이미지**: `/web-ui/public/samples/bwms_pid_sample.png` (page_7)
- **빌더**: http://localhost:5173/blueprintflow

### 3.2 Line Detector 파라미터
```json
{
  "detect_regions": true,
  "min_region_area": 1000,
  "classify_styles": true,
  "region_line_styles": "dashed,dash_dot",
  "visualize": true
}
```

### 3.3 결과
- **라인**: 2,370개 검출
- **점선 영역**: 101개 검출
- **스타일 분류**: solid, dashed, dotted, dash_dot
- **처리 시간**: 약 35초

### 3.4 SIGNAL FOR BWMS 영역 매칭
```
PaddleOCR 텍스트: 147개
├── SIGNAL/BWMS 관련: 22개
└── 매칭된 영역: 10개 ✅

검출된 SIGNAL 영역 예시:
[1] (873, 1173) ~ (1290, 1420) - 텍스트: SIGNAL, FOR BWMS
[2] (2387, 1463) ~ (2478, 1498) - 텍스트: SIGNAL, FOR_BWMS
[3] (2468, 1434) ~ (2791, 1593) - 텍스트: SIGNAL, FOR BWMS
```

---

## 4. 빌더에서 테스트 가능한 파이프라인

### 4.1 현재 즉시 사용 가능
```
ImageInput (BWMS P&ID 샘플)
    │
    ├──▶ YOLO (model_type=pid_class_aware) ──▶ 심볼 검출
    │
    ├──▶ Line Detector (detect_regions=true) ──▶ 라인 + 점선 영역
    │
    ├──▶ PaddleOCR ──▶ 텍스트 검출
    │
    └──▶ PID Analyzer (equipment/detect) ──▶ Equipment List ✅
```

### 4.2 추가 개발 필요
```
Line Detector regions + PaddleOCR texts
    │
    └──▶ [새 API] Valve Signal Matcher ──▶ Valve Signal List
             │
             └── 영역 내 밸브 ID 추출 로직
```

---

## 5. 개발 로드맵 (권장)

### Week 1: 1-2 Valve Signal List 완성
- [ ] PID Analyzer 확장: SIGNAL 영역 + 밸브 ID 매칭 API
- [ ] Line Detector regions + OCR 밸브 태그 조합
- [ ] Excel 출력 기능
- **예상 공수**: 3-5일

### Week 2: 1-1 체크리스트 기본 규칙
- [ ] Design Checker에 BWMS 규칙 5개 추가
  - BWMS-004: FMU-ECU 순서
  - BWMS-005: GDS 위치
  - BWMS-008: ECS 밸브 위치
  - BWMS-009: HYCHLOR 필터 위치
- [ ] 위치 관계 분석 로직 (upstream/downstream)
- **예상 공수**: 5-7일

### Week 3+: 체크리스트 UI + 리포트
- [ ] Human-in-the-Loop 체크리스트 검증 UI
- [ ] 60개 항목 표시 + 자동/수동 구분
- [ ] PDF/Excel 통합 리포트 생성
- **예상 공수**: 1-2주

---

## 6. Blueprint AI BOM 연동 전략

### 6.1 활용 가능한 기능
| Blueprint AI BOM 기능 | TECHCROSS 활용 |
|----------------------|----------------|
| Human-in-the-Loop | 체크리스트 60개 항목 검증 UI |
| VLM 분류 | P&ID 영역 분류 (Ballasting/De-Ballasting) |
| 노트 추출 | NOTE 영역에서 스케일 정보 추출 |
| 리비전 비교 | P&ID Rev.A → Rev.B 변경 사항 추적 |

### 6.2 통합 아키텍처
```
BlueprintFlow 파이프라인
    │
    ├── YOLO + Line Detector + OCR
    │       │
    │       ▼
    ├── BWMS Analyzer (신규)
    │       │
    │       ├──▶ 1-2 Valve Signal List
    │       ├──▶ 1-3 Equipment List ✅
    │       └──▶ 1-1 체크리스트 (기본 규칙)
    │
    └── Blueprint AI BOM
            │
            └──▶ Human-in-the-Loop 검증 UI
                     │
                     └──▶ 최종 리포트 (PDF/Excel)
```

---

## 7. 기술적 의존성

### 7.1 즉시 해결 가능
- 영역 내 밸브 ID 매칭: PID Analyzer API 확장
- FMU-ECU 순서 검증: PID Analyzer 연결 분석 활용
- GDS 위치 검증: 심볼 좌표 비교

### 7.2 추가 데이터 필요
- 거리 계산 (5m, 10m): 스케일 정보 필요 → NOTE 영역 OCR
- 용량 비교 (4.3%): Components List OCR 파싱
- Deviation List: POR 원본 문서 필요

### 7.3 장기 개발 필요
- BWMS 전용 YOLO 모델: 학습 데이터 200-500장 필요
- 60개 체크리스트 전체 자동화: 규칙별 개별 구현

---

## 8. 샘플 이미지 위치

```
빌더 샘플:
/web-ui/public/samples/bwms_pid_sample.png  ← 빌더에서 선택 가능

테스트 이미지:
/apply-company/techloss/test_output/
├── page_1.png
├── page_3.png (BWMS P&ID)
├── page_5.png
└── page_7.png (SIGNAL 영역 가장 많음) ← 빌더 샘플로 등록됨
```

---

## 9. 관련 문서

- [TECHCROSS 개발 로드맵](.todos/TECHCROSS_개발_로드맵.md)
- [Phase1 즉시개발](.todos/TECHCROSS_Phase1_즉시개발.md)
- [POC 개발 우선순위](apply-company/techloss/TECHCROSS_POC_개발_우선순위.md)
- [미구현 기능 평가](apply-company/techloss/TECHLOSS_미구현기능_평가.md)

---

**작성자**: Claude AI (Opus 4.5)
**최종 업데이트**: 2025-12-29
