# TECHCROSS POC 개발 우선순위

> 작성일: 2025-12-26

---

## Phase 1: 핵심 인프라 (MVP)

### 1순위: P&ID 심볼/텍스트 인식 기반 구축

- YOLO (model_type=pid_class_aware) 모델에 BWMS 장비 8종 클래스 추가 (ECU, FMU, ANU, TSU, APU, GDS, EWU, CPC)
- OCR로 장비명/밸브ID 텍스트 추출
- "SIGNAL FOR BWMS" 라벨 감지
- 기존 기능 활용: YOLO (P&ID 모드), OCR Ensemble, Line Detector

### 2순위: Equipment List 자동 생성 (1-3)

- 인식된 장비 목록화
- '*' 마크(MAKER SUPPLY) 필터링
- Excel 출력
- 이유: 1-1 체크리스트보다 단순하고, 인식 결과 검증에 활용 가능

---

## Phase 2: 핵심 기능

### 3순위: Valve Signal List 자동 생성 (1-2)

- "SIGNAL FOR BWMS" 밸브 추출
- 밸브ID, 타입 매핑
- 카테고리 분류 (Required/Alarm By-pass/PUMP/ABNORMAL)
- Excel 출력

### 4순위: 체크리스트 자동 검토 (1-1)

- 설계 규칙 9개 검증 로직 구현
  - FMU → ECU 후단 위치
  - TSU-APU 거리 ≤ 5m
  - ANU Injection Port ≤ 10m
  - Mixing Pump = Ballast Pump × 4.3%
- 충족/미충족/N/A 판정
- 기존 기능 활용: Design Checker 확장

---

## Phase 3: 확장 기능

### 5순위: 체크리스트 UI

- 60개 항목 표시
- 자동 검증 결과 + 수동 검토 입력
- 승인 워크플로우

### 6순위: Deviation List (1-4)

- POR 대비 편차 항목 관리
- 구매자 결정 입력
- 이유: POR 원본 문서 확보 후 진행

### 7순위: PDF 리포트 생성

- 검토 결과 종합 리포트
- 체크리스트 + List 통합 출력

---

## 의존성 다이어그램

```
[Phase 1]
   │
   ├─ 심볼/텍스트 인식 ─┬─► Equipment List (1-3)
   │                    │
   │                    └─► Valve Signal List (1-2)
   │
[Phase 2]
   │
   ├─ 설계 규칙 검증 ────► 체크리스트 검토 (1-1)
   │
[Phase 3]
   │
   ├─ UI 개발 ──────────► 체크리스트 UI
   │
   ├─ POR 문서 확보 ────► Deviation List (1-4)
   │
   └─ 전체 통합 ────────► PDF 리포트
```

---

## 리스크 및 블로커

| 항목 | 리스크 | 대응 |
|------|--------|------|
| 체크리스트 xlsm 손상 | 60개 항목 파악 불가 | 파일 재요청 (질문 1번) |
| BWMS 심볼 학습 데이터 | YOLO 재학습 필요 | 샘플 도면으로 라벨링 |
| 거리 계산 (5m, 10m) | 스케일 정보 필요 | NOTE 영역 스케일 추출 또는 수동 입력 |
| Deviation POR 기준 | 원본 문서 없음 | 질문 14번 회신 대기 |

---

## 권장 MVP 범위

2주 내 데모 가능 범위:

1. P&ID 업로드 → 심볼/텍스트 인식
2. Equipment List 자동 생성 (Excel)
3. Valve Signal List 자동 생성 (Excel)
4. 기본 설계 규칙 3개 검증 (위치 관계)

이 범위로 먼저 진행하고, 체크리스트 파일 확보 후 1-1 기능 확장 권장.

---

## 관련 문서

- [질문 목록 (이메일용)](./TECHCROSS_질문목록_이메일용.md)
- [작업 계획서](../.todos/REMAINING_WORK_PLAN.md)
