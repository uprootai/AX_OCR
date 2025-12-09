# eDOCr2 API

> **기계 도면 특화 OCR - 치수, GD&T, 텍스트 자동 추출**

---

## 기본 정보

| 항목 | 값 |
|------|-----|
| **포트** | 5002 |
| **엔드포인트** | `POST /api/v1/ocr` |
| **GPU 권장** | ✅ (CPU 3배 느림) |
| **VRAM** | 2-4GB |

---

## 파라미터

### version (버전 선택)

| 값 | 설명 |
|----|------|
| `v1` | 레거시 버전 (포트 5001) |
| `v2` | 개선된 버전 (기본) |

- **타입**: select
- **기본값**: `v2`

### language (인식 언어)

| 값 | 설명 |
|----|------|
| `ko` | 한국어 |
| `en` | 영어 |
| `ko+en` | 한국어+영어 (기본) |
| `ja` | 일본어 |
| `zh` | 중국어 |

- **타입**: select
- **기본값**: `ko+en`

### extract_dimensions (치수 추출)

치수 정보를 추출합니다 (예: 85.5mm, R20, C2).

- **타입**: boolean
- **기본값**: `true`

### extract_gdt (GD&T 추출)

기하공차 정보를 추출합니다 (평행도, 직각도, 위치도 등).

- **타입**: boolean
- **기본값**: `true`

### extract_text (텍스트 추출)

일반 텍스트를 추출합니다 (도면 번호, 재질, 주석 등).

- **타입**: boolean
- **기본값**: `true`

### extract_tables (테이블 추출)

부품표 등 테이블 데이터를 추출합니다.

- **타입**: boolean
- **기본값**: `false`
- **주의**: 활성화 시 메모리 2배 사용

### cluster_threshold (클러스터링 임계값)

텍스트 그룹화를 위한 거리 임계값입니다.

- **타입**: number (10 ~ 200)
- **기본값**: `50`
- **팁**: 작은 글자가 많으면 낮추기

### visualize (시각화)

결과 이미지에 OCR 결과를 표시합니다.

- **타입**: boolean
- **기본값**: `true`

---

## 출력

| 필드 | 타입 | 설명 |
|------|------|------|
| `dimensions` | array | 추출된 치수 목록 |
| `gdt_symbols` | array | GD&T 기호 목록 |
| `text_blocks` | array | 텍스트 블록 목록 |
| `tables` | array | 테이블 데이터 |
| `visualized_image` | string | 시각화 이미지 (base64) |

### dimension 객체 구조

```json
{
  "type": "linear",
  "value": "85.5",
  "unit": "mm",
  "tolerance": "+0.1/-0.05",
  "confidence": 0.92,
  "bbox": [100, 200, 150, 220]
}
```

### gdt_symbol 객체 구조

```json
{
  "type": "parallelism",
  "value": "0.05",
  "datum": "A",
  "confidence": 0.88,
  "bbox": [200, 300, 280, 340]
}
```

---

## 사용 예시

### curl
```bash
curl -X POST http://localhost:5002/api/v1/ocr \
  -F "file=@drawing.jpg" \
  -F "language=ko+en" \
  -F "extract_dimensions=true" \
  -F "extract_gdt=true"
```

### Python
```python
import requests

files = {"file": open("drawing.jpg", "rb")}
data = {
    "language": "ko+en",
    "extract_dimensions": True,
    "extract_gdt": True,
    "extract_text": True,
    "visualize": True
}

response = requests.post(
    "http://localhost:5002/api/v1/ocr",
    files=files,
    data=data
)
print(response.json())
```

---

## 추출 가능한 치수 유형

| 유형 | 예시 | 설명 |
|------|------|------|
| `linear` | 85.5mm | 선형 치수 |
| `diameter` | ⌀50 | 직경 |
| `radius` | R20 | 반경 |
| `angle` | 45° | 각도 |
| `chamfer` | C2 | 모따기 |
| `tolerance` | ±0.1 | 공차 |

## 추출 가능한 GD&T 기호

| 기호 | 이름 | 설명 |
|------|------|------|
| ⏥ | 평면도 | Flatness |
| ⌭ | 원통도 | Cylindricity |
| ⊕ | 위치도 | Position |
| ⊥ | 수직도 | Perpendicularity |
| ∥ | 평행도 | Parallelism |

---

## 권장 파이프라인

### 기본 치수 추출
```
ImageInput → eDOCr2
```

### 정밀 분석 (YOLO 선행)
```
ImageInput → YOLO → eDOCr2 → SkinModel
```

### 저해상도 도면
```
ImageInput → ESRGAN(2x) → eDOCr2
```

---

## 리소스 요구사항

| 항목 | 최소 | 권장 |
|------|------|------|
| VRAM | 1.5GB | 2GB |
| RAM | 2GB | 4GB |
| CPU 코어 | 4 | 8 |
| CUDA | 11.8+ | 12.x |

### 파라미터별 리소스 영향

| 파라미터 | 영향 |
|----------|------|
| extract_tables | 테이블 추출 시 메모리 2배 |

---

**마지막 업데이트**: 2025-12-09
