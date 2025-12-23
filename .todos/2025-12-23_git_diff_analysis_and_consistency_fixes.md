# Git Diff 분석 및 일관성 수정 작업

**작성일**: 2025-12-23
**분석 대상**: 마지막 커밋 대비 변경 사항 (54개 파일, +3432/-676 라인)
**목적**: 부분적으로 적용된 패턴을 다른 노드에도 일관성 있게 적용

---

## 📊 변경 사항 요약

### 주요 변경 카테고리

| 카테고리 | 파일 수 | 핵심 변경 |
|----------|---------|----------|
| Claude Skills/Commands | 4+2 | feature-implementer 추가, 리스크 평가 시스템 |
| BlueprintFlow Executors | 3 | drawing_type 패스스루, 이미지 패스스루 |
| API Specs | 16 | healthEndpoint 경로 변경 (/health → /api/v1/health) |
| Container Router | 1 | Docker SDK 블로킹 호출 → ThreadPoolExecutor |
| Blueprint AI BOM | 15+ | 도면 분류, 관계 분석, 검증 기능 추가 |
| Web UI | 12 | 도면 타입 추천, 노드 UI 개선 |

---

## 🔴 Critical: drawing_type 패스스루 누락

### 문제 설명
`ImageInput` 노드에서 `drawing_type` 파라미터를 출력하도록 변경됨.
`eDOCr2` 노드에만 패스스루 로직이 추가됨.
**다른 모든 executor들에 동일한 패스스루 로직이 누락됨.**

### 영향
워크플로우: `ImageInput → YOLO → BOM`
- YOLO에서 drawing_type이 누락되어 BOM에 전달되지 않음
- BOM 세션에 drawing_type이 "auto"로 저장됨 (의도와 다름)

### 수정 필요 파일 (15개) - ✅ 모두 완료됨

#### 필수 수정 (BOM 파이프라인에 포함되는 노드)
```
- [x] gateway-api/blueprintflow/executors/yolo_executor.py ✅
- [x] gateway-api/blueprintflow/executors/yolopid_executor.py ✅
- [x] gateway-api/blueprintflow/executors/paddleocr_executor.py ✅
- [x] gateway-api/blueprintflow/executors/skinmodel_executor.py ✅
```

#### 권장 수정 (일관성을 위해)
```
- [x] gateway-api/blueprintflow/executors/tesseract_executor.py ✅
- [x] gateway-api/blueprintflow/executors/trocr_executor.py ✅
- [x] gateway-api/blueprintflow/executors/doctr_executor.py ✅
- [x] gateway-api/blueprintflow/executors/easyocr_executor.py ✅
- [x] gateway-api/blueprintflow/executors/suryaocr_executor.py ✅
- [x] gateway-api/blueprintflow/executors/ocr_ensemble_executor.py ✅
- [x] gateway-api/blueprintflow/executors/esrgan_executor.py ✅
- [x] gateway-api/blueprintflow/executors/edgnet_executor.py ✅
- [x] gateway-api/blueprintflow/executors/vl_executor.py ✅
- [x] gateway-api/blueprintflow/executors/linedetector_executor.py ✅
- [x] gateway-api/blueprintflow/executors/pidanalyzer_executor.py ✅
- [x] gateway-api/blueprintflow/executors/designchecker_executor.py ✅
```

### 수정 패턴 (복사하여 사용)
```python
# execute() 함수의 return 직전에 추가:

# 원본 이미지 패스스루 (후속 노드에서 필요)
if inputs.get("image"):
    output["image"] = inputs["image"]

# drawing_type 패스스루 (BOM 세션 생성에 필요)
if inputs.get("drawing_type"):
    output["drawing_type"] = inputs["drawing_type"]

return output
```

---

## 🟠 High: image 패스스루 누락

### 문제 설명
일부 노드만 원본 이미지를 패스스루함.
BOM 노드는 원본 이미지가 필요함 (검증 UI 표시용).

### 현재 상태

| Executor | image 패스스루 | drawing_type 패스스루 |
|----------|---------------|---------------------|
| imageinput | 출력 ✅ | 출력 ✅ |
| yolo | ✅ | ❌ |
| yolopid | ❌ | ❌ |
| edocr2 | ✅ | ✅ |
| paddleocr | ❌ | ❌ |
| skinmodel | ❌ | ❌ |
| vl | ❌ | ❌ |
| 기타 OCR | ❌ | ❌ |

### 수정 우선순위
1. **yolo_executor.py** - drawing_type 추가 (image는 이미 있음)
2. **yolopid_executor.py** - 둘 다 추가
3. **paddleocr_executor.py** - 둘 다 추가
4. **skinmodel_executor.py** - 둘 다 추가

---

## 🟡 Medium: healthEndpoint 일관성 확인

### 변경 내용
모든 API Specs에서 healthEndpoint가 변경됨:
- `/health` → `/api/v1/health` (대부분)
- `/health` → `/api/v2/health` (edocr2)

### 확인 필요 사항
```bash
# 각 API 서버의 실제 health 엔드포인트 확인
- [ ] curl http://localhost:5002/api/v2/health  # edocr2
- [ ] curl http://localhost:5005/api/v1/health  # yolo
- [ ] curl http://localhost:5006/api/v1/health  # paddleocr
- [ ] curl http://localhost:5008/api/v1/health  # tesseract
- [ ] curl http://localhost:5012/api/v1/health  # edgnet
- [ ] curl http://localhost:5013/api/v1/health  # suryaocr
- [ ] curl http://localhost:5014/api/v1/health  # doctr
- [ ] curl http://localhost:5015/api/v1/health  # easyocr
- [ ] curl http://localhost:5016/api/v1/health  # line-detector
- [ ] curl http://localhost:5017/api/v1/health  # yolo-pid
- [ ] curl http://localhost:5018/api/v1/health  # pid-analyzer
- [ ] curl http://localhost:5019/api/v1/health  # design-checker
```

### 불일치 발견 시
해당 API 서버의 api_server.py에서 health 엔드포인트 확인 후:
- api_specs 수정 또는
- API 서버 수정

---

## 🟡 Medium: Container Router ThreadPoolExecutor 패턴

### 변경 내용
Docker SDK의 블로킹 호출을 async로 변환:
- `_get_container_status_sync()` - 동기 함수로 분리
- `asyncio.run_in_executor()` - ThreadPool에서 실행
- `asyncio.wait_for()` - 타임아웃 적용

### 확인 필요 사항
```
- [ ] Dashboard에서 컨테이너 상태 조회 정상 동작 확인
- [ ] Stop/Start/Restart 버튼 정상 동작 확인
- [ ] 타임아웃 시 에러 메시지 표시 확인
```

---

## 🟢 Low: Blueprint AI BOM 새 기능 통합

### 추가된 라우터 (통합 확인 필요)
```
- [ ] blueprint-ai-bom/backend/routers/analysis_router.py
- [ ] blueprint-ai-bom/backend/routers/classification_router.py
- [ ] blueprint-ai-bom/backend/routers/relation_router.py
- [ ] blueprint-ai-bom/backend/routers/verification_router.py
```

### 추가된 서비스
```
- [ ] blueprint-ai-bom/backend/services/vlm_classifier.py
- [ ] blueprint-ai-bom/backend/services/dimension_service.py
- [ ] blueprint-ai-bom/backend/services/dimension_relation_service.py
- [ ] blueprint-ai-bom/backend/services/line_detector_service.py
- [ ] blueprint-ai-bom/backend/services/active_learning_service.py
```

### 추가된 스키마
```
- [ ] blueprint-ai-bom/backend/schemas/classification.py
- [ ] blueprint-ai-bom/backend/schemas/dimension.py
- [ ] blueprint-ai-bom/backend/schemas/line.py
- [ ] blueprint-ai-bom/backend/schemas/relation.py
- [ ] blueprint-ai-bom/backend/schemas/analysis_options.py
```

### 추가된 프론트엔드 컴포넌트
```
- [ ] blueprint-ai-bom/frontend/src/components/AnalysisOptions.tsx
- [ ] blueprint-ai-bom/frontend/src/components/DimensionList.tsx
- [ ] blueprint-ai-bom/frontend/src/components/DrawingClassifier.tsx
- [ ] blueprint-ai-bom/frontend/src/components/IntegratedOverlay.tsx
- [ ] blueprint-ai-bom/frontend/src/components/LineOverlay.tsx
- [ ] blueprint-ai-bom/frontend/src/components/RelationList.tsx
- [ ] blueprint-ai-bom/frontend/src/components/RelationOverlay.tsx
- [ ] blueprint-ai-bom/frontend/src/components/VerificationQueue.tsx
- [ ] blueprint-ai-bom/frontend/src/components/Tooltip.tsx
```

### 통합 테스트 시나리오
```
1. [ ] WorkflowPage에서 새 컴포넌트들이 정상 렌더링되는지 확인
2. [ ] drawing_type별로 다른 UI가 표시되는지 확인
3. [ ] 도면 분류 기능 동작 확인 (VLM 사용 시)
4. [ ] 치수-부품 관계 분석 기능 확인
5. [ ] 검증 큐 기능 확인
```

---

## 📋 작업 순서 (권장)

### Phase 1: Critical 수정 (즉시)
1. `yolo_executor.py`에 drawing_type 패스스루 추가
2. `yolopid_executor.py`에 image, drawing_type 패스스루 추가
3. 워크플로우 테스트: ImageInput → YOLO → BOM

### Phase 2: 일관성 수정
4. 나머지 executor들에 패스스루 추가 (15개)
5. healthEndpoint 실제 값 확인 및 수정

### Phase 3: 통합 테스트
6. Blueprint AI BOM 새 기능 테스트
7. Container Router 기능 테스트
8. 전체 워크플로우 E2E 테스트

---

## 🔧 빠른 수정 스크립트

### yolo_executor.py 수정
```python
# gateway-api/blueprintflow/executors/yolo_executor.py
# return 직전에 추가:

# drawing_type 패스스루 (BOM 세션 생성에 필요)
if inputs.get("drawing_type"):
    output["drawing_type"] = inputs["drawing_type"]
```

### 일괄 확인 명령어
```bash
# 모든 executor의 패스스루 상태 확인
for f in gateway-api/blueprintflow/executors/*_executor.py; do
  echo "=== $(basename $f) ==="
  grep -c "drawing_type" "$f" || echo "0"
done
```

---

## 📝 변경 로그 템플릿

### 커밋 메시지 (수정 완료 후)
```
fix: Add drawing_type passthrough to all executors

- Add drawing_type passthrough to yolo, yolopid, paddleocr executors
- Add image passthrough where missing
- Ensure BOM receives drawing_type from ImageInput through any pipeline

Affected executors:
- yolo_executor.py
- yolopid_executor.py
- paddleocr_executor.py
- [기타 수정된 파일들]

Fixes: drawing_type not reaching BOM when going through YOLO node
```

---

**작성자**: Claude Code
**상태**: ✅ Phase 1 & Phase 2 완료 (2025-12-23)

---

## ✅ 완료된 작업 (2025-12-23)

### Phase 1 완료: Critical 수정
- ✅ `yolo_executor.py` - drawing_type 패스스루 추가
- ✅ `yolopid_executor.py` - image + drawing_type 패스스루 추가
- ✅ `paddleocr_executor.py` - image + drawing_type 패스스루 추가
- ✅ `skinmodel_executor.py` - image + drawing_type 패스스루 추가

### Phase 2 완료: 일관성 수정
모든 나머지 executor에 image + drawing_type 패스스루 추가 완료:
- tesseract, trocr, doctr, easyocr, suryaocr, ocr_ensemble
- esrgan, edgnet, vl, linedetector, pidanalyzer, designchecker

**총 수정 파일: 16개 executor**

### 남은 작업 (Phase 3)

---

## 📋 앞으로 해야 할 작업 (상세)

### 1. healthEndpoint 일관성 검증 (Medium Priority)

**목적**: API Spec에 정의된 healthEndpoint가 실제 API 서버에 존재하는지 확인

**작업 단계**:
```bash
# Step 1: 각 API 서버 health 엔드포인트 테스트
curl http://localhost:5002/api/v2/health  # edocr2
curl http://localhost:5005/api/v1/health  # yolo
curl http://localhost:5006/api/v1/health  # paddleocr
curl http://localhost:5008/api/v1/health  # tesseract
curl http://localhost:5012/api/v1/health  # edgnet
curl http://localhost:5013/api/v1/health  # suryaocr
curl http://localhost:5014/api/v1/health  # doctr
curl http://localhost:5015/api/v1/health  # easyocr
curl http://localhost:5016/api/v1/health  # line-detector
curl http://localhost:5017/api/v1/health  # yolo-pid
curl http://localhost:5018/api/v1/health  # pid-analyzer
curl http://localhost:5019/api/v1/health  # design-checker

# Step 2: 실패하는 항목 기록

# Step 3: 불일치 시 수정
# Option A: api_specs/*.yaml의 healthEndpoint 수정
# Option B: models/*-api/api_server.py에 엔드포인트 추가
```

**수정 파일 (불일치 시)**:
- `gateway-api/api_specs/{api-id}.yaml` - healthEndpoint 필드
- `models/{api-id}-api/api_server.py` - @app.get("/api/v1/health") 추가

---

### 2. Container Router 기능 테스트 (Medium Priority)

**목적**: Docker SDK 비동기화가 정상 동작하는지 확인

**테스트 시나리오**:
```
[ ] 1. Dashboard 접속 → API Status 페이지 로드
    - 예상: 모든 컨테이너 상태 표시 (2-3초 내)
    - 확인: 페이지가 멈추지 않고 로드되는지

[ ] 2. 컨테이너 Stop 버튼 클릭
    - 예상: 컨테이너 중지, UI 상태 업데이트
    - 확인: API 응답 시간 < 10초

[ ] 3. 컨테이너 Start 버튼 클릭
    - 예상: 컨테이너 시작, Health 체크 후 상태 업데이트
    - 확인: API 응답 시간 < 30초

[ ] 4. 컨테이너 Restart 버튼 클릭
    - 예상: 컨테이너 재시작 완료
    - 확인: 에러 없이 완료

[ ] 5. 타임아웃 테스트
    - 방법: 존재하지 않는 컨테이너 이름으로 요청
    - 예상: 10초 타임아웃 후 에러 메시지 표시
```

**관련 파일**:
- `gateway-api/routers/container_router.py` - 수정된 코드
- `web-ui/src/pages/admin/APIDetail.tsx` - 프론트엔드 UI

---

### 3. Blueprint AI BOM 새 기능 통합 테스트 (High Priority)

**목적**: 새로 추가된 기능들이 정상 동작하는지 확인

#### 3.1 도면 분류 기능 테스트
```
[ ] VLM 분류기 API 테스트
    - POST /api/v1/classify
    - 입력: 도면 이미지
    - 예상 출력: { drawing_type: "mechanical" | "pid" | ... }

[ ] 프론트엔드 DrawingClassifier 컴포넌트
    - 이미지 업로드 시 자동 분류 트리거
    - 분류 결과 UI 표시
    - 사용자가 수정 가능
```

#### 3.2 치수-부품 관계 분석 테스트
```
[ ] 관계 분석 API 테스트
    - POST /api/v1/relations/analyze
    - 입력: OCR 결과 + 검출 결과
    - 예상 출력: 치수와 부품 간 매핑

[ ] RelationOverlay 컴포넌트
    - 도면 위에 관계선 표시
    - 클릭 시 상세 정보 표시

[ ] RelationList 컴포넌트
    - 관계 목록 테이블 표시
    - 정렬/필터 기능
```

#### 3.3 검증 큐 기능 테스트
```
[ ] 검증 큐 API 테스트
    - GET /api/v1/verification/queue
    - POST /api/v1/verification/approve/{id}
    - POST /api/v1/verification/reject/{id}

[ ] VerificationQueue 컴포넌트
    - 대기 중인 항목 목록 표시
    - 승인/거부 버튼 동작
    - 실시간 업데이트 (WebSocket 또는 폴링)
```

#### 3.4 통합 워크플로우 테스트
```
[ ] 전체 파이프라인 테스트
    1. ImageInput에서 도면 업로드
    2. drawing_type 자동 분류 확인
    3. YOLO → eDOCr2 → BOM 파이프라인 실행
    4. BOM 결과에서 치수-부품 관계 확인
    5. 검증 큐에서 결과 승인
```

**관련 파일**:
- 백엔드: `blueprint-ai-bom/backend/routers/*.py`
- 프론트엔드: `blueprint-ai-bom/frontend/src/components/*.tsx`

---

### 4. 프론트엔드 빌드 검증 (Low Priority)

**목적**: 새로 추가된 컴포넌트들이 빌드 에러 없이 동작하는지 확인

```bash
# Step 1: 린트 검사
cd web-ui && npm run lint
cd blueprint-ai-bom/frontend && npm run lint

# Step 2: 타입 체크 및 빌드
cd web-ui && npm run build
cd blueprint-ai-bom/frontend && npm run build

# Step 3: 테스트 실행
cd web-ui && npm run test:run
```

**체크리스트**:
```
[ ] ESLint 에러 0개
[ ] TypeScript 빌드 성공
[ ] 테스트 전체 통과
```

---

### 5. E2E 워크플로우 테스트 (Final)

**전체 시나리오**:
```
[ ] 시나리오 1: 기계도면 BOM 생성
    ImageInput (mechanical) → YOLO → eDOCr2 → BOM
    - drawing_type이 "mechanical"로 BOM에 전달되는지 확인

[ ] 시나리오 2: P&ID 분석
    ImageInput (pid) → YOLO-PID → Line Detector → PID Analyzer → Design Checker
    - drawing_type이 끝까지 전달되는지 확인

[ ] 시나리오 3: VL 기반 분석
    ImageInput → VL (분류) → YOLO → OCR → BOM
    - VL 결과가 다음 노드로 전달되는지 확인

[ ] 시나리오 4: 전처리 포함 파이프라인
    ImageInput → ESRGAN (업스케일) → YOLO → OCR → BOM
    - 업스케일된 이미지로 분석 정상 동작

[ ] 시나리오 5: 멀티 OCR 앙상블
    ImageInput → YOLO → OCR Ensemble → BOM
    - 앙상블 결과가 BOM에 정상 전달
```

---

## 📅 권장 작업 일정

| 우선순위 | 작업 | 예상 소요 | 담당 |
|---------|------|----------|------|
| 🔴 High | Blueprint AI BOM 통합 테스트 | 2-3시간 | - |
| 🟠 Medium | Container Router 테스트 | 30분 | - |
| 🟡 Medium | healthEndpoint 검증 | 1시간 | - |
| 🟢 Low | 프론트엔드 빌드 검증 | 30분 | - |
| 🔵 Final | E2E 워크플로우 테스트 | 2시간 | - |

---

## 🔧 빠른 테스트 명령어 모음

```bash
# 1. 컨테이너 상태 확인
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 2. 게이트웨이 로그 확인
docker logs gateway-api --tail 100 -f

# 3. BOM API 헬스 체크
curl http://localhost:5020/api/v1/health

# 4. 프론트엔드 빌드
cd web-ui && npm run build

# 5. 백엔드 테스트
cd gateway-api && pytest tests/ -v

# 6. 전체 서비스 재시작
docker-compose restart gateway-api blueprint-ai-bom-api
```

---

## 📝 이슈 발견 시 기록 템플릿

```markdown
### Issue: [제목]

**발견일**: YYYY-MM-DD
**심각도**: 🔴Critical / 🟠High / 🟡Medium / 🟢Low
**상태**: Open / In Progress / Resolved

**증상**:
- [무엇이 문제인지]

**재현 방법**:
1. [Step 1]
2. [Step 2]

**예상 원인**:
- [추정 원인]

**해결 방법**:
- [수정 내용]

**관련 파일**:
- [파일 경로]
```
