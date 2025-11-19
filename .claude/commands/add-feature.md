---
description: Add a new feature to an API following modular structure
---

Please add a new feature to the specified API following this workflow:

## 1. Create Service Module

Example for Gateway API adding Tesseract OCR:
```bash
cd gateway-api/services
cat > tesseract_service.py << 'EOF'
async def call_tesseract_ocr(image_bytes: bytes) -> Dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{TESSERACT_API_URL}/api/v1/ocr",
            files={"file": ("image.jpg", image_bytes, "image/jpeg")}
        )
        return response.json()
EOF
```

## 2. Export from __init__.py
```python
# services/__init__.py
from .tesseract_service import call_tesseract_ocr

__all__ = [
    # ... existing
    "call_tesseract_ocr"
]
```

## 3. Add Response Model (if needed)
```python
# models/response.py
class TesseractResults(BaseModel):
    text: str
    confidence: float
```

## 4. Use in api_server.py
```python
from services import call_tesseract_ocr

@app.post("/api/v1/process")
async def process_drawing(...):
    tesseract_results = await call_tesseract_ocr(file_bytes)
```

## 5. Test
```bash
docker-compose restart gateway-api
docker logs gateway-api -f
```

## 6. Update Documentation
- Update WORKFLOWS.md if new workflow
- Update ROADMAP.md with completion status
- Add to CHANGELOG if significant feature
