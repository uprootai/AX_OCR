# 코드베이스 정리 분석 보고서

> **작성일**: 2025-12-18
> **목적**: LLM 이해도 향상 및 불필요한 파일 정리
> **분석 범위**: 전체 프로젝트 (`/home/uproot/ax/poc`)

---

## 1. 레거시/불필요 파일 상세 분석

### 1.1 `blueprint-ai-bom/legacy/` (권장: 삭제)

| 항목 | 내용 |
|------|------|
| **위치** | `blueprint-ai-bom/legacy/` |
| **크기** | ~540KB (코드) |
| **파일 수** | 4개 Python 앱 + utils 폴더 |

#### 왜 레거시인가?

```
현재 상태:
├── blueprint-ai-bom/
│   ├── backend/          ← 새 FastAPI 구현 (현재 사용)
│   ├── frontend/         ← 새 React 구현 (현재 사용)
│   └── legacy/           ← 옛 Streamlit 앱 (사용 안 함)
```

**legacy/README.md에 명시된 내용**:
> "이 폴더는 기존 Streamlit 기반 구현을 보존합니다.
> 새 React + FastAPI 구현이 완료된 후 삭제될 예정입니다."

#### 파일별 상세

| 파일 | 줄 수 | 설명 | 마이그레이션 상태 |
|------|-------|------|------------------|
| `real_ai_app.py` | 2,681줄 | 메인 Streamlit 앱 | ✅ backend/로 마이그레이션 완료 |
| `real_ai_app_complete.py` | 3,200줄 | 전체 기능 버전 | ✅ 마이그레이션 완료 |
| `real_ai_app_error.py` | 2,770줄 | 에러 핸들링 버전 | ✅ 마이그레이션 완료 |
| `real_ai_app_backup_*.py` | 2,612줄 | 백업 파일 | 불필요 |
| `utils/` | ~1,000줄 | 유틸리티 모듈 | ✅ backend/services/로 이동 |

#### 결론

- **마이그레이션 완료 확인됨** (README.md의 체크리스트)
- 참조용 코드는 이미 새 구현에 반영됨
- **삭제 권장** (단, 최종 확인 후)

---

### 1.2 `scripts/tests/archive/` (권장: 삭제)

| 항목 | 내용 |
|------|------|
| **위치** | `scripts/tests/archive/` |
| **크기** | ~60KB |
| **파일 수** | 22개 |

#### 왜 아카이브인가?

이 폴더의 테스트들은 2025년 11월 13~19일에 작성된 **일회성 수동 테스트**입니다.

| 파일 예시 | 내용 | 왜 불필요한가 |
|----------|------|--------------|
| `test_full_pipeline.py` | 전체 파이프라인 수동 테스트 | 현재 `gateway-api/tests/`에 자동화된 버전 존재 |
| `test_file_upload.py` | 파일 업로드 테스트 | 단순 스크립트, 테스트 프레임워크 미사용 |
| `test_yolo_api_direct.py` | YOLO API 직접 호출 | `pytest` 기반 테스트로 대체됨 |
| `test_sample_*.py` | 샘플 이미지 테스트들 | 하드코딩된 경로, 재사용 불가 |

#### 현재 테스트 체계

```
실제 사용 중인 테스트:
├── gateway-api/tests/           ← pytest 기반 (사용 중)
│   ├── test_executor_registry.py
│   ├── test_dag_validator.py
│   └── ...
├── web-ui/src/**/*.test.ts      ← vitest 기반 (사용 중)
└── scripts/tests/               ← 활성 테스트
    ├── test_workflow.json
    └── test_full_pipeline.py
```

#### 결론

- **일회성 디버깅 스크립트**로, 현재 테스트 프레임워크와 무관
- 재사용 불가능한 하드코딩된 경로들
- **삭제 권장**

---

### 1.3 `models/edgnet-api/models/` 중간 체크포인트 (권장: 삭제)

| 항목 | 내용 |
|------|------|
| **위치** | `models/edgnet-api/models/` |
| **크기** | **1.78GB** (5개 파일) |

#### 파일 목록

```
edgnet_large.pth              ← 최종 모델 (356MB) - 유지
edgnet_large_epoch_10.pth     ← 중간 체크포인트 - 삭제 가능
edgnet_large_epoch_20.pth     ← 중간 체크포인트 - 삭제 가능
edgnet_large_epoch_30.pth     ← 중간 체크포인트 - 삭제 가능
edgnet_large_epoch_40.pth     ← 중간 체크포인트 - 삭제 가능
edgnet_large_epoch_50.pth     ← 중간 체크포인트 - 삭제 가능
edgnet_simple.pth             ← 경량 모델 (25KB) - 유지
```

#### 왜 삭제 가능한가?

- 학습 중간 저장된 체크포인트
- `edgnet_large.pth`가 최종 학습 결과
- 재학습이 필요하면 다시 생성 가능
- **프로덕션에서는 최종 모델만 필요**

#### 결론

- **1.78GB 절약 가능**
- 삭제 명령: `rm models/edgnet-api/models/edgnet_large_epoch_*.pth`

---

### 1.4 `models/edocr2-api/` vs `models/edocr2-v2-api/` (분석 필요)

| 항목 | edocr2-api | edocr2-v2-api |
|------|------------|---------------|
| **크기** | 158MB | 355MB |
| **Docker 사용** | ❌ 없음 | ✅ 사용 중 |
| **포트** | 5001 (미사용) | 5002 (활성) |

#### docker-compose.yml 확인 결과

```yaml
# 실제 사용 중인 서비스
edocr2-v2-api:
  build:
    context: ./models/edocr2-v2-api
  ports:
    - "5002:5002"

# edocr2-api (5001)는 정의되어 있지 않음!
```

#### 중복 파일 확인

| 파일 | edocr2-api | edocr2-v2-api | 동일? |
|------|------------|---------------|-------|
| `api_server_edocr_v1.py` | 1,049줄 | 1,049줄 | ✅ 동일 |
| `api_server_edocr_v2.py` | 688줄 | 688줄 | ✅ 동일 |
| `README.md` | 동일 | 동일 | ✅ 동일 |

#### 결론

- `edocr2-api/`는 **사용되지 않는 구버전**
- `edocr2-v2-api/`만 Docker에서 실행됨
- **추가 확인 후 edocr2-api/ 삭제 고려** (150MB 절약)

---

## 2. 문서 중복 분석

### 2.1 중복된 문서 위치

```
중복 구조:
docs/                           ← 원본 (68개 문서)
├── ADMIN_MANUAL.md
├── papers/
└── ...

web-ui/public/docs/             ← 복사본 (65개 문서)
├── ADMIN_MANUAL.md             ← docs/와 동일
└── ...

web-ui/dist/docs/               ← 빌드 결과물 (65개 문서)
├── ADMIN_MANUAL.md             ← 빌드 시 복사됨
└── ...
```

### 2.2 중복 문서 목록 (상위 10개)

| 문서명 | 원본 위치 | 중복 위치 |
|--------|----------|----------|
| `ADMIN_MANUAL.md` | docs/ | web-ui/public/docs/, web-ui/dist/docs/ |
| `DYNAMIC_API_SYSTEM_GUIDE.md` | docs/ | web-ui/public/docs/, web-ui/dist/docs/ |
| `INSTALLATION_GUIDE.md` | docs/ | web-ui/public/docs/, web-ui/dist/docs/ |
| `TROUBLESHOOTING.md` | docs/ | web-ui/public/docs/, web-ui/dist/docs/ |
| `papers/*.md` (15개) | docs/papers/ | web-ui/public/docs/papers/ |
| `dockerization/*.md` (3개) | docs/dockerization/ | web-ui/public/docs/dockerization/ |

### 2.3 권장 해결책

**Option A: 심볼릭 링크 (권장)**
```bash
# web-ui/public/docs를 심볼릭 링크로 대체
rm -rf web-ui/public/docs
ln -s ../../docs web-ui/public/docs
```

**Option B: 빌드 스크립트에서 복사**
```javascript
// vite.config.ts에서 빌드 시 docs/ 복사
```

---

## 3. 대용량 코드 파일 분석

### 3.1 500줄 이상 파일 (LLM 이해도 저하 위험)

| 파일 | 줄 수 | 문제점 | 권장 조치 |
|------|-------|--------|----------|
| `gateway-api/api_server.py` | 2,569 | 50+ 함수가 단일 파일 | 라우터 분리 |
| `nodeDefinitions.ts` | 1,934 | 정적 데이터 집합 | YAML/JSON 분리 |
| `BlueprintFlowBuilder.tsx` | 1,706 | 모놀리식 컴포넌트 | 하위 컴포넌트 분리 |
| `Guide.tsx` | 1,236 | 대형 컴포넌트 | 섹션별 분리 |
| `APIStatusMonitor.tsx` | 914 | 복잡한 모니터링 UI | 훅/컴포넌트 분리 |

### 3.2 `api_server.py` 상세 분석

현재 구조:
```python
# api_server.py (2,569줄)
# ├── imports (1-50줄)
# ├── FastAPI 설정 (50-120줄)
# ├── 유틸리티 함수 (120-800줄) ← utils/에 이미 있는 함수 중복
# ├── /process 엔드포인트 (800-1700줄) ← 900줄 단일 함수!
# ├── /workflow/* 엔드포인트 (1700-2100줄)
# ├── /api/v1/specs/* 엔드포인트 (2100-2569줄)
```

권장 리팩토링:
```
gateway-api/
├── api_server.py              ← 100줄 (앱 설정만)
├── routers/
│   ├── process_router.py      ← /process 엔드포인트
│   ├── workflow_router.py     ← /workflow/* 엔드포인트
│   ├── spec_router.py         ← /api/v1/specs/*
│   ├── admin_router.py        ← 이미 분리됨 ✅
│   └── container_router.py    ← 이미 분리됨 ✅
```

---

## 4. 기타 정리 대상

### 4.1 결과 파일 (정기 정리 필요)

| 위치 | 크기 | 내용 |
|------|------|------|
| `gateway-api/results/` | 192MB | 워크플로우 실행 결과 |
| `models/yolo-api/results/` | 174MB | YOLO 추론 결과 |
| `test-results/` | 22MB | 테스트 실행 결과 |

### 4.2 백업/Deprecated 파일

| 파일 | 권장 |
|------|------|
| `gateway-api/api_specs/yolo-pid.yaml.deprecated` | 삭제 |
| `models/yolo-pid-api/api_server.py.backup` | 삭제 |

### 4.3 캐시 파일

- `__pycache__/` 폴더들: 118개 파일 (자동 생성, 무시 가능)

---

## 5. 조치 우선순위

### 즉시 조치 (안전)

```bash
# 1. EDGNet 중간 체크포인트 삭제 (1.78GB)
rm /home/uproot/ax/poc/models/edgnet-api/models/edgnet_large_epoch_*.pth

# 2. deprecated/backup 파일 삭제
rm /home/uproot/ax/poc/gateway-api/api_specs/yolo-pid.yaml.deprecated
rm /home/uproot/ax/poc/models/yolo-pid-api/api_server.py.backup

# 3. 테스트 아카이브 삭제
rm -rf /home/uproot/ax/poc/scripts/tests/archive/
```

### 확인 후 조치

| 항목 | 확인 사항 | 예상 절약 |
|------|----------|----------|
| `legacy/` 폴더 | 마이그레이션 완료 최종 확인 | 540KB |
| `edocr2-api/` 폴더 | v2만 사용 확인 | 158MB |
| 결과 파일들 | 백업 필요 여부 확인 | 388MB |

### 중기 리팩토링

| 작업 | 우선순위 | 예상 효과 |
|------|----------|----------|
| `api_server.py` 라우터 분리 | 높음 | LLM 이해도 50% 향상 |
| `nodeDefinitions.ts` 데이터 분리 | 중간 | 유지보수성 향상 |
| 문서 중복 제거 | 낮음 | 혼란 방지 |

---

## 6. 결론

### 절약 가능한 디스크 공간

| 항목 | 크기 |
|------|------|
| EDGNet 체크포인트 | 1.78GB |
| edocr2-api (확인 후) | 158MB |
| 결과 파일 (선택적) | 388MB |
| 레거시/아카이브 | ~1MB |
| **총계** | **~2.3GB** |

### LLM 이해도 개선 효과

- 현재: 2,500줄+ 파일 5개
- 목표: 500줄 이하로 분리
- 효과: 코드 리뷰/수정 시 컨텍스트 절약, 정확도 향상

---

## 부록: 삭제 스크립트

```bash
#!/bin/bash
# cleanup.sh - 안전한 정리 작업

# 1. 안전한 삭제 (즉시 실행 가능)
echo "=== 안전한 정리 시작 ==="
rm -v models/edgnet-api/models/edgnet_large_epoch_*.pth
rm -v gateway-api/api_specs/yolo-pid.yaml.deprecated
rm -v models/yolo-pid-api/api_server.py.backup
rm -rf scripts/tests/archive/
echo "=== 완료: ~1.78GB 절약 ==="

# 2. 확인 필요한 삭제 (주석 해제 전 확인)
# rm -rf blueprint-ai-bom/legacy/
# rm -rf models/edocr2-api/
```
