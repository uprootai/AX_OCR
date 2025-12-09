# SkinModel API

> **FEM 기반 기하공차 예측 및 제조 가능성 분석**

---

## 기본 정보

| 항목 | 값 |
|------|-----|
| **포트** | 5003 |
| **엔드포인트** | `POST /api/v1/tolerance` |
| **GPU 선택** | ⚡ CPU로도 빠름 |
| **VRAM** | ~1GB |

---

## 입력

이 API는 JSON 형식의 입력을 받습니다.

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `dimensions` | array | ✅ | 치수 정보 리스트 |
| `material` | object/string | ✅ | 재질 정보 |

### dimensions 객체 구조

```json
{
  "type": "linear",
  "value": 85.5,
  "tolerance": 0.1,
  "unit": "mm"
}
```

---

## 파라미터

### material_type (재질 타입)

| 값 | 설명 |
|----|------|
| `aluminum` | 알루미늄 |
| `steel` | 철강 (기본) |
| `stainless` | 스테인리스 |
| `titanium` | 티타늄 |
| `plastic` | 플라스틱 |

- **타입**: select
- **기본값**: `steel`

### manufacturing_process (제조 공정)

| 값 | 설명 |
|----|------|
| `machining` | 기계 가공 (기본) |
| `casting` | 주조 |
| `3d_printing` | 3D 프린팅 |
| `welding` | 용접 |
| `sheet_metal` | 판금 |

- **타입**: select
- **기본값**: `machining`

### correlation_length (상관 길이)

Random Field 시뮬레이션의 상관 길이입니다.

- **타입**: number (0.1 ~ 10.0)
- **기본값**: `1.0`
- **팁**: 큰 부품은 높은 값, 정밀 부품은 낮은 값

### task (분석 작업)

| 값 | 설명 |
|----|------|
| `tolerance` | 공차 예측 (기본) |
| `validate` | 규격 검증 |
| `manufacturability` | 제조 가능성 평가 |

- **타입**: select
- **기본값**: `tolerance`

---

## 출력

| 필드 | 타입 | 설명 |
|------|------|------|
| `tolerance_prediction` | object | 예측된 공차 값 |
| `manufacturability` | object | 제조 가능성 평가 |
| `assemblability` | object | 조립 가능성 평가 |
| `visualized_image` | string | 공차 시각화 이미지 |

### tolerance_prediction 객체 구조

```json
{
  "predicted_tolerance": 0.05,
  "confidence": 0.88,
  "grade": "IT7",
  "recommendation": "현재 공차는 machining 공정에 적합합니다"
}
```

### manufacturability 객체 구조

```json
{
  "score": 0.85,
  "feasible": true,
  "cost_factor": 1.2,
  "issues": [],
  "suggestions": ["공차를 IT8로 완화하면 비용 20% 절감 가능"]
}
```

---

## 사용 예시

### Python
```python
import requests

data = {
    "dimensions": [
        {"type": "linear", "value": 85.5, "tolerance": 0.1, "unit": "mm"},
        {"type": "diameter", "value": 50.0, "tolerance": 0.05, "unit": "mm"}
    ],
    "material": {"type": "steel", "grade": "S45C"},
    "material_type": "steel",
    "manufacturing_process": "machining",
    "task": "tolerance"
}

response = requests.post(
    "http://localhost:5003/api/v1/tolerance",
    json=data
)
print(response.json())
```

---

## 분석 작업 비교

| 작업 | 용도 | 시간 |
|------|------|------|
| tolerance | 공차 예측 | 빠름 |
| validate | ISO/ASME 검증 | 빠름 |
| manufacturability | 제조 가능성 | 보통 |

---

## 권장 파이프라인

### 기본 공차 분석
```
ImageInput → eDOCr2 → SkinModel (task=tolerance)
```

### 제조 가능성 평가
```
ImageInput → eDOCr2 → SkinModel (task=manufacturability)
```

### 전체 분석
```
ImageInput → YOLO → eDOCr2 → SkinModel → Knowledge
```

---

## 리소스 요구사항

| 항목 | 최소 | 권장 |
|------|------|------|
| VRAM | 512MB | 1GB |
| RAM | 1GB | 2GB |
| CPU 코어 | 2 | 4 |
| CUDA | 11.0+ | 12.x |

### 파라미터별 리소스 영향

| 파라미터 | 영향 |
|----------|------|
| task | manufacturability → 시간 증가 |

---

**마지막 업데이트**: 2025-12-09
