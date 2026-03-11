# S05: 관련 API 섹션 추가

> **상태**: ⬜ Todo
> **선행**: S01 (규칙), S04 (섹션 순서 — 위치 확정)
> **산출물**: ~50개 파일에 `## 관련 API` 섹션 추가

---

## 목표

API 엔드포인트와 관련된 문서에 `## 관련 API` 섹션을 추가하여,
문서 → API, API → 문서 양방향 탐색이 가능하게 한다.

## Tasks

### T01 대상 파일 + API 매핑 확정

**대상 기준**: 해당 문서가 설명하는 기능을 수행하는 API가 존재하는 경우

| 카테고리 | 대상 파일 수 | 매핑 예시 |
|---------|-----------|----------|
| system-overview | 4 | → Gateway `/admin/status`, `/health` |
| analysis-pipeline | 6 | → YOLO `/detect`, OCR `/extract`, VLM `/classify` |
| blueprintflow | 5 | → Gateway `/blueprintflow/*` |
| agent-verification | 3 | → Gateway `/verification/*` |
| bom-generation | 4 | → Blueprint AI BOM `/api/v1/*` |
| pid-analysis | 4 | → PID Analyzer `/api/v1/*` |
| batch-delivery | 3 | → Gateway `/projects/*`, `/export/*` |
| quality-assurance | 4 | → Gateway `/qa/*`, `/feedback/*` |
| frontend | 6 | → 각 페이지가 호출하는 API |
| devops | 3 | → Gateway `/admin/docker/*` |
| deployment | 2 | → 설치/운영 관련 API |
| **합계** | **~44개** | |

### T02 API 엔드포인트 수집

소스:
- `api_specs/*.yaml` (OpenAPI 스펙)
- `gateway-api/app/routers/*.py` (실제 라우터)
- 기존 `api-reference/*.md` 문서

출력: `scripts/api-endpoint-map.json`
```json
{
  "yolo-detection": {
    "endpoints": [
      { "method": "POST", "path": "/api/v1/detect", "description": "이미지 객체 검출" }
    ],
    "docs": ["analysis-pipeline/yolo-detection.mdx"]
  }
}
```

### T03 섹션 일괄 추가

각 대상 파일의 `## 관련 문서` 바로 위에 삽입:

```markdown
## 관련 API

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| POST | `Gateway /api/v1/detect` | 이미지 객체 검출 |
| GET | `Gateway /health` | 서비스 헬스체크 |
```

### T04 양방향 링크 검증

- 문서 → API: `## 관련 API`의 엔드포인트가 실제 존재하는지
- API → 문서: `api-reference/*.md`의 `## 관련 문서`에 역링크 존재하는지

```bash
node scripts/verify-api-links.mjs
# Output: 0 broken links, 0 missing backlinks
```

## 완료 조건

- [ ] ~50개 파일에 `## 관련 API` 섹션 존재
- [ ] 모든 엔드포인트가 실제 API 스펙과 일치
- [ ] 양방향 링크 정합성 100%
