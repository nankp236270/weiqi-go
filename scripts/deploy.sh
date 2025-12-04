#!/bin/bash

# 部署脚本 - 启动所有服务

set -e

echo "🚀 开始部署 Weiqi-Go 项目..."

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "⚠️  未找到 .env 文件，从 .env.example 创建..."
    cp .env.example .env
    echo "⚠️  请编辑 .env 文件设置你的配置！"
    exit 1
fi

# 停止旧容器
echo "📦 停止旧容器..."
docker compose down

# 构建镜像
echo "🔨 构建 Docker 镜像..."
docker compose build

# 启动服务
echo "▶️  启动服务..."
docker compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
docker compose ps

# 健康检查
echo ""
echo "🏥 健康检查..."

# 检查 MongoDB
if docker compose exec -T mongo mongosh --eval "db.runCommand('ping')" > /dev/null 2>&1; then
    echo "✅ MongoDB: 健康"
else
    echo "❌ MongoDB: 不健康"
fi

# 检查 AI 服务
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ AI 服务: 健康"
else
    echo "❌ AI 服务: 不健康"
fi

# 检查后端服务
sleep 5
if curl -f http://localhost:8080/v1/games > /dev/null 2>&1; then
    echo "✅ 后端服务: 健康"
else
    echo "❌ 后端服务: 不健康"
fi

echo ""
echo "🎉 部署完成！"
echo ""
echo "📝 服务地址:"
echo "   - 后端 API: http://localhost:8080"
echo "   - AI 服务: http://localhost:8000"
echo "   - AI 文档: http://localhost:8000/docs"
echo "   - MongoDB: localhost:27017"
echo ""
echo "📚 查看日志: docker compose logs -f"
echo "🛑 停止服务: docker compose down"

