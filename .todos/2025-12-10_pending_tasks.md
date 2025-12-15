# 미완료 작업 정리 - 기능 확장

> **작성일**: 2025-12-10
> **최종 업데이트**: 2025-12-14
> **환경**: 온프레미스 납품

---

## 1. 비용 산정 엔진 (중요도: 중간)

**필요 이유**: 도면 분석 결과를 실제 견적으로 연결해야 고객 가치가 완성됨.

### 1.1 재질 데이터베이스 (1~2일)

**목적**: 도면에서 추출한 재질명으로 원자재 비용 자동 계산

**데이터 구조**:
```json
{
  "SS400": {
    "name": "일반 구조용강",
    "price_per_kg": 1200,
    "machinability": 1.0,
    "hardness": "HB 130-180"
  },
  "S45C": {
    "name": "기계 구조용강",
    "price_per_kg": 1800,
    "machinability": 1.2,
    "hardness": "HB 160-220"
  },
  "SUS304": {
    "name": "스테인리스강",
    "price_per_kg": 4500,
    "machinability": 1.8,
    "hardness": "HB 187"
  },
  "AL6061": {
    "name": "알루미늄 합금",
    "price_per_kg": 3200,
    "machinability": 0.7,
    "hardness": "HB 95"
  }
}
```

**활용 예시**:
```
입력: 도면에서 "재질: SUS304, 중량 5kg" 추출
출력: 원자재비 = 4,500원 × 5kg = 22,500원
```

**구현 위치**: `gateway-api/data/materials.json` 또는 `gateway-api/services/material_service.py`

---

### 1.2 공차 등급 테이블 (1일)

**목적**: eDOCr2가 추출한 공차(H7, ±0.01 등)를 ISO 등급으로 변환하여 가공 난이도 판단

**데이터 구조**:
```json
{
  "IT6": {
    "tolerance_range": "±0.008mm",
    "time_multiplier": 3.0,
    "cost_addition": 200,
    "required_process": ["정밀 연삭", "호닝"],
    "example": "베어링 하우징, 정밀 축"
  },
  "IT7": {
    "tolerance_range": "±0.015mm",
    "time_multiplier": 2.0,
    "cost_addition": 100,
    "required_process": ["보링", "리밍"],
    "example": "H7 구멍, 미끄럼 끼워맞춤"
  },
  "IT8": {
    "tolerance_range": "±0.022mm",
    "time_multiplier": 1.5,
    "cost_addition": 50,
    "required_process": ["정밀 선삭"],
    "example": "일반 기계 부품"
  },
  "IT10": {
    "tolerance_range": "±0.058mm",
    "time_multiplier": 1.0,
    "cost_addition": 0,
    "required_process": ["일반 선삭"],
    "example": "비정밀 부품"
  }
}
```

**공차 → 등급 매핑**:
```python
def tolerance_to_grade(tolerance_str: str) -> str:
    """
    H7 → IT7
    ±0.01 → IT7 (10µm급)
    ±0.05 → IT10
    """
    if 'H7' in tolerance_str or 'h7' in tolerance_str:
        return 'IT7'
    elif 'H6' in tolerance_str:
        return 'IT6'
    # ... 패턴 매칭
```

---

### 1.3 공정 규칙 엔진 (2~3일)

**목적**: 치수/공차/표면조도 조합에 따라 필요 공정을 자동 판단

**규칙 예시**:

| 조건 | 필요 공정 | 예상 시간 |
|------|----------|----------|
| 구멍 φ10mm H7 | 드릴 → 보링 → 리밍 | 15분/개 |
| 구멍 φ10mm H11 | 드릴 | 3분/개 |
| 표면 Ra 0.8 이하 | 연삭 추가 | +10분 |
| 표면 Ra 3.2 | 선삭 마무리 | +3분 |
| 외경 IT6 | 센터리스 연삭 | +20분 |

**구현 구조**:
```python
class ProcessRuleEngine:
    def determine_processes(self, feature: dict) -> list:
        """
        입력: {'type': 'hole', 'diameter': 10, 'tolerance': 'H7', 'surface': 'Ra 1.6'}
        출력: [
            {'process': '드릴', 'time_min': 3},
            {'process': '보링', 'time_min': 5},
            {'process': '리밍', 'time_min': 7}
        ]
        """
        rules = self.load_rules()
        matched = []
        for rule in rules:
            if self.match_condition(feature, rule):
                matched.extend(rule['processes'])
        return matched
```

**규칙 파일 형식** (`gateway-api/data/process_rules.yaml`):
```yaml
rules:
  - name: "정밀 구멍 가공"
    condition:
      type: "hole"
      tolerance_grade: ["IT6", "IT7"]
    processes:
      - { name: "드릴", time_per_unit: 3 }
      - { name: "보링", time_per_unit: 5 }
      - { name: "리밍", time_per_unit: 7 }

  - name: "고정밀 표면"
    condition:
      surface_roughness_max: 0.8
    processes:
      - { name: "연삭", time_per_unit: 10 }
```

---

### 1.4 유사 부품 기반 견적 (2일)

**목적**: Knowledge Engine에서 유사한 과거 부품을 검색하여 견적 추정

**검색 조건**:
- 재질 동일/유사
- 크기 ±20% 범위
- 형상 유사도 (원통/직육면체/복합)

**구현**:
```python
async def find_similar_parts(part_info: dict) -> list:
    """
    입력: {'material': 'SUS304', 'dimensions': [50, 100, 30], 'shape': 'cylindrical'}
    출력: [
        {'part_id': 'P001', 'similarity': 0.92, 'actual_quote': 450000},
        {'part_id': 'P015', 'similarity': 0.85, 'actual_quote': 380000}
    ]
    """
    # Knowledge API 호출 (GraphRAG)
    results = await knowledge_api.search({
        'query': f"재질:{part_info['material']} 형상:{part_info['shape']}",
        'filters': {
            'size_range': calculate_size_range(part_info['dimensions'])
        }
    })
    return weighted_average_quote(results)
```

**예상 견적 계산**:
```
유사 부품 3건 발견:
- P001: 45만원 (유사도 92%)
- P015: 38만원 (유사도 85%)
- P023: 52만원 (유사도 78%)

가중 평균: (45×0.92 + 38×0.85 + 52×0.78) / (0.92+0.85+0.78) = 44.2만원
예상 범위: 38만원 ~ 52만원
```

---

## 2. 견적서 출력 (중요도: 중간)

**필요 이유**: CSV만으로는 고객에게 전달하기 부적합. 전문적인 견적서 필요.

### 2.1 Excel 견적서 템플릿 (2일)

**템플릿 구조**:
```
┌─────────────────────────────────────────────────────────┐
│ [회사 로고]                    견 적 서                 │
│                                                         │
│ 견적번호: QT-2024-001         견적일: 2024-12-14       │
│ 고객사: (주)테크크로스         유효기간: 30일           │
├─────────────────────────────────────────────────────────┤
│ No │ 품명          │ 규격    │ 재질  │ 수량 │ 단가    │
├────┼───────────────┼─────────┼───────┼──────┼─────────┤
│ 1  │ 브라켓        │ 50×100  │ SS400 │ 10   │ 50,000  │
│ 2  │ 축            │ φ30×200 │ S45C  │ 5    │ 120,000 │
│ 3  │ 하우징        │ 100×150 │ AL6061│ 2    │ 280,000 │
├─────────────────────────────────────────────────────────┤
│                              소계:     1,660,000원     │
│                              VAT:        166,000원     │
│                              합계:     1,826,000원     │
├─────────────────────────────────────────────────────────┤
│ 비고:                                                   │
│ - 납기: 발주 후 14일                                    │
│ - 결제조건: 납품 후 30일                                │
└─────────────────────────────────────────────────────────┘
```

**구현** (`gateway-api/services/quote_export_service.py`):
```python
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border

def create_quote_excel(bom_data: list, customer_info: dict) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "견적서"

    # 헤더
    ws.merge_cells('A1:F1')
    ws['A1'] = "견 적 서"
    ws['A1'].font = Font(size=20, bold=True)

    # BOM 테이블
    headers = ['No', '품명', '규격', '재질', '수량', '단가']
    for col, header in enumerate(headers, 1):
        ws.cell(row=5, column=col, value=header)

    # 데이터 행
    for row_idx, item in enumerate(bom_data, 6):
        ws.cell(row=row_idx, column=1, value=row_idx-5)
        ws.cell(row=row_idx, column=2, value=item['name'])
        # ...

    # 합계
    total_row = len(bom_data) + 7
    ws.cell(row=total_row, column=5, value="소계:")
    ws.cell(row=total_row, column=6, value=sum(item['total'] for item in bom_data))

    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
```

---

## 3. 제거된 항목

| 항목 | 제거 이유 |
|------|----------|
| ~~ERP/MES 연동~~ | 고객사별 시스템이 다름, 납품 후 별도 협의 |
| ~~PPT 보완 문서~~ | 영업용, 납품과 무관 |

---

## 우선순위 요약

| 순위 | 작업 | 예상 기간 | 필수 여부 | 의존성 |
|------|------|----------|----------|--------|
| 1 | 공정 규칙 엔진 | 2~3일 | 권장 | 공차 등급 테이블 |
| 2 | 재질 DB | 1~2일 | 권장 | 없음 |
| 3 | 공차 등급 테이블 | 1일 | 권장 | 없음 |
| 4 | 유사 부품 검색 | 2일 | 선택 | Knowledge Engine |
| 5 | 견적서 템플릿 | 2일 | 선택 | BOM 생성 완료 |

**총 예상 작업량**: 약 8~10일 (선택 포함)

---

## 구현 순서 권장

```
1단계: 기초 데이터 (2일)
├── 재질 DB (materials.json)
└── 공차 등급 테이블 (tolerance_grades.json)

2단계: 규칙 엔진 (3일)
└── 공정 규칙 엔진 (process_rules.yaml + ProcessRuleEngine)

3단계: 출력 (2일)
└── Excel 견적서 템플릿

4단계: 고급 기능 (2일, 선택)
└── 유사 부품 검색 (Knowledge Engine 연동)
```

---

**참고**: 이 작업들은 통합 작업(2025-12-14_integration_strategy.md) 완료 후 진행 권장
