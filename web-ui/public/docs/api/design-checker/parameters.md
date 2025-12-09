# Design Checker API

> **P&ID 도면 설계 오류 검출 및 규정 검증**

---

## 기본 정보

| 항목 | 값 |
|------|-----|
| **포트** | 5019 |
| **엔드포인트** | `POST /api/v1/check` |
| **GPU 필요** | ❌ CPU 전용 |
| **RAM** | ~1GB |

---

## 입력

이 API는 JSON 형식의 입력을 받습니다.

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `symbols` | array | ✅ | YOLO-PID 검출 결과 |
| `connections` | array | ✅ | PID Analyzer 연결 분석 결과 |
| `lines` | array | ❌ | Line Detector 결과 |

---

## 파라미터

### categories (검사 카테고리)

검사할 규칙 카테고리를 지정합니다. 빈 값이면 전체 검사.

- **타입**: string (쉼표 구분)
- **기본값**: `` (전체)
- **예시**: `valve,instrument`, `safety`

### 지원 카테고리

| 카테고리 | 설명 |
|----------|------|
| `valve` | 밸브 배치 규칙 |
| `instrument` | 계기 연결 규칙 |
| `safety` | 안전 장치 규칙 |
| `piping` | 배관 규칙 |
| `equipment` | 장비 연결 규칙 |

### severity_threshold (최소 심각도)

보고할 최소 심각도 레벨을 설정합니다.

| 값 | 설명 | 포함 범위 |
|----|------|----------|
| `error` | 오류만 | 오류 |
| `warning` | 경고 이상 | 오류 + 경고 |
| `info` | 전체 (기본) | 오류 + 경고 + 정보 |

- **타입**: select
- **기본값**: `info`

---

## 출력

| 필드 | 타입 | 설명 |
|------|------|------|
| `violations` | array | 위반 사항 목록 |
| `summary` | object | 검사 요약 |
| `compliance_score` | number | 규정 준수율 (0-100%) |

### violation 객체 구조

```json
{
  "id": "V001",
  "rule_id": "VAL-001",
  "rule_name": "Relief valve required",
  "severity": "error",
  "category": "safety",
  "message": "펌프 P-001 출구에 릴리프 밸브가 없습니다",
  "location": {
    "symbol_id": "S001",
    "symbol_type": "centrifugal_pump",
    "bbox": [100, 200, 150, 250]
  },
  "suggestion": "릴리프 밸브(RV)를 펌프 출구 라인에 추가하세요"
}
```

### summary 객체 구조

```json
{
  "total_rules_checked": 45,
  "passed": 42,
  "violations": {
    "error": 1,
    "warning": 2,
    "info": 5
  },
  "by_category": {
    "valve": {"passed": 10, "failed": 1},
    "safety": {"passed": 8, "failed": 2},
    "instrument": {"passed": 12, "failed": 0}
  }
}
```

---

## 검사 규칙 예시

### 안전 규칙 (Safety)

| 규칙 ID | 설명 |
|---------|------|
| SAF-001 | 펌프 출구에 릴리프 밸브 필요 |
| SAF-002 | 압력 용기에 안전 밸브 필요 |
| SAF-003 | 비상 차단 밸브(ESD) 배치 |

### 밸브 규칙 (Valve)

| 규칙 ID | 설명 |
|---------|------|
| VAL-001 | 체크 밸브 방향 검증 |
| VAL-002 | 수동 밸브 접근성 |
| VAL-003 | 컨트롤 밸브 바이패스 |

### 계기 규칙 (Instrument)

| 규칙 ID | 설명 |
|---------|------|
| INS-001 | 압력계 위치 적정성 |
| INS-002 | 유량계 직관부 확보 |
| INS-003 | 온도계 삽입 깊이 |

---

## 사용 예시

### Python
```python
import requests

# 먼저 YOLO-PID, Line Detector, PID Analyzer 실행
yolo_result = {...}      # YOLO-PID 결과
pid_result = {...}       # PID Analyzer 결과
line_result = {...}      # Line Detector 결과

data = {
    "symbols": yolo_result["detections"],
    "connections": pid_result["connections"],
    "lines": line_result.get("lines", []),
    "categories": "",  # 전체 검사
    "severity_threshold": "info"
}

response = requests.post(
    "http://localhost:5019/api/v1/check",
    json=data
)

result = response.json()
print(f"준수율: {result['compliance_score']}%")
print(f"위반 사항: {len(result['violations'])}건")
```

---

## 권장 파이프라인

### P&ID 전체 분석
```
ImageInput → YOLO-PID → Line Detector → PID Analyzer → Design Checker
```

### 안전 검사만
```
... → Design Checker (categories=safety)
```

---

## 리소스 요구사항

| 항목 | 최소 | 권장 |
|------|------|------|
| RAM | 512MB | 1GB |
| CPU 코어 | 2 | 4 |

---

**마지막 업데이트**: 2025-12-09
