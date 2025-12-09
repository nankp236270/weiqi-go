# AI 使用示例

這個目錄包含了各種使用圍棋 AI 的示例腳本。

## 示例列表

### 1. simple_game.py - 人機對弈

與 AI 進行一局完整的圍棋對弈。

**運行方式:**
```bash
cd weiqi-ai
python examples/simple_game.py
```

**功能:**
- 選擇黑棋或白棋
- 與 AI 輪流下棋
- 查看 AI 的思考過程
- 自動計算終局得分

**操作說明:**
- 輸入格式: `x,y` (例如: `3,3`)
- 虛手: 輸入 `pass`
- 退出: 按 `Ctrl+C`

### 2. ai_vs_ai.py - AI 對弈

觀看兩個不同強度的 AI 互相對弈。

**運行方式:**
```bash
cd weiqi-ai
python examples/ai_vs_ai.py
```

**功能:**
- AI 1 (400 次模擬) vs AI 2 (200 次模擬)
- 自動進行完整對局
- 顯示每步的勝率評估
- 每 10 步顯示一次棋盤

## 自定義配置

### 調整 AI 強度

編輯腳本中的 `num_simulations` 參數:

```python
# 弱 AI
ai = PureMCTSPlayer(num_simulations=100)

# 中等 AI
ai = PureMCTSPlayer(num_simulations=400)

# 強 AI
ai = PureMCTSPlayer(num_simulations=800)

# 超強 AI
ai = PureMCTSPlayer(num_simulations=1600)
```

### 使用神經網絡 AI

```python
from ai.mcts_player import NeuralMCTSPlayer

# 創建神經網絡 AI
ai = NeuralMCTSPlayer(
    model_path="models/best_model.pth",
    num_simulations=800
)
```

## 更多示例

### 批量對弈測試

```python
# 測試 AI 強度
wins = 0
total = 10

for i in range(total):
    game = Game()
    # ... 進行對弈
    result = game.calculate_score()
    if result.winner == Player.BLACK:
        wins += 1

print(f"勝率: {wins/total:.1%}")
```

### 保存對局記錄

```python
# 記錄所有著法
moves = []

while not game.game_over:
    move, _ = ai.get_move(game)
    if move:
        moves.append((move.x, move.y))
        game.play_move(move)

# 保存到文件
import json
with open('game_record.json', 'w') as f:
    json.dump(moves, f)
```

### 分析 AI 決策

```python
# 獲取詳細統計
move, stats = ai.get_move(game)

print(f"總模擬次數: {stats['total_simulations']}")
print(f"最佳著法訪問次數: {stats['best_move_visits']}")
print(f"最佳著法勝率: {stats['best_move_win_rate']:.2%}")
print(f"合法著法數量: {stats['num_legal_moves']}")
```

## 故障排除

### 問題 1: 導入錯誤

**錯誤信息:**
```
ModuleNotFoundError: No module named 'core'
```

**解決方案:**
確保從 `weiqi-ai` 目錄運行腳本:
```bash
cd weiqi-ai
python examples/simple_game.py
```

### 問題 2: AI 響應慢

**原因:** MCTS 模擬次數過多

**解決方案:**
減少模擬次數:
```python
ai = PureMCTSPlayer(num_simulations=200)  # 從 400 減少到 200
```

### 問題 3: 內存不足

**原因:** MCTS 樹過大

**解決方案:**
- 減少模擬次數
- 限制最大步數
- 定期清理 MCTS 樹

## 進階用法

### 實現自定義 AI

```python
from ai.mcts_player import MCTSPlayer

class MyCustomAI(MCTSPlayer):
    def get_move(self, game_state):
        # 自定義決策邏輯
        move, stats = super().get_move(game_state)
        
        # 添加自定義處理
        # ...
        
        return move, stats
```

### 集成到 Web 應用

```python
from fastapi import FastAPI
from ai.mcts_player import PureMCTSPlayer

app = FastAPI()
ai = PureMCTSPlayer(num_simulations=400)

@app.post("/get-move")
async def get_move(board_state: dict):
    game = Game.from_dict(board_state)
    move, stats = ai.get_move(game)
    return {"x": move.x, "y": move.y, "stats": stats}
```

## 相關文檔

- [AI 實現文檔](../../docs/AI_IMPLEMENTATION.md)
- [AI 快速入門](../../docs/AI_QUICKSTART.md)
- [API 文檔](../../00-API文檔.md)

## 貢獻

歡迎提交更多示例！請確保:
1. 代碼清晰易懂
2. 包含詳細註釋
3. 更新此 README

