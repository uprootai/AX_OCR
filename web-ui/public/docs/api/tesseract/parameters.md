# Tesseract OCR API

> **Google Tesseract 기반 오픈소스 OCR 엔진**

---

## 기본 정보

| 항목 | 값 |
|------|-----|
| **포트** | 5008 |
| **엔드포인트** | `POST /api/v1/ocr` |
| **GPU 필요** | ❌ CPU 전용 |
| **RAM** | ~1GB |

---

## 파라미터

### lang (인식 언어)

| 값 | 설명 |
|----|------|
| `eng` | 영어 (기본) |
| `kor` | 한국어 |
| `jpn` | 일본어 |
| `chi_sim` | 중국어 간체 |
| `chi_tra` | 중국어 번체 |
| `eng+kor` | 영어+한국어 |

- **타입**: select
- **기본값**: `eng`

### psm (Page Segmentation Mode)

페이지 분할 방식을 설정합니다.

| 값 | 설명 |
|----|------|
| `0` | OSD (Orientation and Script Detection) |
| `1` | 자동 페이지 분할 + OSD |
| `3` | 자동 페이지 분할 (기본) |
| `4` | 단일 열 텍스트 |
| `6` | 단일 텍스트 블록 |
| `7` | 단일 텍스트 라인 |
| `11` | 희소 텍스트 |
| `12` | OSD 포함 희소 텍스트 |
| `13` | 단일 문자 |

- **타입**: select
- **기본값**: `3`
- **팁**: 도면 치수는 `6` 또는 `7` 권장

### output_type (출력 형식)

| 값 | 설명 |
|----|------|
| `string` | 문자열만 반환 |
| `data` | 상세 데이터 (기본) |
| `dict` | 딕셔너리 형태 |

- **타입**: select
- **기본값**: `data`

---

## 출력

| 필드 | 타입 | 설명 |
|------|------|------|
| `texts` | array | 인식된 텍스트 목록 |
| `full_text` | string | 전체 텍스트 |

### text 객체 구조

```json
{
  "text": "12.5mm",
  "confidence": 0.89,
  "bbox": [100, 200, 150, 220]
}
```

---

## 사용 예시

### curl
```bash
curl -X POST http://localhost:5008/api/v1/ocr \
  -F "file=@document.jpg" \
  -F "lang=eng+kor" \
  -F "psm=3"
```

### Python
```python
import requests

files = {"file": open("document.jpg", "rb")}
data = {
    "lang": "eng+kor",
    "psm": "3"
}

response = requests.post(
    "http://localhost:5008/api/v1/ocr",
    files=files,
    data=data
)
print(response.json())
```

---

## 장단점

### 장점
- 오픈소스 (Apache 2.0)
- CPU만으로 빠른 처리
- 100+ 언어 지원
- 가벼운 리소스 사용

### 단점
- 손글씨에 약함
- 노이즈 이미지에 민감
- 복잡한 레이아웃 처리 제한

---

## 권장 파이프라인

### 문서 텍스트 추출
```
ImageInput → Tesseract (psm=3)
```

### OCR 앙상블 참여
```
ImageInput → OCR Ensemble (Tesseract 15% 가중치)
```

---

## 리소스 요구사항

| 항목 | 최소 | 권장 |
|------|------|------|
| RAM | 512MB | 1GB |
| CPU 코어 | 2 | 4 |
| 디스크 | 500MB | 1GB |

---

**마지막 업데이트**: 2025-12-09
