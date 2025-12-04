# Weiqi-Go API 文档

## 基础信息

- **Base URL**: `http://localhost:8080`
- **API 版本**: v1
- **认证方式**: JWT Bearer Token

---

## 认证 API

### 1. 用户注册

**端点**: `POST /v1/auth/register`

**请求体**:
```json
{
  "username": "string (3-20字符)",
  "email": "string (有效邮箱)",
  "password": "string (最少6字符)"
}
```

**响应** (201 Created):
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "player1",
    "email": "player1@example.com",
    "created_at": "2025-12-03T10:00:00Z"
  }
}
```

**示例**:
```bash
curl -X POST http://localhost:8080/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "player1",
    "email": "player1@example.com",
    "password": "password123"
  }'
```

---

### 2. 用户登录

**端点**: `POST /v1/auth/login`

**请求体**:
```json
{
  "username": "string",
  "password": "string"
}
```

**响应** (200 OK):
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "player1",
    "email": "player1@example.com",
    "created_at": "2025-12-03T10:00:00Z"
  }
}
```

**示例**:
```bash
curl -X POST http://localhost:8080/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "player1",
    "password": "password123"
  }'
```

---

### 3. 获取当前用户信息

**端点**: `GET /v1/auth/me`

**认证**: 需要

**响应** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "player1",
  "email": "player1@example.com",
  "created_at": "2025-12-03T10:00:00Z"
}
```

**示例**:
```bash
curl http://localhost:8080/v1/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 游戏管理 API

### 4. 创建游戏

**端点**: `POST /v1/games`

**认证**: 推荐（未认证时创建匿名游戏）

**请求体**:
```json
{
  "is_ai_game": false
}
```

**参数说明**:
- `is_ai_game`: 是否为人机对弈（true=AI游戏，false=等待玩家）

**响应** (201 Created):
```json
{
  "game_id": "550e8400-e29b-41d4-a716-446655440000",
  "state": {
    "board": [[0, 0, ...], ...],
    "next_player": 1,
    "passes": 0,
    "game_over": false,
    "player_black": "user-id",
    "player_white": "",
    "status": "waiting",
    "is_ai_game": false
  }
}
```

**游戏状态说明**:
- `waiting`: 等待玩家加入
- `playing`: 进行中
- `finished`: 已结束

**示例**:
```bash
# 创建等待玩家的游戏
curl -X POST http://localhost:8080/v1/games \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_ai_game": false}'

# 创建 AI 游戏
curl -X POST http://localhost:8080/v1/games \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_ai_game": true}'
```

---

### 5. 加入游戏

**端点**: `POST /v1/games/:id/join`

**认证**: 需要

**响应** (200 OK):
```json
{
  "message": "joined game successfully",
  "state": {
    "board": [[0, 0, ...], ...],
    "next_player": 1,
    "player_black": "creator-id",
    "player_white": "your-id",
    "status": "playing"
  }
}
```

**错误响应**:
- `400`: 游戏不在等待状态 / 游戏已满 / 不能加入自己的游戏

**示例**:
```bash
curl -X POST http://localhost:8080/v1/games/GAME_ID/join \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 6. 获取游戏状态

**端点**: `GET /v1/games/:id`

**认证**: 不需要

**响应** (200 OK):
```json
{
  "board": {
    "grid": [[0, 0, ...], ...]
  },
  "next_player": 1,
  "passes": 0,
  "game_over": false,
  "captures_by_b": 0,
  "captures_by_w": 0,
  "player_black": "user-id-1",
  "player_white": "user-id-2",
  "status": "playing",
  "is_ai_game": false
}
```

**棋盘值说明**:
- `0`: 空点
- `1`: 黑子
- `2`: 白子

**示例**:
```bash
curl http://localhost:8080/v1/games/GAME_ID
```

---

### 7. 落子

**端点**: `POST /v1/games/:id/move`

**认证**: 推荐（启用权限控制）

**请求体**:
```json
{
  "x": 3,
  "y": 3
}
```

**坐标说明**:
- 坐标范围: 0-18
- 左上角为 (0, 0)
- 右下角为 (18, 18)

**响应** (200 OK):
```json
{
  "board": {
    "grid": [[0, 0, ...], ...]
  },
  "next_player": 2,
  "passes": 0,
  "game_over": false
}
```

**错误响应**:
- `400`: 非法落子（越界、非空、自杀、Ko规则）
- `403`: 不是你的回合

**示例**:
```bash
curl -X POST http://localhost:8080/v1/games/GAME_ID/move \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"x": 3, "y": 3}'
```

---

### 8. 虚手

**端点**: `POST /v1/games/:id/pass`

**认证**: 推荐

**响应** (200 OK):
```json
{
  "board": {...},
  "next_player": 2,
  "passes": 1,
  "game_over": false
}
```

**游戏结束响应** (连续两次虚手):
```json
{
  "message": "game over",
  "state": {...},
  "score": {
    "black_score": 180.0,
    "white_score": 185.75,
    "winner": 2
  }
}
```

**示例**:
```bash
curl -X POST http://localhost:8080/v1/games/GAME_ID/pass \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 9. AI 落子

**端点**: `POST /v1/games/:id/ai-move`

**认证**: 不需要

**响应** (200 OK):
```json
{
  "move": {
    "x": 5,
    "y": 7
  },
  "state": {
    "board": {...},
    "next_player": 1
  }
}
```

**错误响应**:
- `503`: AI 服务未配置
- `400`: 游戏已结束

**示例**:
```bash
curl -X POST http://localhost:8080/v1/games/GAME_ID/ai-move
```

---

### 10. 获取我的游戏列表

**端点**: `GET /v1/games/my`

**认证**: 需要

**响应** (200 OK):
```json
{
  "games": [
    {
      "id": "game-id-1",
      "player_black": "your-id",
      "player_white": "opponent-id",
      "status": "playing",
      "is_ai_game": false,
      "next_player": 1,
      "game_over": false
    },
    {
      "id": "game-id-2",
      "player_black": "your-id",
      "player_white": "AI",
      "status": "playing",
      "is_ai_game": true,
      "next_player": 2,
      "game_over": false
    }
  ],
  "count": 2
}
```

**示例**:
```bash
curl http://localhost:8080/v1/games/my \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 11. 获取等待中的游戏列表

**端点**: `GET /v1/games/waiting`

**认证**: 不需要

**响应** (200 OK):
```json
{
  "games": [
    {
      "id": "game-id-1",
      "player_black": "user-id",
      "player_white": "",
      "status": "waiting",
      "is_ai_game": false,
      "next_player": 1,
      "game_over": false
    }
  ],
  "count": 1
}
```

**示例**:
```bash
curl http://localhost:8080/v1/games/waiting
```

---

## 错误响应格式

所有错误响应遵循统一格式：

```json
{
  "error": "错误描述信息"
}
```

### 常见 HTTP 状态码

- `200 OK`: 请求成功
- `201 Created`: 资源创建成功
- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 未认证或 Token 无效
- `403 Forbidden`: 无权限执行操作
- `404 Not Found`: 资源不存在
- `409 Conflict`: 资源冲突（如用户名已存在）
- `500 Internal Server Error`: 服务器内部错误
- `503 Service Unavailable`: 服务不可用

---

## 完整游戏流程示例

### 场景 1：玩家对战

```bash
# 1. 玩家1注册并登录
TOKEN1=$(curl -s -X POST http://localhost:8080/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"player1","email":"p1@example.com","password":"pass123"}' \
  | jq -r '.token')

# 2. 玩家2注册并登录
TOKEN2=$(curl -s -X POST http://localhost:8080/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"player2","email":"p2@example.com","password":"pass123"}' \
  | jq -r '.token')

# 3. 玩家1创建游戏
GAME_ID=$(curl -s -X POST http://localhost:8080/v1/games \
  -H "Authorization: Bearer $TOKEN1" \
  -H "Content-Type: application/json" \
  -d '{"is_ai_game":false}' \
  | jq -r '.game_id')

# 4. 玩家2加入游戏
curl -X POST http://localhost:8080/v1/games/$GAME_ID/join \
  -H "Authorization: Bearer $TOKEN2"

# 5. 玩家1落子（黑棋）
curl -X POST http://localhost:8080/v1/games/$GAME_ID/move \
  -H "Authorization: Bearer $TOKEN1" \
  -H "Content-Type: application/json" \
  -d '{"x":3,"y":3}'

# 6. 玩家2落子（白棋）
curl -X POST http://localhost:8080/v1/games/$GAME_ID/move \
  -H "Authorization: Bearer $TOKEN2" \
  -H "Content-Type: application/json" \
  -d '{"x":3,"y":4}'
```

### 场景 2：人机对战

```bash
# 1. 登录
TOKEN=$(curl -s -X POST http://localhost:8080/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"player1","password":"pass123"}' \
  | jq -r '.token')

# 2. 创建 AI 游戏
GAME_ID=$(curl -s -X POST http://localhost:8080/v1/games \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_ai_game":true}' \
  | jq -r '.game_id')

# 3. 玩家落子
curl -X POST http://localhost:8080/v1/games/$GAME_ID/move \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"x":9,"y":9}'

# 4. AI 落子
curl -X POST http://localhost:8080/v1/games/$GAME_ID/ai-move
```

---

## 注意事项

1. **Token 有效期**: JWT Token 有效期为 24 小时
2. **Token 格式**: 必须使用 `Bearer YOUR_TOKEN` 格式
3. **坐标系统**: 使用 0-18 的坐标，左上角为原点
4. **游戏规则**: 遵循中国围棋规则，黑方贴 3.75 子
5. **权限控制**: 只有游戏中的玩家才能在自己的回合落子
6. **AI 服务**: 需要配置 `AI_SERVICE_URL` 环境变量

---

## 开发工具

### 使用 jq 处理 JSON

```bash
# 安装 jq
sudo apt install jq  # Ubuntu/Debian
brew install jq      # macOS

# 提取 Token
TOKEN=$(curl -s ... | jq -r '.token')

# 美化输出
curl ... | jq '.'
```

### 使用 Postman

1. 导入 API 端点
2. 设置环境变量 `BASE_URL` 和 `TOKEN`
3. 在请求头中添加 `Authorization: Bearer {{TOKEN}}`

---

## 更新日志

### v1.0.0 (2025-12-03)
- ✅ 用户认证系统
- ✅ 游戏权限控制
- ✅ 玩家对战
- ✅ 人机对弈
- ✅ 游戏列表
- ✅ 完整的围棋规则

---

**文档版本**: 1.0.0  
**最后更新**: 2025年12月3日

