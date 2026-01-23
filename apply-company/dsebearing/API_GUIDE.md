# DSE Bearing API 사용 가이드

> **버전**: 1.0.0 | **최종 업데이트**: 2026-01-22

## 개요

DSE Bearing API는 베어링 도면을 분석하여 자동으로 견적서를 생성하는 통합 파이프라인입니다.

```
도면 이미지 → Title Block 파싱 → Parts List 추출 → BOM 매칭 → 견적 생성 → Excel/PDF 출력
```

## Base URL

```
http://localhost:8000/api/v1/dsebearing
```

---

## 빠른 시작

### 1. 전체 파이프라인 (단일 호출)

도면 이미지에서 바로 견적까지 생성:

```bash
# Step 1: Title Block 파싱
curl -X POST http://localhost:8000/api/v1/dsebearing/titleblock \
  -F "file=@drawing.png" \
  -F "profile=bearing"

# Step 2: Parts List 추출
curl -X POST http://localhost:8000/api/v1/dsebearing/partslist \
  -F "file=@drawing.png" \
  -F "profile=bearing"

# Step 3: BOM 매칭 + 견적 생성
curl -X POST http://localhost:8000/api/v1/dsebearing/bommatcher \
  -F "titleblock_data={...}" \
  -F "partslist_data={...}" \
  -F "customer_id=DSE" \
  -F "generate_quote=true"
```

### 2. 견적서만 생성

부품 정보가 있다면 바로 견적 생성:

```bash
curl -X POST http://localhost:8000/api/v1/dsebearing/quotegenerator \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "DSE",
    "parts": [
      {"no": "1", "description": "RING UPPER", "material": "SF45A", "qty": 1, "weight": 25},
      {"no": "2", "description": "PAD ASSY", "material": "ASTM B23 GR.2", "qty": 8, "weight": 5}
    ]
  }'
```

---

## API 엔드포인트

### Title Block 파싱

도면의 Title Block에서 도면번호, 리비전, 품명, 재질을 추출합니다.

**POST** `/titleblock`

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| file | File | O | 도면 이미지 (PNG, JPG) |
| profile | string | X | 파싱 프로파일 (default: bearing) |

**응답 예시**:
```json
{
  "drawing_number": "TD0062016",
  "revision": "A",
  "part_name": "RING ASSY. T1",
  "material": "SF45A",
  "confidence": 0.92
}
```

---

### Parts List 추출

도면에서 부품 목록을 추출합니다.

**POST** `/partslist`

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| file | File | O | 도면 이미지 |
| profile | string | X | 파싱 프로파일 |

**응답 예시**:
```json
{
  "items": [
    {"no": "1", "description": "RING UPPER", "material": "SF45A", "qty": 1, "weight": 25.0},
    {"no": "2", "description": "PAD ASSY", "material": "ASTM B23 GR.2", "qty": 8, "weight": 5.0}
  ],
  "confidence": 0.88
}
```

---

### Dimension 파싱

도면에서 치수 정보를 추출합니다.

**POST** `/dimensionparser`

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| file | File | O | 도면 이미지 |
| dimension_type | string | X | 치수 타입 (bearing) |

**응답 예시**:
```json
{
  "dimensions": [
    {"raw_text": "Ø450", "type": "diameter", "value": 450, "unit": "mm"},
    {"raw_text": "120±0.05", "type": "tolerance", "value": 120, "tolerance": 0.05}
  ],
  "count": 2
}
```

---

### BOM 매칭

Title Block, Parts List, Dimension 데이터를 통합하여 BOM을 생성합니다.

**POST** `/bommatcher`

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| titleblock_data | JSON string | O | Title Block 파싱 결과 |
| partslist_data | JSON string | O | Parts List 파싱 결과 |
| dimension_data | JSON string | X | Dimension 파싱 결과 |
| customer_id | string | X | 고객 ID (default: DSE) |
| generate_quote | boolean | X | 견적 자동 생성 (default: false) |

**응답 예시**:
```json
{
  "matched_items": [
    {"item_no": 1, "part_name": "RING UPPER", "material": "SF45A", "quantity": 1}
  ],
  "match_confidence": 0.85,
  "quote": {
    "quote_number": "Q-2026-0122-001",
    "total": 525844
  }
}
```

---

### 견적 생성

부품 목록으로 견적서를 생성합니다.

**POST** `/quotegenerator`

**Content-Type**: `application/json`

**요청 본문**:
```json
{
  "customer_id": "DSE",
  "parts": [
    {"no": "1", "description": "RING UPPER", "material": "SF45A", "qty": 1, "weight": 25}
  ]
}
```

**응답 예시**:
```json
{
  "quote_number": "Q-2026-0122-001",
  "items": [
    {
      "no": "1",
      "description": "RING UPPER",
      "material": "SF45A",
      "qty": 1,
      "unit_price": 162500,
      "total_price": 162500
    }
  ],
  "subtotal": 162500,
  "discount": 8125,
  "tax": 16250,
  "total": 170625,
  "currency": "KRW"
}
```

---

### 견적서 내보내기 (Excel)

견적 데이터를 Excel 파일로 다운로드합니다.

**POST** `/quote/export/excel`

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| quote_data | JSON string | O | 견적 데이터 |
| customer_id | string | X | 고객 ID |

```bash
curl -X POST http://localhost:8000/api/v1/dsebearing/quote/export/excel \
  -F "quote_data={\"quote_number\":\"Q-TEST-001\",\"items\":[...],\"total\":100000}" \
  -F "customer_id=DSE" \
  --output quote.xlsx
```

---

### 견적서 내보내기 (PDF)

견적 데이터를 PDF 파일로 다운로드합니다.

**POST** `/quote/export/pdf`

```bash
curl -X POST http://localhost:8000/api/v1/dsebearing/quote/export/pdf \
  -F "quote_data={...}" \
  -F "customer_id=DSE" \
  --output quote.pdf
```

---

### 가격 정보 조회

#### 재질 목록

**GET** `/prices/materials`

```json
{
  "materials": [
    {"code": "SF45A", "name": "탄소강", "price_per_kg": 5000},
    {"code": "ASTM B23 GR.2", "name": "화이트메탈", "price_per_kg": 25000}
  ]
}
```

#### 가공비 목록

**GET** `/prices/labor`

```json
{
  "labor_costs": [
    {"type": "BEARING", "base_cost": 50000},
    {"type": "PAD", "base_cost": 30000}
  ]
}
```

#### 수량 할인

**GET** `/prices/discounts`

```json
{
  "quantity_discounts": [
    {"min_qty": 10, "discount_rate": 0.05},
    {"min_qty": 50, "discount_rate": 0.10}
  ]
}
```

---

### 고객 정보

#### 고객 목록

**GET** `/customers`

```json
{
  "customers": [
    {"customer_id": "DSE", "customer_name": "DSE Bearing"},
    {"customer_id": "DOOSAN", "customer_name": "두산에너빌리티"}
  ]
}
```

#### 고객 상세

**GET** `/customers/{customer_id}`

```json
{
  "customer_id": "DSE",
  "customer_name": "DSE Bearing",
  "material_discount": 0.05,
  "labor_discount": 0.03,
  "payment_terms": 30
}
```

#### 고객 전체 설정

**GET** `/customers/{customer_id}/full`

```json
{
  "customer": {...},
  "parsing_profile": {
    "profile_id": "dse_bearing",
    "ocr_engine": "edocr2"
  },
  "quote_template": {
    "type": "quote",
    "visible_columns": ["no", "description", "material", "qty", "unit_price", "total_price"]
  }
}
```

---

## 지원 재질

| 코드 | 재질명 | 단가 (KRW/kg) |
|------|--------|---------------|
| SF45A | 탄소강 | 5,000 |
| SF440A | 합금강 | 7,500 |
| SM45C | 기계구조용탄소강 | 6,000 |
| SCM440 | 크롬몰리브덴강 | 8,500 |
| SUS304 | 스테인리스강 | 12,000 |
| SUS316 | 스테인리스강 (316) | 15,000 |
| ASTM B23 GR.2 | 화이트메탈 | 25,000 |
| ASTM B22 GR.4 | 청동 | 18,000 |
| C3604 | 쾌삭황동 | 10,000 |
| A6061 | 알루미늄합금 | 8,000 |
| PTFE | 테프론 | 20,000 |
| PEEK | 피크 | 50,000 |

---

## 고객별 할인

| 고객 | 재료비 할인 | 가공비 할인 | 결제 조건 |
|------|-------------|-------------|-----------|
| DSE | 5% | 3% | 30일 |
| DOOSAN | 8% | 5% | 45일 |

---

## 수량 할인

| 수량 | 할인율 |
|------|--------|
| 1-9 | 0% |
| 10-49 | 5% |
| 50-99 | 10% |
| 100+ | 15% |

---

## 에러 코드

| HTTP 코드 | 설명 |
|-----------|------|
| 200 | 성공 |
| 400 | 잘못된 요청 (파라미터 누락) |
| 404 | 고객/재질 없음 |
| 415 | 지원하지 않는 파일 형식 |
| 500 | 서버 오류 |

---

## 연동 예시

### Python

```python
import httpx
import asyncio

async def create_quote():
    async with httpx.AsyncClient() as client:
        # 1. Title Block 파싱
        with open("drawing.png", "rb") as f:
            resp = await client.post(
                "http://localhost:8000/api/v1/dsebearing/titleblock",
                files={"file": ("drawing.png", f, "image/png")},
                data={"profile": "bearing"}
            )
            titleblock = resp.json()

        # 2. 견적 생성
        resp = await client.post(
            "http://localhost:8000/api/v1/dsebearing/quotegenerator",
            json={
                "customer_id": "DSE",
                "parts": [
                    {"no": "1", "description": "RING", "material": "SF45A", "qty": 1, "weight": 25}
                ]
            }
        )
        quote = resp.json()
        print(f"견적 총액: {quote['total']:,} KRW")

asyncio.run(create_quote())
```

### JavaScript (Fetch)

```javascript
async function createQuote() {
  // 견적 생성
  const response = await fetch('http://localhost:8000/api/v1/dsebearing/quotegenerator', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      customer_id: 'DSE',
      parts: [
        { no: '1', description: 'RING', material: 'SF45A', qty: 1, weight: 25 }
      ]
    })
  });

  const quote = await response.json();
  console.log(`견적 총액: ${quote.total.toLocaleString()} KRW`);
}
```

---

## BlueprintFlow 통합

web-ui의 BlueprintFlow에서 "DSE Bearing 견적 파이프라인" 템플릿을 사용할 수 있습니다.

1. http://localhost:5173/blueprintflow/builder 접속
2. Templates > DSE Bearing 견적 파이프라인 선택
3. 도면 이미지 업로드
4. Run Pipeline 실행

---

## 테스트

```bash
# 단위 테스트
cd gateway-api
python3 -m pytest tests/unit/test_dsebearing_services.py -v

# E2E 테스트
python3 tests/e2e/test_dsebearing_pipeline.py
```

---

## 관련 문서

- API 스펙: `/gateway-api/api_specs/dsebearing.yaml`
- 서비스 코드: `/gateway-api/services/`
  - `dsebearing_parser.py` - 파싱 로직
  - `price_database.py` - 가격 데이터베이스
  - `customer_config.py` - 고객 설정
  - `quote_exporter.py` - Excel/PDF 출력
- 라우터: `/gateway-api/routers/dsebearing_router.py`
