#!/bin/bash
set -e

echo "=========================================="
echo "  Blueprint AI BOM - Self-contained Import"
echo "  (Port Offset: +10000)"
echo "=========================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# [1/3] Docker 이미지 로드
echo "[1/3] Loading Docker images..."
for img in docker/images/*.tar.gz; do
    if [ -f "$img" ]; then
        echo "  Loading: $(basename "$img")"
        gunzip -c "$img" | docker load
    fi
done

for img in docker/images/*.tar; do
    if [ -f "$img" ]; then
        echo "  Loading: $(basename "$img")"
        docker load -i "$img"
    fi
done

# [2/3] Docker 네트워크 생성
echo ""
echo "[2/3] Creating Docker network..."
docker network create panasia_network 2>/dev/null || echo "  Network already exists"

# [3/3] 서비스 시작
echo ""
echo "[3/3] Starting services..."
cd docker
docker-compose up -d

echo ""
echo "=========================================="
echo "  Import Complete!"
echo "=========================================="
echo ""
echo "컨테이너 접두사: panasia-"
echo "포트 오프셋: +10000"
echo ""
echo "=========================================="
echo "  UI 접속 URL:"
echo "=========================================="
echo "  ★ http://localhost:13000"
echo ""
echo "API endpoints:"
echo "  - panasia-blueprint-ai-bom-backend: http://localhost:15020"
echo "  - panasia-gateway-api: http://localhost:18000"
echo "  - panasia-yolo-api: http://localhost:15005"

echo ""
echo "서비스 상태 확인:"
echo "  cd docker && docker-compose ps"
echo ""
echo "서비스 중지:"
echo "  cd docker && docker-compose down"
