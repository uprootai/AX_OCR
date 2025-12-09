# VL (Vision-Language) API

> **멀티모달 AI - 이미지 이해 및 자연어 질의응답**

---

## 기본 정보

| 항목 | 값 |
|------|-----|
| **포트** | 5004 |
| **엔드포인트** | `POST /api/v1/analyze` |
| **GPU 필수** | ✅ |
| **VRAM** | 6-10GB |

---

## 입력

이 API는 JSON 형식의 입력을 받습니다.

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `image` | string | ✅ | 이미지 (base64) |
| `prompt` | string | ❌ | 질문/지시사항 |

---

## 파라미터

### model (모델 선택)

| 값 | 설명 | VRAM |
|----|------|------|
| `qwen-vl` | Qwen2-VL (기본) | ~8GB |
| `llava` | LLaVA | ~6GB |
| `cogvlm` | CogVLM | ~10GB |
| `local` | 로컬 모델 | 가변 |

- **타입**: select
- **기본값**: `qwen-vl`

### temperature (창의성)

응답의 다양성을 조절합니다.

- **타입**: number (0.0 ~ 2.0)
- **기본값**: `0.7`
- **팁**: 0에 가까울수록 일관적, 높을수록 창의적

---

## 출력

| 필드 | 타입 | 설명 |
|------|------|------|
| `response` | string | AI 응답 텍스트 |
| `analysis` | object | 상세 분석 결과 |

### analysis 객체 구조

```json
{
  "detected_objects": ["bearing", "shaft", "housing"],
  "text_found": ["DWG-001", "Rev.A"],
  "drawing_type": "assembly",
  "confidence": 0.89
}
```

---

## 사용 예시

### Python
```python
import requests
import base64

# 이미지를 base64로 인코딩
with open("drawing.jpg", "rb") as f:
    image_b64 = base64.b64encode(f.read()).decode()

data = {
    "image": image_b64,
    "prompt": "이 도면에서 주요 치수들을 나열해주세요",
    "model": "qwen-vl",
    "temperature": 0.7
}

response = requests.post(
    "http://localhost:5004/api/v1/analyze",
    json=data
)
print(response.json())
```

---

## 활용 예시

### 도면 분석
```
프롬프트: "이 도면의 주요 부품들을 설명해주세요"
응답: "이 도면은 베어링 하우징 어셈블리입니다. 주요 부품:
1. 메인 하우징 (⌀120mm)
2. 베어링 (6205)
3. 샤프트 (⌀25mm)..."
```

### 설계 검토
```
프롬프트: "이 설계에서 잠재적인 문제점이 있나요?"
응답: "다음 사항을 검토해보세요:
1. 베어링 시트의 공차가 H7로 지정되어 있으나...
2. 리브 구조가 없어 강성이 부족할 수 있습니다..."
```

### 치수 추출
```
프롬프트: "모든 직경 치수를 나열해주세요"
응답: "직경 치수 목록:
- ⌀120mm (하우징 외경)
- ⌀80mm (베어링 시트)
- ⌀25mm (샤프트)..."
```

---

## TextInput 연동

BlueprintFlow에서 TextInput 노드와 연결하여 동적 프롬프트를 사용할 수 있습니다.

```
ImageInput → VL ← TextInput (prompt)
```

TextInput에서 입력한 텍스트가 VL의 prompt로 전달됩니다.

---

## 권장 파이프라인

### 도면 이해
```
ImageInput → VL (prompt="이 도면을 설명해주세요")
```

### 치수 검증
```
ImageInput → eDOCr2 → VL (prompt="추출된 치수가 맞는지 확인해주세요")
```

### 품질 검사
```
ImageInput → YOLO → VL (prompt="검출된 심볼들이 올바른지 확인해주세요")
```

---

## 리소스 요구사항

| 항목 | 최소 | 권장 |
|------|------|------|
| VRAM | 6GB | 8GB |
| RAM | 12GB | 16GB |
| CPU 코어 | 8 | 16 |
| CUDA | 11.8+ | 12.x |

### 모델별 리소스 비교

| 모델 | VRAM | 속도 | 정확도 |
|------|------|------|--------|
| qwen-vl | 8GB | 보통 | 높음 |
| llava | 6GB | 빠름 | 보통 |
| cogvlm | 10GB | 느림 | 최고 |

---

**마지막 업데이트**: 2025-12-09
