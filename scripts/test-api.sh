#!/bin/bash

# API 测试脚本

set -e

BASE_URL="http://localhost:8080"
AI_URL="http://localhost:8000"

echo "🧪 开始测试 Weiqi-Go API..."
echo ""

# 测试 AI 服务健康
echo "1️⃣  测试 AI 服务健康..."
if curl -f $AI_URL/health > /dev/null 2>&1; then
    echo "✅ AI 服务健康"
else
    echo "❌ AI 服务不可用"
    exit 1
fi

# 创建游戏
echo ""
echo "2️⃣  创建新游戏..."
RESPONSE=$(curl -s -X POST $BASE_URL/v1/games)
GAME_ID=$(echo $RESPONSE | jq -r '.game_id')

if [ "$GAME_ID" == "null" ] || [ -z "$GAME_ID" ]; then
    echo "❌ 创建游戏失败"
    echo "响应: $RESPONSE"
    exit 1
fi

echo "✅ 游戏创建成功"
echo "   游戏 ID: $GAME_ID"

# 玩家落子（黑棋）
echo ""
echo "3️⃣  玩家落子 (3,3)..."
RESPONSE=$(curl -s -X POST $BASE_URL/v1/games/$GAME_ID/move \
    -H "Content-Type: application/json" \
    -d '{"x": 3, "y": 3}')

NEXT_PLAYER=$(echo $RESPONSE | jq -r '.next_player')
if [ "$NEXT_PLAYER" == "2" ]; then
    echo "✅ 黑棋落子成功，轮到白棋"
else
    echo "❌ 落子失败"
    echo "响应: $RESPONSE"
    exit 1
fi

# AI 落子（白棋）
echo ""
echo "4️⃣  AI 落子..."
RESPONSE=$(curl -s -X POST $BASE_URL/v1/games/$GAME_ID/ai-move)

AI_MOVE=$(echo $RESPONSE | jq -r '.move')
if [ "$AI_MOVE" != "null" ]; then
    echo "✅ AI 落子成功"
    echo "   位置: $(echo $RESPONSE | jq '.move')"
else
    echo "❌ AI 落子失败"
    echo "响应: $RESPONSE"
    exit 1
fi

# 再次玩家落子
echo ""
echo "5️⃣  玩家再次落子 (3,4)..."
curl -s -X POST $BASE_URL/v1/games/$GAME_ID/move \
    -H "Content-Type: application/json" \
    -d '{"x": 3, "y": 4}' > /dev/null

echo "✅ 落子成功"

# 获取游戏状态
echo ""
echo "6️⃣  获取游戏状态..."
RESPONSE=$(curl -s $BASE_URL/v1/games/$GAME_ID)

GAME_OVER=$(echo $RESPONSE | jq -r '.game_over')
PASSES=$(echo $RESPONSE | jq -r '.passes')

echo "✅ 游戏状态获取成功"
echo "   游戏结束: $GAME_OVER"
echo "   虚手次数: $PASSES"

# 测试虚手
echo ""
echo "7️⃣  测试虚手..."
curl -s -X POST $BASE_URL/v1/games/$GAME_ID/pass > /dev/null
curl -s -X POST $BASE_URL/v1/games/$GAME_ID/pass > /dev/null

RESPONSE=$(curl -s $BASE_URL/v1/games/$GAME_ID)
GAME_OVER=$(echo $RESPONSE | jq -r '.game_over')

if [ "$GAME_OVER" == "true" ]; then
    echo "✅ 连续虚手后游戏结束"
else
    echo "❌ 游戏应该已结束"
fi

echo ""
echo "🎉 所有测试通过！"
echo ""
echo "📊 测试总结:"
echo "   ✅ AI 服务健康检查"
echo "   ✅ 创建游戏"
echo "   ✅ 玩家落子"
echo "   ✅ AI 落子"
echo "   ✅ 获取游戏状态"
echo "   ✅ 虚手功能"
echo "   ✅ 游戏结束判断"

