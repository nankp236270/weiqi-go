#!/bin/bash

# 游戏权限控制测试脚本

set -e

BASE_URL="http://localhost:8080"

echo "🎮 开始测试游戏权限控制..."
echo ""

# 1. 注册两个用户
echo "1️⃣  注册两个用户..."
USER1_TOKEN=$(curl -s -X POST $BASE_URL/v1/auth/register \
    -H "Content-Type: application/json" \
    -d '{
        "username": "player1",
        "email": "player1@example.com",
        "password": "password123"
    }' | jq -r '.token')

USER2_TOKEN=$(curl -s -X POST $BASE_URL/v1/auth/register \
    -H "Content-Type: application/json" \
    -d '{
        "username": "player2",
        "email": "player2@example.com",
        "password": "password123"
    }' | jq -r '.token')

if [ "$USER1_TOKEN" == "null" ] || [ "$USER2_TOKEN" == "null" ]; then
    echo "❌ 用户注册失败"
    exit 1
fi

echo "✅ 两个用户注册成功"

# 2. 玩家1创建游戏（等待玩家）
echo ""
echo "2️⃣  玩家1创建游戏（等待玩家加入）..."
GAME_ID=$(curl -s -X POST $BASE_URL/v1/games \
    -H "Authorization: Bearer $USER1_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"is_ai_game": false}' | jq -r '.game_id')

if [ "$GAME_ID" == "null" ]; then
    echo "❌ 创建游戏失败"
    exit 1
fi

echo "✅ 游戏创建成功"
echo "   游戏 ID: $GAME_ID"

# 3. 查看等待中的游戏列表
echo ""
echo "3️⃣  查看等待中的游戏列表..."
WAITING_COUNT=$(curl -s $BASE_URL/v1/games/waiting | jq '.count')

if [ "$WAITING_COUNT" -ge "1" ]; then
    echo "✅ 找到 $WAITING_COUNT 个等待中的游戏"
else
    echo "❌ 应该有至少1个等待中的游戏"
    exit 1
fi

# 4. 玩家2加入游戏
echo ""
echo "4️⃣  玩家2加入游戏..."
JOIN_RESPONSE=$(curl -s -X POST $BASE_URL/v1/games/$GAME_ID/join \
    -H "Authorization: Bearer $USER2_TOKEN")

MESSAGE=$(echo $JOIN_RESPONSE | jq -r '.message')

if [[ "$MESSAGE" == *"joined"* ]]; then
    echo "✅ 玩家2成功加入游戏"
else
    echo "❌ 加入游戏失败"
    echo "响应: $JOIN_RESPONSE"
    exit 1
fi

# 5. 玩家1落子（黑棋）
echo ""
echo "5️⃣  玩家1落子（黑棋）..."
MOVE1_RESPONSE=$(curl -s -X POST $BASE_URL/v1/games/$GAME_ID/move \
    -H "Authorization: Bearer $USER1_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"x": 3, "y": 3}')

NEXT_PLAYER=$(echo $MOVE1_RESPONSE | jq -r '.next_player')

if [ "$NEXT_PLAYER" == "2" ]; then
    echo "✅ 玩家1落子成功"
else
    echo "❌ 落子失败"
    echo "响应: $MOVE1_RESPONSE"
    exit 1
fi

# 6. 测试玩家1再次落子（应该失败）
echo ""
echo "6️⃣  测试玩家1再次落子（应该失败）..."
ERROR_RESPONSE=$(curl -s -X POST $BASE_URL/v1/games/$GAME_ID/move \
    -H "Authorization: Bearer $USER1_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"x": 3, "y": 4}')

ERROR=$(echo $ERROR_RESPONSE | jq -r '.error')

if [[ "$ERROR" == *"not your turn"* ]]; then
    echo "✅ 正确拒绝非当前玩家的落子"
else
    echo "❌ 应该拒绝非当前玩家的落子"
    echo "响应: $ERROR_RESPONSE"
    exit 1
fi

# 7. 玩家2落子（白棋）
echo ""
echo "7️⃣  玩家2落子（白棋）..."
MOVE2_RESPONSE=$(curl -s -X POST $BASE_URL/v1/games/$GAME_ID/move \
    -H "Authorization: Bearer $USER2_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"x": 3, "y": 4}')

NEXT_PLAYER=$(echo $MOVE2_RESPONSE | jq -r '.next_player')

if [ "$NEXT_PLAYER" == "1" ]; then
    echo "✅ 玩家2落子成功"
else
    echo "❌ 落子失败"
    exit 1
fi

# 8. 查看玩家1的游戏列表
echo ""
echo "8️⃣  查看玩家1的游戏列表..."
MY_GAMES=$(curl -s $BASE_URL/v1/games/my \
    -H "Authorization: Bearer $USER1_TOKEN")

GAME_COUNT=$(echo $MY_GAMES | jq '.count')

if [ "$GAME_COUNT" -ge "1" ]; then
    echo "✅ 玩家1有 $GAME_COUNT 个游戏"
else
    echo "❌ 应该至少有1个游戏"
    exit 1
fi

# 9. 创建 AI 游戏
echo ""
echo "9️⃣  创建 AI 游戏..."
AI_GAME_ID=$(curl -s -X POST $BASE_URL/v1/games \
    -H "Authorization: Bearer $USER1_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"is_ai_game": true}' | jq -r '.game_id')

if [ "$AI_GAME_ID" != "null" ]; then
    echo "✅ AI 游戏创建成功"
    echo "   游戏 ID: $AI_GAME_ID"
else
    echo "❌ AI 游戏创建失败"
    exit 1
fi

# 10. 在 AI 游戏中落子
echo ""
echo "🔟  在 AI 游戏中落子..."
AI_MOVE=$(curl -s -X POST $BASE_URL/v1/games/$AI_GAME_ID/move \
    -H "Authorization: Bearer $USER1_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"x": 9, "y": 9}')

AI_NEXT=$(echo $AI_MOVE | jq -r '.next_player')

if [ "$AI_NEXT" == "2" ]; then
    echo "✅ AI 游戏落子成功"
else
    echo "❌ AI 游戏落子失败"
    exit 1
fi

echo ""
echo "🎉 所有游戏权限测试通过！"
echo ""
echo "📊 测试总结:"
echo "   ✅ 创建游戏并绑定创建者"
echo "   ✅ 查看等待中的游戏"
echo "   ✅ 玩家加入游戏"
echo "   ✅ 落子权限验证"
echo "   ✅ 拒绝非当前玩家落子"
echo "   ✅ 查看我的游戏列表"
echo "   ✅ 创建 AI 游戏"
echo "   ✅ AI 游戏权限控制"

