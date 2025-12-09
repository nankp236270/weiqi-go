# 訓練和工具腳本

這個目錄包含了用於訓練和管理 AI 模型的實用腳本。

## 訓練腳本

### 1. train_quick.sh - 快速訓練（30 分鐘）

快速體驗訓練流程，適合測試和學習。

```bash
cd weiqi-ai
chmod +x scripts/train_quick.sh
./scripts/train_quick.sh
```

**配置:**
- 迭代次數: 5
- 自我對弈: 20 局/迭代
- MCTS 模擬: 200 次
- 預計時間: ~30 分鐘

### 2. train_standard.sh - 標準訓練（4 小時）

獲得一個可用的 AI 模型。

```bash
cd weiqi-ai
chmod +x scripts/train_standard.sh
./scripts/train_standard.sh
```

**配置:**
- 迭代次數: 20
- 自我對弈: 50 局/迭代
- MCTS 模擬: 400 次
- 預計時間: ~4 小時（CPU）或 ~1 小時（GPU）

### 3. train_advanced.sh - 高級訓練（24+ 小時）

獲得高水平的 AI 模型。

```bash
cd weiqi-ai
chmod +x scripts/train_advanced.sh
./scripts/train_advanced.sh
```

**配置:**
- 迭代次數: 100
- 自我對弈: 100 局/迭代
- MCTS 模擬: 800 次
- 預計時間: ~24 小時（GPU 推薦）

## 工具腳本

### compare_models.py - 模型比較工具

比較兩個模型的強度，或比較模型與純 MCTS。

**用法:**

```bash
cd weiqi-ai

# 比較訓練好的模型與純 MCTS
python scripts/compare_models.py \
    --model1 models/best_model_iter20.pth \
    --games 20

# 比較兩個訓練好的模型
python scripts/compare_models.py \
    --model1 models/best_model_iter20.pth \
    --model2 models/best_model_iter50.pth \
    --games 30 \
    --simulations 400
```

**參數:**
- `--model1`: 模型 1 的路徑（不指定則使用純 MCTS）
- `--model2`: 模型 2 的路徑（不指定則使用純 MCTS）
- `--games`: 對弈局數（默認：20）
- `--simulations`: MCTS 模擬次數（默認：400）

**輸出示例:**
```
================================================================
比較結果
================================================================

玩家 1 勝: 14/20 (70.0%)
玩家 2 勝: 6/20 (30.0%)
平局: 0/20 (0.0%)

🏆 玩家 1 更強！
   優勢: 40.0%
```

## 使用流程

### 1. 第一次訓練

```bash
# 快速體驗
./scripts/train_quick.sh

# 等待訓練完成後，測試模型
export AI_MODE=neural_mcts
export MODEL_PATH=$(pwd)/models/quick_*/best_model_iter5.pth
export NUM_SIMULATIONS=400
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### 2. 比較模型強度

```bash
# 比較訓練好的模型與純 MCTS
python scripts/compare_models.py \
    --model1 models/quick_*/best_model_iter5.pth \
    --games 10
```

### 3. 繼續訓練

如果對結果滿意，可以進行更長時間的訓練：

```bash
# 標準訓練
./scripts/train_standard.sh

# 或從之前的模型繼續
python training/train.py \
    --resume models/quick_*/best_model_iter5.pth \
    --iterations 20 \
    --save-dir models/continued
```

### 4. 部署最佳模型

```bash
# 找出最強的模型
python scripts/compare_models.py \
    --model1 models/standard_*/best_model_iter20.pth \
    --model2 models/advanced_*/best_model_iter100.pth

# 部署最強模型
export AI_MODE=neural_mcts
export MODEL_PATH=$(pwd)/models/advanced_*/best_model_iter100.pth
export NUM_SIMULATIONS=800
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## 訓練技巧

### 1. 分階段訓練

```bash
# 階段 1: 快速訓練
./scripts/train_quick.sh

# 階段 2: 從快速訓練的結果繼續
python training/train.py \
    --resume models/quick_*/best_model_iter5.pth \
    --iterations 15 \
    --save-dir models/stage2

# 階段 3: 高質量訓練
python training/train.py \
    --resume models/stage2/best_model_iter15.pth \
    --iterations 30 \
    --simulations 800 \
    --save-dir models/stage3
```

### 2. 後台訓練

```bash
# 使用 nohup 在後台訓練
nohup ./scripts/train_standard.sh > training.log 2>&1 &

# 查看訓練進度
tail -f training.log

# 或使用 screen/tmux
screen -S training
./scripts/train_standard.sh
# Ctrl+A, D 分離會話
```

### 3. 定期備份

```bash
# 創建備份腳本
cat > scripts/backup_models.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="backups/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"
cp -r models/* "$BACKUP_DIR/"
echo "已備份到 $BACKUP_DIR"
EOF

chmod +x scripts/backup_models.sh

# 定期運行
./scripts/backup_models.sh
```

## 故障排除

### 腳本無法執行

```bash
# 添加執行權限
chmod +x scripts/*.sh
```

### 訓練中斷

所有訓練腳本都會保存檢查點，可以從中斷處繼續：

```bash
# 查找最後的檢查點
ls -lt models/*/best_model_*.pth | head -1

# 繼續訓練
python training/train.py \
    --resume models/.../best_model_iter15.pth \
    --iterations 50
```

### 內存不足

修改訓練腳本，減少批次大小和模擬次數：

```bash
# 編輯腳本，將
#   --batch-size 64
# 改為
#   --batch-size 32

# 將
#   --simulations 400
# 改為
#   --simulations 200
```

## 相關文檔

- [訓練完整指南](../../docs/AI_TRAINING_GUIDE.md)
- [AI 快速入門](../../docs/AI_QUICKSTART.md)
- [AI 實現文檔](../../docs/AI_IMPLEMENTATION.md)

## 貢獻

歡迎提交更多實用腳本！

