# Analyze 페이지 문제 분석 보고서

테스트 시간: 2025-10-27 11:22

## 🔍 발견된 문제

### 1️⃣ EDGNet API - PDF 파일 처리 불가

**증상:**
- 사용자가 PDF 파일 업로드 후 분석 버튼 클릭
- UI가 멈춘 것처럼 보임

**로그 분석:**
```
2025-10-27 11:22:27 - API Gateway - Processing sample1_interm_shaft.pdf
2025-10-27 11:22:27 - EDGNet API - HTTP/1.1 400 Bad Request
2025-10-27 11:22:27 - ERROR: EDGNet API call failed
2025-10-27 11:22:29 - eDOCr2 API - HTTP/1.1 200 OK ✓
2025-10-27 11:22:31 - Skin Model API - HTTP/1.1 200 OK ✓
2025-10-27 11:22:31 - Gateway API - HTTP/1.1 200 OK (전체 응답)
```

**원인:**
- **EDGNet API는 이미지만 처리 가능** (JPG, PNG 등)
- PDF 파일을 EDGNet에 전달하면 400 Bad Request 발생
- Gateway는 부분 실패해도 200 OK 반환 (다른 API는 성공)

**검증:**
```bash
# PDF 파일 테스트 - EDGNet 실패
curl -X POST http://localhost:8000/api/v1/process \
  -F "file=sample1_interm_shaft.pdf" \
  -F "use_segmentation=true"
→ EDGNet: 400 Bad Request

# 이미지 파일 테스트 - 모두 성공
curl -X POST http://localhost:8000/api/v1/process \
  -F "file=sample2_interm_shaft.jpg" \
  -F "use_segmentation=true"
→ 모든 API: 200 OK ✓
```

---

## 📊 API 파일 형식 지원

| API | PDF | JPG/PNG | 비고 |
|-----|-----|---------|------|
| **eDOCr2** (OCR) | ✅ | ✅ | 모든 형식 지원 |
| **EDGNet** (Segmentation) | ❌ | ✅ | **이미지만 지원** |
| **Skin Model** (Tolerance) | N/A | N/A | JSON 입력 (파일 무관) |
| **Gateway** (통합) | ⚠️ | ✅ | EDGNet 사용 시 이미지 권장 |

---

## 🎯 Analyze 페이지 기능 설명

### ✅ Analyze 페이지는 **통합 테스트**

**동작 방식:**
```
[Analyze 페이지]
      ↓
   Gateway API (/api/v1/process)
      ↓
   ┌─────┬─────────┬──────────┐
   ↓     ↓         ↓          ↓
eDOCr2  EDGNet  Skin Model  결과 통합
  OCR   세그멘테이션  공차분석
```

**특징:**
- **하나의 API 호출**로 모든 분석 수행
- OCR + 세그멘테이션 + 공차 분석을 순차 실행
- 결과를 통합하여 반환

### ❌ Quick Test는 **개별 테스트**

**Quick Test 링크:**
- • eDOCr2 → `/test/edocr2` (OCR만 테스트)
- • EDGNet → `/test/edgnet` (세그멘테이션만 테스트)
- • Skin Model → `/test/skinmodel` (공차 분석만 테스트)
- • Gateway → `/test/gateway` (통합 테스트)

**차이점:**
| 구분 | Analyze 페이지 | Test 페이지 |
|-----|---------------|------------|
| API 호출 | Gateway 1회 | 개별 API 1회 |
| 분석 범위 | 통합 (OCR+Seg+Tol) | 단일 기능 |
| 옵션 제어 | 체크박스로 선택 | API별 상세 옵션 |
| 디버깅 | 결과 위주 | Request/Response 상세 |
| 용도 | 프로덕션 분석 | API 테스트/디버깅 |

---

## 🔧 해결 방안

### 즉시 조치 (권장)

#### 1. 샘플 파일 기본값 변경
- PDF → JPG로 변경
- 이미지 파일을 기본 샘플로 제공

#### 2. Analyze 페이지에 안내 추가
```
┌─────────────────────────────────────┐
│ ℹ️  통합 분석 안내                    │
│                                     │
│ • 이 페이지는 모든 분석을 한번에 수행합니다 │
│ • 세그멘테이션 옵션 사용 시 이미지 권장     │
│ • 개별 API 테스트는 Test 메뉴 이용      │
└─────────────────────────────────────┘
```

#### 3. 파일 형식 검증 추가
```typescript
if (options.segmentation && file.type === 'application/pdf') {
  alert('세그멘테이션 분석은 이미지 파일만 지원합니다.\nJPG 또는 PNG 파일을 선택해주세요.');
  return;
}
```

#### 4. 에러 메시지 개선
```
EDGNet 분석 실패: PDF 파일은 지원하지 않습니다.
이미지 파일(JPG, PNG)을 선택하거나 세그멘테이션 옵션을 해제하세요.
```

---

## 📝 사용자 가이드

### Analyze 페이지 사용법

#### ✅ 권장: 이미지 파일 + 모든 옵션
```
파일: sample2_interm_shaft.jpg
옵션:
  ☑ OCR 분석
  ☑ 세그멘테이션
  ☑ 공차 분석
  ☐ 시각화

→ 모든 기능 정상 작동 ✓
```

#### ⚠️ 주의: PDF 파일 + 세그멘테이션
```
파일: sample1_interm_shaft.pdf
옵션:
  ☑ OCR 분석
  ☑ 세그멘테이션  ← EDGNet 실패
  ☑ 공차 분석
  
→ OCR, 공차는 성공하지만 세그멘테이션 실패
```

#### ✅ 대안: PDF 파일 + OCR/공차만
```
파일: sample1_interm_shaft.pdf
옵션:
  ☑ OCR 분석
  ☐ 세그멘테이션  ← 해제
  ☑ 공차 분석
  
→ 모든 기능 정상 작동 ✓
```

---

## 🎯 결론

1. **Analyze 페이지 = Gateway API 통합 테스트**
   - 한 번에 모든 분석 수행
   - 프로덕션 레벨 분석 용도

2. **Quick Test = 개별 API 테스트**
   - 각 API를 독립적으로 테스트
   - 디버깅 및 개발 용도

3. **EDGNet은 이미지만 지원**
   - PDF 파일 사용 시 세그멘테이션 옵션 해제 필요
   - 또는 이미지 파일 사용 권장

4. **사용자에게 명확한 안내 필요**
   - 파일 형식 제한 표시
   - 옵션별 지원 형식 안내
   - 에러 메시지 개선
