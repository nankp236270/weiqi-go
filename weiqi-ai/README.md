# Weiqi AI Service

这是 weiqi-go 项目的 Python AI 服务，负责提供围棋 AI 决策和计分功能。

## 项目结构

```
weiqi-ai/
├── core/           # 围棋规则引擎（与 Go 后端保持 100% 一致）
├── ai/             # AI 算法实现（MCTS、神经网络等）
├── api/            # FastAPI 服务端点
├── tests/          # 测试文件
├── training/       # 模型训练脚本
└── requirements.txt
```

## 安装

```bash
pip install -r requirements.txt
```

## 运行

```bash
# 开发模式
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn api.main:app --host 0.0.0.0 --port 8000
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

## 开发规范

1. **规则一致性**: 所有围棋规则实现必须与 Go 后端完全一致
2. **测试驱动**: 所有新功能必须有对应的测试用例
3. **类型注解**: 使用 Python 类型提示提高代码可读性
4. **文档字符串**: 所有公共函数必须有 docstring

