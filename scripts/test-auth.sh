#!/bin/bash

# 用户认证测试脚本

set -e

BASE_URL="http://localhost:8080"

echo "🔐 开始测试用户认证功能..."
echo ""

# 1. 注册新用户
echo "1️⃣  注册新用户..."
REGISTER_RESPONSE=$(curl -s -X POST $BASE_URL/v1/auth/register \
    -H "Content-Type: application/json" \
    -d '{
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    }')

TOKEN=$(echo $REGISTER_RESPONSE | jq -r '.token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
    echo "❌ 注册失败"
    echo "响应: $REGISTER_RESPONSE"
    exit 1
fi

echo "✅ 注册成功"
echo "   Token: ${TOKEN:0:20}..."

# 2. 获取当前用户信息
echo ""
echo "2️⃣  获取当前用户信息..."
ME_RESPONSE=$(curl -s $BASE_URL/v1/auth/me \
    -H "Authorization: Bearer $TOKEN")

USERNAME=$(echo $ME_RESPONSE | jq -r '.username')

if [ "$USERNAME" == "testuser" ]; then
    echo "✅ 获取用户信息成功"
    echo "   用户名: $USERNAME"
else
    echo "❌ 获取用户信息失败"
    echo "响应: $ME_RESPONSE"
    exit 1
fi

# 3. 测试登录
echo ""
echo "3️⃣  测试登录..."
LOGIN_RESPONSE=$(curl -s -X POST $BASE_URL/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{
        "username": "testuser",
        "password": "password123"
    }')

NEW_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.token')

if [ "$NEW_TOKEN" == "null" ] || [ -z "$NEW_TOKEN" ]; then
    echo "❌ 登录失败"
    echo "响应: $LOGIN_RESPONSE"
    exit 1
fi

echo "✅ 登录成功"
echo "   新 Token: ${NEW_TOKEN:0:20}..."

# 4. 测试错误密码
echo ""
echo "4️⃣  测试错误密码..."
ERROR_RESPONSE=$(curl -s -X POST $BASE_URL/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{
        "username": "testuser",
        "password": "wrongpassword"
    }')

ERROR=$(echo $ERROR_RESPONSE | jq -r '.error')

if [ "$ERROR" != "null" ]; then
    echo "✅ 正确拒绝错误密码"
else
    echo "❌ 应该拒绝错误密码"
    exit 1
fi

# 5. 测试无 Token 访问受保护端点
echo ""
echo "5️⃣  测试无 Token 访问受保护端点..."
UNAUTH_RESPONSE=$(curl -s $BASE_URL/v1/auth/me)

ERROR=$(echo $UNAUTH_RESPONSE | jq -r '.error')

if [ "$ERROR" != "null" ]; then
    echo "✅ 正确拒绝未认证请求"
else
    echo "❌ 应该拒绝未认证请求"
    exit 1
fi

# 6. 测试重复注册
echo ""
echo "6️⃣  测试重复注册..."
DUP_RESPONSE=$(curl -s -X POST $BASE_URL/v1/auth/register \
    -H "Content-Type: application/json" \
    -d '{
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    }')

ERROR=$(echo $DUP_RESPONSE | jq -r '.error')

if [[ "$ERROR" == *"already exists"* ]]; then
    echo "✅ 正确拒绝重复注册"
else
    echo "❌ 应该拒绝重复注册"
    echo "响应: $DUP_RESPONSE"
    exit 1
fi

echo ""
echo "🎉 所有认证测试通过！"
echo ""
echo "📊 测试总结:"
echo "   ✅ 用户注册"
echo "   ✅ 用户登录"
echo "   ✅ 获取用户信息"
echo "   ✅ Token 验证"
echo "   ✅ 错误密码拒绝"
echo "   ✅ 未认证请求拒绝"
echo "   ✅ 重复注册拒绝"

