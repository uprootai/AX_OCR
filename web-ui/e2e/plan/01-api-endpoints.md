# API Endpoints Test Scenarios

> **Total Endpoints**: 119개
> **Total Test Scenarios**: 200+
> **Priority**: P0 (Critical) ~ P3 (Low)

---

## 1. 시스템 상태 API (5개 엔드포인트)

### 1.1 GET `/` - API 상태 확인

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| SYS-001 | 정상 상태 확인 | - | `{status: "healthy"}` | P0 |
| SYS-002 | 응답 스키마 검증 | - | `name`, `version`, `timestamp` 포함 | P1 |

### 1.2 GET `/health` - 헬스 체크

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| SYS-003 | 정상 헬스 체크 | - | HTTP 200, `{status: "healthy"}` | P0 |
| SYS-004 | 서비스 다운 시 | 서비스 중단 | HTTP 503 또는 연결 오류 | P1 |

### 1.3 GET `/api/system/gpu` - GPU 상태 조회

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| SYS-005 | GPU 사용 가능 | GPU 환경 | `{available: true, gpu_util, memory_*}` | P1 |
| SYS-006 | GPU 없음 | CPU 환경 | `{available: false}` | P1 |
| SYS-007 | VRAM 사용량 검증 | GPU 사용 중 | `memory_percent` 0-100 범위 | P2 |

### 1.4 GET `/api/system/info` - 시스템 정보

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| SYS-008 | 시스템 정보 조회 | - | `class_count`, `version` 포함 | P1 |
| SYS-009 | 세션 수 정확성 | 세션 3개 생성 후 | `session_count: 3` | P2 |

### 1.5 POST `/api/system/cache/clear` - 캐시 정리

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| SYS-010 | 전체 캐시 정리 | `cache_type: "all"` | `{status: "success", cleared: true}` | P1 |
| SYS-011 | 업로드 캐시만 | `cache_type: "uploads"` | 업로드 디렉토리 정리 | P2 |
| SYS-012 | 메모리 캐시만 | `cache_type: "memory"` | 메모리 캐시 정리 | P2 |
| SYS-013 | 잘못된 타입 | `cache_type: "invalid"` | HTTP 400 | P2 |

---

## 2. 세션 관리 API (9개 엔드포인트)

### 2.1 POST `/sessions/upload` - 이미지 업로드 & 세션 생성

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| SES-001 | PNG 이미지 업로드 | `page_1.png` | 세션 ID 반환, 파일 저장 | P0 |
| SES-002 | JPG 이미지 업로드 | `test.jpg` | 세션 ID 반환 | P0 |
| SES-003 | PDF 업로드 | `drawing.pdf` | 첫 페이지 이미지 변환 | P1 |
| SES-004 | drawing_type 지정 | `drawing_type: "pid"` | 해당 타입으로 설정 | P1 |
| SES-005 | features 지정 | `features: "pid_valve_detection,pid_equipment_detection"` | 기능 활성화 | P1 |
| SES-006 | 대용량 파일 (50MB) | 50MB 이미지 | HTTP 413 또는 처리 | P2 |
| SES-007 | 지원하지 않는 형식 | `file.txt` | HTTP 400 | P1 |
| SES-008 | 빈 파일 | 0 바이트 파일 | HTTP 400 | P1 |
| SES-009 | 손상된 이미지 | 손상된 PNG | HTTP 400 또는 500 | P2 |

### 2.2 GET `/sessions` - 세션 목록 조회

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| SES-010 | 기본 조회 | - | 최근 50개 세션 | P0 |
| SES-011 | limit 적용 | `limit: 10` | 10개 세션 | P1 |
| SES-012 | 빈 목록 | 세션 없음 | `[]` | P1 |
| SES-013 | limit 범위 초과 | `limit: 1000` | HTTP 422 (최대 100) | P2 |
| SES-014 | limit 음수 | `limit: -1` | HTTP 422 (최소 1) | P2 |

### 2.3 GET `/sessions/{session_id}` - 세션 상세 조회

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| SES-015 | 정상 조회 | 유효한 session_id | 세션 상세 정보 | P0 |
| SES-016 | 이미지 포함 | `include_image: true` | `image_base64` 포함 | P1 |
| SES-017 | 이미지 제외 | `include_image: false` | `image_base64` 없음 | P1 |
| SES-018 | 존재하지 않는 세션 | `session_id: "invalid"` | HTTP 404 | P1 |

### 2.4 PATCH `/sessions/{session_id}` - 세션 정보 업데이트

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| SES-019 | 상태 변경 | `{status: "completed"}` | 상태 업데이트 | P1 |
| SES-020 | features 변경 | `{features: ["gdt_parsing"]}` | 기능 업데이트 | P1 |
| SES-021 | 이미지 크기 설정 | `{image_width: 1920, image_height: 1080}` | 크기 저장 | P2 |
| SES-022 | 존재하지 않는 세션 | 잘못된 ID | HTTP 404 | P1 |

### 2.5 GET `/sessions/{session_id}/image` - 세션 이미지 조회

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| SES-023 | 정상 조회 | 유효한 session_id | Base64 이미지, MIME 타입 | P0 |
| SES-024 | 이미지 없는 세션 | 이미지 삭제됨 | HTTP 404 | P1 |

### 2.6 DELETE `/sessions/{session_id}` - 세션 삭제

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| SES-025 | 정상 삭제 | 유효한 session_id | HTTP 200, 파일 삭제 | P0 |
| SES-026 | 존재하지 않는 세션 | 잘못된 ID | HTTP 404 | P1 |
| SES-027 | 삭제 후 재조회 | 삭제된 session_id | HTTP 404 | P1 |

### 2.7 DELETE `/sessions` - 모든 세션 삭제

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| SES-028 | 전체 삭제 | 세션 5개 존재 | `{deleted_count: 5}` | P1 |
| SES-029 | 빈 상태에서 삭제 | 세션 0개 | `{deleted_count: 0}` | P2 |

### 2.8 GET `/api/sessions/stats` - 세션 통계

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| SES-030 | 통계 조회 | - | `total_sessions`, `by_status` | P2 |

### 2.9 DELETE `/api/sessions/cleanup` - 오래된 세션 정리

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| SES-031 | 24시간 이상 세션 정리 | `max_age_hours: 24` | 오래된 세션 삭제 | P2 |
| SES-032 | 1시간 이상 세션 정리 | `max_age_hours: 1` | 해당 세션 삭제 | P2 |

---

## 3. 검출 API (8개 엔드포인트)

### 3.1 POST `/detection/{session_id}/detect` - YOLO 검출 실행

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| DET-001 | 기본 검출 | 유효한 session_id | 검출 결과, 바운딩 박스 | P0 |
| DET-002 | confidence 0.4 (기본) | `config.confidence: 0.4` | 중간 수준 검출 | P0 |
| DET-003 | confidence 0.1 (낮음) | `config.confidence: 0.1` | 많은 검출 | P1 |
| DET-004 | confidence 0.9 (높음) | `config.confidence: 0.9` | 적은 검출 | P1 |
| DET-005 | iou_threshold 0.5 | `config.iou_threshold: 0.5` | NMS 적용 | P1 |
| DET-006 | imgsz 640 | `config.imgsz: 640` | 작은 입력 크기 | P2 |
| DET-007 | imgsz 1280 | `config.imgsz: 1280` | 큰 입력 크기 | P2 |
| DET-008 | model_id 지정 | `config.model_id: "panasia_yolo"` | 특정 모델 사용 | P1 |
| DET-009 | 빈 이미지 | 검출 대상 없음 | `{detections: [], total_count: 0}` | P1 |
| DET-010 | 대용량 이미지 | 4000x4000 이미지 | 정상 처리 또는 리사이즈 | P2 |

### 3.2 GET `/detection/{session_id}/detections` - 검출 결과 조회

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| DET-011 | 정상 조회 | 검출 완료된 세션 | 모든 검출 결과 | P0 |
| DET-012 | 검증 상태 포함 | - | `verification_status` 필드 | P1 |
| DET-013 | 검출 없는 세션 | 검출 전 세션 | `{detections: []}` | P1 |

### 3.3 PUT `/detection/{session_id}/verify` - 단일 검출 검증

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| DET-014 | 승인 | `{detection_id, status: "approved"}` | 상태 변경 | P0 |
| DET-015 | 거부 | `{detection_id, status: "rejected"}` | 상태 변경 | P0 |
| DET-016 | 클래스 수정 | `{detection_id, status: "modified", modified_class_name: "NEW"}` | 클래스 변경 | P1 |
| DET-017 | 바운딩 박스 수정 | `{detection_id, modified_bbox: [x1,y1,x2,y2]}` | 좌표 변경 | P2 |
| DET-018 | 존재하지 않는 검출 | 잘못된 detection_id | HTTP 404 | P1 |

### 3.4 PUT `/detection/{session_id}/verify/bulk` - 일괄 검출 검증

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| DET-019 | 전체 승인 | `{action: "approve_all"}` | 모든 pending → approved | P0 |
| DET-020 | 전체 거부 | `{action: "reject_all"}` | 모든 pending → rejected | P1 |
| DET-021 | 선택 승인 | `{detection_ids: [...], action: "approve"}` | 선택 항목만 승인 | P1 |
| DET-022 | 빈 목록 | `{detection_ids: []}` | 변경 없음 | P2 |

### 3.5 POST `/detection/{session_id}/manual` - 수동 검출 추가

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| DET-023 | 정상 추가 | `{class_name, bbox: [x1,y1,x2,y2]}` | 새 검출 추가, status: "manual" | P0 |
| DET-024 | 신뢰도 1.0 | 수동 추가 | `confidence: 1.0` | P1 |
| DET-025 | 잘못된 좌표 | `{bbox: [-1, 0, 100, 100]}` | HTTP 400 | P2 |
| DET-026 | 좌표 범위 초과 | 이미지 크기 초과 | HTTP 400 또는 클램핑 | P2 |

### 3.6 POST `/detection/{session_id}/import-bulk` - 일괄 검출 가져오기

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| DET-027 | YOLO 형식 가져오기 | YOLO 레이블 배열 | 검출 생성 | P2 |
| DET-028 | initial_status 지정 | `initial_status: "approved"` | 모두 승인 상태 | P2 |

### 3.7 DELETE `/detection/{session_id}/detection/{detection_id}` - 검출 삭제

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| DET-029 | 정상 삭제 | 유효한 detection_id | 검출 제거 | P1 |
| DET-030 | 존재하지 않는 검출 | 잘못된 ID | HTTP 404 | P2 |

### 3.8 GET `/detection/classes` - 클래스 목록 조회

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| DET-031 | 클래스 목록 | - | 모든 클래스와 매핑 | P1 |

---

## 4. BOM 관리 API (5개 엔드포인트)

### 4.1 POST `/bom/{session_id}/generate` - BOM 생성

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| BOM-001 | 정상 생성 | 검증 완료된 세션 | BOM 항목 생성 | P0 |
| BOM-002 | 가격 계산 | - | 단가 × 수량 = 합계 | P1 |
| BOM-003 | 클래스별 집계 | - | 동일 클래스 수량 합계 | P1 |
| BOM-004 | 검출 없는 세션 | detections 없음 | `{items: []}` | P1 |
| BOM-005 | 승인된 항목만 | approved만 | rejected 제외 | P1 |

### 4.2 GET `/bom/{session_id}` - BOM 조회

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| BOM-006 | 정상 조회 | 생성된 BOM | 전체 BOM 데이터 | P0 |
| BOM-007 | BOM 없는 세션 | 생성 전 | HTTP 404 또는 빈 응답 | P1 |

### 4.3 POST `/bom/{session_id}/export` - BOM 내보내기

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| BOM-008 | Excel 내보내기 | `format: "excel"` | .xlsx 파일 경로 | P0 |
| BOM-009 | CSV 내보내기 | `format: "csv"` | .csv 파일 경로 | P1 |
| BOM-010 | JSON 내보내기 | `format: "json"` | .json 파일 경로 | P1 |
| BOM-011 | 지원하지 않는 형식 | `format: "xml"` | HTTP 501 | P2 |

### 4.4 GET `/bom/{session_id}/download` - BOM 파일 다운로드

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| BOM-012 | Excel 다운로드 | `format: "excel"` | FileResponse (.xlsx) | P0 |
| BOM-013 | Content-Type 확인 | - | `application/vnd.openxmlformats-...` | P1 |
| BOM-014 | 파일명 확인 | - | `Content-Disposition` 헤더 | P2 |

### 4.5 GET `/bom/{session_id}/summary` - BOM 요약 조회

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| BOM-015 | 요약 조회 | - | `item_count`, `detection_count` | P1 |

---

## 5. P&ID Features API (16개 엔드포인트)

### 5.1 POST `/pid-features/{session_id}/valve/detect` - 밸브 검출

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| PID-001 | 기본 검출 | P&ID 이미지 | 밸브 목록 | P0 |
| PID-002 | 카테고리 분류 | - | Control, Isolation, Safety 등 6개 | P0 |
| PID-003 | rule_id 지정 | `rule_id: "custom_rule"` | 해당 규칙 적용 | P1 |
| PID-004 | profile 지정 | `profile: "bwms"` | BWMS 프로파일 적용 | P1 |
| PID-005 | language 지정 | `language: "ko"` | 한국어 OCR | P2 |

### 5.2 GET `/pid-features/{session_id}/valve` - 밸브 조회

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| PID-006 | 정상 조회 | 검출 완료 | 모든 밸브 데이터 | P0 |
| PID-007 | 카테고리별 집계 | - | `by_category` 통계 | P1 |

### 5.3 POST `/pid-features/{session_id}/equipment/detect` - 장비 검출

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| PID-008 | 기본 검출 | P&ID 이미지 | 장비 목록 | P0 |
| PID-009 | 타입 분류 | - | PUMP, VALVE, TANK 등 9개 | P0 |
| PID-010 | vendor_supply 감지 | `*` 표시 장비 | `vendor_supply: true` | P1 |
| PID-011 | BWMS 태그 인식 | - | ECU, FMU, HGU 등 | P1 |

### 5.4 GET `/pid-features/{session_id}/equipment` - 장비 조회

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| PID-012 | 정상 조회 | 검출 완료 | 모든 장비 데이터 | P0 |
| PID-013 | 타입별 집계 | - | `by_type` 통계 | P1 |

### 5.5 POST `/pid-features/{session_id}/checklist/check` - 체크리스트 검사

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| PID-014 | 기본 검사 | P&ID 데이터 | 체크리스트 결과 | P0 |
| PID-015 | 60개 항목 검증 | - | `total_count: 60` 근처 | P0 |
| PID-016 | rule_profile: default | `rule_profile: "default"` | 기본 규칙 적용 | P1 |
| PID-017 | rule_profile: bwms | `rule_profile: "bwms"` | BWMS 규칙 적용 | P1 |
| PID-018 | enabled_rules 지정 | `enabled_rules: "rule1,rule2"` | 특정 규칙만 | P2 |
| PID-019 | compliance_rate 계산 | - | 0.0~1.0 범위 | P1 |
| PID-020 | auto_status vs final_status | - | 두 상태 구분 | P1 |

### 5.6 GET `/pid-features/{session_id}/checklist` - 체크리스트 조회

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| PID-021 | 정상 조회 | 검사 완료 | 모든 체크리스트 항목 | P0 |
| PID-022 | summary 통계 | - | Pass, Fail, N/A 등 집계 | P1 |

### 5.7 POST `/pid-features/{session_id}/deviation/analyze` - 편차 분석

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| PID-023 | 기본 분석 | - | 편차 목록 | P1 |
| PID-024 | analysis_types: standard_check | - | 표준 기반 검사 | P1 |
| PID-025 | analysis_types: revision_compare | `baseline_session_id` 포함 | 리비전 비교 | P2 |
| PID-026 | severity_threshold: high | - | high 이상만 | P1 |
| PID-027 | standards: ISO_10628 | - | ISO 10628 기준 | P2 |

### 5.8 GET `/pid-features/{session_id}/deviation` - 편차 조회

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| PID-028 | 정상 조회 | 분석 완료 | 모든 편차 데이터 | P1 |
| PID-029 | 심각도별 집계 | - | `by_severity` 통계 | P1 |

### 5.9 GET `/pid-features/{session_id}/verify/queue` - 검증 큐

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| PID-030 | 밸브 검증 큐 | `item_type: "valve"` | 밸브 검증 목록 | P0 |
| PID-031 | 장비 검증 큐 | `item_type: "equipment"` | 장비 검증 목록 | P0 |
| PID-032 | 체크리스트 검증 큐 | `item_type: "checklist_item"` | 체크리스트 검증 목록 | P0 |

### 5.10 POST `/pid-features/{session_id}/verify` - 항목 검증

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| PID-033 | 밸브 승인 | `{item_id, item_type: "valve", action: "approve"}` | 상태 변경 | P0 |
| PID-034 | 장비 거부 | `{item_id, item_type: "equipment", action: "reject"}` | 상태 변경 | P0 |
| PID-035 | 수정 | `{..., action: "modify", modified_data: {...}}` | 데이터 수정 | P1 |

### 5.11 POST `/pid-features/{session_id}/verify/bulk` - 일괄 검증

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| PID-036 | 전체 승인 | `{item_ids: [...], action: "approve"}` | 모든 항목 승인 | P0 |
| PID-037 | 전체 거부 | `{item_ids: [...], action: "reject"}` | 모든 항목 거부 | P1 |

### 5.12 POST `/pid-features/{session_id}/export` - Excel 내보내기

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| PID-038 | 밸브 내보내기 | `export_type: "valve"` | Excel 파일 | P0 |
| PID-039 | 장비 내보내기 | `export_type: "equipment"` | Excel 파일 | P0 |
| PID-040 | 체크리스트 내보내기 | `export_type: "checklist"` | Excel 파일 | P0 |
| PID-041 | 전체 내보내기 | `export_type: "all"` | Excel 파일 (여러 시트) | P0 |
| PID-042 | include_rejected: true | - | 거부 항목 포함 | P1 |
| PID-043 | include_rejected: false | - | 거부 항목 제외 | P1 |
| PID-044 | project_name 포함 | `project_name: "Test"` | 헤더에 포함 | P2 |
| PID-045 | drawing_no 포함 | `drawing_no: "DWG-001"` | 헤더에 포함 | P2 |

### 5.13 GET `/pid-features/{session_id}/summary` - P&ID 분석 요약

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| PID-046 | 요약 조회 | 모든 분석 완료 | 통합 요약 | P1 |

---

## 6. 분석 API (Analysis Package)

### 6.1 치수 API (6개)

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| ANA-001 | 치수 추출 | POST extract | eDOCr2로 치수 추출 | P0 |
| ANA-002 | 치수 목록 조회 | GET | 모든 치수 | P0 |
| ANA-003 | 치수 업데이트 | PUT | 값/상태 변경 | P1 |
| ANA-004 | 치수 삭제 | DELETE | 제거 | P2 |
| ANA-005 | 일괄 검증 | PUT bulk-verify | 여러 치수 검증 | P1 |
| ANA-006 | 일괄 가져오기 | POST import-bulk | 외부 데이터 가져오기 | P2 |

### 6.2 선 & 연결성 API (4개)

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| ANA-007 | 선 검출 | POST | 선 목록, 교점 | P1 |
| ANA-008 | 선 조회 | GET | 검출된 선 | P1 |
| ANA-009 | 치수-심볼 링크 생성 | POST | 관계 생성 | P1 |
| ANA-010 | 링크 조회 | GET | 관계 목록 | P1 |

### 6.3 영역 API (3개)

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| ANA-011 | 영역 검출 | POST | 영역 분할 | P2 |
| ANA-012 | 영역 조회 | GET | 영역 목록 | P2 |
| ANA-013 | 영역 세분화 | POST refine | 세분화된 영역 | P2 |

### 6.4 GD&T API (2개)

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| ANA-014 | GD&T 파싱 | POST parse | FCF, 데이텀 | P2 |
| ANA-015 | GD&T 조회 | GET | 파싱 결과 | P2 |

---

## 7. 검증 API (Active Learning) (6개)

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| VER-001 | 검증 큐 조회 | GET queue | 우선순위별 정렬 | P0 |
| VER-002 | 검증 통계 | GET stats | critical, high, medium, low 집계 | P1 |
| VER-003 | 일괄 승인 | POST approve-all | 임계값 이상 자동 승인 | P1 |
| VER-004 | 항목 검증 | POST verify | 개별 검증 | P0 |
| VER-005 | 학습 데이터 조회 | GET training-data | YOLO 재학습용 | P2 |
| VER-006 | 임계값 업데이트 | PUT thresholds | 우선순위 임계값 변경 | P2 |

---

## 8. 분류 API (VLM) (2개)

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| CLS-001 | 도면 분류 | POST classify | 도면 타입, 신뢰도 | P1 |
| CLS-002 | 프로바이더 목록 | GET providers | local, openai, anthropic | P2 |

---

## 9. 설정 API (5개)

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| SET-001 | API 키 조회 | GET api-keys | 마스킹된 키, 프로바이더 | P2 |
| SET-002 | API 키 설정 | POST api-keys/{provider} | 키 저장 | P2 |
| SET-003 | API 키 삭제 | DELETE api-keys/{provider} | 키 삭제 | P2 |
| SET-004 | 연결 테스트 | POST test-connection | 연결 성공/실패 | P2 |
| SET-005 | 모델 목록 | GET providers/{provider}/models | 사용 가능 모델 | P2 |

---

## 10. 피드백 루프 API (5개)

| ID | 시나리오 | 입력 | 기대 결과 | 우선순위 |
|----|----------|------|----------|----------|
| FDB-001 | 피드백 통계 | GET stats | 승인/거부/수정 수, 정확도 | P2 |
| FDB-002 | 검증 완료 세션 | GET sessions | 재학습 가능 세션 | P2 |
| FDB-003 | YOLO 데이터셋 내보내기 | POST export | YOLO 형식 파일 | P2 |
| FDB-004 | 내보내기 목록 | GET exports | 내보낸 파일 목록 | P3 |
| FDB-005 | 시스템 상태 | GET health | 데이터 품질 점수 | P3 |

---

## 부록: 에러 코드 테스트

| 상태 코드 | 시나리오 | 테스트 방법 |
|-----------|----------|-------------|
| 400 | 잘못된 요청 | 필수 파라미터 누락, 잘못된 형식 |
| 404 | 리소스 없음 | 존재하지 않는 session_id |
| 422 | 검증 실패 | 범위 초과 파라미터 |
| 500 | 서버 오류 | 내부 처리 오류 유발 |
| 503 | 외부 서비스 오류 | 외부 API 중단 |
