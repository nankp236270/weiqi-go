#!/bin/bash
# 一鍵啟動自動訓練系統

set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

echo "============================================================"
echo "圍棋 AI 自動訓練系統 - 一鍵啟動"
echo "============================================================"
echo ""

# 檢查虛擬環境
if [ ! -d "venv" ]; then
    echo "錯誤: 未找到虛擬環境"
    echo "請先運行: ./快速安裝.sh"
    exit 1
fi

# 激活虛擬環境
echo "激活虛擬環境..."
source venv/bin/activate

# 創建必要目錄
mkdir -p logs
mkdir -p models

# 檢查是否已有訓練在運行
if [ -f "logs/auto_train.pid" ]; then
    OLD_PID=$(cat logs/auto_train.pid)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "警告: 檢測到已有訓練進程在運行 (PID: $OLD_PID)"
        echo ""
        read -p "是否停止舊進程並啟動新的？(y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "停止舊進程..."
            ./scripts/stop_training.sh
            sleep 3
        else
            echo "取消啟動"
            exit 0
        fi
    fi
fi

echo ""
echo "配置檢查..."
echo "✓ Python 版本: $(python --version)"
echo "✓ 工作目錄: $BASE_DIR"
echo "✓ 虛擬環境: 已激活"
echo ""

# 顯示訓練配置
echo "訓練配置:"
echo "  - 每輪迭代: 10 次"
echo "  - 自我對弈: 30 局/迭代"
echo "  - 評估局數: 20 局"
echo "  - MCTS 模擬: 200 次"
echo "  - 最小勝率: 55%"
echo ""
echo "預計每輪訓練時間: 1-2 小時"
echo "系統將持續運行，不斷訓練和升級模型"
echo ""

read -p "是否開始自動訓練？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "取消啟動"
    exit 0
fi

echo ""
echo "啟動自動訓練..."

# 啟動訓練（後台運行）
nohup ./scripts/auto_train.sh > logs/auto_train.log 2>&1 &
TRAIN_PID=$!

# 保存 PID
echo $TRAIN_PID > logs/auto_train.pid

echo "✓ 訓練已啟動 (PID: $TRAIN_PID)"
echo ""

# 等待幾秒確認啟動成功
sleep 3

if ps -p $TRAIN_PID > /dev/null; then
    echo "============================================================"
    echo "✓ 自動訓練系統已成功啟動！"
    echo "============================================================"
    echo ""
    echo "監控命令:"
    echo "  1. 實時監控面板:"
    echo "     ./scripts/monitor_training.sh"
    echo ""
    echo "  2. 查看訓練日誌:"
    echo "     tail -f logs/training_history.txt"
    echo ""
    echo "  3. 查看進化歷史:"
    echo "     python scripts/view_evolution.py"
    echo ""
    echo "  4. 查看完整日誌:"
    echo "     tail -f logs/auto_train.log"
    echo ""
    echo "停止訓練:"
    echo "  ./scripts/stop_training.sh"
    echo ""
    echo "提示: 訓練將在後台持續運行，即使關閉終端也不會停止"
    echo "      建議在 screen 或 tmux 中運行監控面板"
    echo ""
else
    echo "錯誤: 訓練啟動失敗"
    echo "請查看日誌: cat logs/auto_train.log"
    exit 1
fi

