# Knowledge Engine API

GraphRAG + VectorRAG 기반 도메인 지식 엔진

## Overview

- **Purpose**: 도메인 지식 검색 및 유사 부품 매칭
- **Port**: 5007
- **GPU**: Not required (CPU only)
- **Backend**: Neo4j Graph DB + Vector Search

## Key Features

| Feature | Description |
|---------|-------------|
| **GraphRAG** | 관계 기반 그래프 검색 |
| **VectorRAG** | 의미 기반 벡터 유사도 검색 |
| **Hybrid Mode** | GraphRAG + VectorRAG 결합 |
| **ISO Validation** | ISO/ASME 규격 검증 |
| **Cost Lookup** | 과거 비용 정보 조회 |

## Quick Start (Standalone)

### Prerequisites
- Docker & Docker Compose
- Neo4j Database (별도 구성 필요)

### 1. Run the API

```bash
cd models/knowledge-api
docker-compose -f docker-compose.single.yml up -d
docker logs knowledge-api-standalone -f
```

### 2. Check Health

```bash
curl http://localhost:5007/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "knowledge-api",
  "version": "1.0.0",
  "neo4j_connected": true,
  "vector_index": "ready"
}
```

### 3. API Documentation

Open in browser: **http://localhost:5007/docs**

## API Endpoints

### Health Check
```bash
GET /api/v1/health
```

### Hybrid Search
```bash
POST /api/v1/hybrid/search
Content-Type: application/json

Body:
{
  "query": "Ø25 H7 부품",
  "dimensions": ["25", "H7"],
  "search_mode": "hybrid",
  "graph_weight": 0.6,
  "top_k": 5,
  "include_cost": true,
  "material_filter": ""
}
```

### GraphRAG Search
```bash
POST /api/v1/graphrag/search
```

### VectorRAG Search
```bash
POST /api/v1/vectorrag/search
```

## Testing

```bash
curl -X POST http://localhost:5007/api/v1/hybrid/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Ø25 H7 shaft",
    "dimensions": ["25", "H7"],
    "search_mode": "hybrid",
    "top_k": 5
  }'
```

## Response Example

```json
{
  "status": "success",
  "data": {
    "results": [
      {
        "id": "PART-001",
        "name": "Shaft Ø25 H7",
        "similarity": 0.95,
        "material": "SUS304",
        "cost": 15000
      }
    ],
    "similar_parts": [
      {
        "part_number": "PART-001",
        "dimensions": ["Ø25", "H7"],
        "projects": ["PRJ-2024-001", "PRJ-2024-005"]
      }
    ],
    "total_found": 12
  },
  "processing_time": 0.35
}
```

## Search Modes

| Mode | Description | Speed | Accuracy |
|------|-------------|-------|----------|
| `graphrag` | 관계 기반 검색 | Fast | Good for relationships |
| `vectorrag` | 의미 유사도 검색 | Medium | Good for semantics |
| `hybrid` | 두 방식 결합 | Slower | Best accuracy |

## Docker Image Distribution

### Build Image
```bash
docker build -t ax-knowledge-api:latest .
```

### Run Standalone Container
```bash
docker run -d \
  --name knowledge-api \
  -p 5007:5007 \
  -e NEO4J_URI=bolt://neo4j:7687 \
  -e NEO4J_USER=neo4j \
  -e NEO4J_PASSWORD=password \
  ax-knowledge-api:latest
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `KNOWLEDGE_PORT` | 5007 | API server port |
| `NEO4J_URI` | bolt://neo4j:7687 | Neo4j connection URI |
| `NEO4J_USER` | neo4j | Neo4j username |
| `NEO4J_PASSWORD` | password | Neo4j password |
| `VECTOR_DB_PATH` | /app/vector_db | Vector index path |

## Performance

| Metric | Value |
|--------|-------|
| GraphRAG search | ~0.1s |
| VectorRAG search | ~0.2s |
| Hybrid search | ~0.3s |
| Memory | ~2GB |

## Project Structure

```
knowledge-api/
├── Dockerfile
├── README.md
├── api_server.py
├── services/
│   ├── graphrag_service.py
│   └── vectorrag_service.py
├── models/
│   └── schemas.py
├── neo4j/
│   └── queries.py
├── requirements.txt
└── vector_db/
```

## Integration with AX PoC

This API is part of the **AX Drawing Analysis System**.

- **Main Project**: [ax-poc](https://github.com/your-org/ax-poc)
- **Usage in Pipeline**: Knowledge lookup after analysis
- **Inputs**: Dimensions from eDOCr2, tolerance from SkinModel

### Pipeline Integration

```python
# Search for similar parts based on extracted dimensions
knowledge_result = knowledge_api.search(
    query="shaft",
    dimensions=["Ø25", "H7"],
    search_mode="hybrid"
)
```

## License

Part of the AX Project (2025)

## Support

For issues or questions:
1. Check API documentation: http://localhost:5007/docs
2. Review logs: `docker logs knowledge-api-standalone`
3. Contact: AX Project Team

---

**Version**: 1.0.0
**Last Updated**: 2025-12-31
**Maintained By**: AX Project Team
