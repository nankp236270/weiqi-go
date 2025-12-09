# 圍棋 AI 快速入門指南

## 5 分鐘快速開始

### 1. 安裝依賴

```bash
cd weiqi-ai
pip install -r requirements.txt
```

### 2. 測試 AI 系統

```bash
python test_ai.py
```

這會運行一系列測試，驗證：
- ✓ 純 MCTS AI 功能
- ✓ 蒙特卡洛計分系統
- ✓ 自我對弈功能
- ✓ 神經網絡結構

### 3. 啟動 AI 服務

```bash
# 使用純 MCTS（無需訓練，立即可用）
export AI_MODE=pure_mcts
export NUM_SIMULATIONS=400
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### 4. 測試 API

```bash
# 獲取 AI 著法
curl -X POST http://localhost:8000/v1/ai/move \
  -H "Content-Type: application/json" \
  -d '{
    "board": [[0,0,0,...], [0,0,0,...], ...],
    "next_player": 1,
    "history": []
  }'
```

## 進階使用

### 訓練神經網絡

```bash
# 快速訓練（10 次迭代，約 30 分鐘）
python training/train.py \
    --iterations 10 \
    --self-play-games 20 \
    --eval-games 5 \
    --simulations 200 \
    --save-dir models
```

### 使用訓練好的模型

```bash
export AI_MODE=neural_mcts
export MODEL_PATH=models/best_model_iter10.pth
export NUM_SIMULATIONS=800
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## Docker 部署

### 構建鏡像

```bash
cd weiqi-ai
docker build -t weiqi-ai:latest .
```

### 運行容器

```bash
# 純 MCTS 模式
docker run -d \
  -p 8000:8000 \
  -e AI_MODE=pure_mcts \
  -e NUM_SIMULATIONS=400 \
  --name weiqi-ai \
  weiqi-ai:latest

# 神經網絡模式（需要掛載模型）
docker run -d \
  -p 8000:8000 \
  -e AI_MODE=neural_mcts \
  -e MODEL_PATH=/app/models/best_model.pth \
  -e NUM_SIMULATIONS=800 \
  -v $(pwd)/models:/app/models \
  --name weiqi-ai \
  weiqi-ai:latest
```

## 常見問題

### Q1: AI 響應太慢怎麼辦？

**A:** 減少 MCTS 模擬次數：

```bash
export NUM_SIMULATIONS=200  # 從 400 減少到 200
```

### Q2: 如何提高 AI 強度？

**A:** 增加 MCTS 模擬次數或訓練神經網絡：

```bash
# 方法 1: 增加模擬次數
export NUM_SIMULATIONS=800

# 方法 2: 訓練並使用神經網絡
python training/train.py --iterations 50
export AI_MODE=neural_mcts
export MODEL_PATH=models/best_model_iter50.pth
```

### Q3: 訓練需要多長時間？

**A:** 取決於配置：

- 10 次迭代（基礎）: ~30 分鐘
- 50 次迭代（中級）: ~3 小時
- 100 次迭代（高級）: ~6 小時

使用 GPU 可以加速 5-10 倍。

### Q4: 需要 GPU 嗎？

**A:** 不是必須的：

- **純 MCTS**: 不需要 GPU，CPU 即可
- **神經網絡訓練**: 強烈建議使用 GPU
- **神經網絡推理**: CPU 也可以，但 GPU 更快

### Q5: 如何評估 AI 強度？

**A:** 讓 AI 與自己對弈：

```bash
python test_ai.py  # 運行自我對弈測試
```

或者與其他 AI 對弈比較。

## 性能參考

### 純 MCTS

| 模擬次數 | 響應時間 | 相對強度 |
|---------|---------|---------|
| 100 | ~0.5s | 初級 |
| 200 | ~1s | 中級 |
| 400 | ~2s | 高級 |
| 800 | ~4s | 專家 |

### 神經網絡 MCTS

| 模擬次數 | 響應時間 | 相對強度 |
|---------|---------|---------|
| 200 | ~1s | 高級 |
| 400 | ~2s | 專家 |
| 800 | ~4s | 大師 |
| 1600 | ~8s | 頂級 |

*注：時間基於 Intel i7 CPU，實際性能因硬件而異*

## 下一步

1. 閱讀 [AI_IMPLEMENTATION.md](AI_IMPLEMENTATION.md) 了解技術細節
2. 閱讀 [README_AI.md](../weiqi-ai/README_AI.md) 了解完整功能
3. 開始訓練自己的神經網絡模型
4. 調整超參數優化性能

## 獲取幫助

- 查看 [API 文檔](../00-API文檔.md)
- 查看 [項目概覽](../08-項目概覽.md)
- 提交 Issue 或 Pull Request

祝您使用愉快！🎮

