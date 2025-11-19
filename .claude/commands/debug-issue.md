---
description: Debug common issues following systematic workflow
---

Please debug the issue using this systematic approach:

## 1. Check Logs
```bash
# Gateway API errors
docker logs gateway-api --tail 100 | grep ERROR

# Specific service errors
docker logs <service-name> --tail 50

# Look for exceptions
docker logs gateway-api | grep -A 10 "Exception in ASGI"
```

## 2. Common Issue Patterns

### "바운딩박스 값이 안나와요" (OCR values not showing)
1. Check if OCR is returning data:
   ```bash
   docker logs gateway-api | grep "eDOCr2 완료"
   # Should see: "eDOCr2 완료: N개 치수 추출"
   ```
2. If N=0, check data structure access in code
3. Verify matching logic is working

### API 500 Error
1. Look for Pydantic validation errors:
   ```bash
   docker logs gateway-api | grep "ResponseValidationError"
   ```
2. Check model definitions in models/response.py
3. Verify data types match API response

### Container Unhealthy
1. Check status: `docker ps | grep unhealthy`
2. Check health endpoint: `curl http://localhost:<port>/api/v1/health`
3. Restart: `docker-compose restart <service-name>`
4. If still failing, rebuild:
   ```bash
   docker-compose build <service-name>
   docker-compose up -d <service-name>
   ```

## 3. Document in KNOWN_ISSUES.md
If this is a new issue, add it to KNOWN_ISSUES.md following the template
