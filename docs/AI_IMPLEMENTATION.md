# 圍棋 AI 實現文檔

## 概述

本文檔詳細說明圍棋 AI 的實現細節，包括算法原理、架構設計和使用方法。

## 技術棧

### 核心算法

1. **MCTS (Monte Carlo Tree Search)**
   - 選擇 (Selection): 使用 UCB 公式選擇最佳子節點
   - 展開 (Expansion): 展開新的子節點
   - 模擬 (Simulation): 隨機模擬或使用神經網絡評估
   - 回傳 (Backpropagation): 更新路徑上所有節點的統計信息

2. **神經網絡**
   - 架構: ResNet 風格的卷積神經網絡
   - 輸入: 17 個特徵平面 (19x19)
   - 輸出: 策略頭 (361 個位置的概率) + 價值頭 (勝率評估)

3. **強化學習**
   - 自我對弈生成訓練數據
   - 策略梯度 + 價值函數學習
   - 迭代改進模型

## MCTS 算法詳解

### UCB 公式

```
UCB = Q + C_PUCT * P * sqrt(N_parent) / (1 + N_child)
```

其中：
- `Q`: 子節點的平均價值（勝率）
- `P`: 先驗概率（來自神經網絡的策略預測）
- `C_PUCT`: 探索常數（默認 1.5）
- `N_parent`: 父節點的訪問次數
- `N_child`: 子節點的訪問次數

### 搜索流程

```python
for _ in range(num_simulations):
    # 1. 選擇: 從根節點向下選擇到葉節點
    node = root
    while not node.is_leaf:
        node = select_child_with_max_ucb(node)
    
    # 2. 展開: 如果不是終局，展開一個新子節點
    if not node.is_terminal:
        node = expand(node)
    
    # 3. 評估: 使用神經網絡或隨機模擬評估葉節點
    value = evaluate(node)
    
    # 4. 回傳: 向上更新所有節點的統計
    backpropagate(node, value)
```

## 神經網絡架構

### 輸入編碼

17 個特徵平面 (19x19):
1. 通道 1-8: 當前玩家的棋子（最近 8 步）
2. 通道 9-16: 對手的棋子（最近 8 步）
3. 通道 17: 當前玩家顏色（黑=1，白=0）

### 網絡結構

```
Input (17, 19, 19)
    ↓
Conv2d(17 → 128, kernel=3, padding=1)
BatchNorm2d(128)
ReLU
    ↓
ResidualBlock × 10
    ↓
    ├─→ PolicyHead → (361,) logits → Softmax → 策略分佈
    └─→ ValueHead → (1,) → Tanh → 價值評估 [-1, 1]
```

### 殘差塊

```python
class ResidualBlock(nn.Module):
    def forward(self, x):
        residual = x
        out = self.conv1(x)
        out = self.bn1(out)
        out = F.relu(out)
        out = self.conv2(out)
        out = self.bn2(out)
        out += residual  # 殘差連接
        out = F.relu(out)
        return out
```

## 訓練流程

### 自我對弈

```python
# 1. 使用當前最佳模型進行自我對弈
player = NeuralMCTSPlayer(model=best_model)
game = Game()

while not game.over:
    # 使用 MCTS 選擇著法
    move, policy = player.get_move(game)
    
    # 記錄訓練樣本
    examples.append({
        'state': encode(game),
        'policy': policy,
        'player': game.next_player
    })
    
    # 執行著法
    game.play_move(move)

# 2. 根據最終結果為所有樣本賦值
winner = game.calculate_score().winner
for example in examples:
    if example['player'] == winner:
        example['value'] = 1.0
    else:
        example['value'] = -1.0
```

### 數據增強

對每個訓練樣本生成 8 個變體：
- 原始
- 旋轉 90°, 180°, 270°
- 水平翻轉
- 水平翻轉 + 旋轉 90°, 180°, 270°

### 神經網絡訓練

```python
# 損失函數
policy_loss = CrossEntropyLoss(predicted_policy, target_policy)
value_loss = MSELoss(predicted_value, target_value)
total_loss = policy_loss + value_loss

# 優化器
optimizer = Adam(network.parameters(), lr=0.001, weight_decay=1e-4)
```

### 模型評估

```python
# 新模型 vs 舊模型對弈
new_wins = 0
old_wins = 0

for _ in range(num_eval_games):
    winner = play_game(new_model, old_model)
    if winner == new_model:
        new_wins += 1
    else:
        old_wins += 1

# 如果新模型勝率 > 55%，更新最佳模型
if new_wins / (new_wins + old_wins) > 0.55:
    best_model = new_model
```

## 計分系統

### 蒙特卡洛計分

```python
# 從終局棋盤開始隨機模擬
ownership = np.zeros((19, 19, 2))  # [black, white]

for _ in range(num_simulations):
    sim_board = board.clone()
    random_playout(sim_board)
    
    # 統計每個空點被哪方佔據
    for i, j in empty_points:
        if sim_board[i][j] == BLACK:
            ownership[i][j][0] += 1
        elif sim_board[i][j] == WHITE:
            ownership[i][j][1] += 1

# 判斷領地歸屬
for i, j in empty_points:
    if ownership[i][j][0] > threshold:
        black_territory += 1
    elif ownership[i][j][1] > threshold:
        white_territory += 1
```

### 神經網絡計分

使用價值網絡直接預測終局結果，結合傳統 BFS 領地分析。

## 性能優化

### 1. MCTS 優化

- **虛擬損失 (Virtual Loss)**: 並行搜索時避免重複探索
- **早期停止**: 如果某個著法明顯最優，提前結束搜索
- **緩存**: 緩存棋盤狀態的哈希值

### 2. 神經網絡優化

- **批處理**: 將多個狀態批量送入神經網絡
- **模型量化**: 使用 INT8 量化減少模型大小
- **TensorRT**: 使用 NVIDIA TensorRT 加速推理

### 3. 訓練優化

- **分佈式訓練**: 使用多 GPU 並行訓練
- **混合精度**: 使用 FP16 加速訓練
- **梯度累積**: 模擬更大的批次大小

## API 集成

### Go 後端調用 AI 服務

```go
// ai/client.go
func GetAIMove(board [][]int, nextPlayer int, history []string) (*Move, error) {
    // 構造請求
    req := MoveRequest{
        Board:      board,
        NextPlayer: nextPlayer,
        History:    history,
    }
    
    // 調用 AI 服務
    resp, err := http.Post("http://weiqi-ai:8000/v1/ai/move", "application/json", req)
    if err != nil {
        return nil, err
    }
    
    // 解析響應
    var move MoveResponse
    json.NewDecoder(resp.Body).Decode(&move)
    
    return &Move{X: move.X, Y: move.Y}, nil
}
```

## 配置建議

### 開發環境

```bash
AI_MODE=pure_mcts
NUM_SIMULATIONS=200
SCORING_MODE=monte_carlo
SCORING_SIMULATIONS=100
```

### 生產環境

```bash
AI_MODE=neural_mcts
MODEL_PATH=/app/models/best_model.pth
NUM_SIMULATIONS=800
SCORING_MODE=neural
```

### 高性能環境

```bash
AI_MODE=neural_mcts
MODEL_PATH=/app/models/best_model.pth
NUM_SIMULATIONS=1600
SCORING_MODE=neural
DEVICE=cuda
```

## 故障排除

### 問題 1: AI 響應慢

**原因**: MCTS 模擬次數過多

**解決方案**:
- 減少 `NUM_SIMULATIONS` (400 → 200)
- 使用 GPU 加速神經網絡推理
- 啟用批處理

### 問題 2: 內存不足

**原因**: MCTS 樹過大或批次大小過大

**解決方案**:
- 減少模擬次數
- 減少批次大小
- 使用模型量化

### 問題 3: 訓練不收斂

**原因**: 學習率過大或數據不足

**解決方案**:
- 降低學習率 (0.001 → 0.0001)
- 增加自我對弈遊戲數
- 使用學習率衰減

## 未來改進方向

1. **算法改進**
   - 實現 Gumbel AlphaZero
   - 添加開局庫
   - 實現形勢判斷

2. **性能優化**
   - 使用 C++ 重寫 MCTS 核心
   - 實現 GPU 並行 MCTS
   - 優化神經網絡架構

3. **功能擴展**
   - 支持不同棋盤大小 (9x9, 13x13)
   - 實現讓子棋
   - 添加復盤分析功能

## 參考文獻

1. Silver, D., et al. (2017). "Mastering the game of Go without human knowledge." Nature, 550(7676), 354-359.
2. Silver, D., et al. (2016). "Mastering the game of Go with deep neural networks and tree search." Nature, 529(7587), 484-489.
3. Browne, C. B., et al. (2012). "A survey of monte carlo tree search methods." IEEE Transactions on Computational Intelligence and AI in games, 4(1), 1-43.

## 附錄

### A. 超參數調優指南

| 參數 | 推薦範圍 | 說明 |
|------|----------|------|
| C_PUCT | 1.0 - 2.0 | 探索常數，越大越傾向探索 |
| NUM_SIMULATIONS | 400 - 1600 | 模擬次數，越多越強但越慢 |
| LEARNING_RATE | 0.0001 - 0.001 | 學習率 |
| BATCH_SIZE | 32 - 128 | 批次大小 |
| NUM_RESIDUAL_BLOCKS | 10 - 40 | 殘差塊數量 |

### B. 訓練時間估算

- 1 局自我對弈: ~30 秒 (400 次模擬)
- 1 次迭代 (50 局): ~25 分鐘
- 訓練 10 次迭代: ~4 小時
- 訓練 100 次迭代: ~40 小時

使用 GPU 可以加速 5-10 倍。

