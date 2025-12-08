# Executor Visualization 수정 작업

**날짜**: 2025-12-07
**작업자**: Claude Code (Opus 4.5)
**목적**: BlueprintFlow 파이프라인 결과 시각화 호환성 수정

---

## 문제 요약

프론트엔드 `BlueprintFlowBuilder.tsx`는 노드 출력에서 `output?.image` 또는 `output?.visualized_image` 필드를 찾아 이미지를 표시합니다. 하지만 여러 Executor가 다른 필드명(`visualization`)을 사용하거나 시각화 이미지를 전달하지 않고 있습니다.

---

## 수정 대상 목록

### 1. 필드명 불일치 (이미 수정됨)

| Executor | 파일 | 기존 필드 | 수정 후 |
|----------|------|----------|---------|
| ✅ Line Detector | `linedetector_executor.py` | `visualization` | `visualized_image` + `image` |
| ✅ YOLO-PID | `yolopid_executor.py` | `visualization` | `visualized_image` + `image` |
| ✅ PID Analyzer | `pidanalyzer_executor.py` | `visualization` | `visualized_image` + `image` |

### 2. 시각화 이미지 미전달 (수정 완료)

| Executor | 파일 | 문제 | 수정 내용 |
|----------|------|------|----------|
| ✅ Tesseract | `tesseract_executor.py` | API 반환값 중 `visualized_image` 미전달 | 필드 추가 완료 |
| ✅ TrOCR | `trocr_executor.py` | API 반환값 중 `visualized_image` 미전달 | 필드 추가 완료 |
| ✅ OCR Ensemble | `ocr_ensemble_executor.py` | API 반환값 중 `visualized_image` 미전달 | 필드 추가 완료 |

### 3. 시각화 기능 없음 (현재 상태 유지 - 의도된 설계)

| Executor | 이유 |
|----------|------|
| Design Checker | 텍스트 분석 결과만 반환 (위반 목록) |
| VL | 텍스트 응답만 반환 (caption/answer) |
| SkinModel | 공차 데이터만 반환 |
| Knowledge | 검색 결과만 반환 |

### 4. 프론트엔드 개선 (향후 작업)

| 항목 | 설명 | 우선순위 |
|------|------|----------|
| ⬜ 원본 이미지 표시 | 파이프라인 첫 단계에 원본 이미지 표시 | Medium |
| ⬜ 누적 오버레이 | 이전 노드 결과 위에 현재 결과 오버레이 | Low |

---

## 수정 상세 내역

### 1.1 Line Detector Executor (수정 완료)

**파일**: `gateway-api/blueprintflow/executors/linedetector_executor.py`

```python
# Before
"visualization": data.get("visualization", ""),

# After
"visualized_image": data.get("visualization", ""),
"image": data.get("visualization", ""),
```

### 1.2 YOLO-PID Executor (수정 완료)

**파일**: `gateway-api/blueprintflow/executors/yolopid_executor.py`

```python
# Before
"visualization": data.get("visualization", ""),

# After
visualization = data.get("visualization", "")
"visualized_image": visualization,
"image": visualization,
```

### 1.3 PID Analyzer Executor (수정 완료)

**파일**: `gateway-api/blueprintflow/executors/pidanalyzer_executor.py`

```python
# Before
"visualization": data.get("visualization", ""),

# After
visualization = data.get("visualization", "")
"visualized_image": visualization,
"image": visualization,
```

### 2.1 Tesseract Executor (수정 완료)

**파일**: `gateway-api/blueprintflow/executors/tesseract_executor.py`

```python
# 추가됨
"visualized_image": result.get("visualized_image", ""),
"image": result.get("visualized_image", ""),
```

### 2.2 TrOCR Executor (수정 완료)

**파일**: `gateway-api/blueprintflow/executors/trocr_executor.py`

```python
# 추가됨
"visualized_image": result.get("visualized_image", ""),
"image": result.get("visualized_image", ""),
```

### 2.3 OCR Ensemble Executor (수정 완료)

**파일**: `gateway-api/blueprintflow/executors/ocr_ensemble_executor.py`

```python
# 추가됨
"visualized_image": result.get("visualized_image", ""),
"image": result.get("visualized_image", ""),
```

---

## 테스트 계획

1. 각 수정된 Executor에 대해:
   - 단위 테스트 실행
   - BlueprintFlow에서 실제 파이프라인 실행
   - 결과 이미지 표시 확인

2. E2E 테스트:
   - `e2e/pid-analysis.spec.ts` 실행
   - 시각화 결과 캡처

---

## 진행 상태

- [x] 문제 분석 완료
- [x] Line Detector 수정
- [x] YOLO-PID 수정
- [x] PID Analyzer 수정
- [x] Tesseract 수정
- [x] TrOCR 수정
- [x] OCR Ensemble 수정
- [x] 빌드 검증 ✅ (23.07s)
- [x] 테스트 실행 ✅ (31/31 passed)

---

## 완료 요약

**작업 완료 시각**: 2025-12-07 10:17

### 수정된 파일 (6개)

1. `gateway-api/blueprintflow/executors/linedetector_executor.py`
2. `gateway-api/blueprintflow/executors/yolopid_executor.py`
3. `gateway-api/blueprintflow/executors/pidanalyzer_executor.py`
4. `gateway-api/blueprintflow/executors/tesseract_executor.py`
5. `gateway-api/blueprintflow/executors/trocr_executor.py`
6. `gateway-api/blueprintflow/executors/ocr_ensemble_executor.py`

### 검증 결과

- **프론트엔드 빌드**: ✅ 성공 (23.07s)
- **단위 테스트**: ✅ 31/31 통과

---

## 참고 파일

- 프론트엔드: `web-ui/src/pages/blueprintflow/BlueprintFlowBuilder.tsx:781`
- 시각화 컴포넌트: `web-ui/src/components/debug/`
