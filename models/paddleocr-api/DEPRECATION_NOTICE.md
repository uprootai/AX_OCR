# PaddleOCR API Deprecation Notice

> **상태**: DEPRECATED (삭제 권장)
> **날짜**: 2025-11-13
> **이유**: eDOCr2 API와 기능 중복, 고유 가치 부족

---

## 📋 Summary

PaddleOCR API는 **삭제 권장** 대상입니다.

**핵심 이유**:
1. eDOCr2 API와 기능 중복 (텍스트 인식)
2. 엔지니어링 도면에 대한 전문성 부족
3. 시스템 복잡도 증가 without unique value
4. "각 API 고유 능력치 최대화" 목표에 부합하지 않음

---

## 🔍 Functional Analysis

### PaddleOCR API 기능

| 기능 | 설명 | 특징 |
|-----|------|------|
| **텍스트 검출** | 이미지에서 텍스트 영역 검출 | Bounding box 반환 |
| **텍스트 인식** | 검출된 영역의 텍스트 OCR | 일반 텍스트 인식 |
| **다국어 지원** | en, ch, korean, japan 등 | PaddleOCR 강점 |
| **회전 감지** | 회전된 텍스트 자동 보정 | `use_angle_cls` |

**API Endpoint**:
- `POST /api/v1/ocr`: 이미지 업로드 → 텍스트 검출/인식

**입력**: 이미지 파일 (PNG, JPG)
**출력**: 텍스트 + 신뢰도 + Bbox

---

### eDOCr2 API 기능

| 기능 | 설명 | 특징 |
|-----|------|------|
| **치수 추출** | 엔지니어링 치수 인식 (φ100, R50, etc.) | **전문화됨** |
| **GD&T 추출** | 기하공차 기호 인식 (⌹, ○, ⌖, etc.) | **전문화됨** |
| **표 추출** | 엔지니어링 도면 표 인식 | **전문화됨** |
| **텍스트 추출** | 일반 텍스트 블록 OCR | PaddleOCR와 유사 |

**API Endpoint**:
- `POST /api/v1/ocr`: PDF/이미지 → Dimensions + GD&T + Text + Tables

**정확도**:
- 치수 추출: 93.75% Recall (논문 기준)
- GD&T 추출: ~90%
- 텍스트 추출: <1% CER

---

## 📊 Comparison Matrix

| 항목 | PaddleOCR API | eDOCr2 API | 결과 |
|-----|--------------|-----------|------|
| **일반 텍스트 인식** | ✅ Good | ✅ Acceptable | 🟡 중복 |
| **치수 인식** | ❌ Poor | ✅ Excellent (93.75%) | ✅ eDOCr2 승 |
| **GD&T 인식** | ❌ No | ✅ Excellent (~90%) | ✅ eDOCr2 승 |
| **다국어 지원** | ✅ Excellent | ⚠️ English only | 🟡 PaddleOCR 강점 |
| **도면 전문성** | ❌ No | ✅ Yes | ✅ eDOCr2 승 |
| **정확도 (도면)** | ~60-70% | ~90-93% | ✅ eDOCr2 승 |

**종합 평가**: eDOCr2가 엔지니어링 도면에서 압도적으로 우수

---

## 💡 Decision Rationale

### 삭제 권장 이유

1. **기능 중복** (80% overlap)
   - eDOCr2의 `extract_text=true` 옵션이 PaddleOCR의 역할 대체 가능
   - 엔지니어링 도면이라는 특수 도메인에서는 전문 모델이 필수

2. **고유 가치 부족**
   - PaddleOCR의 유일한 강점: 다국어 지원
   - 그러나 현재 시스템 요구사항: English engineering drawings
   - 다국어 도면이 필요하다면 VL API (GPT-4V, Claude Sonnet) 사용 가능

3. **시스템 복잡도 증가**
   - 6개 API → 5개 API로 단순화
   - Docker 컨테이너 1개 제거
   - 유지보수 부담 감소

4. **사용자 목표와 불일치**
   - "각각의 API별로 고유한 능력치를 최대치로 끌어오는게 목적"
   - PaddleOCR은 고유 능력이 아닌 범용 능력
   - eDOCr2가 같은 작업을 더 잘 수행

---

## 🔄 Migration Path

### Case 1: 일반 텍스트 OCR이 필요한 경우

**Before** (PaddleOCR):
```python
response = await call_paddleocr(
    file_bytes=image_bytes,
    filename="drawing.jpg",
    min_confidence=0.5
)
texts = [d.text for d in response.detections]
```

**After** (eDOCr2):
```python
response = await call_edocr2(
    file_bytes=image_bytes,
    filename="drawing.pdf",
    extract_text=True,
    extract_dimensions=False,  # Optional
    extract_gdt=False  # Optional
)
texts = response.data["text"]  # Text blocks from eDOCr2
```

### Case 2: 다국어 OCR이 필요한 경우

**Before** (PaddleOCR with Chinese):
```python
# paddleocr-api with lang=ch
response = await call_paddleocr(...)
```

**After** (VL API):
```python
# Use GPT-4V or Claude Sonnet for multilingual OCR
response = await call_vl_api(
    file_bytes=image_bytes,
    prompt="Extract all text from this Chinese engineering drawing"
)
```

---

## 🗑️ Removal Steps

### Step 1: Gateway API 수정

**파일**: `gateway-api/api_server.py`

**변경 사항**:
1. `PADDLEOCR_API_URL` 환경 변수 제거
2. `call_paddleocr()` 함수 제거
3. Health check에서 PaddleOCR 제거
4. 모든 PaddleOCR 호출을 eDOCr2로 대체

### Step 2: Docker Compose 수정

**파일**: `docker-compose.yml`

**변경 사항**:
```yaml
# 삭제
services:
  paddleocr-api:
    ...  # 전체 서비스 제거
```

### Step 3: 디렉토리 제거 (Optional)

```bash
# 백업 (혹시 몰라서)
mv /home/uproot/ax/poc/paddleocr-api /home/uproot/ax/poc/paddleocr-api.DEPRECATED

# 또는 완전 삭제
# rm -rf /home/uproot/ax/poc/paddleocr-api
```

---

## 📋 Testing After Removal

### Test 1: Gateway Health Check

```bash
curl http://localhost:5000/api/v1/health

# Expected: No "paddleocr" in response
```

### Test 2: Text Extraction via eDOCr2

```bash
curl -X POST http://localhost:5001/api/v1/ocr \
  -F "file=@test_drawing.pdf" \
  -F "extract_text=true" \
  -F "extract_dimensions=false" \
  -F "extract_gdt=false"

# Expected: Text extracted successfully
```

### Test 3: Full Pipeline

```bash
curl -X POST http://localhost:5000/api/v1/analyze \
  -F "file=@test_drawing.pdf" \
  -F "extract_text=true"

# Expected: Complete analysis without PaddleOCR
```

---

## ⚠️ Caveats & Considerations

### 1. 다국어 도면이 필요한 경우

**현재 해결책**:
- VL API (GPT-4V, Claude Sonnet) 사용
- 또는 eDOCr2에 multilingual support 추가 (향후)

### 2. PaddleOCR만의 고유 기능이 필요한 경우

현재까지 확인된 고유 기능:
- 없음 (eDOCr2와 VL API가 커버)

### 3. 레거시 코드가 PaddleOCR에 의존하는 경우

**확인 필요**:
```bash
# Gateway 외 다른 곳에서 사용 여부 확인
grep -r "paddleocr" /home/uproot/ax/poc --exclude-dir=paddleocr-api
```

**확인 결과**: Gateway API에서만 사용 (다른 곳 없음)

---

## ✅ Final Decision

**결론**: **PaddleOCR API 삭제**

**실행**:
1. Gateway API에서 PaddleOCR 호출 제거
2. Docker Compose에서 paddleocr-api 서비스 제거
3. 디렉토리 보관 (백업) 또는 삭제

**예상 효과**:
- 시스템 단순화 (6 APIs → 5 APIs)
- 유지보수 부담 감소
- 각 API의 고유 역할 명확화
- 성능 향상 (불필요한 서비스 제거)

---

**작성일**: 2025-11-13
**버전**: 1.0.0
**상태**: DEPRECATED - 삭제 권장
