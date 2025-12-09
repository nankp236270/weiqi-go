# 圍棋 AI 訓練完整指南

## 目錄

1. [訓練前準備](#訓練前準備)
2. [快速開始訓練](#快速開始訓練)
3. [訓練參數詳解](#訓練參數詳解)
4. [訓練過程監控](#訓練過程監控)
5. [模型保存和使用](#模型保存和使用)
6. [進階訓練技巧](#進階訓練技巧)
7. [常見問題](#常見問題)

## 訓練前準備

### 1. 環境要求

#### 最低配置（CPU 訓練）
- CPU: 4 核心以上
- 內存: 8GB+
- 硬盤: 10GB 可用空間
- 時間: 準備等待較長時間

#### 推薦配置（GPU 訓練）
- CPU: 8 核心以上
- 內存: 16GB+
- GPU: NVIDIA GPU（8GB+ 顯存）
- 硬盤: 20GB 可用空間
- CUDA: 11.0+

### 2. 安裝依賴

```bash
cd weiqi-ai

# 基礎依賴
pip install -r requirements.txt

# 如果有 NVIDIA GPU，安裝 CUDA 版本的 PyTorch
pip install torch==2.1.0+cu118 torchvision==0.16.0+cu118 --index-url https://download.pytorch.org/whl/cu118
```

### 3. 驗證環境

```bash
# 測試 AI 系統
python test_ai.py

# 檢查 GPU 是否可用（如果有）
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

## 快速開始訓練

### 方案 1: 快速體驗（30 分鐘）

適合快速測試和學習訓練流程。

```bash
cd weiqi-ai

python training/train.py \
    --iterations 5 \
    --self-play-games 20 \
    --eval-games 5 \
    --simulations 200 \
    --epochs 5 \
    --batch-size 32 \
    --save-dir models/quick
```

**預期結果:**
- 訓練時間: ~30 分鐘（CPU）
- 模型強度: 比純 MCTS 強 20-30%
- 適用場景: 測試和學習

### 方案 2: 標準訓練（4 小時）

適合獲得一個可用的 AI 模型。

```bash
python training/train.py \
    --iterations 20 \
    --self-play-games 50 \
    --eval-games 10 \
    --simulations 400 \
    --epochs 10 \
    --batch-size 64 \
    --save-dir models/standard
```

**預期結果:**
- 訓練時間: ~4 小時（CPU）或 ~1 小時（GPU）
- 模型強度: 比純 MCTS 強 50-100%
- 適用場景: 實際使用

### 方案 3: 高級訓練（24+ 小時）

適合獲得高水平的 AI。

```bash
python training/train.py \
    --iterations 100 \
    --self-play-games 100 \
    --eval-games 20 \
    --simulations 800 \
    --epochs 15 \
    --batch-size 128 \
    --learning-rate 0.0005 \
    --device cuda \
    --save-dir models/advanced
```

**預期結果:**
- 訓練時間: ~24 小時（GPU）
- 模型強度: 業餘初段-中段水平
- 適用場景: 高水平對弈

## 訓練參數詳解

### 核心參數

#### `--iterations` (迭代次數)
- **說明**: 訓練循環的次數
- **推薦值**: 
  - 快速測試: 5-10
  - 標準訓練: 20-50
  - 高級訓練: 100+
- **影響**: 越多越強，但時間也越長

#### `--self-play-games` (自我對弈遊戲數)
- **說明**: 每次迭代生成的訓練數據量
- **推薦值**:
  - 快速測試: 20-30
  - 標準訓練: 50-100
  - 高級訓練: 100-200
- **影響**: 越多數據質量越好，但時間越長

#### `--eval-games` (評估遊戲數)
- **說明**: 評估新模型 vs 舊模型的對弈數
- **推薦值**: 10-20
- **影響**: 越多評估越準確，但時間越長

#### `--simulations` (MCTS 模擬次數)
- **說明**: 每步棋的 MCTS 搜索深度
- **推薦值**:
  - 快速測試: 200-400
  - 標準訓練: 400-800
  - 高級訓練: 800-1600
- **影響**: 越多生成的數據質量越高，但時間越長

### 神經網絡參數

#### `--learning-rate` (學習率)
- **說明**: 神經網絡的學習速度
- **推薦值**: 0.0001 - 0.001
- **默認值**: 0.001
- **調整建議**:
  - 訓練不穩定: 降低到 0.0005 或 0.0001
  - 訓練太慢: 提高到 0.002
  - 後期訓練: 逐漸降低

#### `--batch-size` (批次大小)
- **說明**: 每次訓練使用的樣本數
- **推薦值**:
  - CPU: 32-64
  - GPU (8GB): 64-128
  - GPU (16GB+): 128-256
- **影響**: 越大訓練越穩定，但需要更多內存

#### `--epochs` (訓練輪數)
- **說明**: 每次迭代訓練神經網絡的輪數
- **推薦值**: 10-15
- **影響**: 越多模型擬合越好，但可能過擬合

### 其他參數

#### `--device` (訓練設備)
- **選項**: `cpu` 或 `cuda`
- **說明**: 使用 CPU 還是 GPU 訓練
- **推薦**: 有 GPU 就用 `cuda`

#### `--save-dir` (保存目錄)
- **說明**: 模型和訓練數據的保存位置
- **默認值**: `models`
- **建議**: 為不同的訓練實驗使用不同的目錄

#### `--resume` (恢復訓練)
- **說明**: 從之前的檢查點繼續訓練
- **用法**: `--resume models/best_model_iter20.pth`

## 訓練過程監控

### 訓練輸出解讀

```
================================================================
Iteration 5
================================================================

Step 1: Self-play data generation
Generating game 1/50...
  Moves: 156, Winner: 1, Examples: 156
Generating game 2/50...
  Moves: 142, Winner: 2, Examples: 142
...
Generated 7500 training examples from 50 games

Step 2: Training new model
Augmenting data: 7500 -> 60000 examples
Epoch 1/10: Total Loss = 2.3456, Policy Loss = 1.8234, Value Loss = 0.5222
Epoch 2/10: Total Loss = 2.1234, Policy Loss = 1.6543, Value Loss = 0.4691
...

Step 3: Evaluating new model vs best model
  Game 1/10 finished
  Game 2/10 finished
  ...

Evaluation results:
  New model wins: 6
  Best model wins: 4
  Draws: 0
  New model win rate: 60.00%

✓ New model is better! Updating best model.
Saved checkpoint to models/best_model_iter5.pth
```

### 關鍵指標

#### 1. 損失值 (Loss)
- **Total Loss**: 總損失，越低越好
- **Policy Loss**: 策略損失，越低越好
- **Value Loss**: 價值損失，越低越好

**正常趨勢**: 隨著訓練進行，損失應該逐漸下降

#### 2. 勝率 (Win Rate)
- **說明**: 新模型對舊模型的勝率
- **閾值**: 默認 55%（可調整）
- **意義**: 超過閾值則更新最佳模型

#### 3. 遊戲步數 (Moves)
- **說明**: 每局遊戲的步數
- **正常範圍**: 100-250 步
- **異常**: 
  - 太少 (<50): 可能有 bug
  - 太多 (>300): AI 可能陷入僵局

## 模型保存和使用

### 模型文件結構

```
models/
├── best_model_iter5.pth      # 第 5 次迭代的最佳模型
├── best_model_iter10.pth     # 第 10 次迭代的最佳模型
├── best_model_iter20.pth     # 第 20 次迭代的最佳模型
└── training_data/            # 訓練數據
    ├── training_data_20250101_120000_games50.pkl
    └── training_data_20250101_130000_games100.pkl
```

### 使用訓練好的模型

#### 1. 啟動 AI 服務

```bash
export AI_MODE=neural_mcts
export MODEL_PATH=/home/zhuji/weiqi-go/weiqi-ai/models/best_model_iter20.pth
export NUM_SIMULATIONS=800
export SCORING_MODE=neural

cd weiqi-ai
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

#### 2. Docker 部署

```bash
# 構建鏡像
docker build -t weiqi-ai:trained weiqi-ai/

# 運行（掛載模型目錄）
docker run -d -p 8000:8000 \
  -e AI_MODE=neural_mcts \
  -e MODEL_PATH=/app/models/best_model_iter20.pth \
  -e NUM_SIMULATIONS=800 \
  -v $(pwd)/weiqi-ai/models:/app/models \
  weiqi-ai:trained
```

#### 3. 測試模型

```bash
# 人機對弈測試
python examples/simple_game.py

# AI 對弈測試
python examples/ai_vs_ai.py
```

### 模型版本管理

#### 保存模型元數據

創建 `models/model_info.json`:

```json
{
  "models": [
    {
      "name": "best_model_iter20.pth",
      "iteration": 20,
      "training_games": 1000,
      "win_rate": 0.65,
      "training_time_hours": 4.5,
      "date": "2025-12-04",
      "notes": "標準訓練，400 次模擬"
    },
    {
      "name": "best_model_iter50.pth",
      "iteration": 50,
      "training_games": 2500,
      "win_rate": 0.72,
      "training_time_hours": 12,
      "date": "2025-12-05",
      "notes": "高級訓練，800 次模擬"
    }
  ]
}
```

#### 比較不同模型

```python
# 創建測試腳本 compare_models.py
from ai.mcts_player import NeuralMCTSPlayer
from core.game import Game
from core.board import Player

def compare_models(model1_path, model2_path, num_games=20):
    """比較兩個模型的強度"""
    player1 = NeuralMCTSPlayer(model_path=model1_path, num_simulations=400)
    player2 = NeuralMCTSPlayer(model_path=model2_path, num_simulations=400)
    
    wins1 = 0
    wins2 = 0
    
    for i in range(num_games):
        game = Game()
        # 交替先手
        if i % 2 == 0:
            black, white = player1, player2
        else:
            black, white = player2, player1
        
        # 對弈...
        # (完整代碼見 examples/ai_vs_ai.py)
        
    print(f"Model 1 wins: {wins1}/{num_games}")
    print(f"Model 2 wins: {wins2}/{num_games}")

# 使用
compare_models(
    "models/best_model_iter20.pth",
    "models/best_model_iter50.pth",
    num_games=20
)
```

## 進階訓練技巧

### 1. 分階段訓練

```bash
# 階段 1: 快速訓練獲得基礎模型（2 小時）
python training/train.py \
    --iterations 10 \
    --self-play-games 30 \
    --simulations 200 \
    --save-dir models/stage1

# 階段 2: 從基礎模型繼續訓練（4 小時）
python training/train.py \
    --resume models/stage1/best_model_iter10.pth \
    --iterations 20 \
    --self-play-games 50 \
    --simulations 400 \
    --save-dir models/stage2

# 階段 3: 高質量訓練（12 小時）
python training/train.py \
    --resume models/stage2/best_model_iter20.pth \
    --iterations 50 \
    --self-play-games 100 \
    --simulations 800 \
    --save-dir models/stage3
```

### 2. 學習率衰減

```bash
# 初期：較高學習率
python training/train.py \
    --iterations 20 \
    --learning-rate 0.001 \
    --save-dir models/phase1

# 中期：降低學習率
python training/train.py \
    --resume models/phase1/best_model_iter20.pth \
    --iterations 30 \
    --learning-rate 0.0005 \
    --save-dir models/phase2

# 後期：更低學習率
python training/train.py \
    --resume models/phase2/best_model_iter30.pth \
    --iterations 50 \
    --learning-rate 0.0001 \
    --save-dir models/phase3
```

### 3. 數據增強策略

訓練系統已自動包含數據增強（旋轉、翻轉），將數據量擴大 8 倍。

### 4. 並行訓練（多 GPU）

如果有多個 GPU，可以修改訓練腳本使用 DataParallel:

```python
# 在 training/trainer.py 中
if torch.cuda.device_count() > 1:
    print(f"Using {torch.cuda.device_count()} GPUs")
    self.network = nn.DataParallel(self.network)
```

### 5. 訓練日誌

```bash
# 保存訓練日誌
python training/train.py \
    --iterations 50 \
    --save-dir models/experiment1 \
    2>&1 | tee logs/training_$(date +%Y%m%d_%H%M%S).log
```

## 常見問題

### Q1: 訓練中斷了怎麼辦？

**A:** 使用 `--resume` 參數從最後一個檢查點繼續：

```bash
python training/train.py \
    --resume models/best_model_iter15.pth \
    --iterations 50 \
    --save-dir models
```

### Q2: 內存不足 (Out of Memory)

**A:** 減少批次大小和模擬次數：

```bash
python training/train.py \
    --batch-size 32 \
    --simulations 200 \
    --self-play-games 30
```

### Q3: 訓練損失不下降

**可能原因:**
1. 學習率太高或太低
2. 數據質量不好
3. 模型已經收斂

**解決方案:**
```bash
# 降低學習率
python training/train.py --learning-rate 0.0001

# 增加數據量
python training/train.py --self-play-games 100

# 增加模擬次數提高數據質量
python training/train.py --simulations 800
```

### Q4: 新模型一直無法超越舊模型

**可能原因:**
1. 訓練數據不足
2. 評估遊戲數太少（運氣因素）
3. 模型已經達到瓶頸

**解決方案:**
```bash
# 增加訓練數據
python training/train.py --self-play-games 100

# 增加評估遊戲數
python training/train.py --eval-games 30

# 降低勝率閾值（修改 trainer.py 中的 win_rate_threshold）
```

### Q5: 訓練速度太慢

**解決方案:**

1. **使用 GPU**
```bash
python training/train.py --device cuda
```

2. **減少模擬次數**
```bash
python training/train.py --simulations 200
```

3. **減少遊戲數**
```bash
python training/train.py --self-play-games 30
```

4. **使用更小的網絡**（需要修改代碼）

### Q6: 如何評估模型強度？

**方法 1: 與純 MCTS 對弈**
```python
python examples/ai_vs_ai.py
# 修改腳本，一個用神經網絡，一個用純 MCTS
```

**方法 2: 人類測試**
```bash
python examples/simple_game.py
```

**方法 3: 與不同版本模型對弈**
```python
# 使用上面的 compare_models.py
```

### Q7: 訓練數據可以重複使用嗎？

**A:** 可以！訓練數據保存在 `models/training_data/` 目錄下：

```python
# 加載之前的訓練數據
from training.self_play import load_training_data, merge_training_data

# 合併多個訓練數據文件
all_data = merge_training_data([
    "models/training_data/training_data_20250101_120000_games50.pkl",
    "models/training_data/training_data_20250101_130000_games100.pkl"
])

# 使用合併的數據訓練
# (需要修改訓練腳本)
```

## 訓練檢查清單

### 開始訓練前

- [ ] 確認環境配置正確（運行 `python test_ai.py`）
- [ ] 確認有足夠的硬盤空間（10GB+）
- [ ] 確認訓練參數合理
- [ ] 創建保存目錄
- [ ] 準備好監控訓練過程

### 訓練過程中

- [ ] 定期檢查訓練日誌
- [ ] 監控損失值是否下降
- [ ] 監控勝率是否提升
- [ ] 注意內存和 CPU/GPU 使用率
- [ ] 定期保存檢查點

### 訓練完成後

- [ ] 測試模型（人機對弈）
- [ ] 記錄模型信息（迭代次數、勝率等）
- [ ] 備份重要模型
- [ ] 部署到生產環境
- [ ] 收集用戶反饋

## 下一步

1. 開始您的第一次訓練（快速方案）
2. 測試訓練好的模型
3. 根據結果調整參數
4. 進行更長時間的訓練
5. 部署最佳模型到生產環境

祝訓練順利！🚀

