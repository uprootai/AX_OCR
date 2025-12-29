# P&ID Analyzer API Endpoints

전체 21개 엔드포인트 가이드

---

## Health & Info (3개)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/health` | 헬스 체크 |
| GET | `/api/v1/health` | 헬스 체크 (v1) |
| GET | `/api/v1/info` | API 정보 및 BlueprintFlow 메타데이터 |

### GET /api/v1/info 응답 예시

```json
{
  "id": "pid-analyzer",
  "name": "P&ID Analyzer",
  "version": "2.0.0",
  "description": "P&ID 심볼 연결 분석 및 BOM 생성 API",
  "blueprintflow": {
    "category": "analysis",
    "color": "#10b981",
    "icon": "GitMerge"
  }
}
```

---

## Analysis (2개)

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/analyze` | 메인 분석 (연결성 그래프 + BOM 생성) |
| POST | `/api/v1/process` | BlueprintFlow 호환 (analyze 별칭) |

### curl 예시

```bash
# 심볼 연결 분석 + BOM 생성
curl -X POST http://localhost:5018/api/v1/analyze \
  -F "file=@pid_image.png" \
  -F 'symbols=[{"class":"pump","bbox":[100,200,150,250]}]' \
  -F 'lines=[{"start_point":[100,200],"end_point":[300,200]}]' \
  -F "generate_bom=true"
```

---

## BWMS (3개)

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/bwms/detect-equipment` | BWMS 장비 검출 (ECU, Pump 등) |
| POST | `/api/v1/bwms/generate-equipment-list` | BWMS 장비 목록 생성 |
| GET | `/api/v1/bwms/equipment-types` | 지원 장비 유형 조회 |

### curl 예시

```bash
# BWMS 장비 검출
curl -X POST http://localhost:5018/api/v1/bwms/detect-equipment \
  -F "file=@bwms_pid.png" \
  -F 'symbols=[{"class":"ecu","bbox":[100,200,150,250]}]'

# 지원 장비 유형
curl http://localhost:5018/api/v1/bwms/equipment-types
```

---

## Equipment (4개)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/v1/equipment/profiles` | 장비 프로필 목록 |
| GET | `/api/v1/equipment/profiles/{profile_id}` | 특정 프로필 상세 |
| POST | `/api/v1/equipment/detect` | 장비 검출 |
| POST | `/api/v1/equipment/export-excel` | Excel 내보내기 |

### curl 예시

```bash
# 프로필 목록 조회
curl http://localhost:5018/api/v1/equipment/profiles

# 장비 검출
curl -X POST http://localhost:5018/api/v1/equipment/detect \
  -F "file=@pid_image.png" \
  -F 'symbols=[{"class":"pump","bbox":[100,200,150,250]}]' \
  -F "profile_id=bwms_ecs"
```

---

## Region Rules (5개)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/v1/region-rules` | 영역 추출 규칙 목록 |
| GET | `/api/v1/region-rules/{rule_id}` | 특정 규칙 상세 |
| POST | `/api/v1/region-rules` | 규칙 생성 |
| PUT | `/api/v1/region-rules/{rule_id}` | 규칙 수정 |
| DELETE | `/api/v1/region-rules/{rule_id}` | 규칙 삭제 |

### curl 예시

```bash
# 규칙 목록 조회
curl http://localhost:5018/api/v1/region-rules

# 규칙 생성
curl -X POST http://localhost:5018/api/v1/region-rules \
  -H "Content-Type: application/json" \
  -d '{
    "id": "custom_rule",
    "name": "Custom Rule",
    "enabled": true,
    "category": "custom",
    "region_criteria": {"line_styles": ["dashed"], "min_area": 1000}
  }'
```

---

## Region Text & Valve Signal (4개)

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/region-text/extract` | 영역 기반 텍스트 추출 |
| POST | `/api/v1/valve-signal/extract` | 밸브 시그널 리스트 추출 |
| POST | `/api/v1/valve-signal/export-excel` | 밸브 시그널 Excel 내보내기 |

### curl 예시

```bash
# 영역 텍스트 추출
curl -X POST http://localhost:5018/api/v1/region-text/extract \
  -F "file=@pid_image.png" \
  -F 'regions=[{"id":0,"bbox":[100,200,500,400],"region_type":"signal_group"}]' \
  -F 'texts=[{"text":"BWV-001","bbox":[150,250,200,280]}]'

# 밸브 시그널 추출 (BWMS)
curl -X POST http://localhost:5018/api/v1/valve-signal/extract \
  -F "file=@bwms_pid.png" \
  -F 'regions=[{"id":0,"bbox":[100,200,500,400],"region_type":"signal_group"}]' \
  -F 'texts=[{"text":"BWV-001","bbox":[150,250,200,280]}]' \
  -F "rule_ids=valve_signal_bwms"

# Excel 내보내기
curl -X POST http://localhost:5018/api/v1/valve-signal/export-excel \
  -F 'valve_signals=[{"valve_id":"BWV-001","region_id":0}]' \
  -F "output_format=xlsx" \
  --output valve_signals.xlsx
```

---

## 규칙 파일 구조

```
region_rules.yaml         # UI에서 수정 가능한 규칙 설정
├── valve_signal_bwms     # BWMS 밸브 시그널 규칙
├── alarm_bypass          # 알람 바이패스 밸브 규칙
├── signal_region_general # 일반 시그널 영역 규칙
└── required_signal       # 필수 신호 추출 규칙
```

| 카테고리 | 설명 | 색상 |
|----------|------|------|
| `bwms` | BWMS 선박평형수 관련 | 빨강 |
| `general` | 일반 P&ID 규칙 | 파랑 |
| `custom` | 사용자 정의 규칙 | 회색 |

---

**Last Updated**: 2025-12-29
