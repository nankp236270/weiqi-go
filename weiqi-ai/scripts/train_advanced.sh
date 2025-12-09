#!/bin/bash
# 高級訓練腳本（24+ 小時）

set -e

echo "========================================="
echo "圍棋 AI 高級訓練"
echo "預計時間: 24+ 小時 (GPU 推薦)"
echo "========================================="
echo ""

# 檢查是否在正確的目錄
if [ ! -f "training/train.py" ]; then
    echo "錯誤: 請在 weiqi-ai 目錄下運行此腳本"
    exit 1
fi

# 檢測 GPU
if ! python3 -c "import torch; exit(0 if torch.cuda.is_available() else 1)" 2>/dev/null; then
    echo "警告: 未檢測到 GPU！"
    echo "高級訓練強烈建議使用 GPU，否則可能需要數天時間。"
    read -p "是否繼續？(y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    DEVICE="cpu"
else
    DEVICE="cuda"
    echo "✓ 檢測到 GPU"
fi
echo ""

# 創建保存目錄
SAVE_DIR="models/advanced_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$SAVE_DIR"
mkdir -p logs

LOG_FILE="logs/training_advanced_$(date +%Y%m%d_%H%M%S).log"

echo "保存目錄: $SAVE_DIR"
echo "日誌文件: $LOG_FILE"
echo ""
echo "訓練配置:"
echo "  - 迭代次數: 100"
echo "  - 自我對弈: 100 局/迭代"
echo "  - MCTS 模擬: 800 次"
echo "  - 設備: $DEVICE"
echo ""

read -p "按 Enter 開始訓練..."

# 開始訓練
python3 training/train.py \
    --iterations 100 \
    --self-play-games 100 \
    --eval-games 20 \
    --simulations 800 \
    --epochs 15 \
    --batch-size 128 \
    --learning-rate 0.0005 \
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
echo "部署模型:"
echo "  export AI_MODE=neural_mcts"
echo "  export MODEL_PATH=$(pwd)/$SAVE_DIR/best_model_iter100.pth"
echo "  export NUM_SIMULATIONS=1600"
echo "  uvicorn api.main:app --host 0.0.0.0 --port 8000"
echo ""

