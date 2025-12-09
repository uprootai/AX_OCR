# Surya OCR API

> **90+ 언어 지원, 레이아웃 분석 포함 OCR**

---

## 기본 정보

| 항목 | 값 |
|------|-----|
| **포트** | 5013 |
| **엔드포인트** | `POST /api/v1/ocr` |
| **GPU 권장** | ✅ (CPU 5배 느림) |
| **VRAM** | 3-5GB |
| **라이선스** | GPL-3.0 |

---

## 파라미터

### languages (인식 언어)

지원하는 90+ 언어 중 사용할 언어를 지정합니다.

- **타입**: string (쉼표 구분)
- **기본값**: `ko,en`
- **예시**: `ko,en`, `ja,en`, `zh,en`

### detect_layout (레이아웃 분석)

페이지의 레이아웃 구조를 분석합니다.

- **타입**: boolean
- **기본값**: `false`
- **팁**: 문서 구조 파악이 필요하면 활성화

### visualize (시각화)

결과 이미지에 텍스트 영역을 표시합니다.

- **타입**: boolean
- **기본값**: `true`

---

## 출력

| 필드 | 타입 | 설명 |
|------|------|------|
| `texts` | array | 인식된 텍스트 배열 |
| `full_text` | string | 전체 텍스트 |
| `layout` | object | 레이아웃 분석 결과 |

### text 객체 구조

```json
{
  "text": "도면 번호: DWG-001",
  "confidence": 0.94,
  "bbox": [100, 50, 300, 80],
  "language": "ko"
}
```

### layout 객체 구조 (detect_layout=true)

```json
{
  "blocks": [
    {
      "type": "title",
      "bbox": [100, 50, 500, 100],
      "text": "도면 제목"
    },
    {
      "type": "table",
      "bbox": [100, 200, 600, 400],
      "rows": 5,
      "cols": 3
    }
  ]
}
```

---

## 지원 언어 (주요)

| 언어 코드 | 언어 |
|-----------|------|
| `ko` | 한국어 |
| `en` | 영어 |
| `ja` | 일본어 |
| `zh` | 중국어 |
| `de` | 독일어 |
| `fr` | 프랑스어 |
| `ru` | 러시아어 |
| `ar` | 아랍어 |

---

## 사용 예시

### curl
```bash
curl -X POST http://localhost:5013/api/v1/ocr \
  -F "file=@document.jpg" \
  -F "languages=ko,en" \
  -F "detect_layout=false"
```

### Python
```python
import requests

files = {"file": open("document.jpg", "rb")}
data = {
    "languages": "ko,en",
    "detect_layout": True,
    "visualize": True
}

response = requests.post(
    "http://localhost:5013/api/v1/ocr",
    files=files,
    data=data
)
print(response.json())
```

---

## 특징

### 장점
- 90+ 언어 지원 (세계 최다)
- 레이아웃 분석 기능
- 복잡한 문서 구조 처리

### 단점
- GPL-3.0 라이선스 (상용 제약)
- 레이아웃 분석 시 메모리 증가

---

## 권장 파이프라인

### 다국어 문서 OCR
```
ImageInput → Surya OCR (detect_layout=true)
```

### 한글/영문 도면
```
ImageInput → Surya OCR (languages=ko,en)
```

---

## 리소스 요구사항

| 항목 | 최소 | 권장 |
|------|------|------|
| VRAM | 2.5GB | 5GB |
| RAM | 4GB | 6GB |
| CPU 코어 | 4 | 8 |
| CUDA | 11.8+ | 12.x |

### 파라미터별 리소스 영향

| 파라미터 | 영향 |
|----------|------|
| detect_layout | OCR만: 3GB, 레이아웃: 5GB |

---

**마지막 업데이트**: 2025-12-09
