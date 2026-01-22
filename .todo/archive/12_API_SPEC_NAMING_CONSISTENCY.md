# API Spec 네이밍 일관성 작업

> **생성일**: 2026-01-19
> **우선순위**: P3 (낮음 - 기능에 영향 없음)
> **상태**: 정보 기록용

---

## 현황 분석

### 현재 API Spec 파일 목록 (24개)

| 파일명 | 네이밍 패턴 | ID | 일관성 |
|--------|-------------|-----|--------|
| blueprint-ai-bom.yaml | kebab-case | blueprint-ai-bom | ✅ |
| designchecker.yaml | lowercase | designchecker | ⚠️ |
| doctr.yaml | lowercase | doctr | ✅ |
| easyocr.yaml | lowercase | easyocr | ✅ |
| edgnet.yaml | lowercase | edgnet | ✅ |
| edocr2.yaml | lowercase | edocr2 | ✅ |
| esrgan.yaml | lowercase | esrgan | ✅ |
| excelexport.yaml | lowercase | excelexport | ⚠️ |
| gtcomparison.yaml | lowercase | gtcomparison | ⚠️ |
| knowledge.yaml | lowercase | knowledge | ✅ |
| linedetector.yaml | lowercase | linedetector | ⚠️ |
| ocr_ensemble.yaml | snake_case | ocr_ensemble | ⚠️ |
| paddleocr.yaml | lowercase | paddleocr | ✅ |
| pdfexport.yaml | lowercase | pdfexport | ⚠️ |
| pidanalyzer.yaml | lowercase | pidanalyzer | ⚠️ |
| pidcomposer.yaml | lowercase | pidcomposer | ⚠️ |
| pidfeatures.yaml | lowercase | pidfeatures | ⚠️ |
| skinmodel.yaml | lowercase | skinmodel | ✅ |
| suryaocr.yaml | lowercase | suryaocr | ✅ |
| tesseract.yaml | lowercase | tesseract | ✅ |
| trocr.yaml | lowercase | trocr | ✅ |
| verificationqueue.yaml | lowercase | verificationqueue | ⚠️ |
| vl.yaml | lowercase | vl | ✅ |
| yolo.yaml | lowercase | yolo | ✅ |

### 네이밍 패턴 분석

**선호 패턴**: `lowercase.yaml` (하이픈 없음)

**이유**:
1. 대부분의 API가 이미 lowercase 패턴 사용
2. metadata.id와 파일명 일치 용이
3. 파일 시스템 호환성 우수

### 변경 히스토리

| 이전 파일명 | 현재 파일명 | 변경 이유 |
|-------------|-------------|-----------|
| design-checker.yaml | designchecker.yaml | 일관성 |
| line-detector.yaml | linedetector.yaml | 일관성 |
| pid-composer.yaml | pidcomposer.yaml | 일관성 |
| ocr-ensemble.yaml | ocr_ensemble.yaml | 부분 변경 |

---

## 권장 사항

### 유지할 현재 상태 (변경 불필요)

기능에 영향이 없으므로 현재 상태 유지 권장:
- 코드가 `metadata.id`를 기준으로 동작
- 파일명은 인간 가독성을 위한 것

### 향후 새 API 추가 시 규칙

1. **파일명**: `{apiname}.yaml` (모두 소문자, 하이픈/언더스코어 없음)
2. **metadata.id**: 파일명과 동일
3. **예외**: 복합어가 모호한 경우 하이픈 허용 (예: `blueprint-ai-bom.yaml`)

---

## 코드 참조 위치

API 스펙 파일 로딩 로직:

```typescript
// web-ui/src/services/specService.ts
export async function loadAPISpec(apiId: string): Promise<APISpec | null> {
  // apiId로 스펙 조회 (파일명이 아닌 metadata.id 기준)
}
```

```python
# gateway-api/utils/helpers.py
def load_api_spec(api_id: str) -> dict:
    # api_specs/ 디렉토리에서 metadata.id 매칭
```

---

## 결론

**작업 필요 없음** - 현재 상태 유지

네이밍 불일치가 있지만:
1. 기능에 영향 없음
2. 리팩토링 비용 > 이점
3. 향후 새 API 추가 시 규칙만 따르면 됨

---

*마지막 업데이트: 2026-01-19*
