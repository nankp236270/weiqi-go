#!/bin/bash
# 訓練監控腳本
# 實時顯示訓練進度和狀態

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODELS_DIR="$BASE_DIR/models"
LOGS_DIR="$BASE_DIR/logs"
HISTORY_FILE="$LOGS_DIR/training_history.txt"

clear

print_header() {
    echo ""
    echo "============================================================"
    echo "$1"
    echo "============================================================"
    echo ""
}

while true; do
    clear
    
    print_header "圍棋 AI 訓練監控面板"
    
    echo "更新時間: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    # 顯示當前代數
    if [ -f "$MODELS_DIR/.generation" ]; then
        CURRENT_GEN=$(cat "$MODELS_DIR/.generation")
        echo "📊 當前代數: 第 $CURRENT_GEN 代"
    else
        echo "📊 當前代數: 未開始訓練"
    fi
    
    # 顯示最佳模型
    if [ -L "$MODELS_DIR/best_model.pth" ]; then
        BEST_MODEL=$(readlink "$MODELS_DIR/best_model.pth")
        echo "🏆 最佳模型: $BEST_MODEL"
        
        # 顯示模型文件大小
        if [ -f "$BEST_MODEL" ]; then
            MODEL_SIZE=$(du -h "$BEST_MODEL" | cut -f1)
            echo "📦 模型大小: $MODEL_SIZE"
        fi
    else
        echo "🏆 最佳模型: 無"
    fi
    
    echo ""
    
    # 顯示進化歷史
    if [ -f "$MODELS_DIR/evolution_history.txt" ]; then
        print_header "進化歷史（最近 10 代）"
        tail -10 "$MODELS_DIR/evolution_history.txt"
    fi
    
    # 顯示訓練日誌（最近 20 行）
    if [ -f "$HISTORY_FILE" ]; then
        print_header "訓練日誌（最近 20 行）"
        tail -20 "$HISTORY_FILE"
    fi
    
    # 顯示磁盤使用情況
    echo ""
    echo "💾 模型目錄大小: $(du -sh $MODELS_DIR | cut -f1)"
    
    # 顯示模型數量
    TOTAL_MODELS=$(find "$MODELS_DIR" -name "*.pth" | wc -l)
    FAILED_DIRS=$(find "$MODELS_DIR" -name "*_failed" -type d | wc -l)
    echo "📁 模型總數: $TOTAL_MODELS"
    echo "❌ 失敗嘗試: $FAILED_DIRS"
    
    echo ""
    echo "按 Ctrl+C 退出監控"
    echo ""
    
    # 每 10 秒更新一次
    sleep 10
done
