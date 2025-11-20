#!/bin/bash
# Docker 이미지 오프라인 패키지 생성 스크립트
# 온프레미스 설치를 위한 모든 Docker 이미지 export

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
EXPORT_DIR="${PROJECT_ROOT}/offline_package"

echo "============================================"
echo "🐳 Docker 이미지 Export 시작"
echo "============================================"

# Export 디렉토리 생성
mkdir -p "${EXPORT_DIR}"
cd "${EXPORT_DIR}"

# 프로젝트 Docker 이미지 목록
IMAGES=(
    "poc_web-ui:latest"
    "poc_gateway:latest"
    "poc_edocr2:latest"
    "poc_yolo:latest"
    "poc_edgnet:latest"
    "poc_skinmodel:latest"
    "poc_vl:latest"
    "poc_paddleocr:latest"
    "poc_admin-dashboard:latest"
)

# 필요한 베이스 이미지들
BASE_IMAGES=(
    "nginx:alpine"
    "python:3.11-slim"
    "prom/prometheus:latest"
    "grafana/grafana:latest"
)

echo ""
echo "📦 1단계: 프로젝트 Docker 이미지 Export"
echo "----------------------------------------"

for image in "${IMAGES[@]}"; do
    echo "Exporting: $image"
    filename=$(echo "$image" | sed 's/:/_/g' | sed 's/\//_/g')

    if docker image inspect "$image" > /dev/null 2>&1; then
        docker save -o "${filename}.tar" "$image"
        echo "  ✅ Saved to ${filename}.tar"
    else
        echo "  ⚠️  Image not found: $image (skipping)"
    fi
done

echo ""
echo "📦 2단계: 베이스 Docker 이미지 Export"
echo "----------------------------------------"

for image in "${BASE_IMAGES[@]}"; do
    echo "Pulling and exporting: $image"
    filename=$(echo "$image" | sed 's/:/_/g' | sed 's/\//_/g')

    docker pull "$image" || echo "  ⚠️  Failed to pull: $image"
    docker save -o "${filename}.tar" "$image"
    echo "  ✅ Saved to ${filename}.tar"
done

echo ""
echo "📦 3단계: 압축 및 체크섬 생성"
echo "----------------------------------------"

# 압축
echo "Compressing all tar files..."
tar -czf docker_images.tar.gz *.tar

# 체크섬 생성
echo "Generating checksums..."
sha256sum docker_images.tar.gz > docker_images.sha256

# 원본 tar 파일 삭제 (압축본만 유지)
rm -f *.tar

# 패키지 정보 파일 생성
cat > package_info.txt <<EOF
AI Drawing Analysis System - Docker Images Package
===================================================

Export Date: $(date)
Total Images: $((${#IMAGES[@]} + ${#BASE_IMAGES[@]}))

Project Images:
$(printf '  - %s\n' "${IMAGES[@]}")

Base Images:
$(printf '  - %s\n' "${BASE_IMAGES[@]}")

Package Contents:
  - docker_images.tar.gz (compressed Docker images)
  - docker_images.sha256 (checksum for verification)
  - package_info.txt (this file)

Installation:
  1. Verify checksum:
     sha256sum -c docker_images.sha256

  2. Extract:
     tar -xzf docker_images.tar.gz

  3. Load images:
     for img in *.tar; do docker load -i \$img; done

EOF

echo ""
echo "✅ Export 완료!"
echo "----------------------------------------"
echo "패키지 위치: ${EXPORT_DIR}"
echo ""
ls -lh docker_images.tar.gz
echo ""
echo "체크섬:"
cat docker_images.sha256
echo ""
echo "📄 패키지 정보:"
cat package_info.txt
