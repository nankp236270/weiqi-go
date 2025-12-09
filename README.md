# 围棋对战平台 (Weiqi Go)

一个功能完整的围棋对战平台，支持人机对战、AI 自动对弈，并集成了基于 MCTS 和神经网络的智能 AI。

---

## 📋 项目简介

本项目包含：
- **前端**：Vue 3 + TypeScript + Element Plus 的现代化 Web 界面
- **后端**：Go 语言实现的高性能 API 服务
- **AI 服务**：Python 实现的智能围棋 AI（MCTS + 神经网络）
- **数据库**：MongoDB 用于数据持久化

---

## 🚀 快速开始

### 使用 Docker Compose（推荐）

```bash
# 克隆项目
git clone <repository-url>
cd weiqi-go

# 启动所有服务
docker compose up -d

# 访问应用
# 前端: http://localhost:30000
# 后端 API: http://localhost:8080
# AI 服务: http://localhost:8000
```

### 本地开发

#### 前端
```bash
cd weiqi-frontend
npm install
npm run dev
```

#### 后端
```bash
cd weiqi-go
go mod download
go run main.go
```

#### AI 服务
```bash
cd weiqi-ai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

---

## 📁 项目结构

```
weiqi-go/
├── weiqi-frontend/      # Vue 3 前端
├── weiqi-ai/            # Python AI 服务
│   ├── ai/              # AI 核心逻辑（MCTS、神经网络）
│   ├── api/             # FastAPI 服务
│   ├── core/            # 围棋核心逻辑
│   ├── training/        # 训练相关代码
│   └── scripts/         # 训练和工具脚本
├── game/                # Go 后端游戏逻辑
├── api/                 # Go 后端 API
├── ai/                  # Go AI 客户端
└── docs/                # 项目文档
```

---

## 🎮 功能特性

### 游戏功能
- ✅ 标准 19×19 围棋对弈
- ✅ 人机对战（AI 支持）
- ✅ AI 自动对弈
- ✅ 中国规则计分（子空皆地，黑贴 3.75 子）
- ✅ 劫争检测和处理
- ✅ 提子判定
- ✅ 虚手（Pass）支持

### AI 特性
- ✅ **纯 MCTS**：基于蒙特卡洛树搜索
- ✅ **神经网络辅助 MCTS**：AlphaGo Zero 风格
- ✅ **智能计分**：蒙特卡洛模拟或神经网络辅助
- ✅ **自我对弈训练**：强化学习训练循环
- ✅ **数据增强**：旋转、翻转等 8 种变换

### 前端特性
- ✅ 现代化 UI 设计
- ✅ 实时棋盘更新
- ✅ 落子预览
- ✅ 游戏历史记录
- ✅ 响应式设计

---

## 🤖 AI 系统

### AI 模式

1. **纯 MCTS 模式**（默认）
   - 无需训练，开箱即用
   - 基于蒙特卡洛树搜索
   - 适合快速测试

2. **神经网络模式**
   - 需要训练模型
   - 性能更强，更接近人类棋手
   - 支持持续训练和迭代

### AI 训练（可选）

> **注意**：AI 训练需要大量计算资源，建议在高性能机器上进行。

详细训练指南请参考：
- [AI 训练和使用指南](./docs/AI_TRAINING_GUIDE.md)
- [AI 快速开始](./docs/AI_QUICKSTART.md)

---

## 📚 文档索引

### 核心文档
- [项目完整开发报告](./17-项目完整开发报告.md)
- [部署指南](./docs/DEPLOYMENT.md)
- [API 文档](./docs/README.md)

### AI 相关
- [AI 实现文档](./docs/AI_IMPLEMENTATION.md)
- [AI 训练指南](./docs/AI_TRAINING_GUIDE.md)
- [AI 快速开始](./docs/AI_QUICKSTART.md)

### 问题修复记录
- [Bug 修复汇总](./docs/bug-fixes/修复记录汇总.md)

---

## 🔧 配置说明

### 环境变量

#### AI 服务 (`weiqi-ai`)
```bash
AI_MODE=pure_mcts              # AI 模式：pure_mcts 或 neural_mcts
NUM_SIMULATIONS=400            # MCTS 模拟次数
SCORING_MODE=monte_carlo       # 计分模式：monte_carlo 或 neural
SCORING_SIMULATIONS=200        # 计分模拟次数
MODEL_PATH=/path/to/model.pth  # 神经网络模型路径（neural_mcts 模式需要）
```

#### 后端服务
```bash
AI_SERVICE_URL=http://weiqi-ai:8000  # AI 服务地址
MONGO_URI=mongodb://weiqi-mongo:27017  # MongoDB 连接
```

---

## 🛠️ 开发指南

### 技术栈

**前端**：
- Vue 3
- TypeScript
- Element Plus
- Pinia (状态管理)
- Axios

**后端**：
- Go 1.25+
- Gin (Web 框架)
- MongoDB

**AI 服务**：
- Python 3.11+
- PyTorch
- FastAPI
- NumPy

### 代码规范

- 前端：遵循 Vue 3 Composition API 风格
- 后端：遵循 Go 标准项目结构
- AI：遵循 Python PEP 8 规范

---

## 📊 性能说明

### AI 性能

| 模式 | 模拟次数 | 每步耗时 | 棋力 |
|------|----------|----------|------|
| 纯 MCTS (400) | 400 | ~2-5秒 | 初级 |
| 纯 MCTS (800) | 800 | ~5-10秒 | 中级 |
| 神经网络 (400) | 400 | ~1-3秒 | 高级 |

### 资源需求

- **运行 AI 服务**：2GB RAM，1 CPU 核心
- **训练 AI 模型**：8GB+ RAM，GPU 推荐（否则极慢）

---

## 🐛 已知问题

- AI 训练在 CPU 上非常慢（建议使用 GPU）
- 大规模自我对弈需要大量磁盘空间
- Docker 镜像较大（~8GB，主要是 PyTorch）

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

---

## 📝 更新日志

### 2025-12-09
- ✅ 完成 AI 系统集成
- ✅ 实现自动训练系统
- ✅ 优化 Docker 构建
- ✅ 修复训练相关 Bug
- ✅ 文档整理和简体化

### 2025-12-06
- ✅ 完成前端开发
- ✅ 完成后端 API
- ✅ 集成 MongoDB

---

## 📄 许可证

MIT License

---

## 👥 作者

[Your Name]

---

## 🙏 致谢

- AlphaGo Zero 论文提供的 AI 架构灵感
- 围棋社区的支持和反馈
