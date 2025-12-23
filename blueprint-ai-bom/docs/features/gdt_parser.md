# GD&T 파서

> **목적**: 도면 내 기하공차 및 데이텀 자동 검출
> **상태**: ✅ 구현 완료 (2025-12-19)

---

## 개요

GD&T(Geometric Dimensioning and Tolerancing) 파서는
OCR로 추출된 텍스트에서 기하공차 심볼, 공차값, 데이텀 참조를 파싱합니다.

```
OCR 텍스트 → GD&T 파서 → 구조화된 공차 데이터
```

---

## 지원 심볼

### 기하공차 심볼

| 심볼 | 유니코드 | 의미 | 정규식 패턴 |
|------|---------|------|------------|
| ⌀ | U+2300 | 직경 | `[⌀ØφΦ∅]` |
| ⊥ | U+22A5 | 직각도 | `[⊥]` |
| ∥ | U+2225 | 평행도 | `[∥\|\|]` |
| ⊙ | U+2299 | 동심도 | `[⊙◎]` |
| ⌖ | U+2316 | 위치도 | `[⌖⊕]` |
| ○ | U+25CB | 진원도 | `[○◯]` |
| ◇ | U+25C7 | 프로파일 | `[◇◆]` |
| ⌓ | U+2313 | 원통도 | `[⌓]` |
| △ | U+25B3 | 평면도 | `[△▽]` |

### 데이텀 심볼

| 패턴 | 예시 | 설명 |
|------|------|------|
| `[A-Z]` | A, B, C | 단일 데이텀 |
| `[A-Z]-[A-Z]` | A-B | 복합 데이텀 |
| `[A-Z][A-Z]` | AB | 공통 데이텀 |

---

## 백엔드 구현

### 서비스 (`services/gdt_parser.py`)

```python
class GDTParser:
    def parse_gdt_text(self, text: str) -> list[GDTAnnotation]:
        """텍스트에서 GD&T 정보 추출"""

    def parse_tolerance(self, text: str) -> Optional[ToleranceInfo]:
        """공차값 파싱 (±0.1, 0.05 등)"""

    def extract_datums(self, text: str) -> list[str]:
        """데이텀 참조 추출"""

    def classify_gdt_type(self, symbol: str) -> GDTType:
        """심볼로 GD&T 타입 분류"""
```

### 데이터 모델 (`schemas/gdt.py`)

```python
class GDTAnnotation(BaseModel):
    id: str
    gdt_type: GDTType  # DIAMETER, PERPENDICULARITY, PARALLELISM, ...
    symbol: str
    value: Optional[float]
    unit: str = "mm"
    datums: list[str] = []
    bbox: BBoxDict
    confidence: float
    raw_text: str

class GDTType(str, Enum):
    DIAMETER = "diameter"
    PERPENDICULARITY = "perpendicularity"
    PARALLELISM = "parallelism"
    CONCENTRICITY = "concentricity"
    POSITION = "position"
    CIRCULARITY = "circularity"
    CYLINDRICITY = "cylindricity"
    FLATNESS = "flatness"
    PROFILE = "profile"
```

---

## 파싱 예시

### 입력

```
⌀0.05|A|B
∥0.1 A-B
⊥0.02 A
```

### 출력

```json
[
  {
    "id": "gdt-001",
    "gdt_type": "diameter",
    "symbol": "⌀",
    "value": 0.05,
    "datums": ["A", "B"],
    "raw_text": "⌀0.05|A|B"
  },
  {
    "id": "gdt-002",
    "gdt_type": "parallelism",
    "symbol": "∥",
    "value": 0.1,
    "datums": ["A-B"],
    "raw_text": "∥0.1 A-B"
  },
  {
    "id": "gdt-003",
    "gdt_type": "perpendicularity",
    "symbol": "⊥",
    "value": 0.02,
    "datums": ["A"],
    "raw_text": "⊥0.02 A"
  }
]
```

---

## 프론트엔드 구현

### `GDTEditor.tsx`

GD&T 검출 결과를 시각화하고 편집할 수 있는 UI 컴포넌트

**기능**:
- GD&T 심볼 오버레이
- 공차값 편집
- 데이텀 참조 표시
- 검증 상태 표시

---

## 정규식 패턴

### 공차값 패턴

```python
# 기본 공차: ±0.1, ±0.05
TOLERANCE_PATTERN = r'[±]\s*(\d+\.?\d*)'

# 범위 공차: +0.1/-0.05
RANGE_PATTERN = r'[+](\d+\.?\d*)\s*/\s*[-](\d+\.?\d*)'

# GD&T 공차: ⌀0.05
GDT_VALUE_PATTERN = r'([⌀⊥∥⊙⌖])\s*(\d+\.?\d*)'
```

### 데이텀 패턴

```python
# 단일 데이텀: A, B, C
SINGLE_DATUM = r'\b([A-Z])\b'

# 복합 데이텀: A-B, A-B-C
COMPOUND_DATUM = r'\b([A-Z](?:-[A-Z])+)\b'

# 프레임 구분자: |A|B| 형식
FRAME_DATUM = r'\|([A-Z])\|'
```

---

## 제한사항

1. **언어**: 현재 영문/숫자 기반 GD&T만 지원
2. **OCR 품질**: 특수 심볼 인식률에 따라 성능 변동
3. **복잡한 프레임**: 다단계 GD&T 프레임은 부분 지원

---

## 관련 파일

| 파일 | 설명 |
|------|------|
| `backend/services/gdt_parser.py` | GD&T 파서 서비스 |
| `backend/schemas/gdt.py` | 데이터 모델 |
| `frontend/src/components/GDTEditor.tsx` | UI 컴포넌트 |

---

**구현일**: 2025-12-19
