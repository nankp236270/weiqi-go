#!/bin/bash
# 停止訓練腳本
# 優雅地停止自動訓練進程

echo "正在查找訓練進程..."

# 查找 auto_train.sh 進程
PIDS=$(ps aux | grep "auto_train.sh" | grep -v grep | awk '{print $2}')

if [ -z "$PIDS" ]; then
    echo "未找到運行中的訓練進程"
    exit 0
fi

echo "找到以下訓練進程:"
ps aux | grep "auto_train.sh" | grep -v grep

echo ""
echo "正在停止訓練進程..."

for PID in $PIDS; do
    echo "停止進程 $PID"
    kill -TERM $PID
done

echo ""
echo "等待進程退出..."
sleep 3

# 檢查是否還有殘留進程
REMAINING=$(ps aux | grep "auto_train.sh" | grep -v grep | wc -l)

if [ $REMAINING -gt 0 ]; then
    echo "警告: 仍有進程未退出，強制終止..."
    for PID in $PIDS; do
        kill -KILL $PID 2>/dev/null
    done
fi

echo "✓ 訓練已停止"

# 也停止可能的 Python 訓練進程
PYTHON_PIDS=$(ps aux | grep "training/train.py" | grep -v grep | awk '{print $2}')
if [ -n "$PYTHON_PIDS" ]; then
    echo ""
    echo "發現 Python 訓練進程，正在停止..."
    for PID in $PYTHON_PIDS; do
        echo "停止進程 $PID"
        kill -TERM $PID
    done
fi

echo ""
echo "所有訓練進程已停止"

