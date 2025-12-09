# ESRGAN API

> **Real-ESRGAN 기반 이미지 업스케일링**

---

## 기본 정보

| 항목 | 값 |
|------|-----|
| **포트** | 5010 |
| **엔드포인트** | `POST /api/v1/upscale` |
| **GPU 필수** | ✅ (CPU 20배 느림) |
| **VRAM** | 4-6GB |

---

## 파라미터

### scale (업스케일 배율)

| 값 | 설명 | 출력 해상도 | VRAM |
|----|------|------------|------|
| `2` | 2배 업스케일 | 2000px → 4000px | 4GB |
| `4` | 4배 업스케일 | 2000px → 8000px | 6GB |

- **타입**: select
- **기본값**: `2`
- **주의**: 4x는 처리 시간 5배, 출력 파일 16배

### model (모델 선택)

| 값 | 용도 | 특징 |
|----|------|------|
| `RealESRGAN_x4plus` | 일반 이미지 | 품질 우선 |
| `RealESRGAN_x2plus` | 2배 전용 | 속도 우선 |
| `realesr-animevideov3` | 애니메이션 | 선명한 엣지 |

- **타입**: select
- **기본값**: `RealESRGAN_x4plus`

### denoise_strength (노이즈 제거 강도)

업스케일 시 노이즈 제거 정도입니다.

- **타입**: number (0.0 ~ 1.0)
- **기본값**: `0.5`
- **팁**: 스캔 도면은 0.7 권장

### face_enhance (얼굴 향상)

얼굴 영역 품질 향상 (도면에서는 비활성화 권장)

- **타입**: boolean
- **기본값**: `false`

### tile_size (타일 크기)

메모리 제한 시 타일 처리 크기입니다.

- **타입**: number
- **기본값**: `0` (자동)
- **팁**: VRAM 부족 시 `256` 또는 `128` 설정

---

## 출력

| 필드 | 타입 | 설명 |
|------|------|------|
| `image` | base64 | 업스케일된 이미지 |
| `original_size` | object | 원본 크기 { width, height } |
| `upscaled_size` | object | 결과 크기 { width, height } |
| `processing_time` | number | 처리 시간 (초) |

---

## 사용 예시

### curl
```bash
curl -X POST http://localhost:5010/api/v1/upscale \
  -F "file=@low_res_drawing.jpg" \
  -F "scale=2" \
  -F "denoise_strength=0.5"
```

### Python
```python
import requests

files = {"file": open("low_res_drawing.jpg", "rb")}
data = {"scale": 2, "denoise_strength": 0.5}

response = requests.post(
    "http://localhost:5010/api/v1/upscale",
    files=files,
    data=data
)
print(response.json())
```

---

## 권장 파이프라인

### 저해상도 도면 OCR 개선
```
ImageInput → ESRGAN(2x) → eDOCr2
```

### 고정밀 분석 (4x 주의)
```
ImageInput → ESRGAN(4x) → OCR Ensemble
```

**주의**: 4x 업스케일 후 OCR은 처리 시간이 매우 길어집니다 (타임아웃 10분).

---

## 성능 벤치마크

| 입력 크기 | 2x 시간 | 4x 시간 | 출력 크기 |
|----------|---------|---------|----------|
| 1000x1000 | 2초 | 8초 | 4MB/16MB |
| 2000x2000 | 8초 | 35초 | 16MB/64MB |
| 4000x4000 | 30초 | 150초 | 64MB/256MB |

---

## 리소스 요구사항

| 항목 | 최소 | 권장 |
|------|------|------|
| VRAM | 4GB | 6GB |
| RAM | 4GB | 8GB |
| CPU 코어 | 4 | 8 |
| CUDA | 11.8+ | 12.x |

---

**마지막 업데이트**: 2025-12-09
