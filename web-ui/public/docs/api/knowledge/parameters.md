# Knowledge Engine API

> **GraphRAG + VectorRAG 하이브리드 도메인 지식 검색 엔진**

---

## 기본 정보

| 항목 | 값 |
|------|-----|
| **포트** | 5007 |
| **엔드포인트** | `POST /api/v1/hybrid/search` |
| **GPU 필요** | ❌ CPU 전용 |
| **RAM** | ~2GB (+ Neo4j) |

---

## 파라미터

### search_mode (검색 모드)

| 값 | 설명 | 특징 |
|----|------|------|
| `graphrag` | 그래프 기반 검색 | 관계 중심, 빠름 |
| `vectorrag` | 벡터 유사도 검색 | 의미 중심, 정확 |
| `hybrid` | 하이브리드 (기본) | 둘 다 활용, 최적 |

- **타입**: select
- **기본값**: `hybrid`

### graph_weight (GraphRAG 가중치)

하이브리드 검색 시 GraphRAG 결과의 가중치입니다.

- **타입**: number (0.0 ~ 1.0)
- **기본값**: `0.6`
- **팁**: VectorRAG 가중치는 `1 - graph_weight`

### top_k (검색 결과 개수)

반환할 검색 결과의 최대 개수입니다.

- **타입**: number (1 ~ 20)
- **기본값**: `5`

### validate_standards (규격 검증)

ISO/ASME 규격 준수 여부를 검증합니다.

- **타입**: boolean
- **기본값**: `false`

### include_cost (비용 정보 포함)

과거 프로젝트의 비용 정보를 포함합니다.

- **타입**: boolean
- **기본값**: `true`

### material_filter (재질 필터)

특정 재질로 검색 결과를 필터링합니다.

- **타입**: string
- **기본값**: `` (빈 값 = 필터 없음)
- **예시**: `SUS304`, `Al6061`, `SS400`

---

## 입력

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `query` | string | ❌ | 검색 쿼리 텍스트 |
| `dimensions` | string[] | ❌ | 치수 정보 배열 |
| `tolerance` | string | ❌ | 공차 등급 (H7 등) |
| `material` | string | ❌ | 재질 정보 |

---

## 출력

| 필드 | 타입 | 설명 |
|------|------|------|
| `results` | array | 검색 결과 목록 |
| `similar_parts` | array | 유사 부품 목록 |
| `total_found` | number | 총 검색 결과 수 |

### result 객체 구조

```json
{
  "part_id": "P-2024-0123",
  "name": "축 브라켓",
  "similarity": 0.92,
  "dimensions": ["85mm", "120mm", "45mm"],
  "material": "SUS304",
  "tolerance": "H7",
  "cost_history": [
    {"date": "2024-01", "cost": 15000},
    {"date": "2024-06", "cost": 14500}
  ]
}
```

---

## 사용 예시

### curl
```bash
curl -X POST http://localhost:5007/api/v1/hybrid/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "베어링 하우징",
    "dimensions": ["50mm", "80mm"],
    "search_mode": "hybrid",
    "top_k": 5
  }'
```

### Python
```python
import requests

data = {
    "query": "베어링 하우징",
    "dimensions": ["50mm", "80mm"],
    "tolerance": "H7",
    "search_mode": "hybrid",
    "graph_weight": 0.6,
    "top_k": 5,
    "include_cost": True
}

response = requests.post(
    "http://localhost:5007/api/v1/hybrid/search",
    json=data
)
print(response.json())
```

---

## 검색 모드 비교

| 모드 | 속도 | 정확도 | 용도 |
|------|------|--------|------|
| graphrag | 빠름 | 관계 중심 | 연결된 부품 찾기 |
| vectorrag | 보통 | 의미 중심 | 유사 부품 찾기 |
| hybrid | 보통 | 최고 | 종합 검색 |

---

## 권장 파이프라인

### 치수 기반 유사 부품 검색
```
ImageInput → eDOCr2 → Knowledge (dimensions 입력)
```

### 공차 기반 과거 프로젝트 검색
```
ImageInput → SkinModel → Knowledge (tolerance 입력)
```

### 전체 분석 파이프라인
```
ImageInput → YOLO → eDOCr2 → SkinModel → Knowledge
```

---

## 리소스 요구사항

| 항목 | 최소 | 권장 |
|------|------|------|
| RAM | 1GB | 2GB |
| CPU 코어 | 2 | 4 |
| Neo4j | 별도 필요 | 4GB RAM |

---

**마지막 업데이트**: 2025-12-09
