# PID Analyzer API

> **P&ID 연결성 분석 및 BOM 추출**

---

## 기본 정보

| 항목 | 값 |
|------|-----|
| **포트** | 5018 |
| **엔드포인트** | `POST /api/v1/analyze` |
| **GPU 필요** | ❌ CPU 전용 |
| **RAM** | ~2GB |

---

## 입력

이 API는 JSON 형식의 입력을 받습니다.

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `symbols` | array | ✅ | YOLO-PID 검출 결과 |
| `lines` | array | ✅ | Line Detector 결과 |
| `intersections` | array | ❌ | 교차점 정보 |
| `image` | string | ❌ | 원본 이미지 (base64, 시각화용) |

---

## 파라미터

### generate_bom (BOM 생성)

부품 리스트(Bill of Materials)를 생성합니다.

- **타입**: boolean
- **기본값**: `true`

### generate_valve_list (밸브 리스트 생성)

밸브 시그널 리스트를 생성합니다.

- **타입**: boolean
- **기본값**: `true`

### generate_equipment_list (장비 리스트 생성)

장비 리스트를 생성합니다.

- **타입**: boolean
- **기본값**: `true`

### visualize (시각화)

연결 관계를 시각화합니다.

- **타입**: boolean
- **기본값**: `true`

---

## 출력

| 필드 | 타입 | 설명 |
|------|------|------|
| `connections` | array | 심볼 간 연결 관계 |
| `graph` | object | 연결성 그래프 |
| `bom` | array | 부품 리스트 (BOM) |
| `valve_list` | array | 밸브 시그널 리스트 |
| `equipment_list` | array | 장비 리스트 |

### connection 객체 구조

```json
{
  "id": "C001",
  "from": {
    "symbol_id": "S001",
    "type": "gate_valve",
    "port": "outlet"
  },
  "to": {
    "symbol_id": "S002",
    "type": "centrifugal_pump",
    "port": "inlet"
  },
  "line_id": "L005",
  "line_type": "process_line"
}
```

### bom 객체 구조

```json
{
  "item_no": 1,
  "tag": "V-001",
  "description": "Gate Valve",
  "type": "gate_valve",
  "quantity": 1,
  "size": "2\"",
  "material": "SS304"
}
```

### valve_list 객체 구조

```json
{
  "tag": "XV-001",
  "type": "solenoid_valve",
  "connected_to": ["P-001", "T-001"],
  "signal_type": "DI/DO",
  "fail_position": "FC"
}
```

### equipment_list 객체 구조

```json
{
  "tag": "P-001",
  "type": "centrifugal_pump",
  "connected_valves": ["V-001", "V-002"],
  "inlet_line": "L001",
  "outlet_line": "L002"
}
```

---

## 사용 예시

### Python
```python
import requests

# 먼저 YOLO-PID와 Line Detector 실행
yolo_result = {...}  # YOLO-PID 결과
line_result = {...}  # Line Detector 결과

data = {
    "symbols": yolo_result["detections"],
    "lines": line_result["lines"],
    "intersections": line_result.get("intersections", []),
    "generate_bom": True,
    "generate_valve_list": True,
    "generate_equipment_list": True,
    "visualize": True
}

response = requests.post(
    "http://localhost:5018/api/v1/analyze",
    json=data
)
print(response.json())
```

---

## 분석 알고리즘

```
YOLO-PID 심볼
    ↓
[심볼 위치 분석]
  - 바운딩 박스 중심점
  - 포트 위치 추정
    ↓
Line Detector 라인
    ↓
[연결성 분석]
  - 심볼-라인 교차 검출
  - 그래프 구축
    ↓
[BOM/리스트 생성]
  - 부품 집계
  - 태그 생성
    ↓
결과 출력
```

---

## 권장 파이프라인

### P&ID 전체 분석
```
ImageInput → YOLO-PID → Line Detector → PID Analyzer → Design Checker
```

### 연결성만 분석
```
ImageInput → YOLO-PID → Line Detector → PID Analyzer
```

---

## 리소스 요구사항

| 항목 | 최소 | 권장 |
|------|------|------|
| RAM | 1GB | 2GB |
| CPU 코어 | 2 | 4 |

---

**마지막 업데이트**: 2025-12-09
