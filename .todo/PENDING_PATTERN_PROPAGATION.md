# 패턴 확산 적용 작업 목록

> **작성일**: 2026-02-01
> **기준**: ea3463f 대비 변경사항에서 발견된 부분적 적용 패턴
> **목적**: 한 노드/서비스에 적용된 변경이 다른 노드에도 적용되어야 하는 항목 추적

---

## P0: 즉시 확인 필요 (잔여 참조 정리)

### 0-1. Excel Export 잔여 참조 완전 제거 확인

**배경**: Excel Export 노드를 완전 삭제했으나, 코드베이스 전체에서 참조가 남아있을 수 있음

**확인 대상**:

| 항목 | 확인 방법 | 예상 |
|------|----------|------|
| CLAUDE.md 노드 목록 | `grep -i "excel" CLAUDE.md` | ❓ 노드 30개 목록에 Excel Export 포함 여부 |
| node-palette/constants.ts | `grep "excelexport\|excel-export\|FileSpreadsheet" web-ui/` | ✅ 이미 제거됨 |
| apiRegistry.ts | `grep "excelexport" web-ui/src/config/apiRegistry.ts` | ❓ 확인 필요 |
| SaveTemplateModal.tsx | diff에서 1줄 변경 확인 | ❓ excelexport 참조 제거인지 확인 |
| 사용자 저장 템플릿 | DB/localStorage에 excelexport 노드 포함 템플릿 | ❓ 런타임 에러 가능 |

**작업**:
```bash
# 전체 코드베이스 검색
grep -r "excelexport\|excel.export\|ExcelExport\|FileSpreadsheet" --include="*.ts" --include="*.tsx" --include="*.py" --include="*.yaml" --include="*.md" web-ui/ gateway-api/ blueprint-ai-bom/ CLAUDE.md
```

---

## P1: 다른 OCR 엔진에 _safe_to_gray() 패턴 적용

### 1-1. cv2.cvtColor(img, COLOR_BGR2GRAY) 안전화

**문제**: eDOCr2에서 `cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)` 호출 시 이미 그레이스케일인 이미지가 들어오면 크래시. 전처리 파이프라인(CLAHE 등)이 그레이스케일을 반환하는 경우 발생.

**eDOCr2 수정 완료**: `_safe_to_gray()` 함수 도입, 7곳 교체

**다른 API 확인 대상**:

| API | 파일 | 확인 내용 | 우선순위 |
|-----|------|----------|----------|
| **PaddleOCR** | `models/paddleocr-api/services/ocr_service.py` | `cv2.cvtColor` 직접 호출 여부 | 높음 |
| **EasyOCR** | `models/easyocr-api/services/ocr_service.py` | 동일 | 높음 |
| **Tesseract** | `models/tesseract-api/services/ocr_service.py` | 동일 | 중간 |
| **TrOCR** | `models/trocr-api/services/ocr_service.py` | 동일 | 중간 |
| **DocTR** | `models/doctr-api/services/ocr_service.py` | 동일 | 중간 |
| **SuryaOCR** | `models/suryaocr-api/services/ocr_service.py` | 동일 | 낮음 |
| **EDGNet** | `models/edgnet-api/services/segmentation_service.py` | 엣지 검출 전처리 | 중간 |
| **Line Detector** | `models/line-detector-api/services/line_service.py` | 라인 검출 전처리 | 중간 |
| **ESRGAN** | `models/esrgan-api/services/upscale_service.py` | 업스케일링 전처리 | 낮음 |

**검색 방법**:
```bash
grep -rn "cv2.cvtColor.*COLOR_BGR2GRAY\|cv2.cvtColor.*COLOR_RGB2GRAY" models/ --include="*.py" | grep -v "edocr2"
```

**적용 패턴**:
```python
def _safe_to_gray(img):
    if img is None or img.size == 0:
        return img
    if len(img.shape) == 2:
        return img
    if img.shape[2] == 1:
        return img[:, :, 0]
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
```

---

### 1-2. 제로 차원 이미지 방어 패턴

**문제**: YOLO 검출 바운딩박스로 크롭 시 폭/높이가 0인 ROI가 발생 가능. `fit()` 등 리사이즈 함수에서 division-by-zero.

**eDOCr2 수정 완료**: `keras_ocr/tools.py` `fit()` 함수에 가드 추가

**다른 API 확인 대상**:

| API | 파일 | 확인 내용 |
|-----|------|----------|
| **PaddleOCR** | 크롭 후 텍스트 인식 | `img[y1:y2, x1:x2]` 결과가 빈 배열일 경우 |
| **Table Detector** | 테이블 셀 크롭 | 셀 좌표가 이미지 경계 밖일 경우 |
| **OCR Ensemble** | 영역별 OCR 호출 | YOLO 박스를 크롭해서 전달하는 경로 |

**검색 방법**:
```bash
grep -rn "img\[.*:.*,.*:.*\]\|image\[.*:.*,.*:.*\]" models/ --include="*.py" | head -30
```

---

### 1-3. numpy 배열 리스트 제거 시 `is` 비교 사용

**문제**: `list.remove(np_array)`는 내부적으로 `==` 비교 → numpy element-wise 비교 → `ValueError: The truth value of an array is ambiguous`

**eDOCr2 수정 완료**: `ocr_pipelines.py`에서 `is` identity 비교로 변경

**확인 대상**: numpy 배열을 리스트에 넣고 `remove()`/`index()`를 호출하는 코드

```bash
grep -rn "\.remove(" models/ --include="*.py" | grep -v "__pycache__" | head -20
```

---

## P1: GPU→CPU 폴백 패턴 전파

### 1-4. GPU 전처리 API에 CPU 폴백 추가

**배경**: eDOCr2에서 GPU 전처리 실패 시 CPU CLAHE+GaussianBlur 폴백 추가. GPU 불가 환경(CPU-only 서버)에서도 동일 품질 보장.

**현재 상태**:
- ✅ eDOCr2: GPU→CPU 폴백 구현 완료
- ❓ PaddleOCR: GPU 사용 여부 확인 필요 (PaddlePaddle은 자체 GPU 관리)
- ❓ EasyOCR: GPU 전처리 여부 확인 필요
- ❓ ESRGAN: GPU 전용이므로 CPU 폴백 불가하지만 에러 핸들링 필요

**확인 대상**:

| API | GPU 사용 | 폴백 필요 여부 |
|-----|----------|---------------|
| PaddleOCR | PaddlePaddle GPU | 자체 CPU 폴백 있음 (확인 필요) |
| EasyOCR | PyTorch GPU | 자체 CPU 모드 있음 (확인 필요) |
| TrOCR | HuggingFace GPU | transformers가 자동 관리 |
| DocTR | TF/PyTorch GPU | 자체 CPU 모드 |
| ESRGAN | PyTorch GPU | GPU 전용 (에러 시 원본 반환 고려) |
| YOLO | Ultralytics GPU | 자체 CPU 폴백 있음 |

---

## P1: Executor features/params 병합 패턴 전파

### 1-5. 다른 Executor에서 inputs+parameters 병합 필요 여부

**배경**: BOM executor에서 `features`를 inputs과 parameters 양쪽에서 받아 병합하도록 변경. 동일 키가 inputs와 parameters에 모두 있는 다른 executor가 있는지 확인.

**패턴**:
```python
# 리스트 파라미터 병합 패턴
input_values = inputs.get("key", [])
param_values = self.parameters.get("key", [])
merged = list(dict.fromkeys(list(input_values) + list(param_values)))  # 중복 제거, 순서 유지
```

**확인 대상**:

| Executor | 리스트형 파라미터 | 확인 필요 |
|----------|-----------------|----------|
| `pidfeatures_executor` | `features` 리스트 | ❓ inputs과 params 양쪽 수신 여부 |
| `designchecker_executor` | `rules` 리스트 | ❓ 동일 |
| `ocr_ensemble_executor` | `engines` 리스트 | ❓ 동일 |
| `verificationqueue_executor` | `stages` 리스트 | ❓ 동일 |

**검색 방법**:
```bash
grep -rn "self\.parameters\.get.*\[\]" gateway-api/blueprintflow/executors/ --include="*.py"
```

---

## P1: _call_api() 메서드 추출 패턴 전파

### 1-6. 다른 Executor에서 API 호출 로직 분리

**배경**: Table Detector executor에서 `execute()` 내 인라인 httpx 호출을 `_call_api()` 별도 메서드로 추출. multi-region 처리와 에러 핸들링 개선.

**현재 상태**:
- ✅ `tabledetector_executor.py`: `_call_api()` 분리 완료
- ❓ `bom_executor.py`: `execute()` 내 httpx 호출 인라인
- ❓ `pdfexport_executor.py`: `execute()` 내 httpx 호출 인라인
- ❓ `pidfeatures_executor.py`: `execute()` 내 httpx 호출 인라인

**이점**:
1. 재시도 로직 추가 용이
2. 타임아웃 개별 설정
3. 에러 격리 (한 API 실패가 다른 처리에 영향 안줌)
4. 테스트 시 mock 용이

**확인 대상**:
```bash
grep -rn "httpx.AsyncClient" gateway-api/blueprintflow/executors/ --include="*.py"
```

---

## P2: Table Detector multi-crop 패턴 확장

### 2-1. 비DSE 템플릿에 multi-crop 적용

**배경**: DSE Bearing 6개 템플릿에만 `crop_regions: ['title_block', 'revision_table', 'parts_list_right']` 적용됨.

**확인 대상**: 다른 Table Detector 사용 템플릿 (있다면) 에도 동일 multi-crop 기본값 적용

**프론트엔드 영향**:
- `detectionNodes.ts`의 `table_detector` 프로파일에 `multi_crop_drawing`이 default로 설정됨
- 사용자가 빌더에서 Table Detector를 새로 추가하면 자동으로 3개 영역 크롭 적용
- 기존 저장된 워크플로우는 `crop_regions`가 없으므로 `auto_crop: "full"` 폴백

### 2-2. 품질 필터 임계값 커스터마이징

**현재**: `max_empty_ratio: 0.7` 하드코딩된 기본값
**필요**: 도면 종류별로 다른 임계값이 적절할 수 있음

| 도면 종류 | 적절한 임계값 | 이유 |
|-----------|-------------|------|
| 기계 도면 (Parts List) | 0.7 | 표준 BOM 테이블 |
| P&ID 도면 | 0.5 | 더 엄격한 필터 필요 (노이즈 많음) |
| 전력 단선도 | 0.8 | 빈 셀이 많은 것이 정상 |

---

## P2: dimension_service 멀티 엔진 패턴 확장

### 2-3. PaddleOCR 외 다른 OCR 엔진 통합

**현재**: `dimension_service.py`에 eDOCr2 + PaddleOCR 2개 엔진 지원

**향후 확장 대상**:

| OCR 엔진 | 특화 분야 | 통합 가치 |
|----------|----------|----------|
| **Tesseract** | 영문 일반 텍스트 | 중간 (도면번호/리비전) |
| **TrOCR** | 필기체/특수 폰트 | 높음 (수기 치수) |
| **DocTR** | 문서 레이아웃 | 중간 (테이블 구조) |
| **EasyOCR** | 다국어 | 높음 (한국어 치수) |

**필요 작업** (각 엔진 추가 시):
1. `_parse_{engine}_detection()` 파서 메서드 추가
2. `_ENGINE_BASE_WEIGHTS`에 가중치 추가
3. `_ENGINE_SPECIALTY_BONUS`에 특화 보너스 추가
4. `extract_dimensions()`의 엔진 호출 루프에 추가

### 2-4. 가중 투표 병합 → OCR Ensemble executor 통합

**현재**: `dimension_service.py`의 `_merge_multi_engine()`과 OCR Ensemble의 `merge_results()`가 유사한 로직을 별도 구현

**향후**: 공통 투표 라이브러리 추출 고려
```
blueprint-ai-bom/backend/services/dimension_service.py  → _merge_multi_engine()
models/ocr-ensemble-api/services/ensemble_service.py     → merge_results()
→ 공통 패턴: IoU 클러스터링 + 가중 투표 + 합의 보너스
```

---

## P2: CLAUDE.md 노드 수 동기화

### 2-5. CLAUDE.md BlueprintFlow 노드 타입 목록 업데이트

**현재 CLAUDE.md**: "노드 타입 (30개)" — Excel Export 포함 상태

**필요**:
1. Excel Export 제거 → 29개
2. Table Detector 파라미터 유효 목록에 `crop_regions`, `enable_quality_filter`, `max_empty_ratio` 추가
3. BOM 유효 파라미터에 `drawing_type`, `features` 추가
4. DSE Bearing 템플릿 수 12→6개로 갱신

---

## P3: 장기 표준화 작업

### 3-1. Executor API 호출 재시도/타임아웃 표준화

**현재**: 각 executor가 개별적으로 `httpx.AsyncClient(timeout=...)` 설정
**필요**: 공통 베이스 클래스에 재시도 로직 + 설정 가능한 타임아웃

### 3-2. Docker 컨테이너 GPU→CPU 자동 감지

**현재**: `use_gpu_preprocessing` 파라미터로 수동 설정
**필요**: 컨테이너 시작 시 GPU 가용성 자동 감지 → 적절한 모드 선택

### 3-3. 크롭 좌표 시각화 디버그 도구

**현재**: Table Detector의 `crop_regions`가 정확한 영역을 크롭하는지 확인하려면 실행 후 결과만 볼 수 있음
**필요**: 빌더에서 크롭 영역을 이미지 위에 오버레이로 미리보기

---

## 작업 체크리스트 요약

### 즉시 (P0)
- [ ] **0-1**: Excel Export 잔여 참조 전체 검색 및 정리

### 이번 주 (P1)
- [ ] **1-1**: 다른 OCR API에서 `cv2.cvtColor` 직접 호출 검색 → _safe_to_gray 필요 여부
- [ ] **1-2**: 크롭 후 제로 차원 이미지 방어 검색
- [ ] **1-3**: numpy 배열 리스트 `remove()` 사용 검색
- [ ] **1-4**: GPU 전처리 API 폴백 상태 확인
- [ ] **1-5**: Executor inputs+parameters 병합 필요 케이스 검색
- [ ] **1-6**: Executor _call_api() 메서드 추출 필요 케이스 검색

### 다음 주 (P2)
- [ ] **2-1**: 비DSE 템플릿 multi-crop 적용
- [ ] **2-2**: 품질 필터 도면 종류별 임계값
- [ ] **2-3**: dimension_service 다른 OCR 엔진 통합
- [ ] **2-4**: 가중 투표 병합 공통 라이브러리 검토
- [ ] **2-5**: CLAUDE.md 노드/파라미터 목록 갱신

### 장기 (P3)
- [ ] **3-1**: Executor API 호출 재시도/타임아웃 표준화
- [ ] **3-2**: Docker GPU 자동 감지
- [ ] **3-3**: 크롭 영역 미리보기 도구

---

## 관련 파일 경로

### 패턴 소스 (변경 완료된 파일)
```
gateway-api/blueprintflow/executors/bom_executor.py        # features 병합 패턴
gateway-api/blueprintflow/executors/tabledetector_executor.py  # multi-crop + _call_api() 패턴
models/edocr2-v2-api/edocr2_src/tools/ocr_pipelines.py    # _safe_to_gray() 패턴
models/edocr2-v2-api/services/ocr_processor.py             # GPU→CPU 폴백 패턴
models/edocr2-v2-api/edocr2_src/keras_ocr/tools.py        # 제로 차원 가드 패턴
blueprint-ai-bom/backend/services/dimension_service.py     # 멀티 엔진 가중 투표 패턴
```

### 적용 대상 (검사 필요한 파일)
```
models/paddleocr-api/services/ocr_service.py
models/easyocr-api/services/ocr_service.py
models/tesseract-api/services/ocr_service.py
models/trocr-api/services/ocr_service.py
models/doctr-api/services/ocr_service.py
models/suryaocr-api/services/ocr_service.py
models/edgnet-api/services/segmentation_service.py
models/line-detector-api/services/line_service.py
gateway-api/blueprintflow/executors/*_executor.py
```

---

*이 문서는 부분적 변경이 다른 노드/서비스에 확산 적용되어야 하는 패턴을 추적합니다.*
*작업 완료 시 체크박스를 갱신하세요.*

*작성: Claude Code (Opus 4.5) - 2026-02-01*
