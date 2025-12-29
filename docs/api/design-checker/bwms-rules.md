# BWMS Rules Management Guide

TECHCROSS BWMS P&ID 설계 규칙 관리 가이드

---

## 개요

BWMS (Ballast Water Management System) 규칙 시스템은 선박평형수처리시스템 P&ID 도면 검증을 위한 전용 규칙 세트입니다.

### 규칙 구성

| 구분 | 수량 | 설명 |
|------|------|------|
| **내장 규칙** | 7개 | bwms_rules.py에 하드코딩 |
| **동적 규칙** | 가변 | YAML/Excel에서 로드 |

---

## 내장 BWMS 규칙 (7개)

### BWMS-001: G-2 Sampling Port 상류 위치
- **심각도**: warning
- **자동검사**: O
- **설명**: G-2 Sampling Port는 상류(upstream)에 위치해야 함

### BWMS-004: FMU-ECU 순서 검증
- **심각도**: error
- **자동검사**: O
- **설명**: FMU(유량계)는 ECU(전해조) 후단에 위치해야 함

### BWMS-005: GDS 위치 검증
- **심각도**: error
- **자동검사**: O
- **설명**: GDS(가스감지센서)는 ECU 또는 HGU 상부에 위치해야 함

### BWMS-006: TSU-APU 거리 제한
- **심각도**: warning
- **자동검사**: O
- **설명**: TSU와 APU 간 거리는 5m 이내여야 함

### BWMS-007: Mixing Pump 용량 검증
- **심각도**: warning
- **자동검사**: X (수동 확인 필요)
- **설명**: Mixing Pump 용량은 Ballast Pump의 4.3%여야 함

### BWMS-008: UV Reactor 사양 검증
- **심각도**: warning
- **자동검사**: X (수동 확인 필요)
- **설명**: UV Reactor 사양은 처리 용량에 맞게 설정

### BWMS-009: HYCHLOR 필터 위치
- **심각도**: warning
- **자동검사**: O
- **설명**: HYCHLOR 제품에서 필터는 ECU 전단에 위치해야 함
- **product_type**: HYCHLOR

---

## 동적 규칙 관리

### 규칙 파일 구조

```yaml
# config/ecs/ecs_rules.yaml
metadata:
  created_at: "2025-12-29T05:36:02"
  source: "excel_upload"
  original_file: "ECS_Checklist.xlsx"
  product_type: "ECS"

rules:
  - rule_id: "BWMS-001"
    name: "G-2 Sampling Port 상류 위치"
    name_en: "G-2 Sampling Port Upstream Position"
    severity: "warning"
    check_type: "position"
    category: "ecs"
    equipment: "G-2 Sampling Port"
    condition: "upstream_of"
    condition_value: ""
    description: "G-2 Sampling Port는 상류에 위치해야 합니다"
    suggestion: "위치를 확인하세요"
    auto_checkable: true
    standard: "TECHCROSS BWMS"
```

### 카테고리별 폴더

| 폴더 | 용도 | 예시 파일 |
|------|------|-----------|
| `config/common/` | 공통 규칙 | base_rules.yaml |
| `config/ecs/` | ECS 전용 | ecs_rules.yaml |
| `config/hychlor/` | HYCHLOR 전용 | hychlor_rules.yaml |
| `config/custom/` | 프로젝트별 | project_a.yaml |

---

## Excel 체크리스트 업로드

### 템플릿 다운로드

```bash
curl -O http://localhost:5019/api/v1/checklist/template
```

### 템플릿 열 구조

| 열 | 필수 | 설명 |
|----|------|------|
| `rule_id` | O | 규칙 ID (예: BWMS-001) |
| `name` | O | 규칙 이름 (한글) |
| `name_en` | X | 규칙 이름 (영문) |
| `severity` | O | error / warning / info |
| `check_type` | O | position / sequence / distance / capacity |
| `equipment` | O | 대상 장비 (쉼표 구분) |
| `condition` | O | 조건 (upstream_of, after, above 등) |
| `condition_value` | X | 조건 값 (예: 5m) |
| `description` | X | 상세 설명 |
| `suggestion` | X | 해결 제안 |
| `auto_checkable` | X | 자동검사 가능 여부 (TRUE/FALSE) |

### 업로드

```bash
curl -X POST http://localhost:5019/api/v1/checklist/upload \
  -F "file=@my_checklist.xlsx" \
  -F "category=ecs" \
  -F "product_type=ECS"
```

---

## 규칙 활성화/비활성화

### 개별 규칙 제어

```bash
# 특정 규칙 비활성화
curl -X POST http://localhost:5019/api/v1/rules/disable \
  -F "rule_id=BWMS-007"

# 규칙 다시 활성화
curl -X POST http://localhost:5019/api/v1/rules/enable \
  -F "rule_id=BWMS-007"
```

### 프로필 단위 제어

```bash
# ECS 프로필 전체 활성화
curl -X POST http://localhost:5019/api/v1/rules/profile/activate \
  -F "profile_path=ecs/ecs_rules.yaml"

# ECS 프로필 비활성화
curl -X POST http://localhost:5019/api/v1/rules/profile/deactivate \
  -F "profile_path=ecs/ecs_rules.yaml"
```

---

## 제품 타입 필터링

| product_type | 설명 | 적용 규칙 |
|--------------|------|-----------|
| `ALL` | 모든 제품 | 모든 규칙 적용 |
| `ECS` | ECS 제품만 | BWMS-007 등 |
| `HYCHLOR` | HYCHLOR만 | BWMS-009 등 |

---

## 서버 시작 시 자동 로드

`api_server.py`의 lifespan에서 자동으로 규칙 로드:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # config/ 폴더의 YAML 자동 로드
    loaded_rules = rule_loader.load_all_rules()
    bwms_checker._dynamic_rules = dict(loaded_rules)
    yield
```

---

## 상태 확인 API

```bash
# 전체 상태
curl http://localhost:5019/api/v1/rules/status

# 현재 로드된 BWMS 규칙
curl http://localhost:5019/api/v1/checklist/current
```

### 응답 예시

```json
{
  "active_profiles": [
    "common/base_rules.yaml",
    "ecs/ecs_rules.yaml"
  ],
  "disabled_rules": ["BWMS-007"],
  "total_rules_loaded": 6,
  "categories": {
    "ecs": { "files": 1, "file_list": ["ecs_rules.yaml"] }
  }
}
```

---

**Last Updated**: 2025-12-29
