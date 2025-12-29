# Codebase Consistency Review - 2025-12-29

> 마지막 커밋 대비 변경사항 분석 및 일관성 적용 작업 목록

---

## 변경 요약

### 완료된 핵심 변경

| 패턴 | 상태 | 설명 |
|------|------|------|
| Lifespan 마이그레이션 | ✅ 완료 | 모든 17개 API에 `@asynccontextmanager` 적용 |
| on_event 제거 | ✅ 완료 | `@app.on_event("startup/shutdown")` 전면 제거 |
| pid_symbol → pid_class_aware | ✅ 완료 | 모든 파일에서 통일 |
| vl-api 라우터 분리 | ✅ 완료 | 1035줄 → 202줄 |
| design-checker-api 리팩토링 | ✅ 완료 | 1482줄 → 167줄 |
| line-detector-api 라우터 분리 | ✅ 완료 | routers/, services/ 분리 |
| pid-analyzer-api 라우터 분리 | ✅ 완료 | routers/, services/ 분리 |

### 프론트엔드 변경

| 파일 | 변경 | 내용 |
|------|------|------|
| analysisNodes.ts | +42/-17 | pid_class_aware 통일, BWMS 규칙, Design Checker 파라미터 |
| detectionNodes.ts | +13/-4 | bom_detector 기본값, 파라미터 설명 개선 |
| segmentationNodes.ts | +8/-10 | min_region_area 기본값 5000으로 통일 |

### API 스펙 변경

| 파일 | 변경 | 내용 |
|------|------|------|
| yolo.yaml | +122 | modelTypes 상세 설명 추가 |
| pid-analyzer.yaml | +159 | additionalEndpoints (Valve Signal), regionRulesSchema |
| design-checker.yaml | +12 | include_bwms 파라미터 추가 |

---

## P0: 즉시 Git Add 필요 (✅ 완료)

### [x] vl-api 신규 파일 staging

**상태**: ✅ 완료 (2025-12-29)

```bash
git add models/vl-api/routers/ models/vl-api/schemas.py models/vl-api/services/
```

---

## P1: 일관성 수정 완료

### [x] 1.1 pid_symbol → pid_class_aware 일관성

**상태**: ✅ 완료 (2025-12-29)

| 파일 | 상태 | 비고 |
|------|------|------|
| `gateway-api/api_specs/yolo.yaml` | ✅ 완료 | pid_class_aware 사용 |
| `gateway-api/blueprintflow/executors/yolo_executor.py` | ✅ 완료 | 파라미터 전달만 |
| `web-ui/src/config/nodes/detectionNodes.ts` | ✅ 완료 | pid_class_aware 사용 |
| `gateway-api/services/yolo_service.py:48` | ✅ 수정 완료 | 주석 수정 |
| `web-ui/src/config/nodes/analysisNodes.ts` | ✅ 수정 완료 | 4곳 수정 |

### [x] 1.2 min_region_area 기본값 통일

**상태**: ✅ 완료 (2025-12-29)

| 위치 | 수정 전 | 수정 후 |
|------|--------|--------|
| segmentationNodes.ts default | 1000 | 5000 |
| segmentationNodes.ts min | 500 | 1000 |
| segmentationNodes.ts step | 500 | 1000 |

### [x] 1.3 Valve Signal 파라미터 정리

**상태**: ✅ 프론트엔드에서 제거 완료 (2025-12-29)

**결정**: Valve Signal은 별도 API (`/api/v1/valve-signal/extract`)로만 사용

**제거된 항목**:
- PID Analyzer inputs: `regions`, `texts` (Valve Signal용)
- PID Analyzer outputs: `region_extraction`
- PID Analyzer analysis_type: `region_extraction` 옵션
- 파라미터 4개: `extract_valve_signals`, `valve_signal_rule_id`, `text_margin`, `export_valve_signal_excel`

**추가된 usageTip**:
> 🎛️ Valve Signal 추출은 별도 API (/api/v1/valve-signal/extract)를 사용하세요

---

## P2: 라우터 분리 대상 (500줄 이상)

### 현재 상태 (4/18 완료)

| API | 라인 수 | 상태 | 비고 |
|-----|--------|------|------|
| design-checker-api | 167 | ✅ 완료 | routers/, schemas.py, constants.py |
| line-detector-api | ~400 | ✅ 완료 | routers/, services/ |
| pid-analyzer-api | ~400 | ✅ 완료 | routers/, services/ |
| vl-api | 202 | ✅ 완료 | routers/, services/, schemas.py |

### [ ] 2.1 yolo-api 라우터 분리 (867줄)

**현재 구조**:
```
models/yolo-api/
├── api_server.py (867줄) ❌
├── services/
│   └── inference_service.py
└── models/
    └── schemas.py
```

**목표 구조**:
```
models/yolo-api/
├── api_server.py (~200줄)
├── routers/
│   ├── __init__.py
│   └── detection_router.py (~400줄)
├── services/
│   └── inference_service.py
└── schemas.py (루트로 이동)
```

**분리 대상 엔드포인트**:
- `/api/v1/info`
- `/api/v1/detect`
- `/api/v1/detect/batch`
- `/api/v1/models`
- `/api/v1/models/{model_id}`

### [ ] 2.2 edgnet-api 라우터 분리 (669줄)

**분리 대상**:
- `/api/v1/info`
- `/api/v1/segment`
- `/api/v1/edge`
- `/api/v1/mask`

### [ ] 2.3 ocr-ensemble-api 라우터 분리 (648줄)

**분리 대상**:
- `/api/v1/info`
- `/api/v1/recognize`
- `/api/v1/vote`
- `/api/v1/engines`

### [ ] 2.4 knowledge-api 라우터 분리 (533줄)

**분리 대상**:
- `/api/v1/info`
- `/api/v1/query`
- `/api/v1/graph/*`

### [ ] 2.5 esrgan-api 라우터 분리 (507줄)

**분리 대상**:
- `/api/v1/info`
- `/api/v1/upscale`

---

## P3: 문서화 표준 (endpoints.md)

### 완료된 문서 (3/18)

- ✅ `docs/api/design-checker/endpoints.md`
- ✅ `docs/api/line-detector/endpoints.md`
- ✅ `docs/api/pid-analyzer/endpoints.md`

### [ ] 3.1 미완료 문서 (15개)

**우선순위 높음 (핵심 API)**:

| API | 파일 | 엔드포인트 수 |
|-----|------|--------------|
| yolo | docs/api/yolo/endpoints.md | 5개 |
| edocr2 | docs/api/edocr2/endpoints.md | 4개 |
| vl | docs/api/vl/endpoints.md | 6개 |
| blueprint-ai-bom | docs/api/blueprint-ai-bom/endpoints.md | 20+개 |

**우선순위 중간 (OCR 계열)**:

| API | 파일 | 엔드포인트 수 |
|-----|------|--------------|
| paddleocr | docs/api/paddleocr/endpoints.md | 3개 |
| tesseract | docs/api/tesseract/endpoints.md | 3개 |
| trocr | docs/api/trocr/endpoints.md | 3개 |
| surya-ocr | docs/api/surya-ocr/endpoints.md | 4개 |
| doctr | docs/api/doctr/endpoints.md | 3개 |
| easyocr | docs/api/easyocr/endpoints.md | 3개 |
| ocr-ensemble | docs/api/ocr-ensemble/endpoints.md | 4개 |

**우선순위 낮음 (기타)**:

| API | 파일 | 엔드포인트 수 |
|-----|------|--------------|
| edgnet | docs/api/edgnet/endpoints.md | 4개 |
| esrgan | docs/api/esrgan/endpoints.md | 2개 |
| knowledge | docs/api/knowledge/endpoints.md | 5개 |
| skinmodel | docs/api/skinmodel/endpoints.md | 3개 |

**endpoints.md 표준 템플릿**:
```markdown
# {API Name} API Endpoints

## 엔드포인트 목록

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | /health | 헬스체크 |
| GET | /api/v1/info | API 메타데이터 |
| POST | /api/v1/{main} | 주요 기능 |

## 상세 설명

### GET /health
...

### POST /api/v1/{main}

**요청:**
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|

**응답:**
```json
{...}
```
```

---

## P4: 프론트엔드 동기화

### [x] 4.1 노드 정의 변경사항 (✅ 완료)

| 파일 | 변경 내용 | 상태 |
|------|----------|------|
| analysisNodes.ts | `pid_symbol` → `pid_class_aware` | ✅ 완료 |
| analysisNodes.ts | Design Checker에 `include_bwms` 추가 | ✅ 완료 |
| analysisNodes.ts | Design Checker categories에 `bwms` 옵션 추가 | ✅ 완료 |
| analysisNodes.ts | Design Checker에 PaddleOCR 입력 추가 | ✅ 완료 |
| segmentationNodes.ts | `min_region_area` 기본값 5000 | ✅ 완료 |

### [ ] 4.2 APIDetail.tsx 하이퍼파라미터 동기화

**확인 필요**:
- [ ] Design Checker `include_bwms` 파라미터 반영
- [ ] Line Detector 새 파라미터 (classify_styles, detect_regions 등) 반영

---

## P5: API 스펙 확장

### [x] 5.1 yolo.yaml modelTypes 추가 (✅ 완료)

**추가된 내용**:
- `modelTypes` 섹션: engineering, pid_class_aware, pid_class_agnostic, bom_detector 상세 설명
- 각 모델별 detectableSymbols, recommendedParams, useCases

### [x] 5.2 pid-analyzer.yaml additionalEndpoints (✅ 완료)

**추가된 엔드포인트**:
- `/api/v1/region-rules` (CRUD)
- `/api/v1/region-text/extract`
- `/api/v1/valve-signal/extract`
- `/api/v1/valve-signal/export-excel`

### [ ] 5.3 다른 API 스펙에 modelTypes/additionalEndpoints 패턴 적용

**적용 대상**:
- edocr2.yaml: 모델 옵션 상세화
- vl.yaml: 프로바이더별 상세 설명

---

## P6: 테스트 결과 파일 정리

### [ ] 6.1 삭제된 테스트 결과 파일

```
deleted:    test-results/pid-analysis-new/*
deleted:    test-results/pid-analysis/00-29-48_P_ID_Analysis_Pipeline/*
deleted:    test-results/pid-debug/*
```

**확인**: 의도적 삭제인지 확인 필요

---

## 검증 명령어 모음

```bash
# 1. lifespan 적용 확인
grep -l "asynccontextmanager" models/*/api_server.py | wc -l  # 17개여야 함

# 2. on_event 잔존 확인
grep -r "@app.on_event" models/  # 결과 없어야 함

# 3. pid_symbol 잔존 확인 (하위호환성 매핑 제외)
grep -r "pid_symbol" --include="*.ts" --include="*.py" . | grep -v model_id_map

# 4. 파일 라인 수 확인
wc -l models/*/api_server.py | sort -rn | head -10

# 5. 라우터 디렉토리 현황
ls -d models/*/routers 2>/dev/null

# 6. 구문 오류 검증
for f in models/*/api_server.py; do python3 -m py_compile "$f" && echo "✅ $f" || echo "❌ $f"; done

# 7. TypeScript 빌드 검증
cd web-ui && npx tsc --noEmit
```

---

## 작업 순서 권장

1. **P2.1: yolo-api 라우터 분리** (1시간) - 가장 큰 파일
2. **P2.2-P2.5: 나머지 500줄+ API 분리** (각 30분)
3. **P3: 핵심 API 문서화** (yolo, edocr2, vl) (2시간)
4. **P4.2: APIDetail.tsx 동기화** (30분)
5. **P5.3: API 스펙 패턴 확장** (1시간)

---

## 커밋 대기 파일 요약

```
Modified (Staged):
- gateway-api/services/yolo_service.py (pid_class_aware 주석 수정)
- web-ui/src/config/nodes/analysisNodes.ts (+42 lines)
- web-ui/src/config/nodes/segmentationNodes.ts (min_region_area 수정)

Untracked (Add 필요):
- models/vl-api/routers/
- models/vl-api/schemas.py
- models/vl-api/services/
```

---

*Created: 2025-12-29*
*Last Updated: 2025-12-29*
