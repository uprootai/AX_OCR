#!/bin/bash
#
# YOLOv11 학습 파이프라인 (합성 데이터 포함)
#

set -e

echo "========================================================================"
echo "🚀 YOLOv11 Training Pipeline with Synthetic Data"
echo "========================================================================"

# =============================
# Configuration
# =============================

SYNTHETIC_COUNT=1000
MODEL_SIZE="n"
EPOCHS=100
BATCH_SIZE=4  # Reduced from 16 to avoid OOM
DEVICE="0"
IMGSZ=640     # Reduced from 1280 to save memory

# =============================
# Phase 1: Generate Synthetic Data
# =============================

echo ""
echo "📊 Phase 1: Generating Synthetic Data..."
echo "----------------------------------------"

python3 scripts/generate_synthetic_random.py \
    --count ${SYNTHETIC_COUNT} \
    --output datasets/synthetic_random \
    --width 1920 \
    --height 1080

echo "✅ Synthetic data generated: ${SYNTHETIC_COUNT} images"

# =============================
# Phase 2: Check for Real Data
# =============================

echo ""
echo "📂 Phase 2: Checking for Real Data..."
echo "----------------------------------------"

REAL_DATA_PATH="datasets/engineering_drawings"

if [ -d "${REAL_DATA_PATH}" ]; then
    echo "✅ Real data found: ${REAL_DATA_PATH}"

    # Merge datasets
    echo ""
    echo "🔄 Merging synthetic + real datasets..."

    python3 scripts/merge_datasets.py \
        --datasets datasets/synthetic_random ${REAL_DATA_PATH} \
        --output datasets/combined

    TRAINING_DATA="datasets/combined/data.yaml"
    echo "✅ Using combined dataset"
else
    echo "⚠️  No real data found, using synthetic only"
    TRAINING_DATA="datasets/synthetic_random/data.yaml"
fi

# =============================
# Phase 3: Train Model
# =============================

echo ""
echo "🎯 Phase 3: Training YOLOv11..."
echo "----------------------------------------"
echo "Model: yolo11${MODEL_SIZE}"
echo "Data: ${TRAINING_DATA}"
echo "Epochs: ${EPOCHS}"
echo "Batch: ${BATCH_SIZE}"
echo "Device: ${DEVICE}"
echo "----------------------------------------"

python3 scripts/train_yolo.py \
    --model-size ${MODEL_SIZE} \
    --data ${TRAINING_DATA} \
    --epochs ${EPOCHS} \
    --batch ${BATCH_SIZE} \
    --imgsz ${IMGSZ} \
    --workers 2 \
    --device ${DEVICE} \
    --project runs/train \
    --name synthetic_training

echo ""
echo "✅ Training complete!"
echo "📁 Results: runs/train/synthetic_training/"
echo "🏆 Best model: runs/train/synthetic_training/weights/best.pt"

# =============================
# Phase 4: Evaluate Model
# =============================

echo ""
echo "📊 Phase 4: Evaluating Model..."
echo "----------------------------------------"

python3 scripts/evaluate_yolo.py \
    --model runs/train/synthetic_training/weights/best.pt \
    --data ${TRAINING_DATA} \
    --split test \
    --device ${DEVICE}

echo ""
echo "========================================================================"
echo "✅ Pipeline Complete!"
echo "========================================================================"
echo ""
echo "📌 Next Steps:"
echo "   1. Check results: runs/train/synthetic_training/"
echo "   2. Test inference: python scripts/inference_yolo.py"
echo "   3. Deploy model: cp runs/train/synthetic_training/weights/best.pt yolo-api/models/"
echo ""
