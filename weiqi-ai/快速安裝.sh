#!/bin/bash
# 快速安裝腳本

set -e

echo "========================================="
echo "圍棋 AI 快速安裝"
echo "========================================="
echo ""

# 檢查 Python 版本
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python 版本: $PYTHON_VERSION"
echo ""

# 檢查是否在虛擬環境中
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✓ 已在虛擬環境中: $VIRTUAL_ENV"
    echo ""
else
    echo "創建虛擬環境..."
    
    # 檢查是否已存在 venv
    if [ -d "venv" ]; then
        echo "✓ 虛擬環境已存在"
    else
        python3 -m venv venv
        echo "✓ 虛擬環境已創建"
    fi
    
    echo ""
    echo "激活虛擬環境..."
    source venv/bin/activate
    echo "✓ 虛擬環境已激活"
    echo ""
fi

# 升級 pip
echo "升級 pip..."
pip install --upgrade pip
echo ""

# 安裝依賴
echo "安裝依賴..."
pip install -r requirements.txt
echo ""

# 測試安裝
echo "========================================="
echo "測試安裝"
echo "========================================="
echo ""

# 運行快速測試（不運行 MCTS，避免卡住）
python test_quick.py

echo ""
echo "注意: 這是快速測試，只驗證模塊導入。"
echo "如果要運行完整測試（包括 MCTS），請運行: python test_ai.py"

echo ""
echo "========================================="
echo "安裝完成！"
echo "========================================="
echo ""
echo "下一步:"
echo "  1. 啟動 AI 服務:"
echo "     source venv/bin/activate  # 如果還沒激活"
echo "     export AI_MODE=pure_mcts"
echo "     export NUM_SIMULATIONS=400"
echo "     python -m uvicorn api.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "  2. 人機對弈:"
echo "     python examples/simple_game.py"
echo ""
echo "  3. 訓練 AI:"
echo "     ./scripts/train_quick.sh"
echo ""

