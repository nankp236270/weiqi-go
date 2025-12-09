#!/bin/bash
# 持續訓練腳本 - 自動迭代升級模型
# 
# 這個腳本會：
# 1. 不斷進行訓練迭代
# 2. 自動評估新模型
# 3. 保留最佳模型
# 4. 使用最佳模型繼續訓練

set -e

# ============================================================
# 配置參數
# ============================================================

# 訓練階段配置
STAGE_ITERATIONS=10          # 每個階段的迭代次數
SELF_PLAY_GAMES=30          # 每次迭代的自我對弈遊戲數
EVAL_GAMES=10               # 評估遊戲數
SIMULATIONS=100             # MCTS 模擬次數（平衡速度和質量）
EPOCHS=5                    # 訓練輪數
BATCH_SIZE=64               # 批次大小
LEARNING_RATE=0.001         # 學習率

# 持續訓練配置
MAX_STAGES=100              # 最大訓練階段數（設置為 0 表示無限訓練）
EVAL_THRESHOLD=0.55         # 新模型勝率閾值（超過此值才升級）
CHECKPOINT_INTERVAL=5       # 每 N 個階段保存一次檢查點

# 目錄配置
BASE_DIR="models/continuous_$(date +%Y%m%d_%H%M%S)"
BEST_MODEL_DIR="$BASE_DIR/best_models"
CHECKPOINT_DIR="$BASE_DIR/checkpoints"
LOG_DIR="$BASE_DIR/logs"

# ============================================================
# 初始化
# ============================================================

echo "============================================================"
echo "圍棋 AI 持續訓練系統"
echo "============================================================"
echo ""
echo "訓練配置:"
echo "  - 每階段迭代數: $STAGE_ITERATIONS"
echo "  - 自我對弈遊戲數: $SELF_PLAY_GAMES"
echo "  - MCTS 模擬次數: $SIMULATIONS"
echo "  - 最大訓練階段: $MAX_STAGES (0=無限)"
echo "  - 升級閾值: $EVAL_THRESHOLD"
echo ""
echo "保存目錄: $BASE_DIR"
echo "============================================================"
echo ""

# 檢查是否在正確的目錄
if [ ! -f "training/train.py" ]; then
    echo "錯誤: 請在 weiqi-ai 目錄下運行此腳本"
    exit 1
fi

# 創建目錄
mkdir -p "$BEST_MODEL_DIR"
mkdir -p "$CHECKPOINT_DIR"
mkdir -p "$LOG_DIR"

# 初始化變量
CURRENT_STAGE=1
CURRENT_MODEL=""
TOTAL_ITERATIONS=0
BEST_WINRATE=0.0

# 創建訓練記錄文件
TRAINING_LOG="$BASE_DIR/training_history.txt"
echo "# 持續訓練記錄" > "$TRAINING_LOG"
echo "# 開始時間: $(date)" >> "$TRAINING_LOG"
echo "# 配置: iterations=$STAGE_ITERATIONS, games=$SELF_PLAY_GAMES, simulations=$SIMULATIONS" >> "$TRAINING_LOG"
echo "" >> "$TRAINING_LOG"

# ============================================================
# 訓練循環
# ============================================================

while true; do
    echo ""
    echo "============================================================"
    echo "訓練階段 $CURRENT_STAGE"
    echo "總迭代數: $TOTAL_ITERATIONS"
    if [ -n "$CURRENT_MODEL" ]; then
        echo "當前最佳模型: $CURRENT_MODEL"
        echo "當前最佳勝率: $BEST_WINRATE"
    fi
    echo "============================================================"
    echo ""
    
    # 設置當前階段的保存目錄
    STAGE_DIR="$BASE_DIR/stage_$(printf "%03d" $CURRENT_STAGE)"
    mkdir -p "$STAGE_DIR"
    
    # 準備訓練命令
    TRAIN_CMD="python3 training/train.py \
        --iterations $STAGE_ITERATIONS \
        --self-play-games $SELF_PLAY_GAMES \
        --eval-games $EVAL_GAMES \
        --simulations $SIMULATIONS \
        --epochs $EPOCHS \
        --batch-size $BATCH_SIZE \
        --learning-rate $LEARNING_RATE \
        --save-dir $STAGE_DIR"
    
    # 如果有當前模型，從它繼續訓練
    if [ -n "$CURRENT_MODEL" ]; then
        TRAIN_CMD="$TRAIN_CMD --resume $CURRENT_MODEL"
        echo "從現有模型繼續訓練: $CURRENT_MODEL"
    else
        echo "從隨機網絡開始訓練"
    fi
    
    # 執行訓練
    echo ""
    echo "開始訓練..."
    echo ""
    
    if $TRAIN_CMD 2>&1 | tee "$LOG_DIR/stage_$(printf "%03d" $CURRENT_STAGE).log"; then
        echo ""
        echo "✓ 階段 $CURRENT_STAGE 訓練完成"
        
        # 找到這個階段產生的最佳模型
        NEW_MODEL=$(find "$STAGE_DIR" -name "best_model_iter*.pth" | sort -V | tail -1)
        
        if [ -n "$NEW_MODEL" ]; then
            echo "新模型: $NEW_MODEL"
            
            # 如果有現有模型，進行對比評估
            if [ -n "$CURRENT_MODEL" ]; then
                echo ""
                echo "評估新模型 vs 當前最佳模型..."
                
                # 使用 compare_models.py 進行評估
                EVAL_RESULT=$(python3 scripts/compare_models.py \
                    --model1 "$NEW_MODEL" \
                    --model2 "$CURRENT_MODEL" \
                    --games $EVAL_GAMES \
                    --simulations $SIMULATIONS 2>&1 | grep "Model 1 win rate:" | awk '{print $5}')
                
                echo "新模型勝率: $EVAL_RESULT"
                
                # 檢查是否超過閾值
                if (( $(echo "$EVAL_RESULT > $EVAL_THRESHOLD" | bc -l) )); then
                    echo "✓ 新模型表現更好！升級模型"
                    
                    # 保存為最佳模型
                    BEST_MODEL_PATH="$BEST_MODEL_DIR/best_model_stage_$(printf "%03d" $CURRENT_STAGE).pth"
                    cp "$NEW_MODEL" "$BEST_MODEL_PATH"
                    CURRENT_MODEL="$BEST_MODEL_PATH"
                    BEST_WINRATE="$EVAL_RESULT"
                    
                    # 記錄到訓練日誌
                    echo "Stage $CURRENT_STAGE: 模型升級 (勝率: $EVAL_RESULT)" >> "$TRAINING_LOG"
                else
                    echo "✗ 新模型未達到升級標準，保留當前模型"
                    echo "Stage $CURRENT_STAGE: 未升級 (勝率: $EVAL_RESULT)" >> "$TRAINING_LOG"
                fi
            else
                # 第一個模型，直接設為當前模型
                BEST_MODEL_PATH="$BEST_MODEL_DIR/best_model_stage_$(printf "%03d" $CURRENT_STAGE).pth"
                cp "$NEW_MODEL" "$BEST_MODEL_PATH"
                CURRENT_MODEL="$BEST_MODEL_PATH"
                BEST_WINRATE="N/A (首個模型)"
                
                echo "✓ 設置為初始最佳模型"
                echo "Stage $CURRENT_STAGE: 初始模型" >> "$TRAINING_LOG"
            fi
        else
            echo "⚠ 警告: 未找到訓練產生的模型"
        fi
        
        # 更新計數器
        TOTAL_ITERATIONS=$((TOTAL_ITERATIONS + STAGE_ITERATIONS))
        
        # 定期保存檢查點
        if [ $((CURRENT_STAGE % CHECKPOINT_INTERVAL)) -eq 0 ]; then
            echo ""
            echo "保存檢查點..."
            CHECKPOINT_PATH="$CHECKPOINT_DIR/checkpoint_stage_$(printf "%03d" $CURRENT_STAGE).pth"
            cp "$CURRENT_MODEL" "$CHECKPOINT_PATH"
            echo "✓ 檢查點已保存: $CHECKPOINT_PATH"
        fi
        
        # 顯示統計信息
        echo ""
        echo "訓練統計:"
        echo "  - 完成階段數: $CURRENT_STAGE"
        echo "  - 總迭代數: $TOTAL_ITERATIONS"
        echo "  - 當前最佳模型: $CURRENT_MODEL"
        echo "  - 當前最佳勝率: $BEST_WINRATE"
        
    else
        echo ""
        echo "✗ 階段 $CURRENT_STAGE 訓練失敗"
        echo "Stage $CURRENT_STAGE: 訓練失敗" >> "$TRAINING_LOG"
    fi
    
    # 檢查是否達到最大階段數
    if [ $MAX_STAGES -gt 0 ] && [ $CURRENT_STAGE -ge $MAX_STAGES ]; then
        echo ""
        echo "============================================================"
        echo "已完成所有訓練階段 ($MAX_STAGES)"
        echo "============================================================"
        break
    fi
    
    # 增加階段計數
    CURRENT_STAGE=$((CURRENT_STAGE + 1))
    
    # 短暫休息（避免過熱）
    echo ""
    echo "等待 10 秒後開始下一階段..."
    sleep 10
done

# ============================================================
# 訓練完成
# ============================================================

echo ""
echo "============================================================"
echo "持續訓練完成！"
echo "============================================================"
echo ""
echo "訓練統計:"
echo "  - 完成階段數: $CURRENT_STAGE"
echo "  - 總迭代數: $TOTAL_ITERATIONS"
echo "  - 最終最佳模型: $CURRENT_MODEL"
echo ""
echo "模型保存位置:"
echo "  - 最佳模型: $BEST_MODEL_DIR/"
echo "  - 檢查點: $CHECKPOINT_DIR/"
echo "  - 訓練日誌: $LOG_DIR/"
echo ""
echo "使用最佳模型:"
echo "  export AI_MODE=neural_mcts"
echo "  export MODEL_PATH=$CURRENT_MODEL"
echo "  export NUM_SIMULATIONS=400"
echo "  python -m uvicorn api.main:app --host 0.0.0.0 --port 8001"
echo ""

