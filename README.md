# 🎮 Weiqi-Go

[![Go Version](https://img.shields.io/badge/Go-1.25-blue.svg)](https://golang.org/)
[![Python Version](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success.svg)](https://github.com/your-repo/weiqi-go)

一个功能完整的在线围棋游戏平台，支持玩家对战和人机对弈。

## ✨ 特性

- 🎯 **完整的围棋规则引擎**（中国规则）
- 👥 **玩家对战**（实时匹配）
- 🤖 **人机对弈**（AI 支持）
- 🔐 **用户认证系统**（JWT）
- 🎮 **游戏权限控制**
- 📝 **结构化日志**（slog）
- 🐳 **Docker 一键部署**
- 📊 **完整的 API 文档**

## 🚀 快速开始

```bash
# 1. 克隆项目
git clone https://github.com/your-repo/weiqi-go.git
cd weiqi-go

# 2. 配置环境
cp .env.example .env
# 编辑 .env 设置密码和密钥

# 3. 一键部署
make deploy

# 4. 测试 API
make test-api
```

访问服务：
- 后端 API: http://localhost:8080
- AI 服务: http://localhost:8000
- AI 文档: http://localhost:8000/docs

## 📚 文档

- [快速开始](快速开始.md) - 详细的安装和使用指南
- [API 文档](API文档.md) - 完整的 API 接口文档
- [围棋规则](RULES.md) - 围棋规则规范
- [项目总结](项目最终总结.md) - 完整的项目总结

## 🏗️ 项目架构

**1. 项目愿景**
*   构建一个功能完善的网页围棋游戏。
*   核心功能包括**人机对弈**和**玩家对弈**（作为未来扩展方向）。
*   AI 应具备高水平棋力，基于**蒙特卡洛树搜索 (MCTS)** 和**强化学习 (RL)**。

**2. 核心架构：混合微服务架构 (Go + Python)**
*   我们采用前后端分离，后端由两个独立的微服务组成的混合架构，以最大化发挥不同语言的优势。

    *   **前端 (Presentation Layer)**
        *   **技术栈**: **Vue.js + TypeScript**。
        *   **职责**: 负责所有用户界面的渲染和交互。它是一个“瘦客户端”，不包含任何围棋游戏的核心规则逻辑。只负责向 Go 后端发送玩家操作，并根据返回的数据更新视图。

    *   **Go 后端 (Game Logic & API Layer)**
        *   **技术栈**: **Go** (使用标准库 `net/http` 或 Gin 等框架)。
        *   **职责**:
            1.  **游戏规则引擎**: 作为游戏世界唯一的“规则权威”，处理落子、提子、胜负判断等所有核心逻辑。
            2.  **API 网关**: 提供 RESTful API (用于常规请求) 和 WebSocket (用于未来的实时对战)，作为前端与后端系统的通信枢纽。
            3.  **对局管理**: 管理棋局状态、玩家信息等。
            4.  **AI 协调者**: 在人机对弈中，当轮到 AI 行动时，它会作为客户端去调用 Python AI 服务的 API 来获取决策。

    *   **Python AI 服务 (Intelligence Layer)**
        *   **技术栈**: **Python** + **FastAPI** + **PyTorch/TensorFlow**。
        *   **职责**:
            1.  **AI 模型推理 (Online)**: 提供一个独立的、无状态的 API 端点 (例如 `/get_move`)。该服务加载预先训练好的神经网络模型，结合 MCTS 算法，接收一个棋盘状态，返回最佳走法。
            2.  **终局点目 (End-game Scoring)**: 提供一个 API 端点 (例如 `/calculate_score`)，接收最终棋盘状态，返回双方的领地、死子和最终得分。这避免了在 Go 中重复实现复杂的点目逻辑。
            3.  **AI 模型训练 (Offline)**: 这是一个独立于线上服务的流程。我们将在 Python 项目中实现一个独立的围棋环境，用于强化学习中的大规模自我对弈 (self-play) 和模型训练。

**3. 核心挑战与解决方案：规则一致性**
*   **问题**: Go（线上环境）和 Python（训练环境）中存在两套独立的围棋规则实现，必须保证它们 100% 等价。
*   **解决方案**: 我们将采用一个“三层保障体系”：
    1.  **规则规范文档**: 创建一份独立于代码的详细规则说明文档，作为所有实现的“唯一事实来源”。
    2.  **共享测试用例库**: 使用一个独立的 Git 仓库，以 JSON 格式存储大量的标准测试用例，覆盖各种棋局场景（提子、打劫、禁入点等）。
    3.  **自动化交叉验证**: Go 和 Python 的项目都将在各自的 CI/CD 流水线中集成这个共享测试库，确保任何代码提交都不会破坏与另一方规则的一致性。

**4. 开发流程与迭代计划**
*   我们将从一个最小可行产品 (MVP) 开始，逐步迭代。
*   **第一步**: 搭建基础框架。
    *   Go: 实现基础棋盘逻辑和提子算法。
    *   Python: 创建一个能返回随机合法走法的简单 AI API。
    *   Vue: 创建一个能显示棋盘并响应点击的前端界面。
*   **后续步骤**:
    *   在 Go 中完善所有围棋规则（打劫、禁入点）。
    *   在 Python 中实现纯 MCTS 算法，提升 AI 棋力。
    *   引入神经网络，通过自我对弈进行强化学习训练，并将模型集成到 AI 服务中。
    *   在 Go 后端和前端支持 WebSocket，以实现玩家间的实时对战。
