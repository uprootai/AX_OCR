---
description: Test individual API endpoints with various scenarios
---

Please test the specified API endpoint:

1. For **YOLO API** (Port 5005):
   ```bash
   curl -X POST \
     -F "file=@test.jpg" \
     -F "conf_threshold=0.25" \
     -F "visualize=true" \
     http://localhost:5005/api/v1/detect
   ```

2. For **eDOCr2 v2** (Port 5002):
   ```bash
   curl -X POST \
     -F "file=@test.jpg" \
     http://localhost:5002/api/v2/ocr
   ```

3. For **PaddleOCR** (Port 5006):
   ```bash
   curl -X POST \
     -F "file=@test.jpg" \
     -F "lang=en" \
     http://localhost:5006/api/v1/ocr
   ```

4. For **Gateway Speed Mode** (Port 8000):
   ```bash
   curl -X POST \
     -F "file=@test.jpg" \
     -F "pipeline_mode=speed" \
     -F "use_ocr=true" \
     -F "visualize=true" \
     http://localhost:8000/api/v1/process | jq .
   ```

5. For **Gateway Hybrid Mode** (Port 8000):
   ```bash
   curl -X POST \
     -F "file=@test.jpg" \
     -F "pipeline_mode=hybrid" \
     -F "use_yolo_crop_ocr=true" \
     -F "use_ensemble=true" \
     -F "visualize=true" \
     http://localhost:8000/api/v1/process | jq .
   ```

Check the response for:
- Status code (should be 200)
- Response structure matches expected schema
- Processing time is within acceptable range
- No errors in logs: `docker logs <service-name> --tail 50`
