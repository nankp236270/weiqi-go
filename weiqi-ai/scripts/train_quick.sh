#!/bin/bash
# 快速訓練腳本（30 分鐘體驗）

set -e

echo "========================================="
echo "圍棋 AI 快速訓練"
echo "預計時間: 30 分鐘"
echo "========================================="
echo ""

# 檢查是否在正確的目錄
if [ ! -f "training/train.py" ]; then
    echo "錯誤: 請在 weiqi-ai 目錄下運行此腳本"
    exit 1
fi

# 創建保存目錄
SAVE_DIR="models/quick_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$SAVE_DIR"

echo "保存目錄: $SAVE_DIR"
echo ""

# 開始訓練
python3 training/train.py \
    --iterations 5 \
    --self-play-games 20 \
    --eval-games 5 \
    --simulations 200 \
    --epochs 5 \
    --batch-size 32 \
    --learning-rate 0.001 \
    --save-dir "$SAVE_DIR"

echo ""
echo "========================================="
echo "訓練完成！"
echo "========================================="
echo ""
echo "模型保存在: $SAVE_DIR"
echo ""
echo "測試模型:"
echo "  export AI_MODE=neural_mcts"
echo "  export MODEL_PATH=$(pwd)/$SAVE_DIR/best_model_iter5.pth"
echo "  export NUM_SIMULATIONS=400"
echo "  uvicorn api.main:app --host 0.0.0.0 --port 8000"
echo ""

