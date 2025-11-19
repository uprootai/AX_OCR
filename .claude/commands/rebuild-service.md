---
description: Rebuild and restart a Docker service safely
---

Please rebuild the specified service following this workflow:

## Single Service Rebuild

```bash
# 1. Stop service
docker-compose stop <service-name>

# 2. Rebuild
docker-compose build <service-name>

# 3. Start
docker-compose up -d <service-name>

# 4. Check logs
docker logs <service-name> -f
```

## Common Services
- `gateway-api` - Main orchestrator (Port 8000)
- `yolo-api` - Object detection (Port 5005)
- `edocr2-v2-api` - OCR service (Port 5002)
- `paddleocr-api` - Aux OCR (Port 5006)
- `skinmodel-api` - Tolerance (Port 5003)
- `web-ui` - React frontend (Port 5173)

## Rebuild All Services
```bash
docker-compose down
docker-compose build
docker-compose up -d
```

## Verify Health
```bash
# Check all containers
docker ps

# Check specific service health
curl http://localhost:<port>/api/v1/health

# Check logs for errors
docker logs <service-name> --tail 100 | grep ERROR
```

## If Issues Persist
```bash
# Clean Docker cache
docker container prune -f
docker image prune -f

# Full system clean (careful!)
docker system prune -a
```
