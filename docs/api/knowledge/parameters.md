# Knowledge API Parameters

> GraphRAG + VectorRAG 기반 도메인 지식 엔진
> **최종 업데이트**: 2026-01-17 | **버전**: 1.0.0

## 기본 정보

| 항목 | 값 |
|------|-----|
| **Port** | 5007 |
| **Main Endpoints** | `/api/v1/hybrid/search`, `/api/v1/graph/component` |
| **Method** | POST |
| **Content-Type** | application/json |
| **Timeout** | 30초 |

## 파라미터

### search_mode
| 항목 | 값 |
|------|-----|
| **타입** | select |
| **기본값** | `hybrid` |
| **옵션** | `graphrag`, `vectorrag`, `hybrid` |
| **설명** | 검색 모드 선택 |

- **graphrag**: 관계 기반 검색 (Neo4j 그래프 탐색)
- **vectorrag**: 의미 기반 유사도 검색 (벡터 임베딩)
- **hybrid**: 두 방식을 결합한 최적 검색

### graph_weight
| 항목 | 값 |
|------|-----|
| **타입** | number |
| **기본값** | `0.6` |
| **범위** | 0 ~ 1 (step: 0.1) |
| **설명** | Hybrid 모드에서 GraphRAG 가중치 |

### top_k
| 항목 | 값 |
|------|-----|
| **타입** | number |
| **기본값** | `5` |
| **범위** | 1 ~ 20 (step: 1) |
| **설명** | 검색 결과 개수 |

### validate_standards
| 항목 | 값 |
|------|-----|
| **타입** | boolean |
| **기본값** | `false` |
| **설명** | ISO/ASME 규격 검증 활성화 |

### include_cost
| 항목 | 값 |
|------|-----|
| **타입** | boolean |
| **기본값** | `true` |
| **설명** | 과거 비용 정보 포함 여부 |

### material_filter
| 항목 | 값 |
|------|-----|
| **타입** | string |
| **기본값** | `""` (빈 문자열) |
| **설명** | 재질 필터 (빈 값은 필터 없음) |

## 입력

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `query` | string | ❌ | 검색 쿼리 텍스트 |
| `dimensions` | string[] | ❌ | 치수 정보 |
| `tolerance` | string | ❌ | 공차 등급 (예: H7) |
| `material` | string | ❌ | 재질 정보 |

## 출력

| 필드 | 타입 | 설명 |
|------|------|------|
| `results` | SearchResult[] | 검색 결과 목록 |
| `similar_parts` | Part[] | 유사 부품 목록 |
| `total_found` | number | 검색된 총 결과 수 |

---

## Component 생성 (`/api/v1/graph/component`)

### 입력 파라미터

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `name` | string | ✅ | 부품명 |
| `part_id` | string | ❌ | 부품 ID (미지정시 UUID 자동생성) |
| `category` | string | ❌ | 카테고리 (transformer, circuit_breaker 등) |
| `manufacturer` | string | ❌ | 제조사 |
| `unit_price` | number | ❌ | 단가 |
| `specifications` | object | ❌ | 사양 정보 (JSON) |
| `material` | string | ❌ | 재질 |
| `dimensions` | DimensionInfo[] | ❌ | 치수 정보 |
| `tolerances` | ToleranceInfo[] | ❌ | 공차 정보 |
| `processes` | ProcessInfo[] | ❌ | 필요 공정 |
| `metadata` | object | ❌ | 추가 메타데이터 |

### 응답 예시

```json
{
  "status": "success",
  "component_id": "TR-001",
  "message": "Component 변압기 3상 22.9kV created successfully"
}
```

---

## 사용 팁

- GraphRAG는 관계 기반 검색에 강합니다
- VectorRAG는 의미 기반 유사도 검색에 강합니다
- Hybrid 모드가 가장 정확합니다
- Component 생성 시 `part_id`를 지정하면 해당 ID로 저장됩니다

## 추천 연결

| 소스 노드 | 필드 | 이유 |
|-----------|------|------|
| eDOCr2 | dimensions | 추출된 치수로 유사 부품을 검색합니다 |
| SkinModel | tolerance_prediction | 공차 정보로 과거 프로젝트를 검색합니다 |
