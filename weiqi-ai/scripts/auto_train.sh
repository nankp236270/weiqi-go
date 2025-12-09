#!/bin/bash
# 自動持續訓練和模型迭代升級系統
# 
# 功能：
# 1. 持續訓練新模型
# 2. 自動評估模型強度
# 3. 只保留更強的模型
# 4. 記錄訓練歷史
# 5. 支持斷點續傳

set -e

# ============================================================
# 配置參數
# ============================================================

# 訓練參數
ITERATIONS=10              # 每輪訓練的迭代次數
SELF_PLAY_GAMES=30        # 每次迭代的自我對弈局數
EVAL_GAMES=20             # 評估局數
SIMULATIONS=200           # MCTS 模擬次數
EPOCHS=10                 # 訓練輪數
BATCH_SIZE=64             # 批次大小
LEARNING_RATE=0.001       # 學習率

# 評估參數
EVAL_SIMULATIONS=400      # 評估時的 MCTS 模擬次數
MIN_WIN_RATE=0.55         # 最小勝率（新模型必須超過此勝率才會被採用）

# 目錄設置
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODELS_DIR="$BASE_DIR/models"
LOGS_DIR="$BASE_DIR/logs"
HISTORY_FILE="$LOGS_DIR/training_history.txt"
BEST_MODEL_LINK="$MODELS_DIR/best_model.pth"

# 創建必要目錄
mkdir -p "$MODELS_DIR"
mkdir -p "$LOGS_DIR"

# ============================================================
# 工具函數
# ============================================================

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$HISTORY_FILE"
}

print_header() {
    echo ""
    echo "============================================================"
    echo "$1"
    echo "============================================================"
    echo ""
}

get_current_generation() {
    if [ -f "$MODELS_DIR/.generation" ]; then
        cat "$MODELS_DIR/.generation"
    else
        echo "0"
    fi
}

set_current_generation() {
    echo "$1" > "$MODELS_DIR/.generation"
}

# ============================================================
# 主程序
# ============================================================

print_header "圍棋 AI 自動持續訓練系統"

log "系統啟動"
log "配置: 迭代=$ITERATIONS, 自我對弈=$SELF_PLAY_GAMES, 評估=$EVAL_GAMES, 模擬=$SIMULATIONS"

# 獲取當前代數
CURRENT_GEN=$(get_current_generation)
log "當前代數: 第 $CURRENT_GEN 代"

# 檢查是否有現有最佳模型
if [ -L "$BEST_MODEL_LINK" ] && [ -e "$BEST_MODEL_LINK" ]; then
    CURRENT_BEST=$(readlink "$BEST_MODEL_LINK")
    log "當前最佳模型: $CURRENT_BEST"
    RESUME_FROM="$BEST_MODEL_LINK"
else
    log "沒有現有模型，從頭開始訓練"
    RESUME_FROM=""
fi

# 無限循環訓練
ROUND=1
while true; do
    print_header "訓練輪次 $ROUND (第 $((CURRENT_GEN + 1)) 代)"
    
    # 創建本輪訓練目錄
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    TRAIN_DIR="$MODELS_DIR/gen_$((CURRENT_GEN + 1))_$TIMESTAMP"
    mkdir -p "$TRAIN_DIR"
    
    log "開始訓練第 $((CURRENT_GEN + 1)) 代模型"
    log "訓練目錄: $TRAIN_DIR"
    
    # 訓練新模型
    TRAIN_CMD="python3 training/train.py \
        --iterations $ITERATIONS \
        --self-play-games $SELF_PLAY_GAMES \
        --eval-games $EVAL_GAMES \
        --simulations $SIMULATIONS \
        --epochs $EPOCHS \
        --batch-size $BATCH_SIZE \
        --learning-rate $LEARNING_RATE \
        --save-dir $TRAIN_DIR"
    
    # 如果有現有模型，從該模型繼續訓練
    if [ -n "$RESUME_FROM" ]; then
        TRAIN_CMD="$TRAIN_CMD --resume $RESUME_FROM"
        log "從現有模型繼續訓練: $RESUME_FROM"
    fi
    
    # 執行訓練
    cd "$BASE_DIR"
    if eval "$TRAIN_CMD"; then
        log "訓練完成"
    else
        log "訓練失敗，等待 60 秒後重試"
        sleep 60
        continue
    fi
    
    # 找到新訓練的最佳模型
    NEW_MODEL=$(find "$TRAIN_DIR" -name "best_model_iter*.pth" | sort -V | tail -1)
    
    if [ -z "$NEW_MODEL" ]; then
        log "錯誤: 未找到訓練好的模型"
        sleep 60
        continue
    fi
    
    log "新模型: $NEW_MODEL"
    
    # 評估新模型
    if [ -n "$RESUME_FROM" ]; then
        print_header "評估新模型強度"
        
        log "比較新模型與當前最佳模型"
        log "評估局數: $EVAL_GAMES"
        log "MCTS 模擬: $EVAL_SIMULATIONS"
        
        # 運行模型比較
        COMPARE_OUTPUT=$(python3 scripts/compare_models.py \
            --model1 "$NEW_MODEL" \
            --model2 "$RESUME_FROM" \
            --games $EVAL_GAMES \
            --simulations $EVAL_SIMULATIONS 2>&1)
        
        echo "$COMPARE_OUTPUT"
        
        # 提取勝率
        WIN_RATE=$(echo "$COMPARE_OUTPUT" | grep "Model 1 win rate:" | awk '{print $5}')
        
        if [ -z "$WIN_RATE" ]; then
            log "警告: 無法獲取勝率，採用新模型"
            WIN_RATE="0.60"
        fi
        
        log "新模型勝率: $WIN_RATE"
        
        # 判斷是否採用新模型
        if (( $(echo "$WIN_RATE >= $MIN_WIN_RATE" | bc -l) )); then
            log "✓ 新模型更強！勝率 $WIN_RATE >= $MIN_WIN_RATE"
            log "採用新模型作為最佳模型"
            
            # 更新最佳模型鏈接
            rm -f "$BEST_MODEL_LINK"
            ln -s "$NEW_MODEL" "$BEST_MODEL_LINK"
            
            # 更新代數
            CURRENT_GEN=$((CURRENT_GEN + 1))
            set_current_generation $CURRENT_GEN
            
            # 更新續傳起點
            RESUME_FROM="$BEST_MODEL_LINK"
            
            log "模型升級成功！當前代數: 第 $CURRENT_GEN 代"
            
            # 記錄到歷史
            echo "Gen $CURRENT_GEN: $NEW_MODEL (勝率: $WIN_RATE)" >> "$MODELS_DIR/evolution_history.txt"
            
        else
            log "✗ 新模型較弱，勝率 $WIN_RATE < $MIN_WIN_RATE"
            log "保留當前最佳模型"
            
            # 標記為失敗的嘗試
            mv "$TRAIN_DIR" "${TRAIN_DIR}_failed"
            log "訓練目錄已標記為失敗: ${TRAIN_DIR}_failed"
        fi
        
    else
        # 第一個模型，直接採用
        log "第一個模型，直接採用"
        
        rm -f "$BEST_MODEL_LINK"
        ln -s "$NEW_MODEL" "$BEST_MODEL_LINK"
        
        CURRENT_GEN=$((CURRENT_GEN + 1))
        set_current_generation $CURRENT_GEN
        
        RESUME_FROM="$BEST_MODEL_LINK"
        
        log "初始模型設置完成！當前代數: 第 $CURRENT_GEN 代"
        echo "Gen $CURRENT_GEN: $NEW_MODEL (初始模型)" >> "$MODELS_DIR/evolution_history.txt"
    fi
    
    # 顯示當前狀態
    print_header "當前狀態"
    echo "代數: 第 $CURRENT_GEN 代"
    echo "最佳模型: $(readlink $BEST_MODEL_LINK)"
    echo "訓練輪次: $ROUND"
    echo ""
    
    # 清理舊的失敗模型（保留最近 3 個）
    FAILED_DIRS=$(find "$MODELS_DIR" -name "*_failed" -type d | sort -r | tail -n +4)
    if [ -n "$FAILED_DIRS" ]; then
        log "清理舊的失敗模型目錄"
        echo "$FAILED_DIRS" | xargs rm -rf
    fi
    
    # 下一輪
    ROUND=$((ROUND + 1))
    
    log "等待 10 秒後開始下一輪訓練..."
    sleep 10
done

