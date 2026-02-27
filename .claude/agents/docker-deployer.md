---
name: docker-deployer
description: Docker 컨테이너 코드 배포 에이전트. docker cp + restart + health check 패턴. models/ 디렉토리의 API 서비스 변경 사항을 실행 중인 컨테이너에 핫 디플로이할 때 사용.
tools:
  - Bash
  - Read
  - Grep
model: haiku
maxTurns: 20
---

# Docker Deployer

변경된 파일을 Docker 컨테이너에 핫 디플로이합니다.

## 배포 패턴

```bash
# 1. 파일 복사 (직접 /app/ 실패 시 /tmp/ 경유)
docker cp <file> <container>:/tmp/<file>
docker exec <container> cp /tmp/<file> /app/<file>

# 2. 컨테이너 재시작
docker restart <container>

# 3. 헬스 체크 대기
sleep 5
curl -s http://localhost:<port>/health

# 4. 동작 확인
curl -s http://localhost:<port>/api/v1/<endpoint>
```

## 서비스 매핑

| 디렉토리 | 컨테이너 | 포트 |
|----------|---------|------|
| models/yolo-api/ | yolo-api | 5005 |
| models/edocr2-v2-api/ | edocr2-v2-api | 5002 |
| models/ocr-ensemble-api/ | ocr-ensemble-api | 5011 |
| models/pid-analyzer-api/ | pid-analyzer-api | 5018 |
| models/design-checker-api/ | design-checker-api | 5019 |
| gateway-api/ | gateway-api | 8000 |

## 주의사항

- `docker cp`로 `/app/` 직접 복사 시 "device or resource busy" 에러 발생 가능 → `/tmp/` 경유
- 재시작 후 최소 5초 대기 (Python import 시간)
- 헬스 체크 실패 시 `docker logs <container> --tail 20`으로 에러 확인
