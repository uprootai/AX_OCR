# 🔧 Common Workflows

**Step-by-step guides for frequent tasks**

---

## 🚀 Development Workflows

### Add New Feature to API

**Example**: Add Tesseract OCR to Gateway

1. **Create service module**
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

2. **Export from __init__.py**
```python
# services/__init__.py
from .tesseract_service import call_tesseract_ocr

__all__ = [
    # ... existing
    "call_tesseract_ocr"
]
```

3. **Add response model** (if needed)
```python
# models/response.py
class TesseractResults(BaseModel):
    text: str
    confidence: float
```

4. **Use in api_server.py**
```python
from services import call_tesseract_ocr

@app.post("/api/v1/process")
async def process_drawing(...):
    tesseract_results = await call_tesseract_ocr(file_bytes)
```

5. **Test**
```bash
docker-compose restart gateway-api
docker logs gateway-api -f
```

---

### Modify Existing Function

**Example**: Change YOLO confidence threshold default

1. **Find the service file**
```bash
grep -r "conf_threshold" yolo-api/services/
# Result: services/inference.py:145
```

2. **Edit the file**
```python
# services/inference.py (Line 145)
def predict(
    self,
    image_bytes: bytes,
    conf_threshold: float = 0.30,  # ← Changed from 0.25
    ...
):
```

3. **Restart and test**
```bash
docker-compose restart yolo-api
curl -X POST -F "file=@test.jpg" http://localhost:5005/api/v1/detect
```

---

### Delete Deprecated Feature

**Example**: Remove PaddleOCR from Gateway

1. **Delete service file**
```bash
rm gateway-api/services/paddleocr_service.py
```

2. **Remove from __init__.py**
```python
# Remove: from .paddleocr_service import call_paddleocr_detect
```

3. **Remove from api_server.py**
```python
# Remove: from services import call_paddleocr_detect
# Remove: paddleocr_results = await call_paddleocr_detect(...)
```

4. **Verify no references**
```bash
grep -r "paddleocr" gateway-api/
# Should return empty
```

5. **Test**
```bash
docker-compose restart gateway-api
```

---

## 🐛 Debugging Workflows

### Debug API 500 Error

1. **Check logs**
```bash
docker logs gateway-api --tail 100 | grep ERROR
```

2. **Look for Pydantic validation errors**
```bash
docker logs gateway-api | grep "ResponseValidationError"
```

3. **Check specific error details**
```bash
docker logs gateway-api | grep -A 10 "Exception in ASGI"
```

4. **Common fixes**:
   - Pydantic model mismatch → Check models/response.py
   - Import error → Check __init__.py exports
   - Async error → Check await keywords

---

### Debug "바운딩박스 값이 안나와요"

1. **Check OCR is returning data**
```bash
docker logs gateway-api | grep "eDOCr2 완료"
# Should see: "eDOCr2 완료: N개 치수 추출"
```

2. **If N=0, check data structure**
```python
# Check if accessing nested keys correctly
# WRONG: results.get("data", {}).get("dimensions")
# RIGHT: results.get("dimensions")
```

3. **Verify matching logic**
```bash
docker logs gateway-api | grep "Matching YOLO"
# Should see successful matching
```

---

### Debug Container Unhealthy

1. **Check status**
```bash
docker ps | grep unhealthy
```

2. **Check container logs**
```bash
docker logs <container-name> --tail 50
```

3. **Check health endpoint**
```bash
curl http://localhost:<port>/api/v1/health
```

4. **Restart container**
```bash
docker-compose restart <service-name>
```

5. **If still failing, rebuild**
```bash
docker-compose build <service-name>
docker-compose up -d <service-name>
```

---

## 🧪 Testing Workflows

### Test Individual API

```bash
# YOLO API
curl -X POST \
  -F "file=@test.jpg" \
  -F "conf_threshold=0.25" \
  -F "visualize=true" \
  http://localhost:5005/api/v1/detect

# eDOCr2 v2
curl -X POST \
  -F "file=@test.jpg" \
  http://localhost:5002/api/v2/ocr

# PaddleOCR
curl -X POST \
  -F "file=@test.jpg" \
  -F "lang=en" \
  http://localhost:5006/api/v1/ocr
```

### Test Gateway Pipeline

**Speed Mode**:
```bash
curl -X POST \
  -F "file=@test.jpg" \
  -F "pipeline_mode=speed" \
  -F "use_ocr=true" \
  -F "use_segmentation=false" \
  -F "use_tolerance=true" \
  -F "visualize=true" \
  http://localhost:8000/api/v1/process | jq .
```

**Hybrid Mode**:
```bash
curl -X POST \
  -F "file=@test.jpg" \
  -F "pipeline_mode=hybrid" \
  -F "use_ocr=true" \
  -F "use_yolo_crop_ocr=true" \
  -F "use_ensemble=true" \
  -F "visualize=true" \
  http://localhost:8000/api/v1/process | jq .
```

---

## 🐳 Docker Workflows

### Rebuild Single Service

```bash
# Stop service
docker-compose stop gateway-api

# Rebuild
docker-compose build gateway-api

# Start
docker-compose up -d gateway-api

# Check logs
docker logs gateway-api -f
```

### Rebuild All Services

```bash
docker-compose down
docker-compose build
docker-compose up -d
```

### Clean Docker Cache

```bash
# Remove all stopped containers
docker container prune -f

# Remove unused images
docker image prune -f

# Remove all unused data
docker system prune -a
```

---

## 📝 Documentation Workflows

### Update After Code Change

1. **Check if affects user-facing behavior**
   - Yes → Update QUICK_START.md or WORKFLOWS.md
   - No → Only update code comments

2. **Check if affects architecture**
   - Yes → Update ARCHITECTURE.md
   - No → Skip

3. **Check if fixes known issue**
   - Yes → Move from KNOWN_ISSUES.md to Resolved section
   - Yes → Update ROADMAP.md with [x]

4. **Always update**:
   - Add entry to ROADMAP.md if new feature
   - Update CHANGELOG.md (if exists)

---

## 🔄 Git Workflows

### Before Committing

1. **Test locally**
```bash
docker-compose restart <service>
# Verify it works
```

2. **Check for sensitive data**
```bash
grep -r "password\|secret\|key" .
# Make sure nothing leaked
```

3. **Format commit message**
```bash
git add .
git commit -m "feat(gateway): add Tesseract OCR support

- Add tesseract_service.py
- Update services/__init__.py
- Add TesseractResults model
- Test integration

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## ⚠️ Common Pitfalls

### Import Circular Dependencies

**Problem**: `models` imports from `services`, `services` imports from `models`

**Solution**: Follow dependency order
```
models/ → utils/ → services/ → api_server.py
```

### Pydantic Model Changes

**Problem**: Added required field, broke existing API

**Solution**: Always add with default value
```python
# GOOD
class Detection(BaseModel):
    new_field: str = "default"

# BAD
class Detection(BaseModel):
    new_field: str  # ← Required! Breaks API
```

### Dockerfile Module Copy

**Problem**: Added new module, forgot to update Dockerfile

**Solution**: Always add COPY line
```dockerfile
COPY models/ ./models/
COPY services/ ./services/
COPY utils/ ./utils/
COPY new_module/ ./new_module/  # ← Don't forget!
```

---

## 🔗 Related Documents

- [QUICK_START.md](QUICK_START.md) - Quick reference
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [KNOWN_ISSUES.md](KNOWN_ISSUES.md) - Issue tracker
- [ROADMAP.md](ROADMAP.md) - Project roadmap

---

**Last Updated**: 2025-11-19
**Maintained By**: Claude Code Team
