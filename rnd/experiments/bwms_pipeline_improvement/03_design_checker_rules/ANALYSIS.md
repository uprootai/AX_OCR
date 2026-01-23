# Design Checker BWMS 규칙 최적화 분석

> **작성일**: 2026-01-20
> **상태**: 🔴 분석 중
> **우선순위**: P1 (High)

---

## 1. 문제 정의

BWMS Checklist 검증 시 **범용 규칙이 적용**되어 ECS/HYCHLOR 제품별 특화 검증이 누락됨.

### 현재 설정
```yaml
rule_profile: bwms
product_type: ALL     # ← 문제: 제품별 규칙 미적용
severity_threshold: warning
```

### 목표
- 60개 BWMS 체크리스트 항목 전체 커버
- ECS / HYCHLOR 제품별 규칙 분리
- 자동화 가능 항목 vs Manual 검토 항목 구분

---

## 2. BWMS 체크리스트 구조

### 2.1 체크리스트 카테고리 (60개 항목)

| 카테고리 | 항목 수 | 자동화 가능 | Manual |
|----------|---------|-------------|--------|
| **General** | 8 | 5 | 3 |
| **Ballast Pump** | 6 | 4 | 2 |
| **Filter** | 7 | 5 | 2 |
| **UV/EC Unit** | 10 | 6 | 4 |
| **Valve & Pipe** | 12 | 9 | 3 |
| **Instrument** | 8 | 6 | 2 |
| **Electrical** | 5 | 2 | 3 |
| **Safety** | 4 | 3 | 1 |
| **Total** | **60** | **40 (67%)** | **20 (33%)** |

### 2.2 자동화 가능 항목 예시

```yaml
# 심볼 존재 확인 (YOLO로 검출 가능)
- id: BWMS-001
  description: "밸러스트 펌프 심볼 존재 확인"
  rule_type: symbol_exists
  target_class: ["Pump", "Ballast Pump"]
  min_count: 1

# 연결성 확인 (Line Detector + PID Analyzer)
- id: BWMS-015
  description: "필터 입출구 배관 연결 확인"
  rule_type: connectivity
  source_class: "Filter"
  target_class: "Pipe"
  connection_points: ["inlet", "outlet"]

# 센서 존재 확인
- id: BWMS-032
  description: "유량계 설치 확인"
  rule_type: symbol_exists
  target_class: ["Flow Meter", "FIT", "FE"]
  min_count: 1
```

### 2.3 Manual 검토 필요 항목 예시

```yaml
# 텍스트/사양 확인 필요
- id: BWMS-007
  description: "펌프 용량이 설계 요구사항 충족"
  rule_type: manual
  requires: ["Pump capacity spec", "Design calculation"]

# 외부 문서 참조 필요
- id: BWMS-055
  description: "전기 설비 인증서 확인"
  rule_type: manual
  requires: ["Certificate document"]
```

---

## 3. 제품별 규칙 차이

### 3.1 ECS (Electro-Chlorination System)

```yaml
product_id: ECS
description: "전기분해 살균 방식"
specific_rules:
  - 전해조(Electrolyzer) 심볼 필수
  - 염소 농도 센서(TRC) 필수
  - 중화 탱크 또는 탈기 장치 필수
  - 수소 배출 라인 확인

required_symbols:
  - Electrolyzer
  - TRC (Total Residual Chlorine)
  - Neutralizing Tank (optional)
  - Hydrogen Vent
```

### 3.2 HYCHLOR (Sodium Hypochlorite)

```yaml
product_id: HYCHLOR
description: "차아염소산나트륨 주입 방식"
specific_rules:
  - 약품 탱크(Chemical Tank) 심볼 필수
  - 주입 펌프(Dosing Pump) 필수
  - 농도 조절 밸브 확인
  - 안전 샤워/아이워시 근접 배치

required_symbols:
  - Chemical Storage Tank
  - Dosing Pump
  - Control Valve (for concentration)
  - Safety Shower (near tank)
```

### 3.3 공통 규칙

```yaml
common_rules:
  - 밸러스트 펌프 존재
  - 필터 시스템 존재
  - 바이패스 라인 존재
  - 샘플링 포인트 존재
  - 유량계/압력계 존재
  - ESDV (긴급차단밸브) 존재
```

---

## 4. 현재 Design Checker 구현 상태

### 4.1 구현된 규칙

```python
# design-checker-api/config/rules/bwms.yaml
rules:
  - id: symbol_count
    description: "심볼 수량 검증"
    implemented: true

  - id: connectivity
    description: "연결성 검증"
    implemented: partial  # 기본 연결만

  - id: tag_naming
    description: "태그 명명 규칙"
    implemented: false
```

### 4.2 미구현 규칙

| 규칙 | 우선순위 | 구현 난이도 |
|------|----------|-------------|
| 제품별 필수 심볼 | P0 | 낮음 |
| 라인 타입별 연결 검증 | P1 | 중간 |
| 태그 패턴 매칭 | P1 | 중간 |
| 안전 장비 근접성 | P2 | 높음 |
| 전기 설비 영역 구분 | P2 | 높음 |

---

## 5. 실험 계획

### 실험 1: 제품 타입별 규칙 분리

```yaml
# 현재
product_type: ALL

# 테스트 A - ECS
product_type: ECS
expected: ECS 전용 10개 규칙 추가 적용

# 테스트 B - HYCHLOR
product_type: HYCHLOR
expected: HYCHLOR 전용 8개 규칙 추가 적용
```

---

### 실험 2: 자동화 가능 규칙 구현

**Phase 1: 심볼 존재 확인 (20개 규칙)**
```python
def check_symbol_exists(detections, target_classes, min_count):
    count = sum(1 for d in detections if d['class'] in target_classes)
    return count >= min_count
```

**Phase 2: 연결성 확인 (15개 규칙)**
```python
def check_connectivity(symbol_id, connections, required_types):
    connected_types = [c['type'] for c in connections.get(symbol_id, [])]
    return all(rt in connected_types for rt in required_types)
```

---

### 실험 3: 체크리스트 결과 포맷

```yaml
# 현재 출력
{
  "violations": [...],
  "warnings": [...]
}

# 목표 출력
{
  "checklist_results": [
    {
      "id": "BWMS-001",
      "description": "밸러스트 펌프 존재 확인",
      "status": "PASS",
      "evidence": "Pump detected at (x, y) with 95% confidence"
    },
    {
      "id": "BWMS-015",
      "description": "필터 연결 확인",
      "status": "FAIL",
      "reason": "Filter outlet not connected to pipe"
    },
    {
      "id": "BWMS-055",
      "description": "전기 인증서 확인",
      "status": "MANUAL",
      "action_required": "Review certificate document"
    }
  ],
  "summary": {
    "total": 60,
    "pass": 45,
    "fail": 5,
    "manual": 10,
    "compliance_rate": 90%
  }
}
```

---

## 6. 권장 즉시 적용 설정

```yaml
# 현재 → 권장
rule_profile: bwms
product_type: ECS    # ALL → ECS (도면에 따라)
severity_threshold: warning
# 추가 권장
output_format: detailed_checklist  # 신규
include_evidence: true             # 신규
```

---

## 7. 구현 로드맵

### Phase 1: 규칙 정의 (1일)
- [ ] 60개 체크리스트 항목 YAML 정의
- [ ] ECS/HYCHLOR 제품별 규칙 분리
- [ ] 자동화/Manual 분류

### Phase 2: 심볼 존재 규칙 (1일)
- [ ] 20개 심볼 존재 확인 규칙 구현
- [ ] YOLO 클래스명 매핑

### Phase 3: 연결성 규칙 (2일)
- [ ] 15개 연결성 확인 규칙 구현
- [ ] PID Analyzer 결과 활용

### Phase 4: 결과 포맷 (1일)
- [ ] 상세 체크리스트 결과 포맷
- [ ] Excel 내보내기 템플릿 연동

---

## 8. 다음 단계

1. [ ] BWMS 체크리스트 60개 항목 YAML 정의
2. [ ] ECS 제품 규칙 프로파일 생성
3. [ ] HYCHLOR 제품 규칙 프로파일 생성
4. [ ] Design Checker API 파라미터 확장

---

## 관련 파일

- `RULE_DEFINITIONS.md`: 60개 체크리스트 규칙 정의
- `PRODUCT_PROFILES.md`: ECS/HYCHLOR 프로파일
- `../../../models/design-checker-api/`: API 소스

---

*작성자*: Claude Code (Opus 4.5)
