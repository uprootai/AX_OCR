# EasyOCR API

> **80+ 언어 지원, CPU 친화적, 한국어 특화 OCR**

---

## 기본 정보

| 항목 | 값 |
|------|-----|
| **포트** | 5015 |
| **엔드포인트** | `POST /api/v1/ocr` |
| **GPU 선택** | ⚡ CPU에서도 합리적 속도 |
| **VRAM** | 2-4GB |
| **라이선스** | Apache 2.0 |

---

## 파라미터

### languages (인식 언어)

사용할 언어를 쉼표로 구분하여 지정합니다.

- **타입**: string
- **기본값**: `ko,en`
- **예시**: `ko,en`, `ja,en`, `ch_sim,en`

### 주요 지원 언어

| 코드 | 언어 |
|------|------|
| `ko` | 한국어 |
| `en` | 영어 |
| `ja` | 일본어 |
| `ch_sim` | 중국어 간체 |
| `ch_tra` | 중국어 번체 |
| `th` | 태국어 |
| `vi` | 베트남어 |

### detail (상세 결과)

바운딩 박스와 신뢰도를 포함한 상세 결과를 반환합니다.

- **타입**: boolean
- **기본값**: `true`

### paragraph (문단 결합)

인접한 텍스트를 문단 단위로 결합합니다.

- **타입**: boolean
- **기본값**: `false`
- **팁**: 문서 텍스트 추출 시 유용

### batch_size (배치 크기)

동시 처리할 이미지 영역 수입니다.

- **타입**: number (1 ~ 32)
- **기본값**: `1`
- **팁**: GPU 메모리 여유 시 8-16 권장

### visualize (시각화)

결과 이미지에 텍스트 영역을 표시합니다.

- **타입**: boolean
- **기본값**: `true`

---

## 출력

| 필드 | 타입 | 설명 |
|------|------|------|
| `texts` | array | 인식된 텍스트 배열 (bbox 포함) |
| `full_text` | string | 전체 텍스트 |

### text 객체 구조 (detail=true)

```json
{
  "text": "도면 치수",
  "confidence": 0.89,
  "bbox": [[100, 200], [200, 200], [200, 230], [100, 230]]
}
```

### text 객체 구조 (detail=false)

```json
{
  "text": "도면 치수"
}
```

---

## 사용 예시

### curl
```bash
curl -X POST http://localhost:5015/api/v1/ocr \
  -F "file=@document.jpg" \
  -F "languages=ko,en" \
  -F "detail=true"
```

### Python
```python
import requests

files = {"file": open("document.jpg", "rb")}
data = {
    "languages": "ko,en",
    "detail": True,
    "paragraph": False,
    "batch_size": 1,
    "visualize": True
}

response = requests.post(
    "http://localhost:5015/api/v1/ocr",
    files=files,
    data=data
)
print(response.json())
```

---

## 특징

### 장점
- 80+ 언어 지원
- 한국어 인식 우수
- CPU에서도 합리적 성능
- 간편한 사용법
- Apache 2.0 라이선스

### 단점
- 복잡한 레이아웃에 약함
- 손글씨에 제한적

---

## 권장 파이프라인

### 한글 문서 OCR
```
ImageInput → EasyOCR (languages=ko,en)
```

### 빠른 텍스트 추출
```
ImageInput → EasyOCR (paragraph=true)
```

---

## 리소스 요구사항

| 항목 | 최소 | 권장 |
|------|------|------|
| VRAM | 1.5GB | 2GB |
| RAM | 2GB | 3GB |
| CPU 코어 | 4 | 8 |
| CUDA | 11.0+ | 12.x |

### 파라미터별 리소스 영향

| 파라미터 | 영향 |
|----------|------|
| batch_size | batch1: 2GB, batch8: 4GB |

---

**마지막 업데이트**: 2025-12-09
