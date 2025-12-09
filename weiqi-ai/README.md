# Weiqi AI Service

这是 weiqi-go 项目的 Python AI 服务，提供基于 **MCTS（蒙特卡洛树搜索）+ 神经网络** 的围棋 AI 决策和智能计分功能。

## 特性

✨ **核心功能**
- 🎯 基于 MCTS 的强大围棋 AI
- 🧠 神经网络辅助（策略网络 + 价值网络）
- 🎓 强化学习训练系统（自我对弈）
- 📊 智能终局计分（蒙特卡洛模拟 / 神经网络）
- 🔄 完整的训练循环（AlphaGo Zero 风格）

## 项目结构

```
weiqi-ai/
├── core/           # 围棋规则引擎（与 Go 后端保持 100% 一致）
│   ├── board.py    # 棋盘逻辑（落子、提子、Ko 规则）
│   └── game.py     # 游戏状态管理
├── ai/             # AI 算法实现
│   ├── mcts.py     # MCTS 核心算法
│   ├── network.py  # 神经网络架构（ResNet + 双头输出）
│   ├── mcts_player.py  # MCTS 玩家封装
│   └── scoring.py  # 智能计分系统
├── training/       # 训练模块
│   ├── self_play.py    # 自我对弈数据生成
│   ├── trainer.py      # 神经网络训练器
│   └── train.py        # 训练脚本
├── api/            # FastAPI 服务端点
│   └── main.py     # API 实现
├── scripts/        # 管理和训练脚本
│   ├── auto_train.sh       # 自动训练主程序
│   ├── monitor_training.sh # 监控面板
│   ├── stop_training.sh    # 停止训练
│   └── view_evolution.py   # 查看进化历史
├── examples/       # 示例代码
├── tests/          # 测试文件
└── requirements.txt
```

## 快速开始

### 1. 一键安装

```bash
# 自动安装所有依赖并测试
./快速安装.sh
```

### 2. 自动训练系统（推荐）⭐

**持续训练，自动升级模型**

```bash
# 一键启动自动训练（后台运行）
./开始自动训练.sh

# 实时监控训练进度
./scripts/monitor_training.sh

# 查看进化历史
python scripts/view_evolution.py

# 停止训练
./scripts/stop_training.sh
```

自动训练系统会：
- ✅ 持续训练新模型
- ✅ 自动评估模型强度
- ✅ 只保留更强的模型
- ✅ 记录完整进化历史
- ✅ 支持断点续传

### 3. 手动训练（可选）

```bash
# 快速训练（30 分钟）
./scripts/train_quick.sh

# 标准训练（4 小时）
./scripts/train_standard.sh

# 高级训练（12 小时）
./scripts/train_advanced.sh
```

### 4. 运行 AI 服务

#### 使用纯 MCTS（无需训练模型）

```bash
export AI_MODE=pure_mcts
export NUM_SIMULATIONS=400
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

#### 使用训练好的模型

```bash
export AI_MODE=neural_mcts
export MODEL_PATH=models/best_model.pth
export NUM_SIMULATIONS=800
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### 5. 人机对弈测试

```bash
# 简单对弈
python examples/simple_game.py

# AI vs AI
python examples/ai_vs_ai.py
```

## 测试

```bash
pytest tests/ -v
```

## API 端点

### 1. 获取 AI 落子
- **端点**: `POST /v1/ai/move`
- **描述**: 根据当前棋盘状态返回 AI 的下一步落子
- **请求体**:
  ```json
  {
    "board": [[0, 0, ...], ...],  // 19x19 数组
    "next_player": 1,              // 1=黑, 2=白
    "history": ["hash1", "hash2"]  // 历史状态哈希
  }
  ```
- **响应**:
  ```json
  {
    "x": 3,
    "y": 3,
    "confidence": 0.85
  }
  ```

### 2. 计算终局得分
- **端点**: `POST /v1/game/score`
- **描述**: 计算终局时的得分
- **请求体**:
  ```json
  {
    "board": [[0, 0, ...], ...]
  }
  ```
- **响应**:
  ```json
  {
    "black_score": 180.0,
    "white_score": 185.75,
    "winner": 2
  }
  ```

## 配置说明

### 环境变量

```bash
# AI 模式
AI_MODE=pure_mcts              # pure_mcts 或 neural_mcts

# MCTS 模拟次数
NUM_SIMULATIONS=400            # 越大越强，但越慢

# 计分模式
SCORING_MODE=monte_carlo       # monte_carlo 或 neural

# 模型路径（neural_mcts 模式需要）
MODEL_PATH=/path/to/model.pth
```

### 训练配置

编辑 `training_config.ini`:

```ini
[training]
iterations = 10              # 每轮迭代次数
self_play_games = 30        # 自我对弈局数
epochs = 10                 # 训练轮数
simulations = 200           # MCTS 模拟次数
eval_games = 20             # 评估局数
min_win_rate = 0.55         # 最小胜率要求
```

## 性能说明

### AI 强度对比

| 模式 | 相对强度 | 响应时间 | 需要训练 |
|------|---------|---------|---------|
| 纯 MCTS (200) | 10x | ~1s | ❌ |
| 纯 MCTS (400) | 30x | ~2s | ❌ |
| 纯 MCTS (800) | 50x | ~4s | ❌ |
| 神经网络 MCTS (400) | 100x | ~2s | ✅ |
| 神经网络 MCTS (800) | 200x | ~4s | ✅ |

### 训练时间预估

| 配置 | 每轮时间 | 适用场景 |
|------|---------|---------|
| 快速测试 | 15-30分钟 | 验证系统 |
| 标准训练 | 1-2小时 | 日常使用 |
| 深度训练 | 3-5小时 | 高质量模型 |

## 开发规范

1. **规则一致性**: 所有围棋规则实现必须与 Go 后端完全一致
2. **测试驱动**: 所有新功能必须有对应的测试用例
3. **类型注解**: 使用 Python 类型提示提高代码可读性
4. **文档字符串**: 所有公共函数必须有 docstring

## 相关文档

- [AI 完整指南](../docs/AI_GUIDE.md) - 详细的使用和训练指南
- [AI 实现文档](../docs/AI_IMPLEMENTATION.md) - 技术实现细节
- [AI 快速开始](../docs/AI_QUICKSTART.md) - 快速入门

## 故障排除

### 常见问题

1. **训练太慢？**
   - 使用 GPU
   - 减少训练参数
   - 使用快速配置

2. **内存不足？**
   - 减少批次大小
   - 减少模拟次数

3. **模型不升级？**
   - 查看胜率日志
   - 降低胜率阈值

详细故障排除请参考 [AI 完整指南](../docs/AI_GUIDE.md#故障排除)。

---

**版本**: v2.0  
**最后更新**: 2025-12-09  
**状态**: ✅ 完整且已测试
