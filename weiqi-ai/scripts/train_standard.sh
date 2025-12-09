#!/bin/bash
# 標準訓練腳本（4 小時）

set -e

echo "========================================="
echo "圍棋 AI 標準訓練"
echo "預計時間: 4 小時 (CPU) / 1 小時 (GPU)"
echo "========================================="
echo ""

# 檢查是否在正確的目錄
if [ ! -f "training/train.py" ]; then
    echo "錯誤: 請在 weiqi-ai 目錄下運行此腳本"
    exit 1
fi

# 檢測 GPU
DEVICE="cpu"
if python3 -c "import torch; exit(0 if torch.cuda.is_available() else 1)" 2>/dev/null; then
    DEVICE="cuda"
    echo "✓ 檢測到 GPU，將使用 CUDA 加速"
else
    echo "! 未檢測到 GPU，將使用 CPU 訓練（較慢）"
fi
echo ""

# 創建保存目錄
SAVE_DIR="models/standard_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$SAVE_DIR"
mkdir -p logs

LOG_FILE="logs/training_$(date +%Y%m%d_%H%M%S).log"

echo "保存目錄: $SAVE_DIR"
echo "日誌文件: $LOG_FILE"
echo ""

# 開始訓練
python3 training/train.py \
    --iterations 20 \
    --self-play-games 50 \
    --eval-games 10 \
    --simulations 400 \
    --epochs 10 \
    --batch-size 64 \
    --learning-rate 0.001 \
    --device "$DEVICE" \
    --save-dir "$SAVE_DIR" \
    2>&1 | tee "$LOG_FILE"

echo ""
echo "========================================="
echo "訓練完成！"
echo "========================================="
echo ""
echo "模型保存在: $SAVE_DIR"
echo "訓練日誌: $LOG_FILE"
echo ""
echo "測試模型:"
echo "  export AI_MODE=neural_mcts"
echo "  export MODEL_PATH=$(pwd)/$SAVE_DIR/best_model_iter20.pth"
echo "  export NUM_SIMULATIONS=800"
echo "  uvicorn api.main:app --host 0.0.0.0 --port 8000"
echo ""

