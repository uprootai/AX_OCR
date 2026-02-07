#!/bin/bash
# Docker GPU Auto-Detection Entrypoint Script
# 컨테이너 시작 시 GPU 가용성을 체크하고 환경변수를 설정합니다.
#
# 사용법:
#   1. Dockerfile에서 COPY 및 ENTRYPOINT 설정
#   2. 환경변수 USE_GPU=auto|true|false (기본값: auto)
#
# 설정되는 환경변수:
#   - GPU_AVAILABLE: true/false
#   - GPU_COUNT: 사용 가능한 GPU 수
#   - GPU_NAME: GPU 이름 (있는 경우)
#   - CUDA_VISIBLE_DEVICES: (USE_GPU=false인 경우 빈 문자열)

set -e

# ========================================
# GPU 감지 함수
# ========================================

detect_gpu() {
    local gpu_available="false"
    local gpu_count=0
    local gpu_name=""

    # Method 1: nvidia-smi 명령 체크
    if command -v nvidia-smi &> /dev/null; then
        if nvidia-smi &> /dev/null; then
            gpu_available="true"
            gpu_count=$(nvidia-smi --query-gpu=count --format=csv,noheader,nounits 2>/dev/null | head -1 || echo "0")
            gpu_name=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || echo "Unknown")
        fi
    fi

    # Method 2: /dev/nvidia* 디바이스 체크 (nvidia-smi 없는 경우)
    if [[ "$gpu_available" == "false" ]] && [[ -e /dev/nvidia0 ]]; then
        gpu_available="true"
        gpu_count=$(ls /dev/nvidia* 2>/dev/null | grep -c "nvidia[0-9]" || echo "1")
        gpu_name="Unknown (detected via /dev/nvidia*)"
    fi

    # Method 3: PyTorch CUDA 체크 (Python 사용 가능한 경우)
    if [[ "$gpu_available" == "false" ]] && command -v python &> /dev/null; then
        local torch_cuda=$(python -c "import torch; print(torch.cuda.is_available())" 2>/dev/null || echo "False")
        if [[ "$torch_cuda" == "True" ]]; then
            gpu_available="true"
            gpu_count=$(python -c "import torch; print(torch.cuda.device_count())" 2>/dev/null || echo "1")
            gpu_name=$(python -c "import torch; print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'Unknown')" 2>/dev/null || echo "Unknown")
        fi
    fi

    # 환경변수 내보내기
    export GPU_AVAILABLE="$gpu_available"
    export GPU_COUNT="$gpu_count"
    export GPU_NAME="$gpu_name"
}

# ========================================
# 메인 로직
# ========================================

# GPU 감지 실행
detect_gpu

# USE_GPU 환경변수 처리 (기본값: auto)
USE_GPU="${USE_GPU:-auto}"

case "$USE_GPU" in
    "true")
        if [[ "$GPU_AVAILABLE" == "false" ]]; then
            echo "⚠️  Warning: USE_GPU=true but no GPU detected. Falling back to CPU."
            export CUDA_VISIBLE_DEVICES=""
        else
            echo "🚀 GPU Mode: Forced (${GPU_COUNT}x ${GPU_NAME})"
        fi
        ;;
    "false")
        echo "💻 CPU Mode: Forced (GPU disabled)"
        export CUDA_VISIBLE_DEVICES=""
        export GPU_AVAILABLE="false"
        ;;
    "auto"|*)
        if [[ "$GPU_AVAILABLE" == "true" ]]; then
            echo "🚀 GPU Mode: Auto-detected (${GPU_COUNT}x ${GPU_NAME})"
        else
            echo "💻 CPU Mode: Auto-detected (no GPU available)"
        fi
        ;;
esac

# 시작 로그
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 GPU Detection Summary"
echo "   GPU_AVAILABLE: $GPU_AVAILABLE"
echo "   GPU_COUNT: $GPU_COUNT"
echo "   GPU_NAME: $GPU_NAME"
echo "   USE_GPU: $USE_GPU"
echo "   CUDA_VISIBLE_DEVICES: ${CUDA_VISIBLE_DEVICES:-all}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 원래 명령 실행
exec "$@"
