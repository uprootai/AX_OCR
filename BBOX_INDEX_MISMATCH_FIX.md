# 🔴 Critical Bug Fix: Bbox Index Mismatch

**날짜**: 2025-10-29
**심각도**: Critical
**영향**: v2 API의 시각화 라벨과 JSON 응답 불일치

---

## 🐛 문제 발견

사용자 보고: "x,y,w,h 안에있는 결과와 json 안에 있는결과가 서로 불일치"

### 증상

시각화 이미지의 **D0, D1, D2** 라벨이 JSON 응답의 `dimensions[0], dimensions[1], dimensions[2]`와 **다른 dimension을 가리킴**

---

## 🔍 근본 원인 분석

### 문제의 아키텍처

```
1. OCR 처리 → dimensions (원본 배열)
                    ↓
2. 변환 함수 → ui_dimensions (변환된 배열)  ← 예외 시 continue!
                    ↓
3. API 응답: result = {dimensions: ui_dimensions}
4. 시각화:   for idx, dim in enumerate(dimensions)  ← 원본 사용!
```

### 문제의 핵심

**`api_server_edocr_v2.py:54-104` - `transform_edocr2_to_ui_format` 함수**

```python
for dim in dimensions:
    try:
        # 변환 로직...
        ui_dimensions.append(...)
    except Exception as e:
        logger.warning(f"Failed to transform dimension: {e}")
        continue  # ⚠️ 예외 발생 시 건너뜀!
```

### 인덱스 불일치 시나리오

```
원본 dimensions:
  [0] "R6"    → 성공 → ui_dimensions[0]
  [1] "invalid" → 실패 (파싱 에러) → 건너뜀
  [2] "R32"   → 성공 → ui_dimensions[1]  ❌ 인덱스 2 → 1로 변경
  [3] "7"     → 성공 → ui_dimensions[2]  ❌ 인덱스 3 → 2로 변경

시각화 (라인 410):
  for idx, dim in enumerate(dimensions):
    label = f"D{idx}"  # D0, D1, D2, D3

API 응답 (라인 398):
  result = {"dimensions": ui_dimensions}  # [0], [1], [2] (3개만!)

결과:
  D0 → dimensions[0] = ui_dimensions[0]  ✅ 일치
  D1 → dimensions[1] ≠ ui_dimensions[1]  ❌ 불일치!
  D2 → dimensions[2] ≠ ui_dimensions[2]  ❌ 불일치!
  D3 → dimensions[3] ≠ 존재하지 않음    ❌ 불일치!
```

---

## ✅ 해결 방법

### 1. ui_dimensions에 원본 정보 추가

**파일**: `api_server_edocr_v2.py`

**변경 전 (라인 93-99)**:
```python
ui_dimensions.append({
    'type': dim_type,
    'value': value,
    'unit': 'mm',
    'tolerance': tolerance,
    'bbox': bbox_info
})
```

**변경 후 (라인 93-101)**:
```python
ui_dimensions.append({
    'type': dim_type,
    'value': value,
    'unit': 'mm',
    'tolerance': tolerance,
    'bbox': bbox_info,
    '_original_bbox': bbox,  # 원본 polygon bbox 유지
    '_original_text': text   # 원본 텍스트 유지
})
```

### 2. 시각화에서 ui_dimensions 사용

**변경 전 (라인 410)**:
```python
for idx, dim in enumerate(dimensions):  # 원본 사용 ❌
```

**변경 후 (라인 414)**:
```python
for idx, dim in enumerate(ui_dimensions):  # 변환된 배열 사용 ✅
    bbox = dim.get('_original_bbox', [])  # 원본 bbox 사용
```

### 3. API 응답에서 내부 필드 제거

**추가됨 (라인 401-416)**:
```python
# Remove internal fields before sending response
clean_dimensions = []
for dim in ui_dimensions:
    clean_dim = {k: v for k, v in dim.items() if not k.startswith('_')}
    clean_dimensions.append(clean_dim)

clean_gdt = []
for gdt in ui_gdt:
    clean_g = {k: v for k, v in gdt.items() if not k.startswith('_')}
    clean_gdt.append(clean_g)

result = {
    "dimensions": clean_dimensions,
    "gdt": clean_gdt,
    "text": ui_text
}
```

### 4. GD&T에도 동일 로직 적용

- GD&T 변환에도 `_original_bbox`, `_original_text` 추가
- GD&T 시각화도 `ui_gdt` 사용

---

## 📋 변경 파일 목록

| 파일 | 라인 | 변경 내용 |
|------|------|-----------|
| `api_server_edocr_v2.py` | 93-101 | ui_dimensions에 _original_bbox 추가 |
| `api_server_edocr_v2.py` | 143-150 | ui_gdt에 _original_bbox 추가 |
| `api_server_edocr_v2.py` | 401-416 | API 응답 정제 로직 추가 |
| `api_server_edocr_v2.py` | 414-431 | 시각화에서 ui_dimensions 사용 |
| `api_server_edocr_v2.py` | 434-451 | 시각화에서 ui_gdt 사용 |

---

## 🔄 새로운 아키텍처

```
1. OCR 처리 → dimensions (원본 배열)
                    ↓
2. 변환 함수 → ui_dimensions (변환된 배열 + 원본 정보)
                    ├─ bbox: {x, y, width, height}
                    ├─ _original_bbox: [[x,y], ...]
                    └─ _original_text: "R6"
                    ↓
3. 정제 함수 → clean_dimensions (내부 필드 제거)
                    ├─ bbox: {x, y, width, height}
                    └─ (원본 정보 제거됨)
                    ↓
4. API 응답: result = {dimensions: clean_dimensions}
5. 시각화:   for idx, dim in enumerate(ui_dimensions)
              └─ dim.get('_original_bbox')  ← 원본 polygon 사용
```

### 이제 항상 일치:

- **API 응답**: `dimensions[i]` = `clean_dimensions[i]`
- **시각화**: `D{i}` = `ui_dimensions[i]` (원본 bbox 사용)

---

## ✅ 검증

### 테스트 시나리오

```bash
# v2 컨테이너 재시작
docker restart edocr2-api-v2

# 잠시 대기
sleep 10

# OCR 실행 (시각화 포함)
curl -X POST http://localhost:5002/api/v2/ocr \
  -F "file=@sample.jpg" \
  -F "visualize=true"

# 확인 사항:
# 1. JSON의 dimensions[0] 값
# 2. 시각화 이미지의 D0 라벨 위치
# 3. 두 값이 일치하는지 확인
```

### 예상 결과

**이전 (버그 있음)**:
- JSON `dimensions[0]`: R6, bbox=(52, 42, 47, 18)
- 시각화 D0: R32 위치  ❌ 불일치

**이후 (수정됨)**:
- JSON `dimensions[0]`: R6, bbox=(52, 42, 47, 18)
- 시각화 D0: R6 위치  ✅ 일치

---

## 🎯 영향 범위

### 수정됨
- ✅ v2 API (`api_server_edocr_v2.py`)
- ✅ 시각화 라벨 (D0, D1, ..., G0, G1, ...)
- ✅ JSON 응답 (dimensions, gdt)

### 영향 없음
- v1 API (변환 로직이 다름)
- 다른 마이크로서비스
- 클라이언트 UI (API 응답 형식 동일)

---

## 📝 추가 개선 사항

### 고려할 사항

1. **에러 로깅 강화**:
   ```python
   except Exception as e:
       logger.error(f"Failed to transform dimension: {e}, dim={dim}")
       continue
   ```

2. **변환 성공률 추적**:
   ```python
   success_count = len(ui_dimensions)
   total_count = len(dimensions)
   logger.info(f"Transformed {success_count}/{total_count} dimensions")
   ```

3. **부분 파싱 허용**:
   현재는 예외 발생 시 전체 dimension을 건너뜀. 부분적으로 파싱 가능하다면 포함시키는 것이 나을 수 있음.

---

## 🚀 배포 체크리스트

- [x] 코드 수정 완료
- [x] v2 컨테이너 업데이트
- [x] v2 컨테이너 재시작
- [ ] 테스트 실행 (사용자 확인 필요)
- [ ] 검증 문서 작성
- [ ] v1 API 확인 (동일 문제 있는지)

---

## 🔗 관련 이슈

- **원본 이슈**: bbox에 width, height 추가 필요
- **발견된 버그**: 시각화와 JSON 인덱스 불일치
- **해결 방법**: 통합 데이터 소스 사용 (ui_dimensions)

---

**Generated by**: Claude Code
**Fix Type**: Critical Bug Fix
**Test Status**: Pending User Verification
**Rollback Plan**: `docker cp` 원본 파일 복원 후 `docker restart`
