---
description: Add a new feature to an API following modular structure (project)
---

Please add a new feature to the specified API following this workflow:

## 0. Feature Contract

Before implementation, define the current feature boundary.

```xml
<contract>
  <goal>Add one feature with the minimum safe change set</goal>
  <scope>Only the target API, directly related modules, specs, and tests</scope>
  <success_definition>Feature implemented + minimum verification passed</success_definition>
  <stop_conditions>
    <condition>Stop broadening the design once one implementation path is clearly safe.</condition>
    <condition>Stop and ask or escalate if required API details are missing.</condition>
  </stop_conditions>
</contract>
```

Use a short private scratchpad before edits:

```xml
<think_tool visibility="private">
  <feature_goal/>
  <unknowns/>
  <evidence_needed/>
  <edit_plan/>
  <risk_checks/>
  <exit_test/>
</think_tool>
```

## Pre-Flight Checks

### 1. Risk Assessment
Before starting, analyze the scope:

| Change Type | Risk Level | Requires |
|-------------|------------|----------|
| New file only | 🟢 Low | Proceed |
| Modify existing code | 🟡 Medium | User approval |
| API endpoint change | 🟠 High | Detailed review |
| Breaking change | 🔴 Critical | Explicit confirmation |

### 2. Dry-Run Preview (Optional)
```
Would create:
  - gateway-api/services/new_service.py (~50 lines)
  - gateway-api/api_specs/new-api.yaml (~80 lines)

Would modify:
  - gateway-api/services/__init__.py (+2 lines)
  - docker-compose.yml (+15 lines)

Risk Level: 🟡 Medium
Proceed? (Y/n)
```

Early-stop rules:
- if one safe scaffold pattern already matches the project, stop comparing alternatives
- if the change becomes High/Critical risk, narrow scope or escalate before editing
- if verification fails repeatedly, switch to Reflector summary instead of continuing blind edits

---

## Implementation Steps

### Step 1: Create Service Module

Example for Gateway API adding Tesseract OCR:
```python
# gateway-api/services/tesseract_service.py
import httpx
from typing import Dict
import os

TESSERACT_API_URL = os.getenv("TESSERACT_API_URL", "http://tesseract-api:5008")

async def call_tesseract_ocr(
    file_bytes: bytes,
    filename: str = "image.jpg",
    language: str = "kor+eng"
) -> Dict:
    """Tesseract OCR API 호출"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{TESSERACT_API_URL}/api/v1/ocr",
            files={"file": (filename, file_bytes, "image/jpeg")},
            data={"language": language}
        )
        response.raise_for_status()
        return response.json()
```

### Step 2: Export from __init__.py
```python
# gateway-api/services/__init__.py
from .tesseract_service import call_tesseract_ocr

__all__ = [
    # ... existing
    "call_tesseract_ocr"
]
```

### Step 3: Create API Spec (if new API)
```yaml
# gateway-api/api_specs/tesseract.yaml
name: tesseract
version: "1.0.0"
display_name: Tesseract OCR
category: ocr
description: Open-source OCR engine

container:
  service_name: tesseract-api
  port: 5008
  health_endpoint: /api/v1/health

parameters:
  - name: language
    type: select
    default: "kor+eng"
    options: ["kor", "eng", "kor+eng", "jpn"]
    description: OCR language
```

### Step 4: Add Response Model (if needed)
```python
# gateway-api/models/response.py
class TesseractResults(BaseModel):
    text: str
    confidence: float
    language: str
    processing_time: float
```

### Step 5: Create Executor (for BlueprintFlow)
```python
# gateway-api/blueprintflow/executors/tesseract_executor.py
from ..executors.base_executor import BaseNodeExecutor
from ..executors.executor_registry import ExecutorRegistry
from services import call_tesseract_ocr

class TesseractExecutor(BaseNodeExecutor):
    """Tesseract OCR 실행기"""

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        file_bytes = prepare_image_for_api(inputs, context)
        language = self.parameters.get("language", "kor+eng")

        result = await call_tesseract_ocr(
            file_bytes=file_bytes,
            language=language
        )

        return {
            "text": result.get("text", ""),
            "confidence": result.get("confidence", 0),
        }

# 실행기 등록
ExecutorRegistry.register("tesseract", TesseractExecutor)
```

### Step 6: Use in api_server.py (if direct API call needed)
```python
from services import call_tesseract_ocr

@app.post("/api/v1/process")
async def process_drawing(...):
    tesseract_results = await call_tesseract_ocr(file_bytes)
```

---

## Quality Gate Checks

### Backend
```bash
# Import 검증
cd gateway-api
python -c "from services import call_tesseract_ocr"

# 테스트 실행
pytest tests/ -v -k "tesseract"
```

### Docker
```bash
# 설정 검증
docker-compose config

# 서비스 재시작
docker-compose restart gateway-api

# 로그 확인
docker logs gateway-api -f
```

### API Health Check
```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:5008/api/v1/health  # 새 API
```

### Failure Summary Before Retry

If validation fails, summarize before changing more files:

```xml
<reflector>
  <failed_check/>
  <confirmed_facts/>
  <discarded_hypotheses/>
  <root_cause_candidate/>
  <next_action/>
</reflector>
```

---

## Post-Implementation

### Update Documentation
- [ ] `CLAUDE.md` - API 서비스 목록 업데이트
- [ ] `gateway-api/api_specs/` - 스펙 파일 추가
- [ ] Dashboard 설정 (APIStatusMonitor.tsx, APIDetail.tsx)

### Git Commit
```bash
git add .
git commit -m "feat: Add Tesseract OCR service

- Add tesseract_service.py with call_tesseract_ocr()
- Add TesseractExecutor for BlueprintFlow
- Add API spec tesseract.yaml
- Register in executor_registry

🤖 Generated with [Claude Code](https://claude.com/claude-code)"
```

---

## Risk Mitigation

### Escalate to Codex Cross-Check When
- High or Critical change cannot be reduced
- two implementation options remain after local inspection
- validation fails more than twice with conflicting signals

Prepare a compact packet using:
- `/home/uproot/ax/poc/.claude/commands/codex-cross-check.md`
- `/home/uproot/ax/poc/.claude/templates/codex-cross-check-system-prompt.xml`

### If Something Breaks:
```bash
# 롤백
git checkout -- gateway-api/services/

# 컨테이너 재시작
docker-compose restart gateway-api

# 로그 확인
docker logs gateway-api --tail 100 | grep ERROR
```

### Common Issues:
| Issue | Solution |
|-------|----------|
| Import error | `__init__.py`에 export 추가 |
| Connection refused | 컨테이너 health check 확인 |
| Timeout | httpx timeout 값 증가 |
| Type error | Pydantic 모델 스키마 확인 |
