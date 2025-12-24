#!/bin/bash
# 문서 동기화 스크립트
# 원본: /home/uproot/ax/poc/docs/ → 대상: /home/uproot/ax/poc/web-ui/public/docs/

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEB_UI_DIR="$(dirname "$SCRIPT_DIR")"
SOURCE_DOCS="/home/uproot/ax/poc/docs"
TARGET_DOCS="$WEB_UI_DIR/public/docs"

echo "=========================================="
echo "📄 문서 동기화 스크립트"
echo "=========================================="
echo "원본: $SOURCE_DOCS"
echo "대상: $TARGET_DOCS"
echo ""

synced=0
skipped=0

# 파일 동기화 함수
sync_file() {
    local src="$1"
    local dst="$2"
    local src_path="$SOURCE_DOCS/$src"
    local dst_path="$TARGET_DOCS/$dst"

    if [ -f "$src_path" ]; then
        dst_dir=$(dirname "$dst_path")
        mkdir -p "$dst_dir"

        if [ ! -f "$dst_path" ] || ! cmp -s "$src_path" "$dst_path"; then
            cp "$src_path" "$dst_path"
            echo "  ✅ $dst"
            ((synced++))
        else
            ((skipped++))
        fi
    else
        echo "  ⚠️  원본 없음: $src"
    fi
}

echo "📁 파일 동기화 중..."

# Root level docs
sync_file "INSTALLATION_GUIDE.md" "INSTALLATION_GUIDE.md"
sync_file "TROUBLESHOOTING.md" "TROUBLESHOOTING.md"
sync_file "DEPLOYMENT_GUIDE.md" "DEPLOYMENT_GUIDE.md"
sync_file "ADMIN_MANUAL.md" "ADMIN_MANUAL.md"
sync_file "DYNAMIC_API_SYSTEM_GUIDE.md" "DYNAMIC_API_SYSTEM_GUIDE.md"
sync_file "GPU_CONFIGURATION_EXPLAINED.md" "GPU_CONFIGURATION_EXPLAINED.md"
sync_file "ONPREMISE_DEPLOYMENT_GUIDE.md" "ONPREMISE_DEPLOYMENT_GUIDE.md"

# Developer docs
sync_file "developer/API_SPEC_SYSTEM_GUIDE.md" "developer/API_SPEC_SYSTEM_GUIDE.md"
sync_file "developer/VL_API_SETUP_GUIDE.md" "developer/VL_API_SETUP_GUIDE.md"
sync_file "developer/LLM_USABILITY_GUIDE.md" "LLM_USABILITY_GUIDE.md"
sync_file "developer/API_PARAMETERS_DETAILED_GUIDE.md" "API_PARAMETERS_DETAILED_GUIDE.md"
sync_file "developer/API_REPLACEMENT_GUIDE.md" "API_REPLACEMENT_GUIDE.md"

# BlueprintFlow docs
sync_file "blueprintflow/08_textinput_node_guide.md" "blueprintflow/08_textinput_node_guide.md"
sync_file "blueprintflow/09_vl_textinput_integration.md" "blueprintflow/09_vl_textinput_integration.md"
sync_file "blueprintflow/BLUEPRINTFLOW_API_INTEGRATION_GUIDE.md" "BLUEPRINTFLOW_API_INTEGRATION_GUIDE.md"
sync_file "blueprintflow/BLUEPRINTFLOW_ARCHITECTURE_COMPLETE_DESIGN.md" "BLUEPRINTFLOW_ARCHITECTURE_COMPLETE_DESIGN.md"

# Dockerization docs
sync_file "dockerization/DOCKER_REBUILD_STATUS.md" "DOCKER_REBUILD_STATUS.md"
sync_file "dockerization/2025-11-23_yolo_dockerization_guide.md" "dockerization/2025-11-23_yolo_dockerization_guide.md"
sync_file "dockerization/2025-11-23_paddleocr_dockerization_guide.md" "dockerization/2025-11-23_paddleocr_dockerization_guide.md"

# 디렉토리 동기화
echo ""
echo "📂 디렉토리 동기화 중..."

for dir in papers opensource; do
    src_path="$SOURCE_DOCS/$dir"
    dst_path="$TARGET_DOCS/$dir"

    if [ -d "$src_path" ]; then
        # 기존 대상이 심링크면 삭제
        if [ -L "$dst_path" ]; then
            rm "$dst_path"
        fi

        # rsync로 동기화
        rsync -av --delete --quiet "$src_path/" "$dst_path/" 2>/dev/null || cp -r "$src_path" "$dst_path"
        file_count=$(find "$dst_path" -type f -name "*.md" 2>/dev/null | wc -l)
        echo "  ✅ $dir/ ($file_count개 파일)"
    else
        echo "  ⚠️  원본 디렉토리 없음: $dir"
    fi
done

echo ""
echo "=========================================="
echo "✅ 동기화 완료"
echo "   - 업데이트: $synced개 파일"
echo "   - 변경없음: $skipped개 파일"
echo "=========================================="
