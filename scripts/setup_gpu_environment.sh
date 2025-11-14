#!/bin/bash
# GPU 환경 설정 스크립트
# RTX 3080 Laptop GPU를 활용한 AX 시스템 최적화

set -e

echo "=========================================="
echo "AX GPU Environment Setup"
echo "Target: RTX 3080 Laptop (8GB VRAM)"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check GPU
echo "🔍 Checking GPU..."
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
    echo -e "${GREEN}✅ NVIDIA GPU detected${NC}"
else
    echo -e "${RED}❌ nvidia-smi not found. Please install NVIDIA drivers.${NC}"
    exit 1
fi

echo ""

# Check CUDA
echo "🔍 Checking CUDA..."
if command -v nvcc &> /dev/null; then
    nvcc --version | grep "release"
    echo -e "${GREEN}✅ CUDA toolkit installed${NC}"
else
    echo -e "${YELLOW}⚠️  CUDA toolkit not found (optional for PyTorch)${NC}"
fi

echo ""

# Check Python
echo "🔍 Checking Python..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"

if [[ "$PYTHON_VERSION" < "3.8" ]]; then
    echo -e "${RED}❌ Python 3.8+ required${NC}"
    exit 1
else
    echo -e "${GREEN}✅ Python version OK${NC}"
fi

echo ""

# Install GPU packages
echo "📦 Installing GPU-accelerated packages..."
echo ""

# 1. PyTorch with CUDA 12.1
echo "1️⃣  Installing PyTorch (CUDA 12.1)..."
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 --quiet
echo -e "${GREEN}✅ PyTorch installed${NC}"

# 2. YOLO (Ultralytics)
echo "2️⃣  Installing Ultralytics YOLO..."
pip3 install ultralytics --quiet
echo -e "${GREEN}✅ YOLO installed${NC}"

# 3. PyTorch Geometric (EDGNet)
echo "3️⃣  Installing PyTorch Geometric..."
pip3 install torch-geometric torch-scatter torch-sparse -f https://data.pyg.org/whl/torch-2.1.0+cu121.html --quiet
echo -e "${GREEN}✅ PyTorch Geometric installed${NC}"

# 4. XGBoost GPU (Skin Model)
echo "4️⃣  Installing XGBoost..."
pip3 install xgboost --quiet
echo -e "${GREEN}✅ XGBoost installed${NC}"

# 5. cuPy (GPU image processing)
echo "5️⃣  Installing cuPy (CUDA 12.x)..."
pip3 install cupy-cuda12x --quiet
echo -e "${GREEN}✅ cuPy installed${NC}"

# 6. Optional: DGL (alternative to PyG)
echo "6️⃣  Installing DGL (optional)..."
pip3 install dgl-cu121 -f https://data.dgl.ai/wheels/cu121/repo.html --quiet || echo -e "${YELLOW}⚠️  DGL installation skipped${NC}"

echo ""

# Verify installations
echo "🧪 Verifying GPU support..."
echo ""

# PyTorch CUDA
echo -n "PyTorch CUDA: "
python3 -c "import torch; print('✅ Available' if torch.cuda.is_available() else '❌ Not available')"

# PyTorch GPU name
python3 -c "import torch; print(f'GPU: {torch.cuda.get_device_name(0)}') if torch.cuda.is_available() else None"

# YOLO
echo -n "YOLO: "
python3 -c "from ultralytics import YOLO; print('✅ Available')" 2>/dev/null || echo "❌ Not available"

# PyTorch Geometric
echo -n "PyTorch Geometric: "
python3 -c "import torch_geometric; print('✅ Available')" 2>/dev/null || echo "❌ Not available"

# XGBoost
echo -n "XGBoost: "
python3 -c "import xgboost; print('✅ Available')" 2>/dev/null || echo "❌ Not available"

# cuPy
echo -n "cuPy: "
python3 -c "import cupy; print('✅ Available')" 2>/dev/null || echo "❌ Not available"

echo ""

# Display GPU memory
echo "💾 GPU Memory Status:"
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | \
    awk '{printf "   Used: %d MB / %d MB (%.1f%%)\n", $1, $2, ($1/$2)*100}'

echo ""

# Save configuration
echo "📄 Saving configuration..."
cat > gpu_config.json <<EOF
{
  "gpu_name": "$(nvidia-smi --query-gpu=name --format=csv,noheader)",
  "vram_total_mb": $(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits),
  "driver_version": "$(nvidia-smi --query-gpu=driver_version --format=csv,noheader)",
  "cuda_version": "12.1",
  "pytorch_version": "$(python3 -c 'import torch; print(torch.__version__)' 2>/dev/null || echo 'unknown')",
  "setup_date": "$(date -I)",
  "packages": {
    "torch": "$(python3 -c 'import torch; print(torch.__version__)' 2>/dev/null || echo 'N/A')",
    "ultralytics": "$(python3 -c 'import ultralytics; print(ultralytics.__version__)' 2>/dev/null || echo 'N/A')",
    "torch_geometric": "$(python3 -c 'import torch_geometric; print(torch_geometric.__version__)' 2>/dev/null || echo 'N/A')",
    "xgboost": "$(python3 -c 'import xgboost; print(xgboost.__version__)' 2>/dev/null || echo 'N/A')",
    "cupy": "$(python3 -c 'import cupy; print(cupy.__version__)' 2>/dev/null || echo 'N/A')"
  }
}
EOF

echo -e "${GREEN}✅ Configuration saved to gpu_config.json${NC}"

echo ""
echo "=========================================="
echo "✅ GPU Environment Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Convert YOLO to GPU:"
echo "   python3 scripts/convert_yolo_to_gpu.py"
echo ""
echo "2. Augment EDGNet data:"
echo "   python3 scripts/augment_edgnet_dataset.py"
echo ""
echo "3. Retrain EDGNet with GPU:"
echo "   python3 scripts/retrain_edgnet_gpu.py"
echo ""
echo "Expected improvements:"
echo "- YOLO:        10s → 1-2s      (5-10x faster) ⚡"
echo "- eDOCr2:      23s → 5-8s      (3-5x faster) ⚡"
echo "- EDGNet:      1-2h → 10-20min (6x faster) ⚡"
echo "- Skin Model:  2min → 20s      (6x faster) ⚡"
echo ""
echo "Score improvement: 89 → 95-100 points 🎯"
echo ""
