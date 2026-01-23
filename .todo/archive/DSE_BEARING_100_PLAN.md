# DSE Bearing 100점 달성 계획서

> **작성일**: 2026-01-22
> **목표**: 테이블/치수 추출 68점 → 100점
> **원칙**: 기존 코드 최대 활용, 최소 개발로 최대 효과

---

## 🔴 핵심 원칙: BlueprintFlow 통합 필수

### 모든 Phase에 적용되는 필수 원칙

**독립 스크립트/모듈 금지** - 모든 기능은 BlueprintFlow Builder 내 노드로 구현

### 통합 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                  BlueprintFlow Builder                   │
├─────────────────────────────────────────────────────────┤
│  web-ui/src/config/nodeDefinitions.ts    ← 노드 정의     │
│  web-ui/src/config/apiRegistry.ts        ← API 등록     │
├─────────────────────────────────────────────────────────┤
│  gateway-api/api_specs/*.yaml            ← API 스펙     │
│  gateway-api/blueprintflow/executors/    ← Executor     │
├─────────────────────────────────────────────────────────┤
│  models/*-api/                           ← 마이크로서비스 │
└─────────────────────────────────────────────────────────┘
```

### Phase별 구현 형태

| Phase | 새 기능 | 통합 형태 | 카테고리 |
|-------|---------|----------|----------|
| Phase 1 | Title Block Parser | **새 노드** 또는 eDOCr2 파라미터 확장 | `ocr` |
| Phase 2 | Parts List 강화 | Table Detector **프로파일 추가** | `detection` |
| Phase 3 | 복합 치수 파서 | eDOCr2 **후처리 노드** | `analysis` |
| Phase 4 | BOM Matcher | **새 노드** | `analysis` |
| Phase 5 | Quote Calculator | **새 노드** | `analysis` |
| Phase 6 | 통합 파이프라인 | **템플릿** 등록 | - |

### 매 Phase 완료 체크리스트

```
□ gateway-api/api_specs/{node}.yaml     - API 스펙 정의
□ gateway-api/blueprintflow/executors/  - Executor 구현
□ web-ui/src/config/nodes/              - 노드 정의 추가
□ web-ui/src/config/apiRegistry.ts      - API 등록
□ web-ui/src/locales/{ko,en}.json       - i18n 추가
□ BlueprintFlow Builder에서 드래그&드롭 테스트
□ 기존 노드와 연결 테스트 (입력/출력 호환)
```

### 금지 사항

| 금지 | 이유 | 대안 |
|------|------|------|
| `scripts/*.py` 독립 실행 | UI 통합 불가 | Executor로 구현 |
| 하드코딩된 경로/값 | 재사용 불가 | 파라미터화 |
| 콘솔 출력만 | 파이프라인 연결 불가 | 구조화된 JSON 출력 |
| 단일 도면만 처리 | 배치 처리 불가 | 배열 입력 지원 |

---

## 현재 상태 분석

### 점수 현황 (68/100)

| 항목 | 현재 점수 | 목표 점수 | 갭 |
|------|----------|----------|-----|
| 테이블 추출 | 65 | 95 | +30 |
| 치수 추출 | 70 | 95 | +25 |
| 도면 정보 (Title Block) | 55 | 95 | +40 |
| GD&T | 60 | 85 | +25 |
| 표면 거칠기 | 50 | 80 | +30 |
| BOM 매칭 | 40 | 90 | +50 |
| 견적 자동화 | 0 | 80 | +80 |

### 활용 가능한 기존 코드

| 컴포넌트 | 위치 | 활용 방안 |
|----------|------|----------|
| **Table Detector** | `models/table-detector-api/` | Parts List 추출 기반 |
| **eDOCr2** | `models/edocr2-v2-api/` | 치수/GD&T 추출 |
| **YOLO engineering** | `models/yolo-api/` | 심볼 검출 전처리 |
| **Blueprint AI BOM** | `blueprint-ai-bom/` | Human-in-the-loop 패턴 |
| **Excel Export** | `gateway-api/blueprintflow/executors/` | 견적서 출력 |
| **Design Checker** | `models/design-checker-api/` | 파이프라인 통합 패턴 |

---

## Phase 1: Title Block Parser (P0) ✅ 완료

**목표**: 55점 → 95점 (+40)
**예상 기간**: 3일
**의존성**: 없음
**완료일**: 2026-01-22

### 구현 내역
- ✅ `gateway-api/api_specs/titleblock.yaml` - API 스펙 정의
- ✅ `gateway-api/blueprintflow/executors/titleblock_executor.py` - Executor 구현
- ✅ `web-ui/src/config/nodes/analysisNodes.ts` - 노드 정의 추가
- ✅ `web-ui/src/config/apiRegistry.ts` - API 레지스트리 등록
- ✅ 테스트 통과 (304개)

### 1.1 문제 정의

현재 eDOCr2는 텍스트를 추출하지만 **구조화된 필드 파싱이 없음**:
- 도면번호 (TD00XXXXX)
- Rev (A, B, C, D)
- 품명 (BEARING CASING ASSY 등)
- 재질 (SF440A, SS400 등)
- 중량, 도면척도, 작성일 등

### 1.2 구현 전략

**방안 A: Table Detector 활용** (권장)
```
Title Block = 테이블 → Table Detector로 영역 검출 + OCR
```

**방안 B: 템플릿 매칭** (백업)
```
DOOSAN 도면 레이아웃 고정 → 좌표 기반 ROI 추출
```

### 1.3 구현 상세

#### Step 1: Title Block 영역 검출
```python
# 기존 Table Detector 활용
# gateway-api/services/table_service.py 수정

async def detect_title_block(image: bytes) -> TitleBlockRegion:
    """도면 우하단 Title Block 영역 검출"""
    # Table Detector API 호출
    tables = await table_detector.detect(image, mode="detect")

    # 우하단 영역 필터링 (도면의 80% 이하 영역)
    title_block = filter_bottom_right(tables, threshold=0.8)
    return title_block
```

#### Step 2: 필드 파서 구현
```python
# 신규: gateway-api/services/title_block_parser.py

TITLE_BLOCK_FIELDS = {
    "drawing_number": r"TD\d{7}",
    "revision": r"Rev\.?\s*([A-Z])",
    "part_name": r"(BEARING|CASING|RING|PAD|BOLT|PIN)",
    "material": r"(SF440A|SS400|SM490A|S45C|SUS\d+|ASTM\s*[A-Z]\d+)",
    "weight": r"(\d+\.?\d*)\s*(kg|KG)",
    "scale": r"(\d+:\d+)",
}

def parse_title_block(ocr_text: str) -> TitleBlockData:
    """Title Block OCR 결과에서 구조화된 필드 추출"""
    result = {}
    for field, pattern in TITLE_BLOCK_FIELDS.items():
        match = re.search(pattern, ocr_text, re.IGNORECASE)
        if match:
            result[field] = match.group(1) if match.groups() else match.group(0)
    return TitleBlockData(**result)
```

#### Step 3: API 엔드포인트 추가
```yaml
# gateway-api/api_specs/edocr2.yaml 확장

parameters:
  - name: extract_title_block
    type: boolean
    default: false
    description: Title Block 구조화 추출

outputs:
  - name: title_block
    type: TitleBlockData
    description: 파싱된 Title Block 필드
```

### 1.4 테스트 계획

| 테스트 | 입력 | 기대 출력 |
|--------|------|----------|
| TD0062018 파싱 | casing_assy_t1_page1.png | drawing_number=TD0062018, revision=A |
| 재질 추출 | 다양한 도면 | SF440A, SS400 등 정확 추출 |
| 누락 필드 처리 | 불완전 Title Block | null 반환, 에러 없음 |

### 1.5 완료 기준

- [ ] Title Block 영역 자동 검출 (정확도 90%+)
- [ ] 6개 주요 필드 파싱 (drawing_number, revision, part_name, material, weight, scale)
- [ ] 94개 DSE Bearing 도면 테스트 통과
- [ ] 단위 테스트 20개 이상

---

## Phase 2: Parts List 추출 강화 (P0)

**목표**: 65점 → 95점 (+30)
**예상 기간**: 2일
**의존성**: Phase 1 (Title Block 영역 제외)

### 2.1 문제 정의

Parts List 테이블 구조:
```
| NO | PART NAME | MAT'L | Q'TY | REMARKS |
|----|-----------|-------|------|---------|
| 1  | CASING    | SF440A| 1    | -       |
| 2  | LINER PAD | B23   | 8    | BABBITT |
```

현재 Table Detector가 검출하지만:
- 셀 병합 처리 미흡
- 헤더 인식 불안정
- 한글/영문 혼합 시 OCR 오류

### 2.2 구현 전략

**기존 Table Detector 파라미터 최적화**:
```python
# DSE Bearing 전용 프로파일 추가
# gateway-api/api_specs/tabledetector.yaml

profiles:
  available:
    - name: bearing_parts_list
      label: "베어링 Parts List"
      description: "DSE Bearing 도면 Parts List 최적화"
      params:
        mode: analyze
        ocr_engine: paddle  # 한글 지원 강화
        borderless: false   # Parts List는 테두리 있음
        confidence_threshold: 0.6
        min_confidence: 60
        output_format: json
```

### 2.3 구현 상세

#### Step 1: Parts List 전용 후처리
```python
# 신규: gateway-api/services/parts_list_parser.py

PARTS_LIST_HEADERS = ["NO", "PART NAME", "MAT'L", "Q'TY", "REMARKS", "DWG NO"]

def normalize_parts_list(table_data: dict) -> PartsListData:
    """Parts List 테이블 정규화"""
    # 헤더 매핑 (유사도 기반)
    headers = fuzzy_match_headers(table_data["headers"], PARTS_LIST_HEADERS)

    # 데이터 정규화
    rows = []
    for row in table_data["data"]:
        normalized = {
            "no": int(row.get("NO", 0)),
            "part_name": row.get("PART NAME", "").strip(),
            "material": normalize_material(row.get("MAT'L", "")),
            "quantity": int(row.get("Q'TY", 1)),
            "remarks": row.get("REMARKS", ""),
        }
        rows.append(normalized)

    return PartsListData(headers=headers, rows=rows)
```

#### Step 2: 재질 코드 정규화
```python
MATERIAL_ALIASES = {
    "SF440A": ["SF440", "SF-440A", "SF 440A"],
    "SS400": ["SS-400", "SS 400"],
    "ASTM B23": ["B23", "ASTM B-23", "BABBITT"],
    # ...
}

def normalize_material(raw: str) -> str:
    """재질 코드 정규화"""
    for standard, aliases in MATERIAL_ALIASES.items():
        if raw.upper() in [a.upper() for a in aliases]:
            return standard
    return raw.upper()
```

### 2.4 완료 기준

- [ ] Parts List 테이블 검출 정확도 95%+
- [ ] 헤더 자동 인식 (NO, PART NAME, MAT'L, Q'TY)
- [ ] 재질 코드 정규화 (15개 주요 재질)
- [ ] 셀 병합 처리

---

## Phase 3: 복합 치수 파서 (P1)

**목표**: 70점 → 95점 (+25)
**예상 기간**: 2일
**의존성**: 없음

### 3.1 문제 정의

DSE Bearing 도면의 치수 형식:
```
OD670×ID440           → {outer_diameter: 670, inner_diameter: 440}
1100×ID680×200L       → {width: 1100, inner_diameter: 680, length: 200}
360×190               → {dimension1: 360, dimension2: 190}
Ø25H7                 → {diameter: 25, tolerance: "H7"}
50.0±0.1              → {value: 50.0, tolerance: "±0.1"}
```

현재 eDOCr2는 텍스트로 추출하지만 **구조화 파싱 없음**.

### 3.2 구현 상세

```python
# 신규: gateway-api/services/dimension_parser.py

import re
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class BearingDimension:
    outer_diameter: Optional[float] = None
    inner_diameter: Optional[float] = None
    length: Optional[float] = None
    width: Optional[float] = None
    tolerance: Optional[str] = None
    raw_text: str = ""

DIMENSION_PATTERNS = [
    # OD670×ID440
    (r"OD(\d+\.?\d*)×ID(\d+\.?\d*)", lambda m: {
        "outer_diameter": float(m.group(1)),
        "inner_diameter": float(m.group(2))
    }),
    # 1100×ID680×200L
    (r"(\d+\.?\d*)×ID(\d+\.?\d*)×(\d+\.?\d*)L", lambda m: {
        "width": float(m.group(1)),
        "inner_diameter": float(m.group(2)),
        "length": float(m.group(3))
    }),
    # Ø25H7
    (r"[ØφΦ](\d+\.?\d*)([A-Z]\d+)?", lambda m: {
        "diameter": float(m.group(1)),
        "tolerance": m.group(2)
    }),
    # 50.0±0.1
    (r"(\d+\.?\d*)\s*[±]\s*(\d+\.?\d*)", lambda m: {
        "value": float(m.group(1)),
        "tolerance": f"±{m.group(2)}"
    }),
]

def parse_bearing_dimension(text: str) -> BearingDimension:
    """베어링 치수 텍스트 파싱"""
    for pattern, extractor in DIMENSION_PATTERNS:
        match = re.search(pattern, text)
        if match:
            data = extractor(match)
            return BearingDimension(raw_text=text, **data)
    return BearingDimension(raw_text=text)
```

### 3.3 eDOCr2 통합

```python
# models/edocr2-v2-api/services/dimension_service.py 수정

async def extract_dimensions_with_parsing(image: bytes) -> DimensionResult:
    """치수 추출 + 베어링 치수 파싱"""
    # 기존 eDOCr2 추출
    raw_dimensions = await extract_dimensions(image)

    # 베어링 치수 파싱 추가
    parsed = []
    for dim in raw_dimensions:
        parsed_dim = parse_bearing_dimension(dim.text)
        parsed_dim.bbox = dim.bbox
        parsed_dim.confidence = dim.confidence
        parsed.append(parsed_dim)

    return DimensionResult(
        raw=raw_dimensions,
        parsed=parsed,
        bearing_dimensions=filter_bearing_dimensions(parsed)
    )
```

### 3.4 완료 기준

- [ ] 5가지 베어링 치수 패턴 파싱
- [ ] OD/ID/Length 자동 분류
- [ ] 공차 (H7, ±0.1 등) 추출
- [ ] 단위 테스트 30개 이상

---

## Phase 4: BOM 자동 매칭 (P1)

**목표**: 40점 → 90점 (+50)
**예상 기간**: 3일
**의존성**: Phase 1 (Title Block), Phase 2 (Parts List)

### 4.1 문제 정의

- BOM 파일: 395개 품목 (TD 도면번호 기준)
- 도면 파일: 94개 PDF
- 필요: 도면번호로 BOM ↔ 도면 자동 연결

### 4.2 구현 전략

**기존 Blueprint AI BOM 패턴 활용**:
```
blueprint-ai-bom/backend/services/matching_service.py
→ 이미 유사도 기반 매칭 로직 존재
```

### 4.3 구현 상세

#### Step 1: BOM 데이터 로더
```python
# 신규: gateway-api/services/bom_loader.py

import pandas as pd
from typing import Dict, List

class BOMLoader:
    def __init__(self, bom_path: str):
        self.bom_df = pd.read_excel(bom_path)
        self.drawing_index = self._build_index()

    def _build_index(self) -> Dict[str, dict]:
        """도면번호 → BOM 항목 인덱스"""
        index = {}
        for _, row in self.bom_df.iterrows():
            dwg_no = row.get("도면번호", row.get("DWG NO", ""))
            if dwg_no:
                index[dwg_no] = row.to_dict()
        return index

    def match(self, drawing_number: str) -> dict:
        """도면번호로 BOM 항목 조회"""
        # 정확 매칭
        if drawing_number in self.drawing_index:
            return self.drawing_index[drawing_number]

        # 퍼지 매칭 (TD0060700 vs TD0060700 Rev.B)
        base_number = re.match(r"(TD\d{7})", drawing_number)
        if base_number:
            return self.drawing_index.get(base_number.group(1), {})

        return {}
```

#### Step 2: 자동 매칭 파이프라인
```python
# 신규: gateway-api/blueprintflow/executors/bom_matcher_executor.py

class BOMMatcherExecutor(BaseExecutor):
    """BOM 자동 매칭 Executor"""

    async def execute(self, inputs: dict) -> dict:
        # 입력: title_block (Phase 1에서 추출)
        title_block = inputs.get("title_block", {})
        drawing_number = title_block.get("drawing_number")

        if not drawing_number:
            return {"matched": False, "reason": "도면번호 없음"}

        # BOM 매칭
        bom_item = self.bom_loader.match(drawing_number)

        if bom_item:
            return {
                "matched": True,
                "drawing_number": drawing_number,
                "bom_item": bom_item,
                "material": bom_item.get("재질"),
                "weight": bom_item.get("중량"),
                "quantity": bom_item.get("수량"),
            }

        return {"matched": False, "reason": "BOM에 없는 도면번호"}
```

#### Step 3: BlueprintFlow 노드 추가
```typescript
// web-ui/src/config/nodes/analysisNodes.ts 추가

export const bomMatcherNode: NodeDefinition = {
  id: 'bom_matcher',
  type: 'bom_matcher',
  label: 'BOM Matcher',
  category: 'analysis',
  description: '도면번호로 BOM 자동 매칭',
  inputs: ['title_block'],
  outputs: ['bom_item', 'matched'],
  parameters: [
    {
      name: 'bom_file',
      type: 'file',
      accept: '.xlsx,.csv',
      description: 'BOM 파일 업로드',
    },
    {
      name: 'fuzzy_match',
      type: 'boolean',
      default: true,
      description: '퍼지 매칭 사용',
    },
  ],
};
```

### 4.4 완료 기준

- [ ] BOM 파일 로더 (Excel/CSV)
- [ ] 도면번호 기반 자동 매칭
- [ ] 퍼지 매칭 (Rev 무시)
- [ ] 매칭률 95%+ (94개 도면 중 89개 이상)
- [ ] BlueprintFlow 노드 통합

---

## Phase 5: 견적 자동화 (P2)

**목표**: 0점 → 80점 (+80)
**예상 기간**: 5일
**의존성**: Phase 1-4 모두

### 5.1 문제 정의

견적 산출에 필요한 정보:
1. **소재비**: 재질 × 중량 × 단가
2. **가공비**: 치수/공차 복잡도 × 난이도 단가
3. **외주비**: 특수 공정 (열처리, 베빗 등)

### 5.2 구현 전략

**기존 Excel Export 패턴 활용**:
```
gateway-api/blueprintflow/executors/excel_export_executor.py
→ Excel 출력 로직 재사용
```

### 5.3 구현 상세

#### Step 1: 단가 테이블 정의
```python
# 신규: gateway-api/config/pricing_tables.py

MATERIAL_UNIT_PRICE = {
    # 재질: 원/kg
    "SF440A": 3500,
    "SM490A": 2800,
    "SS400": 2200,
    "S45C": 3000,
    "SUS304": 8500,
    "SUS316": 12000,
    "ASTM B23": 45000,  # Babbitt
}

MACHINING_DIFFICULTY = {
    # 공차 등급: 난이도 계수
    "H6": 2.5,
    "H7": 2.0,
    "H8": 1.5,
    "g6": 2.5,
    "±0.01": 3.0,
    "±0.05": 2.0,
    "±0.1": 1.5,
    "ISO 2768-m": 1.0,  # 일반 공차
}

BASE_MACHINING_RATE = 50000  # 원/시간
```

#### Step 2: 견적 계산 엔진
```python
# 신규: gateway-api/services/quote_calculator.py

@dataclass
class QuoteResult:
    material_cost: float      # 소재비
    machining_cost: float     # 가공비
    outsourcing_cost: float   # 외주비
    total_cost: float         # 합계
    breakdown: dict           # 상세 내역

class QuoteCalculator:
    def calculate(
        self,
        material: str,
        weight: float,
        dimensions: List[BearingDimension],
        tolerances: List[str],
    ) -> QuoteResult:
        # 1. 소재비
        unit_price = MATERIAL_UNIT_PRICE.get(material, 3000)
        material_cost = weight * unit_price

        # 2. 가공비 (치수 복잡도 기반)
        difficulty = self._calculate_difficulty(dimensions, tolerances)
        estimated_hours = self._estimate_machining_hours(dimensions)
        machining_cost = estimated_hours * BASE_MACHINING_RATE * difficulty

        # 3. 외주비 (베빗, 열처리 등)
        outsourcing_cost = self._calculate_outsourcing(material, tolerances)

        return QuoteResult(
            material_cost=material_cost,
            machining_cost=machining_cost,
            outsourcing_cost=outsourcing_cost,
            total_cost=material_cost + machining_cost + outsourcing_cost,
            breakdown={...}
        )
```

#### Step 3: 견적서 Excel 출력
```python
# gateway-api/blueprintflow/executors/quote_export_executor.py

class QuoteExportExecutor(BaseExecutor):
    """견적서 Excel 출력"""

    async def execute(self, inputs: dict) -> dict:
        quotes = inputs.get("quotes", [])

        # Excel 워크북 생성
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "견적서"

        # 헤더
        headers = ["NO", "도면번호", "품명", "재질", "중량", "소재비", "가공비", "외주비", "합계"]
        ws.append(headers)

        # 데이터
        total = 0
        for i, q in enumerate(quotes, 1):
            row = [
                i,
                q["drawing_number"],
                q["part_name"],
                q["material"],
                q["weight"],
                q["material_cost"],
                q["machining_cost"],
                q["outsourcing_cost"],
                q["total_cost"],
            ]
            ws.append(row)
            total += q["total_cost"]

        # 합계
        ws.append(["", "", "", "", "", "", "", "총합계", total])

        # 저장
        output_path = f"/tmp/quote_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        wb.save(output_path)

        return {"file_path": output_path, "total_cost": total}
```

### 5.4 완료 기준

- [ ] 단가 테이블 설정 (재질 15종, 공차 10등급)
- [ ] 소재비/가공비/외주비 자동 계산
- [ ] 견적서 Excel 출력
- [ ] BlueprintFlow 노드 통합

---

## Phase 6: DSE Bearing 통합 파이프라인 (P2)

**목표**: 전체 워크플로우 통합
**예상 기간**: 2일
**의존성**: Phase 1-5 모두

### 6.1 최종 파이프라인

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Image Input │───▶│    YOLO     │───▶│   eDOCr2    │
│  (도면 PNG) │    │ engineering │    │ dimensions  │
└─────────────┘    └─────────────┘    └──────┬──────┘
                                             │
┌─────────────┐    ┌─────────────┐           │
│   Table     │───▶│ Title Block │───────────┤
│  Detector   │    │   Parser    │           │
└─────────────┘    └──────┬──────┘           │
                          │                   │
                          ▼                   ▼
                   ┌─────────────┐    ┌─────────────┐
                   │ BOM Matcher │◀───│  Dimension  │
                   │             │    │   Parser    │
                   └──────┬──────┘    └──────┬──────┘
                          │                   │
                          └─────────┬─────────┘
                                    ▼
                          ┌─────────────────┐
                          │ Quote Calculator│
                          └────────┬────────┘
                                   ▼
                          ┌─────────────────┐
                          │  Excel Export   │
                          │   (견적서)       │
                          └─────────────────┘
```

### 6.2 BlueprintFlow 템플릿

```json
{
  "name": "DSE Bearing 견적 자동화",
  "description": "베어링 도면 → 테이블/치수 추출 → BOM 매칭 → 견적 생성",
  "nodes": [
    {"id": "input", "type": "imageinput"},
    {"id": "yolo", "type": "yolo", "params": {"model_type": "engineering"}},
    {"id": "edocr2", "type": "edocr2", "params": {"extract_dimensions": true}},
    {"id": "table", "type": "tabledetector", "params": {"profile": "bearing_parts_list"}},
    {"id": "title_block", "type": "title_block_parser"},
    {"id": "dim_parser", "type": "dimension_parser"},
    {"id": "bom", "type": "bom_matcher"},
    {"id": "quote", "type": "quote_calculator"},
    {"id": "export", "type": "excel_export"}
  ],
  "edges": [
    {"from": "input", "to": "yolo"},
    {"from": "input", "to": "table"},
    {"from": "yolo", "to": "edocr2"},
    {"from": "table", "to": "title_block"},
    {"from": "edocr2", "to": "dim_parser"},
    {"from": "title_block", "to": "bom"},
    {"from": "dim_parser", "to": "quote"},
    {"from": "bom", "to": "quote"},
    {"from": "quote", "to": "export"}
  ]
}
```

---

## 일정 요약

| Phase | 작업 | 기간 | 누적 |
|-------|------|------|------|
| **Phase 1** | Title Block Parser | 3일 | 3일 |
| **Phase 2** | Parts List 강화 | 2일 | 5일 |
| **Phase 3** | 복합 치수 파서 | 2일 | 7일 |
| **Phase 4** | BOM 자동 매칭 | 3일 | 10일 |
| **Phase 5** | 견적 자동화 | 5일 | 15일 |
| **Phase 6** | 통합 파이프라인 | 2일 | **17일** |

---

## 예상 최종 점수

| 항목 | 현재 | 목표 | 달성 방안 |
|------|------|------|----------|
| 테이블 추출 | 65 | **95** | Phase 2 |
| 치수 추출 | 70 | **95** | Phase 3 |
| 도면 정보 | 55 | **95** | Phase 1 |
| GD&T | 60 | **85** | Phase 3 (부분) |
| 표면 거칠기 | 50 | **80** | eDOCr2 기존 기능 |
| BOM 매칭 | 40 | **90** | Phase 4 |
| 견적 자동화 | 0 | **80** | Phase 5 |

**가중 평균**: (95×2 + 95 + 95 + 85 + 80 + 90 + 80) / 8 = **89.4점**

---

## 리스크 및 대응

| 리스크 | 영향 | 대응 |
|--------|------|------|
| OCR 정확도 미달 | 테이블/치수 추출 실패 | PaddleOCR/EasyOCR 대체, 전처리 강화 |
| 도면 레이아웃 불일치 | Title Block 검출 실패 | 템플릿 매칭 백업 방안 |
| 단가 테이블 미확정 | 견적 정확도 저하 | 고객 미팅에서 확정 필요 |
| BOM 형식 불일치 | 매칭 실패 | 고객 BOM 샘플 사전 확보 |

---

## 다음 단계

1. **고객 미팅 후 확정 사항**:
   - 견적서 양식 (Excel 템플릿)
   - 단가 테이블 (재질별, 공정별)
   - 우선 견적 대상 품목 리스트

2. **Phase 1 착수 조건**:
   - 고객 회신 완료
   - 테스트 도면 5장 선정

---

*작성: Claude Code*
*최종 업데이트: 2026-01-22*
