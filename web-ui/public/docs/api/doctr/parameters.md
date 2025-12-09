# DocTR API

> **2단계 파이프라인 OCR (Detection + Recognition)**

---

## 기본 정보

| 항목 | 값 |
|------|-----|
| **포트** | 5014 |
| **엔드포인트** | `POST /api/v1/ocr` |
| **GPU 권장** | ✅ (CPU 4배 느림) |
| **VRAM** | 1.5-2.5GB |
| **라이선스** | Apache 2.0 |

---

## 파라미터

### det_arch (Detection 모델)

텍스트 영역 검출에 사용할 모델입니다.

| 값 | 설명 | VRAM |
|----|------|------|
| `db_resnet50` | ResNet50 기반 (기본) | ~2.5GB |
| `db_mobilenet_v3_large` | MobileNet 기반 | ~1.5GB |
| `linknet_resnet18` | LinkNet 기반 | ~2GB |

- **타입**: select
- **기본값**: `db_resnet50`

### reco_arch (Recognition 모델)

텍스트 인식에 사용할 모델입니다.

| 값 | 설명 | 특징 |
|----|------|------|
| `crnn_vgg16_bn` | CRNN VGG16 (기본) | 범용 |
| `crnn_mobilenet_v3_small` | CRNN MobileNet | 빠름 |
| `master` | MASTER 모델 | 정확 |

- **타입**: select
- **기본값**: `crnn_vgg16_bn`

### straighten_pages (페이지 정렬)

기울어진 페이지를 자동으로 정렬합니다.

- **타입**: boolean
- **기본값**: `false`
- **팁**: 스캔 문서에 유용

### export_as_xml (XML 내보내기)

결과를 XML 형식으로도 제공합니다.

- **타입**: boolean
- **기본값**: `false`

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
| `pages` | array | 페이지별 상세 결과 |

### text 객체 구조

```json
{
  "text": "DIMENSION: 50mm",
  "confidence": 0.91,
  "bbox": [[100, 200], [300, 200], [300, 230], [100, 230]]
}
```

### pages 객체 구조

```json
{
  "page_idx": 0,
  "dimensions": [1920, 1080],
  "blocks": [
    {
      "lines": [
        {
          "words": [
            {"value": "DIMENSION:", "confidence": 0.95},
            {"value": "50mm", "confidence": 0.88}
          ]
        }
      ]
    }
  ]
}
```

---

## 사용 예시

### curl
```bash
curl -X POST http://localhost:5014/api/v1/ocr \
  -F "file=@document.jpg" \
  -F "det_arch=db_resnet50" \
  -F "reco_arch=crnn_vgg16_bn"
```

### Python
```python
import requests

files = {"file": open("document.jpg", "rb")}
data = {
    "det_arch": "db_resnet50",
    "reco_arch": "crnn_vgg16_bn",
    "straighten_pages": False,
    "visualize": True
}

response = requests.post(
    "http://localhost:5014/api/v1/ocr",
    files=files,
    data=data
)
print(response.json())
```

---

## 2단계 파이프라인

```
입력 이미지
    ↓
[Detection Stage]
  - 텍스트 영역 검출
  - 바운딩 박스 생성
    ↓
[Recognition Stage]
  - 각 영역 텍스트 인식
  - 신뢰도 계산
    ↓
결과 출력
```

---

## 모델 조합 권장

| 용도 | Detection | Recognition |
|------|-----------|-------------|
| **빠른 처리** | mobilenet_v3_large | crnn_mobilenet_v3_small |
| **균형** | db_resnet50 | crnn_vgg16_bn |
| **정확도** | db_resnet50 | master |

---

## 권장 파이프라인

### 문서 OCR
```
ImageInput → DocTR
```

### 정밀 도면 분석
```
ImageInput → ESRGAN(2x) → DocTR
```

---

## 리소스 요구사항

| 항목 | 최소 | 권장 |
|------|------|------|
| VRAM | 1.5GB | 2.5GB |
| RAM | 2GB | 4GB |
| CPU 코어 | 4 | 8 |
| CUDA | 11.8+ | 12.x |

### 파라미터별 리소스 영향

| 파라미터 | 영향 |
|----------|------|
| det_arch | mobilenet: 1.5GB, resnet50: 2.5GB |

---

**마지막 업데이트**: 2025-12-09
