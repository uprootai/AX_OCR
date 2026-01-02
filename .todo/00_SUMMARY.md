# 변경사항 요약 및 향후 작업 목록

> 마지막 커밋 대비 변경사항 분석 (2026-01-02)
> 총 23개 파일 수정, 5개 신규 디렉토리

---

## 핵심 변경사항

### 1. PID Composer API 신규 생성 (포트 5021)
- 별도 마이크로서비스로 레이어 합성 기능 분리
- Gateway의 pid_overlay 코드 제거 및 독립 서비스로 이전

### 2. Web-UI 통합
- apiRegistry.ts: 20번째 API 추가
- constants.ts: Dashboard 모니터링 목록 추가
- analysisNodes.ts: BlueprintFlow 노드 정의 추가

### 3. YOLO 모델 레지스트리 업데이트
- pid_symbol: 60종 → 32종으로 클래스 수정
- pid_class_aware: 32종 클래스명 상세 추가

### 4. Blueprint AI BOM 검출 서비스 개선
- MODEL_CONFIGS: 5개 모델 타입별 기본 설정 추가
- SAHI 자동 활성화 로직 추가

### 5. eDOCr2 파라미터 정리
- ocrNodes.ts: version 파라미터 제거 (v1/v2/ensemble → v2 단일화)

---

## 향후 작업 목록 (TODO 파일)

| 파일 | 설명 | 우선순위 |
|------|------|----------|
| `01_NEW_API_CHECKLIST.md` | 새 API 추가 시 체크리스트 | P0 |
| `02_VISUALIZATION_EXTENSION.md` | 다른 노드에 시각화 기능 확장 | P1 |
| `03_MODEL_CONFIG_PATTERN.md` | 모델 설정 패턴 다른 서비스에 적용 | P1 |
| `04_GATEWAY_SERVICE_SEPARATION.md` | Gateway 서비스 분리 후보 | P2 |
| `05_CLEANUP_TASKS.md` | 기존 코드 정리 작업 | P2 |
| `06_TEST_COVERAGE.md` | 테스트 커버리지 확대 | P2 |

---

## 영향받는 파일 (23개)

### 수정된 파일
```
CLAUDE.md                                    # API 문서 업데이트
blueprint-ai-bom/backend/routers/session_router.py
blueprint-ai-bom/backend/schemas/detection.py
blueprint-ai-bom/backend/services/detection_service.py  # MODEL_CONFIGS 추가
docker-compose.yml                           # pid-composer-api 추가
gateway-api/api_server.py                    # pid_overlay 제거
gateway-api/api_specs/edocr2.yaml
gateway-api/docker-compose.yml
gateway-api/routers/__init__.py              # pid_overlay 제거
gateway-api/services/__init__.py             # pid_overlay 제거
gateway-api/services/ocr_service.py
models/design-checker-api/Dockerfile
models/design-checker-api/config/_active.yaml
models/design-checker-api/routers/checklist_router.py
models/yolo-api/models/model_registry.yaml   # 클래스명 상세화
models/yolo-api/routers/detection_router.py
web-ui/src/App.tsx                           # 라우팅 추가
web-ui/src/components/monitoring/constants.ts # Dashboard 목록 추가
web-ui/src/config/apiRegistry.ts             # API 레지스트리 추가
web-ui/src/config/nodes/analysisNodes.ts     # 노드 정의 추가
web-ui/src/config/nodes/ocrNodes.ts          # version 파라미터 제거
web-ui/src/store/monitoringStore.ts
web-ui/src/store/workflowStore.ts
```

### 신규 생성 (Untracked)
```
models/pid-composer-api/                     # 신규 마이크로서비스
gateway-api/api_specs/pid-composer.yaml      # API 스펙
web-ui/src/components/pid/                   # PID 컴포넌트
web-ui/src/pages/pid-overlay/                # PID 오버레이 페이지
models/design-checker-api/config/common/     # 공통 설정
```

---

## 패턴 분석

### 새 API 추가 시 필수 체크리스트 (6단계)
1. `models/{api-id}-api/` - 마이크로서비스 생성
2. `gateway-api/api_specs/{api-id}.yaml` - API 스펙
3. `docker-compose.yml` - 서비스 등록
4. `web-ui/src/config/apiRegistry.ts` - API 레지스트리
5. `web-ui/src/components/monitoring/constants.ts` - Dashboard 목록
6. `web-ui/src/config/nodes/{category}Nodes.ts` - 노드 정의

### 서비스 분리 패턴
- Gateway 내부 서비스 → 별도 마이크로서비스
- pid_overlay → pid-composer-api로 분리 완료
- 다른 후보: vl_service, tolerance_service

### 모델 설정 패턴 (MODEL_CONFIGS)
- 모델별 기본 파라미터 중앙화
- confidence, iou, imgsz, use_sahi 등
- 다른 서비스에도 적용 권장
