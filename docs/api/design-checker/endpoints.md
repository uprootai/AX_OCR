# Design Checker API Endpoints

전체 20개 엔드포인트 가이드

---

## Health & Info (3개)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/health` | 헬스 체크 |
| GET | `/api/v1/health` | 헬스 체크 (v1) |
| GET | `/api/v1/info` | API 정보 및 규칙 통계 |

### GET /api/v1/info 응답 예시

```json
{
  "success": true,
  "data": {
    "name": "Design Checker API",
    "version": "1.0.0",
    "rules": {
      "design_rules": 20,
      "bwms_builtin": 7,
      "bwms_dynamic": 6,
      "total": 33
    },
    "standards": ["ISO 10628", "ISA 5.1", "TECHCROSS BWMS"]
  }
}
```

---

## Check (3개)

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/check` | 통합 설계 검증 |
| POST | `/api/v1/check/bwms` | BWMS 전용 검증 |
| POST | `/api/v1/process` | BlueprintFlow 호환 |

### curl 예시

```bash
# 통합 검증
curl -X POST http://localhost:5019/api/v1/check \
  -F 'symbols=[{"class":"pump","bbox":[100,200,150,250]}]' \
  -F 'connections=[]' \
  -F 'severity_threshold=warning'

# BWMS 전용
curl -X POST http://localhost:5019/api/v1/check/bwms \
  -F 'symbols=[{"class":"ecu","bbox":[100,200,150,250]}]' \
  -F 'enabled_rules=BWMS-001,BWMS-004'
```

---

## Rules (6개)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/v1/rules` | 설계 규칙 목록 (20개) |
| GET | `/api/v1/rules/bwms` | BWMS 규칙 목록 (7+동적) |
| GET | `/api/v1/rules/status` | 규칙 로딩 상태 |
| GET | `/api/v1/rules/files` | YAML 파일 목록 |
| POST | `/api/v1/rules/reload` | YAML에서 규칙 재로드 |
| POST | `/api/v1/rules/disable` | 개별 규칙 비활성화 |
| POST | `/api/v1/rules/enable` | 개별 규칙 활성화 |

### 규칙 비활성화/활성화 예시

```bash
# 규칙 비활성화
curl -X POST http://localhost:5019/api/v1/rules/disable \
  -F "rule_id=BWMS-001"

# 규칙 활성화
curl -X POST http://localhost:5019/api/v1/rules/enable \
  -F "rule_id=BWMS-001"

# 규칙 상태 확인
curl http://localhost:5019/api/v1/rules/status
```

---

## Profile (2개)

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/rules/profile/activate` | 규칙 프로필 활성화 |
| POST | `/api/v1/rules/profile/deactivate` | 규칙 프로필 비활성화 |

### 프로필 관리 예시

```bash
# ECS 전용 프로필 활성화
curl -X POST http://localhost:5019/api/v1/rules/profile/activate \
  -F "profile_path=ecs/ecs_rules.yaml"

# 프로필 비활성화
curl -X POST http://localhost:5019/api/v1/rules/profile/deactivate \
  -F "profile_path=ecs/ecs_rules.yaml"
```

---

## Checklist (5개)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/v1/checklist/template` | Excel 템플릿 다운로드 |
| POST | `/api/v1/checklist/upload` | 체크리스트 업로드 |
| GET | `/api/v1/checklist/files` | 업로드된 파일 목록 |
| POST | `/api/v1/checklist/load` | 저장된 체크리스트 로드 |
| GET | `/api/v1/checklist/current` | 현재 로드된 규칙 조회 |

### 체크리스트 업로드 예시

```bash
# Excel 체크리스트 업로드 (ECS 카테고리)
curl -X POST http://localhost:5019/api/v1/checklist/upload \
  -F "file=@checklist.xlsx" \
  -F "category=ecs" \
  -F "product_type=ECS"

# 현재 로드된 규칙 확인
curl http://localhost:5019/api/v1/checklist/current
```

---

## 카테고리별 YAML 관리

```
config/
├── common/          # 공통 규칙
├── ecs/             # ECS 제품 전용
├── hychlor/         # HYCHLOR 제품 전용
└── custom/          # 사용자 정의
```

| 카테고리 | 설명 | product_type |
|----------|------|--------------|
| `common` | 모든 제품 공통 규칙 | ALL |
| `ecs` | ECS 전용 규칙 | ECS |
| `hychlor` | HYCHLOR 전용 규칙 | HYCHLOR |
| `custom` | 프로젝트별 커스텀 규칙 | ALL |

---

**Last Updated**: 2025-12-29
